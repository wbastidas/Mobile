"""Sincronización y comunicación con la app móvil (RF-SYNC, RF-MOV-02/09/10).

Flujo:
  1. pull    -> descarga incremental: trabajos nuevos, órdenes de borrado,
                versión de parámetros de calidad (RF-SYNC.7).
  2. upload  -> el dispositivo sube el paquete (atributos+geometrías+fotos meta)
                con clave de idempotencia (RF-SYNC.5) y resultado de validación.
  3. verify  -> verificación de completitud; si todo confirmado, consolida a
                ArcSDE/Oracle y marca el trabajo Terminado (RF-MOV-10.2).
  4. confirm-delete -> el dispositivo confirma la ejecución de un borrado remoto.
"""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.enums import (
    AuditAction,
    ElementOperation,
    RemoteDeleteStatus,
    Role,
    ValidationResult,
    WorkStatus,
)
from app.models.device import Device
from app.models.element import Element, WorkElement
from app.models.element_log import ElementLog
from app.models.field_change import FieldChange
from app.models.quality_novelty import QualityNovelty
from app.models.quality_params import QualityParamSet, SchemaDefinition
from app.models.sync import Photo, RemoteDeleteOrder, SyncPackage
from app.models.user import User
from app.models.work import Work
from app.modules.gis.adapter import ExtractedElement, get_gis_adapter
from app.services import photo_storage
from app.schemas.sync import (
    PullResponse,
    SyncUploadRequest,
    SyncUploadResponse,
    SyncVerifyResponse,
)
from app.services import audit

router = APIRouter(prefix="/sync", tags=["sync"])


def _field_user(user: User = Depends(get_current_user)) -> User:
    role = user.role if isinstance(user.role, str) else user.role.value
    if role != Role.FIELD.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo funcionarios de campo.")
    return user


def _persist_novelties(db: Session, pkg: SyncPackage, report_json: str | None) -> None:
    """Extrae del reporte de validación las novedades por regla y las persiste.

    Tolera formatos: el DTO detallado {"result":..,"issues":[{...}]} o el conteo
    simple {"issues": n} (retrocompatible; en ese caso no hay detalle que guardar).
    """
    if not report_json:
        return
    try:
        data = json.loads(report_json)
    except (json.JSONDecodeError, TypeError):
        return
    issues = data.get("issues")
    if not isinstance(issues, list):
        return
    for it in issues:
        if not isinstance(it, dict):
            continue
        db.add(QualityNovelty(
            package_id=pkg.id, work_id=pkg.work_id, un_id=pkg.un_id,
            element_guid=it.get("element_guid"), element_type=it.get("element_type"),
            field=it.get("field"), rule_type=it.get("rule_type") or "desconocida",
            message=it.get("message"), expected=it.get("expected"), actual=it.get("actual"),
        ))


def _get_device(db: Session, device_uid: str, user: User) -> Device:
    device = db.query(Device).filter(Device.device_uid == device_uid).first()
    if not device or not device.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispositivo no autorizado.")
    if device.un_id != user.un_id or device.assigned_user_id not in (None, user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Dispositivo no vinculado al funcionario.")
    return device


@router.get("/pull", response_model=PullResponse)
def pull(device_uid: str, db: Session = Depends(get_db), user: User = Depends(_field_user)):
    """Descarga incremental de novedades para el dispositivo (RF-SYNC.7)."""
    device = _get_device(db, device_uid, user)
    device.last_seen_at = datetime.now(timezone.utc)

    # Trabajos asignados aún no descargados / en curso.
    works = (
        db.query(Work)
        .filter(Work.device_id == device.id)
        .filter(Work.status.in_([WorkStatus.ASSIGNED, WorkStatus.DOWNLOADED, WorkStatus.IN_PROGRESS,
                                 WorkStatus.SYNC_PENDING]))
        .all()
    )
    new_works = []
    for w in works:
        elements = db.query(WorkElement).filter(WorkElement.work_id == w.id).all()
        new_works.append({
            "id": w.id, "code": w.code, "title": w.title, "work_type": w.work_type,
            "status": w.status, "schema_version": w.schema_version,
            "sector_geojson": w.sector_geojson,
            "elements": [
                {"element_guid": e.element_guid, "geometry_geojson": e.geometry_geojson,
                 "attributes_json": e.attributes_json, "completed": e.completed}
                for e in elements
            ],
        })
        if w.status == WorkStatus.ASSIGNED:
            w.status = WorkStatus.DOWNLOADED
            w.downloaded_at = datetime.now(timezone.utc)

    # Órdenes de borrado remoto en cola (RF-WEB-05 / RF-MOV-02).
    delete_orders = (
        db.query(RemoteDeleteOrder)
        .filter(RemoteDeleteOrder.device_id == device.id,
                RemoteDeleteOrder.status == RemoteDeleteStatus.QUEUED)
        .all()
    )

    # Parámetros de calidad vigentes (RF-WEB-10.3) y esquema activo.
    qp = db.query(QualityParamSet).filter(QualityParamSet.is_active.is_(True)).first()
    schema = db.query(SchemaDefinition).filter(SchemaDefinition.is_active.is_(True)).first()

    db.commit()
    return PullResponse(
        new_works=new_works,
        remote_delete_work_ids=[o.work_id for o in delete_orders],
        quality_params_version=qp.version if qp else None,
        quality_params_rules=json.loads(qp.rules_json) if qp else None,
        schema_version=schema.version if schema else None,
    )


@router.post("/upload", response_model=SyncUploadResponse)
def upload(payload: SyncUploadRequest, db: Session = Depends(get_db), user: User = Depends(_field_user)):
    """Recibe un paquete de sincronización (RF-WEB-09). Idempotente (RF-SYNC.5)."""
    device = _get_device(db, payload.device_uid, user)
    work = db.get(Work, payload.work_id)
    if not work or work.device_id != device.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trabajo no asignado a este dispositivo.")

    # Idempotencia: reintentos no duplican (RF-SYNC.5).
    existing = db.query(SyncPackage).filter(
        SyncPackage.idempotency_key == payload.idempotency_key
    ).first()
    if existing:
        missing = [p.sha256 for p in existing.photos if not p.fully_received]
        return SyncUploadResponse(package_id=existing.id, accepted=True, duplicate=True,
                                  missing_photos=missing, detail="Paquete ya recibido (idempotente).")

    pkg = SyncPackage(
        idempotency_key=payload.idempotency_key,
        work_id=work.id, device_id=device.id, un_id=work.un_id,
        schema_version=payload.schema_version, checksum=payload.checksum,
        payload_json=payload.payload_json,
        validation_result=payload.validation_result,
        validation_report_json=payload.validation_report_json,
    )
    db.add(pkg)
    db.flush()

    # Registro de metadata de fotos (los binarios llegan por chunks, RF-SYNC.3).
    for ph in payload.photos:
        db.add(Photo(package_id=pkg.id, element_guid=ph.element_guid, work_id=work.id,
                     gps_lat=ph.gps_lat, gps_lon=ph.gps_lon, captured_at=ph.captured_at,
                     user_id=user.id, device_id=device.id, sha256=ph.sha256,
                     size_bytes=ph.size_bytes, total_chunks=max(1, ph.total_chunks),
                     fully_received=(ph.total_chunks <= 1 and ph.size_bytes == 0)))

    # Persistir el detalle de novedades de calidad por regla (RF-WEB-09.2).
    _persist_novelties(db, pkg, payload.validation_report_json)

    work.status = WorkStatus.SYNCING
    work.validation_result = payload.validation_result
    audit.record(db, action=AuditAction.SYNC_RECEIVE.value, actor=user, entity_type="Work",
                 entity_id=work.id, un_id=work.un_id, device_id=device.id,
                 new_values={"package_id": pkg.id, "validation": payload.validation_result})
    db.commit()

    missing = [p.sha256 for p in pkg.photos if not p.fully_received]
    return SyncUploadResponse(package_id=pkg.id, accepted=True, duplicate=False,
                              missing_photos=missing,
                              detail="Paquete recibido; suba las fotos pendientes por chunks.")


@router.post("/photo/{sha256}/chunk")
async def upload_photo_chunk(
    sha256: str,
    index: int,
    total: int,
    chunk: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(_field_user),
):
    """Sube un chunk de una foto (subida reanudable por lotes, RF-SYNC.3).

    Al recibir el último chunk ensambla el archivo y verifica su integridad por
    SHA-256 (RF-SYNC.4). Solo si el hash coincide la foto se marca como recibida.

    Seguridad: el hash y los índices se validan antes de tocar el sistema de
    archivos, y cada chunk respeta el tamaño máximo configurado.
    """
    if not photo_storage.SHA256_RE.fullmatch(sha256):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Identificador de foto inválido (se espera SHA-256 hex).")
    if total < 1 or total > 10_000 or index < 0 or index >= total:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "Índices de chunk fuera de rango.")

    photos = (
        db.query(Photo)
        .filter(Photo.sha256 == sha256, Photo.user_id == user.id)
        .all()
    )
    if not photos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto no registrada para este funcionario.")
    if all(p.fully_received for p in photos):
        return {"received": total, "total": total, "complete": True, "verified": True,
                "detail": "Foto ya recibida (idempotente)."}

    data = await chunk.read(settings.UPLOAD_CHUNK_MAX_BYTES + 1)
    if len(data) > settings.UPLOAD_CHUNK_MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            "El chunk excede el tamaño máximo permitido.")
    result = photo_storage.save_chunk(sha256, index, total, data)

    for p in photos:
        p.received_chunks = result.received

    if not result.complete:
        db.commit()
        return {"received": result.received, "total": total, "complete": False, "verified": False}

    work_id = photos[0].work_id or "sin_trabajo"
    assembled = photo_storage.assemble_and_verify(sha256, total, work_id)
    if assembled.verified:
        stored_at = photo_storage.final_path(work_id, sha256)
        for p in photos:
            p.fully_received = True
            p.received_chunks = total
            p.storage_path = stored_at
    db.commit()
    return {"received": assembled.received, "total": total,
            "complete": assembled.complete, "verified": assembled.verified,
            "detail": "Foto recibida y verificada." if assembled.verified
            else "Integridad fallida; reintente la foto."}


@router.post("/verify/{package_id}", response_model=SyncVerifyResponse)
def verify(package_id: str, db: Session = Depends(get_db), user: User = Depends(_field_user)):
    """Verificación de completitud y consolidación (RF-MOV-10.2, RF-WEB-09.3/4).

    RN-04: si algo está incompleto, el trabajo NO puede terminarse; queda
    pendiente para reintentar todo el proceso.
    """
    pkg = db.get(SyncPackage, package_id)
    if not pkg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Paquete no encontrado.")
    work = db.get(Work, pkg.work_id)
    device = _get_device(db, work.device.device_uid if work.device else "", user)

    pending = [p.sha256 for p in pkg.photos if not p.fully_received]
    if pending:
        work.status = WorkStatus.SYNC_PENDING
        db.commit()
        return SyncVerifyResponse(work_id=work.id, verified=False, status=work.status,
                                  detail=f"Faltan {len(pending)} fotos por confirmar; reintente.")

    pkg.verified = True
    audit.record(db, action=AuditAction.SYNC_VERIFY.value, actor=user, entity_type="Work",
                 entity_id=work.id, un_id=work.un_id, device_id=device.id)

    # Persistir elementos del paquete en el modelo corporativo + bitácora (RF-WEB-07).
    try:
        elements = json.loads(pkg.payload_json).get("elements", [])
    except (json.JSONDecodeError, AttributeError):
        elements = []
    extracted = []
    for el in elements:
        guid = el.get("guid") or el.get("element_guid")
        if not guid:
            continue
        entity = db.query(Element).filter(Element.guid == guid).first()
        attrs = el.get("attributes") or {}
        attrs_json = json.dumps(attrs, ensure_ascii=False)

        # La operación de campo la determinan los flags del móvil, no si el
        # espejo local ya existe: un elemento del sector se EDITA (UPDATE) aunque
        # sea la primera vez que se materializa como fila `Element`.
        if bool(el.get("deleted")):
            operation = ElementOperation.DELETE
        elif bool(el.get("is_new")):
            operation = ElementOperation.CREATE
        else:
            operation = ElementOperation.UPDATE

        before = entity.attributes_json if entity else None

        if operation == ElementOperation.DELETE:
            if entity:
                entity.deleted = True  # baja lógica; el editor la aplica en la GDB
            element_type = entity.element_type if entity else el.get("element_type", "DESCONOCIDO")
        elif entity is None:
            entity = Element(guid=guid, element_type=el.get("element_type", "DESCONOCIDO"),
                             un_id=work.un_id, parent_guid=el.get("parent_guid"),
                             geometry_geojson=el.get("geometry_geojson"),
                             attributes_json=attrs_json,
                             is_new=(operation == ElementOperation.CREATE))
            db.add(entity)
            db.flush()
            element_type = entity.element_type
        else:
            entity.geometry_geojson = el.get("geometry_geojson", entity.geometry_geojson)
            entity.attributes_json = attrs_json
            element_type = entity.element_type

        # Bitácora por elemento (RF-WEB-07) con el tipo de operación.
        if entity:
            db.add(ElementLog(element_id=entity.id, element_guid=guid, event_type=operation.value,
                              detail=f"{operation.value} en trabajo {work.code}", work_id=work.id,
                              user_id=user.id, device_id=device.id))

        # Histórico de cambios por usuario y por trabajo.
        db.add(FieldChange(
            user_id=user.id, username=user.username, device_id=device.id,
            work_id=work.id, work_code=work.code, un_id=work.un_id,
            element_guid=guid, element_type=element_type, operation=operation.value,
            attributes_before=before,
            attributes_after=(None if operation == ElementOperation.DELETE else attrs_json),
        ))

        extracted.append(ExtractedElement(
            guid=guid, element_type=element_type,
            geometry_geojson=el.get("geometry_geojson"),
            attributes=attrs, parent_guid=el.get("parent_guid"),
            operation=operation.value,
        ))

    # Consolidación hacia ArcSDE/Oracle mediante el adaptador aislado (§7.2, RN-11).
    # Con el adaptador de staging, esto crea un lote reversible en revisión.
    result = get_gis_adapter().consolidate(work.business_unit.code, extracted,
                                           db=db, work_id=work.id)
    if not result.ok:
        work.status = WorkStatus.SYNC_PENDING
        db.commit()
        return SyncVerifyResponse(work_id=work.id, verified=False, status=work.status,
                                  detail="Falló la consolidación corporativa; reintente.")

    pkg.consolidated = True
    work.synced_at = datetime.now(timezone.utc)
    work.completed_at = datetime.now(timezone.utc)
    work.status = (WorkStatus.WITH_ISSUES if pkg.validation_result == ValidationResult.WITH_ISSUES
                   else WorkStatus.COMPLETED)
    audit.record(db, action=AuditAction.CONSOLIDATE.value, actor=user, entity_type="Work",
                 entity_id=work.id, un_id=work.un_id, device_id=device.id,
                 new_values={"staging_ref": result.staging_ref, "guids": result.consolidated_guids})
    db.commit()
    return SyncVerifyResponse(work_id=work.id, verified=True, status=work.status,
                              detail=f"Sincronización verificada y consolidada. {result.message}")


@router.post("/confirm-delete/{work_id}")
def confirm_remote_delete(work_id: str, device_uid: str,
                          db: Session = Depends(get_db), user: User = Depends(_field_user)):
    """El dispositivo confirma la ejecución de un borrado remoto (RF-WEB-05.2)."""
    device = _get_device(db, device_uid, user)
    order = (db.query(RemoteDeleteOrder)
             .filter(RemoteDeleteOrder.work_id == work_id,
                     RemoteDeleteOrder.device_id == device.id,
                     RemoteDeleteOrder.status == RemoteDeleteStatus.QUEUED)
             .first())
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden de borrado no encontrada.")
    order.status = RemoteDeleteStatus.CONFIRMED
    order.confirmed_at = datetime.now(timezone.utc).isoformat()

    # Libera el trabajo del dispositivo, habilitando reasignación (RF-WEB-04.7).
    work = db.get(Work, work_id)
    if work:
        work.device_id = None
        work.status = WorkStatus.CREATED
    audit.record(db, action=AuditAction.REMOTE_DELETE_CONFIRM.value, actor=user,
                 entity_type="Work", entity_id=work_id, un_id=order.un_id, device_id=device.id)
    db.commit()
    return {"detail": "Borrado remoto confirmado; trabajo liberado para reasignación."}

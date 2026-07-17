"""Datos semilla para desarrollo y demostración.

Crea: Matriz + 2 UN, usuarios de todos los roles, un dispositivo, parámetros de
calidad, definición de esquema y trabajos de ejemplo de los tres tipos.

Uso:  python -m app.seed
"""
import json

from app.core import database
from app.core.enums import AuthType, Role, WorkStatus, WorkType
from app.core.security import hash_password
from app.models.business_unit import BusinessUnit
from app.models.device import Device
from app.models.element import WorkElement
from app.models.quality_params import QualityParamSet, SchemaDefinition
from app.models.user import User
from app.models.work import Work

DEMO_PASSWORD = "Campo2026!"


def run():
    # Resuelve engine/sesión en tiempo de ejecución (permite override en pruebas).
    database.Base.metadata.create_all(bind=database.engine)
    db = database.SessionLocal()
    try:
        if db.query(BusinessUnit).count() > 0:
            print("La base ya tiene datos; se omite el seed.")
            return

        matriz = BusinessUnit(code="MATRIZ", name="Oficina Central (Matriz)", is_headquarters=True)
        un_norte = BusinessUnit(code="UN-NORTE", name="Unidad de Negocio Norte")
        un_sur = BusinessUnit(code="UN-SUR", name="Unidad de Negocio Sur")
        db.add_all([matriz, un_norte, un_sur])
        db.flush()

        users = [
            User(username="admin", full_name="Administrador del Sistema", role=Role.ADMIN,
                 auth_type=AuthType.LOCAL, hashed_password=hash_password(DEMO_PASSWORD)),
            User(username="op.matriz", full_name="Operador Matriz", role=Role.OPERATOR_MATRIZ,
                 auth_type=AuthType.LOCAL, hashed_password=hash_password(DEMO_PASSWORD)),
            User(username="op.norte", full_name="Operador UN Norte", role=Role.OPERATOR_UN,
                 un_id=un_norte.id, auth_type=AuthType.LOCAL,
                 hashed_password=hash_password(DEMO_PASSWORD)),
            User(username="view.sur", full_name="Visualizador UN Sur", role=Role.VIEWER_UN,
                 un_id=un_sur.id, auth_type=AuthType.LOCAL,
                 hashed_password=hash_password(DEMO_PASSWORD)),
            User(username="campo.norte", full_name="Funcionario de Campo Norte", role=Role.FIELD,
                 un_id=un_norte.id, auth_type=AuthType.LOCAL,
                 hashed_password=hash_password(DEMO_PASSWORD)),
        ]
        db.add_all(users)
        db.flush()
        field_user = users[-1]

        device = Device(device_uid="ANDROID-DEMO-001", alias="Tablet Campo Norte 01",
                        un_id=un_norte.id, assigned_user_id=field_user.id)
        db.add(device)

        qp_rules = {
            "version": 1,
            "rules": {
                "POSTE": [
                    {"field": "material", "type": "domain", "values": ["HORMIGON", "MADERA", "METAL"]},
                    {"field": "altura_m", "type": "range", "min": 6, "max": 20},
                    {"rule": "min_photos", "value": 2},
                ],
                "LUMINARIA": [
                    {"field": "potencia_w", "type": "required"},
                ],
            },
        }
        db.add(QualityParamSet(version=1, description="Parámetros iniciales",
                               rules_json=json.dumps(qp_rules, ensure_ascii=False),
                               is_active=True))

        schema_def = {
            "version": 1,
            "layers": [
                {"name": "POSTE", "geometry": "point",
                 "fields": [{"name": "material", "type": "text"},
                            {"name": "altura_m", "type": "number"}]},
                {"name": "LUMINARIA", "geometry": "point", "parent": "POSTE",
                 "fields": [{"name": "potencia_w", "type": "number"}]},
            ],
        }
        db.add(SchemaDefinition(version=1, description="Esquema eléctrico inicial",
                                definition_json=json.dumps(schema_def, ensure_ascii=False),
                                is_active=True))

        # Trabajo tipo Revisión de red (sector)
        w1 = Work(code="REV-2026-001", title="Revisión sector Centro Norte",
                  work_type=WorkType.REVISION_RED, un_id=un_norte.id,
                  status=WorkStatus.CREATED,
                  sector_geojson='{"type":"Polygon","coordinates":[[[-78.51,-0.21],'
                                 '[-78.49,-0.21],[-78.49,-0.19],[-78.51,-0.19],[-78.51,-0.21]]]}')
        db.add(w1)
        db.flush()
        db.add(WorkElement(work_id=w1.id, element_guid="UN-NORTE-POSTE-0001",
                           geometry_geojson='{"type":"Point","coordinates":[-78.5,-0.2]}',
                           attributes_json='{"material":"HORMIGON","altura_m":12}'))

        # Trabajo tipo Orden puntual
        w2 = Work(code="ORD-2026-014", title="Inspección poste dañado",
                  work_type=WorkType.ORDEN_PUNTUAL, un_id=un_norte.id, status=WorkStatus.CREATED)
        db.add(w2)
        db.flush()
        db.add(WorkElement(work_id=w2.id, element_guid="UN-NORTE-POSTE-0042"))

        # Trabajo tipo Mantenimiento/proyecto
        w3 = Work(code="MTO-2026-003", title="Proyecto ampliación red barrio Sur",
                  work_type=WorkType.MANTENIMIENTO, un_id=un_sur.id, status=WorkStatus.CREATED)
        db.add(w3)

        db.commit()
        print("Seed completado.")
        print(f"  UN: MATRIZ, UN-NORTE, UN-SUR")
        print(f"  Usuarios (clave '{DEMO_PASSWORD}'): admin, op.matriz, op.norte, view.sur, campo.norte")
        print(f"  Dispositivo: ANDROID-DEMO-001")
        print(f"  Trabajos: REV-2026-001, ORD-2026-014, MTO-2026-003")
    finally:
        db.close()


if __name__ == "__main__":
    run()

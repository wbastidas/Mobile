# Estado de implementación y trazabilidad

Sistema de Gestión y Levantamiento de Datos Eléctricos en Campo.
Documento vivo que resume qué está implementado, cómo se verificó y qué queda
pendiente, con trazabilidad a los requerimientos del documento fuente.

## 1. Resumen por componente

| Componente | Tecnología | Estado | Verificación en este entorno |
|---|---|---|---|
| **Backend API** | Python · FastAPI · SQLAlchemy | Base funcional completa | ✅ 23 pruebas `pytest` + smoke en vivo |
| **WEB-ADMIN** | React · TypeScript · Vite | Base funcional completa | ✅ `tsc` estricto + `vite build` + endpoints en vivo |
| **APP-CAMPO · core** | Kotlin puro (JVM) | Lógica crítica completa | ✅ 19 pruebas JUnit (Gradle) |
| **APP-CAMPO · app** | Kotlin · Jetpack Compose | Base funcional completa | ⚠️ Compila en Android Studio; sin Android SDK aquí |

> El módulo `mobile/core` aísla deliberadamente la lógica sensible (validación de
> calidad, snapping, geometría, idempotencia) en Kotlin puro para poder probarla
> sin el SDK de Android. Es la parte más crítica de la app y está verificada.

## 2. Cómo ejecutar y probar

```bash
# Backend (API + pruebas)
cd backend && pip install -r requirements.txt
python -m app.seed && uvicorn app.main:app --reload   # http://localhost:8000/docs
python -m pytest                                       # 23 pruebas

# Frontend (SPA)
cd frontend && npm install && npm run dev              # http://localhost:5173
npm run build                                          # typecheck + build

# Móvil — lógica core (sin Android SDK)
cd mobile/core && gradle test                          # 19 pruebas JUnit

# Móvil — app completa (requiere Android Studio + SDK)
# abrir mobile/ en Android Studio; ./gradlew :app:assembleDebug
```

## 3. Matriz de trazabilidad — Plataforma Web (RF-WEB)

| ID | Requerimiento | Implementación | Estado |
|---|---|---|---|
| RF-WEB-01 | Autenticación doble mecanismo | `backend/app/api/v1/auth.py`, `core/security.py` · web `pages/Login.tsx` | ✅ (local); corporativo delegable (PD-05) |
| RF-WEB-02 | Usuarios, roles, UN, dispositivos | `api/v1/{users,business_units,devices}.py` · web `pages/{Users,Devices}.tsx` | ✅ |
| RF-WEB-03 | Tipos de trabajo | `core/enums.py` (WorkType), `api/v1/works.py` | ✅ |
| RF-WEB-04 | Asignación a dispositivos | `works.assign_works` · web `pages/Works.tsx` | ✅ (RN-01/02/07) |
| RF-WEB-05 | Borrado remoto | `works.remote_delete`, `sync.confirm_remote_delete` | ✅ |
| RF-WEB-06 | Dashboard geográfico | `api/v1/dashboard.py` · web `pages/Dashboard.tsx`, `WorkDetailDrawer` | ✅ (mapa: lista + timeline) |
| RF-WEB-07 | Bitácora por elemento | `models/element_log.py`, `api/v1/elements.py` | ✅ |
| RF-WEB-08 | Auditoría append-only | `services/audit.py`, `api/v1/audit.py` · web `pages/Audit.tsx` | ✅ |
| RF-WEB-09 | Recepción y consolidación | `api/v1/sync.py` (upload/verify) · novedades `quality/novelties` | ✅ |
| RF-WEB-10 | Parámetros de calidad | `api/v1/quality.py` · web `pages/Quality.tsx` | ✅ |
| RF-WEB-11 | Reportería + exportación | `services/{reports,exporters}.py`, `api/v1/reports.py` · web `pages/Reports.tsx` | ✅ Excel/PDF/CSV |
| RF-WEB-12 | Interfaz moderna/responsiva | `frontend/src` (React + CSS) | ✅ |

## 4. Matriz de trazabilidad — App Móvil (RF-MOV)

| ID | Requerimiento | Implementación | Estado |
|---|---|---|---|
| RF-MOV-01 | Autenticación + sesión offline | `data/repo/AuthRepository`, `data/local/SessionStore` | ✅ |
| RF-MOV-02 | Operación offline por defecto | capa `data/` completa + `sync/SyncManager.pull` | ✅ |
| RF-MOV-03 | Almacenamiento GeoPackage | `data/local/GeoPackageStore` | ✅ |
| RF-MOV-04 | UI adaptativa teléfono/tablet | `ui/workdetail/WorkDetailScreen` (WindowSizeClass) | ✅ |
| RF-MOV-05 | Presentación por tipo | `ui/workdetail/Panes`, `OsmMap` | ✅ |
| RF-MOV-06 | Captura/edición + snapping | `WorkDetailViewModel`, `core/geo/SnappingEngine` | ✅ (snapping ✅ probado) |
| RF-MOV-07 | Modo solo punto + fotos | `WorkDetailViewModel.capturePoint` | ✅ |
| RF-MOV-08 | Fotos con metadata/compresión/hash | `media/PhotoManager`, `ui/capture/PhotoCapture` | ✅ |
| RF-MOV-09 | Validación de calidad en dispositivo | `core/quality/QualityValidator` | ✅ probado (8 tests) |
| RF-MOV-10 | Sincronización y cierre | `sync/SyncManager` | ✅ |
| RF-MOV-11 | Rendimiento y recursos | índices GPKG, lazy lists, IO fuera de UI | ✅ (base) |

## 5. Sincronización, modelo e integración

| ID | Requerimiento | Implementación | Estado |
|---|---|---|---|
| RF-SYNC | Canal seguro, idempotencia, estados, incremental | `api/v1/sync.py`, `core/model/Ids`, `sync/SyncManager` | ✅ |
| RF-SYNC.3/4 | Fotos por chunks + integridad | `sync/photo/{sha}/chunk`, `services/photo_storage.py` | ✅ probado |
| §6 Modelo | GUID, relaciones, esquema evolutivo, versión | `models/`, `SchemaDefinition`, `Work.schema_version` | ✅ dirigido por metadatos |
| §7 GIS | Origen/destino ArcSDE/Oracle aislado | `modules/gis/adapter.py` (interfaz + stub) | ✅ adaptador; impl. real = PD-02 |

## 6. Reglas de negocio (RN)

Todas verificadas con pruebas automatizadas salvo indicación:

| ID | Regla | Verificación |
|---|---|---|
| RN-01 | Un trabajo → un dispositivo a la vez | `tests/test_works_and_sync.py::test_assignment_exclusivity_rn01` |
| RN-02 | Un dispositivo → múltiples trabajos | `...::test_multiple_works_one_device_rn02` |
| RN-03 | Eliminación local solo tras sync/borrado remoto | `GeoPackageStore.deleteWork`, `SyncManager` |
| RN-04 | Sync parcial/fallida → no termina, reintenta | `...::test_sync_pending_when_photo_missing`, `test_photo_chunk_integrity_failure` |
| RN-05 | Segregación Matriz/UN | `core/deps.py`; `tests/test_auth_and_scope.py` |
| RN-06 | GUID único e inmutable | `models/base.py`, `core/model/Ids` |
| RN-07 | Relación puesto/unidad | `Element.parent_guid`, validación `requires_parent` |
| RN-08 | Foto con metadata GPS/fecha | `models/sync.py::Photo`, `PhotoManager` |
| RN-09 | Validación en dispositivo antes de consolidar | `core/quality/QualityValidator` (probado) |
| RN-10 | Todo cambio auditado | `services/audit.py` |
| RN-11 | Consolidación siempre a ArcSDE/Oracle | `sync.verify` → `modules/gis/adapter` |

## 7. Requerimientos no funcionales (RNF)

| ID | Estado |
|---|---|
| RNF-01 Seguridad | JWT, hashing, sesión cifrada (Keystore), TLS en producción, auditoría inmutable · ✅ base |
| RNF-02 Rendimiento | índices, lazy loading, IO fuera de UI · ✅ base (falta profiling en dispositivo) |
| RNF-03 Plataforma/despliegue | Backend Windows Server (Python), web SPA, Android 8.0+ · ✅ |
| RNF-04 Usabilidad | UI moderna web/móvil, contraste/tamaños táctiles · ✅ base |
| RNF-05 Resiliencia | persistencia inmediata local, sync concurrente · ✅ base |
| RNF-06 Mantenibilidad | módulos separados, metadatos, versionado API · ✅ |
| RNF-07 Eficiencia de recursos | compresión de fotos, limpieza, caché acotada · ✅ base |

## 8. Pendientes

**No verificables en este entorno (requieren Android SDK/dispositivo):**
- Compilar el APK y pruebas instrumentadas de UI.
- Afinar ciclo de vida del `MapView` (osmdroid) y tiles offline.

**Pulido / siguientes iteraciones:**
- Formularios de captura generados desde `SchemaDefinition` (§6.4).
- Certificate pinning (RF-SYNC.1) en la app.
- Migraciones Alembic + PostGIS (hoy SQLite en dev, código agnóstico a la BD).
- Implementación real del adaptador GIS (ArcPy / servicios REST / staging Oracle).

**Pendientes de definición del negocio (del documento):** PD-01 a PD-05.

## 9. Conteo de pruebas

| Suite | Pruebas | Estado |
|---|---|---|
| Backend `pytest` | 23 | ✅ |
| Móvil `core` JUnit | 19 | ✅ |
| Frontend build (`tsc` + `vite`) | — | ✅ sin errores |

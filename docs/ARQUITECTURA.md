# Arquitectura — Sistema de Levantamiento Eléctrico en Campo

> Diseño de la solución completa (backend, web y móvil).
> Referencia: `REQUERIMIENTOS_Sistema_Levantamiento_Electrico.md`.
> Estado de implementación y trazabilidad detallada: [`ESTADO.md`](ESTADO.md).

## 1. Visión general

La solución se compone de tres piezas que comparten contratos; las tres están
implementadas a nivel de base funcional:

```
        ┌────────────────────┐        ┌────────────────────┐
        │  WEB-ADMIN (React) │        │ APP-CAMPO (Android)│
        │  SPA administración│        │  Kotlin, offline   │
        └─────────┬──────────┘        └─────────┬──────────┘
                  │ HTTPS/JWT                    │ HTTPS/JWT (sync)
                  └──────────────┬───────────────┘
                        ┌────────▼─────────┐
                        │   BACKEND API    │
                        │  FastAPI/Python  │
                        └───┬─────────┬────┘
              ┌─────────────┘         └──────────────┐
     ┌────────▼─────────┐               ┌────────────▼───────────┐
     │  BD del sistema  │               │  Adaptador GIS (aislado)│
     │ Postgres/PostGIS │               │  → ArcSDE / Oracle      │
     └──────────────────┘               └────────────────────────┘
```

Principio rector (RNF-06): **arquitectura modular**. Cada capacidad
(asignación, sincronización, validación, integración GIS, reportería) vive en su
propio módulo, desacoplada del resto.

## 2. Backend — capas

| Capa | Ubicación | Responsabilidad |
|---|---|---|
| Configuración | `core/config.py` | Settings por entorno (Pydantic). |
| Persistencia | `core/database.py`, `models/` | Engine/sesión + modelos ORM. |
| Seguridad | `core/security.py` | JWT, hashing, política de contraseñas. |
| Acceso (RBAC) | `core/deps.py` | Usuario actual + **segregación Matriz/UN**. |
| Contratos | `schemas/` | Validación y serialización (Pydantic). |
| API | `api/v1/` | Endpoints REST por recurso. |
| Servicios | `services/` | Lógica transversal (auditoría). |
| Integración GIS | `modules/gis/` | Adaptador ArcSDE/Oracle reemplazable. |

## 3. Modelo de datos

Entidades principales (todas con `id` GUID — RN-06 — y `created_at/updated_at`):

- **BusinessUnit** — Matriz y UN; raíz de la segregación (RN-05).
- **User** — usuarios web y funcionarios de campo; `role`, `auth_type`, `un_id`.
- **Device** — dispositivo autorizado, vinculado a funcionario + UN.
- **Work** — trabajo; `work_type`, `status`, `un_id`, `device_id`,
  `schema_version`, `sector_geojson`, `validation_result`.
- **WorkElement** — elementos empaquetados en un trabajo (geometría + atributos).
- **Element** — elemento del modelo eléctrico (GUID), `parent_guid` (RN-07).
- **ElementLog** — bitácora por GUID (RF-WEB-07).
- **QualityParamSet** / **SchemaDefinition** — parámetros de calidad y esquema,
  **versionados** y dirigidos por metadatos (§6.4/6.5).
- **SyncPackage** / **Photo** / **RemoteDeleteOrder** — sincronización (RF-SYNC).
- **AuditLog** — registro append-only inmutable (RF-WEB-08, RN-10).

### Decisiones de diseño

- **Geometrías como GeoJSON de texto** para mantener el código agnóstico a la BD
  y ejecutable con SQLite en desarrollo. En producción se mapean a columnas
  `geometry` de **PostGIS** con índices espaciales (equivalente al GPKG del móvil).
- **Modelado dirigido por metadatos** (§6.4): las capas, formularios y reglas de
  calidad se derivan de `SchemaDefinition`/`QualityParamSet` versionados, no de
  código rígido — absorbe la evolución del esquema sin reingeniería.
- **Versión de esquema por trabajo** (`Work.schema_version`) para compatibilidad
  en sincronización (§6.5).

## 4. Seguridad y control de acceso

- **Doble mecanismo de login** (RF-WEB-01): local (usuario/clave con política y
  bloqueo por intentos) y corporativo (delegación AD/LDAP/SSO, habilitable —
  pendiente PD-05). Login móvil valida **funcionario + dispositivo autorizado**
  (RF-MOV-01).
- **JWT** access + refresh; claims con `role` y `un_id`.
- **Segregación Matriz/UN a nivel backend** (regla obligatoria §2.1, RN-05):
  - `scope_un_filter()` limita las **consultas de lista** a la UN del usuario.
  - `enforce_un_scope()` bloquea el **acceso puntual** a datos de otra UN (403).
  - Los roles Matriz (`ADMIN`, `OPERATOR_MATRIZ`, `VIEWER_MATRIZ`) ven todo.
  Se aplica en cada endpoint, no solo en la interfaz.
- **Auditoría append-only**: toda operación relevante registra usuario, rol,
  acción, entidad, valores previo/nuevo, UN, IP y dispositivo.

## 5. Ciclo de vida del trabajo y sincronización

Estados (RF-SYNC.6):

```
CREATED → ASSIGNED → DOWNLOADED → IN_PROGRESS → SYNCING →
          SYNCED/WITH_ISSUES → COMPLETED
                    │
                    └→ SYNC_PENDING (fallo/parcial) ──(reintento)──┘
```

Reglas de negocio garantizadas por la API:

- **RN-01** exclusividad: un trabajo → un dispositivo (409 si ya asignado).
- **RN-02** multiplicidad: un dispositivo → múltiples trabajos.
- **RF-WEB-04.7** reasignación solo tras **borrado remoto confirmado** (libera
  `device_id`).
- **RN-04** si falta cualquier foto o falla la consolidación, el trabajo queda
  `SYNC_PENDING`; **no** se termina y se reintenta todo el proceso.
- **RF-SYNC.5** idempotencia por `idempotency_key`: reintentos no duplican.
- Al verificar completitud, se persisten los elementos, se registra la **bitácora**
  y se **consolida** hacia ArcSDE/Oracle vía el adaptador (RN-11).

## 6. Integración GIS (aislada) — §7

`app/modules/gis/adapter.py` define la interfaz `GISAdapter`:

- `extract_by_sector` / `extract_by_guids` — **origen** de trabajos (§7.1).
- `consolidate` — **destino**: carga de resultados verificados preservando GUIDs
  y relaciones puesto/unidad, con `staging_ref` reversible (§7.2/7.4).

`StubGISAdapter` simula el comportamiento para desarrollo/pruebas. La
implementación real (ArcPy, servicios REST de ArcGIS, o staging en tablas Oracle
con aprobación — PD-02) se coloca detrás de esta interfaz **sin tocar el resto
del sistema**.

## 7. Trazabilidad requerimiento → implementación

| Requerimiento | Implementación |
|---|---|
| RF-WEB-01 | `api/v1/auth.py`, `core/security.py` |
| RF-WEB-02 | `api/v1/users.py`, `business_units.py`, `devices.py` |
| RF-WEB-03/04 | `api/v1/works.py` (`create_work`, `assign_works`) |
| RF-WEB-05 | `works.remote_delete`, `sync.confirm_remote_delete` |
| RF-WEB-06 | `api/v1/dashboard.py` |
| RF-WEB-07 | `models/element_log.py`, `api/v1/elements.py` |
| RF-WEB-08 | `services/audit.py`, `models/audit_log.py`, `api/v1/audit.py` |
| RF-WEB-09 | `api/v1/sync.py` (`upload`, `verify`) |
| RF-WEB-10 | `api/v1/quality.py` |
| RF-MOV-01 | `auth.mobile_login` |
| RF-MOV-02/10 | `sync.pull`, `sync.verify` |
| RF-MOV-09 | `SyncPackage.validation_result` + reporte |
| RF-SYNC | `api/v1/sync.py` (idempotencia, estados, incremental) |
| §6 modelo | `models/`, `SchemaDefinition`, `schema_version` |
| §7 GIS | `modules/gis/adapter.py` |
| RN-01..11 | ver §5 y tabla anterior; verificado en `tests/` |

## 8. Pendientes de definición (del documento)

PD-01 (validación fallida ¿bloquea o marca?), PD-02 (versiones ArcGIS/Oracle),
PD-03 (esquema eléctrico), PD-04 (formato parámetros de calidad), PD-05 (auth
corporativa). El diseño dirigido por metadatos y el adaptador GIS aislado
permiten cerrar estos puntos sin reingeniería.

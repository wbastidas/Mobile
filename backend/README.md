# Backend — Sistema de Levantamiento Eléctrico en Campo

API REST (FastAPI + SQLAlchemy) que sirve de base compartida a la **Plataforma
Web de Administración (WEB-ADMIN)** y a la **App Móvil de Campo (APP-CAMPO)**.

Esta es la **primera iteración**: *Backend API + Modelo de datos*. Implementa el
núcleo funcional descrito en el documento de requerimientos (autenticación,
usuarios/roles/UN, dispositivos, trabajos, asignación, borrado remoto,
sincronización, validación de calidad, bitácora, auditoría, dashboard e
integración GIS aislada).

## Stack

- **Python 3.11** · **FastAPI** · **SQLAlchemy 2.0** · **Pydantic v2**
- Autenticación **JWT** (access + refresh) con hashing `pbkdf2_sha256`.
- BD: **SQLite** en desarrollo (cero configuración); **PostgreSQL + PostGIS** en
  producción (geometrías, índices espaciales). El código es agnóstico a la BD:
  las geometrías se guardan como GeoJSON de texto, mapeables a `geometry` PostGIS.
- Integración con **ArcSDE/Oracle** aislada en un módulo adaptador (`app/modules/gis`).

## Puesta en marcha

```bash
cd backend
python -m pip install -r requirements.txt
cp .env.example .env            # opcional; hay valores por defecto

python -m app.seed              # datos de demostración
uvicorn app.main:app --reload   # API en http://localhost:8000
```

- Documentación interactiva (Swagger): **http://localhost:8000/docs**
- Salud del servicio: **http://localhost:8000/health**

### Usuarios de demostración (clave `Campo2026!`)

| Usuario       | Rol               | Ámbito     |
|---------------|-------------------|------------|
| `admin`       | Administrador     | Global     |
| `op.matriz`   | Operador Matriz   | Global     |
| `op.norte`    | Operador UN       | UN-NORTE   |
| `view.sur`    | Visualizador UN   | UN-SUR     |
| `campo.norte` | Funcionario campo | UN-NORTE   |

Dispositivo de demo: `ANDROID-DEMO-001` (vinculado a `campo.norte`, UN-NORTE).

## Pruebas

```bash
python -m pytest -q
```

23 pruebas que cubren: login y bloqueo por intentos, segregación Matriz/UN,
exclusividad de asignación (RN-01/02), borrado remoto + reasignación, flujo
completo de sincronización, idempotencia, subida de fotos por chunks con
verificación de integridad, novedades de calidad por regla y reportería con
exportación (Excel/PDF/CSV).

## Estructura

```
backend/app
├── main.py              # arranque FastAPI, CORS, health
├── core/                # config, base de datos, seguridad, enums, dependencias RBAC
├── models/              # modelos SQLAlchemy (dominio)
├── schemas/             # esquemas Pydantic (I/O de la API)
├── services/            # servicios (auditoría)
├── api/v1/              # endpoints por recurso + router agregador
├── modules/gis/         # adaptador aislado ArcSDE/Oracle (§7)
└── seed.py              # datos de demostración
```

## Mapa de endpoints ↔ requerimientos

| Recurso | Endpoints | Requerimiento |
|---|---|---|
| `auth` | login web/móvil, refresh, me | RF-WEB-01, RF-MOV-01 |
| `business-units` | CRUD UN | RF-WEB-02.2 |
| `users` | CRUD usuarios, contraseña | RF-WEB-02.1 |
| `devices` | registro/gestión dispositivos | RF-WEB-02.3 |
| `works` | crear/listar, asignar, borrado remoto | RF-WEB-03/04/05 |
| `sync` | pull, upload, **photo/{sha}/chunk**, verify, confirm-delete | RF-SYNC, RF-MOV-09/10 |
| `quality` | parámetros, esquema, **novedades por regla** | RF-WEB-10, RF-WEB-09.2, §6.4 |
| `elements` | elemento + bitácora por GUID | RF-WEB-07 |
| `audit` | consulta de auditoría | RF-WEB-08 |
| `dashboard` | resumen, mapa, línea de tiempo | RF-WEB-06 |
| `reports` | reportes + exportación Excel/PDF/CSV | RF-WEB-11 |

Ver `docs/ARQUITECTURA.md` (diseño) y `docs/ESTADO.md` (trazabilidad completa).

## Próximas iteraciones

1. Migraciones **Alembic** + PostGIS (hoy SQLite en dev; código agnóstico a la BD).
2. Implementación real del adaptador GIS (ArcPy / servicios REST / staging Oracle).
3. Autenticación corporativa (AD/LDAP/SSO) según infraestructura (PD-05).

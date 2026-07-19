# Sistema de Gestión y Levantamiento de Datos Eléctricos en Campo

Solución empresarial para el levantamiento y gestión de datos de redes de
distribución eléctrica (postes y elementos relacionados), compuesta por:

1. **Backend API** — Base compartida (FastAPI/Python) con integración a la
   geodatabase corporativa **ArcSDE/Oracle**. ✅ *Implementado.*
2. **WEB-ADMIN** — Plataforma web de administración (asignación, monitoreo,
   auditoría, reportería) en **React + TypeScript**. ✅ *Implementado.*
3. **APP-CAMPO** — App **Android nativa (Kotlin)** para levantamiento offline
   sobre GeoPackage. ✅ *Implementado (base funcional).*

## Estado actual

Los **tres componentes** están implementados a nivel de base funcional y con
contratos compartidos: autenticación doble mecanismo, gestión de usuarios/roles/UN
y dispositivos, los tres tipos de trabajo, asignación con reglas de exclusividad,
borrado remoto, sincronización idempotente con **fotos por chunks verificadas por
hash**, validación de calidad en dispositivo con **novedades a nivel de regla**,
bitácora por elemento, auditoría append-only, dashboard con detalle por trabajo,
**reportería con exportación a Excel/PDF/CSV**, app móvil offline sobre GeoPackage
con UI adaptativa, **snapping**, **mapa (osmdroid)** y **cámara real**, e
integración GIS aislada hacia ArcSDE/Oracle.

Verificación en este entorno: **23 pruebas backend (`pytest`)**, **19 del núcleo
móvil (`core`, JUnit)** y **build del frontend** (`tsc` + `vite`) en verde. La app
Android completa se compila en Android Studio (no hay Android SDK en CI).

➡️ **Estado detallado y matriz de trazabilidad:** [`docs/ESTADO.md`](docs/ESTADO.md)
➡️ **Diseño de arquitectura:** [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)

## Inicio rápido

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload   # http://localhost:8000/docs
python -m pytest                # 23 pruebas
```

## Estructura del repositorio

```
.
├── backend/                 # API FastAPI + modelo de datos + pruebas pytest
├── frontend/                # WEB-ADMIN: SPA React + TypeScript (Vite)
├── mobile/                  # APP-CAMPO: Android nativo (Kotlin)
│   ├── core/                # Kotlin puro (validación de calidad) + tests JUnit
│   └── app/                 # app Android (Compose, MVVM, sync offline)
├── docs/                    # ARQUITECTURA.md (diseño) · ESTADO.md (trazabilidad)
└── REQUERIMIENTOS_*.md      # documento de requerimientos (insumo)
```

Guías por componente: [`backend/README.md`](backend/README.md) ·
[`frontend/README.md`](frontend/README.md) · [`mobile/README.md`](mobile/README.md).

## Tecnología

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, JWT,
  openpyxl/reportlab. BD SQLite en desarrollo → PostgreSQL/PostGIS en
  producción (Windows Server).
- **Frontend:** React 18 + TypeScript, Vite, React Query, Axios.
- **Móvil:** Android nativo (Kotlin 2.0), Jetpack Compose, GeoPackage offline,
  Retrofit, osmdroid. Módulo `core` en Kotlin puro con pruebas JUnit.
- **GIS:** adaptador aislado hacia ArcSDE/Oracle (ArcPy / servicios REST).

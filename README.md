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

Esta primera iteración entrega el **Backend API + modelo de datos**, núcleo del
que dependen la web y el móvil. Cubre autenticación de doble mecanismo,
gestión de usuarios/roles/UN, dispositivos, los tres tipos de trabajo,
asignación con reglas de exclusividad, borrado remoto, sincronización con
idempotencia y verificación de completitud, validación de calidad, bitácora por
elemento, auditoría append-only, dashboard e integración GIS aislada.

➡️ **Guía de uso, pruebas y endpoints:** [`backend/README.md`](backend/README.md)
➡️ **Diseño y trazabilidad de requerimientos:** [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)

## Inicio rápido

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload   # http://localhost:8000/docs
python -m pytest                # 11 pruebas
```

## Estructura del repositorio

```
.
├── backend/                 # API FastAPI + modelo de datos + pruebas pytest
├── frontend/                # WEB-ADMIN: SPA React + TypeScript (Vite)
├── mobile/                  # APP-CAMPO: Android nativo (Kotlin)
│   ├── core/                # Kotlin puro (validación de calidad) + tests JUnit
│   └── app/                 # app Android (Compose, MVVM, sync offline)
├── docs/                    # documentación de arquitectura
└── REQUERIMIENTOS_*.md      # documento de requerimientos (insumo)
```

Guías por componente: [`backend/README.md`](backend/README.md) ·
[`frontend/README.md`](frontend/README.md) · [`mobile/README.md`](mobile/README.md).

## Tecnología

- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, JWT.
  BD SQLite en desarrollo → PostgreSQL/PostGIS en producción (Windows Server).
- **Frontend (próximo):** React + TypeScript.
- **Móvil (próximo):** Android nativo (Kotlin), GeoPackage offline.
- **GIS:** adaptador aislado hacia ArcSDE/Oracle (ArcPy / servicios REST).

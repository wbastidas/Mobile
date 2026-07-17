# WEB-ADMIN — Frontend (React + TypeScript)

SPA de administración del Sistema de Levantamiento Eléctrico. Consume el
Backend API (`../backend`). Diseño moderno y responsivo (RF-WEB-12).

## Stack

- **React 18 + TypeScript**, **Vite**.
- **React Router** (rutas protegidas por rol), **TanStack Query** (datos),
  **Axios** (cliente con JWT + refresh automático).

## Puesta en marcha

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxy /api -> http://localhost:8000)
```

Requiere el backend corriendo (`uvicorn app.main:app --reload` en `../backend`)
y datos semilla (`python -m app.seed`). Ingrese con, p. ej., `admin` / `Campo2026!`.

## Scripts

| Comando | Acción |
|---|---|
| `npm run dev` | Servidor de desarrollo con proxy al backend. |
| `npm run build` | Typecheck (`tsc`) + build de producción. |
| `npm run preview` | Sirve el build de producción. |
| `npm run typecheck` | Solo verificación de tipos. |

## Estructura

```
src/
├── main.tsx            # bootstrap (Router, React Query, Auth)
├── App.tsx             # rutas protegidas por rol
├── types.ts            # tipos alineados con el backend
├── api/                # cliente axios (JWT/refresh) + endpoints tipados
├── auth/               # contexto de autenticación
├── components/         # Layout, UI (badges, headers)
└── pages/              # Login, Dashboard, Trabajos, Dispositivos,
                        # Usuarios, Parámetros de calidad, Auditoría
```

## Pantallas y requerimientos

| Pantalla | Requerimiento |
|---|---|
| Login | RF-WEB-01 |
| Dashboard (resumen, activos, por estado/tipo) | RF-WEB-06 |
| Trabajos (crear, asignar, borrado remoto) | RF-WEB-03/04/05 |
| Dispositivos (registro/gestión) | RF-WEB-02.3 |
| Usuarios (rol + UN) | RF-WEB-02.1 |
| Parámetros de calidad (versionado) | RF-WEB-10 |
| Auditoría (append-only, filtrable) | RF-WEB-08 |

La visibilidad de menús y acciones respeta el rol (Matriz/UN, operador/visualizador);
la **segregación de datos se garantiza además en el backend** (RN-05).

## Próximos pasos

- Mapa interactivo (Leaflet/MapLibre) con los polígonos de sector y elementos.
- Línea de tiempo por trabajo y bitácora por elemento (endpoints ya disponibles).
- Reportería con exportación (RF-WEB-11).

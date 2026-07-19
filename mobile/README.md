# APP-CAMPO — Aplicación Móvil Android (Kotlin)

App **Android nativa** para el levantamiento y edición de datos eléctricos en
campo, con **operación offline por defecto** (RF-MOV-01…11). Consume el mismo
Backend API (`../backend`) que la plataforma web.

## Stack

- **Kotlin 2.0**, **Jetpack Compose** (Material 3), **MVVM**.
- **Coroutines/Flow**, **Retrofit + OkHttp** (sync), **kotlinx.serialization**.
- **SQLite/GeoPackage** para almacenamiento local; **EncryptedSharedPreferences**
  (Android Keystore) para la sesión cifrada offline.
- `minSdk 26` (Android 8.0+), `targetSdk 34` (RNF-03).

## Módulos

```
mobile/
├── core/          # Kotlin puro (SIN Android): modelos, GUID, motor de
│                  # validación de calidad y DTOs de sync. Probado con JUnit.
└── app/           # Aplicación Android (Compose + capas de datos/sync/UI).
```

El módulo **`core`** se puede compilar y **probar sin el SDK de Android**:

```bash
cd mobile/core
gradle test          # o: ../gradlew :core:test  (con Android SDK configurado)
```

> Las 8 pruebas del motor de validación de calidad (RF-MOV-09) se ejecutan y
> pasan de forma independiente. Es la lógica más crítica de la app.

## Compilar la app completa

Requiere el **SDK de Android** (Android Studio Ladybug o superior). Cree
`mobile/local.properties` con la ruta del SDK y abra `mobile/` en Android Studio:

```properties
sdk.dir=/ruta/a/Android/Sdk
```

Luego: `./gradlew :app:assembleDebug` (o Run ▶ desde Android Studio).
La URL del backend se configura en `app/build.gradle.kts`
(`API_BASE_URL`; por defecto `http://10.0.2.2:8000/api/v1/` para el emulador).

## Arquitectura y requerimientos

| Componente | Ruta | Requerimiento |
|---|---|---|
| Login funcionario + dispositivo | `data/repo/AuthRepository`, `ui/login` | RF-MOV-01 |
| Sesión cifrada offline | `data/local/SessionStore` | RF-MOV-01.3, RNF-01 |
| Almacenamiento GeoPackage | `data/local/GeoPackageStore` | RF-MOV-03 |
| Operación offline | toda la capa de datos | RF-MOV-02, RNF-05 |
| UI adaptativa teléfono/tablet | `ui/workdetail/WorkDetailScreen` | RF-MOV-04 |
| Presentación por tipo de trabajo | `ui/workdetail/Panes` | RF-MOV-05 |
| Captura/edición + observaciones | `ui/workdetail` (CaptureForm) | RF-MOV-06 |
| GUID generado en dispositivo | `core/model/Ids` | RF-MOV-06.5, RN-06 |
| Modo solo punto + fotos | `WorkDetailViewModel.capturePoint` | RF-MOV-07 |
| Fotos con metadata/compresión/hash | `media/PhotoManager` | RF-MOV-08, RN-08 |
| Validación de calidad en dispositivo | `core/quality/QualityValidator` | RF-MOV-09 |
| Reporte de novedades por regla | `core/quality/ReportMapper` → `ValidationReportDto` | RF-WEB-09.2 |
| Snapping a elementos existentes | `core/geo/SnappingEngine` | RF-MOV-06.2 |
| Mapa interactivo (sector + elementos) | `ui/workdetail/OsmMap` (osmdroid) | RF-MOV-04/05 |
| Captura de foto con cámara real | `ui/capture/PhotoCapture` | RF-MOV-08 |
| Geometría para el mapa (GeoJSON) | `core/geo/GeoJson` | RF-MOV-05 |
| Sincronización y cierre | `sync/SyncManager` | RF-MOV-10, RF-SYNC |
| Idempotencia de sync | `core/model/Ids.idempotencyKey` | RF-SYNC.5 |

## Flujo de sincronización (`SyncManager`)

1. **pull** — descarga incremental: trabajos, órdenes de borrado remoto y
   parámetros de calidad vigentes (RF-SYNC.7).
2. **syncWork** — valida localmente (RF-MOV-09) → sube el paquete idempotente →
   sube fotos por chunks verificando integridad (RF-SYNC.3/4) → **verifica
   completitud** y consolida (RF-MOV-10.2).
3. Ante **cualquier** fallo o foto faltante, el trabajo queda `SYNC_PENDING` y
   todo el proceso se reintenta (RN-04). La eliminación local **solo** ocurre
   tras sincronización confirmada o por borrado remoto (RN-03).

## Pendientes / próximos pasos

- **Mapa** (`OsmMap`, osmdroid) y **cámara** (`PhotoCapture`) ya integrados; se
  compilan y prueban en dispositivo/emulador con Android Studio. Falta afinar el
  ciclo de vida del `MapView` (onResume/onPause) y tiles offline.
- Generación de formularios desde `SchemaDefinition` (§6.4) en la captura.
- Certificate pinning (RF-SYNC.1) y pruebas instrumentadas de UI.

> Nota: `gradle-wrapper.jar` se incluye para reproducibilidad. Si su entorno lo
> regenera, use `gradle wrapper --gradle-version 8.14.3`.

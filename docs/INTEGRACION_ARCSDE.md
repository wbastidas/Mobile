# Análisis — Integración final con ArcSDE/Oracle (subida de cambios)

> Cubre la sección §7 del documento de requerimientos y el pendiente **PD-02**
> (versiones exactas de ArcGIS Desktop, ArcSDE y Oracle).
> Estado: **staging reversible implementado y probado**; el conector físico de
> carga se elige al cerrar PD-02 (comparativa abajo).

## 1. El problema

Los resultados verificados de campo deben **consolidarse** en la geodatabase
corporativa (ArcSDE sobre Oracle, gestionada con ArcGIS Desktop) cumpliendo:

- preservar **GUIDs** y relaciones **puesto/unidad** (§7.2, RN-06/07),
- carga **auditada y reversible** con respaldo/staging previo (§7.4),
- posibilidad de **revisión previa por un operador** (RF-WEB-09.4),
- todo **aislado en un módulo adaptador** para no acoplar el sistema (§7.3, RNF-06).

Una escritura directa desde la API hacia ArcSDE violaría los cuatro puntos: sin
revisión, sin reversibilidad, y acoplando el backend a las librerías ArcGIS.

## 2. Arquitectura implementada: staging con aprobación

```
 App móvil ──sync/verify──► Backend ──consolidate()──► GIS Adapter (aislado)
                                                          │
                                              ┌───────────▼───────────┐
                                              │  LOTE DE STAGING      │
                                              │  gis_staging_batches  │  PENDING_REVIEW
                                              │  gis_staging_elements │  (GUID + padre +
                                              └───────────┬───────────┘   geometría + attrs)
                                   Operador (web)         │
                              ┌── approve ──► LOADED ─────┤──► [Conector físico → ArcSDE/Oracle]
                              └── rollback ─► ROLLED_BACK ┘        (PD-02, ver §3)
```

- `modules/gis/adapter.py` — interfaz `GISAdapter` (contrato estable).
- `modules/gis/staging.py` — `StagingGISAdapter`: `consolidate()` crea el lote
  **en la misma transacción** de la sincronización (atómico: o se registra el
  trabajo Y su lote, o ninguno).
- `api/v1/gis.py` — endpoints de operador: listar (con segregación Matriz/UN),
  detalle, `approve` (dispara la carga real) y `rollback`. Toda decisión queda
  auditada (RN-10).
- Selección por configuración: `GIS_ADAPTER=staging` (default) | `stub` (pruebas).

**Verificación:** 4 pruebas (`tests/test_gis_staging.py`) — creación del lote al
sincronizar con GUID/atributos preservados, aprobación única + auditoría,
rollback y segregación por UN.

## 3. Conector físico de carga (a decidir con PD-02)

Cuando un lote pasa a `LOADED`, algo debe escribir en ArcSDE/Oracle. Opciones:

| Criterio | A) ArcPy / geoprocesamiento | B) ArcGIS REST (Feature Services) | C) Tablas Oracle + job PL/SQL |
|---|---|---|---|
| Requisitos | Lic. ArcGIS + Python de ArcGIS en el servidor | ArcGIS Server/Enterprise publicado | Solo cliente Oracle (python-oracledb) |
| Respeta versionado SDE / archivado | ✅ nativo (`edit sessions`, reconcile/post) | ✅ vía applyEdits sobre capa versionada | ⚠️ NO toca las tablas delta de SDE de forma soportada |
| Relaciones puesto/unidad (relationship classes) | ✅ nativo | ✅ si el servicio las expone | ⚠️ manual, frágil |
| GUIDs preservados | ✅ | ✅ (`useGlobalIds=true`) | ✅ |
| Complejidad operativa | Media (proceso separado, agenda/cola) | Baja (HTTP puro desde el backend) | Media-alta + riesgo de corromper SDE |
| Riesgo | Bajo | Bajo-medio (depende de publicación) | **Alto** (escribir SDE por debajo no está soportado por Esri) |

**Recomendación:**

1. **Preferida — B (ArcGIS REST `applyEdits`)** si la organización tiene ArcGIS
   Server/Enterprise: el backend consume HTTP puro (sin dependencias Esri en
   Python), con `useGlobalIds=true` para preservar GUIDs y rollback nativo
   (`rollbackOnFailure`). El conector es una clase más detrás de `approve`.
2. **Alternativa — A (ArcPy)** si solo hay ArcGIS Desktop: un *worker* separado
   (no dentro de la API) lee lotes `LOADED` pendientes de carga y ejecuta el
   geoprocesamiento con `arcpy.da.Editor` (edit session → insert/update por
   GUID → reconcile/post de la versión). El worker corre donde está licenciado
   ArcGIS, desacoplado del backend por la propia tabla de staging.
3. **Descartada — C**: escribir directamente las tablas SDE en Oracle no es un
   mecanismo soportado y puede corromper el versionado/archivado.

En ambas opciones viables, la tabla de staging ya implementada es el **buffer y
el registro de reversibilidad**: la carga física es idempotente por lote
(reintentable) y `rollback` revierte antes de cargar, o dispara la edición
inversa después (los valores previos pueden snapshotearse en el lote al
extenderlo con `old_values`).

## 4. Flujo extremo a extremo (con estados)

1. Campo sincroniza → `sync/verify` valida completitud → trabajo `COMPLETED`.
2. En la misma transacción, `StagingGISAdapter.consolidate()` crea el lote
   `PENDING_REVIEW` con los elementos (GUID, padre, geometría, atributos).
3. Operador revisa en la web (`GET /gis/staging`, detalle por lote).
4. `approve` → `LOADED` + auditoría → el conector físico (A o B) aplica los
   cambios en ArcSDE/Oracle preservando GUIDs/relaciones (RN-11).
5. `rollback` → `ROLLED_BACK` + auditoría; el lote nunca llega a la geodatabase.

## 5. Información pendiente para cerrar PD-02

- Versiones exactas: ArcGIS Desktop/Pro, ArcSDE/geodatabase enterprise, Oracle.
- ¿Existe ArcGIS Server/Enterprise con Feature Services publicables? (decide A vs B)
- ¿La geodatabase usa versionado tradicional o branch versioning? ¿Archivado?
- Nombre de las feature classes / relationship classes del modelo eléctrico
  (alimenta también `SchemaDefinition`, PD-03).
- Cuenta de servicio y permisos mínimos hacia Oracle/ArcGIS (RNF-01: mínimo
  privilegio).

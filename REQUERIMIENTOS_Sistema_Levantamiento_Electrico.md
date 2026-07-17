# Documento de Requerimientos de Software
# Sistema de Gestión y Levantamiento de Datos Eléctricos en Campo

**Versión:** 1.0
**Fecha:** Julio 2026
**Estado:** Borrador para desarrollo
**Audiencia:** Equipo de desarrollo (documento preparado para implementación asistida con Claude Code)

---

## 1. Introducción

### 1.1 Propósito
Este documento define los requerimientos funcionales y no funcionales de una solución empresarial compuesta por:

1. **Plataforma Web de Administración (WEB-ADMIN):** aplicación web moderna para asignación de trabajos, monitoreo, auditoría y reportería, desplegable en servidores Windows.
2. **Aplicación Móvil de Campo (APP-CAMPO):** aplicación **Android nativa** para el levantamiento y edición de datos eléctricos en campo, con operación **offline por defecto**.

### 1.2 Alcance del negocio
La empresa opera con una **Matriz** (oficina central) y múltiples **Unidades de Negocio** (UN) distribuidas geográficamente. El dominio de datos gira en torno a **postes eléctricos y elementos relacionados** de redes de distribución eléctrica (transformadores, luminarias, seccionadores, tramos de red, acometidas, etc., según el modelo eléctrico vigente).

El repositorio corporativo final es una geodatabase empresarial **ArcSDE sobre Oracle**, gestionada con **ArcGIS Desktop**. De esta base se **extrae** la información geográfica y atributiva para armar los trabajos, y hacia ella se **consolidan** los resultados sincronizados y validados.

### 1.3 Definiciones y acrónimos

| Término | Definición |
|---|---|
| Matriz | Oficina central de la empresa; visibilidad total de los datos. |
| UN | Unidad de Negocio; visibilidad restringida a su ámbito local. |
| Trabajo | Unidad de asignación enviada a un dispositivo: revisión, orden de trabajo o actividad de mantenimiento/proyecto. |
| Elemento | Entidad del modelo eléctrico (poste, transformador, luminaria, etc.). |
| GPKG | GeoPackage, formato estándar OGC para datos geoespaciales en SQLite. |
| GUID | Identificador único global de cada elemento (campo único del modelo). |
| Snapping | Ajuste automático de la geometría capturada a elementos existentes de la red. |
| Parámetros de calidad | Archivo precargado con reglas de validación de datos. |
| ArcSDE/Oracle | Geodatabase empresarial corporativa destino/origen de los datos. |

---

## 2. Actores y roles

### 2.1 Roles de la Plataforma Web

| Rol | Ámbito | Permisos |
|---|---|---|
| **Administrador del Sistema** | Global | Gestión de usuarios, roles, unidades de negocio, dispositivos, parámetros de calidad, configuración general. |
| **Operador/Editor Matriz** | Global | Asigna trabajos, manipula datos, ordena borrados remotos, gestiona el ciclo de vida de trabajos en toda la organización. |
| **Operador/Editor UN** | Su UN | Igual que el anterior, restringido a su unidad de negocio. |
| **Visualizador Matriz** | Global | Solo lectura de dashboard, histórico y reportes de toda la organización. |
| **Visualizador UN** | Su UN | Solo lectura de la información local de su unidad de negocio. |

**Regla de segregación de datos (obligatoria):** todo dato (trabajo, elemento, dispositivo, reporte) pertenece a una UN. Los roles de ámbito UN jamás pueden ver ni manipular datos de otra UN. Los roles Matriz ven y/u operan sobre todas las UN. La segregación se aplica a nivel de backend (no solo de interfaz).

### 2.2 Actores de la Aplicación Móvil

| Actor | Descripción |
|---|---|
| **Funcionario de campo** | Usuario con credenciales propias (usuario y clave) registrado en el sistema y vinculado a una UN y a un dispositivo. Ejecuta los trabajos asignados. |

---

## 3. Requerimientos Funcionales — Plataforma Web (WEB-ADMIN)

### RF-WEB-01: Autenticación de doble mecanismo
1. **Login corporativo:** autenticación contra el dominio interno de la empresa (Active Directory vía LDAP/LDAPS o SSO con SAML/OAuth2-OIDC según infraestructura disponible).
2. **Login local:** usuario y contraseña creados y gestionados dentro del sistema (con política de contraseñas: longitud mínima, complejidad, expiración configurable, bloqueo por intentos fallidos).
3. Ambos mecanismos deben convivir; un usuario se marca como "corporativo" o "local" al crearse.
4. Sesiones con expiración configurable, tokens seguros (JWT firmado o cookies HttpOnly + SameSite), cierre de sesión explícito.

### RF-WEB-02: Gestión de usuarios, roles y unidades de negocio
1. CRUD de usuarios con asignación de rol y UN.
2. CRUD de unidades de negocio.
3. Registro y gestión de **dispositivos móviles** autorizados (alta, baja, vinculación a funcionario y UN).
4. Toda operación de gestión queda auditada (ver RF-WEB-08).

### RF-WEB-03: Tipos de trabajo
El sistema soporta al menos tres tipos de trabajo, cada uno con su propia estructura de presentación y captura:

1. **Revisión en campo de redes eléctricas:** ámbito por **sector geográfico** (polígono); incluye todos los elementos de la red dentro del sector.
2. **Orden de trabajo puntual:** revisión de elementos específicos (postes u otros dispositivos eléctricos) identificados por su GUID.
3. **Actividad de mantenimiento / proyecto eléctrico:** conjunto de tareas sobre red existente o nueva, con posible captura de elementos nuevos.

Cada tipo define: campos atributivos requeridos, formularios de captura, reglas de calidad aplicables y forma de presentación en la app móvil.

### RF-WEB-04: Asignación de trabajos a dispositivos
1. El operador selecciona trabajos (por sector geográfico o por órdenes existentes) y los asigna a un **dispositivo**.
2. **Regla de exclusividad:** un trabajo solo puede estar asignado a **un dispositivo a la vez**.
3. **Multiplicidad:** un dispositivo puede tener **múltiples trabajos** asignados simultáneamente.
4. Flujo de asignación secuencial: el operador carga uno o varios trabajos a un dispositivo y luego continúa con el siguiente dispositivo.
5. La asignación empaqueta **geometría + atributos** de los elementos involucrados (extraídos de la geodatabase corporativa) y los deja disponibles para descarga del dispositivo.
6. Envío en lote (varios trabajos a la vez) o **carga paulatina/incremental**: se pueden agregar trabajos nuevos a un dispositivo que ya tiene trabajos en curso; la app los detectará en su próxima conexión.
7. **Reasignación:** un trabajo puede reasignarse a otro dispositivo solo si primero se retira (borrado remoto confirmado) del dispositivo original.

### RF-WEB-05: Borrado remoto de trabajos
1. La web puede ordenar el **borrado de uno o varios trabajos** asignados a un dispositivo.
2. La orden queda en cola y se ejecuta cuando el dispositivo se conecta; el dispositivo confirma la ejecución.
3. El borrado remoto queda auditado (quién lo ordenó, cuándo, qué dispositivo, qué trabajos, cuándo se confirmó).

### RF-WEB-06: Dashboard geográfico
1. Mapa interactivo con **todos los trabajos activos**: ubicación/extensión, tipo, estado, dispositivo/funcionario asignado, UN, antigüedad.
2. Filtros por UN, tipo de trabajo, estado, dispositivo, funcionario y rango de fechas.
3. Acceso al **histórico de trabajos terminados** con la misma capacidad de filtrado y visualización en mapa.
4. Detalle por trabajo: línea de tiempo de eventos (asignado, descargado, en ejecución, sincronizado, validado, cerrado).
5. Respeta la segregación Matriz/UN según el rol del usuario.

### RF-WEB-07: Bitácora por elemento
1. Cada elemento (identificado por su GUID) acumula una **bitácora** de todo lo que le ocurre: ediciones atributivas, cambios geométricos, fotos asociadas, observaciones, trabajos en los que participó, validaciones y quién/cuándo.
2. Consultable desde el mapa (clic en elemento) y desde búsqueda por GUID.

### RF-WEB-08: Auditoría e histórico integral
1. Registro inmutable (append-only) de: asignaciones, envíos a dispositivos, sincronizaciones, cambios de datos, borrados remotos, resultados de validación, cambios de configuración y acciones de usuarios.
2. Cada registro incluye: usuario, rol, fecha/hora (servidor), acción, entidad afectada, valores anterior/nuevo cuando aplique, dirección IP/dispositivo.
3. Consulta de auditoría con filtros y exportación.

### RF-WEB-09: Recepción y consolidación de sincronizaciones
1. Recepción de paquetes sincronizados desde la app móvil: datos atributivos, geometrías, fotos y **resultado de la validación de calidad** ejecutada en el dispositivo.
2. Visualización de las **novedades** reportadas por la validación, con detalle por elemento y por regla incumplida.
3. Flujo de cierre: solo cuando la sincronización está **completa y verificada** el trabajo puede pasar a estado "Terminado" y consolidarse.
4. Consolidación final de los cambios hacia la geodatabase corporativa **ArcSDE/Oracle** (proceso de carga controlado, con posibilidad de revisión previa por un operador si se configura así).
5. Si la sincronización fue parcial o falló, el trabajo permanece "En sincronización pendiente" y el proceso completo debe reintentarse (ver RF-SYNC).

### RF-WEB-10: Gestión de parámetros de calidad
1. Carga y versionamiento del **archivo de parámetros de calidad** (formato estructurado: JSON o similar) que la app móvil usará para validar.
2. Asociación de conjuntos de reglas por tipo de trabajo y/o tipo de elemento.
3. Distribución automática de la versión vigente a los dispositivos en su siguiente conexión.

### RF-WEB-11: Reportería
1. Reportes de: trabajos por estado/UN/tipo/periodo, productividad por funcionario/dispositivo, novedades de calidad más frecuentes, tiempos de ciclo (asignación → cierre), elementos intervenidos.
2. Exportación a Excel/PDF.
3. Los reportes respetan la segregación Matriz/UN.

### RF-WEB-12: Interfaz
1. Diseño **moderno, visualmente atractivo y responsivo** (uso cómodo en desktop, laptop y tablet).
2. Tiempos de respuesta rápidos (ver requerimientos no funcionales).

---

## 4. Requerimientos Funcionales — Aplicación Móvil (APP-CAMPO)

### RF-MOV-01: Autenticación
1. Login con **usuario y clave** propios del funcionario.
2. El dispositivo debe estar **registrado y autorizado** en la plataforma web; la combinación funcionario+dispositivo se valida en el primer login con conexión.
3. Sesión offline persistente tras el primer login exitoso (con credenciales cifradas localmente y expiración configurable); revalidación al reconectar.

### RF-MOV-02: Operación offline por defecto
1. Toda la operación de campo (visualizar, capturar, editar, fotografiar, observar) funciona **sin conectividad**.
2. Al detectar conexión, la app: (a) consulta trabajos nuevos asignados y los notifica/descarga, (b) recibe órdenes de borrado remoto, (c) recibe actualizaciones del archivo de parámetros de calidad, (d) permite iniciar sincronización de resultados.

### RF-MOV-03: Almacenamiento local en GeoPackage
1. Los datos geográficos y atributivos de cada trabajo se almacenan y editan en formato **GeoPackage (GPKG)**.
2. Estructura por trabajo o consolidada por dispositivo (decisión de diseño), con índices espaciales habilitados.
3. El GPKG contiene las capas de elementos del modelo eléctrico vigente con su GUID.

### RF-MOV-04: Interfaz adaptativa por dispositivo
1. **Teléfono:** navegación con **transición** entre la vista de mapa (visual) y la vista de formularios/atributos.
2. **Tablet:** **pantalla dividida** con el mapa y el panel atributivo visibles simultáneamente.
3. Detección automática del factor de forma; comportamiento correcto en rotación de pantalla.
4. Diseño visual cuidado, fluido y consistente con la identidad de la solución.

### RF-MOV-05: Presentación según tipo de trabajo
1. La app presenta cada trabajo con una interfaz acorde a su tipo:
   - **Revisión de red:** mapa del sector con todos los elementos, lista de pendientes/completados, avance porcentual.
   - **Orden puntual:** ficha del/los elementos objetivo, navegación asistida hacia ellos.
   - **Mantenimiento/proyecto:** checklist de actividades, captura de elementos nuevos y modificados.
2. Un funcionario puede tener **múltiples trabajos** abiertos y **editar varios a la vez**, cambiando entre ellos sin pérdida de estado.

### RF-MOV-06: Captura y edición de elementos
1. Registro y edición de datos eléctricos de postes y elementos relacionados según los formularios del tipo de trabajo.
2. **Snapping** configurable contra elementos designados de la red (p. ej., nuevos elementos que deben coincidir/conectarse con postes o tramos existentes), con tolerancia parametrizable.
3. Respeto de la relación **puesto/unidad** de los elementos según el modelo eléctrico vigente (elementos hijos vinculados a su elemento padre).
4. Campo de **observaciones** de texto libre por elemento.
5. Cada elemento nuevo recibe un **GUID** generado en el dispositivo; los existentes conservan el suyo.

### RF-MOV-07: Modo sin geometría (solo punto + fotos)
1. Opción de trabajo/registro que **no requiere geometría más allá de un punto**: el funcionario captura su posición (o un punto) y llena información complementaria basada **únicamente en fotos** y campos atributivos simples.

### RF-MOV-08: Fotografías con metadata y trazabilidad
1. Captura de **múltiples fotos por elemento o actividad**.
2. Cada foto embebe/registra metadata obligatoria: **coordenadas GPS, fecha y hora de captura**, elemento/actividad asociado, funcionario y dispositivo — garantizando trazabilidad de **dónde y cuándo estuvo** el funcionario.
3. **Compresión automática** de imágenes (resolución y calidad configurables) para evitar problemas de rendimiento y almacenamiento con muchos trabajos.
4. Gestión cuidadosa del ciclo de vida de las fotos en el teléfono: almacenamiento organizado por trabajo/elemento, verificación de integridad (hash) antes y después de transferir, y **eliminación local solo tras confirmación de recepción** en el servidor.

### RF-MOV-09: Validación de calidad en el dispositivo
1. La app mantiene el **archivo de parámetros de calidad** precargado (y actualizable desde la web).
2. Antes de/durante la sincronización, la app **valida localmente** que la información cumpla los parámetros: campos obligatorios, dominios de valores, rangos, consistencia geométrica, fotos mínimas requeridas, relaciones puesto/unidad, etc.
3. La app **explica las novedades** encontradas de forma clara: qué elemento, qué regla, qué valor, y qué se espera.
4. El resultado de la validación (aprobado / con novedades) se incluye en el paquete de sincronización y se refleja en la plataforma web.

### RF-MOV-10: Sincronización y cierre
1. Sincronización bidireccional segura al haber conectividad (ver RF-SYNC).
2. Al finalizar la subida, la app ejecuta una **verificación de completitud**: todo dato, geometría y foto confirmados por el servidor.
3. Si la verificación es exitosa y **no queda nada pendiente** en el dispositivo para ese trabajo, la app **consulta al usuario si desea eliminarlo** localmente. La eliminación local **solo** es posible tras sincronización completa confirmada, o por **orden de borrado remoto** desde la web.
4. Si hay **cualquier problema de sincronización** (corte, error, foto faltante), el trabajo **no puede darse por terminado**; la app lo marca como pendiente y el **proceso completo se reintenta** hasta lograr la verificación exitosa.

### RF-MOV-11: Rendimiento y gestión de recursos
1. Mejores prácticas para alto volumen: carga diferida (lazy loading) de capas y listas, paginación, renderizado por niveles de zoom, índices espaciales en GPKG, procesamiento de imágenes fuera del hilo de UI.
2. Uso **eficiente de RAM**: liberación proactiva de recursos, reciclaje de vistas, caché acotada de tiles/imágenes.
3. **Limpieza de datos obsoletos:** la app elimina automáticamente todo lo que ya no sirve (trabajos cerrados y confirmados, fotos ya transferidas y verificadas, cachés vencidas), manteniendo el dispositivo liviano.

---

## 5. Requerimientos de Sincronización y Comunicación (RF-SYNC)

1. **Canal seguro:** toda transferencia sobre **HTTPS/TLS 1.2+**; opcionalmente certificate pinning en la app móvil.
2. **Autenticación de cada petición:** token del funcionario + identificación del dispositivo autorizado.
3. **Transferencia rápida y robusta:** compresión de payloads, subida de fotos **por lotes y reanudable** (chunked/resumable upload), reintentos con backoff exponencial, tolerancia a redes inestables.
4. **Integridad:** checksums/hashes por archivo y por paquete; el servidor confirma recepción íntegra; nada se da por transferido sin confirmación.
5. **Idempotencia:** reintentos no generan duplicados (claves de idempotencia por paquete/elemento/foto usando GUID + versión).
6. **Estados sincronizados:** el servidor y el dispositivo mantienen un protocolo de estados por trabajo (Asignado → Descargado → En ejecución → En sincronización → Sincronizado/Verificado → Terminado | Con novedades) visible en el dashboard.
7. **Descarga incremental:** el dispositivo consulta y descarga solo lo nuevo o cambiado (trabajos nuevos, parámetros de calidad actualizados, órdenes de borrado).

---

## 6. Modelo de Datos

1. **Núcleo:** postes eléctricos y elementos relacionados del modelo eléctrico vigente.
2. **Identificador:** todo elemento posee un campo único tipo **GUID**.
3. **Relaciones:** el modelo respeta la relación **puesto/unidad** existente entre ciertos elementos (padre-hijo, p. ej., equipos montados sobre un poste).
4. **Esquema evolutivo:** el esquema inicial es básico y **puede cambiar**; la solución debe soportar la evolución del modelo (nuevas capas, campos, dominios) **sin reingeniería mayor** — se recomienda modelado dirigido por metadatos/configuración: los formularios, capas del GPKG y reglas de calidad se generan a partir de definiciones de esquema versionadas, no de código rígido.
5. **Versionamiento de esquema:** cada trabajo registra la versión de esquema con la que fue generado, para compatibilidad en sincronización.
6. **Segregación:** todas las entidades incluyen la UN propietaria.

---

## 7. Integración con la Geodatabase Corporativa (ArcSDE/Oracle)

1. **Origen:** la extracción de geometría y atributos para armar trabajos proviene de la geodatabase **ArcSDE sobre Oracle** (leída con herramientas ArcGIS o vistas/servicios definidos con el área GIS).
2. **Destino:** los resultados consolidados (cambios verificados y validados) se cargan de vuelta a ArcSDE/Oracle, preservando GUIDs y relaciones puesto/unidad.
3. El mecanismo específico (ArcPy/geoprocesamiento, servicios REST de ArcGIS, staging en tablas intermedias Oracle con proceso de aprobación) se definirá con las versiones de ArcGIS/ArcSDE/Oracle disponibles; el diseño debe **aislar esta integración en un módulo/adaptador independiente** para no acoplar el resto del sistema.
4. Toda carga a la geodatabase corporativa queda auditada y es reversible (respaldo/staging previo).

---

## 8. Requerimientos No Funcionales

### RNF-01: Seguridad
- Cifrado en tránsito (TLS 1.2+) y en reposo para credenciales y datos sensibles en el dispositivo (cifrado del almacenamiento local/keystore de Android).
- Cumplimiento de mejores prácticas OWASP (Top 10 web y MASVS móvil).
- Principio de mínimo privilegio en roles y en cuentas de servicio hacia Oracle/AD.
- Registros de auditoría inmutables.

### RNF-02: Rendimiento
- Web: respuesta de interacciones comunes < 2 s; dashboard geográfico fluido con cientos de trabajos activos.
- Móvil: apertura de trabajo < 3 s; navegación de mapa fluida (≥ 30 fps percibidos) con miles de elementos mediante renderizado optimizado; captura de foto y guardado sin bloqueo de UI.
- Sincronización eficiente en redes móviles 3G/4G inestables.

### RNF-03: Plataforma y despliegue
- Plataforma web con **tecnología moderna desplegable en Windows Server** (p. ej., backend .NET o Node.js/Java + frontend SPA moderno; base de datos del sistema compatible con el entorno; decisión final en diseño técnico).
- App móvil: **Android nativo** (Kotlin recomendado), soporte de teléfonos y tablets, versiones de Android definidas en diseño técnico (sugerido: Android 8.0+).

### RNF-04: Usabilidad
- Interfaces modernas y visualmente atractivas en ambos aplicativos.
- Web responsiva; móvil adaptativa teléfono/tablet.
- Uso con guantes/sol directo considerado en la app de campo (contraste, tamaños táctiles).

### RNF-05: Disponibilidad y resiliencia
- La app de campo nunca pierde datos capturados: persistencia inmediata local, recuperación ante cierres inesperados.
- El servidor tolera sincronizaciones concurrentes de múltiples dispositivos.

### RNF-06: Mantenibilidad y evolución
- Arquitectura modular (asignación, sincronización, validación, integración GIS, reportería como módulos separados).
- Modelo de datos y formularios dirigidos por configuración para absorber cambios de esquema.
- Código y APIs documentados; versionamiento de API.

### RNF-07: Eficiencia de recursos
- Uso eficiente de RAM y almacenamiento en el dispositivo; limpieza automática de datos que ya no sirven; fotos comprimidas.

---

## 9. Reglas de Negocio (resumen)

| ID | Regla |
|---|---|
| RN-01 | Un trabajo solo puede estar asignado a un dispositivo a la vez. |
| RN-02 | Un dispositivo puede tener múltiples trabajos simultáneos. |
| RN-03 | Un trabajo solo se elimina del dispositivo tras sincronización completa confirmada, o por orden remota desde la web. |
| RN-04 | Si la sincronización falla o es parcial, el trabajo no puede darse por terminado y el proceso completo se reintenta. |
| RN-05 | Los usuarios de UN solo ven/operan datos de su UN; los de Matriz, de toda la organización. |
| RN-06 | Todo elemento se identifica por GUID único e inmutable. |
| RN-07 | Se respeta la relación puesto/unidad del modelo eléctrico vigente. |
| RN-08 | Toda foto debe tener metadata de coordenadas, fecha y hora. |
| RN-09 | La validación de calidad se ejecuta en el dispositivo con los parámetros vigentes antes de consolidar. |
| RN-10 | Todo cambio y envío queda registrado en el histórico/auditoría. |
| RN-11 | La consolidación final es siempre hacia la geodatabase ArcSDE/Oracle. |

---

## 10. Criterios de Aceptación de Alto Nivel

1. Un operador puede asignar múltiples trabajos (de los tres tipos) a un dispositivo y luego a otro; los dispositivos los reciben al conectarse, incluso de forma paulatina.
2. Un funcionario trabaja completamente offline: edita varios trabajos a la vez sobre GeoPackage, captura elementos con snapping, sube múltiples fotos comprimidas con metadata de posición/fecha/hora, registra observaciones y usa el modo "solo punto + fotos".
3. En teléfono la app transiciona entre mapa y atributos; en tablet muestra ambos en pantalla dividida.
4. Al sincronizar, la app valida contra los parámetros de calidad precargados, explica las novedades, y estas se ven en la web.
5. La app solo ofrece eliminar un trabajo tras verificar sincronización completa; ante fallos, el trabajo queda pendiente y se reintenta todo el proceso.
6. La web ordena un borrado remoto y el dispositivo lo ejecuta y confirma en su siguiente conexión.
7. El dashboard geográfico muestra trabajos activos e histórico, filtrados por rol Matriz/UN; la bitácora por elemento muestra todo lo ocurrido con ese GUID.
8. Los reportes se generan y exportan respetando la segregación de UN.
9. Los resultados verificados se consolidan en ArcSDE/Oracle preservando GUIDs y relaciones.
10. Login web funciona por dominio corporativo y por credenciales locales; login móvil con usuario/clave y dispositivo autorizado.

---

## 11. Fuera de Alcance (fase 1)

- Edición directa sobre la geodatabase ArcSDE desde la web (la consolidación se hace por proceso controlado).
- Soporte iOS.
- Cálculos de ingeniería eléctrica (flujos de carga, etc.); el sistema es de levantamiento y gestión de datos.

## 12. Pendientes de Definición

| ID | Punto abierto | Impacto |
|---|---|---|
| PD-01 | Comportamiento ante validación de calidad fallida: ¿bloquea la subida o sube marcando novedades para corrección posterior? | Flujo de sincronización y cierre. |
| PD-02 | Versiones exactas de ArcGIS Desktop, ArcSDE y Oracle. | Mecanismo del módulo de integración. |
| PD-03 | Esquema detallado del modelo eléctrico (capas, campos, dominios, relaciones puesto/unidad). | Generación de GPKG, formularios y reglas de calidad. |
| PD-04 | Formato definitivo del archivo de parámetros de calidad. | Motor de validación móvil. |
| PD-05 | Infraestructura de autenticación corporativa disponible (AD/LDAP vs. SSO federado). | Módulo de login web. |

---

*Fin del documento. Preparado para servir como insumo de implementación en Claude Code: los IDs de requerimientos (RF-WEB-xx, RF-MOV-xx, RF-SYNC, RNF-xx, RN-xx) pueden usarse para trazar tareas, commits y pruebas.*

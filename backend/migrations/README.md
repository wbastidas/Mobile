# Migraciones (Alembic)

El esquema de la base de datos del sistema se versiona con Alembic. En
desarrollo (SQLite) las tablas se crean automáticamente al arrancar; en
**producción (PostgreSQL/PostGIS)** el esquema se gestiona con migraciones.

```bash
# Aplicar todas las migraciones a la base configurada (DATABASE_URL)
python -m alembic upgrade head

# Generar una nueva migración tras cambiar los modelos
python -m alembic revision --autogenerate -m "descripcion del cambio"

# Revertir la última migración
python -m alembic downgrade -1
```

- La URL de conexión se toma de `settings.DATABASE_URL` (no se duplica en
  `alembic.ini`).
- `render_as_batch=True` permite `ALTER TABLE` también en SQLite.
- **PostGIS:** al migrar a PostgreSQL, las columnas de geometría hoy modeladas
  como texto GeoJSON se sustituyen por columnas `geometry` de GeoAlchemy2, y la
  migración correspondiente habilita la extensión (`CREATE EXTENSION postgis`) e
  crea los índices espaciales (GIST). El código es agnóstico a la BD, por lo que
  ese cambio queda contenido en modelos + migración.

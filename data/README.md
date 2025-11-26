# Directorio de Datos Persistentes

Este directorio contiene todos los datos persistentes de los contenedores Docker.

## Estructura

```
data/
├── postgres/          # Datos de la base de datos PostgreSQL (DefectDojo)
├── redis/             # Datos de Redis (cache y cola de tareas de DefectDojo)
└── defectdojo/
    ├── media/         # Archivos multimedia subidos a DefectDojo
    └── static/        # Archivos estáticos generados por DefectDojo
```

## Importante

- **Estos directorios están en `.gitignore`** - Los datos no se suben al repositorio
- Los directorios se crean automáticamente al arrancar los servicios
- **Backup**: Si necesitas hacer backup, copia este directorio completo
- **Permisos**: Docker gestionará los permisos automáticamente

## Migración desde Volúmenes Docker

Si tenías datos en volúmenes Docker anteriores, puedes migrarlos:

```bash
# Detener servicios
docker-compose --profile defectdojo down

# Copiar datos desde volúmenes (si existen)
docker run --rm -v aplicacinmdica_defectdojo_db_data:/source -v $(pwd)/data/postgres:/dest alpine sh -c "cp -a /source/. /dest/"
docker run --rm -v aplicacinmdica_defectdojo_redis_data:/source -v $(pwd)/data/redis:/dest alpine sh -c "cp -a /source/. /dest/"
docker run --rm -v aplicacinmdica_defectdojo_media:/source -v $(pwd)/data/defectdojo/media:/dest alpine sh -c "cp -a /source/. /dest/"
docker run --rm -v aplicacinmdica_defectdojo_static:/source -v $(pwd)/data/defectdojo/static:/dest alpine sh -c "cp -a /source/. /dest/"

# Ajustar permisos
sudo chown -R 999:999 data/postgres  # Usuario postgres
sudo chown -R 999:999 data/redis      # Usuario redis
sudo chown -R 1000:1000 data/defectdojo  # Usuario defectdojo

# Arrancar de nuevo
docker-compose --profile defectdojo up -d
```

## Limpieza

Para eliminar todos los datos y empezar de cero:

```bash
# Detener servicios
docker-compose --profile defectdojo down

# Eliminar directorios (¡CUIDADO! Esto borra todos los datos)
rm -rf data/postgres/* data/redis/* data/defectdojo/*

# Arrancar de nuevo (se crearán directorios vacíos)
docker-compose --profile defectdojo up -d
```


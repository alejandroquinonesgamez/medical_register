#!/bin/sh
# Wrapper script para ejecutar inicialización antes del entrypoint original
# Este script se ejecuta dentro del contenedor

# Ejecutar script de inicialización
python /app/init_defectdojo.py

# Ejecutar el entrypoint original de DefectDojo
exec /entrypoint-uwsgi.sh "$@"


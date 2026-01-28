#!/bin/sh
# Entrypoint para el contenedor web: crea directorios escribibles, ajusta
# permisos y ejecuta la app como usuario no root (appuser, UID 1000).
# Así se evita tener que usar chmod 777 en el host al desplegar.

set -e

# Directorios que la aplicación debe poder escribir (bind mount .:/app)
mkdir -p /app/data /app/data/temp /app/data/wstg_sync_queue /app/docs/informes /app/instance

# Ajustar dueño para que el proceso no root pueda escribir (UID 1000 = appuser)
chown -R appuser:appuser /app/data /app/instance 2>/dev/null || true
chown -R appuser:appuser /app/docs/informes 2>/dev/null || true
[ -d /app/docs ] && chown appuser:appuser /app/docs 2>/dev/null || true

# Ejecutar como appuser (init_storage + gunicorn); su está en toda imagen Debian
exec su appuser -s /bin/sh -c "python /app/scripts/init_storage.py && exec gunicorn --bind 0.0.0.0:5001 --workers 1 --timeout 120 run:app"

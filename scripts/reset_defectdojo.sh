#!/bin/bash
# Script de RESET de DefectDojo
# 
# Este script reinicializa DefectDojo ejecutando:
# - Migraciones de la base de datos
# - Recolección de archivos estáticos
# - Creación/actualización del usuario admin (admin/admin)
#
# Útil para:
# - Reinicializar DefectDojo después de problemas
# - Resetear la base de datos
# - Forzar la ejecución de migraciones
#
# NOTA: La inicialización normal se ejecuta AUTOMÁTICAMENTE al arrancar el contenedor.
# Este script solo es necesario para hacer un reset manual.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker_compose.sh
source "$SCRIPT_DIR/docker_compose.sh"
cd "$SCRIPT_DIR/.."

echo "🔄 Reinicializando DefectDojo..."
echo "ℹ️  Nota: La inicialización normalmente es automática al arrancar el contenedor"
echo ""

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
until docker_compose --profile defectdojo exec -T defectdojo-db pg_isready -U defectdojo > /dev/null 2>&1; do
  sleep 2
done

echo "✅ Base de datos lista"

# Ejecutar migraciones
echo "📦 Ejecutando migraciones de Django..."
docker_compose --profile defectdojo exec -T defectdojo python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
docker_compose --profile defectdojo exec -T defectdojo python manage.py collectstatic --noinput || true

# Crear usuario admin si no existe
echo "👤 Creando usuario admin (admin/admin)..."
docker_compose --profile defectdojo exec -T defectdojo python manage.py shell << 'EOF'
from dojo.models import User
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'is_superuser': True,
        'is_staff': True,
        'is_active': True,
        'email': 'admin@example.com'
    }
)
if created:
    user.set_password('admin')
    user.save()
    print('✅ Usuario admin creado con contraseña: admin')
else:
    user.set_password('admin')
    user.save()
    print('✅ Contraseña del usuario admin actualizada a: admin')
EOF

echo "✅ Reset de DefectDojo completado"
echo ""
echo "📝 Credenciales por defecto:"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "🌐 Accede a DefectDojo en: http://localhost:8080"


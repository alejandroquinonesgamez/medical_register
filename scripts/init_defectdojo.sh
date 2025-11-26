#!/bin/bash
# Script de inicialización de DefectDojo
# Ejecuta migraciones y crea el usuario admin por defecto

set -e

echo "🔧 Inicializando DefectDojo..."

# Esperar a que la base de datos esté lista
echo "⏳ Esperando a que la base de datos esté lista..."
until docker-compose --profile defectdojo exec -T defectdojo-db pg_isready -U defectdojo > /dev/null 2>&1; do
  sleep 2
done

echo "✅ Base de datos lista"

# Ejecutar migraciones
echo "📦 Ejecutando migraciones de Django..."
docker-compose --profile defectdojo exec -T defectdojo python manage.py migrate --noinput

# Recolectar archivos estáticos
echo "📁 Recolectando archivos estáticos..."
docker-compose --profile defectdojo exec -T defectdojo python manage.py collectstatic --noinput || true

# Crear usuario admin si no existe
echo "👤 Creando usuario admin (admin/admin)..."
docker-compose --profile defectdojo exec -T defectdojo python manage.py shell << 'EOF'
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

echo "✅ Inicialización de DefectDojo completada"
echo ""
echo "📝 Credenciales por defecto:"
echo "   Usuario: admin"
echo "   Contraseña: admin"
echo ""
echo "🌐 Accede a DefectDojo en: http://localhost:8080"


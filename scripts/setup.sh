#!/bin/bash
# Script de configuración inicial del proyecto
# Prepara el entorno para usar la aplicación

set -e

echo "🚀 Configurando el proyecto Medical Register..."
echo ""

# Crear directorios de datos si no existen
echo "📁 Creando directorios de datos..."
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/defectdojo/media
mkdir -p data/defectdojo/static

# Asegurar que los directorios tienen permisos correctos
chmod -R 755 data/

echo "✅ Directorios creados"
echo ""

# Verificar Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker no está instalado"
    echo "   Por favor, instala Docker desde https://www.docker.com/get-started"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose no está instalado"
    echo "   Por favor, instala docker-compose"
    exit 1
fi

echo "✅ Docker y docker-compose detectados"
echo ""

# Construir imagen de la aplicación principal
echo "🔨 Construyendo imagen de la aplicación..."
docker-compose build web

echo ""
echo "✅ Configuración completada"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Arrancar la aplicación principal:"
echo "   docker-compose up -d"
echo ""
echo "2. Arrancar DefectDojo (opcional):"
echo "   docker-compose --profile defectdojo up -d"
echo "   ./scripts/init_defectdojo.sh"
echo ""
echo "3. Acceder a las aplicaciones:"
echo "   - Aplicación Flask: http://localhost:5001"
echo "   - DefectDojo: http://localhost:8080 (usuario: admin, contraseña: admin)"
echo ""


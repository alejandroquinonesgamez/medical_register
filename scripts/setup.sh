#!/bin/bash
# Script de configuración inicial del proyecto
#
# Prepara el entorno para usar la aplicación médica. Realiza:
# 1. Crea directorios de datos necesarios (data/postgres, data/redis, data/defectdojo)
# 2. Configura el archivo .env para Docker Compose (soluciona problemas con caracteres especiales)
# 3. Verifica que Docker y Docker Compose estén instalados
# 4. Construye la imagen de la aplicación
#
# Este script se ejecuta automáticamente al clonar el repositorio
# y debe ejecutarse antes de usar make o Docker Compose.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
# shellcheck source=docker_compose.sh
source "$SCRIPT_DIR/docker_compose.sh"

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

if ! docker_compose_available; then
    echo "❌ Error: Docker Compose no está disponible"
    echo "   Instala el plugin v2 (recomendado): \"docker compose version\" debe funcionar"
    echo "   O el binario v1: paquete docker-compose en tu distribución"
    exit 1
fi

echo "✅ Docker y Docker Compose detectados"
echo ""

# Configurar archivo .env para Docker Compose (soluciona problemas con caracteres especiales)
echo "⚙️  Configurando Docker Compose..."
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE="$PROJECT_ROOT/docker-compose.env.example"

if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        echo "  ✓ Archivo .env creado desde docker-compose.env.example"
    else
        # Crear .env básico
        cat > "$ENV_FILE" <<EOF
COMPOSE_PROJECT_NAME=medical_register
COMPOSE_DOCKER_CLI_BUILD=0
DOCKER_BUILDKIT=0
EOF
        echo "  ✓ Archivo .env creado con configuración básica"
    fi
else
    echo "  ℹ️  Archivo .env ya existe"
fi

echo "✅ Docker Compose configurado"
echo ""

# Construir imagen de la aplicación principal
echo "🔨 Construyendo imagen de la aplicación..."

# Cargar variables de entorno desde .env si existe
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

(cd "$PROJECT_ROOT" && docker_compose build web)

echo ""
echo "✅ Configuración completada"
echo ""
echo "📋 Próximos pasos:"
echo ""
echo "1. Arrancar la aplicación principal:"
echo "   docker compose up -d"
echo "   # o: make"
echo ""
echo "2. Arrancar DefectDojo (opcional):"
echo "   docker compose --profile defectdojo up -d"
echo "   ./scripts/reset_defectdojo.sh  # Solo si necesitas hacer un reset"
echo ""
echo "3. Acceder a las aplicaciones:"
echo "   - Aplicación Flask: http://localhost:5001"
echo "   - DefectDojo: http://localhost:8080 (usuario: admin, contraseña: admin)"
echo ""


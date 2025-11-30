#!/bin/bash
# Script para marcar findings como resueltos en DefectDojo con fechas específicas
# Este script ejecuta el script Python dentro del contenedor de DefectDojo

echo "=== Marcando findings como resueltos con fechas históricas ==="
echo ""

# Verificar si DefectDojo está corriendo
if ! docker-compose ps --profile defectdojo | grep -q "defectdojo.*Up"; then
    echo "⚠️  DefectDojo no está corriendo. Iniciando DefectDojo..."
    COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 docker-compose --profile defectdojo up -d defectdojo
    
    echo "⏳ Esperando a que DefectDojo esté listo..."
    sleep 10
fi

# Copiar el script al contenedor temporalmente y ejecutarlo
echo "📅 Actualizando findings con fechas históricas..."

# Obtener la ruta del script relativa al directorio de scripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_PATH="${SCRIPT_DIR}/resolve_findings_with_dates.py"

# Si no encontramos el script en el directorio de scripts, intentar desde el directorio actual
if [ ! -f "$SCRIPT_PATH" ]; then
    # Intentar desde el directorio de trabajo actual
    if [ -f "./scripts/resolve_findings_with_dates.py" ]; then
        SCRIPT_PATH="./scripts/resolve_findings_with_dates.py"
    elif [ -f "scripts/resolve_findings_with_dates.py" ]; then
        SCRIPT_PATH="scripts/resolve_findings_with_dates.py"
    else
        echo "❌ Error: No se encontró el script resolve_findings_with_dates.py"
        echo "   Buscado en: $SCRIPT_PATH"
        exit 1
    fi
fi

echo "   Usando script: $SCRIPT_PATH"

# Copiar al contenedor y ejecutar
echo "   Copiando script al contenedor..."
if docker cp "$SCRIPT_PATH" defectdojo:/tmp/resolve_findings_with_dates.py 2>/dev/null; then
    echo "   ✓ Script copiado correctamente"
else
    echo "   ⚠️  Error al copiar el script. Verificando que el contenedor esté corriendo..."
    if ! docker ps | grep -q "defectdojo"; then
        echo "   ❌ El contenedor defectdojo no está corriendo"
        exit 1
    fi
    # Intentar de nuevo con ruta absoluta
    docker cp "$SCRIPT_PATH" defectdojo:/tmp/resolve_findings_with_dates.py
fi

echo "   Ejecutando script en DefectDojo..."
COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 docker-compose --profile defectdojo exec -T defectdojo python3 /tmp/resolve_findings_with_dates.py

echo ""
echo "✅ Proceso completado"
echo ""
echo "Puedes ver los findings actualizados en: http://localhost:8080/test/1/findings"


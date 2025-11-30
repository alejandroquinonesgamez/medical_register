#!/bin/bash
# Script para limpiar TODO y volver al estado como recién clonado
# ADVERTENCIA: Este script es DESTRUCTIVO. Elimina todos los datos de Docker, contenedores, imágenes, etc.

set -e

echo "⚠️  ⚠️  ⚠️  ADVERTENCIA ⚠️  ⚠️  ⚠️"
echo ""
echo "Este comando eliminará:"
echo "  - Todos los contenedores Docker del proyecto"
echo "  - Todas las imágenes Docker del proyecto"
echo "  - Todos los volúmenes Docker del proyecto"
echo "  - Todos los datos de PostgreSQL, Redis y DefectDojo"
echo "  - Todos los dumps SQL generados"
echo "  - El entorno virtual (venv/)"
echo "  - Archivos temporales de desarrollo"
echo ""
echo "El proyecto volverá al estado como recién clonado."
echo ""
echo -n "¿Estás seguro de que deseas continuar? (escribe 'si' para confirmar): "
read confirmacion

if [ "$confirmacion" != "si" ]; then
    echo ""
    echo "❌ Operación cancelada."
    exit 0
fi

echo ""
echo "🧹 Iniciando limpieza completa..."
echo ""

COUNT=0

# Paso 1: Detener y eliminar contenedores Docker
echo "Paso 1/8: Deteniendo y eliminando contenedores Docker..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-medical_register}"
    COMPOSE_DOCKER_CLI_BUILD="${COMPOSE_DOCKER_CLI_BUILD:-0}"
    DOCKER_BUILDKIT="${DOCKER_BUILDKIT:-0}"
    
    COMPOSE="COMPOSE_DOCKER_CLI_BUILD=${COMPOSE_DOCKER_CLI_BUILD} DOCKER_BUILDKIT=${DOCKER_BUILDKIT} COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME} docker-compose"
    
    # Detener y eliminar contenedores
    $COMPOSE down --volumes --remove-orphans 2>/dev/null || true
    $COMPOSE --profile defectdojo down --volumes --remove-orphans 2>/dev/null || true
    
    echo "  ✓ Contenedores detenidos y eliminados"
    ((COUNT++))
    
    # Eliminar redes huérfanas del proyecto
    echo ""
    echo "   Eliminando redes huérfanas..."
    NETWORKS=$(docker network ls --format "{{.Name}}" | grep -E "(${COMPOSE_PROJECT_NAME:-medical_register}|defectdojo)" || true)
    if [ -n "$NETWORKS" ]; then
        echo "$NETWORKS" | while read -r network; do
            docker network rm "$network" 2>/dev/null || true
        done
        echo "  ✓ Redes huérfanas eliminadas"
    fi
fi

# Paso 2: Eliminar imágenes del proyecto
echo ""
echo "Paso 2/8: Eliminando imágenes Docker del proyecto..."
if command -v docker &> /dev/null; then
    # Buscar imágenes relacionadas con el proyecto
    PROJECT_NAME="${COMPOSE_PROJECT_NAME:-medical_register}"
    IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "(medical_register|${PROJECT_NAME})" || true)
    
    if [ -n "$IMAGES" ]; then
        echo "$IMAGES" | xargs -r docker rmi -f 2>/dev/null || true
        echo "  ✓ Imágenes eliminadas"
        ((COUNT++))
    else
        echo "  ℹ️  No se encontraron imágenes del proyecto para eliminar"
    fi
fi

# Paso 3: Eliminar datos de PostgreSQL
echo ""
echo "Paso 3/8: Eliminando datos de PostgreSQL..."
if [ -d "data/postgres" ]; then
    rm -rf data/postgres
    echo "  ✓ Directorio data/postgres/ eliminado"
    ((COUNT++))
fi

# Paso 4: Eliminar datos de Redis
echo ""
echo "Paso 4/8: Eliminando datos de Redis..."
if [ -d "data/redis" ]; then
    rm -rf data/redis
    echo "  ✓ Directorio data/redis/ eliminado"
    ((COUNT++))
fi

# Paso 5: Eliminar datos de DefectDojo
echo ""
echo "Paso 5/8: Eliminando datos de DefectDojo..."
if [ -d "data/defectdojo" ]; then
    rm -rf data/defectdojo
    echo "  ✓ Directorio data/defectdojo/ eliminado"
    ((COUNT++))
fi

# Paso 6: Eliminar dumps SQL generados (excepto el inicial)
echo ""
echo "Paso 6/8: Eliminando dumps SQL generados..."
if [ -d "data" ]; then
    DUMP_FILES=$(find data -name "*_db_dump.sql" -not -name "defectdojo_db_initial.sql" 2>/dev/null || true)
    if [ -n "$DUMP_FILES" ]; then
        echo "$DUMP_FILES" | xargs rm -f
        DUMP_COUNT=$(echo "$DUMP_FILES" | wc -l)
        echo "  ✓ $DUMP_COUNT dumps SQL eliminados"
        ((COUNT++))
    else
        echo "  ℹ️  No se encontraron dumps SQL para eliminar"
    fi
fi

# Paso 7: Eliminar entorno virtual
echo ""
echo "Paso 7/8: Eliminando entorno virtual..."
if [ -d "venv" ]; then
    rm -rf venv
    echo "  ✓ Directorio venv/ eliminado"
    ((COUNT++))
fi

# Paso 8: Eliminar .env (se recreará automáticamente)
echo ""
echo "Paso 8/8: Limpiando archivo .env..."
if [ -f ".env" ]; then
    rm -f .env
    echo "  ✓ Archivo .env eliminado (se recreará automáticamente)"
    ((COUNT++))
fi

# Ejecutar limpieza de archivos temporales
echo ""
echo "Ejecutando limpieza de archivos temporales..."
if [ -f "scripts/clean_temp.sh" ]; then
    bash scripts/clean_temp.sh
fi

echo ""
echo "✅ Limpieza completa finalizada"
echo ""
echo "El proyecto ha vuelto al estado como recién clonado."
echo ""
echo "Para volver a iniciar el proyecto, ejecuta:"
echo "  ./scripts/setup.sh    # Linux/Mac/Git Bash"
echo "  .\\scripts\\setup.ps1  # Windows/PowerShell"
echo "  make                  # Luego arranca con make"


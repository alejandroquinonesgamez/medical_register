#!/bin/bash
# Script para cargar el dump de la base de datos de DefectDojo
# Uso: ./scripts/load_defectdojo_db.sh [ruta_al_dump.sql]
# Por defecto usa: ./data/defectdojo_db_initial.sql (dump inicial del repositorio)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker_compose.sh
source "$SCRIPT_DIR/docker_compose.sh"
cd "$SCRIPT_DIR/.."

DUMP_FILE="${1:-./data/defectdojo_db_initial.sql}"

if [ ! -f "$DUMP_FILE" ]; then
    echo "❌ Error: No se encontró el archivo dump: $DUMP_FILE"
    echo "   Uso: $0 [ruta_al_dump.sql]"
    exit 1
fi

echo "📥 Cargando dump de DefectDojo desde: $DUMP_FILE"
echo "⏳ Esto puede tardar unos minutos..."

# Cargar el dump en el contenedor de PostgreSQL
docker-compose --profile defectdojo exec -T defectdojo-db psql -U defectdojo -d defectdojo < "$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Dump cargado correctamente"
    echo "🔄 Reiniciando DefectDojo para aplicar los cambios..."
    docker_compose --profile defectdojo restart defectdojo
else
    echo "❌ Error al cargar el dump"
    exit 1
fi


#!/bin/bash
# Script para exportar la base de datos de DefectDojo a un archivo SQL
# Uso: ./scripts/export_defectdojo_db.sh [ruta_del_dump.sql]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=docker_compose.sh
source "$SCRIPT_DIR/docker_compose.sh"
cd "$SCRIPT_DIR/.."

OUTPUT_FILE="${1:-./data/defectdojo_db_dump.sql}"

# Crear directorio si no existe
mkdir -p "$(dirname "$OUTPUT_FILE")"

echo "📤 Exportando base de datos de DefectDojo..."
echo "⏳ Esto puede tardar unos minutos..."

# Exportar la base de datos
docker_compose --profile defectdojo exec -T defectdojo-db pg_dump -U defectdojo defectdojo > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
    echo "✅ Base de datos exportada correctamente a: $OUTPUT_FILE"
    echo "   Tamaño: $FILE_SIZE"
    echo ""
    echo "💡 Para cargar este dump en otra instalación, usa:"
    echo "   ./scripts/load_defectdojo_db.sh $OUTPUT_FILE"
else
    echo "❌ Error al exportar la base de datos"
    exit 1
fi










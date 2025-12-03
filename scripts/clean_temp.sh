#!/bin/bash
# Script para limpiar archivos temporales del proyecto
# Elimina archivos que están en .gitignore y son generados automáticamente

set -e

echo "🧹 Limpiando archivos temporales del proyecto..."
echo ""

# Contador de archivos eliminados
COUNT=0

# Eliminar archivo de cobertura
if [ -f .coverage ]; then
    rm -f .coverage
    echo "  ✓ Eliminado: .coverage"
    ((COUNT++))
fi

# Eliminar directorio instance/ (base de datos SQLite)
if [ -d instance ]; then
    rm -rf instance
    echo "  ✓ Eliminado: instance/ (base de datos SQLite)"
    ((COUNT++))
fi

# Eliminar directorios __pycache__
PYCACHE_COUNT=$(find . -type d -name "__pycache__" -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -not -path "./venv/*" -not -path "./.git/*" -exec rm -rf {} + 2>/dev/null || true
    echo "  ✓ Eliminados $PYCACHE_COUNT directorios __pycache__/"
    ((COUNT++))
fi

# Eliminar archivos .pyc y .pyo
PYC_FILES=$(find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./venv/*" -not -path "./.git/*" 2>/dev/null | wc -l)
if [ "$PYC_FILES" -gt 0 ]; then
    find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -not -path "./venv/*" -not -path "./.git/*" -delete 2>/dev/null || true
    echo "  ✓ Eliminados $PYC_FILES archivos .pyc/.pyo"
    ((COUNT++))
fi

# Eliminar .pytest_cache
if [ -d .pytest_cache ]; then
    rm -rf .pytest_cache
    echo "  ✓ Eliminado: .pytest_cache/"
    ((COUNT++))
fi

# Eliminar htmlcov
if [ -d htmlcov ]; then
    rm -rf htmlcov
    echo "  ✓ Eliminado: htmlcov/"
    ((COUNT++))
fi

if [ $COUNT -eq 0 ]; then
    echo "  ℹ️  No se encontraron archivos temporales para eliminar"
else
    echo ""
    echo "✅ Limpieza completada: $COUNT elementos eliminados"
fi

echo ""


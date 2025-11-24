#!/bin/bash
# Script para marcar findings como resueltos en DefectDojo

DEFECTDOJO_URL="http://localhost:8080/api/v2"
TOKEN=$(curl -s -X POST "${DEFECTDOJO_URL}/api-token-auth/" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

echo "=== Marcando findings como resueltos en DefectDojo ==="
echo ""

# IDs de los findings (CWE-20 ya está resuelto, IDs 4-8 son los pendientes)
CWE1287_ID=4
CWE843_ID=5
CWE1021_ID=6
CWE703_ID=7
CWE942_ID=8

# CWE-1287: Resuelto
echo "Marcando CWE-1287 como resuelto..."
UPDATE_DATA='{
    "active": false,
    "verified": true,
    "status": "Verified",
    "mitigation": "✅ RESUELTO: Se implementó validación de tipo antes de convertir a float() usando isinstance(). Se verifica que el resultado sea finito usando math.isfinite() para prevenir NaN e Infinity. Se usan excepciones específicas (ValueError, TypeError) en lugar de Exception genérico. Ubicación: app/routes.py líneas 36-52, 94-110"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE1287_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-1287 marcado como resuelto"

# CWE-843: Resuelto
echo "Marcando CWE-843 como resuelto..."
UPDATE_DATA='{
    "active": false,
    "verified": true,
    "status": "Verified",
    "mitigation": "✅ RESUELTO: Se implementó validación de NaN e Infinity después de parseFloat() usando isNaN() e isFinite() en todos los lugares donde se usa parseFloat(). Ubicación: app/static/js/main.js líneas 139-145, 207-213; app/static/js/storage.js líneas 84-89"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE843_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-843 marcado como resuelto"

# CWE-1021: Resuelto
echo "Marcando CWE-1021 como resuelto..."
UPDATE_DATA='{
    "active": false,
    "verified": true,
    "status": "Verified",
    "mitigation": "✅ RESUELTO: Se agregaron headers de seguridad en app/__init__.py usando @app.after_request: X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors '\''none'\'', X-Content-Type-Options: nosniff, X-XSS-Protection: 1; mode=block. Ubicación: app/__init__.py líneas 30-37"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE1021_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-1021 marcado como resuelto"

# CWE-703: Resuelto
echo "Marcando CWE-703 como resuelto..."
UPDATE_DATA='{
    "active": false,
    "verified": true,
    "status": "Verified",
    "mitigation": "✅ RESUELTO: Se mejoró el manejo de excepciones en app/routes.py usando excepciones específicas (ValueError, TypeError) en lugar de Exception genérico. Se agregó logging para debugging. En JavaScript (sync.js) se mejoró el logging para diferenciar tipos de errores. Ubicación: app/routes.py líneas 36-52, 94-110; app/static/js/sync.js líneas 119-130"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE703_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-703 marcado como resuelto"

# CWE-942: Mantener como aceptado (no se cambia CORS porque es monousuario)
echo "Verificando CWE-942 (aceptado temporalmente)..."
CURRENT=$(curl -s -X GET "${DEFECTDOJO_URL}/findings/${CWE942_ID}/" \
    -H "Authorization: Token ${TOKEN}")
ACTIVE=$(echo "$CURRENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['active'])" 2>/dev/null)
if [ "$ACTIVE" = "True" ]; then
    echo "  ℹ️ CWE-942 se mantiene como aceptado temporalmente (aplicación monousuario)"
else
    echo "  ✓ CWE-942 ya está marcado"
fi

echo ""
echo "=== Resumen ==="
echo "✓ CWE-20: Ya estaba resuelto"
echo "✓ CWE-1287: Resuelto"
echo "✓ CWE-843: Resuelto"
echo "✓ CWE-1021: Resuelto"
echo "✓ CWE-703: Resuelto"
echo "⏸️ CWE-942: Aceptado temporalmente (monousuario)"
echo ""
echo "Puedes ver los findings actualizados en: http://localhost:8080/test/1/findings"


#!/bin/bash
# Script para actualizar el estado de los findings en DefectDojo

DEFECTDOJO_URL="http://localhost:8080/api/v2"
TOKEN=$(curl -s -X POST "${DEFECTDOJO_URL}/api-token-auth/" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin"}' | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

echo "=== Actualizando estado de findings en DefectDojo ==="
echo ""

# IDs de los findings
CWE20_ID=3
CWE1287_ID=4
CWE843_ID=5
CWE1021_ID=6
CWE703_ID=7
CWE942_ID=8

# CWE-20: Ya está resuelto - solo verificar que esté correcto
echo "Verificando CWE-20 (Resuelto)..."
CURRENT=$(curl -s -X GET "${DEFECTDOJO_URL}/findings/${CWE20_ID}/" \
    -H "Authorization: Token ${TOKEN}")
ACTIVE=$(echo "$CURRENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['active'])" 2>/dev/null)
VERIFIED=$(echo "$CURRENT" | python3 -c "import sys, json; print(json.load(sys.stdin)['verified'])" 2>/dev/null)

if [ "$ACTIVE" = "False" ] && [ "$VERIFIED" = "True" ]; then
    echo "  ✓ CWE-20 ya está correctamente marcado como resuelto"
else
    echo "  Actualizando CWE-20..."
    curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE20_ID}/" \
        -H "Authorization: Token ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"active": false, "verified": true, "status": "Verified"}' > /dev/null
    echo "  ✓ CWE-20 actualizado"
fi

# CWE-1287: Pendiente - actualizar descripción con estado actual
echo "Actualizando CWE-1287 (Pendiente)..."
UPDATE_DATA='{
    "description": "Uso de float() directamente sobre datos de entrada sin validar primero el tipo. Puede lanzar excepciones no controladas o producir valores inesperados (NaN, Infinity).\n\nESTADO ACTUAL: ⚠️ PENDIENTE DE CORRECCIÓN\n\nUbicación: app/routes.py líneas 36-39, 94-97\n\nAcción requerida:\n- Validar tipo antes de convertir\n- Verificar que el resultado sea un número finito después de la conversión\n- Usar excepciones específicas (ValueError, TypeError) en lugar de Exception genérico",
    "mitigation": "Validar tipo antes de convertir. Verificar que el resultado sea un número finito después de la conversión. Implementar validación similar a la usada en validate_and_sanitize_name().",
    "active": true,
    "verified": false,
    "status": "Active"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE1287_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-1287 actualizado"

# CWE-843: Pendiente - actualizar descripción con estado actual
echo "Actualizando CWE-843 (Pendiente)..."
UPDATE_DATA='{
    "description": "Uso de parseFloat() sin validar que el resultado sea un número válido. parseFloat() puede retornar NaN, que luego se propaga en cálculos matemáticos causando resultados incorrectos.\n\nESTADO ACTUAL: ⚠️ PENDIENTE DE CORRECCIÓN\n\nUbicación: app/static/js/main.js líneas 139, 207; app/static/js/storage.js línea 84\n\nAcción requerida:\n- Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite()\n- Agregar validación antes de usar valores en cálculos (IMC)",
    "mitigation": "Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite(). Agregar validación antes de usar valores en cálculos críticos como el IMC.",
    "active": true,
    "verified": false,
    "status": "Active"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE843_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-843 actualizado"

# CWE-1021: Resuelto - marcar como resuelto
echo "Actualizando CWE-1021 (Resuelto)..."
UPDATE_DATA='{
    "description": "Vulnerabilidad de clickjacking resuelta mediante la implementación de headers de seguridad.\n\nESTADO ACTUAL: ✅ RESUELTO\n\nMitigación implementada: Se agregaron headers de seguridad en app/__init__.py (líneas 28-36) que incluyen:\n- X-Frame-Options: DENY\n- Content-Security-Policy: frame-ancestors '\''none'\''\n- X-Content-Type-Options: nosniff\n- X-XSS-Protection: 1; mode=block\n\nEstos headers previenen que la aplicación sea embebida en iframes maliciosos y protegen contra ataques de clickjacking.",
    "mitigation": "✅ RESUELTO: Se implementaron headers de seguridad en app/__init__.py usando @app.after_request que agrega X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors '\''none'\'', X-Content-Type-Options: nosniff, y X-XSS-Protection: 1; mode=block a todas las respuestas HTTP.",
    "active": false,
    "verified": true,
    "status": "Verified"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE1021_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-1021 marcado como resuelto"

# CWE-703: Mejorado parcialmente - actualizar descripción con estado actual
echo "Actualizando CWE-703 (Mejorado parcialmente)..."
UPDATE_DATA='{
    "description": "Uso de Exception genérico en conversiones de float() que puede ocultar errores inesperados.\n\nESTADO ACTUAL: ⚠️ MEJORADO PARCIALMENTE\n\n✅ MEJORAS IMPLEMENTADAS:\n- La validación de nombres (CWE-20) ya usa manejo estructurado de errores\n- Retorna códigos de error específicos (name_empty, name_too_long, invalid_name)\n- Manejo proactivo en lugar de reactivo (try/except)\n\n⚠️ PENDIENTE:\n- Líneas 38 y 96 en app/routes.py aún usan Exception genérico en conversiones de float()\n- app/static/js/sync.js línea 119 captura cualquier error sin diferenciar tipos\n\nAcción requerida:\n- Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico\n- Agregar logging para debugging",
    "mitigation": "Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico. Agregar logging para debugging. Aplicar el mismo patrón de manejo estructurado de errores usado en la validación de nombres.",
    "active": true,
    "verified": false,
    "status": "Active"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE703_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-703 actualizado"

# CWE-942: Pendiente (aceptado temporalmente) - actualizar descripción con estado actual
echo "Actualizando CWE-942 (Pendiente - Aceptado temporalmente)..."
UPDATE_DATA='{
    "description": "CORS configurado para permitir cualquier origen (origins: '\''*'\''). Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación en el futuro.\n\nESTADO ACTUAL: ⏸️ PENDIENTE - ACEPTADO TEMPORALMENTE\n\nRazón de aceptación temporal:\n- La aplicación es monousuario y no requiere autenticación\n- No hay riesgo inmediato en el contexto actual\n- Se ajustará cuando se defina la arquitectura de despliegue final\n\nUbicación: app/__init__.py líneas 13-19\n\nAcción requerida (futuro):\n- Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue\n- Ajustar configuración si se implementa autenticación",
    "mitigation": "Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue final. Actualmente aceptado porque la aplicación es monousuario y no requiere autenticación. Si se implementa autenticación en el futuro, ajustar CORS es crítico para prevenir CSRF.",
    "active": true,
    "verified": false,
    "status": "Active"
}'
curl -s -X PATCH "${DEFECTDOJO_URL}/findings/${CWE942_ID}/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$UPDATE_DATA" > /dev/null
echo "  ✓ CWE-942 actualizado"

echo ""
echo "=== Resumen ==="
echo "✓ CWE-20: Resuelto (Verified, Active: False)"
echo "⚠️ CWE-1287: Pendiente (Active, Verified: False)"
echo "⚠️ CWE-843: Pendiente (Active, Verified: False)"
echo "✓ CWE-1021: Resuelto (Verified, Active: False)"
echo "⚠️ CWE-703: Mejorado parcialmente (Active, Verified: False)"
echo "⏸️ CWE-942: Pendiente - Aceptado temporalmente (Active, Verified: False)"
echo ""
echo "Puedes ver los findings actualizados en: http://localhost:8080/test/1/findings"


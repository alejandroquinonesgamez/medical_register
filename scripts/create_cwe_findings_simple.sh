#!/bin/bash
# Script simplificado para crear findings de CWE-699 en DefectDojo usando archivos JSON

DEFECTDOJO_URL="http://localhost/defectdojo/api/v2"
USERNAME="admin"
PASSWORD="admin"
TEMP_DIR=$(mktemp -d)

echo "=== Creando findings de CWE-699 en DefectDojo ==="
echo ""

# Obtener token
TOKEN=$(curl -s -X POST "${DEFECTDOJO_URL}/api-token-auth/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "Error: No se pudo obtener el token de API"
    exit 1
fi

# IDs conocidos (ya creados anteriormente)
TEST_ID=1
USER_ID=1

echo "Token obtenido"
echo "Test ID: $TEST_ID"
echo "Usuario ID: $USER_ID"
echo ""

# Crear findings usando archivos JSON
CREATED=0

# CWE-20: RESUELTO
cat > "${TEMP_DIR}/cwe20.json" << 'EOF'
{
    "title": "CWE-20: Validación de entrada insuficiente (nombres) - RESUELTO",
    "description": "Vulnerabilidad de validación de entrada en campos de nombre. Se ha implementado validación robusta con sanitización en backend y frontend.\n\nMitigación: Se implementó la función validate_and_sanitize_name() en app/helpers.py que valida longitud, elimina caracteres peligrosos, y normaliza espacios. Validación también implementada en frontend (app/static/js/config.js).\n\nImpacto: Bajo - Ya resuelto",
    "severity": "Medium",
    "numerical_severity": 3,
    "cwe": 20,
    "status": "Verified",
    "active": false,
    "verified": true,
    "test": 1,
    "found_by": [1],
    "mitigation": "Se implementó la función validate_and_sanitize_name() en app/helpers.py que valida longitud, elimina caracteres peligrosos, y normaliza espacios. Validación también implementada en frontend (app/static/js/config.js).",
    "impact": "Bajo - Ya resuelto",
    "references": "https://cwe.mitre.org/data/definitions/20.html",
    "file_path": "app/helpers.py, app/routes.py, app/static/js/config.js",
    "line": 53
}
EOF

echo "  Creando CWE-20 (Resuelto)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe20.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-20 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# CWE-1287
cat > "${TEMP_DIR}/cwe1287.json" << 'EOF'
{
    "title": "CWE-1287: Validación de tipo insuficiente",
    "description": "Uso de float() directamente sobre datos de entrada sin validar primero el tipo. Puede lanzar excepciones no controladas o producir valores inesperados (NaN, Infinity).",
    "severity": "Medium",
    "numerical_severity": 3,
    "cwe": 1287,
    "status": "Active",
    "active": true,
    "verified": false,
    "test": 1,
    "found_by": [1],
    "mitigation": "Validar tipo antes de convertir. Verificar que el resultado sea un número finito después de la conversión.",
    "impact": "Puede causar errores en cálculos posteriores (IMC) si se envían valores no numéricos o NaN/Infinity",
    "references": "https://cwe.mitre.org/data/definitions/1287.html",
    "file_path": "app/routes.py",
    "line": 36
}
EOF

echo "  Creando CWE-1287 (Pendiente)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe1287.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-1287 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# CWE-843
cat > "${TEMP_DIR}/cwe843.json" << 'EOF'
{
    "title": "CWE-843: Confusión de tipos (NaN no validado)",
    "description": "Uso de parseFloat() sin validar que el resultado sea un número válido. parseFloat() puede retornar NaN, que luego se propaga en cálculos matemáticos causando resultados incorrectos.",
    "severity": "Medium",
    "numerical_severity": 3,
    "cwe": 843,
    "status": "Active",
    "active": true,
    "verified": false,
    "test": 1,
    "found_by": [1],
    "mitigation": "Validar NaN e Infinity después de parseFloat() usando isNaN() e isFinite().",
    "impact": "Puede causar cálculos incorrectos de IMC y errores en validaciones si se introducen valores inválidos",
    "references": "https://cwe.mitre.org/data/definitions/843.html",
    "file_path": "app/static/js/main.js, app/static/js/storage.js",
    "line": 139
}
EOF

echo "  Creando CWE-843 (Pendiente)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe843.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-843 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# CWE-1021
cat > "${TEMP_DIR}/cwe1021.json" << 'EOF'
{
    "title": "CWE-1021: Falta de protección contra clickjacking",
    "description": "No se implementan headers de seguridad (X-Frame-Options, Content-Security-Policy) para prevenir clickjacking. La aplicación es vulnerable a ataques de clickjacking.",
    "severity": "Medium",
    "numerical_severity": 3,
    "cwe": 1021,
    "status": "Active",
    "active": true,
    "verified": false,
    "test": 1,
    "found_by": [1],
    "mitigation": "Agregar headers de seguridad en app/__init__.py: X-Frame-Options: DENY, Content-Security-Policy: frame-ancestors 'none', X-Content-Type-Options: nosniff",
    "impact": "Vulnerabilidad de seguridad conocida. Permite que la aplicación sea embebida en iframes maliciosos",
    "references": "https://cwe.mitre.org/data/definitions/1021.html",
    "file_path": "app/__init__.py",
    "line": null
}
EOF

echo "  Creando CWE-1021 (Pendiente)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe1021.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-1021 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# CWE-703
cat > "${TEMP_DIR}/cwe703.json" << 'EOF'
{
    "title": "CWE-703: Manejo de excepciones demasiado genérico - MEJORADO PARCIALMENTE",
    "description": "Uso de Exception genérico en conversiones de float() que puede ocultar errores inesperados. La validación de nombres ya usa manejo estructurado de errores, pero las conversiones numéricas aún usan Exception genérico.",
    "severity": "Low",
    "numerical_severity": 4,
    "cwe": 703,
    "status": "Active",
    "active": true,
    "verified": false,
    "test": 1,
    "found_by": [1],
    "mitigation": "Especificar excepciones específicas (ValueError, TypeError, KeyError) en lugar de Exception genérico. Agregar logging para debugging.",
    "impact": "Puede ocultar errores inesperados y dificultar el debugging",
    "references": "https://cwe.mitre.org/data/definitions/703.html",
    "file_path": "app/routes.py, app/static/js/sync.js",
    "line": 38
}
EOF

echo "  Creando CWE-703 (Mejorado parcialmente)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe703.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-703 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# CWE-942
cat > "${TEMP_DIR}/cwe942.json" << 'EOF'
{
    "title": "CWE-942: CORS demasiado permisivo",
    "description": "CORS configurado para permitir cualquier origen (origins: '*'). Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación en el futuro.",
    "severity": "Medium",
    "numerical_severity": 3,
    "cwe": 942,
    "status": "Active",
    "active": true,
    "verified": false,
    "test": 1,
    "found_by": [1],
    "mitigation": "Restringir CORS a dominios específicos cuando se defina la arquitectura de despliegue final. Actualmente aceptado porque la aplicación es monousuario y no requiere autenticación.",
    "impact": "Cualquier sitio web puede hacer peticiones a la API. Riesgo de CSRF si se implementa autenticación sin ajustar CORS",
    "references": "https://cwe.mitre.org/data/definitions/942.html",
    "file_path": "app/__init__.py",
    "line": 13
}
EOF

echo "  Creando CWE-942 (Pendiente - Aceptado)..."
HTTP_CODE=$(curl -s -w "\n%{http_code}" -X POST "${DEFECTDOJO_URL}/findings/" \
    -H "Authorization: Token ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${TEMP_DIR}/cwe942.json" | tail -n1)
if [ "$HTTP_CODE" = "201" ]; then
    echo "    ✓ CWE-942 creado"
    CREATED=$((CREATED + 1))
else
    echo "    ✗ Error: $HTTP_CODE"
fi

# Limpiar
rm -rf "${TEMP_DIR}"

echo ""
echo "=== Resumen ==="
echo "Findings creados: $CREATED/6"
echo "Puedes ver los findings en: http://localhost/defectdojo/test/1/findings"


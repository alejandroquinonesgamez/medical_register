# Análisis de Seguridad según CWE-699

## Resumen Ejecutivo

Este documento analiza el código de la aplicación médica según la vista **CWE-699: Software Development** de MITRE, que categoriza debilidades comunes en el desarrollo de software. Se identifican posibles vulnerabilidades y se proporcionan recomendaciones de mejora.

**Referencia**: [CWE-699](https://cwe.mitre.org/data/definitions/699.html)

---

## 1. Type Errors (Errores de Tipo)

### 1.1 CWE-1287: Improper Validation of Specified Type of Input

**Ubicación**: `app/routes.py`

**Problema identificado**:
- En las líneas 37, 75, se usa `float()` directamente sobre datos de entrada sin validar primero el tipo.
- En la línea 44, se usa `datetime.strptime()` sin validar que el formato sea correcto.

**Código afectado**:
```python
# Línea 37
height_m = float(data['talla_m'])

# Línea 75
weight_kg = float(data['peso_kg'])

# Línea 44
birth_date = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
```

**Riesgo**: Si `data['talla_m']` o `data['peso_kg']` no son números válidos, `float()` puede lanzar excepciones no controladas o producir valores inesperados (NaN, Infinity).

**Recomendación**:
```python
# Validar tipo antes de convertir
if not isinstance(data.get('talla_m'), (int, float, str)):
    return jsonify({"error": get_error("invalid_height")}), 400
try:
    height_m = float(data['talla_m'])
    if not math.isfinite(height_m):
        return jsonify({"error": get_error("invalid_height")}), 400
except (ValueError, TypeError):
    return jsonify({"error": get_error("invalid_height")}), 400
```

**Severidad**: Media

---

### 1.2 CWE-843: Access of Resource Using Incompatible Type ('Type Confusion')

**Ubicación**: `app/static/js/storage.js`, `app/static/js/main.js`

**Problema identificado**:
- En `storage.js` línea 84, se usa `parseFloat()` sin validar que el resultado sea un número válido.
- En `main.js` línea 139, se usa `parseFloat()` sin verificar NaN.

**Código afectado**:
```javascript
// storage.js línea 84
peso_kg: parseFloat(weight.peso_kg),

// main.js línea 139
const talla_m = parseFloat(document.getElementById('talla_m').value);
```

**Riesgo**: `parseFloat()` puede retornar `NaN`, que luego se propaga en cálculos matemáticos causando resultados incorrectos.

**Recomendación**:
```javascript
const talla_m = parseFloat(document.getElementById('talla_m').value);
if (isNaN(talla_m) || !isFinite(talla_m)) {
    alert(MESSAGES.errors.invalid_height || 'Altura inválida');
    return;
}
```

**Severidad**: Media

---

## 2. User Interface Security Issues (Problemas de Seguridad en la UI)

### 2.1 CWE-356: Product UI does not Warn User of Unsafe Actions

**Ubicación**: `app/static/js/dev-tools.js` (si existe)

**Problema identificado**:
- La función `clearAllData()` en dev-tools muestra un `confirm()`, pero no advierte claramente sobre la pérdida permanente de datos.
- No hay advertencia visual antes de acciones destructivas en la UI principal.

**Recomendación**:
- Implementar advertencias más claras con iconos y texto destacado.
- Agregar confirmación doble para acciones destructivas.

**Severidad**: Baja (solo afecta dev-tools)

---

### 2.2 CWE-1021: Improper Restriction of Rendered UI Layers or Frames

**Ubicación**: `app/templates/index.html`

**Problema identificado**:
- No se encontraron restricciones explícitas de iframes o frames en el código HTML.
- La aplicación no implementa políticas de seguridad de contenido (CSP) para prevenir clickjacking.

**Recomendación**:
```python
# En app/__init__.py, agregar headers de seguridad
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
    return response
```

**Severidad**: Media

---

## 3. Input Validation (Validación de Entrada)

### 3.1 CWE-20: Improper Input Validation (relacionado) ✅ RESUELTO

**Ubicación**: `app/routes.py`, `app/helpers.py`, `app/static/js/config.js`, `app/static/js/main.js`

**Estado**: ✅ **IMPLEMENTADO**

**Solución implementada**:
- Se creó la función `validate_and_sanitize_name()` en `app/helpers.py` que:
  - Valida que el nombre no esté vacío
  - Valida longitud (1-100 caracteres, configurable)
  - Elimina caracteres peligrosos: `< > " '`
  - Normaliza espacios múltiples
  - Permite solo letras (incluyendo Unicode/acentes), espacios, guiones y apóstrofes
  - Sanitiza el string antes de almacenarlo

- Se implementó validación en el backend (`app/routes.py` líneas 53-71):
  ```python
  # Validar y sanitizar nombre
  nombre_raw = data.get('nombre', '')
  is_valid_nombre, nombre_sanitized, error_key_nombre = validate_and_sanitize_name(
      nombre_raw,
      min_length=VALIDATION_LIMITS["name_min_length"],
      max_length=VALIDATION_LIMITS["name_max_length"]
  )
  if not is_valid_nombre:
      return jsonify({"error": get_error(error_key_nombre or "invalid_name")}), 400
  ```

- Se implementó validación en el frontend (`app/static/js/main.js` líneas 147-167):
  ```javascript
  // Validar y sanitizar nombre
  const nombreValidation = AppConfig.validateAndSanitizeName(nombreInput);
  if (!nombreValidation.isValid) {
      alert(MESSAGES.errors[nombreValidation.errorKey] || 'El nombre no es válido');
      return;
  }
  ```

- Se agregaron límites de validación en `app/config.py`:
  ```python
  "name_min_length": 1,
  "name_max_length": 100,
  ```

- Se agregaron mensajes de error específicos en `app/languages/es.py`

**Severidad**: Media → ✅ Resuelto

---

### 3.2 Validación de JSON Malformado

**Ubicación**: `app/routes.py` línea 34

**Problema identificado**:
- `request.json or {}` puede fallar si el JSON está malformado, causando una excepción no manejada.

**Código afectado**:
```python
data = request.json or {}
```

**Riesgo**: Si el cliente envía JSON malformado, Flask puede lanzar una excepción que no se captura.

**Recomendación**:
```python
try:
    data = request.get_json(force=True) or {}
except Exception:
    return jsonify({"error": get_error("invalid_json")}), 400
```

**Severidad**: Baja

---

## 4. Error Handling (Manejo de Errores)

### 4.1 CWE-703: Improper Check or Handling of Exceptional Conditions

**Ubicación**: `app/routes.py`, `app/static/js/sync.js`

**Estado**: ⚠️ **MEJORADO PARCIALMENTE**

**Problema identificado**:
- En `routes.py` líneas 38 y 76, se captura `Exception` genérico para conversión de tipos, lo que puede ocultar errores inesperados.
- En `sync.js` línea 119, se captura cualquier error sin diferenciar tipos.

**Código afectado**:
```python
# routes.py línea 36-39
try:
    height_m = float(data['talla_m'])
except Exception:  # Muy genérico
    return jsonify({"error": get_error("invalid_height")}), 400

# routes.py línea 74-77
try:
    weight_kg = float(data['peso_kg'])
except Exception:  # Muy genérico
    return jsonify({"error": get_error("invalid_weight")}), 400
```

**Mejora implementada**:
- ✅ **Validación de nombres mejorada**: La función `validate_and_sanitize_name()` en `app/helpers.py` y su uso en `app/routes.py` (líneas 53-71) implementa un manejo de errores más estructurado:
  - No usa `try/except Exception` genérico
  - Retorna tuplas con información específica de error: `(is_valid, sanitized, error_key)`
  - Proporciona códigos de error específicos (`name_empty`, `name_too_long`, `invalid_name`, etc.)
  - Permite un manejo más granular y específico de errores

**Código mejorado**:
```python
# routes.py líneas 53-71 - Validación de nombres (mejorada)
nombre_raw = data.get('nombre', '')
is_valid_nombre, nombre_sanitized, error_key_nombre = validate_and_sanitize_name(
    nombre_raw,
    min_length=VALIDATION_LIMITS["name_min_length"],
    max_length=VALIDATION_LIMITS["name_max_length"]
)
if not is_valid_nombre:
    return jsonify({"error": get_error(error_key_nombre or "invalid_name")}), 400
```

**Pendiente**:
- ⚠️ Aún se usa `Exception` genérico en las conversiones de `float()` para altura y peso (líneas 38, 76)
- ⚠️ El manejo de errores en `sync.js` sigue siendo genérico

**Recomendación para las partes pendientes**:
```python
try:
    height_m = float(data['talla_m'])
except (ValueError, TypeError, KeyError) as e:
    # Log del error para debugging
    current_app.logger.warning(f"Error al convertir altura: {e}")
    return jsonify({"error": get_error("invalid_height")}), 400
```

**Severidad**: Baja (mejorada parcialmente)

---

## 5. User Session Errors (Errores de Sesión)

### 5.1 CWE-488: Exposure of Data Element to Wrong Session

**Ubicación**: `app/config.py` línea 8

**Problema identificado**:
- La aplicación usa un `USER_ID = 1` fijo, lo que significa que todos los usuarios comparten los mismos datos.
- No hay autenticación ni gestión de sesiones.

**Código afectado**:
```python
USER_ID = 1  # Monousuario fijo
```

**Riesgo**: 
- En un entorno multi-usuario, todos los usuarios verían y modificarían los mismos datos.
- No hay aislamiento de datos entre usuarios.

**Estado**: ⏸️ **PENDIENTE - PLANIFICADO PARA FUTURO**

**Nota**: El desarrollador ha indicado que tiene planificado implementar soporte multi-usuario en el futuro. Esta debilidad se abordará cuando se implemente la funcionalidad de autenticación y gestión de sesiones.

**Severidad**: Alta (si se despliega en entorno multi-usuario)

---

### 5.2 CWE-613: Insufficient Session Expiration

**Ubicación**: No aplicable (aplicación sin sesiones)

**Estado**: No hay gestión de sesiones en la aplicación actual.

---

## 6. CORS Configuration (Configuración CORS)

### 6.1 CWE-942: Overly Permissive Cross-domain Whitelist

**Ubicación**: `app/__init__.py` línea 13-19

**Problema identificado**:
- CORS está configurado para permitir cualquier origen (`"origins": "*"`).

**Código afectado**:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Permite cualquier origen
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Riesgo**: 
- Cualquier sitio web puede hacer peticiones a la API.
- Riesgo de CSRF (Cross-Site Request Forgery) si se implementa autenticación en el futuro.

**Estado**: ⏸️ **PENDIENTE - PLANIFICADO PARA FUTURO**

**Nota**: El desarrollador ha indicado que tiene planificado implementar soporte multi-usuario en el futuro. La configuración de CORS se ajustará cuando se implemente la funcionalidad de autenticación y se defina la arquitectura de despliegue final.

**Recomendación futura**:
```python
# En producción, restringir a dominios específicos
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://tu-dominio.com", "https://www.tu-dominio.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Severidad**: Media (alta en producción)

---

## 7. Data Integrity (Integridad de Datos)

### 7.1 Validación Defensiva Implementada ✅

**Ubicación**: `app/routes.py` líneas 130-133, `app/static/js/main.js` líneas 100-114

**Estado**: La aplicación implementa validaciones defensivas antes de calcular el IMC, lo cual es una buena práctica.

**Código positivo**:
```python
# Backend - Validación defensiva
if not (VALIDATION_LIMITS["weight_min"] <= last_weight.weight_kg <= VALIDATION_LIMITS["weight_max"]):
    return jsonify({"error": get_error("weight_out_of_range")}), 400
```

**Evaluación**: ✅ Buena práctica implementada

---

## Resumen de Debilidades Identificadas

| CWE | Descripción | Severidad | Ubicación | Estado |
|-----|-------------|-----------|-----------|--------|
| CWE-1287 | Validación de tipo insuficiente | Media | `routes.py` | ⚠️ Requiere atención |
| CWE-843 | Confusión de tipos (NaN no validado) | Media | `storage.js`, `main.js` | ⚠️ Requiere atención |
| CWE-356 | Falta de advertencia en acciones destructivas | Baja | `dev-tools.js` | ⚠️ Mejora recomendada |
| CWE-1021 | Falta de protección contra clickjacking | Media | `__init__.py` | ⚠️ Requiere atención |
| CWE-20 | Validación de entrada insuficiente (nombres) | Media | `routes.py`, `helpers.py`, `main.js` | ✅ **RESUELTO** |
| CWE-703 | Manejo de excepciones demasiado genérico | Baja | `routes.py`, `sync.js` | ⚠️ **MEJORADO PARCIALMENTE** |
| CWE-488 | Exposición de datos entre sesiones | Alta* | `config.py` | ⏸️ Pendiente (planificado) |
| CWE-942 | CORS demasiado permisivo | Media/Alta | `__init__.py` | ⏸️ Pendiente (planificado) |

*Alta solo si se despliega en entorno multi-usuario

---

## Recomendaciones Prioritarias

### Prioridad Alta
1. ~~**Restringir CORS en producción**~~ - ⏸️ Pendiente (planificado para implementación multi-usuario)
2. ~~**Documentar o corregir USER_ID fijo**~~ - ⏸️ Pendiente (planificado para implementación multi-usuario)
3. **Agregar headers de seguridad** - Implementar X-Frame-Options y CSP

### Prioridad Media
4. **Validar tipos antes de conversión** - Verificar que los datos sean del tipo esperado antes de `float()` o `parseFloat()`
5. ~~**Validar y sanitizar nombres**~~ - ✅ **IMPLEMENTADO** - Validación robusta en backend y frontend
6. **Manejar NaN e Infinity** - Validar que los números sean finitos después de conversión

### Prioridad Baja
7. **Mejorar manejo de excepciones** - ⚠️ **MEJORADO PARCIALMENTE**: La validación de nombres usa manejo estructurado de errores. Pendiente: mejorar conversiones de `float()` y manejo en `sync.js`
8. **Mejorar advertencias en UI** - Hacer más claras las advertencias para acciones destructivas

---

## Conclusión

La aplicación implementa buenas prácticas de validación defensiva y manejo de errores en general. Sin embargo, hay áreas de mejora relacionadas con:

1. **Validación de tipos más estricta** antes de conversiones
2. **Configuración de seguridad** (CORS, headers de seguridad)
3. **Validación de entrada** más completa (especialmente en campos de texto)
4. **Documentación clara** sobre el modelo de usuario (monousuario vs multi-usuario)

La mayoría de las debilidades identificadas son de severidad media o baja, y pueden corregirse sin cambios arquitectónicos significativos.

---

**Fecha de análisis**: 2025-01-27  
**Versión analizada**: Mayor Update (commit 24bfc76)  
**Referencia CWE**: [CWE-699](https://cwe.mitre.org/data/definitions/699.html)


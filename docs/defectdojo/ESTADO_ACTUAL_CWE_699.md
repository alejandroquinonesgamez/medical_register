# Estado Actual del Programa - Análisis CWE-699

**Fecha de análisis**: 2025-01-27  
**Versión analizada**: Mayor Update (post-implementación de validación de nombres)

---

## Resumen Ejecutivo

El programa ha mejorado significativamente en validación de entrada y manejo de errores estructurado, pero aún presenta algunas debilidades de seguridad que requieren atención, especialmente relacionadas con validación de tipos y headers de seguridad.

---

## Estado Detallado por Categoría

### 1. Type Errors (Errores de Tipo) ⚠️ **REQUIERE ATENCIÓN**

#### 1.1 CWE-1287: Improper Validation of Specified Type of Input
**Estado**: ⚠️ **PENDIENTE**

**Ubicación**: `app/routes.py` líneas 36-39 y 94-97

**Problema actual**:
```python
# Línea 36-39
try:
    height_m = float(data['talla_m'])
except Exception:  # ⚠️ Muy genérico
    return jsonify({"error": get_error("invalid_height")}), 400

# Línea 94-97
try:
    weight_kg = float(data['peso_kg'])
except Exception:  # ⚠️ Muy genérico
    return jsonify({"error": get_error("invalid_weight")}), 400
```

**Problemas identificados**:
- ❌ Usa `Exception` genérico que puede ocultar errores inesperados
- ❌ No valida que el resultado sea un número finito (puede ser NaN o Infinity)
- ❌ No valida el tipo antes de la conversión

**Impacto**: Si se envía un valor que no es convertible a float, o si el resultado es NaN/Infinity, puede causar errores en cálculos posteriores.

---

#### 1.2 CWE-843: Access of Resource Using Incompatible Type ('Type Confusion')
**Estado**: ⚠️ **PENDIENTE**

**Ubicación**: `app/static/js/main.js` líneas 139, 207; `app/static/js/storage.js` línea 84

**Problema actual**:
```javascript
// main.js línea 139
const talla_m = parseFloat(document.getElementById('talla_m').value);
// ⚠️ No valida si es NaN o Infinity

// main.js línea 207
const weight_kg = parseFloat(document.getElementById('peso').value);
// ⚠️ No valida si es NaN o Infinity

// storage.js línea 84
peso_kg: parseFloat(weight.peso_kg),
// ⚠️ No valida si es NaN o Infinity
```

**Problemas identificados**:
- ❌ `parseFloat()` puede retornar `NaN` sin validación
- ❌ No se verifica `isFinite()` después de la conversión
- ❌ Los valores NaN pueden propagarse en cálculos matemáticos

**Impacto**: Si un usuario introduce un valor inválido, `parseFloat()` retorna `NaN`, que luego se usa en cálculos (IMC, validaciones) causando resultados incorrectos o errores.

---

### 2. User Interface Security Issues ⚠️ **REQUIERE ATENCIÓN**

#### 2.1 CWE-1021: Improper Restriction of Rendered UI Layers or Frames
**Estado**: ⚠️ **PENDIENTE**

**Ubicación**: `app/__init__.py`

**Problema actual**:
- ❌ No hay headers de seguridad configurados
- ❌ No hay `X-Frame-Options` para prevenir clickjacking
- ❌ No hay `Content-Security-Policy` para restringir frames
- ❌ No hay `X-Content-Type-Options` para prevenir MIME sniffing

**Impacto**: La aplicación es vulnerable a ataques de clickjacking y no tiene protección contra inyección de contenido malicioso a través de iframes.

---

### 3. Input Validation (Validación de Entrada) ✅ **RESUELTO**

#### 3.1 CWE-20: Improper Input Validation
**Estado**: ✅ **IMPLEMENTADO CORRECTAMENTE**

**Ubicación**: `app/helpers.py`, `app/routes.py`, `app/static/js/config.js`, `app/static/js/main.js`

**Implementación actual**:
- ✅ Función `validate_and_sanitize_name()` en backend
- ✅ Función `validateAndSanitizeName()` en frontend
- ✅ Validación de longitud (1-100 caracteres)
- ✅ Eliminación de caracteres peligrosos (`< > " '`)
- ✅ Normalización de espacios múltiples
- ✅ Validación de caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
- ✅ Validación en backend y frontend (defensa en profundidad)

**Código implementado**:
```python
# Backend - routes.py líneas 53-71
nombre_raw = data.get('nombre', '')
is_valid_nombre, nombre_sanitized, error_key_nombre = validate_and_sanitize_name(
    nombre_raw,
    min_length=VALIDATION_LIMITS["name_min_length"],
    max_length=VALIDATION_LIMITS["name_max_length"]
)
if not is_valid_nombre:
    return jsonify({"error": get_error(error_key_nombre or "invalid_name")}), 400
```

```javascript
// Frontend - main.js líneas 147-167
const nombreValidation = AppConfig.validateAndSanitizeName(nombreInput);
if (!nombreValidation.isValid) {
    alert(MESSAGES.errors[nombreValidation.errorKey] || 'El nombre no es válido');
    return;
}
```

**Estado**: ✅ **COMPLETAMENTE IMPLEMENTADO Y FUNCIONAL**

---

### 4. Error Handling (Manejo de Errores) ⚠️ **MEJORADO PARCIALMENTE**

#### 4.1 CWE-703: Improper Check or Handling of Exceptional Conditions
**Estado**: ⚠️ **MEJORADO PARCIALMENTE**

**Mejoras implementadas**:
- ✅ Validación de nombres usa manejo estructurado de errores (no `Exception` genérico)
- ✅ Retorna códigos de error específicos (`name_empty`, `name_too_long`, `invalid_name`)
- ✅ Manejo proactivo en lugar de reactivo (try/except)

**Pendiente**:
- ⚠️ Líneas 38 y 96 en `routes.py` aún usan `Exception` genérico
- ⚠️ `sync.js` línea 119 captura cualquier error sin diferenciar tipos

**Impacto**: El manejo de errores en validación de nombres es robusto, pero otras partes del código aún pueden ocultar errores inesperados.

---

### 5. CORS Configuration ⏸️ **PENDIENTE**

#### 5.1 CWE-942: Overly Permissive Cross-domain Whitelist
**Estado**: ⏸️ **PENDIENTE**

**Ubicación**: `app/__init__.py` líneas 13-19

**Estado actual**:
```python
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # ⚠️ Permite cualquier origen
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

**Impacto actual**: Cualquier sitio web puede hacer peticiones a la API si el backend se expone fuera de `localhost`.

---

### 6. Data Integrity (Integridad de Datos) ✅ **IMPLEMENTADO**

#### 7.1 Validación Defensiva
**Estado**: ✅ **IMPLEMENTADO CORRECTAMENTE**

**Ubicación**: `app/routes.py` líneas 148-153, `app/static/js/main.js` líneas 98-114

**Implementación actual**:
- ✅ Validación defensiva antes de calcular IMC en backend
- ✅ Validación defensiva antes de calcular IMC en frontend
- ✅ Verifica que peso y altura estén dentro de límites antes de usar funciones helper
- ✅ Protege contra datos antiguos o corruptos

**Código implementado**:
```python
# Backend - routes.py líneas 148-153
if not (VALIDATION_LIMITS["weight_min"] <= last_weight.weight_kg <= VALIDATION_LIMITS["weight_max"]):
    return jsonify({"error": get_error("weight_out_of_range")}), 400
if not (VALIDATION_LIMITS["height_min"] <= user.height_m <= VALIDATION_LIMITS["height_max"]):
    return jsonify({"error": get_error("height_out_of_range")}), 400
```

```javascript
// Frontend - main.js líneas 100-114
if (!AppConfig.validateWeight(lastWeight.peso_kg)) {
    imcValue.textContent = '0';
    imcDescription.textContent = MESSAGES.errors.weight_out_of_range || 
        `Peso fuera de rango: ${lastWeight.peso_kg} kg`;
    return;
}
```

**Estado**: ✅ **COMPLETAMENTE IMPLEMENTADO Y FUNCIONAL**

---

## Resumen de Estado por CWE

| CWE | Descripción | Estado | Prioridad | Acción Requerida |
|-----|-------------|--------|-----------|------------------|
| **CWE-1287** | Validación de tipo insuficiente | ⚠️ Pendiente | Media | Mejorar validación de tipos en `float()` |
| **CWE-843** | Confusión de tipos (NaN no validado) | ⚠️ Pendiente | Media | Validar `NaN` e `Infinity` después de `parseFloat()` |
| **CWE-1021** | Falta de protección contra clickjacking | ⚠️ Pendiente | Media | Agregar headers de seguridad |
| **CWE-20** | Validación de entrada insuficiente (nombres) | ✅ Resuelto | - | Ninguna |
| **CWE-703** | Manejo de excepciones demasiado genérico | ⚠️ Mejorado parcialmente | Baja | Mejorar excepciones en conversiones de `float()` |
| **CWE-942** | CORS demasiado permisivo | ⏸️ Pendiente | Media/Alta | Restringir CORS cuando se exponga el backend |

---

## Puntos Fuertes del Programa ✅

1. **Validación de nombres robusta**: Implementación completa con sanitización y validación en múltiples capas
2. **Validaciones defensivas**: Protección contra datos corruptos antes de cálculos críticos
3. **Manejo estructurado de errores**: En validación de nombres, usa códigos de error específicos
4. **Configuración centralizada**: Límites de validación en un solo lugar (`app/config.py`)
5. **Defensa en profundidad**: Validaciones tanto en frontend como en backend

---

## Áreas de Mejora Prioritarias 🔴

### Prioridad Alta (Seguridad Crítica)
1. **Validar NaN e Infinity** en frontend después de `parseFloat()`
   - Ubicación: `app/static/js/main.js` líneas 139, 207
   - Impacto: Puede causar cálculos incorrectos o errores

2. **Agregar headers de seguridad** para prevenir clickjacking
   - Ubicación: `app/__init__.py`
   - Impacto: Vulnerabilidad de seguridad conocida

### Prioridad Media (Robustez)
3. **Mejorar validación de tipos** en conversiones de `float()`
   - Ubicación: `app/routes.py` líneas 36-39, 94-97
   - Impacto: Puede ocultar errores inesperados

4. **Validar que números sean finitos** después de conversión
   - Ubicación: `app/routes.py` (después de `float()`)
   - Impacto: Previene cálculos con NaN/Infinity

### Prioridad Baja (Mejoras)
5. **Mejorar manejo de excepciones** en conversiones restantes
   - Ubicación: `app/routes.py` líneas 38, 96
   - Impacto: Mejor debugging y manejo de errores

---

## Conclusión

El programa ha mejorado significativamente en validación de entrada y manejo de errores estructurado. Las áreas principales que requieren atención son:

1. **Validación de tipos numéricos**: Especialmente validación de NaN/Infinity en frontend
2. **Headers de seguridad**: Implementar protección contra clickjacking
3. **Manejo de excepciones**: Especificar excepciones en lugar de `Exception` genérico

Las acciones pendientes de CORS y cabeceras se aplicarán cuando el backend salga del entorno local.

**Estado general**: ⚠️ **BUENO CON ÁREAS DE MEJORA IDENTIFICADAS**

---

**Última actualización**: 2025-01-27








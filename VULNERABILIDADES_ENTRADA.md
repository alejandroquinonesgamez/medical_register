# Análisis de Vulnerabilidades a Nivel de Entrada

**Fecha:** 2026-01-12  
**Aplicación:** Medical Register - Registro de Peso e IMC  
**Versión:** Producción (main)

---

## Resumen Ejecutivo

Se ha realizado un análisis exhaustivo de las vulnerabilidades a nivel de entrada en la aplicación. Se identificaron **1 vulnerabilidad crítica** y **3 mejoras recomendadas**.

### Estado General: ✅ BUENO (con mejoras recomendadas)

La aplicación implementa validaciones robustas en múltiples capas (frontend y backend), sanitización de nombres, y headers de seguridad. Sin embargo, se encontró un bug crítico en el código que debe corregirse.

---

## Vulnerabilidades Críticas

### 🔴 CRÍTICA: Variable no definida en storage.js

**Ubicación:** `app/static/js/storage.js:89`

**Descripción:**
La función `addWeight()` utiliza la variable `currentDate` que no está definida, lo que causará un error `ReferenceError` en tiempo de ejecución.

**Código afectado:**
```javascript
const newWeight = {
    id: Date.now(),
    peso_kg: peso_kg_parsed,
    fecha_registro: currentDate.toISOString()  // ❌ currentDate no está definido
};
```

**Impacto:**
- **Severidad:** ALTA
- **Probabilidad:** ALTA (ocurre en cada intento de guardar peso)
- **Consecuencia:** La aplicación fallará al intentar guardar un nuevo peso, rompiendo la funcionalidad principal

**Solución:**
```javascript
const currentDate = new Date();  // Agregar esta línea antes de usarla
const newWeight = {
    id: Date.now(),
    peso_kg: peso_kg_parsed,
    fecha_registro: currentDate.toISOString()
};
```

**CWE:** CWE-20 (Improper Input Validation) - Error de programación que impide la validación correcta

---

## Vulnerabilidades de Seguridad

### ✅ PROTECCIÓN XSS: Implementada correctamente

**Estado:** ✅ RESUELTO

**Implementación:**
1. **Backend:** Sanitización de nombres mediante `validate_and_sanitize_name()` que elimina caracteres peligrosos (`<`, `>`, `"`, `'`)
2. **Frontend:** Uso de `textContent` en lugar de `innerHTML` para la mayoría de los casos
3. **Headers de seguridad:** `X-XSS-Protection: 1; mode=block` configurado

**Ubicaciones:**
- `app/helpers.py:43-102` - Función de sanitización
- `app/__init__.py:28-36` - Headers de seguridad
- `app/static/js/main.js:84,93,119` - Uso de `textContent`

**Nota:** Hay 2 usos de `innerHTML` en `main.js:350,355` que requieren atención (ver mejoras recomendadas).

---

### ✅ VALIDACIÓN DE TIPOS: Implementada correctamente

**Estado:** ✅ RESUELTO

**Implementación:**
1. **Validación de tipos numéricos:**
   - Verificación de `isinstance()` antes de conversión
   - Validación de `math.isfinite()` para evitar NaN/Infinity
   - Validación de rangos (min/max)

2. **Validación de fechas:**
   - Parsing con `datetime.strptime()` y manejo de excepciones
   - Validación de rangos de fechas

**Ubicaciones:**
- `app/routes.py:49-69` - Validación de altura
- `app/routes.py:122-142` - Validación de peso
- `app/routes.py:71-79` - Validación de fecha de nacimiento
- `app/static/js/main.js:143-146,219-222` - Validación frontend

**Ejemplo de validación robusta:**
```python
# Validar que sea convertible a float
if not isinstance(talla_raw, (int, float, str)):
    return jsonify({"error": get_error("invalid_height")}), 400

try:
    height_m = float(talla_raw)
except (ValueError, TypeError):
    return jsonify({"error": get_error("invalid_height")}), 400

# Verificar que sea un número finito
if not math.isfinite(height_m):
    return jsonify({"error": get_error("invalid_height")}), 400
```

---

### ✅ SANITIZACIÓN DE NOMBRES: Implementada correctamente

**Estado:** ✅ RESUELTO

**Implementación:**
- Eliminación de caracteres peligrosos: `<`, `>`, `"`, `'`
- Normalización de espacios múltiples
- Validación de caracteres permitidos (letras Unicode, espacios, guiones, apóstrofes)
- Validación de longitud (1-100 caracteres)

**Ubicaciones:**
- `app/helpers.py:43-102` - Función backend
- `app/static/js/config.js:104-151` - Función frontend
- `app/routes.py:81-99` - Uso en API

---

### ⚠️ PROTECCIÓN CSRF: No implementada (aceptable en contexto actual)

**Estado:** ⚠️ ACEPTADO TEMPORALMENTE

**Descripción:**
La aplicación no implementa protección CSRF (Cross-Site Request Forgery). Sin embargo, esto es aceptable en el contexto actual porque:
- La aplicación es monousuario (no requiere autenticación)
- No hay sesiones de usuario
- No hay datos sensibles que puedan ser modificados por terceros

**Riesgo actual:** BAJO

**Recomendación futura:**
Si se implementa autenticación o múltiples usuarios, implementar:
- Tokens CSRF
- SameSite cookies
- Verificación de origen en requests

**Ubicación:** `app/__init__.py:13-19` - CORS configurado para permitir cualquier origen

---

## Mejoras Recomendadas

### 🟡 MEJORA 1: Uso de innerHTML en main.js

**Ubicación:** `app/static/js/main.js:350,355`

**Descripción:**
Se utiliza `innerHTML` para insertar contenido HTML dinámico. Aunque los datos provienen del backend (que ya sanitiza), es mejor práctica usar métodos más seguros.

**Código actual:**
```javascript
recentWeightsList.innerHTML = '<li class="no-data">No hay registros de peso aún</li>';
recentWeightsList.innerHTML = weights.map(entry => {
    // ... código que genera HTML
}).join('');
```

**Recomendación:**
- Usar `textContent` para texto simple
- Usar `createElement()` y `appendChild()` para elementos complejos
- O usar una librería de templating que escape automáticamente

**Prioridad:** MEDIA (los datos ya están sanitizados en backend)

---

### 🟡 MEJORA 2: Validación de Content-Type en requests

**Ubicación:** `app/routes.py` - Todas las rutas POST

**Descripción:**
No se valida explícitamente que el `Content-Type` sea `application/json` antes de procesar `request.json`.

**Recomendación:**
```python
@api.route('/user', methods=['POST'])
def create_or_update_user():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    # ... resto del código
```

**Prioridad:** BAJA (Flask maneja esto automáticamente, pero es buena práctica)

---

### 🟡 MEJORA 3: Rate Limiting

**Ubicación:** Global

**Descripción:**
No hay límites de tasa (rate limiting) para prevenir abuso de la API.

**Recomendación:**
Implementar rate limiting usando `flask-limiter`:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

**Prioridad:** BAJA (aplicación monousuario, bajo riesgo)

---

## Validaciones Implementadas

### ✅ Backend (Python/Flask)

1. **Validación de tipos:**
   - ✅ Verificación de `isinstance()` antes de conversión
   - ✅ Manejo de excepciones en conversiones
   - ✅ Validación de `math.isfinite()` para números

2. **Validación de rangos:**
   - ✅ Altura: 0.4 - 2.72 metros
   - ✅ Peso: 2 - 650 kg
   - ✅ Fecha de nacimiento: 1900-01-01 hasta hoy
   - ✅ Variación de peso: máximo 5 kg/día

3. **Sanitización:**
   - ✅ Eliminación de caracteres peligrosos en nombres
   - ✅ Normalización de espacios
   - ✅ Validación de longitud (1-100 caracteres)

### ✅ Frontend (JavaScript)

1. **Validación de tipos:**
   - ✅ Verificación de `isNaN()` y `isFinite()`
   - ✅ Validación antes de enviar al backend

2. **Validación de rangos:**
   - ✅ Atributos `min` y `max` en inputs HTML
   - ✅ Validación JavaScript antes de submit

3. **Sanitización:**
   - ✅ Función `validateAndSanitizeName()` en frontend
   - ✅ Uso de `textContent` en lugar de `innerHTML` (mayoría de casos)

---

## Headers de Seguridad

### ✅ Implementados

```python
response.headers['X-Frame-Options'] = 'DENY'
response.headers['X-Content-Type-Options'] = 'nosniff'
response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
response.headers['X-XSS-Protection'] = '1; mode=block'
```

**Ubicación:** `app/__init__.py:28-36`

**Protección:**
- ✅ Clickjacking (X-Frame-Options)
- ✅ MIME sniffing (X-Content-Type-Options)
- ✅ XSS (X-XSS-Protection)

---

## Recomendaciones de Acción

### Prioridad ALTA (Corregir inmediatamente)

1. **Corregir bug en storage.js:89**
   - Agregar `const currentDate = new Date();` antes de usarlo
   - Probar que la funcionalidad de guardar peso funciona correctamente

### Prioridad MEDIA (Implementar en próxima iteración)

2. **Reemplazar innerHTML por métodos más seguros**
   - Usar `createElement()` y `appendChild()`
   - O usar una librería de templating

3. **Validar Content-Type explícitamente**
   - Agregar verificación `request.is_json` en rutas POST

### Prioridad BAJA (Considerar para futuro)

4. **Implementar rate limiting**
   - Solo necesario si se implementa autenticación o múltiples usuarios

5. **Mejorar protección CSRF**
   - Solo necesario si se implementa autenticación

---

## Conclusión

La aplicación tiene una **base sólida de validación y sanitización** implementada en múltiples capas. Las vulnerabilidades críticas encontradas son principalmente **bugs de programación** más que vulnerabilidades de seguridad.

**Puntos fuertes:**
- ✅ Validación robusta de tipos y rangos
- ✅ Sanitización de nombres implementada
- ✅ Headers de seguridad configurados
- ✅ Validación en frontend y backend

**Áreas de mejora:**
- 🔴 Corregir bug crítico en storage.js
- 🟡 Mejorar uso de innerHTML
- 🟡 Agregar validación explícita de Content-Type

**Estado general:** ✅ BUENO (con 1 corrección crítica necesaria)

---

## Referencias

- **CWE-20:** Improper Input Validation
- **CWE-79:** Cross-site Scripting (XSS)
- **CWE-352:** Cross-Site Request Forgery (CSRF)
- **OWASP Top 10:** A03:2021 – Injection
- **OWASP Top 10:** A07:2021 – Identification and Authentication Failures

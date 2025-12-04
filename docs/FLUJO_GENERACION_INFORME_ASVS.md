# Flujo de Generación del Informe ASVS 4.0.3

Este documento explica el flujo completo de cómo se obtienen los datos y se genera el informe ASVS automáticamente.

## 📊 Diagrama del Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO: make pdf_report                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: generate_asvs_report.py                               │
│  ────────────────────────────────────────────────────────────  │
│  🔗 INTEGRADO CON DEFECTDOJO                                    │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.1. CONEXIÓN CON DEFECTDOJO                              │  │
│  │     - Inicializa Django para acceso a DefectDojo          │  │
│  │     - Obtiene producto "Medical Register App"             │  │
│  │     - Obtiene Benchmark_Product_Summary (puntajes ASVS) │  │
│  │     - Obtiene findings activos del producto               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.2. MAPEO DE FINDINGS A ASVS                            │  │
│  │     - Mapea CWE → Categorías ASVS:                       │  │
│  │       • CWE-20, CWE-1287, CWE-843 → V5 (Validación)     │  │
│  │       • CWE-703 → V7 (Error Handling)                    │  │
│  │       • CWE-1021 → V8 (Data Protection)                  │  │
│  │       • CWE-942 → V9 (Communications)                    │  │
│  │     - Agrupa findings por categoría ASVS                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.3. INICIALIZACIÓN                                      │  │
│  │     - Crea ASVSAnalyzer con estructura ASVS 4.0.3        │  │
│  │     - Define 14 categorías (V1-V14)                      │  │
│  │     - Define requisitos Nivel 2 por categoría            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.4. ANÁLISIS DE CÓDIGO FUENTE (COMPLEMENTARIO)          │  │
│  │     ┌──────────────────────────────────────────────────┐  │  │
│  │     │ Archivos Python analizados:                      │  │  │
│  │     │ - app/routes.py                                  │  │  │
│  │     │ - app/helpers.py                                 │  │  │
│  │     │ - app/storage.py                                 │  │  │
│  │     │ - app/config.py                                  │  │  │
│  │     └──────────────────────────────────────────────────┘  │  │
│  │     ┌──────────────────────────────────────────────────┐  │  │
│  │     │ Archivos JavaScript analizados:                  │  │  │
│  │     │ - app/static/js/main.js                          │  │  │
│  │     │ - app/static/js/storage.js                        │  │  │
│  │     │ - app/static/js/validation.js                     │  │  │
│  │     └──────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Patrones detectados:                                     │  │
│  │  ✓ Validaciones (validate, sanitize)                    │  │
│  │  ✓ Manejo de errores (try/except)                        │  │
│  │  ✓ Headers de seguridad (X-Frame-Options, CSP, CORS)     │  │
│  │  ✓ Configuración centralizada (config.py)                │  │
│  │  ✓ API REST (@api.route, Blueprint)                      │  │
│  │  ✓ Sanitización frontend (trim, replace)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.3. VERIFICACIÓN ASVS 4.0.3 Nivel 2                     │  │
│  │                                                           │  │
│  │  Para cada categoría V1-V14:                             │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ V1: Architecture, Design and Threat Modeling       │  │  │
│  │  │   - V1.1: ¿Existe README.md?                       │  │  │
│  │  │   - V1.2: ¿Existe carpeta docs/?                   │  │  │
│  │  │   - V1.3: ¿Hay validaciones/error handling?        │  │  │
│  │  │   - V1.4: ¿Hay API REST?                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ V5: Validation, Sanitization and Encoding          │  │  │
│  │  │   - V5.1: ¿Validación frontend Y backend?          │  │  │
│  │  │   - V5.2: ¿Validación de tipos?                    │  │  │
│  │  │   - V5.3: ¿Sanitización implementada?              │  │  │
│  │  │   - V5.4: ¿Validación NaN/Infinity? (parcial)      │  │  │
│  │  │   - V5.5: ¿Validación de límites?                  │  │  │
│  │  │   - V5.6: ¿Validación de formato?                  │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ V2, V3, V4, V6: No aplicable (monousuario)         │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ... (resto de categorías)                                │  │
│  │                                                           │  │
│  │  Resultado: findings = {                                 │  │
│  │    'compliant': ['V1', 'V10', 'V11', 'V13', 'V14'],     │  │
│  │    'partial': ['V5', 'V7', 'V8', 'V9'],                 │  │
│  │    'non_applicable': ['V2', 'V3', 'V4', 'V6'],          │  │
│  │    'missing': []                                         │  │
│  │  }                                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1.4. GENERACIÓN DEL INFORME MARKDOWN                     │  │
│  │                                                           │  │
│  │  ASVSReportGenerator genera:                             │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │ • Encabezado (con ASVS 4.0.3 explícito)          │  │  │
│  │  │ • Sección 1: Descripción de la aplicación         │  │  │
│  │  │ • Sección 2: Análisis de seguridad                │  │  │
│  │  │ • Sección 3: Debilidades identificadas            │  │  │
│  │  │ • Sección 4: Nivel ASVS y requisitos               │  │  │
│  │  │   - Para cada V1-V14:                              │  │  │
│  │  │     * Estado: ✅ CUMPLE / ⚠️ PARCIAL / ❌ PENDIENTE│  │  │
│  │  │     * Requisitos cumplidos                         │  │  │
│  │  │     * Justificaciones                             │  │  │
│  │  │ • Sección 5: Recomendaciones                       │  │  │
│  │  │ • Referencias (enlaces a GitHub ASVS 4.0.3)        │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Guarda en: docs/INFORME_SEGURIDAD.md                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2: generate_pdf_report.py                                 │
│  ────────────────────────────────────────────────────────────  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2.1. LECTURA DEL MARKDOWN                                 │  │
│  │     - Lee: docs/INFORME_SEGURIDAD.md                     │  │
│  │     - Verifica que existe                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2.2. CONVERSIÓN A PDF                                     │  │
│  │     Intenta métodos en orden:                            │  │
│  │     1. markdown2pdf (si disponible)                      │  │
│  │     2. markdown + weasyprint (si disponible)             │  │
│  │     3. markdown + reportlab (si disponible)               │  │
│  │     4. pandoc (si está instalado)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│                             ▼                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 2.3. GUARDADO DEL PDF                                     │  │
│  │     - Guarda en: docs/informes/                          │  │
│  │     - Nombre: INFORME_SEGURIDAD_YYYYMMDD.pdf             │  │
│  │     - Ejemplo: INFORME_SEGURIDAD_20251203.pdf            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ✅ PDF GENERADO
```

## 🔍 Detalle del Proceso

### Fase 1: Análisis de Código (`analyze_code()`)

El script analiza los archivos fuente buscando patrones específicos:

#### Archivos Python analizados:
- **`app/routes.py`**: Busca endpoints API, validaciones, manejo de errores
- **`app/helpers.py`**: Busca funciones de validación y sanitización
- **`app/storage.py`**: Busca manejo de datos
- **`app/config.py`**: Detecta configuración centralizada

#### Archivos JavaScript analizados:
- **`app/static/js/main.js`**: Busca validaciones frontend
- **`app/static/js/storage.js`**: Busca manejo de datos en cliente
- **`app/static/js/validation.js`**: Busca funciones de validación

#### Patrones detectados:

```python
# Ejemplo de detección en Python
if 'validate' in content.lower() or 'sanitize' in content.lower():
    code_analysis['validation'].append(filename)

if 'try:' in content and 'except' in content:
    code_analysis['error_handling'].append(filename)

if 'X-Frame-Options' in content or 'CSP' in content:
    code_analysis['security_headers'].append(filename)

if '@api.route' in content:
    code_analysis['api_rest'] = True
```

```javascript
// Ejemplo de detección en JavaScript
if ('validate' in content || 'parseFloat' in content):
    code_analysis['frontend_validation'].append(filename)

if ('sanitize' in content || 'trim' in content):
    code_analysis['frontend_sanitization'].append(filename)
```

### Fase 2: Verificación ASVS 4.0.3 (`check_asvs_requirements()`)

Para cada categoría V1-V14, el script verifica el cumplimiento:

#### Ejemplo: V5 (Validation, Sanitization and Encoding)

```python
def _check_v5(self):
    compliant = []
    partial = []
    
    # V5.1: Validación en todas las fuentes
    if 'validation' in code_analysis and 'frontend_validation' in code_analysis:
        compliant.append('V5.1')  # ✅ CUMPLE
    elif 'validation' in code_analysis:
        partial.append('V5.1')    # ⚠️ PARCIAL
    
    # V5.2: Validación de tipos
    if 'validation' in code_analysis:
        compliant.append('V5.2')  # ✅ CUMPLE
    
    # V5.3: Sanitización
    if 'frontend_sanitization' in code_analysis:
        compliant.append('V5.3')  # ✅ CUMPLE
    else:
        partial.append('V5.3')    # ⚠️ PARCIAL
    
    # V5.4: Validación NaN/Infinity (siempre parcial por defecto)
    partial.append('V5.4')        # ⚠️ PARCIAL
    
    # Resultado final
    if len(partial) > 0:
        findings['partial'].append({'category': 'V5', ...})
    else:
        findings['compliant'].append('V5')
```

#### Categorías No Aplicables:

```python
# V2, V3, V4, V6: No aplicable para aplicación monousuario
findings['non_applicable'].append({
    'category': 'V2',
    'reason': 'Aplicación monousuario sin autenticación compleja'
})
```

### Fase 3: Generación del Informe (`generate_report()`)

El generador crea el Markdown estructurado:

#### Estructura del Informe:

1. **Encabezado**: Fecha, versión ASVS 4.0.3, enlaces a GitHub
2. **Sección 1**: Descripción de la aplicación (texto fijo)
3. **Sección 2**: Metodología de análisis (texto fijo)
4. **Sección 3**: Debilidades identificadas (texto fijo)
5. **Sección 4**: Nivel ASVS y requisitos (generado dinámicamente)
   - Para cada V1-V14:
     - Estado basado en `findings`
     - Requisitos cumplidos/parciales
     - Justificaciones
6. **Sección 5**: Recomendaciones (texto fijo)
7. **Referencias**: Enlaces a ASVS 4.0.3 en GitHub

#### Ejemplo de generación dinámica:

```python
def _generate_section4(self):
    for code, name in ASVS_403_CATEGORIES.items():
        if code in findings['compliant']:
            # Genera: ✅ CUMPLE
        elif code in [f['category'] for f in findings['partial']]:
            # Genera: ⚠️ PARCIAL
        elif code in [f['category'] for f in findings['non_applicable']]:
            # Genera: ⚠️ No aplicable
```

### Fase 4: Conversión a PDF (`generate_pdf_report()`)

El script de conversión:

1. **Lee el Markdown** generado
2. **Intenta convertir** usando múltiples métodos:
   - `markdown2pdf` (preferido)
   - `weasyprint` (alternativa)
   - `reportlab` (alternativa)
   - `pandoc` (último recurso)
3. **Guarda el PDF** con fecha en el nombre

## 📋 Datos Utilizados

### Fuentes de Datos:

1. **Estructura ASVS 4.0.3** (hardcoded en el script):
   ```python
   ASVS_403_CATEGORIES = {
       'V1': 'Architecture, Design and Threat Modeling',
       'V2': 'Authentication',
       # ... 14 categorías
   }
   ```

2. **Código fuente de la aplicación**:
   - Archivos Python en `app/`
   - Archivos JavaScript en `app/static/js/`
   - Archivos de configuración

3. **Análisis de patrones**:
   - Búsqueda de palabras clave
   - Detección de estructuras de código
   - Verificación de existencia de archivos

### Limitaciones del Análisis Automático:

- **Análisis estático básico**: No ejecuta el código, solo lo lee
- **Patrones simples**: Busca palabras clave y estructuras básicas
- **No verifica lógica compleja**: No analiza la implementación detallada
- **Requiere validación manual**: El informe generado debe revisarse

## 🔄 Flujo Completo Resumido

```
Usuario ejecuta: make pdf_report
         │
         ├─► Paso 1: generate_asvs_report.py
         │   │
         │   ├─► Analiza código fuente (Python + JavaScript)
         │   │   └─► Detecta: validaciones, headers, API, etc.
         │   │
         │   ├─► Verifica requisitos ASVS 4.0.3 Nivel 2
         │   │   └─► Compara código con 14 categorías (V1-V14)
         │   │
         │   └─► Genera Markdown
         │       └─► Guarda: docs/INFORME_SEGURIDAD.md
         │
         └─► Paso 2: generate_pdf_report.py
             │
             ├─► Lee Markdown generado
             │
             ├─► Convierte a PDF (múltiples métodos)
             │
             └─► Guarda PDF
                 └─► docs/informes/INFORME_SEGURIDAD_YYYYMMDD.pdf
```

## 🎯 Puntos Clave

1. **ASVS 4.0.3 está hardcoded** en el script (estructura de categorías)
2. **No descarga datos de GitHub** - usa estructura local
3. **Análisis estático** - lee código, no lo ejecuta
4. **Generación automática** - crea el informe completo desde cero
5. **Dos scripts separados**:
   - `generate_asvs_report.py`: Genera el contenido (Markdown)
   - `generate_pdf_report.py`: Convierte a PDF

## 🔗 Relación entre ASVS y DefectDojo

### Estado Actual

**IMPORTANTE**: En el proyecto actual, **ASVS y DefectDojo NO están integrados directamente**.

- **El informe ASVS** se genera analizando el código fuente directamente
- **DefectDojo** se usa para gestionar findings/vulnerabilidades (CWE-699, etc.)
- **No hay conexión** entre el informe ASVS y los benchmarks de DefectDojo

### Funcionalidad de DefectDojo con ASVS

DefectDojo **SÍ tiene funcionalidad de benchmarks ASVS**, pero **NO se está usando** en este proyecto:

- DefectDojo permite configurar **benchmarks ASVS** para productos
- Los benchmarks permiten evaluar el cumplimiento de ASVS basándose en findings
- Se puede ver el puntaje ASVS en la vista del producto
- DefectDojo soporta ASVS v3.1 (no v4.0.3 directamente)

### Diferencia con el Enfoque Actual

**Enfoque actual (implementado)**:
```
Código fuente → Análisis estático → Informe ASVS
```

**Enfoque con DefectDojo (no implementado)**:
```
Findings en DefectDojo → Benchmarks ASVS → Puntaje ASVS
```

### Posible Integración Futura

Se podría mejorar el informe ASVS integrando con DefectDojo:

1. **Obtener findings de DefectDojo** relacionados con ASVS
2. **Usar benchmarks ASVS de DefectDojo** para evaluar cumplimiento
3. **Combinar análisis de código + findings de DefectDojo** para un informe más completo
4. **Sincronizar** el informe ASVS con el estado real de findings en DefectDojo

## 💡 Mejoras Futuras Posibles

1. **Descargar ASVS 4.0.3 desde GitHub** automáticamente
2. **Análisis más profundo** del código (AST parsing)
3. **Integración con DefectDojo** para obtener findings reales y usar benchmarks ASVS
4. **Análisis dinámico** ejecutando tests de seguridad
5. **Generación de evidencias** con ejemplos de código
6. **Sincronización con benchmarks ASVS de DefectDojo** para evaluación más precisa


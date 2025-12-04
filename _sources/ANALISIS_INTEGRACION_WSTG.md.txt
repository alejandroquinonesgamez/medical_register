# Análisis de Integración: OWASP WSTG Tracker con DefectDojo

## Resumen Ejecutivo

Este documento analiza la integración del [OWASP WSTG Tracker](https://adanalvarez.github.io/owasp-wstg-tracker/) con DefectDojo para mejorar las capacidades de pruebas de seguridad basadas en el OWASP Web Security Testing Guide.

---

## 1. Análisis del OWASP WSTG Tracker

### 1.1 Funcionamiento del Tracker

El **OWASP WSTG Tracker** es una herramienta web que permite gestionar el progreso de pruebas de seguridad basadas en el OWASP Web Security Testing Guide.

**Características principales:**

1. **Checklist Interactivo**: Permite marcar items del WSTG con diferentes estados:
   - `Not Started` - No iniciado
   - `In Progress` - En progreso
   - `Blocked` - Bloqueado
   - `Done` - Completado
   - `Not Applicable` - No aplicable

2. **Persistencia Local**: Autoguardado en `localStorage` del navegador

3. **Importación/Exportación**: Formato JSON para compartir o respaldar progreso

4. **Búsqueda**: Filtrado de items del checklist

5. **Categorización**: Organización por categorías del WSTG

6. **Interfaz Web**: Aplicación frontend (probablemente React/Vue)

### 1.2 Estructura de Datos (Inferida)

El JSON exportado probablemente contiene:
- Lista de items del WSTG con sus IDs únicos
- Estado de cada item (Not Started, In Progress, etc.)
- Notas/comentarios por item
- Timestamps de cambios
- Metadatos (versión WSTG, fecha de exportación)

---

## 2. Integración con DefectDojo

### 2.1 Opciones de Integración

#### Opción 1: Importación de Resultados WSTG como Findings ⭐ **RECOMENDADA**

**Ventajas:**
- Automatiza la creación de findings desde el tracker
- Mantiene el historial y estado de las pruebas
- Permite mapear items WSTG a CWE/OWASP Top 10

**Implementación sugerida:**

1. **Script de Importación** (`scripts/import_wstg_results.py`):
   - Lee el JSON exportado del tracker
   - Mapea items WSTG a findings en DefectDojo
   - Crea/actualiza findings según el estado:
     - `Done` → Finding resuelto/verificado
     - `In Progress` → Finding activo
     - `Blocked` → Finding con nota de bloqueo
     - `Not Applicable` → Se omite o se marca como N/A

2. **Estructura de datos:**
   ```python
   # Mapeo WSTG → DefectDojo
   WSTG_ITEM → Finding:
     - Título: "WSTG-INFO-01: Conduct OSINT reconnaissance"
     - Descripción: Descripción del test del WSTG
     - Severidad: Basada en categoría WSTG
     - Test Type: "WSTG Security Testing"
     - Tags: ["WSTG", "INFO-01", "Reconnaissance"]
   ```

#### Opción 2: Integración Bidireccional

**Ventajas:**
- Sincronización entre tracker y DefectDojo
- Actualización automática del tracker cuando se resuelven findings
- Visibilidad unificada

**Implementación sugerida:**

1. API/endpoint en la app Flask para recibir actualizaciones del tracker
2. Script que sincroniza estados entre ambos sistemas
3. Webhook o polling para mantener consistencia

#### Opción 3: Parser Personalizado para DefectDojo

**Ventajas:**
- Integración nativa con el sistema de importación de DefectDojo
- Compatible con el flujo estándar de DefectDojo
- Permite importar múltiples formatos

**Implementación sugerida:**

1. Crear un parser personalizado siguiendo la estructura de DefectDojo
2. Convertir el JSON del tracker al formato esperado por DefectDojo
3. Usar la API de importación de DefectDojo

---

## 3. Arquitectura Propuesta

```
┌─────────────────────┐
│  WSTG Tracker       │
│  (Frontend Web)     │
│  - Checklist UI      │
│  - localStorage     │
└──────────┬──────────┘
           │ Export JSON
           ▼
┌─────────────────────┐
│  Script Importador  │
│  import_wstg.py     │
│  - Parse JSON        │
│  - Mapeo WSTG→CWE   │
│  - Crear Findings   │
└──────────┬──────────┘
           │ API DefectDojo
           ▼
┌─────────────────────┐
│  DefectDojo          │
│  - Findings          │
│  - Test Types        │
│  - Engagements       │
└─────────────────────┘
```

---

## 4. Consideraciones Técnicas

### 4.1 Mapeo WSTG → CWE/OWASP

- Muchos items WSTG tienen CWE asociados
- Crear un diccionario de mapeo WSTG → CWE
- Usar tags para identificar origen WSTG

### 4.2 Test Types en DefectDojo

- Crear un Test Type específico: **"WSTG Security Testing"**
- Organizar por categorías WSTG (INFO, CONFIG, AUTHN, etc.)

### 4.3 Gestión de Estados

- `Done` → Finding `verified=True`, `active=False`
- `In Progress` → Finding `active=True`, `verified=False`
- `Blocked` → Finding con nota especial
- `Not Applicable` → No crear finding o marcarlo como N/A

### 4.4 Integración con Scripts Existentes

- Reutilizar `manage_findings.py` como base
- Seguir el patrón de `init_defectdojo_internal.py`
- Mantener consistencia con el flujo actual de CWE-699

---

## 5. Archivos a Crear/Modificar

### 5.1 Archivos Nuevos

1. **`scripts/import_wstg_results.py`**
   - Script principal de importación
   - Lee JSON del tracker
   - Crea/actualiza findings en DefectDojo

2. **`scripts/wstg_mapping.py`**
   - Mapeo WSTG → CWE/OWASP
   - Diccionario de correspondencias
   - Funciones de conversión

3. **`data/wstg_checklist.json`** (opcional)
   - Estructura base del checklist WSTG
   - Referencia para validación

### 5.2 Archivos a Modificar

1. **`scripts/manage_findings.py`**
   - Extender para soportar WSTG
   - Añadir funciones de importación WSTG

2. **`docker-compose.yml`**
   - Añadir volumen para datos WSTG (si necesario)

3. **`Makefile`**
   - Añadir target `make import-wstg`
   - Comando para ejecutar importación

---

## 6. Beneficios de la Integración

1. **Trazabilidad**: Seguimiento completo de pruebas WSTG en DefectDojo
2. **Automatización**: Reduce entrada manual de findings
3. **Estandarización**: Alineación con estándares OWASP WSTG
4. **Reporting**: Informes consolidados en DefectDojo
5. **Workflow**: Integración con el flujo de gestión de vulnerabilidades existente

---

## 7. Desafíos Potenciales

1. **Estructura del JSON**: Necesario verificar el formato exacto del export
2. **Mapeo WSTG→CWE**: Algunos items pueden no tener CWE directo
3. **Duplicados**: Evitar findings duplicados si se importa múltiples veces
4. **Sincronización**: Mantener consistencia entre sistemas

---

## 8. Recomendación

### Enfoque Recomendado: Opción 1 (Importación Unidireccional)

**Razones:**
- ✅ Menor complejidad de implementación
- ✅ Reutiliza scripts existentes
- ✅ Permite validar el concepto antes de avanzar
- ✅ Flexibilidad para exportar desde el tracker cuando sea necesario

**Plan de Implementación:**

1. **Fase 1: Análisis del JSON**
   - Obtener ejemplo de JSON exportado del tracker
   - Analizar estructura y campos
   - Documentar formato

2. **Fase 2: Mapeo WSTG → CWE**
   - Crear diccionario de mapeo
   - Identificar items sin CWE directo
   - Definir estrategia para items sin mapeo

3. **Fase 3: Script de Importación**
   - Desarrollar `import_wstg_results.py`
   - Implementar lógica de creación/actualización de findings
   - Manejo de estados y duplicados

4. **Fase 4: Integración con Makefile**
   - Añadir comando `make import-wstg`
   - Documentación de uso

5. **Fase 5: Pruebas y Validación**
   - Probar con JSON de ejemplo
   - Verificar findings creados en DefectDojo
   - Validar mapeos y estados

---

## 9. Ejemplo de Uso (Propuesto)

```bash
# Exportar progreso desde WSTG Tracker (manual)
# Guardar como wstg_export.json

# Importar a DefectDojo
make import-wstg FILE=wstg_export.json

# O usando docker-compose directamente
docker-compose exec defectdojo python /app/manage_findings.py --import-wstg /app/data/wstg_export.json
```

---

## 10. Referencias

- [OWASP WSTG Tracker](https://adanalvarez.github.io/owasp-wstg-tracker/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [DefectDojo Documentation](https://docs.defectdojo.com/)
- [DefectDojo API Documentation](https://defectdojo.github.io/django-DefectDojo/integrations/api-v2-docs/)

---

## 11. Próximos Pasos

1. ✅ Análisis completado
2. ⏳ Obtener ejemplo de JSON exportado del tracker
3. ⏳ Diseñar estructura de mapeo WSTG → CWE
4. ⏳ Implementar script de importación
5. ⏳ Integrar con Makefile
6. ⏳ Probar y validar

---

**Fecha de Análisis**: 2025-12-03  
**Autor**: Análisis técnico para integración WSTG-DefectDojo




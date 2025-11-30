# Flujo de Creación y Resolución de Findings en DefectDojo

## Propósito

Este documento explica cómo modificar los scripts para que DefectDojo refleje el flujo completo de:
1. **Creación del ticket** (estado inicial: activo/pendiente)
2. **Resolución del ticket** (cambio de estado a resuelto)

## Problema Actual

Los scripts actuales crean algunos findings directamente como resueltos, lo que oculta el historial de cuándo fueron creados originalmente y cuándo se resolvieron.

### Estado Actual en el Código

- **CWE-20**: Se crea directamente como resuelto (`active: False, verified: True`)
- **CWE-1021**: Se crea directamente como resuelto (`active: False, verified: True`)
- **Otros CWE**: Se crean como activos (`active: True, verified: False`)

## Solución: Flujo en Dos Pasos

### Paso 1: Crear Todos los Findings como Activos

Modificar `init_defectdojo_internal.py` para crear TODOS los findings inicialmente como activos:

```python
findings_data = {
    'CWE-20': {
        # ... datos del finding ...
        'active': True,      # ⬅️ CAMBIAR A True
        'verified': False,   # ⬅️ CAMBIAR A False
        # ...
    },
    'CWE-1021': {
        # ... datos del finding ...
        'active': True,      # ⬅️ CAMBIAR A True
        'verified': False,   # ⬅️ CAMBIAR A False
        # ...
    },
    # ... resto de findings ya están como activos ...
}
```

### Paso 2: Marcar Como Resueltos Posteriormente

Usar `mark_findings_resolved.sh` o crear un script que marque como resueltos los findings que ya están resueltos en el código:

```bash
# Ejecutar después de crear los findings
./scripts/mark_findings_resolved.sh
```

## Ventajas del Flujo en Dos Pasos

1. **Historial Completo**: DefectDojo rastrea:
   - Fecha de creación original
   - Fecha de resolución
   - Cambios de estado en el historial

2. **Mejor Trazabilidad**: Se puede ver:
   - Cuánto tiempo estuvo activo el finding
   - Cuándo se implementó la solución
   - Quién lo resolvió

3. **Flujo Realista**: Refleja el ciclo de vida real de un bug/vulnerabilidad:
   - Se detecta → Se crea el ticket (activo)
   - Se corrige → Se marca como resuelto

## Implementación Recomendada

### Opción A: Script Único con Dos Fases

Crear un script que:
1. Primero crea todos los findings como activos
2. Luego marca como resueltos los que ya están resueltos

### Opción B: Dos Scripts Separados (Recomendado)

1. **`create_findings_initial.sh`**: Crea todos los findings como activos
2. **`mark_findings_resolved.sh`**: Marca como resueltos los que ya lo están

### Opción C: Flag en el Script de Inicialización

Agregar un flag al script de inicialización:
- `--create-as-active`: Crea todos como activos
- `--create-as-resolved`: Crea algunos como resueltos (comportamiento actual)

## Ejemplo de Flujo

El flujo se ejecuta automáticamente usando el comando:

```bash
# Flujo completo automatizado
make update
```

O en PowerShell:

```powershell
.\make.ps1 update
```

Este comando:
1. Inicializa DefectDojo (crea todos los findings como activos)
2. Ejecuta el script consolidado `manage_findings.py` que marca como resueltos los que ya están resueltos en el código

## Notas Importantes

- DefectDojo mantiene automáticamente el historial de cambios cuando se actualiza el estado de un finding
- Los cambios de estado se registran con timestamp
- Se puede ver el historial completo en la interfaz de DefectDojo

## Conclusión

Para reflejar correctamente el flujo de creación → resolución, es necesario:
1. Crear todos los findings inicialmente como activos
2. Marcar como resueltos en un paso separado

Esto proporciona mejor trazabilidad y un historial más completo en DefectDojo.




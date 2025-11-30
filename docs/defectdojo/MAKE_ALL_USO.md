# Uso de `make update` - Flujo Completo de DefectDojo

## 📋 Descripción

El comando `make update` (o `.\make.ps1 update` en PowerShell) ejecuta el flujo completo para configurar DefectDojo con el historial de creación → resolución de findings.

## 🎯 ¿Qué hace `make update`?

El comando ejecuta automáticamente:

1. **Paso 1**: Verifica y arranca la aplicación principal si es necesario
2. **Paso 2**: Verifica y arranca DefectDojo si es necesario (esto crea todos los findings como **activos/pendientes**)
3. **Paso 3**: Ejecuta el script consolidado `manage_findings.py` que:
   - Crea/actualiza todos los findings
   - Marca los findings resueltos (CWE-20, CWE-1021) como **resueltos** con sus fechas históricas

## 🚀 Uso

### En Linux/Mac o Git Bash (Windows)

```bash
make update
```

### En PowerShell (Windows)

Si `make` no está disponible, puedes usar el script PowerShell equivalente:

```powershell
.\make.ps1 update
```

Este comando hace exactamente lo mismo que `make update`:
1. Verifica y arranca la aplicación principal si es necesario
2. Verifica y arranca DefectDojo si es necesario
3. Ejecuta el script consolidado `manage_findings.py` para gestionar todos los findings

## 📅 Fechas que se Establecen

Después de ejecutar `make update`, los findings tendrán:

### CWE-20 (Validación de entrada)
- **Fecha de creación**: 2025-11-10
- **Fecha de resolución**: 2025-11-24 ✅

### CWE-1021 (Clickjacking)
- **Fecha de creación**: 2025-11-10
- **Fecha de resolución**: 2025-11-24 ✅

### Otros Findings
- **CWE-1287, CWE-843, CWE-703**: Permanecen como activos (pendientes)
- **CWE-942**: Permanece como activo (aceptado temporalmente)

## ✅ Resultado

Después de ejecutar `make update`:

1. **Todos los findings están creados** como activos inicialmente
2. **CWE-20 y CWE-1021 están marcados como resueltos** con:
   - Estado: `active: False, verified: True`
   - Fecha de resolución: 2025-11-24
   - Mitigación completa documentada

3. **Historial completo visible** en DefectDojo:
   - Fecha de creación original
   - Fecha de resolución
   - Cambios de estado registrados

## 🔍 Verificar Resultado

Accede a DefectDojo:
- **URL**: http://localhost:8080
- **Usuario**: admin
- **Contraseña**: admin

Ver los findings:
- **Engagement**: http://localhost:8080/engagement/1/
- **Findings**: http://localhost:8080/test/1/findings

En cada finding podrás ver:
- ✅ Fecha de creación
- ✅ Fecha de resolución (si está resuelto)
- ✅ Historial completo de cambios de estado

## 🔧 Solución de Problemas

### Si el script falla al marcar como resueltos

Si después de ejecutar `make update` los findings no están marcados como resueltos:

```bash
# Esperar un poco más y volver a ejecutar
make update
```

O ejecutar el script consolidado manualmente:

```bash
docker cp scripts/manage_findings.py defectdojo:/tmp/manage_findings.py
docker-compose --profile defectdojo exec -T defectdojo python3 /tmp/manage_findings.py
```

### Si DefectDojo tarda mucho en iniciar

El script espera 60 segundos. Si DefectDojo tarda más:

1. Verifica los logs: `make logs-defectdojo`
2. Espera hasta que esté listo
3. Vuelve a ejecutar: `make update`

### Verificar estado de los contenedores

```bash
make ps
```

O:

```bash
docker-compose --profile defectdojo ps
```

## 📝 Notas

- **Primera ejecución**: DefectDojo puede tardar varios minutos en inicializarse completamente
- **Subsiguientes ejecuciones**: Son más rápidas ya que los contenedores están construidos
- **Base de datos**: Los datos persisten en `./data/postgres/` entre reinicios

## 🎉 Comando Completo

```bash
make update
```

O en PowerShell:

```powershell
.\make.ps1 update
```

¡Y listo! El flujo completo se ejecutará automáticamente.


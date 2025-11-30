# Uso de `make all` - Flujo Completo de DefectDojo

## 📋 Descripción

El comando `make all` ejecuta el flujo completo para configurar DefectDojo con el historial de creación → resolución de findings.

## 🎯 ¿Qué hace `make all`?

El comando ejecuta automáticamente:

1. **Paso 1**: Arranca DefectDojo (esto crea todos los findings como **activos/pendientes**)
2. **Paso 2**: Espera 60 segundos para que DefectDojo esté completamente inicializado
3. **Paso 3**: Marca los findings resueltos como **resueltos** con sus fechas históricas

## 🚀 Uso

### En Linux/Mac o Git Bash (Windows)

```bash
make all
```

### En PowerShell (Windows) - Alternativa

Si `make` no está disponible, puedes usar el script PowerShell equivalente:

```powershell
.\scripts\resolve_findings_all.ps1
```

O ejecutar los pasos manualmente:

```powershell
# Paso 1: Arrancar DefectDojo
$env:COMPOSE_DOCKER_CLI_BUILD="0"
$env:DOCKER_BUILDKIT="0"
docker-compose --profile defectdojo up -d

# Paso 2: Esperar (60 segundos)
Start-Sleep -Seconds 60

# Paso 3: Marcar findings como resueltos
.\scripts\mark_findings_resolved_with_dates.sh
```

## 📅 Fechas que se Establecen

Después de ejecutar `make all`, los findings tendrán:

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

Después de ejecutar `make all`:

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

Si después de ejecutar `make all` los findings no están marcados como resueltos:

```bash
# Esperar un poco más y ejecutar solo el paso de resolución
make resolve-findings
```

O manualmente:

```bash
bash scripts/mark_findings_resolved_with_dates.sh
```

### Si DefectDojo tarda mucho en iniciar

El script espera 60 segundos. Si DefectDojo tarda más:

1. Verifica los logs: `make logs-defectdojo`
2. Espera hasta que esté listo
3. Ejecuta solo: `make resolve-findings`

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
make all
```

¡Y listo! El flujo completo se ejecutará automáticamente.


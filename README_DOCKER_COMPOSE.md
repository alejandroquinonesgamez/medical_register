# Solución para Problemas de Docker Compose con Caracteres Especiales

## Problema

Cuando el proyecto está en una ruta con caracteres especiales o espacios (como `Mi unidad (alejandroquinonesgamez@gmail.com)`), Docker Compose puede fallar con errores relacionados con caracteres no imprimibles.

## Solución Automática

El proyecto incluye una solución automática que se configura al descargar el repositorio. No se requieren pasos manuales.

### Configuración Automática

El archivo `.env` se crea automáticamente en las siguientes situaciones:

1. **Al ejecutar el script de setup** (`./scripts/setup.sh` o `.\scripts\setup.ps1`)
   - El script crea automáticamente el archivo `.env` desde `docker-compose.env.example`

2. **Al usar `make` o `make.ps1` por primera vez**
   - Los scripts detectan si no existe `.env` y lo crean automáticamente

3. **Si el archivo no existe**, se crea automáticamente con:
```env
COMPOSE_PROJECT_NAME=medical_register
COMPOSE_DOCKER_CLI_BUILD=0
DOCKER_BUILDKIT=0
```

## Funcionamiento

El archivo `.env` se lee automáticamente por Docker Compose y establece:
- `COMPOSE_PROJECT_NAME`: Nombre fijo del proyecto para evitar conflictos
- Variables de entorno para desactivar BuildKit si es necesario

**Importante**:
- El archivo `.env` está en `.gitignore` (no se sube al repositorio)
- El archivo `docker-compose.env.example` está en el repositorio como plantilla
- Cada usuario tiene su propio `.env` generado automáticamente

## Verificación

Para verificar que todo funciona correctamente:

```powershell
# Verificar que el archivo .env existe
Test-Path .env

# Verificar que Docker Compose funciona sin errores
docker-compose --profile defectdojo ps
```

Si ves los contenedores listados correctamente, la configuración está funcionando.

## Ventajas de la Solución

- ✅ **Automática**: No requiere configuración manual
- ✅ **Persistente**: Se mantiene al descargar el repositorio
- ✅ **Estándar**: Usa el mecanismo estándar de Docker Compose
- ✅ **Funciona en todos los sistemas**: Windows, Linux, Mac
- ✅ **Sin archivos temporales**: Todo queda configurado permanentemente


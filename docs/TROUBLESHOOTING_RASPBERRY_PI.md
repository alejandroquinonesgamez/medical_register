# Solución de Problemas - Despliegue en Raspberry Pi

## Error: KeyError: 'ContainerConfig'

### Síntoma

Al intentar desplegar en Raspberry Pi, aparece el error:

```
KeyError: 'ContainerConfig'
ERROR: for flask_medical_register  'ContainerConfig'
ERROR: for web  'ContainerConfig'
```

### Causa

Este error ocurre cuando:
1. Hay contenedores existentes con configuración incompatible
2. La imagen del contenedor tiene una configuración antigua
3. Hay un problema con los volúmenes montados

### Solución

#### Paso 1: Eliminar contenedores y volúmenes existentes

```bash
# Detener y eliminar todos los contenedores
docker-compose --profile defectdojo down -v

# Eliminar contenedores huérfanos
docker container prune -f

# Eliminar imágenes antiguas si es necesario
docker image prune -f
```

#### Paso 2: Reconstruir las imágenes

```bash
# Reconstruir sin usar caché
docker-compose --profile defectdojo build --no-cache web

# O reconstruir todo
docker-compose --profile defectdojo build --no-cache
```

#### Paso 3: Crear los contenedores de nuevo

```bash
# Crear y arrancar los servicios
docker-compose --profile defectdojo up -d
```

### Solución Alternativa: Usar Docker Compose V2

Si el problema persiste, intenta usar `docker compose` (v2) en lugar de `docker-compose`:

```bash
# Verificar versión
docker compose version

# Usar docker compose v2
docker compose --profile defectdojo down -v
docker compose --profile defectdojo build --no-cache
docker compose --profile defectdojo up -d
```

### Verificación

Después de aplicar la solución, verifica que los contenedores estén corriendo:

```bash
docker-compose --profile defectdojo ps
```

Todos los contenedores deberían mostrar estado "Up" o "Up (healthy)".

### Notas Adicionales

- En Raspberry Pi, asegúrate de tener suficiente espacio en disco
- Verifica que Docker tenga permisos suficientes
- Si el problema persiste, considera actualizar Docker y docker-compose



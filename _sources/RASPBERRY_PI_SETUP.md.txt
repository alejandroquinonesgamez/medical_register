# Configuración para Raspberry Pi

## ⚠️ Limitaciones Importantes

### Arquitectura ARM64 vs x86_64

**DefectDojo no tiene soporte oficial para ARM64 (Raspberry Pi)**. Las imágenes oficiales de DefectDojo están diseñadas para arquitectura x86_64.

### Soluciones

1. **Emulación QEMU**: Si Docker detecta que estás en ARM64, intentará usar emulación x86_64 automáticamente.
   - **Ventaja**: Permite ejecutar DefectDojo en Raspberry Pi
   - **Desventaja**: Es significativamente más lento (puede ser 5-10x más lento)
   - **Requisito**: Docker debe tener soporte para emulación multi-arquitectura

2. **Sin Restricciones de Recursos**: La configuración no tiene límites de memoria o CPU, permitiendo que Docker gestione los recursos automáticamente según la disponibilidad del sistema.

## Requisitos Previos

### 1. Instalar Docker con soporte multi-arquitectura

```bash
# Verificar que Docker soporta emulación
docker run --rm --platform linux/amd64 hello-world

# Si falla, instalar QEMU
sudo apt-get update
sudo apt-get install -y qemu qemu-user-static binfmt-support
```

### 2. Verificar recursos disponibles

```bash
# Verificar RAM disponible
free -h

# Verificar espacio en disco (DefectDojo necesita ~5GB)
df -h
```

## Instalación

### 1. Arrancar solo la aplicación Flask (sin DefectDojo)

Si DefectDojo causa problemas, puedes arrancar solo la aplicación principal:

```bash
docker-compose up -d web
```

### 2. Arrancar todo (incluyendo DefectDojo)

```bash
# Arrancar todos los servicios
docker-compose up -d

# Verificar estado (puede tardar varios minutos en iniciar)
docker-compose ps

# Ver logs de DefectDojo
docker-compose logs -f defectdojo
```

## Problemas Comunes

### 1. El contenedor de DefectDojo no arranca

**Síntomas**: El contenedor se reinicia constantemente o no pasa el healthcheck.

**Soluciones**:
- Verificar que QEMU está instalado: `docker run --rm --platform linux/amd64 hello-world`
- Aumentar el `start_period` del healthcheck (ya configurado a 300s)
- Verificar logs: `docker-compose logs defectdojo`

### 2. La página de login no carga correctamente

**Síntomas**: La página `/login` se muestra pero sin estilos CSS o JavaScript.

**Causas posibles**:
- Los recursos estáticos no se han generado correctamente
- El volumen `defectdojo_static` está vacío
- Nginx no puede acceder a los archivos estáticos

**Soluciones**:
```bash
# Verificar que los estáticos se generaron
docker-compose exec defectdojo ls -la /app/static

# Regenerar estáticos (si es necesario)
docker-compose exec defectdojo python manage.py collectstatic --noinput

# Verificar permisos del volumen
docker-compose exec defectdojo-nginx ls -la /app/static
```

### 3. Rendimiento muy lento

**Causa**: Emulación QEMU es inherentemente lenta en ARM64.

**Soluciones**:
- Considerar usar un servidor x86_64 para DefectDojo
- Usar solo la aplicación Flask si DefectDojo no es crítico
- Reducir aún más los recursos si es necesario

### 4. Memoria insuficiente

**Síntomas**: Contenedores se matan con "OOM Killed".

**Soluciones**:
- Reducir límites de memoria en `docker-compose.yml`
- Aumentar swap en la Raspberry Pi:
  ```bash
  sudo dphys-swapfile swapoff
  sudo nano /etc/dphys-swapfile  # Cambiar CONF_SWAPSIZE=2048
  sudo dphys-swapfile setup
  sudo dphys-swapfile swapon
  ```

## Alternativas Recomendadas

### Opción 1: Servidor Dedicado para DefectDojo

Ejecutar DefectDojo en un servidor x86_64 separado y acceder remotamente:
- Mejor rendimiento
- Sin problemas de compatibilidad
- La aplicación Flask puede seguir en Raspberry Pi

### Opción 2: Solo Aplicación Flask

Si DefectDojo no es esencial para producción:
```bash
# Arrancar solo la aplicación Flask
docker-compose up -d web
```

### Opción 3: Usar DefectDojo como Servicio Externo

Configurar DefectDojo en un servidor cloud (AWS, DigitalOcean, etc.) y usar la API desde la Raspberry Pi.

## Monitoreo

### Ver uso de recursos

```bash
# Ver uso de CPU y memoria
docker stats

# Ver logs en tiempo real
docker-compose logs -f
```

### Verificar salud de servicios

```bash
# Estado de todos los servicios
docker-compose ps

# Healthcheck específico
docker inspect defectdojo | grep -A 10 Health
```

## Notas Finales

- **Raspberry Pi 5 con 8GB** tiene recursos suficientes para ejecutar DefectDojo con emulación, pero será lento
- El tiempo de inicio puede ser de **5-10 minutos** la primera vez
- Las operaciones en DefectDojo pueden ser **5-10x más lentas** que en x86_64 nativo
- Se recomienda usar DefectDojo solo para desarrollo/testing en Raspberry Pi
- Para producción, usar un servidor x86_64 dedicado



# Uso de Docker Compose - Separación de Servicios

## 📋 Descripción

Los servicios están separados usando **perfiles de Docker Compose** para permitir arrancar la aplicación principal y DefectDojo de forma independiente.

## 🚀 Comandos Disponibles

### 1. Arrancar solo la aplicación principal (Flask)

```bash
docker-compose up -d
```

Esto arrancará únicamente:
- `web` - Aplicación Flask en el puerto 5001
- `frontend-tests` - Servicio para ejecutar tests (solo cuando se invoca explícitamente)

**Acceso**: `http://localhost:5001`

### 2. Arrancar solo DefectDojo

```bash
docker-compose --profile defectdojo up -d
```

Esto arrancará todos los servicios de DefectDojo:
- `defectdojo-db` - PostgreSQL (puerto 5432)
- `defectdojo-redis` - Redis (puerto 6379)
- `defectdojo` - Aplicación Django
- `defectdojo-nginx` - Nginx (puerto 8080)
- `defectdojo-celeryworker` - Worker de Celery
- `defectdojo-celerybeat` - Scheduler de Celery

**Acceso**: `http://localhost:8080`

### 3. Arrancar todo (aplicación + DefectDojo)

```bash
docker-compose --profile defectdojo up -d
```

O simplemente:

```bash
docker-compose up -d --profile defectdojo
```

Esto arrancará todos los servicios de ambos perfiles.

## 📊 Verificar Estado

### Ver todos los servicios (incluyendo los del perfil defectdojo)

```bash
docker-compose ps
```

### Ver solo servicios activos

```bash
docker-compose ps --all
```

## 🛑 Detener Servicios

### Detener solo la aplicación principal

```bash
docker-compose down
```

### Detener solo DefectDojo

```bash
docker-compose --profile defectdojo down
```

### Detener todo

```bash
docker-compose --profile defectdojo down
```

## 📝 Logs

### Ver logs de la aplicación principal

```bash
docker-compose logs -f web
```

### Ver logs de DefectDojo

```bash
docker-compose --profile defectdojo logs -f defectdojo
```

### Ver logs de todos los servicios

```bash
docker-compose --profile defectdojo logs -f
```

## 🔧 Casos de Uso

### Desarrollo Local (solo aplicación Flask)

```bash
# Arrancar solo la aplicación
docker-compose up -d

# Ver logs
docker-compose logs -f web

# Detener
docker-compose down
```

### Testing de Seguridad (solo DefectDojo)

```bash
# Arrancar solo DefectDojo
docker-compose --profile defectdojo up -d

# Esperar a que esté listo (puede tardar varios minutos)
docker-compose --profile defectdojo ps

# Acceder a http://localhost:8080

# Detener
docker-compose --profile defectdojo down
```

### Producción Completa (todo)

```bash
# Arrancar todo
docker-compose --profile defectdojo up -d

# Verificar estado
docker-compose --profile defectdojo ps

# Detener todo
docker-compose --profile defectdojo down
```

## ⚠️ Notas Importantes

1. **Puertos**: 
   - Aplicación Flask: `5001`
   - DefectDojo: `8080`
   - PostgreSQL: `5432`
   - Redis: `6379`

2. **Raspberry Pi**: Si estás usando Raspberry Pi, DefectDojo requerirá emulación QEMU y será más lento. Considera arrancar solo la aplicación principal si DefectDojo no es necesario.

3. **Datos Persistentes**: Los datos se almacenan en directorios locales en `./data/`:
   - `data/postgres/` - Base de datos PostgreSQL
   - `data/redis/` - Datos de Redis
   - `data/defectdojo/media/` - Archivos multimedia
   - `data/defectdojo/static/` - Archivos estáticos
   
   Para eliminar todos los datos:

```bash
docker-compose --profile defectdojo down
rm -rf data/postgres/* data/redis/* data/defectdojo/*
```

4. **Recursos**: DefectDojo consume más recursos. En Raspberry Pi, es recomendable arrancarlo solo cuando sea necesario.

## 🔍 Troubleshooting

### Ver qué servicios están configurados

```bash
docker-compose config --services
```

### Ver servicios con perfiles

```bash
docker-compose config --services --profiles
```

### Verificar configuración

```bash
docker-compose config
```


# Integración de DefectDojo

Este documento describe la integración de **DefectDojo** en la aplicación médica para la gestión de vulnerabilidades de seguridad.

## ¿Qué es DefectDojo?

**DefectDojo** es una plataforma open source para la gestión centralizada de vulnerabilidades de seguridad. Permite:

- Consolidar resultados de múltiples herramientas de seguridad (SAST, DAST, SCA)
- Priorizar vulnerabilidades basándose en riesgos
- Automatizar flujos de trabajo de seguridad
- Generar reportes y dashboards de seguridad
- Integrarse con más de 180 herramientas de seguridad

## Arquitectura de la Integración

La integración incluye los siguientes componentes:

```
┌─────────────────┐
│  Aplicación Web │ (Puerto 5001)
│     Flask       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐        ┌─────────────────┐
│  Nginx Principal│  80 ►  │   Usuarios       │
│  (Proxy reverso)│        │                 │
└────────┬────────┘        └─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌─────────────────┐
│  Flask  │ │ DefectDojo Nginx │
│  /      │ │ /defectdojo      │
└─────────┘ └────────┬────────┘
                     │
                     ▼
┌─────────────────┐  ┌─────────────────┐
│   DefectDojo     │  │   PostgreSQL 15 │
│   (Puerto 8081) │  │   (Puerto 5432) │
└────────┬────────┘  └─────────────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│  Celery Worker   │  │  Celery Beat    │
│  (Tareas async)  │  │  (Tareas cron)  │
└─────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│     Redis 7     │
│   (Puerto 6379) │
└─────────────────┘
```

## Servicios Docker

### 1. DefectDojo (Aplicación Principal)

- **Imagen**: `defectdojo/defectdojo-django:latest`
- **Puerto interno**: `8081`
- **Exposición**: No se expone directamente; se atiende únicamente a través de Nginx (`defectdojo-nginx`)
- **Base de datos**: PostgreSQL (servicio `defectdojo-db`)
- **Cache/Tareas**: Redis (servicio `defectdojo-redis`)

### 2. DefectDojo Nginx (Proxy y estáticos)

- **Imagen**: `defectdojo/defectdojo-nginx:latest`
- **Puerto interno**: `8080` (no expuesto directamente)
- **Función**: Sirve los estáticos ya compilados y actúa como proxy hacia el servicio `defectdojo` (alias interno `uwsgi:3031`)
- **Volúmenes**: Comparte `defectdojo_static` para los assets generados por `collectstatic`
- **Acceso**: A través del nginx principal en http://localhost/defectdojo/

### 3. PostgreSQL Database

- **Imagen**: `postgres:15-alpine`
- **Puerto**: `5432`
- **Base de datos**: `defectdojo`
- **Usuario**: `defectdojo`
- **Contraseña**: `defectdojo_password` (⚠️ **Cambiar en producción**)

### 4. Redis

- **Imagen**: `redis:7-alpine`
- **Puerto**: `6379`
- **Uso**: Cache y broker de mensajes para Celery

### 5. Celery Worker

- **Imagen**: `defectdojo/defectdojo-django:latest`
- **Función**: Procesa tareas asíncronas (análisis de escaneos, etc.)

### 6. Celery Beat

- **Imagen**: `defectdojo/defectdojo-django:latest`
- **Función**: Ejecuta tareas programadas (sincronizaciones, limpiezas, etc.)

## Instalación y Configuración

### Requisitos Previos

- Docker y Docker Compose instalados
- Puerto 80 disponible (nginx principal)
- Puertos internos: 5001 (Flask), 8080 (DefectDojo nginx), 5432 (PostgreSQL), 6379 (Redis)

### Iniciar los Servicios

```bash
# Iniciar todos los servicios
docker-compose up -d

# Verificar que todos los servicios estén ejecutándose
docker-compose ps

# Ver logs de DefectDojo
docker-compose logs -f defectdojo
```

### Inicialización de DefectDojo

La primera vez que se inicia DefectDojo, es necesario preparar la base de datos y crear el usuario administrador:

```bash
# Ejecutar migraciones
docker-compose exec defectdojo python manage.py migrate

# Crear un superusuario (ajusta las credenciales antes de ejecutarlo)
docker-compose exec defectdojo /bin/sh -c \
  "DJANGO_SUPERUSER_USERNAME=admin \
   DJANGO_SUPERUSER_EMAIL=admin@example.com \
   DJANGO_SUPERUSER_PASSWORD=admin \
   python manage.py createsuperuser --noinput"
```

> 💡 Usa el comando anterior para generar rápidamente `admin/admin` y cambia la contraseña en el primer acceso.

### Verificar el Estado

```bash
# Verificar salud de los servicios
docker-compose ps

# Verificar logs de PostgreSQL
docker-compose logs defectdojo-db

# Verificar logs de DefectDojo
docker-compose logs defectdojo

# Verificar logs de Celery
docker-compose logs defectdojo-celeryworker
```

## Acceso a DefectDojo

### Desde la Aplicación Web

1. Abre la aplicación en http://localhost:5001
2. Haz clic en el enlace "🔒 DefectDojo - Gestión de Vulnerabilidades" en el header
3. Se abrirá DefectDojo en una nueva pestaña

### Acceso Directo

- **URL**: http://localhost/defectdojo/
- **Credenciales iniciales** (si usaste el comando anterior):
  - Usuario: `admin`
  - Contraseña: `admin`
- Cambia la contraseña desde la interfaz (`Admin → Users → admin`) o ejecuta:
  ```bash
  docker-compose exec defectdojo python manage.py changepassword admin
  ```

## Configuración de DefectDojo

### Variables de Entorno

Las variables de entorno están configuradas en `docker-compose.yml`:

```yaml
environment:
  DD_DATABASE_URL: postgresql://defectdojo:defectdojo_password@defectdojo-db:5432/defectdojo
  DD_CELERY_BROKER_URL: redis://defectdojo-redis:6379/0
  DD_CELERY_RESULT_BACKEND: redis://defectdojo-redis:6379/0
  DD_SECRET_KEY: defectdojo_secret_key_change_in_production
  DD_DEBUG: "True"
  DD_ALLOWED_HOSTS: "*"
```

⚠️ **IMPORTANTE**: Cambiar `DD_SECRET_KEY` y las contraseñas en producción.

## Uso de DefectDojo

### 1. Configuración Inicial

1. Accede a DefectDojo en http://localhost/defectdojo/
2. Inicia sesión con las credenciales del superusuario
3. Configura:
   - **Products**: Crea un producto para tu aplicación médica
   - **Engagements**: Crea un engagement para el proyecto
   - **Scans**: Configura escaneos de seguridad

### 2. Importar Resultados de Escaneos

DefectDojo puede importar resultados de múltiples herramientas:

- **SAST**: Bandit, SonarQube, Semgrep, etc.
- **DAST**: OWASP ZAP, Burp Suite, etc.
- **SCA**: Snyk, WhiteSource, etc.
- **Y más de 180 herramientas**

### 3. Gestión de Vulnerabilidades

- **Ver vulnerabilidades**: Dashboard principal muestra todas las vulnerabilidades
- **Priorizar**: Basado en severidad, explotabilidad, impacto
- **Asignar**: Asignar vulnerabilidades a desarrolladores
- **Seguimiento**: Rastrear el estado de remediación

### 4. Reportes

Genera reportes de:
- Vulnerabilidades por severidad
- Estado de remediación
- Tendencias temporales
- Cumplimiento normativo

## Relación con el Análisis CWE-699

DefectDojo puede ayudar a gestionar las vulnerabilidades identificadas en el análisis CWE-699:

- **CWE-1287**: Validación de tipo insuficiente
- **CWE-843**: Confusión de tipos (NaN no validado)
- **CWE-1021**: Falta de protección contra clickjacking
- **CWE-20**: Validación de entrada
- **CWE-703**: Manejo de excepciones
- **CWE-488**: Exposición de datos entre sesiones
- **CWE-942**: CORS demasiado permisivo

Puedes crear findings manualmente o importar resultados de herramientas de análisis estático que detecten estas vulnerabilidades.

## Mantenimiento

### Backup de la Base de Datos

```bash
# Crear backup
docker-compose exec defectdojo-db pg_dump -U defectdojo defectdojo > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T defectdojo-db psql -U defectdojo defectdojo < backup_YYYYMMDD.sql
```

### Actualizar DefectDojo

```bash
# Detener los servicios
docker-compose stop defectdojo defectdojo-celeryworker defectdojo-celerybeat

# Actualizar las imágenes
docker-compose pull

# Reiniciar los servicios
docker-compose up -d

# Ejecutar migraciones si es necesario
docker-compose exec defectdojo python manage.py migrate
```

### Reiniciar Servicios

```bash
# Reiniciar DefectDojo
docker-compose restart defectdojo

# Reiniciar Celery
docker-compose restart defectdojo-celeryworker defectdojo-celerybeat

# Reiniciar todos los servicios
docker-compose restart
```

## Solución de Problemas

### DefectDojo no inicia

1. Verificar que PostgreSQL esté ejecutándose:
   ```bash
   docker-compose ps defectdojo-db
   ```

2. Verificar logs:
   ```bash
   docker-compose logs defectdojo
   ```

3. Verificar conectividad a la base de datos:
   ```bash
   docker-compose exec defectdojo-db psql -U defectdojo -d defectdojo -c "SELECT 1;"
   ```

### Error de conexión a la base de datos

1. Verificar que las credenciales en `docker-compose.yml` coincidan
2. Verificar que el servicio PostgreSQL esté saludable:
   ```bash
   docker-compose ps defectdojo-db
   ```

### Puerto 80 ya en uso

Si el puerto 80 está en uso, modifica el puerto del nginx principal en `docker-compose.yml`:
```yaml
nginx:
  ports:
    - "8080:80"  # Cambiar 80 por otro puerto, por ejemplo 8080
```

Luego accede a DefectDojo en `http://localhost:8080/defectdojo/`

### Celery no procesa tareas

1. Verificar que Redis esté ejecutándose:
   ```bash
   docker-compose ps defectdojo-redis
   ```

2. Verificar logs de Celery:
   ```bash
   docker-compose logs defectdojo-celeryworker
   ```

## Seguridad en Producción

⚠️ **IMPORTANTE**: Antes de desplegar en producción:

1. **Cambiar contraseñas por defecto**:
   - PostgreSQL password
   - DefectDojo secret key
   - Usuarios de DefectDojo

2. **Configurar HTTPS**:
   - Usar un proxy reverso (nginx, traefik)
   - Configurar certificados SSL/TLS

3. **Restringir acceso**:
   - Configurar firewall
   - Limitar acceso a DefectDojo solo a usuarios autorizados
   - Configurar `DD_ALLOWED_HOSTS` correctamente

4. **Backups regulares**:
   - Configurar backups automáticos de la base de datos
   - Almacenar backups en ubicación segura

5. **Desactivar modo debug**:
   - Cambiar `DD_DEBUG: "False"` en producción

## Recursos Adicionales

- **Documentación oficial**: https://docs.defectdojo.com
- **Repositorio GitHub**: https://github.com/DefectDojo/django-DefectDojo
- **Comunidad**: https://github.com/DefectDojo/django-DefectDojo/discussions
- **API Documentation**: https://demo.defectdojo.com/api/v2/swagger/

## Soporte

Para problemas relacionados con DefectDojo:
- Consulta la documentación oficial
- Revisa los issues en GitHub: https://github.com/DefectDojo/django-DefectDojo/issues
- Consulta la comunidad en las discusiones de GitHub


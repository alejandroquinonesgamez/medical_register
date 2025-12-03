# Configuración de DefectDojo

## Resumen

DefectDojo está configurado principalmente con valores **estándar**, con algunas **personalizaciones necesarias** para integrar el servicio Nginx oficial.

---

## Configuraciones ESTÁNDAR (Por Defecto)

### Servicios Base
- ✅ **Imagen oficial**: `defectdojo/defectdojo-django:latest`
- ✅ **Base de datos**: PostgreSQL 15 (estándar de DefectDojo)
- ✅ **Cache/Broker**: Redis 7 (estándar de DefectDojo)
- ✅ **Celery Worker**: Para tareas asíncronas (estándar)
- ✅ **Celery Beat**: Para tareas programadas (estándar)

### Variables de Entorno Estándar
- ✅ Variables de entorno de DefectDojo (`DD_*`) con valores estándar
- ✅ Configuración de base de datos estándar
- ✅ Configuración de Celery estándar
- ✅ `DD_DEBUG: "True"` (estándar para desarrollo)
- ✅ `DD_ALLOWED_HOSTS: "*"` (estándar para desarrollo)

### Configuración de Django
- ✅ Configuraciones de Django por defecto de DefectDojo
- ✅ Sistema de auditoría (django-auditlog) estándar
- ✅ API habilitada por defecto
- ✅ Sin modificaciones en el código fuente de DefectDojo

---

## Configuraciones PERSONALIZADAS (Modificadas)

### 1. Servicio Nginx Oficial
**Razón**: Servir archivos estáticos de forma eficiente y hacer proxy a uwsgi

```yaml
defectdojo-nginx:
  image: defectdojo/defectdojo-nginx:latest
  ports:
    - "8080:8080"
```

**Estado**: ✅ **Estándar de DefectDojo** - Es el servicio Nginx oficial recomendado

### 2. Deshabilitación de WhiteNoise
**Razón**: Nginx sirve los archivos estáticos, no es necesario WhiteNoise

```yaml
DD_WHITENOISE: "False"
```

**Estado**: ⚠️ **Personalizado** - Necesario cuando se usa Nginx oficial

### 3. Puerto Interno 8081
**Razón**: Nginx expone el puerto 8080, Django corre internamente en 8081

```yaml
expose:
  - "8081"  # No se expone directamente
```

**Estado**: ⚠️ **Personalizado** - Arquitectura con Nginx como proxy

### 4. Alias de Red 'uwsgi'
**Razón**: El Nginx oficial busca el servicio Django por el nombre 'uwsgi'

```yaml
networks:
  defectdojo-network:
    aliases:
      - uwsgi
```

**Estado**: ⚠️ **Personalizado** - Requerido por la configuración del Nginx oficial

### 5. Volumen Compartido para Estáticos
**Razón**: Nginx y Django necesitan acceso a los archivos estáticos

```yaml
volumes:
  - defectdojo_static:/app/static
```

**Estado**: ⚠️ **Personalizado** - Necesario para la integración con Nginx

### 6. Healthchecks Personalizados
**Razón**: Verificar que los servicios funcionen correctamente

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/')"]
```

**Estado**: ⚠️ **Personalizado** - Adaptado a nuestra arquitectura

---

## Configuraciones de Desarrollo (No para Producción)

⚠️ **IMPORTANTE**: Estas configuraciones son para desarrollo y deben cambiarse en producción:

1. **`DD_DEBUG: "True"`** → Cambiar a `"False"` en producción
2. **`DD_ALLOWED_HOSTS: "*"`** → Restringir a dominios específicos en producción
3. **`DD_SECRET_KEY`** → Cambiar por una clave segura en producción
4. **Contraseñas de base de datos** → Cambiar todas las contraseñas en producción

---

## Conclusión

**DefectDojo está configurado principalmente con valores estándar**, con las siguientes personalizaciones necesarias para la integración del servicio Nginx oficial:

- ✅ Uso del servicio Nginx oficial de DefectDojo (recomendado)
- ✅ Configuración adaptada para que Nginx sirva estáticos
- ✅ Arquitectura con proxy reverso (Nginx → Django)
- ✅ Healthchecks adaptados a la arquitectura

**No hay modificaciones inusuales o problemáticas**. Todas las personalizaciones son estándar cuando se usa el servicio Nginx oficial de DefectDojo.

---

## Referencias

- [Documentación oficial de DefectDojo](https://docs.defectdojo.com)
- [Docker Compose de DefectDojo](https://github.com/DefectDojo/django-DefectDojo)


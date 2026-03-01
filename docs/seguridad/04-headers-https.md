# Headers de seguridad y HTTPS

Los headers se configuran en `app/__init__.py` y se envían en todas las respuestas.

## Headers implementados

- **`X-Frame-Options: DENY`** — Previene clickjacking al impedir que la página se cargue en iframes.
- **`X-Content-Type-Options: nosniff`** — Previene MIME type sniffing.
- **`Content-Security-Policy: frame-ancestors 'none'`** — Refuerza la no inclusión en iframes (CSP nivel 2).
- **`X-XSS-Protection: 1; mode=block`** — Protección XSS legacy (compatible con navegadores antiguos).

## Strict-Transport-Security (HSTS)

HSTS fuerza al navegador a usar solo HTTPS durante un período.

- **Configuración**: `app/config.py` → `HSTS_CONFIG`.
- **Activación**: Solo se envía cuando `SESSION_COOKIE_SECURE=true` o la petición viene por HTTPS (`request.is_secure`).

**Parámetros** (variables de entorno):

- **`HSTS_MAX_AGE`** (default: `31536000`): segundos que el navegador recordará usar HTTPS (1 año).
- **`HSTS_INCLUDE_SUBDOMAINS`** (default: `true`): aplica la política a subdominios.
- **`HSTS_PRELOAD`** (default: `false`): inclusión en listas de preload de navegadores.

**Importante:** Activar HSTS solo cuando HTTPS esté correctamente configurado. En desarrollo local (HTTP), HSTS no se activa.

## Datos en reposo (opcional)

- **SQLCipher**: almacenamiento cifrado en disco con `STORAGE_BACKEND=sqlcipher`.
- **Clave**: `SQLCIPHER_KEY` obligatoria en ese modo.

[← Índice de seguridad](../SEGURIDAD.md)

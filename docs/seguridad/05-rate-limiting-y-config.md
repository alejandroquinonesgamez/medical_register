# Rate limiting y configuración centralizada

## Protección contra fuerza bruta

- **Rate limiting**: Flask-Limiter.
- **Límite**: 3 peticiones por IP por minuto **solo** en `POST /api/auth/login` y `POST /api/auth/register`. El resto de la API no está limitado.
- **Configuración**: `app/__init__.py` (limiter) y `app/routes.py` (decorador `@limiter.limit("3 per minute")` en ambas rutas). Deshabilitado en tests con `APP_TESTING=1`.

## Configuración de seguridad en `app/config.py`

- **`SESSION_CONFIG`**: Cookies de sesión (HttpOnly, Secure, SameSite).
- **`HSTS_CONFIG`**: HSTS (max-age, includeSubDomains, preload).
- **`PASSWORD_HASH_CONFIG`**: Parámetros de Argon2id (time_cost, memory_cost, parallelism, hash_len, salt_len). Los hashes se migran al nuevo coste en el siguiente login (ver [Autenticación y contraseñas](02-autenticacion-contrasenas.md)).
- **`AUTH_CONFIG`**: Límites de longitud de username y password.
- **reCAPTCHA v3**: `RECAPTCHA_SITE_KEY`, `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_MIN_SCORE` (y opcionalmente `RECAPTCHA_VERIFY_URL`). Se leen desde variables de entorno (`.env`). Especificación completa en [Autenticación y contraseñas](02-autenticacion-contrasenas.md).

Esta centralización facilita la gestión y auditoría de las políticas de seguridad.

[← Índice de seguridad](../SEGURIDAD.md)

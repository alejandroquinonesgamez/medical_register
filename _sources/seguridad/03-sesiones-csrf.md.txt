# Sesiones seguras y protección CSRF

## Sesiones seguras

- **Sesión de servidor** con cookie `HttpOnly` (previene acceso desde JavaScript).
- **SameSite**: `Lax` por defecto (protección CSRF adicional).
- **Secure**: Configurable vía `SESSION_COOKIE_SECURE=true` en producción (solo se envía por HTTPS).
- **Clave de sesión**: `FLASK_SECRET_KEY` (o se genera aleatoria si no existe).
- **Configuración**: `app/config.py` → `SESSION_CONFIG`.

## Protección CSRF

- **Token CSRF por sesión**: se genera en backend y se devuelve en `/api/auth/me`, `/api/auth/login`, `/api/auth/register`.
- **Validación**: las rutas `POST` sensibles requieren el header `X-CSRF-Token`.
- **Frontend**: envía automáticamente el token en operaciones de escritura.

[← Índice de seguridad](../SEGURIDAD.md)

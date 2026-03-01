# Seguridad: documentación

Documentación de las medidas de seguridad de la aplicación, organizada por temas.

| Documento | Contenido |
|-----------|-----------|
| [01. Validación y sanitización de entradas](seguridad/01-validacion-entradas.md) | Nombres, peso, altura, fecha, IMC y validación defensiva |
| [02. Autenticación y contraseñas](seguridad/02-autenticacion-contrasenas.md) | Argon2id, registro, HIBP, reCAPTCHA v3, login, migración de hash, logout, almacenamiento y endpoints de auth |
| [03. Sesiones y CSRF](seguridad/03-sesiones-csrf.md) | Sesiones seguras (HttpOnly, SameSite, Secure) y protección CSRF |
| [04. Headers de seguridad, HSTS y SQLCipher](seguridad/04-headers-https.md) | X-Frame-Options, CSP, HSTS, cifrado de base de datos |
| [05. Rate limiting y configuración](seguridad/05-rate-limiting-y-config.md) | Límites por IP en login/register y configuración centralizada |
| [06. WAF: ModSecurity + OWASP CRS](seguridad/06-waf-modsecurity.md) | Arquitectura, configuración, paranoia levels, exclusiones, batería de ataques bloqueados, logs y producción |

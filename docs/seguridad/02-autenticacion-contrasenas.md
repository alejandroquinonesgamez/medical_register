# Autenticación y contraseñas

## Algoritmo de hash y materiales criptográficos

- **Algoritmo**: `Argon2id` con parámetros configurables en `app/config.py` → `PASSWORD_HASH_CONFIG`:
  - **time_cost**: nº de iteraciones sobre la memoria; mayor valor = más lento y más resistencia a fuerza bruta (típico 2–4 para login).
  - **memory_cost**: memoria en KiB (p. ej. 65536 = 64 MiB); Argon2 es memory-hard, más memoria dificulta ataques con GPU/ASIC.
  - **parallelism**: nº de hilos/lanes en paralelo (suele usarse 1–4 según CPU).
  - **hash_len**: longitud del hash de salida en bytes (32 = 256 bits); estándar para derivación de claves.
  - **salt_len**: longitud del salt aleatorio en bytes (16 = 128 bits); un salt distinto por contraseña evita tablas arcoíris.
  Los mismos parámetros están documentados como comentarios en `app/config.py`. Si se cambia la configuración, los hashes existentes se migran de forma transparente en el siguiente login.
- **Salt**: Argon2id genera un **salt aleatorio único por usuario** (incluido en el hash resultante).
- **Pepper**: valor opcional del servidor (`PASSWORD_PEPPER`) concatenado a la contraseña antes de hashear. **No se guarda en base de datos**.

## Registro

1. **Entrada del usuario (cliente)**: el usuario introduce `username` y `password` en el formulario de registro.
2. **Validación cliente**: se valida formato/longitud mínima en frontend para feedback rápido.
3. **Envío al servidor**: el cliente envía `POST /api/auth/register` con JSON: `username`, `password`, `recaptcha_token` (si reCAPTCHA v3 está configurado). **No se almacena la contraseña en `localStorage` ni en cookies.**
4. **Transporte**: HTTPS en producción (`SESSION_COOKIE_SECURE=true`), HSTS cuando HTTPS está activo. Rate limiting: 3 intentos por IP por minuto solo en login y register (ver [Rate limiting y configuración](05-rate-limiting-y-config.md)).
5. **Normalización**: el servidor normaliza `username` y valida reglas de formato.
6. **HIBP** (k‑anonymity): se calcula SHA‑1 de la contraseña; se envía **solo el prefijo** del hash a HIBP. Si la contraseña aparece, **se rechaza**.
7. **Fallback local**: si HIBP falla y `HIBP_FAIL_CLOSED=false`, se consulta `data/common_passwords_fallback.txt`. Si `HIBP_FAIL_CLOSED=true` y HIBP falla, **se rechaza**.
8. **Hasheo**: se concatena el `pepper` en memoria y se aplica **Argon2id** con salt aleatorio. Solo se guarda el hash; **nunca** la contraseña en texto plano.
9. **Respuesta**: sesión de servidor, `csrf_token`, cookie `HttpOnly`. El cliente guarda `csrf_token` en memoria.

## reCAPTCHA v3

### Configuración (variables en `.env`)

- **`RECAPTCHA_SITE_KEY`**: clave pública de sitio (se expone al cliente vía `GET /api/config`).
- **`RECAPTCHA_SECRET_KEY`**: clave secreta para verificar el token en el servidor.
- **`RECAPTCHA_MIN_SCORE`** (opcional): umbral de score 0.0–1.0; por defecto `0.5`. Si el score devuelto por Google es menor, se rechaza la petición.

Si no se configuran `RECAPTCHA_SITE_KEY` y `RECAPTCHA_SECRET_KEY`, la verificación se omite (útil para desarrollo y tests).

**Desarrollo local**: en la [consola de reCAPTCHA Admin](https://www.google.com/recaptcha/admin) hay que añadir `localhost` (y `127.0.0.1` si se accede por IP) a la lista de dominios autorizados de la clave de sitio; si no, Google rechazará los tokens. Tras cambiar el `.env`, reiniciar los contenedores (`make down` y `make`).

### Comportamiento

El cliente obtiene un token con `grecaptcha.execute(siteKey, { action: 'login'|'register' })` y lo envía como `recaptcha_token`. El servidor verifica el token con la API de Google y rechaza si falla, si la acción no coincide o si el score es menor que `RECAPTCHA_MIN_SCORE`.

### Comprobar el score (ratio de validez)

- **Por petición**: la aplicación no registra ni expone el score por defecto. Para ver el score de cada intento de login/registro hay que añadir logging en el servidor (por ejemplo en `app/routes.py` o en `verify_recaptcha_v3` en `app/helpers.py`) y consultar los logs del contenedor.
- **Estadísticas agregadas**: en la consola de [reCAPTCHA Admin](https://www.google.com/recaptcha/admin), sección Analytics/Estadísticas, se puede ver la distribución de scores, volumen de solicitudes y tasa de solicitudes dudosas o bloqueadas; no el score de una petición concreta.

## Login

1. **Envío**: `POST /api/auth/login` con JSON (y `recaptcha_token` si reCAPTCHA está activo).
2. **Servidor**: verifica reCAPTCHA si está configurado; busca usuario; verifica contraseña con Argon2id.
3. **Resultado**: si coincide, crea sesión y devuelve `csrf_token`; si falla, error genérico.
4. **Migración de hash**: si `PASSWORD_HASH_CONFIG` ha cambiado, tras verificar se rehashea y se actualiza el hash en BD en el siguiente login.

## Logout

- `POST /api/auth/logout` con `X-CSRF-Token`. El servidor elimina `user_id` de sesión.

## Almacenamiento

**En el cliente:** La contraseña no se almacena. La sesión usa cookie `HttpOnly` y `SameSite`; el cliente conserva `csrf_token` en memoria. Datos de perfil y pesos en `localStorage` por usuario; no se guardan credenciales.

**En el servidor:** Hash Argon2id por usuario; pepper solo en configuración (`PASSWORD_PEPPER`); sesión en cookie `HttpOnly` y `SameSite`.

## API de autenticación

- `POST /api/auth/register` → creación de usuario + sesión.
- `POST /api/auth/login` → verificación y sesión.
- `POST /api/auth/logout` → cierre de sesión (requiere CSRF).
- `GET /api/auth/me` → estado de sesión + `csrf_token`.

El cliente envía `X-CSRF-Token` en operaciones de escritura. La contraseña solo viaja en el cuerpo del POST en registro/login.

[← Índice de seguridad](../SEGURIDAD.md)

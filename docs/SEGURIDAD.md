## Seguridad: entradas, contraseñas y sesiones

### Validación y sanitización de entradas
- **Nombres y apellidos**: validación de longitud y caracteres permitidos (solo letras, espacios, guiones y apóstrofes). Se eliminan caracteres peligrosos y se normalizan espacios. Implementado en `app/helpers.py` (`validate_and_sanitize_name`).
- **Peso, altura y fecha de nacimiento**: validación de tipo y rango en backend (`/api/user`, `/api/weight`) con límites centralizados en `app/config.py`.
- **Validación defensiva**: cálculo de IMC solo si los datos están dentro de rango (backend y frontend).

### Autenticación y contraseñas
- **Algoritmo**: `Argon2id` con parámetros configurables (`time_cost`, `memory_cost`, `parallelism`, `hash_len`, `salt_len`).
- **Pepper**: valor opcional del servidor (`PASSWORD_PEPPER`) concatenado a la contraseña antes de hashear.
- **Bloqueo de contraseñas filtradas (HIBP)**: se usa la API de Pwned Passwords con
  k-anonymity (SHA-1 parcial). Si aparece en filtraciones conocidas, se rechaza.
- **Fallback local**: lista de contraseñas comunes en
  `data/common_passwords_fallback.txt` (configurable con
  `COMMON_PASSWORDS_FALLBACK_PATH`).
- **Flujo (registro)**:
  - El usuario envía `username` y `password`.
  - El backend consulta **HIBP** (k‑anonymity). Si HIBP falla, se usa el **fallback local**.
  - Si la contraseña está filtrada, se rechaza y se solicita otra.
  - Si es válida, se aplica **Argon2id + pepper** y se guarda el hash en backend.
  - Se responde con registro OK y se crea sesión.
- **Flujo (login)**: compara con `verify_password` (Argon2id) y crea sesión.
- **No se guarda contraseña en el navegador**. El frontend solo usa la API segura.

### Sesiones seguras
- **Sesión de servidor** con cookie `HttpOnly`.
- **SameSite**: `Lax` por defecto.
- **Secure** opcional vía `SESSION_COOKIE_SECURE=true` en producción.
- **Clave de sesión**: `FLASK_SECRET_KEY` (o se genera aleatoria si no existe).

### Protección CSRF
- **Token CSRF por sesión**: se genera en backend y se devuelve en `/api/auth/me`, `/api/auth/login`, `/api/auth/register`.
- **Validación**: todas las rutas `POST` sensibles requieren `X-CSRF-Token`.
- **Frontend**: envía automáticamente el token en operaciones de escritura.

### Datos en reposo (opcional)
- **SQLCipher**: almacenamiento cifrado en disco cuando `STORAGE_BACKEND=sqlcipher`.
- **Clave de cifrado**: `SQLCIPHER_KEY` obligatoria.

### Headers de seguridad
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Content-Security-Policy: frame-ancestors 'none'`
- `X-XSS-Protection: 1; mode=block`


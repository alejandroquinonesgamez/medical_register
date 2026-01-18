## Seguridad: entradas, contraseñas y sesiones

### Validación y sanitización de entradas
- **Nombres y apellidos**: validación de longitud y caracteres permitidos (solo letras, espacios, guiones y apóstrofes). Se eliminan caracteres peligrosos y se normalizan espacios. Implementado en `app/helpers.py` (`validate_and_sanitize_name`).
- **Peso, altura y fecha de nacimiento**: validación de tipo y rango en backend (`/api/user`, `/api/weight`) con límites centralizados en `app/config.py`.
- **Validación defensiva**: cálculo de IMC solo si los datos están dentro de rango (backend y frontend).

### Autenticación y contraseñas
- **Algoritmo**: `Argon2id` con parámetros configurables (`time_cost`, `memory_cost`, `parallelism`, `hash_len`, `salt_len`).
- **Pepper**: valor opcional del servidor (`PASSWORD_PEPPER`) concatenado a la contraseña antes de hashear.
- **Flujo**:
  - Registro: valida usuario y contraseña, hashea con Argon2id y guarda el hash en backend.
  - Login: compara con `verify_password` (Argon2id).
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


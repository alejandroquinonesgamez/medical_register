## Seguridad: entradas, contraseñas y sesiones

### Validación y sanitización de entradas
- **Nombres y apellidos**: validación de longitud y caracteres permitidos (solo letras, espacios, guiones y apóstrofes). Se eliminan caracteres peligrosos y se normalizan espacios. Implementado en `app/helpers.py` (`validate_and_sanitize_name`).
- **Peso, altura y fecha de nacimiento**: validación de tipo y rango en backend (`/api/user`, `/api/weight`) con límites centralizados en `app/config.py`.
- **Validación defensiva**: cálculo de IMC solo si los datos están dentro de rango (backend y frontend).

### Autenticación y contraseñas (detalle completo)
#### Algoritmo de hash y materiales criptográficos
- **Algoritmo**: `Argon2id` con parámetros configurables (`time_cost`, `memory_cost`, `parallelism`, `hash_len`, `salt_len`).
- **Salt**: Argon2id genera un **salt aleatorio único por usuario** (incluido en el hash resultante).
- **Pepper**: valor opcional del servidor (`PASSWORD_PEPPER`) concatenado a la contraseña antes de hashear. **No se guarda en base de datos**.

#### Generación y transmisión de credenciales (registro)
1. **Entrada del usuario (cliente)**: el usuario introduce `username` y `password` en el formulario de registro.
2. **Validación cliente**: se valida formato/longitud mínima en frontend para feedback rápido.
3. **Envío al servidor**: el cliente envía `POST /api/auth/register` con JSON:
   - `username`
   - `password`
   - **No se almacena la contraseña en `localStorage` ni en cookies.**
4. **Transporte**:
   - En producción debe usarse **HTTPS** para proteger la contraseña en tránsito.
   - El contenido viaja en el cuerpo del POST y **no se registra** en el cliente.

#### Verificación de contraseñas filtradas (HIBP + fallback)
5. **Normalización**: el servidor normaliza `username` y valida reglas de formato.
6. **Comprobación HIBP** (k‑anonymity):
   - Se calcula SHA‑1 de la contraseña en el servidor.
   - Se envía **solo el prefijo** del hash a HIBP (`/range/<prefijo>`).
   - Si HIBP responde y la contraseña aparece, **se rechaza**.
7. **Fallback local**:
   - Si HIBP falla y `HIBP_FAIL_CLOSED=false`, se consulta `data/common_passwords_fallback.txt`.
   - Si aparece, **se rechaza**.
   - Si `HIBP_FAIL_CLOSED=true` y HIBP falla, **se rechaza** (fail‑closed).

#### Hashing y almacenamiento en servidor
8. **Hasheo**:
   - Se concatena el `pepper` en memoria (`password + PASSWORD_PEPPER`).
   - Se aplica **Argon2id** con salt aleatorio.
9. **Persistencia**:
   - Solo se guarda **el hash Argon2id** (que ya incluye el salt).
   - **Nunca** se almacena la contraseña en texto plano.

#### Respuesta y sesión (registro)
10. **Sesión**:
   - Si el registro es correcto, se crea sesión de servidor.
   - Se devuelve `csrf_token` y se setea cookie de sesión `HttpOnly`.
11. **Cliente**:
   - El cliente guarda `csrf_token` en memoria (no en `localStorage`).
   - Se inicia flujo de perfil del usuario.

#### Inicio de sesión (login)
1. **Entrada del usuario**: `username` + `password`.
2. **Envío**: `POST /api/auth/login` con JSON.
3. **Servidor**:
   - Busca el usuario por `username`.
   - Hashea `password + pepper` y verifica con Argon2id (`verify_password`).
4. **Resultado**:
   - Si coincide, crea sesión y devuelve `csrf_token`.
   - Si falla, devuelve error genérico de credenciales inválidas.

#### Cierre de sesión (logout)
- `POST /api/auth/logout` con `X-CSRF-Token`.
- El servidor elimina `user_id` de sesión.

#### Almacenamiento en el cliente
- **Contraseña**: **no se almacena** en localStorage, cookies ni memoria persistente.
- **Sesión**:
  - Se mantiene con cookie `HttpOnly` y `SameSite` en el navegador.
  - El cliente solo conserva `csrf_token` en memoria mientras dure la sesión.
- **Datos de usuario**:
  - Datos de perfil y pesos se almacenan en `localStorage` **bajo clave por usuario**.
  - No se guarda ninguna credencial ni hash en el cliente.

#### Almacenamiento en el servidor
- **Hash Argon2id** por usuario en almacenamiento backend.
- **Pepper** solo en configuración del servidor (`PASSWORD_PEPPER`).
- **Sesión**: en memoria/cookie de sesión con `HttpOnly` y `SameSite`.

#### Papel de la API en la transmisión
- **Endpoints de autenticación**:
  - `POST /api/auth/register` → creación de usuario + sesión.
  - `POST /api/auth/login` → verificación y sesión.
  - `POST /api/auth/logout` → cierre de sesión.
  - `GET /api/auth/me` → estado de sesión + `csrf_token`.
- **Protección CSRF**:
  - Para operaciones de escritura, el cliente añade `X-CSRF-Token`.
- **Contenido sensible**:
  - Solo la contraseña viaja en el cuerpo del POST durante registro/login.
  - En el resto de operaciones, se usa la sesión (cookie) + CSRF token.

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
- `X-Frame-Options: DENY` - Previene clickjacking
- `X-Content-Type-Options: nosniff` - Previene MIME type sniffing
- `Content-Security-Policy: frame-ancestors 'none'` - Previene embedding en iframes
- `X-XSS-Protection: 1; mode=block` - Protección XSS (legacy)
- `Strict-Transport-Security` (HSTS) - Solo cuando `SESSION_COOKIE_SECURE=true` o conexión HTTPS:
  - `max-age=31536000` (1 año por defecto, configurable vía `HSTS_MAX_AGE`)
  - `includeSubDomains` (por defecto, configurable vía `HSTS_INCLUDE_SUBDOMAINS`)
  - `preload` (opcional, configurable vía `HSTS_PRELOAD`)

**Nota sobre HSTS**: El header `Strict-Transport-Security` solo se envía cuando:
- `SESSION_COOKIE_SECURE=true` está configurado, o
- La petición viene por HTTPS (`request.is_secure`)

Esto asegura que HSTS solo se active cuando realmente se está usando HTTPS.


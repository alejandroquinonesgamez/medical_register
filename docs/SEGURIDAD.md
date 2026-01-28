## Seguridad: entradas, contraseñas y sesiones

### Validación y sanitización de entradas
- **Nombres y apellidos**: validación de longitud y caracteres permitidos (solo letras, espacios, guiones y apóstrofes). Se eliminan caracteres peligrosos y se normalizan espacios. Implementado en `app/helpers.py` (`validate_and_sanitize_name`).
- **Peso, altura y fecha de nacimiento**: validación de tipo y rango en backend (`/api/user`, `/api/weight`) con límites centralizados en `app/config.py`.
- **Validación defensiva**: cálculo de IMC solo si los datos están dentro de rango (backend y frontend).

### Autenticación y contraseñas (detalle completo)
#### Algoritmo de hash y materiales criptográficos
- **Algoritmo**: `Argon2id` con parámetros configurables en `app/config.py` → `PASSWORD_HASH_CONFIG`:
  - **time_cost**: nº de iteraciones sobre la memoria; mayor valor = más lento y más resistencia a fuerza bruta (típico 2–4 para login).
  - **memory_cost**: memoria en KiB (p. ej. 65536 = 64 MiB); Argon2 es memory-hard, más memoria dificulta ataques con GPU/ASIC.
  - **parallelism**: nº de hilos/lanes en paralelo (suele usarse 1–4 según CPU).
  - **hash_len**: longitud del hash de salida en bytes (32 = 256 bits); estándar para derivación de claves.
  - **salt_len**: longitud del salt aleatorio en bytes (16 = 128 bits); un salt distinto por contraseña evita tablas arcoíris.
  Los mismos parámetros están documentados como comentarios en `app/config.py`. Si se cambia la configuración, los hashes existentes se migran de forma transparente en el siguiente login (véase apartado de inicio de sesión).
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
   - **HTTPS obligatorio en producción**: La aplicación está preparada para usar HTTPS mediante la configuración `SESSION_COOKIE_SECURE=true`.
   - **HSTS (HTTP Strict Transport Security)**: Cuando HTTPS está activo, se envía el header `Strict-Transport-Security` con `max-age=31536000` (1 año) para forzar conexiones seguras.
   - El contenido viaja en el cuerpo del POST cifrado por HTTPS y **no se registra** en el cliente.
   - **Rate limiting**: Protección contra fuerza bruta con límite de 3 intentos por IP por minuto (configurado en `app/__init__.py`).

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
5. **Migración de parámetros de hash**: si en configuración se ha cambiado `PASSWORD_HASH_CONFIG` (p. ej. `time_cost`, `memory_cost`), tras verificar la contraseña el servidor rehashea con la configuración actual y **actualiza el hash en base de datos**. Así los hashes antiguos siguen siendo válidos y se migran de forma transparente en el siguiente login.

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
- **Sesión de servidor** con cookie `HttpOnly` (previene acceso desde JavaScript).
- **SameSite**: `Lax` por defecto (protección CSRF adicional).
- **Secure**: Configurable vía `SESSION_COOKIE_SECURE=true` en producción (solo se envía por HTTPS).
- **Clave de sesión**: `FLASK_SECRET_KEY` (o se genera aleatoria si no existe).
- **Configuración centralizada**: Todas las opciones de sesión están en `app/config.py` (`SESSION_CONFIG`).

### Protección CSRF
- **Token CSRF por sesión**: se genera en backend y se devuelve en `/api/auth/me`, `/api/auth/login`, `/api/auth/register`.
- **Validación**: todas las rutas `POST` sensibles requieren `X-CSRF-Token`.
- **Frontend**: envía automáticamente el token en operaciones de escritura.

### Datos en reposo (opcional)
- **SQLCipher**: almacenamiento cifrado en disco cuando `STORAGE_BACKEND=sqlcipher`.
- **Clave de cifrado**: `SQLCIPHER_KEY` obligatoria.

### Headers de seguridad

La aplicación implementa múltiples headers de seguridad HTTP para proteger contra diversos tipos de ataques. Todos los headers se configuran en `app/__init__.py` y se envían en todas las respuestas.

#### Headers implementados

- **`X-Frame-Options: DENY`** - Previene clickjacking al impedir que la página se cargue en iframes.
- **`X-Content-Type-Options: nosniff`** - Previene MIME type sniffing, forzando al navegador a respetar el Content-Type declarado.
- **`Content-Security-Policy: frame-ancestors 'none'`** - Complementa X-Frame-Options, previene embedding en iframes (CSP nivel 2).
- **`X-XSS-Protection: 1; mode=block`** - Protección XSS legacy para navegadores antiguos (Chrome/Edge ya no lo usan, pero es compatible).

#### Strict-Transport-Security (HSTS)

**HSTS** (HTTP Strict Transport Security) fuerza al navegador a usar solo conexiones HTTPS durante un período determinado.

**Configuración:**
- **Ubicación**: `app/config.py` → `HSTS_CONFIG`
- **Activación condicional**: Solo se envía cuando:
  - `SESSION_COOKIE_SECURE=true` está configurado, o
  - La petición viene por HTTPS (`request.is_secure`)
  
**Parámetros configurables** (variables de entorno):
- **`HSTS_MAX_AGE`** (default: `31536000`): Tiempo en segundos que el navegador recordará usar HTTPS (1 año por defecto).
- **`HSTS_INCLUDE_SUBDOMAINS`** (default: `true`): Extiende la política a todos los subdominios.
- **`HSTS_PRELOAD`** (default: `false`): Permite inclusión en listas de preload de navegadores (requiere registro manual).

**Ejemplo de header enviado:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Importante**: 
- HSTS solo debe activarse cuando HTTPS está correctamente configurado.
- Una vez que un navegador recibe HSTS, recordará usar HTTPS incluso si el usuario escribe HTTP.
- En desarrollo local (HTTP), HSTS no se activa automáticamente.

### Protección contra fuerza bruta

- **Rate limiting**: Implementado con Flask-Limiter.
- **Límite**: 3 intentos por IP por minuto para todas las rutas de API.
- **Configuración**: `app/__init__.py` (deshabilitado en tests con `APP_TESTING=1`).
- **Alcance**: Aplica a todos los endpoints `/api/*`, incluyendo registro y login.

### Configuración de seguridad centralizada

Todas las configuraciones de seguridad están centralizadas en `app/config.py`:

- **`SESSION_CONFIG`**: Configuración de cookies de sesión (HttpOnly, Secure, SameSite).
- **`HSTS_CONFIG`**: Configuración de HSTS (max-age, includeSubDomains, preload).
- **`PASSWORD_HASH_CONFIG`**: Parámetros de Argon2id (time_cost, memory_cost, parallelism, hash_len, salt_len); ver comentarios en `app/config.py` y apartado "Algoritmo de hash y materiales criptográficos" arriba. Los hashes se migran al nuevo coste/parámetros en el siguiente login.
- **`AUTH_CONFIG`**: Límites de longitud de username y password.

Esto facilita la gestión y auditoría de las políticas de seguridad.


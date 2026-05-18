# Pasos para completar las evidencias (PPS Git)

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

---

Guía operativa para cerrar los documentos en `docs/git_docs/PPS_git/` (`firma_commits.md`, `github.md`, `gitleaks.md`, `proteccion-ramas.md`, `semgrep.md`). El ejercicio de **gitignore** ya está hecho (`gitignore.md`).

---

## Constantes del espacio de trabajo

```bash
# Rutas locales
export PPS_ANDROID="/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/medical_register_android"
export PPS_BACKEND="/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/Aplicación Médica"

# Remotos GitHub (SSH)
# Android:  git@github.com:alejandroquinonesgamez/medical_register_apk.git  → rama main
# Backend:  git@github.com:alejandroquinonesgamez/medical_register.git      → rama dev

# Carpeta de capturas (crear una vez)
export PPS_IMG="$PPS_BACKEND/docs/git_docs/img/PPS_git"
mkdir -p "$PPS_IMG"/{GPG,github,gitleaks,proteccion-ramas,semgrep}
```

| Proyecto | Ruta local | Remoto `origin` | Rama habitual |
|---|---|---|---|
| Cliente Android (APK) | `$PPS_ANDROID` | `git@github.com:alejandroquinonesgamez/medical_register_apk.git` | `main` |
| Backend *Aplicación Médica* | `$PPS_BACKEND` | `git@github.com:alejandroquinonesgamez/medical_register.git` | `dev` |

Comprobar o fijar remoto del Android:

```bash
cd "$PPS_ANDROID"
git remote set-url origin git@github.com:alejandroquinonesgamez/medical_register_apk.git
git remote -v
git push origin main
```

Backend:

```bash
cd "$PPS_BACKEND"
git remote -v
git push origin dev
```

> Cada repositorio en GitHub tiene su propia **Settings** / **Security**. Repite la configuración en `medical_register_apk` y en `medical_register` si la práctica lo exige en ambos.

### Si `git push` falla con `Permission denied (publickey)`

Git usa SSH con la clave que indiques. En este equipo la clave de GitHub suele ser `~/.ssh/id_ed25519_github` (no `~/git`, que puede no existir).

**1. Probar conexión a GitHub**

```bash
ssh -i ~/.ssh/id_ed25519_github -o IdentitiesOnly=yes -T git@github.com
```

Esperado: `Hi alejandroquinonesgamez! You've successfully authenticated...`

**2. Configuración recomendada (todos los repos)** — archivo `~/.ssh/config`:

```
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github
  IdentitiesOnly yes
```

**3. Solo para un repo** (ya aplicado en los clones PPS si hace falta):

```bash
cd "$PPS_ANDROID"   # o $PPS_BACKEND
git config core.sshCommand "ssh -i ~/.ssh/id_ed25519_github -o IdentitiesOnly=yes"
```

**4. Si sigue fallando**: comprueba en GitHub → **Settings** → **SSH and GPG keys** que esté la clave pública (`cat ~/.ssh/id_ed25519_github.pub`). Si usas otra ruta de clave, sustituye en los comandos.

**Orden recomendado** (de menos a más invasivo): `firma_commits` → `proteccion-ramas` → `gitleaks` → `github` → `semgrep`.

### Commits sin passphrase GPG (mientras no recuerdes la clave)

En cada `git commit` de esta guía:

```bash
git commit --no-gpg-sign -m "mensaje"
# o, en el clone:
git config commit.gpgsign false
```

---

## Estado del progreso

| Apartado | Documento | Estado | Siguiente acción |
|----------|-----------|--------|------------------|
| 0 | `gitignore.md` | ✅ Hecho | — |
| 1 | `firma_commits.md` | ✅ Evidencias en §8.1 y §11 | — |
| 2 | `proteccion-ramas.md` | ✅ Evidencias en §5 | — |
| 3 | `gitleaks.md` | ✅ Evidencias en §9 (incl. limpieza) | — |
| 4 | `github.md` | ✅ Evidencias en §5 | — |
| 5 | `semgrep.md` | ✅ Evidencias en §9 | — |

---

## 1. `firma_commits.md` — ✅ COMPLETADO

Evidencias documentadas en [`firma_commits.md`](firma_commits.md) §8.1 y §11. Capturas en `docs/git_docs/img/PPS_git/GPG/` y `docs/git_docs/img/GPG/GPG_created.png`.

<details>
<summary>Pasos originales (referencia)</summary>

### Pasos (≈10 min)

**1. Comprobar firma activa**

```bash
git config --global user.signingkey
git config --global commit.gpgsign
gpg --list-secret-keys --keyid-format=LONG
```

**2. Push Android y captura**

```bash
cd "$PPS_ANDROID"
git remote -v
git status
git log -1 --pretty=format:'%h %G? %s'   # %G? debe ser G

# Si hace falta un commit firmado nuevo:
# git commit --allow-empty -m "docs(PPS): evidencia firma GPG en remoto"

git push origin main
```

Navegador: `https://github.com/alejandroquinonesgamez/medical_register_apk/commits/main` → último commit → captura badge **Verified** → guardar como:

`docs/git_docs/img/PPS_git/GPG/verified_android.png`

**3. Push backend y captura**

```bash
cd "$PPS_BACKEND"
git log -1 --pretty=format:'%h %G? %s'
git push origin dev
```

`https://github.com/alejandroquinonesgamez/medical_register/commits/dev` → captura → `verified_appmedica.png`.

**4. Vigilant Mode (opcional)**

GitHub (cuenta de usuario) → **Settings** → **SSH and GPG keys** → activar *Flag unsigned commits as unverified* → captura `vigilant-mode.png`.

**5. Actualizar `firma_commits.md`**

En §8.1:

```markdown
![Commit Verified — Android](img/PPS_git/GPG/verified_android.png)
![Commit Verified — Backend](img/PPS_git/GPG/verified_appmedica.png)
```

Marcar fila 7 del §10 como ✅ e incluir hashes reales de los commits capturados.

</details>

---

## 2. `proteccion-ramas.md` — ✅ COMPLETADO

Evidencias en [`proteccion-ramas.md`](proteccion-ramas.md) §5. Capturas en `docs/git_docs/img/PPS_git/proteccion-ramas/`.

<details>
<summary>Pasos originales (referencia)</summary>

### Pasos (≈25–40 min)

**1. Backend: proteger `dev`**

1. Abrir: `https://github.com/alejandroquinonesgamez/medical_register/settings/branches`
2. **Add branch protection rule** (o *Add rule* / *ruleset* según la UI).
3. **Branch name pattern**: `dev`
4. Activar:
   - **Require a pull request before merging** → **Require approvals** = 1
   - **Require status checks to pass before merging**
   - **Require branches to be up to date before merging**
5. En *status checks*, tras un run de Actions en un PR, seleccionar jobs visibles (p. ej. `build` del workflow *Build and Deploy Sphinx Docs* en PR a `dev`).
6. Guardar → captura `proteccion-ramas/regla-backend-dev.png`

**2. Android: proteger `main`**

Mismo flujo en `https://github.com/alejandroquinonesgamez/medical_register_apk/settings/branches` con pattern `main`. Si no hay Actions aún, basta PR + approvals.

**3. Push directo bloqueado (Android)**

```bash
cd "$PPS_ANDROID"
git checkout main
git pull origin main
echo "" >> README.md
git add -A
git commit -m "chore(PPS): prueba push directo con rama protegida"
git push origin main 2>&1 | tee /tmp/push-protegido-android.txt
```

Esperado: error `GH006` / *protected branch*. Captura → `proteccion-ramas/push-rechazado-android.png`.

**4. Flujo correcto con PR (backend)**

```bash
cd "$PPS_BACKEND"
git checkout dev
git pull origin dev
git checkout -b pps/demo-branch-protection
# Cambio trivial en documentación:
echo "" >> docs/git_docs/PPS_git/proteccion-ramas.md
git add docs/git_docs/PPS_git/proteccion-ramas.md
git commit -m "docs(PPS): evidencia protección de ramas"
git push -u origin pps/demo-branch-protection
```

En GitHub: PR hacia `dev`. Capturas:

- `pr-bloqueado.png` (sin aprobación o checks pendientes)
- `pr-listo-merge.png` (checks verdes + aprobación)

Fusionar y borrar rama de demo.

**5. Actualizar `proteccion-ramas.md`**

Añadir sección **Evidencias (entrega)** al final (ver plantilla al final de este documento).

</details>

---

## 3. `gitleaks.md` — ✅ COMPLETADO (ver [`gitleaks.md`](gitleaks.md) §8–§9)

<details>
<summary>Pasos originales (referencia)</summary>

**Repo**: solo backend `medical_register` · rama de trabajo `dev` · PRs recomendados.

### Qué falta

| # | Evidencia | Captura / artefacto |
|---|-----------|---------------------|
| 1 | Workflow en CI | `.github/workflows/gitleaks.yml` en el repo |
| 2 | Action OK (sin secreto) | `$PPS_IMG/gitleaks/action-verde-setup.png` |
| 3 | Action **fallida** (con secreto de prueba) | `action-fallo.png` |
| 4 | Action OK tras limpiar | `action-ok-tras-limpieza.png` |
| 5 | Escaneo local | extracto en `gitleaks.md` (sin secretos) |
| 6 | Sección en el informe | `gitleaks.md` → **Evidencias (entrega)** |

### Paso 3.1 — Preparar entorno

```bash
export PPS_BACKEND="/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/Aplicación Médica"
export PPS_IMG="$PPS_BACKEND/docs/git_docs/img/PPS_git"
mkdir -p "$PPS_IMG/gitleaks"

cd "$PPS_BACKEND"
git checkout dev
git pull origin dev
git config commit.gpgsign false   # opcional: evitar passphrase en esta sesión
```

### Paso 3.2 — Crear workflow y subir (PR a `dev`)

Crear `.github/workflows/gitleaks.yml`:

```yaml
name: gitleaks

on:
  pull_request:
  push:
    branches: [main, dev]

jobs:
  scan:
    name: gitleaks
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

```bash
cd "$PPS_BACKEND"
git checkout -b pps/gitleaks-setup
git add .github/workflows/gitleaks.yml
git commit --no-gpg-sign -m "ci(PPS): añadir escaneo gitleaks en PR y push"
git push -u origin pps/gitleaks-setup
```

**En GitHub**: PR `pps/gitleaks-setup` → `dev` → **Actions** → job `gitleaks` en verde.

**Captura**: `action-verde-setup.png` (log o resumen “No leaks found”).

> Si `dev` está protegida, el merge del PR puede exigir aprobación + check `build`; espera ambos.

### Paso 3.3 — Demo: secreto que debe fallar

1. **Crear PAT de prueba** (cuenta GitHub): **Settings → Developer settings → Personal access tokens** → fine-grained o classic, **1 día**, permisos mínimos (p. ej. solo lectura de metadata).
2. Copia el token (`github_pat_...` o `ghp_...`).

```bash
cd "$PPS_BACKEND"
git checkout pps/gitleaks-setup
git pull origin pps/gitleaks-setup

mkdir -p docs/git_docs/PPS_git/_demo_gitleaks
# Sustituye por el PAT real de prueba (solo en local, no lo subas a chats):
printf 'github_pat_demo=%s\n' 'PEGA_AQUI_EL_PAT' > docs/git_docs/PPS_git/_demo_gitleaks/leak.txt

git add docs/git_docs/PPS_git/_demo_gitleaks/leak.txt
git status   # solo debe aparecer leak.txt
git commit --no-gpg-sign -m "test(PPS): secreto ficticio para demo gitleaks"
git push
```

**Captura**: Actions → run **rojo** → expandir paso `gitleaks` → ver archivo y regla → `action-fallo.png`.

### Paso 3.4 — Limpiar y run verde

```bash
cd "$PPS_BACKEND"
git rm -r docs/git_docs/PPS_git/_demo_gitleaks
git commit --no-gpg-sign -m "test(PPS): eliminar secreto de demo gitleaks"
git push
```

En GitHub: **revocar** el PAT de prueba. **Captura**: run verde → `action-ok-tras-limpieza.png`.

Fusionar el PR `pps/gitleaks-setup` a `dev` (sin la carpeta `_demo_gitleaks`).

### Paso 3.5 — Escaneo local

```bash
# Arch Linux:
sudo pacman -S gitleaks
# o: https://github.com/gitleaks/gitleaks/releases

cd "$PPS_BACKEND"
gitleaks detect --verbose 2>&1 | tee /tmp/gitleaks-local.txt
head -40 /tmp/gitleaks-local.txt
```

Copia un extracto **sin líneas con secretos** a `gitleaks.md` (apartado de uso local).

### Paso 3.6 — Cerrar `gitleaks.md`

Añadir sección **Evidencias (entrega)** (plantilla §6) con enlaces a las cuatro capturas y al PR. Ver ejemplo de rutas en §8 de este archivo.

</details>

---

## 4. `github.md` — ✅ COMPLETADO (ver [`github.md`](github.md) §3.5 y §5)

<details>
<summary>Pasos originales (referencia)</summary>

**Repo**: `medical_register` (backend). Puedes reutilizar el **mismo PAT de prueba** que en Gitleaks (crea otro si ya revocaste el anterior).

### Qué falta

| # | Evidencia | Captura |
|---|-----------|---------|
| 1 | Opciones activadas en el repo | `github/secret-scanning-on.png`, `github/push-protection-on.png` |
| 2 | Push bloqueado en cliente | `github/push-rejected.png` (+ opcional `/tmp/push-protection-reject.txt`) |
| 3 | Alerta + remediación (recomendado) | `alerta-abierta.png`, `alerta-cerrada.png` |
| 4 | Sección en el informe | `github.md` → **Evidencias (entrega)** |

### Paso 4.1 — Activar en GitHub (solo web)

Abre:

`https://github.com/alejandroquinonesgamez/medical_register/settings/security_analysis`

Activa (nombres según UI):

- **Secret scanning** (y *Secret scanning push protection* / **Push protection**)
- Si el repo es privado y no aparece: documenta en el MD que en plan Free puede estar limitado y que un admin de org lo habilitaría.

**Capturas** en `$PPS_IMG/github/`:

- Pantalla con Secret scanning **Enabled**
- Pantalla con Push protection **Enabled**

### Paso 4.2 — Probar bloqueo en `git push` (sin mergear secreto a `dev`)

```bash
cd "$PPS_BACKEND"
git checkout dev
git pull origin dev
git checkout -b pps/github-push-protection-demo

mkdir -p docs/git_docs/PPS_git/_demo_github
# PAT de prueba (formato que GitHub reconoce):
printf '%s\n' 'ghp_PEGA_AQUI_40_CARACTERES_DE_PAT_DE_PRUEBA' > docs/git_docs/PPS_git/_demo_github/leak.txt

git add docs/git_docs/PPS_git/_demo_github/leak.txt
git commit --no-gpg-sign -m "test(PPS): demo push protection"
git push -u origin pps/github-push-protection-demo 2>&1 | tee /tmp/push-protection-reject.txt
```

**Esperado**: rechazo con mensaje de secret scanning / push protection y URL de ayuda.

**Captura**: terminal → `push-rejected.png`.

Si el push **no** se bloquea:

- Comprueba que Push protection está activo en Settings.
- Usa un PAT **real** recién creado (no una cadena inventada).
- Documenta en `github.md` el comportamiento observado.

### Paso 4.3 — Alerta “en reposo” (si el bloqueo no impidió subir el secreto)

Solo si el paso 4.2 **subió** el fichero al remoto:

1. `https://github.com/alejandroquinonesgamez/medical_register/security/secret-scanning` → alerta abierta → **captura**
2. Revocar PAT en GitHub
3. `git rm -r docs/git_docs/PPS_git/_demo_github` + commit + push
4. Cerrar alerta: *Resolved as real secret* → **captura**

Si el push fue **bloqueado**, basta documentar el bloqueo; la alerta en reposo es opcional.

### Paso 4.4 — Cerrar `github.md`

Sección **Evidencias (entrega)** + párrafo breve de remediación (revocar token, no confiar en borrar commit sin rotar secreto).

Referencias:

- [Remediating a leaked secret](https://docs.github.com/es/code-security/tutorials/remediate-leaked-secrets/remediating-a-leaked-secret)
- [Enabling push protection](https://docs.github.com/en/code-security/how-tos/secure-your-secrets/prevent-future-leaks/enabling-push-protection-for-your-repository)

**PAT de prueba**: fine-grained con permisos mínimos (p. ej. Metadata read-only) o classic **sin scopes**, caducidad 1 día. Revocar tras la demo.

</details>

---

## 5. `semgrep.md` — ✅ COMPLETADO

**Repo**: backend · código bajo `app/` · reglas en `semgrep-rules/`.

### Estado evidencias

| # | Evidencia | Estado |
|---|-----------|--------|
| 1 | Escaneo `auto` en `app/` | ✅ `semgrep/scan-auto.png` |
| 2 | Contexto demo + comando OWASP | ✅ `semgrep/deteccion-vuln.png` |
| 3 | Detección con regla y línea | ✅ `semgrep/vuln-scan.png` |
| 4 | Regla propia | ✅ `semgrep-rules/no-flask-debug.yaml` |
| 5 | CI (PR + workflow) | ✅ `semgrep/action-verde.png` |
| 6 | Semgrep Cloud | ✅ `cloud-proyecto.png`, `cloud-proyecto2.png` |
| 7 | Informe | ✅ `semgrep.md` §9 |
| 8 | CI fallo con demo | ⏭ opcional (`action-fallo.png`) |

### Paso 5.1 — Instalar y escaneo base

```bash
python3 -m pip install --user semgrep
export PATH="$HOME/.local/bin:$PATH"
semgrep --version

cd "$PPS_BACKEND"
semgrep scan --config auto app/ 2>&1 | tee /tmp/semgrep-auto.txt
```

**Captura**: primeras líneas con resumen de findings → `semgrep/scan-auto.png`.

### Paso 5.2 — Vulnerabilidad de prueba (rama aparte)

```bash
cd "$PPS_BACKEND"
git checkout dev
git pull origin dev
git checkout -b pps/semgrep-vuln-demo
```

Crear `app/_semgrep_demo_vuln.py` (la SQL debe llegar a `execute()`, no solo a un `return`):

```python
import sqlite3

def buscar_usuario(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute("SELECT * FROM users WHERE id = " + user_id)
```

> Si el escaneo da **0 findings**, el patrón solo construía la cadena sin ejecutarla; Semgrep prioriza flujos hacia la BD (`execute`, f-strings en `execute`, etc.).

```bash
semgrep scan --config "p/python" --config "p/owasp-top-ten" app/_semgrep_demo_vuln.py 2>&1 | tee /tmp/semgrep-vuln.txt
```

**Capturas**: contexto del fichero → `deteccion-vuln.png`; finding con regla y línea (`--config auto` tras `conn.execute`) → `vuln-scan.png`.

### Paso 5.3 — Regla personalizada

```bash
mkdir -p "$PPS_BACKEND/semgrep-rules"
```

`semgrep-rules/no-flask-debug.yaml`:

```yaml
rules:
  - id: flask-debug-true
    pattern: app.run(..., debug=True, ...)
    message: "No usar debug=True en código fusionado."
    languages: [python]
    severity: ERROR
```

```bash
semgrep scan --config semgrep-rules/no-flask-debug.yaml app/
```

Commit **solo** reglas + fichero demo (luego borrarás el demo):

```bash
cd "$PPS_BACKEND"
git add semgrep-rules/ app/_semgrep_demo_vuln.py
git commit --no-gpg-sign -m "docs(PPS): regla semgrep y demo SQLi para evidencia"
git push -u origin pps/semgrep-vuln-demo
```

Abrir PR a `dev`. **Antes de fusionar**:

```bash
git rm app/_semgrep_demo_vuln.py
git commit --no-gpg-sign -m "docs(PPS): quitar fichero demo semgrep antes de merge"
git push
```

Dejar en `dev` solo `semgrep-rules/` (sin vuln en producción).

### Paso 5.4 — CI opcional (sin `SEMGREP_APP_TOKEN`)

`.github/workflows/semgrep.yml`:

```yaml
name: Semgrep
on:
  pull_request:
  push:
    branches: [dev]
jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep
    steps:
      - uses: actions/checkout@v4
      - run: semgrep scan --config auto app/ --error
```

PR → captura run (verde o fallo documentado). Si hay muchos hallazgos en `tests/`, crea `.semgrepignore` y explícalo en el MD.

### Paso 5.5 — Semgrep Cloud (opcional)

1. `https://semgrep.dev` → login con GitHub  
2. Añadir proyecto `medical_register`  
3. Captura del dashboard → `cloud-proyecto.png`

### Paso 5.6 — Cerrar `semgrep.md`

Sección **Evidencias (entrega)** con tabla y rutas `../img/PPS_git/semgrep/...`.

---

## 6. Plantilla «Evidencias (entrega)» para cada `.md`

Copiar al final de `firma_commits.md`, `github.md`, `gitleaks.md`, `proteccion-ramas.md` y `semgrep.md`:

```markdown
---

## Evidencias (entrega)

| # | Qué demuestra | Archivo / enlace |
|---|---------------|------------------|
| 1 | … | `docs/git_docs/img/PPS_git/...` |
| 2 | … | PR #NN en `medical_register` |

**Fecha**: YYYY-MM-DD  
**Repos**: `medical_register_apk` (rama `main`), `medical_register` (rama `dev`)
```

Commit de documentación en el backend:

```bash
cd "$PPS_BACKEND"
git add docs/git_docs/
git commit -m "docs(PPS): evidencias ejercicios Git (firma, ramas, gitleaks, github, semgrep)"
git push origin dev
```

---

## 7. Resumen: qué falta por documento

| Documento | Estado | Falta principal | Tiempo aprox. |
|-----------|--------|-----------------|---------------|
| **gitignore.md** | ✅ Hecho | — | — |
| **firma_commits.md** | ✅ Hecho | — | — |
| **proteccion-ramas.md** | ✅ Hecho | — | — |
| **gitleaks.md** | ✅ | — | — |
| **github.md** | ✅ | — | — |
| **semgrep.md** | ✅ | — | — |

**Bloque PPS Git (documentación)**: apartados 0–5 **cerrados** para entrega (§9).

---

## 8. Estructura sugerida de capturas

```
docs/git_docs/img/PPS_git/
├── GPG/                         # ✅ apartado 1
│   ├── verified_android.png
│   ├── verified_appmedica.png
│   └── vigilant-mode.png
├── proteccion-ramas/            # ✅ apartado 2
│   ├── regla-backend-dev1.png … dev3.png
│   ├── pr-checks-build.png
│   ├── push-rechazado-android.png
│   └── push-aceptado-android.png
├── gitleaks/                    # ✅ apartado 3
│   ├── action-verde-setup.png
│   ├── action-verde-setup-detail.png
│   ├── action-fallo.png
│   └── action-ok-tras-limpieza.png
├── github/                      # ✅ apartado 4
│   ├── options-enabled.png
│   └── push-rejected.png
└── semgrep/                     # ✅ apartado 5
    ├── scan-auto.png
    ├── deteccion-vuln.png
    ├── vuln-scan.png
    ├── action-verde.png
    ├── cloud-proyecto.png
    └── cloud-proyecto2.png
```

(`GPG_created.png` sigue en `docs/git_docs/img/GPG/`.)

> **Seguridad**: nunca subas tokens reales sin revocarlos. Las carpetas `_demo_gitleaks` y `_demo_github` deben eliminarse antes de fusionar a `dev`/`main`.

---

## 9. Cierre de entrega — estado final

### 9.0. Estado actual (mínimo exigible ya cubierto)

| Documento | Sección evidencias | Capturas en disco |
|-----------|-------------------|-------------------|
| `gitignore.md` | Sin sección gráfica (contenido de `.gitignore`) | — |
| `firma_commits.md` | §11 | GPG ×4 + `img/GPG/GPG_created.png` |
| `proteccion-ramas.md` | §5 | 7 PNG en `proteccion-ramas/` |
| `gitleaks.md` | §9 | 4 PNG en `gitleaks/` |
| `github.md` | §5 | 2 PNG en `github/` |
| `semgrep.md` | §9 | 6 PNG en `semgrep/` |

Capturas **no** exigidas explícitamente en los HTML y **omitidas** a propósito (sin dejar tareas pendientes en los informes):

| Captura omitida | Motivo |
|----------------|--------|
| `github/alerta-abierta.png`, `alerta-cerrada.png` | Push bloqueado (GH013); PAT de prueba caducado/revocado; no hay alerta en reposo |
| `proteccion-ramas/pr-bloqueado.png`, `pr-listo-merge.png` | Redundante con regla + `pr-checks-build` + push rechazado |
| `semgrep/action-fallo.png` | Redundante con `vuln-scan.png` + `action-verde.png` |

Captura **añadida** tras el ciclo gitleaks: `gitleaks/action-ok-tras-limpieza.png` (integrada en `gitleaks.md` §9).

<details>
<summary>Guía histórica: cómo obtener capturas opcionales (solo referencia)</summary>

**Preparación común** (ejecutar una vez por sesión):

```bash
export PPS_BACKEND="/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/Aplicación Médica"
export PPS_ANDROID="/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/medical_register_android"
export PPS_IMG="$PPS_BACKEND/docs/git_docs/img/PPS_git"
mkdir -p "$PPS_IMG"/{gitleaks,github,proteccion-ramas,semgrep}
```

**Qué debe verse en cada captura** (regla general):

- Título del repo `alejandroquinonesgamez/medical_register` (o `medical_register_apk` si aplica).
- Nombre de la rama o del PR.
- Estado claro: ✅ verde, ❌ rojo, “Merging is blocked”, mensaje `GH013`, etc.
- Sin tokens completos visibles (tapa con recuadro si hace falta).

---

### 9.1. Gitleaks — `action-ok-tras-limpieza.png` (opcional)

**Objetivo**: demostrar el ciclo completo *fallo → limpieza → CI verde* (complementa `action-fallo.png`).

**Requisitos previos**:

- Rama `pps/gitleaks-setup` (o la que usaste) con `.github/workflows/gitleaks.yml` ya en GitHub.
- Haber hecho antes el paso con secreto en `_demo_gitleaks/leak.txt` y run rojo (`action-fallo.png`). Si ya borraste la carpeta, puedes saltar directamente al paso 3.

**Paso 1 — Confirmar rama y remoto**

```bash
cd "$PPS_BACKEND"
git fetch origin
git checkout pps/gitleaks-setup   # o tu rama gitleaks
git pull origin pps/gitleaks-setup
git remote -v   # origin → git@github.com:alejandroquinonesgamez/medical_register.git
```

**Paso 2 — Eliminar el secreto de demo del árbol Git**

```bash
cd "$PPS_BACKEND"
# Si la carpeta existe:
git rm -r docs/git_docs/PPS_git/_demo_gitleaks

# Si Git dice que no existe pero sigue en disco:
rm -rf docs/git_docs/PPS_git/_demo_gitleaks
git status

git commit --no-gpg-sign -m "test(PPS): eliminar secreto de demo gitleaks"
```

**Paso 3 — Revocar el PAT de prueba**

1. Abre: `https://github.com/settings/tokens` (o fine-grained tokens).
2. Localiza el token usado en la demo → **Delete** / **Revoke**.
3. No hace falta captura; basta mencionarlo en `gitleaks.md`.

**Paso 4 — Push y esperar Actions**

```bash
git push origin pps/gitleaks-setup
```

1. Abre: `https://github.com/alejandroquinonesgamez/medical_register/actions`
2. Filtro workflow: **gitleaks**
3. Entra en el run más reciente del push (debe ser **verde**).
4. Expande el job **gitleaks** → paso del escaneo → texto tipo *No leaks detected* o *0 leaks*.

**Paso 5 — Captura**

- Guarda como: `$PPS_IMG/gitleaks/action-ok-tras-limpieza.png`
- Incluye: nombre del workflow, commit message de limpieza, check verde.

**Paso 6 — Enlazar en el informe**

En `gitleaks.md` §9, fila 4, añade la imagen:

```markdown
![Run gitleaks tras eliminar demo](../img/PPS_git/gitleaks/action-ok-tras-limpieza.png)
```

**Problemas frecuentes**

| Síntoma | Qué hacer |
|---------|-----------|
| Sigue en rojo tras `git rm` | Comprueba que el commit de limpieza está en la rama del PR; mira el log: a veces el secreto quedó en un commit anterior del PR (rebase o nuevo commit que borre el fichero en todo el diff). |
| No se lanza Actions | El workflow debe existir en la rama; revisa `.github/workflows/gitleaks.yml` y que el push no sea solo a una rama sin workflow. |
| `dev` no deja mergear | Normal si la rama está protegida; la captura del run verde en la rama de PR es suficiente. |

---

### 9.2. GitHub Secret scanning — `alerta-abierta.png` y `alerta-cerrada.png` (opcional)

**Objetivo**: mostrar el flujo de alerta en la UI de GitHub (además del `push-rejected.png` en terminal).

**Importante**: si **Push protection** bloqueó el `git push` (`GH013`), el secreto **no** entró en el remoto y **a menudo no hay alerta** en *Secret scanning*. En ese caso escribe en `github.md`:

> *Push protection impidió la subida; no se generó alerta en reposo. Evidencia principal: `push-rejected.png`.*

Solo sigue esta sección si quieres la alerta o si en algún intento el push **sí** subió el fichero.

#### Caso A — Tienes push bloqueado (tu situación habitual)

**Opción A1 — Documentar sin captura** (válido): una frase en `github.md` §5 (ya hay nota).

**Opción A2 — Forzar alerta en reposo** (solo si aceptas rotar/revocar PAT después):

1. Desactiva temporalmente **Push protection** (no recomendado en repo real con datos sensibles):
   - `https://github.com/alejandroquinonesgamez/medical_register/settings/security_analysis`
   - Desmarca *Push protection* → Save.
2. Repite push con PAT de prueba en rama demo (ver §4 paso 4.2 en el `<details>` de esta guía).
3. Si el push **entra**, ve al paso **Caso B** abajo.
4. **Vuelve a activar** Push protection y revoca el PAT.

#### Caso B — Hay alerta en Security (push subió o escaneo histórico)

**Paso 1 — Abrir listado de alertas**

URL directa:

`https://github.com/alejandroquinonesgamez/medical_register/security/secret-scanning`

(O: repo → pestaña **Security** → **Secret scanning** en el menú lateral.)

**Paso 2 — Captura `alerta-abierta.png`**

1. Clic en la alerta del PAT (tipo *GitHub personal access token*).
2. Debe verse: estado **Open**, ruta del fichero (`leak.txt` o similar), rama, recomendación de revocar.
3. **Tapa** el valor del secreto si aparece.
4. Guarda en `$PPS_IMG/github/alerta-abierta.png`.

**Paso 3 — Remediación**

1. Revoca el PAT: `https://github.com/settings/tokens`
2. En local:

```bash
cd "$PPS_BACKEND"
git checkout pps/github-push-protection-demo   # tu rama demo
git rm -r docs/git_docs/PPS_git/_demo_github
git commit --no-gpg-sign -m "test(PPS): quitar leak demo github"
git push
```

3. En la alerta de GitHub: **Close alert** → motivo *Revoked* o *Used in tests* según UI → confirmar.

**Paso 4 — Captura `alerta-cerrada.png`**

- Misma alerta en estado **Closed** / **Resolved**.
- Guarda en `$PPS_IMG/github/alerta-cerrada.png`.

**Paso 5 — Actualizar `github.md`**

Añade filas e imágenes en §5 Evidencias.

**Problemas frecuentes**

| Síntoma | Qué hacer |
|---------|-----------|
| Lista vacía | Normal con push bloqueado; no insistas; usa `push-rejected.png`. |
| Alerta en otro repo | Comprueba que estás en `medical_register`, no en `medical_register_apk`. |
| No deja cerrar alerta | Revoca primero el token; espera unos minutos y recarga. |

---

### 9.3. Protección de ramas — `pr-bloqueado.png` y `pr-listo-merge.png` (opcional)

**Objetivo**: dos estados del **mismo PR** hacia `dev` en el backend: bloqueado vs listo para fusionar.

**Requisitos**: regla en `dev` activa (PR + 1 approval + check `build`) — ya documentada en `regla-backend-dev*.png`.

**Paso 1 — Crear rama y PR de prueba**

```bash
cd "$PPS_BACKEND"
git fetch origin
git checkout dev
git pull origin dev
git checkout -b pps/demo-pr-estados-$(date +%Y%m%d)

# Cambio mínimo solo en documentación (no tocar app/):
echo "<!-- demo PR estados PPS -->" >> docs/git_docs/PPS_git/proteccion-ramas.md

git add docs/git_docs/PPS_git/proteccion-ramas.md
git commit --no-gpg-sign -m "docs(PPS): demo estados PR (bloqueado vs listo)"
git push -u origin HEAD
```

**Paso 2 — Abrir el Pull Request**

1. GitHub sugiere enlace al crear PR; o abre:
   `https://github.com/alejandroquinonesgamez/medical_register/compare/dev...pps/demo-pr-estados-XXXX`
2. Base: **`dev`** ← Compare: tu rama.
3. Título ejemplo: `docs(PPS): demo estados PR protección ramas`
4. **Create pull request** (no fusiones aún).

**Paso 3 — Captura `pr-bloqueado.png` (inmediatamente)**

En la página del PR, sin aprobar ni esperar a que terminen todos los checks:

1. Baja a la caja de merge: debe decir **Merging is blocked** / *Merge blocked*.
2. Motivos típicos visibles:
   - *Review required* / *At least 1 approving review*
   - *Required status check* `build` *pending* o *expected*
   - *This branch is out-of-date* (si aplica)
3. Pestaña **Checks**: si `build` aún corre, mejor (muestra *pending*).
4. Captura **ancha** que incluya título del PR, rama base `dev` y el mensaje de bloqueo.
5. Guarda: `$PPS_IMG/proteccion-ramas/pr-bloqueado.png`.

**Paso 4 — Esperar check `build`**

1. Pestaña **Checks** → workflow *Build and Deploy Sphinx Docs* (o el que use tu repo).
2. Espera hasta que **build** esté en ✅ (puede tardar varios minutos).
3. Si falla, entra al log, corrige o documenta; para la captura “listo” necesitas `build` verde.

**Paso 5 — Aprobación del PR**

Como eres autor y solo hay un colaborador, usa una de estas vías:

- **Cuenta segunda** / compañero del proyecto: *Files changed* → **Review changes** → **Approve**.
- **Bypass** (solo si tu rol en GitHub lo permite y la práctica lo admite): Settings de la org o regla con excepción — si no, pide review a Adrián u otro miembro.

Sin al menos **1 approving review**, no podrás hacer la captura “listo”.

**Paso 6 — Captura `pr-listo-merge.png`**

Cuando:

- Check **`build`** ✅
- **Approved** ✅
- Caja de merge: **Ready to merge** / botón verde **Merge pull request** habilitado

Guarda: `$PPS_IMG/proteccion-ramas/pr-listo-merge.png`.

**Paso 7 — Cerrar sin dejar basura (recomendado)**

```bash
# En GitHub: Merge PR (squash o merge commit) o cierra sin merge
cd "$PPS_BACKEND"
git checkout dev
git pull origin dev
git push origin --delete pps/demo-pr-estados-XXXX
git branch -d pps/demo-pr-estados-XXXX
```

Opcional: revertir la línea HTML añadida en un commit posterior si no quieres ese comentario en el MD.

**Paso 8 — Actualizar `proteccion-ramas.md`**

En §5.4, cambia fila 4 a ✅ y añade:

```markdown
![PR bloqueado: review y/o checks pendientes](../img/PPS_git/proteccion-ramas/pr-bloqueado.png)
![PR listo para merge: build + aprobación](../img/PPS_git/proteccion-ramas/pr-listo-merge.png)
```

**Problemas frecuentes**

| Síntoma | Qué hacer |
|---------|-----------|
| No aparece `build` en reglas | Haz un PR primero para que GitHub “vea” el check; luego edita la regla de `dev` y añade `build` manualmente. |
| Siempre bloqueado | Falta approval o `build` rojo; no captures “listo” hasta ambos verdes. |
| Eres solo en el repo | GitHub no deja auto-aprobar por defecto; coordina review o documenta limitación en el MD. |

---

### 9.4. Semgrep — `action-fallo.png` (opcional)

**Objetivo**: run de GitHub Actions en **rojo** por detección Semgrep (además de `vuln-scan.png` en local).

**Contexto**: el PR `pps/semgrep-vuln-demo` #1 pudo salir **verde** porque el step *OWASP en fichero demo* no siempre falla con `--error` si el registro no reporta findings en ese fichero. La evidencia local (`vuln-scan.png` con `--config auto`) ya es válida.

#### Opción recomendada — Forzar fallo con `--config auto` en CI (rama temporal)

**Paso 1 — Rama con demo aún presente**

```bash
cd "$PPS_BACKEND"
git checkout pps/semgrep-vuln-demo
git pull origin pps/semgrep-vuln-demo
ls app/_semgrep_demo_vuln.py   # debe existir (conn.execute + concatenación)
```

**Paso 2 — Editar workflow solo para la demo**

En `.github/workflows/semgrep.yml`, en el step *OWASP en fichero demo*, sustituye el `run` por:

```yaml
        run: semgrep scan --config auto app/_semgrep_demo_vuln.py --error
```

(Esto coincide con la detección que ya viste en local.)

```bash
git add .github/workflows/semgrep.yml
git commit --no-gpg-sign -m "ci(PPS): forzar semgrep auto en demo para evidencia CI roja"
git push
```

**Paso 3 — Captura**

1. `https://github.com/alejandroquinonesgamez/medical_register/actions`
2. Workflow **Semgrep** → run **fallido** del PR.
3. Expande job **semgrep** → step que falló → log con regla `sqlalchemy-execute-raw-query` o similar.
4. Guarda: `$PPS_IMG/semgrep/action-fallo.png`.

**Paso 4 — Restaurar workflow “de producción”**

Deja el step OWASP como estaba (o elimina el step demo antes de fusionar a `dev`):

```bash
git checkout .github/workflows/semgrep.yml   # si guardaste copia
# o edita manualmente al contenido con p/python + p/owasp-top-ten
git commit --no-gpg-sign -m "ci(PPS): restaurar workflow semgrep tras captura"
git push
```

**Paso 5 — Quitar fichero demo antes de merge**

```bash
git rm app/_semgrep_demo_vuln.py
git commit --no-gpg-sign -m "docs(PPS): quitar demo semgrep antes de merge"
git push
```

**Alternativa sin tocar YAML**: no hagas `action-fallo.png`; en `semgrep.md` §9 fila 8 indica: *CI verde en PR #1; fallo documentado en CLI (`vuln-scan.png`).*

---

### 9.5. Limpieza obligatoria antes de entregar / fusionar

Checklist ejecutable:

```bash
cd "$PPS_BACKEND"
git status
```

| # | Acción | Comando / enlace |
|---|--------|------------------|
| 1 | Quitar demo Semgrep | `git rm -f app/_semgrep_demo_vuln.py` (si sigue en la rama) |
| 2 | Quitar demos secretos | `git rm -rf docs/git_docs/PPS_git/_demo_gitleaks docs/git_docs/PPS_git/_demo_github` |
| 3 | Revocar PATs de prueba | `https://github.com/settings/tokens` |
| 4 | Comprobar que no hay secretos en el diff | `git diff dev --name-only` antes del commit final |
| 5 | Commit solo documentación PPS | `git add docs/git_docs/ .github/workflows/semgrep-rules/ semgrep-rules/ .semgrepignore` — **no** `git add -A` si tienes WIP (`play_integrity`, etc.) |
| 6 | Push y PR a `dev` | Verificar checks: `build`, `gitleaks`, `semgrep` según workflows activos |
| 7 | Fusionar cuando `dev` lo permita | PR aprobado + checks verdes |

**Mensaje de commit sugerido** (un solo PR de documentación):

```bash
git commit --no-gpg-sign -m "docs(PPS): evidencias Git (gitleaks, github, semgrep, ramas, GPG)"
```

**Android** (`medical_register_apk`): no mezcles en el mismo commit del backend; las capturas GPG/protección Android ya están en sus rutas bajo `docs/git_docs/img/PPS_git/`.

</details>

---

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

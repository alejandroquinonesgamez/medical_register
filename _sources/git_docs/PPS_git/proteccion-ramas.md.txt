# Protección de ramas (Branch protection rules)

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

**Enunciado**: `docs/git_docs/PPS_git/proteccion-ramas.html` (Fernando Raya, 2026-04-20)

> **Nota (evidencia)**: en `medical_register`, la rama `dev` exige el *status check* `build` (workflow *Build and Deploy Sphinx Docs*) antes de fusionar.

---

## Repositorios de este trabajo (espacio de trabajo PPS)

| Proyecto | Ruta local | Remoto `origin` (SSH) | Rama habitual |
|---|---|---|---|
| Cliente Android | `/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/medical_register_android` | `git@github.com:alejandroquinonesgamez/medical_register_apk.git` | `main` |
| Backend | `/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/Aplicación Médica` | `git@github.com:alejandroquinonesgamez/medical_register.git` | `dev` |

Las reglas de protección se configuran **en GitHub**, en el repositorio remoto que corresponda (`medical_register_apk` y/o `medical_register`). El ejemplo de push directo bloqueado (§3.3) debe usar la **rama que hayáis protegido** (`main` en Android, `dev` o `main` en el backend).

```bash
# Ejemplo: push directo a main en el cliente Android (debe fallar si main está protegida)
cd "/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/medical_register_android"
git push origin main
```

---

## 1. Introducción

Las **reglas de protección de ramas** en GitHub (o equivalentes en GitLab: *Protected branches*) imponen restricciones sobre ramas críticas (`main`, `master`, `release/*`, etc.). El enunciado pide activar **revisiones obligatorias** y **comprobaciones de estado** (*status checks*) en la rama principal, y documentar el comportamiento **sin** necesidad de capturar datos sensibles del repositorio.

Documentación oficial:

- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)  
- [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule)

---

## 2. Características (resumen del enunciado)

| Característica | Efecto |
|---|---|
| **Evitar modificaciones directas** | Impide `git push` directo a la rama protegida; los cambios entran vía **Pull Request** (o *merge queue* si está habilitada). |
| **Revisiones obligatorias** | Exige uno o más **aprobaciones** de revisores antes de fusionar (*code review*). |
| **Status checks** | Exige que jobs de CI (tests, Gitleaks, build de docs, etc.) finalicen en **éxito** antes de habilitar el merge. |

---

## 3. Actividad: configuración recomendada en GitHub

Ruta típica en el repositorio:

**Settings → Branches → Branch protection rules → Add rule** (o *Add branch protection rule*).

### 3.1. Ámbito de la regla

- **Branch name pattern**: la rama que uséis como principal en **ese** remoto. En **`medical_register_apk`** suele ser `main`; en **`medical_register`** (backend) el trabajo cotidiano suele estar en `dev` (ajusta el patrón a `dev` si protegéis esa rama en lugar de `main`).

### 3.2. Opciones mínimas alineadas con el enunciado

1. **Require a pull request before merging**  
   - Activar **Require approvals** (al menos **1** en equipos pequeños; más en producción).  
   - Opcional: *Dismiss stale pull request approvals when new commits are pushed*.

2. **Require status checks to pass before merging**  
   - Activar **Require branches to be up to date before merging** (recomendado).  
   - En el buscador de checks, seleccionar los jobs que ya existan en el repo, por ejemplo los definidos en `.github/workflows/coverage.yml` y `build-docs.yml` (los nombres exactos aparecen en la pestaña **Actions** tras una ejecución).

3. **Do not allow bypassing the above settings**  
   - Desactivar bypass para administradores si la política del curso lo exige (así la regla aplica a todos).

Opciones adicionales habituales en PPS:

- **Require conversation resolution before merging** (cerrar todos los hilos de comentario).  
- **Require linear history** (evita merge commits si se prefiere *rebase*/*squash*).  
- **Lock branch** solo en situaciones excepcionales (congelación de release).

### 3.3. Cómo documentar el funcionamiento

1. **Intento de push directo** (debe fallar). Sustituye rama y ruta según el repo que estés probando (`main` en Android, `dev` en el backend si es la rama protegida):

   ```bash
   cd "/home/alejandro/DriveLocal/alejandro/Ciberseguridad/PPS - Puesta a Producción Segura/medical_register_android"
   git checkout main
   git pull origin main
   echo "# test" >> README.md
   git commit -am "chore: demo proteccion rama"
   git push origin main
   ```

   Resultado esperado: `remote: error: GH006: Protected branch update failed...` o mensaje equivalente de GitHub indicando que la rama está protegida.

2. **Flujo correcto**: crear rama, abrir PR hacia la rama protegida, esperar checks verdes y aprobación, fusionar desde la UI (o con *merge queue* si aplica).

3. **Evidencias gráficas**: ver §5 (capturas en `docs/git_docs/img/PPS_git/proteccion-ramas/`).

---

## 4. Relación con otros ejercicios PPS

- **Gitleaks / Semgrep**: si sus workflows publican checks con nombre estable, pueden formar parte de los *status checks* obligatorios.  
- **GitHub Secret scanning / Push protection**: son políticas a nivel de código y seguridad, no sustituyen la revisión humana ni los tests.

---

## 5. Evidencias (entrega) — Apartado 2: protección de ramas

Material gráfico del ejercicio, almacenado en `docs/git_docs/img/PPS_git/proteccion-ramas/`.

### 5.1. Regla de protección en `dev` (`medical_register`)

Configuración en **Settings → Branches** del backend: PR obligatorio, aprobaciones, *status checks* y check **`build`** (*Build and Deploy Sphinx Docs*).

| Captura | Contenido |
|---------|-----------|
| `regla-backend-dev1.png` | Vista general de la regla / opciones de protección |
| `regla-backend-dev2.png` | Detalle de revisiones y comprobaciones |
| `regla-backend-dev3.png` | *Status checks* requeridos (incl. `build`) |

![Regla de protección en dev (1/3)](../img/PPS_git/proteccion-ramas/regla-backend-dev1.png)

![Regla de protección en dev (2/3)](../img/PPS_git/proteccion-ramas/regla-backend-dev2.png)

![Regla de protección en dev (3/3)](../img/PPS_git/proteccion-ramas/regla-backend-dev3.png)

### 5.2. Status check `build` en Pull Request

Pull Request hacia la rama **`dev`**: el workflow de documentación ejecuta el job **`build`** y aparece en la sección **Checks** del PR.

![Checks del PR: job build en verde](../img/PPS_git/proteccion-ramas/pr-checks-build.png)

### 5.3. Push directo a rama protegida (`medical_register_apk` · `main`)

Intento de `git push origin main` sin pasar por PR cuando la rama **`main`** está protegida: GitHub rechaza la actualización.

![Push a main rechazado por rama protegida](../img/PPS_git/proteccion-ramas/push-rechazado-android.png)

> **Nota**: si en algún momento el push directo a `main` fue aceptado (p. ej. antes de activar la regla o con permisos de bypass), puede quedar constancia en `push-aceptado-android.png` como contraste; la evidencia principal del control es el **rechazo** una vez activada la protección.

![Push a main aceptado (referencia / antes de protección o sin regla)](../img/PPS_git/proteccion-ramas/push-aceptado-android.png)

### 5.4. Resumen de hitos

| # | Hito | Estado | Captura |
|---|------|--------|---------|
| 1 | Regla en `dev` con PR + approvals + check `build` | ✅ | `regla-backend-dev1.png` … `regla-backend-dev3.png` |
| 2 | Check `build` en PR a `dev` | ✅ | `pr-checks-build.png` |
| 3 | Push directo a `main` (Android) bloqueado | ✅ | `push-rechazado-android.png` |
| 4 | PR bloqueado / listo para merge (capturas dedicadas) | No incluido | La evidencia del enunciado queda cubierta con la regla en `dev` (§5.1), el check **`build`** en PR (`pr-checks-build.png`) y el push directo bloqueado en Android (`push-rechazado-android.png`). |

**Guía operativa**: [`pasos.md`](pasos.md) §2.

---

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

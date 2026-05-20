# Informe — Ansible (Docker en VM Proxmox, Aplicación Médica)

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

---

## Conformidad con la entrega (PPS)

Este paquete cumple lo pedido para la parte **Ansible** de la práctica:

| Requisito | Dónde se cubre en este informe |
|---|---|
| **Proyecto Ansible** que configura la **VM** (Docker, Compose, despliegue de la app) | §1.2 (playbook y roles), §2 (qué se despliega), código en **`ansible/`** (`site.yml`, `roles/`, etc.). |
| **Documentación** que demuestre el **despliegue correcto** | §2.2, §4 y §7 (capturas: ping, playbook, contenedores, HTTP **200**, navegador en **:5001**). Las figuras enlazan a imágenes en GitHub (`raw.githubusercontent.com`, rama `dev`). |
| **Coordinación con Terraform** | §5: la VM se crea con Terraform; este módulo aprovisiona el stack en la misma máquina. |

El aprovisionamiento de la **VM en Proxmox** se describe en el **[Informe Terraform](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/Informe.md)**.

---

## 1. Introducción

Este documento describe el **módulo Ansible** en la carpeta **`ansible/`** del paquete
de entrega, que configura la **VM ya creada por Terraform** (Proxmox): instala
**Docker Engine** y **Compose v2**, sincroniza el repositorio **Aplicación Médica** en
la VM y ejecuta **`docker compose up`** según el `docker-compose.yml` de la raíz del
repositorio.

A continuación se detalla **qué hace cada rol y cada fichero relevante**, cómo se
controlan los **perfiles** de Compose (`medical_compose_profiles`), qué servicios quedan
en ejecución y cómo se validó el despliegue.

### 1.1. Qué es Ansible (resumen operativo)

Ansible aplica **playbooks** contra inventarios de hosts usando **módulos**
idempotentes (apt, file, template, command, etc.). No hace falta instalar un agente
en la VM: solo **SSH** y Python en el remoto (el intérprete se descubre al hacer
*gathering facts*).

### 1.2. Ficheros y roles del módulo

| Ruta / elemento | Función |
|---|---|
| `site.yml` | Play único: `hosts: medical`, `become: true`, roles **`docker`** y **`medical_compose`** en ese orden. |
| `inventory.ini` | Inventario del host: grupo `[medical]` con `ansible_host`, `ansible_user`, `ansible_ssh_private_key_file`. |
| `inventory.ini.example` | Plantilla mínima de inventario. |
| `ansible.cfg` | Ajustes del proyecto (véase **1.3**). |
| `requirements.yml` | Declara la colección **`ansible.posix`** (necesaria para `synchronize`). |
| `extra_vars.example.yml` | Plantilla: solo **`medical_app_source`** (ruta al repo). |
| `extra_vars.full.example.yml` | Plantilla **despliegue completo**: `medical_app_source` + **`medical_compose_profiles: [defectdojo]`**. |
| `roles/docker/tasks/main.yml` | Instalación de Docker CE y plugin Compose v2 desde el repo oficial de Docker para Debian. |
| `roles/medical_compose/` | Sincronización del código, red `proxy-network`, `.env`, script shell generado y ejecución de Compose. |

> ⚠️ **Inconveniente**: el playbook depende de **red** en la VM (`apt`, `get_url`,
> pulls de imágenes, `pip` dentro del build de `web`). En redes filtradas pueden
> aparecer **timeouts**; el rol `docker` incluye omisión condicional de la GPG y
> **reintentos** en la descarga cuando aplica.

### 1.3. Contenido de `ansible.cfg`

| Sección / clave | Valor | Efecto |
|---|---|---|
| `[defaults]` `inventory` | `inventory.ini` | Sin `-i` en la línea de comandos, se usa ese fichero por defecto. |
| `[defaults]` `host_key_checking` | `false` | No bloquea el primer SSH por huella desconocida (adecuado en **laboratorio**; en producción convendría `true` y `known_hosts` gestionado). |
| `[defaults]` `retry_files_enabled` | `false` | No deja `.retry` en fallos. |
| `[defaults]` `command_warnings` | `false` | Reduce avisos ruidosos de comandos shell. |
| `[privilege_escalation]` `become` | `true` | Las tareas que lo requieran usan `sudo` por defecto (el playbook ya pone `become: true`). |

### 1.4. Valores por defecto del rol `medical_compose` (`defaults/main.yml`)

| Variable | Valor por defecto | Significado |
|---|---|---|
| `medical_app_deploy_path` | `/opt/aplicacion-medica` | Directorio en la VM donde vive una copia del repo. |
| `medical_compose_project_name` | `medical_register` | `COMPOSE_PROJECT_NAME` (coherente con `docker-compose.env.example`). |
| `medical_compose_profiles` | `[]` | Lista de **`--profile`** de Compose. **Vacía** ⇒ solo servicios **sin** cláusula `profiles:` (**`web`** + **`waf`**). DefectDojo requiere **`[defectdojo]`** (véase §2.5). |
| `medical_flask_env` | `production` | Inyectado en `.env` vía `blockinfile` (bloque Ansible). |
| `medical_app_supervisor` | `"0"` | Inyectado en `.env`; desactiva el supervisor de tráfico/DB en servidor (coherente con comentarios del `docker-compose.yml`). |

---

## 2. Qué se despliega con Ansible y de qué manera

**Resumen — despliegue completo (PPS):** con **`deployment_mode = "full"`** en Terraform
la VM queda dimensionada para **DefectDojo** además de **waf** y **web**. En Ansible,
el perfil **`defectdojo`** se activa con **`medical_compose_profiles: [defectdojo]`**
(plantilla [`extra_vars.full.example.yml`](../extra_vars.full.example.yml)). En este
informe se documenta el despliegue con stack mínimo **`web`** + **`waf`**.

### 2.1. Mecanismo (orden real de ejecución)

1. **`ansible-playbook site.yml`** contra el grupo **`medical`** con `become: true`.
2. **`roles/docker`**: prepara APT, clave y `sources` de Docker, instala paquetes
   `docker-ce`, `docker-ce-cli`, `containerd.io`, `docker-buildx-plugin`,
   `docker-compose-plugin` y arranca el servicio **`docker`**.
3. **`roles/medical_compose`**: tareas descritas en detalle en la **sección 3.4**.
4. El script **`/usr/local/bin/aplicacion-medica-compose-up.sh`** (plantilla
   `deploy_compose.sh.j2`) hace `cd` al despliegue y ejecuta
   `docker compose … up -d --build` con `COMPOSE_DOCKER_CLI_BUILD=0`,
   `DOCKER_BUILDKIT=0` y `COMPOSE_PROJECT_NAME={{ medical_compose_project_name }}`. Si
   `medical_compose_profiles` no está vacío, añade **`--profile <nombre>`** por cada
   elemento de la lista.

La definición de **servicios, imágenes, puertos y dependencias** está solo en
**`docker-compose.yml`** del repositorio de la aplicación; Ansible no redefine el
stack, solo prepara disco y entorno y lanza Compose.

### 2.2. Servicios en marcha sin perfiles Compose

Con **`medical_compose_profiles`** vacío (por defecto), Compose arranca los
servicios **sin** `profiles:` en el YAML:

| Servicio | Cómo se obtiene | Función |
|---|---|---|
| **`web`** | `build: .` | Imagen construida desde el `Dockerfile` del repo; Gunicorn en **5001/tcp** dentro de la red de contenedores. |
| **`waf`** | Imagen `owasp/modsecurity-crs:nginx-alpine` | Proxy **ModSecurity + CRS**; publica **`5001:8080`** en el host ⇒ acceso típico **`http://<IP_VM>:5001`**. |

**`waf`** tiene **`depends_on: web`** con condición **`service_healthy`**: hasta que
`web` pase el healthcheck interno, el WAF no estabiliza.

#### Comprobación en navegador (API vía WAF, puerto 5001)

Tras el playbook, el acceso a **`http://<IP_VM>:5001/`** (IP de la VM creada por
Terraform) muestra la aplicación detrás del WAF ModSecurity.

![Captura: navegador en el puerto 5001 (API vía WAF)](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/navegador-api-5001.png)

### 2.3. Datos y `.env`

Si **no** existe `.env` en la VM, se copia desde **`docker-compose.env.example`**
(`remote_src` en el mismo árbol). Se inserta un bloque con **`FLASK_ENV`** y
**`APP_SUPERVISOR`** y se fuerza modo **`0644`** en el fichero para que el usuario
**`appuser` (UID 1000)** del contenedor `web` pueda leer **`/app/.env`** (bind mount
`.:/app`). El **`rsync`** **excluye** `.env` para no pisar secretos desde el
nodo de control en sucesivas ejecuciones.

**`STORAGE_BACKEND`** en Compose cae por defecto en **`sqlite`** si no se define en
`.env` (laboratorio sin PostgreSQL “global” de la app en el stack mínimo).

### 2.4. ¿“Totalmente funcional”?

| Alcance | Tras playbook OK |
|---|---|
| **API + WAF** | Sí en condiciones normales (contenedores **healthy**, red a la VM). |
| **DefectDojo + dependencias** | Solo con **`medical_compose_profiles`** que incluya **`defectdojo`**. |
| **Producción / HTTPS / secretos fuertes** | No; requiere trabajo adicional manual o otras herramientas. |
| **Cliente Android** | Fuera de este módulo; la URL base debe apuntar a la IP de la VM. |

### 2.5. Variable `medical_compose_profiles` (perfiles Compose)

No existe un flag `--all` en CLI: la variable es una **lista YAML** o un **JSON** en
`-e`.

| Dónde definirla | Ejemplo |
|---|---|
| `extra_vars.yml` | `medical_compose_profiles: [defectdojo]` |
| Línea de órdenes | `-e '{"medical_compose_profiles":["defectdojo"]}'` |
| `group_vars` / `host_vars` | Misma clave en YAML del grupo `medical` |

**Perfiles** definidos en `docker-compose.yml` (resumen): **`defectdojo`** (stack
DefectDojo + `wstg-sync` asociado), **`tests`** (`frontend-tests`), **`local`**
(frontend alternativo; **conflictivo** con el puerto **5001** del `waf` si se
mezcla sin criterio).

**Recursos**: con **`deployment_mode = "full"`** en Terraform la VM queda orientada a
**16G / 6 vCPU / 80G** salvo overrides en `terraform.tfvars`. El perfil **`defectdojo`**
exige dimensionamiento acorde; en caso contrario conviene ajustar la VM con Terraform
antes de activarlo en Ansible.

#### Coordinación Terraform + Ansible (DefectDojo)

1. **`terraform apply`** con recursos acordes (salida **`effective_vm_sizing`**).
2. **`ansible-playbook`** con **`medical_compose_profiles: [defectdojo]`** (plantilla
   `extra_vars.full.example.yml`).

Con ese perfil, la interfaz web de DefectDojo queda en **`http://<IP_VM>:8080/`**
(nginx del stack). En el despliegue documentado en este informe se utilizó el stack
mínimo **web + waf** (sin perfil `defectdojo`).

---

## 3. Detalle de inventario, variables y roles

### 3.1. Inventario y conexión

El inventario se define en **`inventory.ini`** (a partir de `inventory.ini.example`),
con **`ansible_host`** igual a la IP de **`terraform output vm_ip_address`** o a la
línea **`ansible_inventory_line`**.

Las rutas con **espacios** en `ansible_ssh_private_key_file` deben ir entre **comillas
dobles** en el fichero INI para que el parser no las divida.

### 3.2. Variable `medical_app_source`

Es la ruta **absoluta** en el nodo de control Ansible al **directorio raíz del
repositorio** (donde están `docker-compose.yml` y el `Dockerfile`).

| Problema | Causa | Solución |
|---|---|---|
| Ruta troceada al usar `-e medical_app_source=/.../PPS - ...` | El shell parte el valor en espacios. | Usar **JSON** o **`-e @extra_vars.yml`** con la ruta entre comillas YAML. |
| `rsync` bajo `.../ansible/home/...` | Filtro **`trim('/')`** en Jinja quitaba la **/** inicial y la ruta pasaba a ser relativa al playbook. | En el rol se usa **`regex_replace('/$', '')`** solo para la barra final. |

### 3.3. Rol `docker` — tareas y efecto en la VM

Orden en `roles/docker/tasks/main.yml`:

| Orden | Tarea (resumen) | Efecto en la VM |
|---|---|---|
| 1 | `apt` update (caché 1 h) | Índice APT actualizado. |
| 2 | Instalar `ca-certificates` | Base para HTTPS a repos. |
| 3 | Crear `/etc/apt/keyrings` | Directorio para la clave GPG de Docker. |
| 4 | `stat` de `docker.asc` | Decide si hace falta bajar la clave. |
| 5 | `get_url` GPG Docker | Escribe `/etc/apt/keyrings/docker.asc` (con reintentos y timeout si aplica). |
| 6 | `copy` `docker.sources` | Añade el repo **Debian** de Docker (`Signed-By` apuntando a la clave). |
| 7 | `apt` instalar paquetes Docker | Instala motor, CLI, containerd, buildx y **plugin Compose v2**. |
| 8 | `service` docker | Servicio **habilitado y arrancado**. |

### 3.4. Rol `medical_compose` — tareas y efecto en la VM

| Orden | Tarea | Efecto |
|---|---|---|
| 1 | `assert` | Falla si falta `medical_app_source`. |
| 2 | `apt` `rsync` | Paquete rsync para `synchronize`. |
| 3 | `file` | Crea `medical_app_deploy_path` (0755). |
| 4 | `synchronize` push | Copia el repo desde el **controlador** a la VM; exclusiones: `.git`, cachés, **`.env`**, `.terraform`, etc. |
| 5 | `stat` + `fail` | Comprueba que exista `docker-compose.env.example` tras el rsync; si no, el playbook falla con mensaje claro. |
| 6 | `file` en bucle | Crea `data/waf`, `data/postgres`, `data/redis`, `data/defectdojo/media`, `data/defectdojo/static`. |
| 7 | `shell` | Crea la red Docker **`proxy-network`** si no existe (requerida porque en `docker-compose.yml` es `external: true`). |
| 8 | `copy` remoto | Crea `.env` desde `docker-compose.env.example` si no existe (`0644`). |
| 9 | `file` | Refuerza **0644** en `.env`. |
| 10 | `blockinfile` | Añade bloque marcado con `FLASK_ENV` y `APP_SUPERVISOR` (`mode: "0644"` en el módulo). |
| 11 | `file` | Vuelve a asegurar **0644** tras el bloque. |
| 12 | `template` | Genera `/usr/local/bin/aplicacion-medica-compose-up.sh`. |
| 13 | `command` + `debug` | Ejecuta ese script y muestra la salida estándar en el recap de Ansible. |

**Problema `.env` Permission denied en `web`**: el contenedor corre como **appuser**;
sin **0644** en el `.env` del host, no puede leer el bind mount. Solución: tareas de
permiso + `mode` en `blockinfile` (véase tabla en **3.4**).

### 3.5. Colección `ansible.posix`

El playbook declara la colección en `requirements.yml`; sin **`ansible.posix`** el
módulo **`synchronize`** no está disponible.

---

## 4. Procedimiento de despliegue

1. **Inventario** (`inventory.ini`): host del grupo `[medical]`, usuario SSH y clave
   privada (ruta entrecomillada si contiene espacios).
2. **Variables** (`extra_vars.yml`): ruta absoluta **`medical_app_source`** al repo;
   plantillas [`extra_vars.example.yml`](../extra_vars.example.yml) (solo **web + waf**)
   o [`extra_vars.full.example.yml`](../extra_vars.full.example.yml) (añade perfil
   **`defectdojo`**).
3. **Colección y playbook**:

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
ansible medical -m ping -i inventory.ini
ansible-playbook site.yml -i inventory.ini -e @extra_vars.yml
```

#### Conectividad SSH y resultado del playbook

El módulo **`ping`** confirma acceso SSH al grupo **`medical`**. El **`site.yml`**
finaliza con **`failed=0`** en el **PLAY RECAP**.

![Captura: ansible ping al grupo medical](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/ansible-ping-ok.png)

![Captura: PLAY RECAP del site.yml](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/ansible-playbook-recap.png)

---

## 5. Relación con Terraform

```mermaid
flowchart LR
  subgraph tf [Terraform]
    A[terraform apply]
  end
  subgraph px [Proxmox]
    B[VM lista por SSH]
  end
  subgraph ans [Ansible]
    C[roles/docker]
    D[roles/medical_compose]
  end
  subgraph dk [Docker]
    E[docker compose up]
  end
  A --> B
  B --> C
  C --> D
  D --> E
```

1. **Terraform** crea la VM (véase el [Informe Terraform](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/Informe.md)).
2. **Ansible** instala Docker y levanta el stack (sección **2** de este documento).

---

## 6. Seguridad y buenas prácticas

- **`inventory.ini`** y **`extra_vars.yml`** contienen datos de acceso (claves, rutas);
  no forman parte del paquete de entrega por contener información sensible.
- **`rsync` excluye `.env`**: los secretos se mantienen en la VM entre ejecuciones.
- **`.env` 0644** en la VM es un **compromiso de laboratorio** para el bind mount;
  endurecer implicaría otra estrategia (secrets de Docker, variables solo en
  `environment:` de Compose, etc.).

---

## 7. Validación del despliegue

En la VM desplegada, los contenedores **`web`** y **`waf`** aparecen en estado
**healthy** y la comprobación HTTP al puerto **5001** devuelve **`HTTP:200`**.

![Captura: docker compose ps (web y waf)](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/docker-ps-waf-web.png)

![Captura: curl HTTP 200 en el puerto 5001](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/curl-api-5001.png)

Comandos equivalentes en la VM:

```bash
sudo docker compose -f /opt/aplicacion-medica/docker-compose.yml ps
curl -sS -o /dev/null -w "HTTP:%{http_code}\n" http://127.0.0.1:5001/
```

---

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

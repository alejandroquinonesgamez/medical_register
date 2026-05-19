# Despliegue Proxmox + Ansible — Aplicación Médica (VM única)

Este directorio automatiza:

1. **Terraform**: crea una VM Debian (cloud-init) en Proxmox. Con **`deployment_mode = "full"`** (por defecto) la VM queda dimensionada para **Docker Compose completo** (waf + web + perfil **DefectDojo** en Ansible): **16 GB RAM, 6 vCPU, 80G** de disco, salvo overrides en `terraform.tfvars`. Con **`minimal`** los presets son **8 GB / 4 vCPU / 50G** (solo waf + web).
2. **Ansible**: instala Docker Engine + plugin Compose v2, crea la red externa `proxy-network` (obligatoria según [docker-compose.yml](../../docker-compose.yml)), sincroniza el repositorio y ejecuta `docker compose up -d --build`. El **despliegue completo** del compose (incluido DefectDojo) se activa con la variable **`medical_compose_profiles`** (véase `ansible/extra_vars.full.example.yml` y [Ansible.md](../../docs/terraform/Ansible.md)).

## Requisitos previos

- Plantilla cloud-init en Proxmox (mismo enfoque que `terraform/jenkins`).
- Snippet `qemu-guest-agent` referenciado en Terraform (`cicustom`), como en los ejemplos existentes.
- Token API Proxmox con permisos sobre el nodo/pool.
- En la máquina de control: **Terraform ≥ 1**, **Ansible**, **rsync**, **OpenSSH**.
- Colección Ansible **`ansible.posix`** (módulo `synchronize`):

```bash
cd ansible
ansible-galaxy collection install -r requirements.yml
```

## Chequeo rápido (sin tocar Proxmox todavía)

Desde `terraform/aplicacion-medica/`:

```bash
./verify-local.sh
```

Esto ejecuta `terraform validate` y `ansible-playbook --syntax-check` usando la ruta real del repo como `medical_app_source`.

- Si existe `terraform/terraform.tfvars`, también lanza **`terraform plan`** (el proveedor **sí contacta la API** de Proxmox; sin servidor o credenciales válidas fallará con error de red o 401).
- Si existe `ansible/inventory.ini`, intenta **`ansible medical -m ping`** contra la VM.

## 1. Terraform

```bash
cd terraform/aplicacion-medica/terraform
cp terraform.tfvars.example terraform.tfvars
# Editar terraform.tfvars: API Proxmox, token, pool, red, ipconfig, clave pública SSH (ruta absoluta recomendada para ssh_key_file)
# deployment_mode = "full"   # por defecto en el ejemplo; "minimal" solo si solo desplegarás waf+web en Ansible

terraform init
terraform apply
```

Tras el `apply`, copia la salida `ansible_inventory_line` o el valor de `vm_ip_address`, y revisa **`effective_vm_sizing`** / **`ansible_full_stack_hint`**.

**Notas:**

- **`deployment_mode`**: `full` (por defecto) aprovisiona **16384 MB RAM, 6 vCPU, 80G** si no pones `vm_memory_mb` (≥ 0), `vm_cores` (> 0) ni `disk_size` no vacío. Para solo API+WAF en Ansible usa `minimal` o fija overrides a mano.
- **`ssh_key_file`**: ruta que **Terraform** pueda leer (`file()`); evita `~` si tu versión no lo expande: usa ruta absoluta.

## 2. Inventario Ansible

```bash
cd ../ansible
cp inventory.ini.example inventory.ini
# Ajusta ansible_host y ansible_ssh_private_key_file
```

El grupo debe llamarse **`medical`** (coincide con `site.yml`).

## 3. Playbook

`medical_app_source` es la ruta **absoluta** al **raíz del repo** *Aplicación Médica* (donde están `docker-compose.yml`, `Dockerfile`, `waf/`, etc.). Si la ruta contiene **espacios**, evita `-e clave=ruta` en shell (Ansible la trocea mal); usa **JSON** o un **YAML** con `-e @fichero`:

```bash
ansible-playbook site.yml -e '{"medical_app_source":"/ruta/absoluta/PPS - .../Aplicación Médica"}'
```

O bien copia [`ansible/extra_vars.example.yml`](ansible/extra_vars.example.yml) a `extra_vars.yml`, rellena la ruta entre comillas y ejecuta:

```bash
ansible-playbook site.yml -e @extra_vars.yml
```

### Perfiles Compose (`medical_compose_profiles`)

Ansible **no** usa una bandera tipo `--all`. La variable es una **lista** de perfiles de `docker-compose.yml`:

| Situación | Qué hacer |
|---|---|
| **Solo API + WAF** | No definas perfiles (lista vacía) o `medical_compose_profiles: []` en `extra_vars.yml`. Terraform puede ir con `deployment_mode = "minimal"`. |
| **Despliegue completo (incluye DefectDojo)** | Terraform **`deployment_mode = "full"`** + Ansible **`medical_compose_profiles: [defectdojo]`**. Plantilla: copia [`ansible/extra_vars.full.example.yml`](ansible/extra_vars.full.example.yml) a `extra_vars.yml` y ajusta `medical_app_source`. |

**Solo añadir DefectDojo** (si ya tienes `extra_vars.yml` con la ruta del repo):

```bash
ansible-playbook site.yml -e @extra_vars.yml \
  -e '{"medical_compose_profiles":["defectdojo"]}'
```

**Varios perfiles** (ejemplo `defectdojo` + `tests`):

```bash
ansible-playbook site.yml -e @extra_vars.yml \
  -e '{"medical_compose_profiles":["defectdojo","tests"]}'
```

Documentación detallada, tabla de perfiles y advertencias (perfil `local`, recursos):
**[Ansible.md](../../docs/terraform/Ansible.md)** (sección 2 y 2.5).

## Qué hace Ansible (resumen fiel al repo)

| Paso | Motivo en el código real |
|------|-------------------------|
| Instalar Docker + Compose v2 | `docker compose` del [Makefile](../../Makefile) |
| `docker network create proxy-network` si no existe | [docker-compose.yml](../../docker-compose.yml): `proxy-network: external: true` (equivalente a `make ensure-proxy-network`) |
| `rsync` del repo a `/opt/aplicacion-medica` | `build: .` y rutas `./waf`, `./data/...` en compose |
| `.env` desde [docker-compose.env.example](../../docker-compose.env.example) si no existe | Misma lógica que `make setup-env` |
| Bloque en `.env`: `FLASK_ENV=production`, `APP_SUPERVISOR=0` | Comentarios en compose para entorno servidor |
| `COMPOSE_DOCKER_CLI_BUILD=0`, `DOCKER_BUILDKIT=0`, `COMPOSE_PROJECT_NAME=medical_register` | [Makefile](../../Makefile) y [docker-compose.env.example](../../docker-compose.env.example) |

El rsync **excluye `.env`** para no machacar secretos en la VM si ya los configuraste a mano.

## Acceso

- API vía WAF: `http://<IP_VM>:5001` (puerto publicado por el servicio `waf` en [docker-compose.yml](../../docker-compose.yml)).
- El APK Android debe usar esa URL base (HTTP solo aceptable en lab; en producción usar TLS).

## Secretos (JWT, reCAPTCHA, SQLCipher, etc.)

Edita `.env` **en la VM** bajo `/opt/aplicacion-medica/.env` o pásalos con **Ansible Vault** / variables de entorno en CI antes del playbook; no subas `terraform.tfvars` ni `.env` reales al repositorio.

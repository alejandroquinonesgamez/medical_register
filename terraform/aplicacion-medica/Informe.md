# Informe — Terraform (VM Proxmox, Aplicación Médica)

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

---

## Conformidad con la entrega (PPS)

Este paquete cumple lo pedido para la parte **Terraform** de la práctica:

| Requisito | Dónde se cubre en este informe |
|---|---|
| **Proyecto Terraform** que crea la **VM en Proxmox** para el backend (y el resto del stack vía Ansible después) | §1.2 (ficheros `.tf`), §2 (recurso `proxmox_vm_qemu`), y el código en la carpeta **`terraform/`** (`main.tf`, `variables.tf`, etc.). |
| **Documentación** que demuestre el **despliegue correcto** | §2.1 (captura en Proxmox con hardware), §5 (plan y salidas `terraform output` / sizing efectivo). Las figuras enlazan a imágenes en GitHub (`raw.githubusercontent.com`, rama `dev`). |
| **Justificación** de **memoria** y **disco** (y CPU acoplada al modo de despliegue) | §2.2: presets `full` vs `minimal` (RAM, vCPU, disco) y cómo los **overrides** en `terraform.tfvars` sustituyen al preset. |

El aprovisionamiento de **Docker** y **Compose** en la VM se describe en **[terraform/docs/Ansible.md](terraform/docs/Ansible.md)**. Las figuras enlazan a **`raw.githubusercontent.com`** (rama **`dev`**, repo **`medical_register`**) para que se vean al abrir el `.md` fuera del clon; en el **ZIP de entrega** las mismas rutas siguen funcionando con conexión a Internet.

---

## 1. Introducción

Este documento describe el **módulo Terraform** en la subcarpeta **`terraform/`**
(junto a este informe en el paquete de entrega; en el monorepo del curso:
`terraform/aplicacion-medica/terraform/`), que crea una **máquina virtual QEMU** en
**Proxmox** para alojar el despliegue Docker del proyecto **Aplicación Médica**
(backend Flask, WAF, servicios opcionales como DefectDojo, etc.). Sigue el mismo
criterio que el ejemplo docente `terraform/jenkins/`, pero **sin `vmid` fijo** en el
código (Proxmox asigna el siguiente ID libre).

A continuación se detalla **qué aplica `terraform apply` en el hipervisor**, cómo se
eligen **RAM, CPU y disco** (`deployment_mode` y `locals.tf`), qué variables existen y
cómo validar la configuración. La instalación de **Docker** y **`docker compose`** en
la VM corresponde a **[terraform/docs/Ansible.md](terraform/docs/Ansible.md)**.

### 1.1. Qué es Terraform (resumen operativo)

Terraform es **Infraestructura como código (IaC)**: se declaran recursos en
ficheros `.tf`, se parametrizan variables (habitualmente vía `terraform.tfvars`) y
Terraform calcula un **plan** de cambios y lo **aplica** de forma reproducible y
auditable.

### 1.2. Ficheros del módulo

| Fichero | Función |
|---|---|
| `providers.tf` | Bloque `terraform` (versión mínima **≥ 1.0.0**) y proveedor **`telmate/proxmox`** en versión **3.0.2-rc07**. Bloque `provider "proxmox"` con URL de API, token y `pm_tls_insecure`. |
| `variables.tf` | Todas las variables de entrada (Proxmox, `deployment_mode`, dimensionado de VM, cloud-init, `ssh_key_file`). Incluye **validación** de `deployment_mode` (`full` \| `minimal`). |
| `locals.tf` | Calcula **`vm_memory_effective`**, **`vm_cores_effective`** y **`disk_size_effective`**: si usas los valores “automáticos” (`vm_memory_mb = -1`, `vm_cores = 0`, `disk_size = ""`), se toma el **preset** según `deployment_mode`; si defines overrides explícitos, **mandan sobre el preset**. |
| `main.tf` | Recurso único **`proxmox_vm_qemu.aplicacion_medica`**: clon desde plantilla, discos, red, CPU, RAM, cloud-init, agente QEMU, etc. |
| `outputs.tf` | Salidas tras el `apply`: IP, `vmid`, línea de inventario Ansible, `deployment_mode`, `effective_vm_sizing`, `ansible_full_stack_hint`. |
| `terraform.tfvars.example` | Plantilla comentada de valores (no contiene secretos reales). |
| `.gitignore` del directorio | Ignora `*.tfvars`, estado local, caché de plugins, etc., para no versionar credenciales. |

> ⚠️ **Inconveniente**: el proveedor Proxmox **contacta la API del hipervisor** incluso
> durante `terraform plan`. No hay un plan “100 % offline”: hace falta red y
> credenciales válidas salvo que solo ejecutes `terraform validate` (sin API).

### 1.3. Variables: conexión al hipervisor y almacenamiento

Estas variables se leen en **`provider "proxmox"`** y en el recurso de la VM (pool,
storage, bridge).

| Variable | Tipo | Uso en la configuración |
|---|---|---|
| `pm_api_url` | `string` | URL base de la API PVE, con sufijo `/api2/json` (ej. `https://host:8006/api2/json`). |
| `pm_tls_insecure` | `bool` (defecto `true`) | Si es `true`, el cliente Terraform **no exige** un certificado TLS de confianza (típico en laboratorio con certificado autofirmado). Si el clúster usa CA válida, puedes poner `false`. |
| `pm_node` | `string` | Nombre del **nodo** PVE donde se crea la VM (`target_node`). |
| `pm_template` | `string` | **Nombre o ID** de la plantilla cloud-init a **clonar** (debe existir en el nodo). |
| `pm_api_token_id` | `string` | Identificador del token API (`usuario@pam!nombre`). |
| `pm_api_token_secret` | `string` (sensible) | Secreto del token. |
| `pm_pool` | `string` | **Pool** de recursos del usuario (en entornos docentes suele ser obligatorio). |
| `pm_storage` | `string` | Almacenamiento para el **disco raíz** SCSI y el volumen **cloud-init** en IDE. |
| `pm_bridge` | `string` | **Bridge** de red de la VM (ej. `vmbr10`). |

### 1.4. Variables: VM, cloud-init y modo de despliegue

| Variable | Tipo / defecto | Qué hace |
|---|---|---|
| `deployment_mode` | `string`, `"full"` | Selecciona el **preset** de tamaño cuando no hay overrides (véase sección 2.2). Valores permitidos: **`full`**, **`minimal`**. |
| `vm_name` | `string`, `pps-aplicacion-medica` | Nombre visible de la VM en Proxmox. |
| `vm_memory_mb` | `number`, `-1` | Si **≥ 0**, es la RAM en MiB **efectiva**. Si **-1**, Terraform usa el preset de `deployment_mode`. |
| `vm_cores` | `number`, `0` | Si **> 0**, número de **cores** por socket. Si **0**, preset según `deployment_mode`. |
| `disk_size` | `string`, `""` | Si **no vacía** (ej. `"50G"`), tamaño del disco SCSI. Si **vacía**, preset según `deployment_mode`. |
| `ipconfig` | `string` | Cadena **`ipconfig0`** de cloud-init (IP estática o DHCP, gateway, IPv6, etc.). |
| `ci_user` / `ci_password` | `string` | Usuario y contraseña del **primer usuario Linux** creado por cloud-init (la contraseña es sensible). |
| `ssh_key_file` | `string` | Ruta en la máquina que ejecuta Terraform al fichero **público** SSH; su contenido se inyecta en la imagen (`sshkeys = file(...)`). Debe ser **ruta absoluta** fiable para `file()`. |

---

## 2. Qué se despliega al ejecutar `terraform apply`

Terraform gestiona **un solo recurso**: `proxmox_vm_qemu.aplicacion_medica`. El
`apply` **crea o modifica esa VM** en Proxmox. **No** instala paquetes en el SO de la
VM, **no** copia el repositorio de la aplicación y **no** ejecuta Docker: eso lo hace
**Ansible** después.

### 2.1. Comportamiento del recurso (resumen fiel a `main.tf`)

| Elemento | Configuración aplicada |
|---|---|
| **Clon** | `clone = var.pm_template` (clon completo; el proveedor gestiona el ciclo de clonación). |
| **Arranque** | `vm_state = "running"`, `boot = "order=scsi0"`, `os_type = "cloud-init"`. |
| **CPU** | Bloque `cpu`: `cores = local.vm_cores_effective`, `sockets = 1`, `type = "host"`. |
| **RAM** | `memory = local.vm_memory_effective`. |
| **Disco** | SCSI0 en `pm_storage` con `size = local.disk_size_effective`; disco **cloud-init** en IDE1 en el mismo storage. |
| **Red** | Una NIC `virtio` al `pm_bridge`. |
| **Cloud-init** | `ipconfig0`, `ciuser`, `cipassword`, `sshkeys`, `skip_ipv6 = true`, `ciupgrade = true`. |
| **QEMU Guest Agent** | `agent = 1` y `cicustom` apuntando al snippet **`vendor=local:snippets/qemu-guest-agent.yml`** en el hipervisor (debe existir en Proxmox, igual que en el ejemplo Jenkins). |
| **Consola** | Bloque `serial { id = 0 }` para compatibilidad con imágenes cloud. |
| **Pool** | `pool = var.pm_pool`. |

#### Evidencia sugerida: VM y recursos en Proxmox

La siguiente figura ilustra que la VM existe en el hipervisor y que **memoria, CPU y
disco** coinciden con lo declarado (preset `deployment_mode` o overrides). Captura
desde Proxmox (pestaña **Resumen** o **Hardware** de la VM).

![Captura: VM en Proxmox con hardware visible](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/proxmox-vm-hardware.png)

### 2.2. `deployment_mode` y cálculo en `locals.tf` (justificación de RAM y disco)

| `deployment_mode` | Objetivo al combinar con Ansible | Preset si `vm_memory_mb = -1`, `vm_cores = 0`, `disk_size = ""` |
|---|---|---|
| **`full`** | Margen para **waf + web + perfil `defectdojo`** en la misma VM | **16384** MiB RAM, **6** vCPU, **80G** disco |
| **`minimal`** | Solo **waf + web** sin DefectDojo | **8192** MiB RAM, **4** vCPU, **50G** disco |

**Justificación:** el backend en contenedores comparte RAM con el **WAF (nginx + ModSecurity + CRS)**, la **API Gunicorn** y, en modo `full`, **DefectDojo** y dependencias (PostgreSQL/redis/nginx internos del stack), que son **muy sensibles** a memoria insuficiente (OOM, arranques lentos o fallidos). El disco debe albergar imágenes Docker, capas, volúmenes y logs de laboratorio; **80G** en `full` reduce fricción con pulls y datos de DefectDojo, y **50G** en `minimal` es suficiente si solo se despliega API+WAF.

Si en `terraform.tfvars` fijas **`vm_memory_mb` ≥ 0**, **`vm_cores` > 0** o
**`disk_size`** no vacío, **esos valores sustituyen al preset** (útil para cuotas del
pool o VMs ya desplegadas). Ejemplo: `deployment_mode = "full"` con
`disk_size = "50G"` fuerza **50G** aunque el preset “full” sea 80G.

### 2.3. Qué no forma parte del `apply`

| No lo hace Terraform | Dónde se hace |
|---|---|
| Docker Engine / Compose | Ansible, rol `docker`. |
| Código en `/opt/aplicacion-medica` | Ansible, `rsync` en `medical_compose`. |
| Red Docker `proxy-network` y contenedores | `docker compose` vía Ansible. |
| Secretos de aplicación (`.env`) | Edición en la VM o plantillas/Ansible Vault; no los genera Terraform. |

---

## 3. Contexto en el repositorio y lecciones aprendidas

### 3.1. Relación con `terraform/jenkins/`

Los valores de entorno **Proxmox** del despliegue docente se alinearon con
`terraform/jenkins/terraform/terraform.tfvars`, adaptando la **clave pública** a una
ruta **dentro del repo** (`terraform/git-terraform-ansible-ejemplo-main/src/.ssh/id_ed25519_pps.pub`)
y usando **IP y nombre de VM distintos** a la VM Jenkins para no solapar recursos.

### 3.2. Problemas encontrados y cómo se resolvieron

| Problema | Causa | Solución |
|---|---|---|
| `terraform plan` sin API | El proveedor habla con Proxmox al planificar. | `verify-local.sh` solo ejecuta `plan` si existe `terraform.tfvars` y hay conectividad; para CI sin red, usar solo `terraform validate`. |
| `ssh_key_file` con `~` o ruta relativa | `file()` y el cwd. | Documentar **ruta absoluta** en `terraform.tfvars.example`. |
| Convivencia con Jenkins | Mismo pool/plantilla. | Distinto `vm_name`, IP en `ipconfig` y `vmid` libre. |

### 3.3. Seguridad y buenas prácticas

- **`terraform.tfvars`**: contiene **token** y **contraseña** cloud-init; está en
  `.gitignore` del módulo y **no debe publicarse**.
- Tras el `apply`, revisar en Proxmox que la VM esté solo en el **pool** del alumno
  y con **firewall** acorde a la práctica.

---

## 4. Flujo mínimo de uso

Desde la **raíz del ZIP de entrega** (donde está este `Informe.md`):

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Editar: API, token, pool, storage, bridge, ipconfig, ci_*, ssh_key_file absoluto
# deployment_mode = "full"   # ya viene en el ejemplo; "minimal" si solo API+WAF

terraform init
terraform apply
terraform output effective_vm_sizing
terraform output ansible_inventory_line
```

En el **monorepo** del curso la ruta equivalente es `terraform/aplicacion-medica/terraform/`.

Siguiente paso: inventario y playbook en **[terraform/docs/Ansible.md](terraform/docs/Ansible.md)**.

---

## 5. Validación

### 5.1. Salidas útiles (`outputs.tf`)

| Salida | Contenido típico |
|---|---|
| `vm_ip_address` | IPv4 de la VM (útil para SSH y `ansible_host`). |
| `ansible_inventory_line` | Línea sugerida bajo `[medical]` para copiar/pegar en `inventory.ini`. |
| `vm_id` | `vmid` numérico en Proxmox. |
| `ssh_command` | Comando SSH de ejemplo. |
| `deployment_mode` | `full` o `minimal` aplicado. |
| `effective_vm_sizing` | Mapa `memory_mb`, `cores`, `disk` **ya con overrides aplicados**. |
| `ansible_full_stack_hint` | Recordatorio textual para usar `medical_compose_profiles: [defectdojo]` en Ansible. |

### 5.2. Comandos

**ZIP de entrega** (`cd terraform`):

```bash
cd terraform
terraform init -backend=false
terraform validate
```

**Monorepo** (`cd terraform/aplicacion-medica/terraform`).

Con `terraform.tfvars` y red al hipervisor:

```bash
cd terraform   # o la ruta larga en el monorepo
terraform plan
terraform apply
terraform output -json effective_vm_sizing
```

#### Evidencia sugerida: plan y salidas en terminal

Tras `terraform plan`, captura el resumen del plan (cambios o “no changes”). Tras
`apply`, muestra al menos **`vm_ip_address`** y **`effective_vm_sizing`** con
`terraform output`.

![Captura: salida de terraform plan](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/terraform-plan.png)

![Captura: salida de terraform output (IP y sizing)](https://raw.githubusercontent.com/alejandroquinonesgamez/medical_register/dev/terraform/aplicacion-medica/terraform/docs/img/terraform-output-vm.png)

El script `terraform/aplicacion-medica/verify-local.sh` ejecuta `validate` y, si
existe `terraform.tfvars`, también `plan` (contacta la API).

---

## 6. Comparativa rápida: Terraform frente a Ansible (en este proyecto)

| Aspecto | Terraform | Ansible |
|---|---|---|
| Responsabilidad | **VM** en Proxmox (hardware, cloud-init, red). | **SO + Docker + código + compose** en la VM. |
| Estado | `terraform.tfstate` (local; sensible). | Sin estado; idempotencia por módulos. |
| “Despliegue completo” app | Dimensiona con `deployment_mode` + perfiles vía doc. | `medical_compose_profiles` (ej. `defectdojo`). |

Las capturas anteriores enlazan desde **§2.1** y **§5** (imágenes servidas desde GitHub). La comprobación HTTP en **`:5001`** documenta el stack ya aprovisionado por Ansible (véase **[terraform/docs/Ansible.md](terraform/docs/Ansible.md)**).

---

**Autores**: Alejandro Quiñones Gámez & Adrián Bertos Gómez

**Asignatura**: PPS — Puesta a Producción Segura

**Curso**: Curso de Especialización en Ciberseguridad en Tecnologías de la Información

**Centro**: IES Zaidín-Vergeles

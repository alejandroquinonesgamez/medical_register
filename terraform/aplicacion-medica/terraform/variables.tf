# Parámetros Proxmox y cloud-init (mismo criterio que terraform/jenkins).

variable "pm_api_url" {
  description = "URL de la API Proxmox (ej. https://192.168.1.100:8006/api2/json)"
  type        = string
}

variable "pm_tls_insecure" {
  description = "true si el certificado de Proxmox no es de confianza (típico en laboratorio)"
  type        = bool
  default     = true
}

variable "pm_node" {
  description = "Nodo Proxmox donde se crea la VM"
  type        = string
}

variable "pm_template" {
  description = "ID o nombre de la plantilla cloud-init a clonar"
  type        = string
}

variable "pm_api_token_id" {
  description = "ID del token API PVE (pveuser@pam!nombre)"
  type        = string
}

variable "pm_api_token_secret" {
  description = "Secreto del token API"
  type        = string
  sensitive   = true
}

variable "pm_pool" {
  description = "Pool de recursos en Proxmox (obligatorio en muchas instalaciones docentes)"
  type        = string
}

variable "pm_storage" {
  description = "Almacenamiento para discos (ej. local-lvm)"
  type        = string
}

variable "pm_bridge" {
  description = "Bridge de red (ej. vmbr0)"
  type        = string
}

variable "deployment_mode" {
  description = <<-EOT
    full = VM dimensionada para el stack completo en Compose (waf + web + perfil defectdojo vía Ansible).
    minimal = solo API + WAF sin DefectDojo (menos RAM/disco por defecto).
  EOT
  type        = string
  default     = "full"

  validation {
    condition     = contains(["full", "minimal"], var.deployment_mode)
    error_message = "deployment_mode debe ser \"full\" o \"minimal\"."
  }
}

variable "vm_name" {
  description = "Nombre visible de la VM en Proxmox"
  type        = string
  default     = "pps-aplicacion-medica"
}

variable "vm_memory_mb" {
  description = "RAM en MB. Valor < 0 = usar preset según deployment_mode (full: 16384, minimal: 8192)."
  type        = number
  default     = -1
}

variable "vm_cores" {
  description = "vCPUs (cores). 0 = preset según deployment_mode (full: 6, minimal: 4)."
  type        = number
  default     = 0
}

variable "disk_size" {
  description = "Disco raíz. Cadena vacía = preset (full: 80G, minimal: 50G)."
  type        = string
  default     = ""
}

variable "ipconfig" {
  description = "Cloud-init ipconfig0 (ej. ip=192.168.0.80/24,gw=192.168.0.1,ip6=dhcp)"
  type        = string
}

variable "ci_user" {
  description = "Usuario Linux creado por cloud-init"
  type        = string
}

variable "ci_password" {
  description = "Contraseña del usuario cloud-init"
  type        = string
  sensitive   = true
}

variable "ssh_key_file" {
  description = "Ruta al fichero de clave pública SSH (en la máquina que ejecuta terraform)"
  type        = string
}

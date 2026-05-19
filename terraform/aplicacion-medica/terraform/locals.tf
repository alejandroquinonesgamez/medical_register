# Presets de tamaño de VM alineados con Ansible:
# - full: misma VM con waf + web + perfil defectdojo (Compose) sin quedarse corta de RAM/disco.
# - minimal: solo waf + web (medical_compose_profiles vacío o sin defectdojo).

locals {
  deployment_presets = {
    full = {
      memory_mb = 16384
      cores     = 6
      disk      = "80G"
    }
    minimal = {
      memory_mb = 8192
      cores     = 4
      disk      = "50G"
    }
  }

  deployment_preset = local.deployment_presets[var.deployment_mode]

  # vm_memory_mb < 0 => usar preset; vm_cores == 0 => preset; disk_size vacío => preset.
  vm_memory_effective = var.vm_memory_mb >= 0 ? var.vm_memory_mb : local.deployment_preset.memory_mb
  vm_cores_effective  = var.vm_cores > 0 ? var.vm_cores : local.deployment_preset.cores
  disk_size_effective = var.disk_size != "" ? var.disk_size : local.deployment_preset.disk
}

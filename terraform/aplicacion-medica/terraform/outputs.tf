output "vm_ip_address" {
  description = "IPv4 de la VM (qemu-guest-agent / cloud-init)"
  value       = proxmox_vm_qemu.aplicacion_medica.default_ipv4_address
}

output "proxmox_node" {
  description = "Nodo Proxmox"
  value       = proxmox_vm_qemu.aplicacion_medica.target_node
}

output "vm_id" {
  description = "vmid en Proxmox"
  value       = proxmox_vm_qemu.aplicacion_medica.vmid
}

output "ssh_command" {
  description = "Ejemplo de SSH"
  value       = "ssh ${var.ci_user}@${proxmox_vm_qemu.aplicacion_medica.default_ipv4_address}"
}

output "ansible_inventory_line" {
  description = "Línea para inventory.ini bajo [medical]"
  value       = "medical-vm ansible_host=${proxmox_vm_qemu.aplicacion_medica.default_ipv4_address} ansible_user=${var.ci_user}"
}

output "deployment_mode" {
  description = "Modo de dimensionado de la VM (full | minimal)"
  value       = var.deployment_mode
}

output "effective_vm_sizing" {
  description = "RAM, vCPU y disco efectivos aplicados a la VM"
  value = {
    memory_mb = local.vm_memory_effective
    cores     = local.vm_cores_effective
    disk      = local.disk_size_effective
  }
}

output "ansible_full_stack_hint" {
  description = "Sugerencia para levantar DefectDojo en la misma VM (requiere RAM suficiente; ver docs/terraform/Ansible.md)"
  value       = "Pasar medical_compose_profiles: [defectdojo] (extra_vars o -e JSON). Copia ansible/extra_vars.full.example.yml."
}

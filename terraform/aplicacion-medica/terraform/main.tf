resource "proxmox_vm_qemu" "aplicacion_medica" {
  name        = var.vm_name
  target_node = var.pm_node
  agent       = 1

  memory  = local.vm_memory_effective
  scsihw  = "virtio-scsi-single"
  os_type = "cloud-init"

  pool     = var.pm_pool
  vm_state = "running"
  boot     = "order=scsi0"

  clone   = var.pm_template
  sshkeys = file(var.ssh_key_file)

  cicustom  = "vendor=local:snippets/qemu-guest-agent.yml"
  ciupgrade = true

  ipconfig0  = var.ipconfig
  skip_ipv6  = true
  ciuser     = var.ci_user
  cipassword = var.ci_password

  serial {
    id = 0
  }

  cpu {
    cores   = local.vm_cores_effective
    sockets = 1
    type    = "host"
  }

  disks {
    scsi {
      scsi0 {
        disk {
          storage = var.pm_storage
          size      = local.disk_size_effective
        }
      }
    }
    ide {
      ide1 {
        cloudinit {
          storage = var.pm_storage
        }
      }
    }
  }

  network {
    id     = 0
    model  = "virtio"
    bridge = var.pm_bridge
  }
}

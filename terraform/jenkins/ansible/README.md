# Ansible Provisioning for Jenkins

Esta configuración provisiona un servidor Jenkins en Debian 13.

## Archivos creados

- `inventory.ini`: inventario base con host de ejemplo.
- `ansible.cfg`: configuración de Ansible.
- `site.yml`: playbook principal.
- `roles/jenkins_server/tasks/main.yml`: tareas de instalación, despliegue y configuración.

## Uso

1. Reemplaza `IP` en `inventory.ini` con la IP de la máquina Debian 13.
2. Ejecuta desde el directorio `ansible`:

```bash
ansible-playbook site.yml
```

## Acceso

  http://IP:8080
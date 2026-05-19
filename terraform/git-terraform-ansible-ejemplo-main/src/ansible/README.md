# Ansible Provisioning for Flask App

Esta configuración provisiona una aplicación Python Flask en Debian 13 usando Nginx como proxy inverso.

## Archivos creados

- `inventory.ini`: inventario base con host de ejemplo.
- `ansible.cfg`: configuración de Ansible.
- `site.yml`: playbook principal.
- `roles/flask_app/tasks/main.yml`: tareas de instalación, despliegue y configuración.
- `roles/flask_app/templates/flask.service.j2`: servicio systemd para Gunicorn.

## Uso

1. Reemplaza `IP` en `inventory.ini` con la IP de la máquina Debian 13.
2. Ejecuta desde `src/ansible`:

```bash
ansible-playbook site.yml
```

## Estructura del despliegue

- `src/app/app.py`
- `src/app/requirements.txt`
- `src/nginx/flask_app` se copia como configuración de Nginx.

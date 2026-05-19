#!/usr/bin/env bash
# Verificación local: Terraform validate + Ansible syntax-check.
# Opcional: terraform plan (requiere terraform.tfvars y API Proxmox alcanzable).
# Opcional: ansible ping (requiere inventory.ini y VM accesible por SSH).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="${ROOT}/terraform"
ANS_DIR="${ROOT}/ansible"
REPO_ROOT="$(cd "${ROOT}/../.." && pwd)"

echo "==> Terraform: init (sin backend remoto) + validate"
cd "${TF_DIR}"
terraform init -backend=false -input=false >/dev/null
terraform validate

echo "==> Ansible: colección ansible.posix + syntax-check"
cd "${ANS_DIR}"
ansible-galaxy collection install -r requirements.yml >/dev/null
TMP_VARS="$(mktemp)"
printf '%s\n' "medical_app_source: \"${REPO_ROOT}\"" >"${TMP_VARS}"
ansible-playbook --syntax-check -i inventory.ini.example site.yml -e @"${TMP_VARS}"
rm -f "${TMP_VARS}"

if [[ -f "${TF_DIR}/terraform.tfvars" ]]; then
  echo "==> Terraform: plan (contacta la API de Proxmox; puede tardar)"
  cd "${TF_DIR}"
  terraform plan -input=false -out=/dev/null
else
  echo "==> Terraform: omitido plan (no existe ${TF_DIR}/terraform.tfvars)"
  echo "    Copia terraform.tfvars.example → terraform.tfvars y vuelve a ejecutar este script."
fi

if [[ -f "${ANS_DIR}/inventory.ini" ]]; then
  echo "==> Ansible: ping al grupo medical"
  cd "${ANS_DIR}"
  ansible medical -m ping -i inventory.ini
else
  echo "==> Ansible: omitido ping (no existe ${ANS_DIR}/inventory.ini)"
  echo "    Copia inventory.ini.example → inventory.ini tras conocer la IP de la VM."
fi

echo "==> Listo."

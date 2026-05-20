#!/usr/bin/env bash
# Genera ansible-aplicacion-medica-entrega.zip en la raíz del repo Aplicación Médica:
#   Informe.md                    (raíz del ZIP; desde ansible/docs/Ansible.md)
#   ansible/                      (playbook, roles, ejemplos, docs/img; sin Ansible.md duplicado)
set -euo pipefail
AM="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$AM/../.." && pwd)"
OUT="$BASE/ansible-aplicacion-medica-entrega.zip"
ANS="$AM/ansible"
INFORME_SRC="$ANS/docs/Ansible.md"
TF_IMG="$AM/terraform/docs/img"
ANSIBLE_IMGS="ansible-ping-ok.png ansible-playbook-recap.png docker-ps-waf-web.png curl-api-5001.png navegador-api-5001.png"

python3 << PY
import zipfile
from pathlib import Path

am = Path("$AM")
base = Path("$BASE")
out = Path("$OUT")
ans = Path("$ANS")
informe_src = Path("$INFORME_SRC")
tf_img = Path("$TF_IMG")
ansible_imgs = """$ANSIBLE_IMGS""".split()

exclude_names = {"inventory.ini", "extra_vars.yml", "Ansible.md"}
exclude_suffix = {".retry"}

def skip_ansible(p: Path) -> bool:
    if not p.is_file():
        return True
    rel = p.relative_to(ans)
    if rel.name in exclude_names:
        return True
    if p.suffix in exclude_suffix:
        return True
    if "__pycache__" in rel.parts:
        return True
    # Las capturas se empaquetan desde terraform/docs/img
    if rel.parts[:2] == ("docs", "img"):
        return True
    return False

if not informe_src.is_file():
    raise SystemExit(f"No existe el informe fuente: {informe_src}")

out.unlink(missing_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(informe_src, "Informe.md")
    for path in ans.rglob("*"):
        if skip_ansible(path):
            continue
        arc = Path("ansible") / path.relative_to(ans)
        zf.write(path, arc.as_posix())
    for name in ansible_imgs:
        src = tf_img / name
        if not src.is_file():
            raise SystemExit(f"Falta captura: {src}")
        arc = Path("ansible/docs/img") / name
        zf.write(src, arc.as_posix())

print("OK:", out, "bytes:", out.stat().st_size)
PY

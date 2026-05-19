#!/usr/bin/env bash
# Genera terraform-aplicacion-medica-entrega.zip en la raíz del repo Aplicación Médica:
#   Informe.md                    (raíz del ZIP)
#   terraform/                    (módulo .tf + docs/)
set -euo pipefail
AM="$(cd "$(dirname "$0")" && pwd)"
BASE="$(cd "$AM/../.." && pwd)"
OUT="$BASE/terraform-aplicacion-medica-entrega.zip"
TF="$AM/terraform"

python3 << PY
import zipfile
from pathlib import Path

am = Path("$AM")
base = Path("$BASE")
out = Path("$OUT")
tf = Path("$TF")
informe = am / "Informe.md"

exclude_names = {"terraform.tfvars", "crash.log"}
def skip(p: Path) -> bool:
    if not p.is_file():
        return True
    rel = p.relative_to(tf)
    if ".terraform" in rel.parts:
        return True
    if p.name in exclude_names:
        return True
    if p.suffix == ".tfstate" or str(p).endswith(".tfstate.backup"):
        return True
    return False

out.unlink(missing_ok=True)
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(informe, "Informe.md")
    for path in tf.rglob("*"):
        if skip(path):
            continue
        arc = Path("terraform") / path.relative_to(tf)
        zf.write(path, arc.as_posix())

print("OK:", out, "bytes:", out.stat().st_size)
PY

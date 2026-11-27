"""Crea un ZIP de lanzamiento con la estructura esperada por el actualizador."""
from pathlib import Path
import json
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]
OUTPUT = ROOT.parent / f"PythonAcademy_Linux_v{VERSION}.zip"
EXCLUDED_DIRS = {".venv", "__pycache__", ".git", ".update_backups", "user_data"}
EXCLUDED_FILES = {".DS_Store"}

with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.name in EXCLUDED_FILES or path.name.endswith(".pyc"):
            continue
        archive.write(path, Path("python_academy") / relative)

print(f"Release creada: {OUTPUT}")

"""Actualizador seguro para Python Academy en Linux.

Comprueba la última publicación de GitHub Releases, descarga un ZIP y actualiza
los archivos de la aplicación sin tocar .venv ni los datos del usuario.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

APP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = APP_DIR / "update_config.json"
VERSION_PATH = APP_DIR / "version.json"
USER_AGENT = "PythonAcademy-Updater/1.0"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
PRESERVED_TOP_LEVEL = {".venv", "user_data", ".update_backups", ".git", "__pycache__"}
PRESERVED_FILES = {"update_config.json"}
ALLOWED_SUFFIXES = {".py", ".json", ".txt", ".md", ".toml", ".cfg"}


class UpdateError(RuntimeError):
    """Error entendible que puede mostrarse en la interfaz."""


@dataclass(frozen=True)
class Release:
    version: str
    name: str
    notes: str
    download_url: str
    asset_name: str


def _read_json(path: Path, default: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default.copy()


def current_version() -> str:
    return str(_read_json(VERSION_PATH, {"version": "0.0.0"}).get("version", "0.0.0"))


def _github_repo() -> str:
    config = _read_json(CONFIG_PATH, {"github_repo": ""})
    repo = str(config.get("github_repo", "")).strip().strip("/")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise UpdateError(
            "El actualizador todavía no está conectado a GitHub. "
            "Configura github_repo en update_config.json con el formato usuario/repositorio."
        )
    return repo


def _version_key(value: str) -> tuple[int, ...]:
    cleaned = value.strip().lower().removeprefix("v")
    match = re.match(r"^(\d+(?:\.\d+){0,3})", cleaned)
    if not match:
        raise UpdateError(f"La versión publicada '{value}' no tiene un formato válido.")
    parts = [int(part) for part in match.group(1).split(".")]
    return tuple((parts + [0, 0, 0, 0])[:4])


def _request(url: str, accept: str = "application/vnd.github+json"):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"},
    )
    try:
        return urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise UpdateError("No encuentro publicaciones en ese repositorio. Revisa el nombre y crea una Release en GitHub.") from exc
        if exc.code == 403:
            raise UpdateError("GitHub limitó temporalmente las consultas. Prueba de nuevo más tarde.") from exc
        raise UpdateError(f"GitHub respondió con un error HTTP {exc.code}.") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise UpdateError("No pude conectarme a GitHub. Revisa tu conexión a internet.") from exc


def check_for_update() -> Release | None:
    repo = _github_repo()
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        with _request(url) as response:
            release_data = json.loads(response.read().decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpdateError("La respuesta de GitHub no se pudo interpretar.") from exc

    tag = str(release_data.get("tag_name", "")).strip()
    if not tag:
        raise UpdateError("La publicación de GitHub no contiene una versión (tag).")
    latest_version = tag.removeprefix("v")
    if _version_key(latest_version) <= _version_key(current_version()):
        return None

    assets = release_data.get("assets") or []
    zip_asset = next(
        (asset for asset in assets if str(asset.get("name", "")).lower().endswith(".zip") and asset.get("browser_download_url")),
        None,
    )
    if not zip_asset:
        raise UpdateError("Hay una versión nueva, pero su publicación no contiene un archivo ZIP descargable.")

    return Release(
        version=latest_version,
        name=str(release_data.get("name") or tag),
        notes=str(release_data.get("body") or ""),
        download_url=str(zip_asset["browser_download_url"]),
        asset_name=str(zip_asset.get("name") or "actualizacion.zip"),
    )


def install_update(release: Release) -> None:
    """Descarga y aplica una release ZIP. Conserva configuración y datos locales."""
    with tempfile.TemporaryDirectory(prefix="python-academy-update-") as temp_name:
        temp_dir = Path(temp_name)
        archive_path = temp_dir / "release.zip"
        try:
            with _request(release.download_url, "application/octet-stream") as response, archive_path.open("wb") as output:
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise UpdateError("El ZIP supera el límite de 100 MB.")
                    output.write(chunk)
        except OSError as exc:
            raise UpdateError("No se pudo guardar la actualización descargada.") from exc

        extract_dir = temp_dir / "extraido"
        extract_dir.mkdir()
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = archive.infolist()
                if not members:
                    raise UpdateError("El ZIP de actualización está vacío.")
                # Detecta el directorio raíz del proyecto (normalmente python_academy/).
                file_names = [m.filename for m in members if not m.is_dir()]
                root_prefix = ""
                if file_names and all(name.startswith("python_academy/") for name in file_names):
                    root_prefix = "python_academy/"

                extracted_files = []
                for member in members:
                    if member.is_dir():
                        continue
                    raw_name = member.filename
                    if root_prefix:
                        if not raw_name.startswith(root_prefix):
                            continue
                        raw_name = raw_name[len(root_prefix):]
                    rel = PurePosixPath(raw_name)
                    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
                        raise UpdateError("El ZIP contiene una ruta no segura y se canceló la actualización.")
                    if rel.parts[0] in PRESERVED_TOP_LEVEL or rel.name in PRESERVED_FILES:
                        continue
                    if rel.suffix.lower() not in ALLOWED_SUFFIXES:
                        continue
                    # No se permite instalar archivos ejecutables ajenos al código del proyecto.
                    destination = extract_dir.joinpath(*rel.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, destination.open("wb") as target:
                        shutil.copyfileobj(source, target)
                    extracted_files.append((destination, rel))
        except zipfile.BadZipFile as exc:
            raise UpdateError("El archivo descargado no es un ZIP válido.") from exc

        relative_names = {str(rel) for _, rel in extracted_files}
        if "main.py" not in relative_names or "version.json" not in relative_names:
            raise UpdateError("El ZIP no parece una versión válida: faltan main.py o version.json.")

        # Verifica que la versión dentro del ZIP coincide con la release anunciada.
        payload_version = _read_json(extract_dir / "version.json", {}).get("version")
        if str(payload_version) != release.version:
            raise UpdateError(
                f"La versión del ZIP ({payload_version}) no coincide con la publicación ({release.version})."
            )

        backup_dir = APP_DIR / ".update_backups" / current_version()
        backup_dir.mkdir(parents=True, exist_ok=True)
        for source, rel in extracted_files:
            destination = APP_DIR.joinpath(*rel.parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists() and destination.is_file():
                backup_path = backup_dir.joinpath(*rel.parts)
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(destination, backup_path)
            # Copia primero a un temporal en el mismo directorio y luego sustituye atómicamente.
            temporary_destination = destination.with_name(destination.name + ".update-tmp")
            shutil.copy2(source, temporary_destination)
            os.replace(temporary_destination, destination)


def setup_instructions() -> str:
    return (
        "Para habilitar las actualizaciones automáticas, crea un repositorio de GitHub "
        "y publica cada versión como una Release con el ZIP de Python Academy. "
        "Después escribe usuario/repositorio en update_config.json. "
        "La guía completa está en README.txt."
    )

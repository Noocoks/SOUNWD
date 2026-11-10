"""Input validation and safe file publication for SOUNWD downloaders."""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

SUPPORTED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "music.youtube.com",
    "m.youtube.com",
    "youtu.be",
}
AUDIO_EXTENSIONS = {
    ".aac", ".flac", ".m4a", ".mka", ".mp3", ".ogg", ".opus", ".wav", ".weba", ".webm"
}
ALLOWED_TEMPLATE_FIELDS = {
    "title", "id", "uploader", "channel", "playlist", "playlist_index", "ext",
    "format_id", "extractor", "upload_date",
}
_TEMPLATE_TOKEN = re.compile(r"%\(([^)]+)\)s")


def validate_youtube_url(value: str) -> bool:
    """Accept only canonical HTTPS YouTube hosts, with no credentials or custom ports."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme == "https"
            and host in SUPPORTED_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and not parsed.fragment
        )
    except (ValueError, AttributeError):
        return False


def validate_output_template(value: str) -> str:
    """Allow a filename template only; never permit path traversal or subdirectories."""
    value = (value or "").strip() or "%(title)s.%(ext)s"
    if len(value) > 200 or "/" in value or "\\" in value or ".." in value:
        raise ValueError("La plantilla solo puede definir un nombre de archivo, no una ruta.")
    tokens = _TEMPLATE_TOKEN.findall(value)
    if any(token not in ALLOWED_TEMPLATE_FIELDS for token in tokens):
        raise ValueError("La plantilla contiene campos de yt-dlp no permitidos.")
    remainder = _TEMPLATE_TOKEN.sub("", value)
    if "%" in remainder or re.search(r'[<>:"|?*\x00-\x1f]', remainder):
        raise ValueError("La plantilla contiene caracteres no permitidos.")
    if remainder.endswith((".", " ")):
        raise ValueError("El nombre no puede terminar en punto o espacio.")
    return value


def validate_advanced_options(options: dict) -> None:
    validate_output_template(options.get("outtmpl", ""))
    selector = options.get("format", "")
    if selector and (len(selector) > 128 or not re.fullmatch(r"[A-Za-z0-9._,+/\[\](){}=<>!&|^-]+", selector)):
        raise ValueError("El selector de formato contiene caracteres no permitidos.")
    playlist_items = options.get("playlist_items", "")
    if playlist_items and not re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", playlist_items):
        raise ValueError("La selección de elementos de lista no tiene un formato válido.")
    rate = options.get("ratelimit", "")
    if rate and not re.fullmatch(r"\d+(?:\.\d+)?[KMG]?", rate, re.I):
        raise ValueError("El límite de velocidad debe ser un valor como 500K o 2M.")
    retries = options.get("retries", "")
    if retries:
        if not retries.isdigit() or int(retries) > 20:
            raise ValueError("Los reintentos deben estar entre 0 y 20.")
    languages = options.get("subtitleslangs", "")
    if languages and not re.fullmatch(r"[A-Za-z0-9,_-]{1,64}", languages):
        raise ValueError("La lista de idiomas de subtítulos no tiene un formato válido.")


def copy_downloaded_files(source_dir: Path, destination_dir: Path) -> list[Path]:
    """Publish only regular audio files using exclusive, no-follow file creation."""
    source_dir = Path(source_dir)
    destination_dir = Path(destination_dir).expanduser()
    destination_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for source in sorted(source_dir.iterdir()):
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        if source.name.endswith((".part", ".ytdl")):
            continue
        stem, suffix = source.stem, source.suffix
        for index in range(1000):
            name = f"{stem}{suffix}" if index == 0 else f"{stem} ({index}){suffix}"
            target = destination_dir / name
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(target, flags, 0o600)
            except FileExistsError:
                continue
            except OSError:
                raise
            try:
                with os.fdopen(descriptor, "wb") as output, source.open("rb") as incoming:
                    shutil.copyfileobj(incoming, output, length=1024 * 1024)
                    output.flush()
                    os.fsync(output.fileno())
            except Exception:
                try:
                    target.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            saved.append(target)
            break
        else:
            raise RuntimeError("No se ha encontrado un nombre de archivo libre.")
    return saved

"""Input validation and safe file publication for SOUNWD downloaders."""
from __future__ import annotations

import os
import re
import shutil
import stat
from pathlib import Path
from urllib.parse import urlsplit
import unicodedata

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
    """Accept only canonical HTTPS YouTube URLs without URL parser ambiguities."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        return False
    if value != value.strip() or "\\" in value:
        return False
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127
           or unicodedata.category(char) in {"Cc", "Cf"} for char in value):
        return False
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        return (
            parsed.scheme.lower() == "https"
            and host in SUPPORTED_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and bool(parsed.netloc)
        )
    except (ValueError, AttributeError):
        return False


def validate_output_template(value: str) -> str:
    """Allow one safe filename template; reject paths, expressions and reserved names."""
    if not isinstance(value, str) or len(value) > 180:
        raise ValueError("La plantilla de nombre es demasiado larga.")
    value = value.strip() or "%(title)s.%(ext)s"
    if value.startswith(("/", "\\")) or "/" in value or "\\" in value or ":" in value or ".." in value:
        raise ValueError("La plantilla solo puede definir un nombre de archivo, no una ruta.")
    if any(ord(char) < 32 or ord(char) == 127 or unicodedata.category(char) in {"Cc", "Cf"}
           for char in value):
        raise ValueError("La plantilla contiene caracteres de control.")
    tokens = _TEMPLATE_TOKEN.findall(value)
    if any(token not in ALLOWED_TEMPLATE_FIELDS for token in tokens):
        raise ValueError("La plantilla contiene campos de yt-dlp no permitidos.")
    remainder = _TEMPLATE_TOKEN.sub("", value)
    if "%" in remainder or any(not (char.isalnum() or char in " _().-") for char in remainder):
        raise ValueError("La plantilla contiene caracteres o expresiones no permitidos.")
    if value.endswith((".", " ")):
        raise ValueError("El nombre no puede terminar en punto o espacio.")
    stem = value.split(".", 1)[0].upper()
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    if stem in reserved:
        raise ValueError("La plantilla utiliza un nombre de archivo reservado.")
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
    """Publish regular audio files exclusively, without following source/destination symlinks."""
    source_dir = Path(source_dir)
    destination_dir = Path(destination_dir).expanduser()
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise ValueError("La carpeta temporal de descargas no es segura.")
    if destination_dir.is_symlink():
        raise ValueError("La carpeta de destino no puede ser un enlace simbólico.")
    destination_dir.mkdir(parents=True, exist_ok=True)
    if not destination_dir.is_dir():
        raise ValueError("La carpeta de destino no es un directorio.")

    saved: list[Path] = []
    for source in sorted(source_dir.iterdir()):
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        if source.name.endswith((".part", ".ytdl")):
            continue

        source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        source_descriptor = os.open(source, source_flags)
        try:
            if not stat.S_ISREG(os.fstat(source_descriptor).st_mode):
                raise ValueError("El origen de descarga no es un archivo regular.")
            stem, suffix = source.stem, source.suffix
            for index in range(1000):
                name = f"{stem}{suffix}" if index == 0 else f"{stem} ({index}){suffix}"
                target = destination_dir / name
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                try:
                    descriptor = os.open(target, flags, 0o600)
                except FileExistsError:
                    continue
                try:
                    with os.fdopen(descriptor, "wb") as output, os.fdopen(source_descriptor, "rb") as incoming:
                        source_descriptor = -1
                        shutil.copyfileobj(incoming, output, length=1024 * 1024)
                        output.flush()
                        os.fsync(output.fileno())
                except Exception:
                    # Keep the exclusive target in place rather than unlinking a
                    # pathname that another local process might have replaced.
                    raise
                saved.append(target)
                break
            else:
                raise RuntimeError("No se ha encontrado un nombre de archivo libre.")
        finally:
            if source_descriptor >= 0:
                os.close(source_descriptor)
    return saved


MAX_PREFERENCES_BYTES = 1024 * 1024
PREFERENCE_STRING_KEYS = frozenset({
    "destination", "audio_format", "quality", "filename_style", "ydl_format",
    "output_template", "playlist_items", "limit_rate", "retries", "subtitle_langs",
})
PREFERENCE_BOOL_KEYS = frozenset({
    "playlist", "embed_thumbnail", "embed_metadata", "write_subtitles",
})


def sanitize_preferences(data: object) -> dict:
    """Keep only known, correctly typed, bounded preference values."""
    if not isinstance(data, dict):
        return {}
    clean = {}
    for key, value in data.items():
        if key in PREFERENCE_STRING_KEYS and isinstance(value, str) and len(value) <= 4096:
            clean[key] = value
        elif key in PREFERENCE_BOOL_KEYS and isinstance(value, bool):
            clean[key] = value
    return clean

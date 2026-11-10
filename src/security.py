"""Strict input and output-boundary validation shared by SOUNWD desktop code."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlsplit

YOUTUBE_HOSTS = frozenset({
    "youtube.com", "www.youtube.com", "music.youtube.com",
    "m.youtube.com", "youtu.be",
})
_ALLOWED_TEMPLATE_FIELDS = frozenset({
    "title", "uploader", "channel", "artist", "track",
    "ext", "id", "playlist_index",
})
_TEMPLATE_FIELD = re.compile(r"%\(([A-Za-z_][A-Za-z0-9_]*)\)s")
_TEMPLATE_LITERAL = re.compile(r"[A-Za-z0-9 _().-]*\Z")
_FORMAT_SELECTOR = re.compile(r"[A-Za-z0-9_./+\[\]()=,:-]{1,128}\Z")
_PLAYLIST_ITEMS = re.compile(r"[0-9, -]{1,100}\Z")
_RATE_LIMIT = re.compile(r"[1-9][0-9]{0,5}(?:K|M|G)?\Z", re.IGNORECASE)
_LANGUAGES = re.compile(r"[A-Za-z0-9,._-]{1,64}\Z")


def validate_youtube_url(value: str) -> str:
    """Accept only canonical HTTPS YouTube URLs; reject userinfo, ports and lookalikes."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("El enlace no es válido.")
    if value != value.strip() or any(ord(ch) < 32 or ch.isspace() for ch in value):
        raise ValueError("El enlace contiene espacios o caracteres de control.")
    if "\\" in value:
        raise ValueError("El enlace no es válido.")
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise ValueError("El enlace no es válido.") from exc
    if parsed.scheme.lower() != "https" or host not in YOUTUBE_HOSTS:
        raise ValueError("Usa un enlace HTTPS oficial de YouTube o YouTube Music.")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("No se permiten credenciales dentro del enlace.")
    if port not in (None, 443):
        raise ValueError("El enlace usa un puerto no permitido.")
    return value


def validate_output_template(template: str) -> str:
    """Permit one filename only; no directories, traversal, drive paths or unknown fields."""
    if not isinstance(template, str) or len(template) > 180:
        raise ValueError("La plantilla de nombre es demasiado larga.")
    template = template.strip()
    if not template:
        return "%(title)s.%(ext)s"
    if template.startswith(("/", "\\")) or "/" in template or "\\" in template:
        raise ValueError("La plantilla solo puede definir un nombre de archivo, no carpetas.")
    if any(ord(ch) < 32 for ch in template) or ":" in template or ".." in template:
        raise ValueError("La plantilla contiene una ruta o caracteres no permitidos.")
    fields = _TEMPLATE_FIELD.findall(template)
    if any(field not in _ALLOWED_TEMPLATE_FIELDS for field in fields):
        raise ValueError("La plantilla contiene un campo de yt-dlp no permitido.")
    literal = _TEMPLATE_FIELD.sub("X", template)
    if "%" in literal or not _TEMPLATE_LITERAL.fullmatch(literal):
        raise ValueError("La plantilla contiene caracteres o expresiones no permitidos.")
    if template.endswith((" ", ".")):
        raise ValueError("El nombre no puede terminar en espacio o punto.")
    stem = template.split(".", 1)[0].upper()
    if stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        raise ValueError("La plantilla utiliza un nombre de archivo reservado.")
    return template


def build_output_path(destination: Path, template: str) -> Path:
    """Resolve the user-selected destination, then confine output to that directory."""
    requested_root = Path(destination).expanduser()
    if requested_root.is_symlink():
        raise ValueError("La carpeta de destino no puede ser un enlace simbólico.")
    root = requested_root.resolve()
    if root.exists() and not root.is_dir():
        raise ValueError("La carpeta de destino no es un directorio.")
    safe_name = validate_output_template(template)
    target = (root / safe_name).resolve()
    if target.parent != root:
        raise ValueError("La ruta de salida intenta salir de la carpeta elegida.")
    return target


def validate_advanced_options(options: dict) -> dict:
    """Validate every free-form advanced field before passing it to yt-dlp."""
    clean = dict(options)
    selector = (clean.get("format") or "").strip()
    if selector and (not _FORMAT_SELECTOR.fullmatch(selector)
                     or "://" in selector.lower()
                     or selector.lower().startswith(("http", "ftp"))
                     or ".." in selector):
        raise ValueError("El selector de formato contiene caracteres no permitidos.")
    clean["format"] = selector
    clean["outtmpl"] = validate_output_template(clean.get("outtmpl", ""))
    items = (clean.get("playlist_items") or "").strip()
    if items and not _PLAYLIST_ITEMS.fullmatch(items):
        raise ValueError("Los elementos de lista deben ser números y rangos separados por comas.")
    clean["playlist_items"] = items
    rate = (clean.get("ratelimit") or "").strip()
    if rate and not _RATE_LIMIT.fullmatch(rate):
        raise ValueError("El límite de velocidad debe ser, por ejemplo, 500K o 2M.")
    clean["ratelimit"] = rate
    retries = (clean.get("retries") or "").strip()
    if retries:
        if not retries.isdecimal() or not 0 <= int(retries) <= 20:
            raise ValueError("Los reintentos deben estar entre 0 y 20.")
        clean["retries"] = int(retries)
    else:
        clean["retries"] = None
    languages = (clean.get("subtitleslangs") or "").strip()
    if languages and not _LANGUAGES.fullmatch(languages):
        raise ValueError("Los idiomas de subtítulos contienen caracteres no permitidos.")
    clean["subtitleslangs"] = languages
    return clean


def is_path_within(path: Path, directory: Path) -> bool:
    """Return True only for a regular, non-symlink file inside directory."""
    try:
        candidate = Path(path)
        if candidate.is_symlink():
            return False
        resolved = candidate.resolve(strict=True)
        root = Path(directory).resolve(strict=True)
        return resolved.is_file() and resolved.is_relative_to(root)
    except (OSError, RuntimeError, ValueError):
        return False

"""Strict URL and option validation for the legacy Kivy Android downloader."""
from __future__ import annotations

import re
from urllib.parse import urlparse

_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "music.youtube.com",
    "m.youtube.com",
    "youtu.be",
}
_ALLOWED_TEMPLATE_FIELDS = {
    "title", "id", "uploader", "channel", "playlist", "playlist_index", "ext"
}
_TEMPLATE_TOKEN = re.compile(r"%\(([^)]+)\)s")


def is_supported_youtube_url(value: str) -> bool:
    if not isinstance(value, str) or not value or len(value) > 2048:
        return False
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return False
    try:
        parsed = urlparse(value.strip())
        return (
            parsed.scheme == "https"
            and (parsed.hostname or "").lower() in _HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and not parsed.fragment
        )
    except (ValueError, AttributeError):
        return False


def safe_output_template(value: str) -> str:
    value = (value or "").strip() or "%(title)s.%(ext)s"
    if len(value) > 200 or "/" in value or "\\" in value or ".." in value:
        raise ValueError("La plantilla solo puede definir un nombre de archivo, no una ruta.")
    tokens = _TEMPLATE_TOKEN.findall(value)
    if any(token not in _ALLOWED_TEMPLATE_FIELDS for token in tokens):
        raise ValueError("La plantilla contiene campos de yt-dlp no permitidos.")
    remainder = _TEMPLATE_TOKEN.sub("", value)
    if "%" in remainder or re.search(r'[<>:"|?*\x00-\x1f]', remainder):
        raise ValueError("La plantilla contiene caracteres no permitidos.")
    if value.endswith((".", " ")):
        raise ValueError("El nombre no puede terminar en punto o espacio.")
    return value


def validate_advanced_options(options: dict) -> None:
    safe_output_template(options.get("output_template", ""))
    retries = options.get("retries", "")
    if retries and (not str(retries).isdigit() or int(retries) > 20):
        raise ValueError("Los reintentos deben estar entre 0 y 20.")
    rate = options.get("limit_rate", "")
    if rate and not re.fullmatch(r"\d+(?:\.\d+)?[KMG]?", rate, re.I):
        raise ValueError("El límite de velocidad debe ser un valor como 500K o 2M.")
    playlist_items = options.get("playlist_items", "")
    if playlist_items and not re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", playlist_items):
        raise ValueError("La selección de elementos de lista no tiene un formato válido.")
    selector = options.get("ydl_format", "")
    if selector and (len(selector) > 128 or not re.fullmatch(r"[A-Za-z0-9._,+/\[\](){}=<>!&|^-]+", selector)):
        raise ValueError("El selector de formato contiene caracteres no permitidos.")
    languages = options.get("subtitle_langs", "")
    if languages and not re.fullmatch(r"[A-Za-z0-9,_-]{1,64}", languages):
        raise ValueError("La lista de idiomas de subtítulos no tiene un formato válido.")

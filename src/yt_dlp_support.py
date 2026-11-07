"""yt-dlp runtime helpers shared by the desktop GUI and CLI."""
from __future__ import annotations
import shutil
import sys
from pathlib import Path

def youtube_runtime_options() -> dict:
    """Return an explicit Deno path, including when running as a PyInstaller bundle."""
    executable = "deno.exe" if sys.platform.startswith("win") else "deno"
    candidates = []
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if bundle_dir:
        candidates.append(Path(bundle_dir) / executable)
    executable_dir = Path(sys.executable).resolve().parent
    candidates.extend((executable_dir / executable, executable_dir / "bin" / executable))
    for candidate in candidates:
        if candidate.is_file():
            return {"js_runtimes": {"deno": {"path": str(candidate)}}}
    installed = shutil.which("deno")
    if installed:
        return {"js_runtimes": {"deno": {"path": installed}}}
    raise RuntimeError(
        "Falta el motor JavaScript Deno, necesario para descargar de YouTube. "
        "Usa la aplicación de escritorio compilada de SOUNWD o instala Deno 2.3 o posterior."
    )

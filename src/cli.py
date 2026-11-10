from __future__ import annotations

import sys
from pathlib import Path

import yt_dlp
import imageio_ffmpeg
from yt_dlp_support import youtube_runtime_options
from security import build_output_path, validate_youtube_url
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, BarColumn, DownloadColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

console = Console()
APP_NAME = "MUSIC DOWNLOADER"
DEFAULT_FOLDER = Path.home() / "Music" / "Music Downloader"
SUPPORTED_HOSTS = {"youtube.com", "www.youtube.com", "music.youtube.com", "m.youtube.com", "youtu.be"}


def show_header() -> None:
    console.clear()
    console.print(
        Panel.fit(
            "[bold bright_magenta]♫ MUSIC DOWNLOADER[/bold bright_magenta]\n"
            "[dim]Descargas de audio sencillas · Windows & Linux[/dim]",
            border_style="bright_magenta",
            padding=(1, 5),
        )
    )


def is_supported_url(value: str) -> bool:
    try:
        validate_youtube_url(value)
        return True
    except ValueError:
        return False


def choose_format() -> tuple[str, str]:
    table = Table(title="Formato de audio", box=box.ROUNDED, border_style="cyan")
    table.add_column("Opción", style="bold cyan", justify="center")
    table.add_column("Formato", style="bold")
    table.add_column("Cuándo elegirlo")
    table.add_row("1", "MP3", "Muy compatible; buena opción general")
    table.add_row("2", "M4A (AAC)", "Buena calidad con archivos compactos")
    table.add_row("3", "FLAC", "Sin pérdidas adicionales al convertir")
    table.add_row("4", "OPUS", "Códec eficiente; compatibilidad variable")
    table.add_row("5", "WAV", "Útil para edición; ocupa bastante")
    console.print(table)
    choice = Prompt.ask("Elige formato", choices=["1", "2", "3", "4", "5"], default="2")
    return {"1": ("mp3", "MP3"), "2": ("m4a", "M4A"), "3": ("flac", "FLAC"),
            "4": ("opus", "OPUS"), "5": ("wav", "WAV")}[choice]


def choose_destination() -> Path:
    console.print(f"\n[dim]Carpeta predeterminada:[/dim] [cyan]{DEFAULT_FOLDER}[/cyan]")
    if Confirm.ask("¿Quieres usar esta carpeta?", default=True):
        destination = DEFAULT_FOLDER
    else:
        raw = Prompt.ask("Escribe la ruta de la carpeta")
        destination = Path(raw.strip().strip('"')).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def download_audio(url: str, audio_format: str, destination: Path, is_playlist: bool) -> None:
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
    )
    task_id = progress.add_task("Preparando descarga…", total=None)

    def progress_hook(data: dict) -> None:
        status = data.get("status")
        if status == "downloading":
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes", 0)
            progress.update(task_id, total=total, completed=downloaded,
                            description="Descargando audio…")
        elif status == "finished":
            progress.update(task_id, description="Convirtiendo audio…")

    options = {
        **youtube_runtime_options(),
        "format": "bestaudio/best",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "outtmpl": str(build_output_path(destination, "%(title)s.%(ext)s")),
        "noplaylist": not is_playlist,
        "windowsfilenames": True,
        "overwrites": False,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": audio_format,
             "preferredquality": "0"},
            {"key": "FFmpegMetadata"},
        ],
    }

    with progress:
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([url])
        progress.update(task_id, completed=1, total=1, description="[green]¡Descarga terminada![/green]")


def main() -> int:
    show_header()
    console.print("[bold]¡Hola![/bold] Vamos a preparar tu descarga.\n")
    console.print("[yellow]Nota:[/yellow] utiliza esta herramienta solo con contenido que tengas derecho a descargar.")
    console.print("[dim]Este programa acepta enlaces de YouTube y YouTube Music; no descarga desde Spotify.\n[/dim]")

    url = Prompt.ask("[bold]Pega el enlace de YouTube o YouTube Music[/bold]").strip()
    if not is_supported_url(url):
        console.print("\n[red]Ese enlace no parece ser de YouTube o YouTube Music.[/red]")
        Prompt.ask("Pulsa Enter para salir", default="")
        return 1

    is_playlist = Confirm.ask("¿Es una lista de reproducción y quieres descargar sus pistas?", default=False)
    audio_format, label = choose_format()
    try:
        destination = choose_destination()
    except OSError as error:
        console.print(f"\n[red]No se puede preparar la carpeta de destino:[/red] {error}")
        return 1

    console.print(Panel(
        f"[bold]Formato:[/bold] {label}\n[bold]Destino:[/bold] {destination}\n"
        f"[bold]Lista de reproducción:[/bold] {'Sí' if is_playlist else 'No'}",
        title="Revisa tu descarga", border_style="green",
    ))
    if not Confirm.ask("¿Empezamos?", default=True):
        console.print("[yellow]Descarga cancelada.[/yellow]")
        return 0

    try:
        download_audio(url, audio_format, destination, is_playlist)
        console.print(f"\n[bold green]Listo.[/bold green] Tus archivos están en:\n[cyan]{destination}[/cyan]")
        return 0
    except yt_dlp.utils.DownloadError as error:
        console.print(f"\n[red]No se pudo completar la descarga:[/red] {error}")
        console.print("[dim]Comprueba el enlace, tu conexión y que FFmpeg esté instalado.[/dim]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Descarga interrumpida por el usuario.[/yellow]")
        return 130
    except Exception as error:
        console.print(f"\n[red]Ha ocurrido un error inesperado:[/red] {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

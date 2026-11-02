from __future__ import annotations

import queue
import threading
from pathlib import Path
from urllib.parse import urlparse

import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox


APP_TITLE = "SONORA"
DEFAULT_FOLDER = Path.home() / "Music" / "Sonora"
SUPPORTED_HOSTS = {
    "youtube.com", "www.youtube.com", "music.youtube.com",
    "m.youtube.com", "youtu.be",
}
FORMATS = {
    "MP3": "mp3",
    "M4A · AAC": "m4a",
    "FLAC": "flac",
    "OPUS": "opus",
    "WAV": "wav",
}


def valid_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return (
            parsed.scheme in {"http", "https"}
            and (parsed.hostname or "").lower() in SUPPORTED_HOSTS
        )
    except ValueError:
        return False


class SonoraApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Sonora · Music Downloader")
        self.geometry("980x720")
        self.minsize(840, 650)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#0B0D14")

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.downloading = False
        self.destination = ctk.StringVar(value=str(DEFAULT_FOLDER))
        self.audio_format = ctk.StringVar(value="M4A · AAC")
        self.playlist = ctk.BooleanVar(value=False)

        self._build_ui()
        self.after(120, self._process_events)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#10131D")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=25, pady=(34, 38))
        ctk.CTkLabel(
            brand, text="♫", font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#A78BFA",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand, text="SONORA", font=ctk.CTkFont(size=23, weight="bold"),
            text_color="#F5F3FF",
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            brand, text="MUSIC DOWNLOADER", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#777C91",
        ).pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(
            sidebar, text="TU ESPACIO", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#777C91",
        ).pack(anchor="w", padx=25, pady=(0, 12))
        self._nav_item(sidebar, "↓   Descargar", active=True)
        self._nav_item(sidebar, "♫   Tu biblioteca", active=False)

        sidebar_bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=22, pady=24)
        ctk.CTkLabel(
            sidebar_bottom, text="Hecho para disfrutar\nde la música.",
            justify="left", text_color="#777C91",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w")
        ctk.CTkLabel(
            sidebar_bottom, text="SONORA  ·  v0.2",
            text_color="#555B70", font=ctk.CTkFont(size=10),
        ).pack(anchor="w", pady=(15, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=42, pady=34)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content, text="Tu música, a tu manera.",
            font=ctk.CTkFont(size=30, weight="bold"), text_color="#F4F1FF",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            content, text="Pega un enlace y nosotros nos encargamos del resto.",
            font=ctk.CTkFont(size=13), text_color="#9297AA",
        ).grid(row=1, column=0, sticky="w", pady=(6, 25))

        link_card = self._card(content, 2)
        ctk.CTkLabel(
            link_card, text="01  ·  ENLACE",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#A78BFA",
        ).pack(anchor="w", padx=22, pady=(19, 10))
        self.url_entry = ctk.CTkEntry(
            link_card, height=48, corner_radius=12,
            placeholder_text="https://www.youtube.com/watch?v=…",
            border_color="#303448", fg_color="#141826",
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.pack(fill="x", padx=22, pady=(0, 18))

        options = ctk.CTkFrame(content, fg_color="transparent")
        options.grid(row=3, column=0, sticky="ew", pady=16)
        options.grid_columnconfigure((0, 1), weight=1)

        format_card = self._card(options, 0)
        ctk.CTkLabel(
            format_card, text="02  ·  FORMATO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#A78BFA",
        ).pack(anchor="w", padx=20, pady=(18, 9))
        ctk.CTkOptionMenu(
            format_card, variable=self.audio_format, values=list(FORMATS),
            height=42, corner_radius=10, fg_color="#292341",
            button_color="#7255C7", button_hover_color="#886CE0",
            dropdown_fg_color="#191D2B",
        ).pack(fill="x", padx=20, pady=(0, 18))

        dest_card = self._card(options, 1)
        ctk.CTkLabel(
            dest_card, text="03  ·  CARPETA DE DESTINO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#A78BFA",
        ).pack(anchor="w", padx=20, pady=(18, 9))
        dest_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=20, pady=(0, 18))
        self.dest_label = ctk.CTkLabel(
            dest_row, text=self._short_path(self.destination.get()),
            text_color="#C8CAD6", font=ctk.CTkFont(size=11), anchor="w",
        )
        self.dest_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            dest_row, text="Elegir", width=70, height=34,
            corner_radius=9, fg_color="#292341", hover_color="#403260",
            command=self._choose_folder,
        ).pack(side="right", padx=(8, 0))

        playlist_row = ctk.CTkFrame(content, fg_color="transparent")
        playlist_row.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkCheckBox(
            playlist_row, text="Es una lista de reproducción",
            variable=self.playlist, font=ctk.CTkFont(size=12),
            text_color="#C8CAD6", fg_color="#8063D5",
            hover_color="#9B82E8", border_color="#555B70",
        ).pack(side="left")

        action_card = self._card(content, 5)
        ctk.CTkLabel(
            action_card, text="TODO LISTO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#A78BFA",
        ).pack(anchor="w", padx=22, pady=(18, 5))
        self.status_label = ctk.CTkLabel(
            action_card, text="Preparado para empezar",
            text_color="#9297AA", font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(anchor="w", padx=22, pady=(0, 12))
        self.progress = ctk.CTkProgressBar(
            action_card, height=8, corner_radius=8,
            progress_color="#9B7AF4", fg_color="#282B3A",
        )
        self.progress.pack(fill="x", padx=22, pady=(0, 16))
        self.progress.set(0)
        self.download_button = ctk.CTkButton(
            action_card, text="↓   Descargar audio", height=48,
            corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8063D5", hover_color="#9679E8",
            command=self._start_download,
        )
        self.download_button.pack(fill="x", padx=22, pady=(0, 20))

        ctk.CTkLabel(
            content,
            text="Descarga únicamente contenido que tengas derecho a guardar.\n"
                 "Sonora usa yt-dlp y no descarga música desde Spotify.",
            text_color="#666C80", justify="left",
            font=ctk.CTkFont(size=10),
        ).grid(row=6, column=0, sticky="w", pady=(16, 0))

    def _nav_item(self, parent: ctk.CTkFrame, text: str, active: bool) -> None:
        ctk.CTkLabel(
            parent, text=text, height=42, corner_radius=10, anchor="w",
            padx=14, fg_color="#252039" if active else "transparent",
            text_color="#E9E4FF" if active else "#858A9D",
            font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
        ).pack(fill="x", padx=14, pady=3)

    def _card(self, parent: ctk.CTkBaseClass, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, corner_radius=16, fg_color="#151927",
            border_width=1, border_color="#252B3B",
        )
        if isinstance(parent, ctk.CTk):
            card.grid(row=row, column=0, sticky="ew")
        elif parent is not None and parent.winfo_class() == "CTkFrame":
            if row == 0:
                card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
            else:
                card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        return card

    @staticmethod
    def _short_path(value: str) -> str:
        path = Path(value)
        parts = path.parts
        if len(parts) > 3:
            return "…/" + "/".join(parts[-2:])
        return str(path)

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.destination.get())
        if selected:
            self.destination.set(selected)
            self.dest_label.configure(text=self._short_path(selected))

    def _start_download(self) -> None:
        if self.downloading:
            return
        url = self.url_entry.get().strip()
        if not valid_url(url):
            messagebox.showwarning(
                "Enlace no válido",
                "Pega un enlace válido de YouTube o YouTube Music.",
            )
            return

        if not self.playlist.get() and "list=" in url and "watch?v=" not in url:
            if not messagebox.askyesno(
                "Parece una lista",
                "El enlace parece ser una lista de reproducción. ¿Quieres descargarla completa?",
            ):
                return
            self.playlist.set(True)

        destination = Path(self.destination.get()).expanduser()
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Carpeta no disponible", str(error))
            return

        if not self._ffmpeg_available():
            messagebox.showerror(
                "Falta FFmpeg",
                "Para convertir el audio necesitas instalar FFmpeg y ffprobe "
                "y añadirlos al PATH del sistema.",
            )
            return

        self.downloading = True
        self.download_button.configure(state="disabled", text="Descargando…")
        self.progress.set(0)
        self.status_label.configure(text="Conectando y preparando la descarga…")
        thread = threading.Thread(
            target=self._download_worker,
            args=(url, FORMATS[self.audio_format.get()], destination, self.playlist.get()),
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _ffmpeg_available() -> bool:
        import shutil
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    def _download_worker(self, url: str, audio_format: str, destination: Path, playlist: bool) -> None:
        def hook(data: dict) -> None:
            status = data.get("status")
            if status == "downloading":
                downloaded = data.get("downloaded_bytes", 0)
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                fraction = downloaded / total if total else 0
                self.events.put(("progress", (min(max(fraction, 0), 1), "Descargando audio…")))
            elif status == "finished":
                self.events.put(("progress", (0.98, "Convirtiendo formato…")))

        options = {
            "format": "bestaudio/best",
            "outtmpl": str(destination / "%(title)s.%(ext)s"),
            "noplaylist": not playlist,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": audio_format, "preferredquality": "0"},
                {"key": "FFmpegMetadata"},
            ],
        }
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                result = downloader.download([url])
            if result:
                raise yt_dlp.utils.DownloadError("yt-dlp no pudo completar la descarga.")
            self.events.put(("done", str(destination)))
        except Exception as error:
            self.events.put(("error", str(error)))

    def _process_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    fraction, label = payload
                    self.progress.set(fraction)
                    self.status_label.configure(text=label)
                elif kind == "done":
                    self.downloading = False
                    self.progress.set(1)
                    self.status_label.configure(text="¡Descarga terminada! Tus archivos están listos.")
                    self.download_button.configure(state="normal", text="↓   Descargar otra vez")
                    messagebox.showinfo("¡Todo listo!", f"Tu audio está guardado en:\n{payload}")
                elif kind == "error":
                    self.downloading = False
                    self.status_label.configure(text="No se pudo completar la descarga.")
                    self.download_button.configure(state="normal", text="↓   Intentar de nuevo")
                    messagebox.showerror(
                        "Error en la descarga",
                        f"{payload}\n\nComprueba el enlace, tu conexión y que FFmpeg esté instalado.",
                    )
        except queue.Empty:
            pass
        self.after(120, self._process_events)


def main() -> None:
    app = SonoraApp()
    app.mainloop()


if __name__ == "__main__":
    main()

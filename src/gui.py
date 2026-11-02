from __future__ import annotations

import queue
import threading
from pathlib import Path
from urllib.parse import urlparse

import customtkinter as ctk
import yt_dlp
from tkinter import filedialog, messagebox


APP_TITLE = "SOUNWD"
DEFAULT_FOLDER = Path.home() / "Music" / "SOUNWD"
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


class SoundwApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SOUNWD · Your sound. Your moments.")
        self.geometry("1000x740")
        self.minsize(860, 680)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color="#11111A")

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

        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#191824")
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=25, pady=(34, 38))
        ctk.CTkLabel(
            brand, text="♫", font=ctk.CTkFont(size=34, weight="bold"),
            text_color="#C6B5E8",
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand, text="SONORA", font=ctk.CTkFont(size=23, weight="bold"),
            text_color="#F5F3FF",
        ).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(
            brand, text="YOUR PERSONAL SOUNDSPACE", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#898294",
        ).pack(anchor="w", pady=(1, 0))

        ctk.CTkLabel(
            sidebar, text="TU ESPACIO", font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#898294",
        ).pack(anchor="w", padx=25, pady=(0, 12))
        self._nav_item(sidebar, "↓   Descargar", active=True)
        self._nav_item(sidebar, "♫   Tu biblioteca", active=False)

        sidebar_bottom = ctk.CTkFrame(sidebar, fg_color="transparent")
        sidebar_bottom.pack(side="bottom", fill="x", padx=22, pady=24)
        ctk.CTkLabel(
            sidebar_bottom, text="Hecho para disfrutar\nde la música.",
            justify="left", text_color="#898294",
            font=ctk.CTkFont(size=12),
        ).pack(anchor="w")
        ctk.CTkLabel(
            sidebar_bottom, text="SOUNWD  ·  v0.3",
            text_color="#716A7B", font=ctk.CTkFont(size=10),
        ).pack(anchor="w", pady=(15, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew", padx=42, pady=34)
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content, text="Tu sonido. Tus momentos.",
            font=ctk.CTkFont(size=30, weight="bold"), text_color="#F2EDF8",
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            content, text="Guarda los sonidos que acompañan tus días.",
            font=ctk.CTkFont(size=13), text_color="#AAA3B5",
        ).grid(row=1, column=0, sticky="w", pady=(6, 25))

        link_card = self._card(content, 2)
        ctk.CTkLabel(
            link_card, text="01  ·  ENLACE DE AUDIO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#C6B5E8",
        ).pack(anchor="w", padx=22, pady=(19, 10))
        self.url_entry = ctk.CTkEntry(
            link_card, height=48, corner_radius=12,
            placeholder_text="https://www.youtube.com/watch?v=…",
            border_color="#3B3549", fg_color="#191824",
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.pack(fill="x", padx=22, pady=(0, 18))

        options = ctk.CTkFrame(content, fg_color="transparent")
        options.grid(row=3, column=0, sticky="ew", pady=16)
        options.grid_columnconfigure((0, 1), weight=1)

        format_card = self._card(options, 0, in_columns=True)
        ctk.CTkLabel(
            format_card, text="02  ·  FORMATO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#C6B5E8",
        ).pack(anchor="w", padx=20, pady=(18, 9))
        ctk.CTkOptionMenu(
            format_card, variable=self.audio_format, values=list(FORMATS),
            height=42, corner_radius=10, fg_color="#30283D",
            button_color="#8872AE", button_hover_color="#A08AC5",
            dropdown_fg_color="#191D2B",
        ).pack(fill="x", padx=20, pady=(0, 18))

        dest_card = self._card(options, 1, in_columns=True)
        ctk.CTkLabel(
            dest_card, text="03  ·  DÓNDE GUARDARLO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#C6B5E8",
        ).pack(anchor="w", padx=20, pady=(18, 9))
        dest_row = ctk.CTkFrame(dest_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=20, pady=(0, 18))
        self.dest_label = ctk.CTkLabel(
            dest_row, text=self._short_path(self.destination.get()),
            text_color="#D2CBD9", font=ctk.CTkFont(size=11), anchor="w",
        )
        self.dest_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            dest_row, text="Elegir", width=70, height=34,
            corner_radius=9, fg_color="#30283D", hover_color="#4A405B",
            command=self._choose_folder,
        ).pack(side="right", padx=(8, 0))

        playlist_row = ctk.CTkFrame(content, fg_color="transparent")
        playlist_row.grid(row=4, column=0, sticky="ew", pady=(0, 15))
        ctk.CTkCheckBox(
            playlist_row, text="Es una lista de reproducción",
            variable=self.playlist, font=ctk.CTkFont(size=12),
            text_color="#D2CBD9", fg_color="#8872AE",
            hover_color="#9B82E8", border_color="#716A7B",
        ).pack(side="left")

        action_card = self._card(content, 5)
        ctk.CTkLabel(
            action_card, text="A TU RITMO",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#C6B5E8",
        ).pack(anchor="w", padx=22, pady=(18, 5))
        self.status_label = ctk.CTkLabel(
            action_card, text="Cuando quieras, empezamos.",
            text_color="#AAA3B5", font=ctk.CTkFont(size=12),
        )
        self.status_label.pack(anchor="w", padx=22, pady=(0, 12))
        self.progress = ctk.CTkProgressBar(
            action_card, height=8, corner_radius=8,
            progress_color="#B5A0D7", fg_color="#373242",
        )
        self.progress.pack(fill="x", padx=22, pady=(0, 16))
        self.progress.set(0)
        self.download_button = ctk.CTkButton(
            action_card, text="↓   Guardar mi música", height=48,
            corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#8872AE", hover_color="#A08AC5",
            command=self._start_download,
        )
        self.download_button.pack(fill="x", padx=22, pady=(0, 20))

        ctk.CTkLabel(
            content,
            text="Descarga únicamente contenido que tengas derecho a guardar.\n"
                 "Sonora usa yt-dlp y no descarga música desde Spotify.",
            text_color="#898294", justify="left",
            font=ctk.CTkFont(size=10),
        ).grid(row=6, column=0, sticky="w", pady=(16, 0))

    def _nav_item(self, parent: ctk.CTkFrame, text: str, active: bool) -> None:
        ctk.CTkLabel(
            parent, text=text, height=42, corner_radius=10, anchor="w",
            padx=14, fg_color="#30283D" if active else "transparent",
            text_color="#F2EDF8" if active else "#A39BAC",
            font=ctk.CTkFont(size=13, weight="bold" if active else "normal"),
        ).pack(fill="x", padx=14, pady=3)

    def _card(self, parent: ctk.CTkFrame, row: int, in_columns: bool = False) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, corner_radius=16, fg_color="#201E2B",
            border_width=1, border_color="#302C3B",
        )
        if in_columns:
            card.grid(row=0, column=row, sticky="nsew",
                      padx=(0, 8) if row == 0 else (8, 0))
        else:
            card.grid(row=row, column=0, sticky="ew")
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
                "Pega un enlace válido de YouTube o YouTube Music para continuar.",
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
            "ffmpeg_location": __import__("imageio_ffmpeg").get_ffmpeg_exe(),
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
                        f"{payload}\n\nComprueba el enlace y tu conexión a Internet."
                    )
        except queue.Empty:
            pass
        self.after(120, self._process_events)


def main() -> None:
    app = SoundwApp()
    app.mainloop()


if __name__ == "__main__":
    main()

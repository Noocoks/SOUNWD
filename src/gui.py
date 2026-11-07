from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlparse
from tkinter import filedialog, messagebox

import customtkinter as ctk
import imageio_ffmpeg
import yt_dlp


APP_NAME = "SOUNWD"
DEFAULT_FOLDER = Path.home() / "Downloads"
if os.name == "nt":
    CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "SOUNWD"
else:
    CONFIG_DIR = Path.home() / ".config" / "SOUNWD"
PREFERENCES_FILE = CONFIG_DIR / "preferences.json"
FORMATS = {"MP3 (recomendado)": "mp3", "M4A": "m4a", "FLAC": "flac", "OPUS": "opus", "WAV": "wav"}
SUPPORTED_HOSTS = {"youtube.com", "www.youtube.com", "music.youtube.com", "m.youtube.com", "youtu.be"}
def valid_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower()
        return parsed.scheme in {"http", "https"} and (
            host in SUPPORTED_HOSTS or any(host.endswith("." + item) for item in SUPPORTED_HOSTS)
        )
    except ValueError:
        return False


class SoundwApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SOUNWD · Tu sonido. Tus momentos.")
        self.geometry("820x780")
        self.minsize(520, 460)
        self.configure(fg_color="#12111A")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.downloading = False
        self.advanced_visible = False
        preferences = self._load_preferences()
        self.destination = ctk.StringVar(value=preferences.get("destination", str(DEFAULT_FOLDER)))
        self.audio_format = ctk.StringVar(value=preferences.get("audio_format", "MP3 (recomendado)"))
        self.playlist = ctk.BooleanVar(value=preferences.get("playlist", False))
        self.quality = ctk.StringVar(value=preferences.get("quality", "Máxima"))
        self.filename_style = ctk.StringVar(value=preferences.get("filename_style", "Solo título"))
        self.ydl_format = ctk.StringVar(value=preferences.get("ydl_format", ""))
        self.output_template = ctk.StringVar(value=preferences.get("output_template", ""))
        self.playlist_items = ctk.StringVar(value=preferences.get("playlist_items", ""))
        self.limit_rate = ctk.StringVar(value=preferences.get("limit_rate", ""))
        self.retries = ctk.StringVar(value=preferences.get("retries", ""))
        self.subtitle_langs = ctk.StringVar(value=preferences.get("subtitle_langs", ""))
        self.embed_thumbnail = ctk.BooleanVar(value=preferences.get("embed_thumbnail", False))
        self.embed_metadata = ctk.BooleanVar(value=preferences.get("embed_metadata", True))
        self.write_subtitles = ctk.BooleanVar(value=preferences.get("write_subtitles", False))
        if self.audio_format.get() not in FORMATS:
            self.audio_format.set("MP3 (recomendado)")
        if self.quality.get() not in {"Máxima", "Alta", "Normal"}:
            self.quality.set("Máxima")
        if self.filename_style.get() not in {"Solo título", "Título y canal"}:
            self.filename_style.set("Solo título")

        self._build_ui()
        self.bind("<Configure>", self._responsive_layout)
        # La barra no se muestra; el desplazamiento se controla con la rueda.
        self.page._scrollbar.grid_remove()
        self.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_mousewheel_linux, add="+")
        self.bind_all("<Button-5>", self._on_mousewheel_linux, add="+")
        self.after(80, self._responsive_layout)
        self.after(120, self._process_events)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        page = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0, scrollbar_button_color="#554766", scrollbar_button_hover_color="#8872AE")
        self.page = page
        page.grid(row=0, column=0, sticky="nsew", padx=24, pady=22)
        page.grid_columnconfigure(0, weight=1)
        # El canvas debe ocupar al menos la altura visible para poder centrar.
        page._parent_canvas.bind("<Configure>", lambda _event: self.after_idle(self._center_content))

        # Filas vacías superior e inferior: absorben el espacio sobrante.
        page._parent_frame.grid_rowconfigure(0, weight=1)
        page._parent_frame.grid_rowconfigure(10, weight=1)

        brand = ctk.CTkFrame(page, fg_color="transparent")
        brand.grid(row=2, column=0, sticky="ew", pady=(0, 28))
        ctk.CTkLabel(brand, text="◖♪", text_color="#C8B6E8",
                     font=ctk.CTkFont(size=30, weight="bold")).pack()
        ctk.CTkLabel(brand, text="SOUNWD.", text_color="#F4EFFA",
                     font=ctk.CTkFont(size=27, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(brand, text="YOUR SOUND. YOUR MOMENTS.",
                     text_color="#A69CAF", font=ctk.CTkFont(size=10, weight="bold")).pack()

        ctk.CTkLabel(page, text="Tu música. Tu espacio. Tu estilo.",
                     text_color="#F4EFFA", font=ctk.CTkFont(size=25, weight="bold")
                     ).grid(row=2, column=0, pady=(0, 7))
        ctk.CTkLabel(page, text="Un lugar tranquilo para guardar los sonidos que te acompañan.",
                     text_color="#B6ADBF", font=ctk.CTkFont(size=13)
                     ).grid(row=3, column=0, pady=(0, 24))

        link_card = ctk.CTkFrame(page, fg_color="#211E2B", corner_radius=18,
                                 border_width=1, border_color="#332D40")
        link_card.grid(row=4, column=0, sticky="ew", pady=(0, 14))
        link_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(link_card, text="1.  PEGA AQUÍ EL ENLACE",
                     text_color="#C9B8E8", font=ctk.CTkFont(size=11, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 8))
        self.url_entry = ctk.CTkEntry(
            link_card, height=52, corner_radius=12,
            placeholder_text="Copia el enlace de YouTube y pégalo aquí",
            border_color="#443B53", fg_color="#17151F",
            text_color="#F4EFFA", placeholder_text_color="#8E8499",
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.url_entry.bind("<Return>", lambda _event: self._start_download())
        link_actions = ctk.CTkFrame(link_card, fg_color="transparent")
        link_actions.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 14))
        ctk.CTkButton(
            link_actions, text="Pegar enlace", width=110, height=30,
            fg_color="#40364F", hover_color="#554766",
            command=self._paste_url,
        ).pack(side="left")
        ctk.CTkButton(
            link_actions, text="Limpiar", width=76, height=30,
            fg_color="transparent", hover_color="#302A3A",
            text_color="#CDBFE0", command=lambda: self.url_entry.delete(0, "end"),
        ).pack(side="left", padx=(8, 0))

        settings = ctk.CTkFrame(page, fg_color="transparent")
        self.settings = settings
        settings.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        settings.grid_columnconfigure((0, 1), weight=1, uniform="settings")

        format_card = ctk.CTkFrame(settings, fg_color="#211E2B", corner_radius=14,
                                   border_width=1, border_color="#332D40")
        format_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(format_card, text="2.  FORMATO DEL ARCHIVO",
                     text_color="#C9B8E8", font=ctk.CTkFont(size=10, weight="bold")
                     ).pack(anchor="w", padx=14, pady=(13, 6))
        ctk.CTkOptionMenu(
            format_card, variable=self.audio_format, values=list(FORMATS),
            command=self._preference_changed,
            height=38, corner_radius=10, fg_color="#40364F",
            button_color="#8872AE", button_hover_color="#9B86BB",
            dropdown_fg_color="#211E2B",
        ).pack(fill="x", padx=12, pady=(0, 13))

        folder_card = ctk.CTkFrame(settings, fg_color="#211E2B", corner_radius=14,
                                   border_width=1, border_color="#332D40")
        folder_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(folder_card, text="3.  CARPETA DE DESCARGA",
                     text_color="#C9B8E8", font=ctk.CTkFont(size=10, weight="bold")
                     ).pack(anchor="w", padx=14, pady=(13, 6))
        folder_row = ctk.CTkFrame(folder_card, fg_color="transparent")
        folder_row.pack(fill="x", padx=12, pady=(0, 13))
        folder_row.grid_columnconfigure(0, weight=1)
        self.folder_label = ctk.CTkLabel(
            folder_row, text=self._short_path(str(self.destination.get())),
            text_color="#D2CBD9", font=ctk.CTkFont(size=10), anchor="w",
        )
        self.folder_label.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            folder_row, text="Elegir", width=66, height=34,
            fg_color="#40364F", hover_color="#554766",
            command=self._choose_folder,
        ).grid(row=0, column=1, padx=(6, 0))

        self.playlist_check = ctk.CTkCheckBox(
            page, text="Descargar la lista completa si el enlace contiene una",
            variable=self.playlist, command=self._save_preferences,
            text_color="#C8BED2", fg_color="#8872AE", hover_color="#9B86BB",
            font=ctk.CTkFont(size=11),
        )
        self.playlist_check.grid(row=6, column=0, sticky="w", pady=(0, 5))

        self.options_toggle = ctk.CTkButton(
            page, text="＋  Opciones avanzadas (yt-dlp)", height=30, width=145,
            fg_color="transparent", hover_color="#282333",
            text_color="#C5B6D8", anchor="w",
            font=ctk.CTkFont(size=11), command=self._toggle_advanced,
        )
        self.options_toggle.grid(row=7, column=0, sticky="w", pady=(0, 4))

        self.advanced = ctk.CTkFrame(page, fg_color="#1C1A25", corner_radius=16,
                                     border_width=1, border_color="#302B3A")
        self.advanced.grid_columnconfigure((0, 1), weight=1, uniform="personal")
        ctk.CTkLabel(self.advanced, text="OPCIONES AVANZADAS DE YT-DLP",
                     text_color="#C9B8E8", font=ctk.CTkFont(size=11, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(13, 8))

        def add_option(label, variable, row, column, placeholder=""):
            ctk.CTkLabel(self.advanced, text=label, text_color="#C8BED2",
                         font=ctk.CTkFont(size=10, weight="bold")
                         ).grid(row=row, column=column, sticky="w", padx=12, pady=(5, 3))
            entry = ctk.CTkEntry(self.advanced, textvariable=variable, height=34,
                                 placeholder_text=placeholder, fg_color="#17151F",
                                 border_color="#443B53", text_color="#F4EFFA")
            entry.grid(row=row + 1, column=column, sticky="ew", padx=12, pady=(0, 7))
            entry.bind("<FocusOut>", lambda _e: self._save_preferences())
            return entry

        add_option("Selector de formato (-f)", self.ydl_format, 1, 0, "Vacío = mejor audio")
        add_option("Plantilla de nombre (-o)", self.output_template, 1, 1, "Vacío = nombre automático")
        add_option("Elementos de lista (--playlist-items)", self.playlist_items, 3, 0, "Ej. 1,3,5-8")
        add_option("Límite de velocidad (--limit-rate)", self.limit_rate, 3, 1, "Ej. 1M o 500K")
        add_option("Reintentos (--retries)", self.retries, 5, 0, "Ej. 10")
        add_option("Idiomas de subtítulos (--sub-langs)", self.subtitle_langs, 5, 1, "Ej. es,en")

        self.embed_thumbnail_check = ctk.CTkCheckBox(
            self.advanced, text="Incrustar portada (--embed-thumbnail)",
            variable=self.embed_thumbnail, command=self._save_preferences,
            text_color="#C8BED2", fg_color="#8872AE", hover_color="#9B86BB",
            font=ctk.CTkFont(size=10))
        self.embed_thumbnail_check.grid(row=8, column=0, sticky="w", padx=12, pady=4)
        self.embed_metadata_check = ctk.CTkCheckBox(
            self.advanced, text="Incrustar metadatos (--embed-metadata)",
            variable=self.embed_metadata, command=self._save_preferences,
            text_color="#C8BED2", fg_color="#8872AE", hover_color="#9B86BB",
            font=ctk.CTkFont(size=10))
        self.embed_metadata_check.grid(row=8, column=1, sticky="w", padx=12, pady=4)
        self.write_subtitles_check = ctk.CTkCheckBox(
            self.advanced, text="Descargar subtítulos (--write-subs)",
            variable=self.write_subtitles, command=self._save_preferences,
            text_color="#C8BED2", fg_color="#8872AE", hover_color="#9B86BB",
            font=ctk.CTkFont(size=10))
        self.write_subtitles_check.grid(row=9, column=0, sticky="w", padx=12, pady=(4, 12))


        self.action_card = ctk.CTkFrame(page, fg_color="#211E2B", corner_radius=18,
                                        border_width=1, border_color="#332D40")
        self.action_card.grid(row=9, column=0, sticky="ew", pady=(8, 0))
        self.action_card.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            self.action_card, text="2.  Pulsa el botón y espera un momento.",
            text_color="#B6ADBF", font=ctk.CTkFont(size=12),
        )
        self.status_label.grid(row=0, column=0, pady=(17, 10))
        self.progress = ctk.CTkProgressBar(
            self.action_card, height=8, corner_radius=8,
            progress_color="#BCA7DE", fg_color="#393342",
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 14))
        self.progress.set(0)
        self.download_button = ctk.CTkButton(
            self.action_card, text="Guardar audio", height=54, corner_radius=13,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#8872AE", hover_color="#A08AC5",
            command=self._start_download,
        )
        self.download_button.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))
        self.open_folder_button = ctk.CTkButton(
            self.action_card, text="Abrir mi carpeta de música", height=34,
            fg_color="transparent", hover_color="#302A3A",
            text_color="#CDBFE0", font=ctk.CTkFont(size=12),
            command=self._open_folder, state="disabled",
        )
        self.open_folder_button.grid(row=4, column=0, pady=(0, 12))

        ctk.CTkLabel(
            page, text="Solo descarga contenido que tengas permiso para guardar.\nSOUNWD no descarga música desde Spotify.",
            text_color="#81798A", justify="center", font=ctk.CTkFont(size=10),
        ).grid(row=10, column=0, pady=(18, 0))


    def _center_content(self) -> None:
        """Centra el contenido cuando cabe y conserva el scroll cuando sobra."""
        canvas = self.page._parent_canvas
        inner = self.page._parent_frame
        if not canvas.winfo_exists() or not inner.winfo_exists():
            return
        canvas.update_idletasks()
        inner.update_idletasks()
        content_height = inner.winfo_reqheight()
        viewport_height = canvas.winfo_height()
        target_height = max(content_height, viewport_height)
        # CustomTkinter guarda el identificador del frame interno del canvas aquí.
        canvas.itemconfigure(self.page._parent_canvas_window, height=target_height)
        self.page.configure(height=target_height)
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _on_mousewheel(self, event):
        # No filtrar por event.widget: CustomTkinter enruta eventos desde
        # widgets internos y el cursor puede estar sobre cualquier control.
        delta = event.delta
        if delta:
            steps = -int(delta / 120) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
            self.page._parent_canvas.yview_scroll(steps, "units")
        return "break"

    def _on_mousewheel_linux(self, event):
        steps = -3 if event.num == 4 else 3
        self.page._parent_canvas.yview_scroll(steps, "units")
        return "break"

    def _responsive_layout(self, event=None) -> None:
        if event is not None and event.widget is not self:
            return
        width = max(self.winfo_width(), 520)
        horizontal = 18 if width < 650 else (30 if width < 850 else 46)
        self.page.grid_configure(padx=horizontal, pady=18 if width < 650 else 26)
        if width < 650:
            self.settings.grid_columnconfigure(0, weight=1)
            self.settings.grid_columnconfigure(1, weight=0)
            for index, card in enumerate(self.settings.winfo_children()):
                card.grid_configure(row=index, column=0, padx=0, pady=(0, 8), sticky="ew")
        else:
            self.settings.grid_columnconfigure(0, weight=1, uniform="settings")
            self.settings.grid_columnconfigure(1, weight=1, uniform="settings")
            for index, card in enumerate(self.settings.winfo_children()):
                card.grid_configure(row=0, column=index,
                                    padx=(0, 7) if index == 0 else (7, 0),
                                    pady=0, sticky="nsew")
        self.after_idle(self._center_content)

    def _paste_url(self) -> None:
        try:
            value = self.clipboard_get()
        except Exception:
            value = ""
        if value:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, value.strip())
            self.url_entry.focus_set()
            self.status_label.configure(text="Enlace pegado. Ya puedes guardar tu audio.")
        else:
            self.status_label.configure(text="No encuentro un enlace en el portapapeles.")

    def _load_preferences(self) -> dict:
        try:
            if PREFERENCES_FILE.exists():
                with PREFERENCES_FILE.open("r", encoding="utf-8") as handle:
                    data = json.load(handle)
                return data if isinstance(data, dict) else {}
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _save_preferences(self) -> None:
        data = {
            "destination": self.destination.get(),
            "audio_format": self.audio_format.get(),
            "playlist": self.playlist.get(),
            "quality": self.quality.get(),
            "filename_style": self.filename_style.get(),
            "ydl_format": self.ydl_format.get(),
            "output_template": self.output_template.get(),
            "playlist_items": self.playlist_items.get(),
            "limit_rate": self.limit_rate.get(),
            "retries": self.retries.get(),
            "subtitle_langs": self.subtitle_langs.get(),
            "embed_thumbnail": self.embed_thumbnail.get(),
            "embed_metadata": self.embed_metadata.get(),
            "write_subtitles": self.write_subtitles.get(),
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with PREFERENCES_FILE.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _preference_changed(self, _value: str = "") -> None:
        self._save_preferences()

    def _toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced.grid(row=7, column=0, sticky="ew", pady=(0, 8))
            self.options_toggle.configure(text="−  Ocultar opciones avanzadas")
            self.action_card.grid_configure(row=8)
        else:
            self.advanced.grid_remove()
            self.options_toggle.configure(text="＋  Opciones avanzadas (yt-dlp)")
            self.action_card.grid_configure(row=7)
        self.after_idle(self._center_content)

    @staticmethod
    def _short_path(value: str) -> str:
        """Muestra una ruta compacta para que quepa en la interfaz."""
        path = Path(value)
        parts = path.parts
        if len(parts) > 3:
            return "…/" + "/".join(parts[-2:])
        return str(path)

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(
            title="Elige dónde guardar tu música",
            initialdir=self.destination.get(),
        )
        if selected:
            self.destination.set(selected)
            self.folder_label.configure(text=self._short_path(selected))
            self._save_preferences()

    def _open_folder(self) -> None:
        folder = Path(self.destination.get()).expanduser()
        folder.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys_platform() == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception:
            messagebox.showinfo("Tu carpeta", f"Tu música está guardada aquí:\n{folder}")

    def _start_download(self) -> None:
        if self.downloading:
            return
        url = self.url_entry.get().strip()
        if not valid_url(url):
            messagebox.showinfo(
                "Primero pega un enlace",
                "Copia un enlace de YouTube o YouTube Music, pégalo en el recuadro y vuelve a pulsar «Guardar audio».",
            )
            self.url_entry.focus_set()
            return

        destination = Path(self.destination.get()).expanduser()
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError:
            messagebox.showerror(
                "No encuentro la carpeta",
                "No he podido preparar la carpeta para guardar tu música. Pulsa «Elegir» y selecciona otra carpeta.",
            )
            return

        self._save_preferences()
        self.downloading = True
        self.download_button.configure(state="disabled", text="Un momento…")
        self.open_folder_button.configure(state="disabled")
        self.progress.set(0)
        self.status_label.configure(text="Conectando… no cierres esta ventana.")
        thread = threading.Thread(
            target=self._download_worker,
            args=(url, FORMATS[self.audio_format.get()], destination, self.playlist.get(), self.quality.get(), self.filename_style.get(), {
                "format": self.ydl_format.get().strip(),
                "outtmpl": self.output_template.get().strip(),
                "playlist_items": self.playlist_items.get().strip(),
                "ratelimit": self.limit_rate.get().strip(),
                "retries": self.retries.get().strip(),
                "subtitleslangs": self.subtitle_langs.get().strip(),
                "embedthumbnail": self.embed_thumbnail.get(),
                "addmetadata": self.embed_metadata.get(),
                "writesubtitles": self.write_subtitles.get(),
            }),
            daemon=True,
        )
        thread.start()

    def _download_worker(self, url: str, audio_format: str, destination: Path, playlist: bool, quality_choice: str, filename_choice: str, advanced: dict) -> None:
        def hook(data: dict) -> None:
            if data.get("status") == "downloading":
                downloaded = data.get("downloaded_bytes", 0)
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                fraction = downloaded / total if total else 0
                self.events.put(("progress", (min(max(fraction, 0), 1), "Descargando tu audio…")))
            elif data.get("status") == "finished":
                self.events.put(("progress", (0.98, "Preparando el archivo…")))

        quality = {"Máxima": "0", "Alta": "192", "Normal": "128"}.get(quality_choice, "0")
        filename = "%(title)s" if filename_choice == "Solo título" else "%(title)s - %(uploader)s"
        output_template = advanced["outtmpl"]
        if output_template and not Path(output_template).expanduser().is_absolute():
            output_template = str(destination / output_template)
        options = {
            "format": advanced["format"] or "bestaudio/best",
            "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
            "outtmpl": output_template or str(destination / (filename + ".%(ext)s")),
            "noplaylist": not playlist,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": audio_format, "preferredquality": quality},
            ],
        }
        if advanced["playlist_items"]:
            options["playlist_items"] = advanced["playlist_items"]
        if advanced["ratelimit"]:
            options["ratelimit"] = advanced["ratelimit"]
        if advanced["retries"]:
            try:
                options["retries"] = max(0, int(advanced["retries"]))
            except ValueError:
                self.events.put(("error", "El número de reintentos debe ser un entero."))
                return
        if advanced["subtitleslangs"]:
            options["subtitleslangs"] = advanced["subtitleslangs"]
        if advanced["writesubtitles"]:
            options["writesubtitles"] = True
        if advanced["embedthumbnail"]:
            options["writethumbnail"] = True
            options["postprocessors"].append({"key": "EmbedThumbnail"})
        if advanced["addmetadata"]:
            options["addmetadata"] = True
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                result = downloader.download([url])
            if result:
                raise RuntimeError("La descarga no ha podido terminar.")
            self.events.put(("done", str(destination)))
        except Exception as error:
            message = str(error).lower()
            if "private" in message or "members-only" in message:
                friendly = "Este audio es privado o requiere una cuenta especial. Prueba con otro enlace."
            elif "unavailable" in message or "not available" in message:
                friendly = "Este audio no está disponible. Comprueba el enlace o prueba con otro."
            elif "ffmpeg" in message:
                friendly = "No se ha podido preparar el formato de audio. Vuelve a intentarlo; si continúa, prueba MP3."
            elif "network" in message or "connection" in message or "timed out" in message:
                friendly = "Parece que la conexión a Internet ha fallado. Comprueba tu conexión y vuelve a intentarlo."
            else:
                friendly = "No se ha podido guardar este audio. Comprueba el enlace y tu conexión, y vuelve a intentarlo."
            self.events.put(("error", friendly))

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
                    self.status_label.configure(text="¡Listo! Tu audio ya está guardado.")
                    self.download_button.configure(state="normal", text="Guardar otro audio")
                    self.open_folder_button.configure(state="normal")
                    self.url_entry.delete(0, "end")
                    messagebox.showinfo(
                        "¡Ya lo tienes!",
                        "Tu audio se ha guardado correctamente. Pulsa «Abrir mi carpeta de música» para encontrarlo.",
                    )
                elif kind == "error":
                    self.downloading = False
                    self.progress.set(0)
                    self.status_label.configure(text="No ha salido bien. Puedes volver a intentarlo.")
                    self.download_button.configure(state="normal", text="Intentar de nuevo")
                    messagebox.showinfo("No se ha podido guardar", str(payload))
        except queue.Empty:
            pass
        self.after(120, self._process_events)


def sys_platform() -> str:
    import sys
    return sys.platform


def main() -> None:
    app = SoundwApp()
    app.mainloop()


if __name__ == "__main__":
    main()

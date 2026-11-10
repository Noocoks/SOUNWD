from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path
from PIL import Image
import tkinter
from tkinter import filedialog, messagebox

# PyInstaller's bootloader splash is available only in packaged builds.
try:
    import pyi_splash as _boot_splash
except ImportError:
    _boot_splash = None

if _boot_splash is not None:
    try:
        _boot_splash.update_text("Cargando la interfaz de SOUNWD...")
    except (ConnectionError, RuntimeError):
        _boot_splash = None

import customtkinter as ctk
from yt_dlp_support import youtube_runtime_options
from security import build_output_path, validate_advanced_options, validate_youtube_url


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
        validate_youtube_url(value)
        return True
    except ValueError:
        return False


def _set_windows_app_user_model_id() -> None:
    """Give Windows 10/11 a stable identity for taskbar grouping and icon lookup."""
    if os.name != "nt":
        return
    try:
        import ctypes

        set_app_id = ctypes.WinDLL("shell32", use_last_error=True).SetCurrentProcessExplicitAppUserModelID
        set_app_id.argtypes = [ctypes.c_wchar_p]
        set_app_id.restype = ctypes.c_long
        result = set_app_id("Noocoks.SOUNWD.Desktop")
        if result != 0:
            raise OSError(f"SetCurrentProcessExplicitAppUserModelID failed: HRESULT {result:#x}")
    except (AttributeError, OSError):
        # A missing optional shell API must never prevent the app from opening.
        pass


class SoundwApp(ctk.CTk):
    def __init__(self) -> None:
        _set_windows_app_user_model_id()
        super().__init__()
        self._native_icon_handles = []
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.title("SOUNWD — Desktop Audio")
        self.geometry("880x800")
        self.minsize(560, 540)
        self.configure(fg_color="#09090B")
        self._set_window_icon()

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
        # Ocultamos solo la barra; CTkScrollableFrame conserva su scroll nativo con rueda.
        self.page._scrollbar.grid_remove()
        # CustomTkinter 5.2.2 does not bind Linux wheel buttons (Button-4/5).
        # Keep the scrollbar hidden, but preserve scrolling on Linux mice/touchpads.
        if sys_platform().startswith("linux"):
            self.page.bind_all("<Button-4>", self._on_linux_mousewheel, add="+")
            self.page.bind_all("<Button-5>", self._on_linux_mousewheel, add="+")
        self.after(80, self._responsive_layout)
        self.after(120, self._process_events)

    def _set_window_icon(self) -> None:
        """Use the skull artwork for the native title bar and taskbar icon."""
        # Canonical brand asset committed in assets/ and reused by every surface.
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
        png_path = bundle_root / "assets" / "sounwd.png"
        if not png_path.is_file():
            raise FileNotFoundError(f"Missing SOUNWD brand asset: {png_path}")
        self._window_icon = tkinter.PhotoImage(file=str(png_path))
        self.iconphoto(True, self._window_icon)
        # CTkImage preserves crisp scaling on HiDPI screens while the native
        # Tk PhotoImage remains available for the OS title bar/taskbar icon.
        with Image.open(png_path) as logo:
            brand_image = logo.copy()
        self._brand_image = ctk.CTkImage(
            light_image=brand_image,
            dark_image=brand_image,
            size=(104, 104),
        )

        # Windows builds additionally embed the ICO generated from this PNG.
        ico_path = bundle_root / "assets" / "sounwd.ico"
        if os.name == "nt" and ico_path.is_file():
            try:
                self.iconbitmap(default=str(ico_path))
            except (OSError, tkinter.TclError):
                pass
            self._set_windows_taskbar_icon(ico_path)

    def _set_windows_taskbar_icon(self, ico_path: Path) -> None:
        """Set both native HWND icons; Tk's iconphoto alone can be ignored by Win10's taskbar."""
        if os.name != "nt":
            return
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.WinDLL("user32", use_last_error=True)
            user32.LoadImageW.argtypes = [
                wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT,
                ctypes.c_int, ctypes.c_int, wintypes.UINT,
            ]
            user32.LoadImageW.restype = wintypes.HANDLE
            user32.SendMessageW.argtypes = [
                wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
            ]
            user32.SendMessageW.restype = wintypes.LRESULT

            # IMAGE_ICON + LR_LOADFROMFILE + LR_DEFAULTSIZE. Keep the HICON
            # handles alive for the lifetime of the window so Explorer can use them.
            icon_handle = user32.LoadImageW(
                None, str(ico_path), 1, 0, 0, 0x0010 | 0x0040
            )
            if not icon_handle:
                raise ctypes.WinError(ctypes.get_last_error())
            hwnd = wintypes.HWND(self.winfo_id())
            user32.SendMessageW(hwnd, 0x0080, 0, icon_handle)  # WM_SETICON / ICON_SMALL
            user32.SendMessageW(hwnd, 0x0080, 1, icon_handle)  # WM_SETICON / ICON_BIG
            self._native_icon_handles.append(icon_handle)
        except (AttributeError, OSError, tkinter.TclError):
            # The embedded executable icon remains a fallback if the shell API
            # is unavailable on an unusual Windows installation.
            pass

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll_page = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color="#A30F2D", scrollbar_button_hover_color="#C21C3B",
        )
        self.page = scroll_page
        scroll_page.grid(row=0, column=0, sticky="nsew", padx=24, pady=20)
        scroll_page.grid_columnconfigure(0, weight=1)
        scroll_page.grid_rowconfigure(0, weight=1)

        # Un único frame de contenido dentro del scroll nativo de CustomTkinter.
        # El centrado vertical se calcula moviendo la ventana del Canvas, sin
        # alterar alturas internas ni desactivar la propagación geométrica.
        page = ctk.CTkFrame(scroll_page, fg_color="transparent", corner_radius=0)
        self.content = page
        page.grid(row=0, column=0, sticky="ew")
        page.grid_columnconfigure(0, weight=1)

        scroll_page._parent_canvas.bind(
            "<Configure>", lambda _event: self.after_idle(self._center_content), add="+"
        )
        page.bind("<Configure>", lambda _event: self.after_idle(self._center_content), add="+")

        brand = ctk.CTkFrame(page, fg_color="transparent")
        brand.grid(row=1, column=0, sticky="ew", pady=(2, 12))
        # The visible logo is the very same Tk PhotoImage used by the window.
        self.brand_mark = ctk.CTkLabel(
            brand, text="", image=self._brand_image, fg_color="transparent",
        )
        self.brand_mark.pack(pady=(0, 2))
        ctk.CTkLabel(brand, text="S O U N W D  //", text_color="#F0F0F2",
                     font=ctk.CTkFont(family="Consolas", size=27, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(brand, text="NOOCOKS  /  DESKTOP AUDIO UTILITY",
                     text_color="#A30F2D", font=ctk.CTkFont(family="Consolas", size=10, weight="bold")).pack()
        ctk.CTkLabel(brand, text="DARK MODE  •  LOCAL OUTPUT  •  NO TRACKING",
                     text_color="#777B84", font=ctk.CTkFont(family="Consolas", size=9)).pack(pady=(3, 0))

        ctk.CTkLabel(page, text="TU AUDIO. TUS REGLAS.",
                     text_color="#F0F0F2", font=ctk.CTkFont(size=22, weight="bold")
                     ).grid(row=2, column=0, pady=(0, 5))
        ctk.CTkLabel(page, text="EXTRAE  ·  CONVIERTE  ·  GUARDA",
                     text_color="#9297A1", font=ctk.CTkFont(family="Consolas", size=10, weight="bold")
                     ).grid(row=3, column=0, pady=(0, 16))

        link_card = ctk.CTkFrame(page, fg_color="#121216", corner_radius=16,
                                 border_width=1, border_color="#30232A")
        link_card.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        link_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(link_card, text="[ 01 ]  INPUT // YOUTUBE SOURCE",
                     text_color="#C3C5CB", font=ctk.CTkFont(size=11, weight="bold")
                     ).grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))
        self.url_entry = ctk.CTkEntry(
            link_card, height=40, corner_radius=12,
            placeholder_text="https://www.youtube.com/watch?v=...",
            border_color="#702037", fg_color="#0C0C10",
            text_color="#F0F0F2", placeholder_text_color="#686D77",
            font=ctk.CTkFont(size=11),
        )
        self.url_entry.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        self.url_entry.bind("<Return>", lambda _event: self._start_download())
        link_actions = ctk.CTkFrame(link_card, fg_color="transparent")
        link_actions.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))
        ctk.CTkButton(
            link_actions, text="Pegar enlace", width=110, height=30,
            fg_color="#A30F2D", hover_color="#C21C3B",
            command=self._paste_url,
        ).pack(side="left")
        ctk.CTkButton(
            link_actions, text="Limpiar", width=76, height=30,
            fg_color="transparent", hover_color="#1D1D23",
            text_color="#C3C5CB", command=lambda: self.url_entry.delete(0, "end"),
        ).pack(side="left", padx=(8, 0))

        settings = ctk.CTkFrame(page, fg_color="transparent")
        self.settings = settings
        settings.grid(row=5, column=0, sticky="ew", pady=(0, 8))
        settings.grid_columnconfigure((0, 1), weight=1, uniform="settings")

        format_card = ctk.CTkFrame(settings, fg_color="#121216", corner_radius=14,
                                   border_width=1, border_color="#30232A")
        format_card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(format_card, text="[ 02 ]  OUTPUT FORMAT",
                     text_color="#C3C5CB", font=ctk.CTkFont(size=10, weight="bold")
                     ).pack(anchor="w", padx=12, pady=(10, 5))
        ctk.CTkOptionMenu(
            format_card, variable=self.audio_format, values=list(FORMATS),
            command=self._preference_changed,
            height=36, corner_radius=10, fg_color="#A30F2D",
            button_color="#702037", button_hover_color="#C21C3B",
            dropdown_fg_color="#17171C",
        ).pack(fill="x", padx=10, pady=(0, 10))

        folder_card = ctk.CTkFrame(settings, fg_color="#121216", corner_radius=14,
                                   border_width=1, border_color="#30232A")
        folder_card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(folder_card, text="[ 03 ]  DESTINATION",
                     text_color="#C3C5CB", font=ctk.CTkFont(size=10, weight="bold")
                     ).pack(anchor="w", padx=12, pady=(10, 5))
        folder_row = ctk.CTkFrame(folder_card, fg_color="transparent")
        folder_row.pack(fill="x", padx=10, pady=(0, 10))
        folder_row.grid_columnconfigure(0, weight=1)
        self.folder_label = ctk.CTkLabel(
            folder_row, text=self._short_path(str(self.destination.get())),
            text_color="#E0E1E5", font=ctk.CTkFont(size=10), anchor="w",
        )
        self.folder_label.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            folder_row, text="Elegir", width=66, height=34,
            fg_color="#702037", hover_color="#A30F2D",
            command=self._choose_folder,
        ).grid(row=0, column=1, padx=(6, 0))

        self.playlist_check = ctk.CTkCheckBox(
            page, text="Descargar la lista completa si el enlace contiene una",
            variable=self.playlist, command=self._save_preferences,
            text_color="#C3C5CB", fg_color="#A30F2D", hover_color="#C21C3B",
            font=ctk.CTkFont(size=11),
        )
        self.playlist_check.grid(row=6, column=0, sticky="w", pady=(0, 5))

        self.options_toggle = ctk.CTkButton(
            page, text="+  ADVANCED // YT-DLP", height=30, width=145,
            fg_color="transparent", hover_color="#1D1D23",
            text_color="#A0A4AD", anchor="w",
            font=ctk.CTkFont(size=11), command=self._toggle_advanced,
        )
        self.options_toggle.grid(row=7, column=0, sticky="w", pady=(0, 4))

        self.advanced = ctk.CTkFrame(page, fg_color="#111115", corner_radius=16,
                                     border_width=1, border_color="#30232A")
        self.advanced.grid_columnconfigure((0, 1), weight=1, uniform="personal")
        ctk.CTkLabel(self.advanced, text="ADVANCED PARAMETERS // YT-DLP",
                     text_color="#C3C5CB", font=ctk.CTkFont(size=11, weight="bold")
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(13, 8))

        def add_option(label, variable, row, column, placeholder=""):
            ctk.CTkLabel(self.advanced, text=label, text_color="#C3C5CB",
                         font=ctk.CTkFont(size=10, weight="bold")
                         ).grid(row=row, column=column, sticky="w", padx=12, pady=(5, 3))
            entry = ctk.CTkEntry(self.advanced, textvariable=variable, height=34,
                                 placeholder_text=placeholder, fg_color="#0C0C10",
                                 border_color="#702037", text_color="#F0F0F2")
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
            text_color="#C3C5CB", fg_color="#A30F2D", hover_color="#C21C3B",
            font=ctk.CTkFont(size=10))
        self.embed_thumbnail_check.grid(row=7, column=0, sticky="w", padx=12, pady=4)
        self.embed_metadata_check = ctk.CTkCheckBox(
            self.advanced, text="Incrustar metadatos (--embed-metadata)",
            variable=self.embed_metadata, command=self._save_preferences,
            text_color="#C3C5CB", fg_color="#858A94", hover_color="#C3C5CB",
            font=ctk.CTkFont(size=10))
        self.embed_metadata_check.grid(row=7, column=1, sticky="w", padx=12, pady=4)
        self.write_subtitles_check = ctk.CTkCheckBox(
            self.advanced, text="Descargar subtítulos (--write-subs)",
            variable=self.write_subtitles, command=self._save_preferences,
            text_color="#C3C5CB", fg_color="#858A94", hover_color="#C3C5CB",
            font=ctk.CTkFont(size=10))
        self.write_subtitles_check.grid(row=8, column=0, sticky="w", padx=12, pady=(4, 12))


        self.action_card = ctk.CTkFrame(page, fg_color="#121216", corner_radius=16,
                                        border_width=1, border_color="#4A1C2B")
        self.action_card.grid(row=9, column=0, sticky="ew", pady=(8, 0))
        self.action_card.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            self.action_card, text="[ SYSTEM READY ]  AWAITING INPUT",
            text_color="#C3C5CB", font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.status_label.grid(row=0, column=0, pady=(8, 4))
        self.progress = ctk.CTkProgressBar(
            self.action_card, height=8, corner_radius=8,
            progress_color="#C21C3B", fg_color="#292930",
        )
        self.progress.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.progress.set(0)
        self.download_button = ctk.CTkButton(
            self.action_card, text="▶  EXTRAER AUDIO", height=44, corner_radius=13,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#A30F2D", hover_color="#C21C3B",
            command=self._start_download,
        )
        self.download_button.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 8))
        self.open_folder_button = ctk.CTkButton(
            self.action_card, text="OPEN OUTPUT DIRECTORY", height=34,
            fg_color="transparent", hover_color="#1D1D23",
            text_color="#C3C5CB", font=ctk.CTkFont(size=12),
            command=self._open_folder, state="disabled",
        )
        self.open_folder_button.grid(row=3, column=0, pady=(0, 8))

        ctk.CTkLabel(
            page, text="[ USE RESPONSIBLY ]  SOLO CONTENIDO AUTORIZADO.\nNO SPOTIFY // NO TRACKING // LOCAL OUTPUT.",
            text_color="#777B84", justify="center", font=ctk.CTkFont(family="Consolas", size=9),
        ).grid(row=10, column=0, pady=(6, 0))


    def _center_content(self) -> None:
        """Centra el bloque moviendo la ventana del Canvas; conserva el scroll."""
        canvas = self.page._parent_canvas
        if not canvas.winfo_exists() or not self.page.winfo_exists():
            return

        canvas.update_idletasks()
        self.content.update_idletasks()
        viewport_height = canvas.winfo_height()
        if viewport_height <= 1:
            return

        # La ventana del Canvas conserva la altura natural de CTkScrollableFrame.
        # No forzamos height ni grid_propagate: eso rompe la geometría en Windows.
        content_height = max(
            self.page.winfo_reqheight(),
            self.content.winfo_reqheight(),
        )
        window_id = self.page._create_window_id
        y_offset = max(0, (viewport_height - content_height) // 2)
        canvas.coords(window_id, 0, y_offset)
        canvas.configure(
            scrollregion=(0, 0, max(canvas.winfo_width(), 1),
                          max(viewport_height, content_height + y_offset))
        )

    def _on_linux_mousewheel(self, event):
        """Scroll the page on Linux, where Tk emits Button-4/Button-5 wheel events."""
        canvas = self.page._parent_canvas
        widget = getattr(event, "widget", None)
        while widget is not None and widget is not canvas:
            widget = getattr(widget, "master", None)
        if widget is not canvas:
            return None

        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")
        return "break"

    def _responsive_layout(self, event=None) -> None:
        if event is not None and event.widget is not self:
            return
        width = max(self.winfo_width(), 520)
        horizontal = 16 if width < 650 else (28 if width < 850 else 42)
        # CTkScrollableFrame se muestra mediante su _parent_frame (grid).
        # self.page vive dentro del Canvas y no debe recibir grid_configure().
        self.page._parent_frame.grid_configure(
            padx=horizontal, pady=14 if width < 650 else 14
        )
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
            self.advanced.grid(row=8, column=0, sticky="ew", pady=(0, 8))
            self.options_toggle.configure(text="−  Ocultar opciones avanzadas")
            self.action_card.grid_configure(row=9)
        else:
            self.advanced.grid_remove()
            self.options_toggle.configure(text="+  ADVANCED // YT-DLP")
            self.action_card.grid_configure(row=9)
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
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))
            elif sys_platform() == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as error:
            messagebox.showerror("No se puede abrir la carpeta", f"No he podido abrir o preparar esta carpeta:\n{folder}\n\nDetalle: {error}")

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
        try:
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
        except Exception as error:
            self.downloading = False
            self.download_button.configure(state="normal", text="▶  EXTRAER AUDIO")
            self.open_folder_button.configure(state="normal")
            self.status_label.configure(text="No se ha podido iniciar la descarga.")
            messagebox.showerror("No se ha podido iniciar", str(error))

    def _download_worker(self, url: str, audio_format: str, destination: Path, playlist: bool, quality_choice: str, filename_choice: str, advanced: dict) -> None:
        """Prepara y ejecuta la descarga fuera del hilo de Tk, notificando siempre el resultado."""
        def hook(data: dict) -> None:
            if data.get("status") == "downloading":
                downloaded = data.get("downloaded_bytes", 0)
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                fraction = downloaded / total if total else 0
                self.events.put(("progress", (min(max(fraction, 0), 1), "Descargando tu audio…")))
            elif data.get("status") == "finished":
                self.events.put(("progress", (0.98, "Preparando el archivo…")))

        retry_count = None
        if advanced["retries"]:
            try:
                retry_count = int(advanced["retries"])
                if retry_count < 0:
                    raise ValueError
            except ValueError:
                self.events.put(("error", "El número de reintentos debe ser un entero igual o mayor que cero."))
                return
        try:
            validate_youtube_url(url)
            # Heavy downloader/post-processing packages are loaded only when needed;
            # this keeps the first window responsive and reduces perceived startup.
            import imageio_ffmpeg
            import yt_dlp

            quality = {"Máxima": "0", "Alta": "192", "Normal": "128"}.get(quality_choice, "0")
            filename = "%(title)s" if filename_choice == "Solo título" else "%(title)s - %(uploader)s"
            safe_advanced = validate_advanced_options(advanced)
            output_template = safe_advanced["outtmpl"]
            if not advanced["outtmpl"]:
                output_template = filename + ".%(ext)s"
            safe_output_path = build_output_path(destination, output_template)
            options = {
                **youtube_runtime_options(),
                "format": safe_advanced["format"] or "bestaudio/best",
                "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
                "outtmpl": str(safe_output_path),
                "noplaylist": not playlist,
                "windowsfilenames": True,
                "overwrites": False,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [hook],
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": audio_format, "preferredquality": quality},
                ],
            }
            if safe_advanced["playlist_items"]:
                options["playlist_items"] = safe_advanced["playlist_items"]
            if safe_advanced["ratelimit"]:
                options["ratelimit"] = safe_advanced["ratelimit"]
            if safe_advanced["retries"] is not None:
                options["retries"] = safe_advanced["retries"]
            if safe_advanced["subtitleslangs"]:
                options["subtitleslangs"] = safe_advanced["subtitleslangs"]
            if advanced["writesubtitles"]:
                options["writesubtitles"] = True
            if advanced["embedthumbnail"]:
                options["writethumbnail"] = True
                options["postprocessors"].append({"key": "EmbedThumbnail"})
            if advanced["addmetadata"]:
                options["addmetadata"] = True

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
            elif "deno" in message or "javascript runtime" in message or "challenge solver" in message:
                friendly = "YouTube necesita el motor JavaScript Deno. Usa la última aplicación de escritorio de SOUNWD o instala Deno 2.3 o posterior si ejecutas desde el código fuente."
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
                        "Tu audio se ha guardado correctamente. Pulsa «OPEN OUTPUT DIRECTORY» para encontrarlo.",
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
    # Force the first frame to be painted before dismissing the bootloader splash.
    app.update_idletasks()
    app.update()
    if _boot_splash is not None:
        try:
            _boot_splash.close()
        except (ConnectionError, RuntimeError):
            pass

    # Optional readiness marker used only by the packaged-startup CI smoke test.
    # It is written after the main window has been rendered and the boot splash closed.
    ready_file = os.environ.get("SOUNWD_SMOKE_READY_FILE")
    if ready_file:
        try:
            Path(ready_file).write_text("ready", encoding="utf-8")
        except OSError:
            pass
    app.mainloop()


if __name__ == "__main__":
    main()

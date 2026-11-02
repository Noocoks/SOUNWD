# ♫ Sonora — Music Downloader

Sonora es una aplicación de escritorio en Python con una interfaz gráfica oscura y sencilla para gestionar descargas de audio mediante yt-dlp.

> Utiliza Sonora únicamente con contenido que tengas derecho a descargar y respeta las condiciones de la plataforma y las licencias aplicables. Sonora no descarga música desde Spotify.

## Abrir Sonora

### Windows — doble clic

1. Instala Python 3.10 o superior desde [python.org](https://www.python.org/downloads/). Durante la instalación, deja activado el Python Launcher.
2. Abre la carpeta del proyecto.
3. Haz doble clic en **Windows/Abrir Sonora.vbs**.

La primera vez aparecerá una pequeña ventana de preparación. Sonora creará su propio entorno e instalará las dependencias automáticamente. En los siguientes inicios abrirá mucho más rápido.

### Linux — acceso directo

Necesitas Python 3.10 o superior y los componentes de Tkinter/venv de tu distribución (en Ubuntu y derivadas: `python3-tk` y `python3-venv`).

1. Abre la carpeta del proyecto.
2. Haz doble clic en **Linux/Sonora.desktop**. Si el escritorio pregunta, elige «Permitir ejecutar» o «Confiar y ejecutar».
3. Para tener un acceso directo en el Escritorio, ejecuta una vez **Linux/Instalar acceso directo.sh** desde el gestor de archivos (elige «Ejecutar» si te lo pregunta). Después podrás abrir Sonora desde ese acceso directo.

La primera vez aparecerá la ventana de preparación y se instalarán automáticamente las dependencias Python en un entorno aislado del proyecto.

## Componentes de audio

Sonora incluye FFmpeg mediante el paquete `imageio-ffmpeg`, por lo que no necesitas instalar FFmpeg por separado.

## Funciones

- Interfaz gráfica con CustomTkinter.
- Enlaces de YouTube y YouTube Music.
- Formatos MP3, M4A/AAC, FLAC, OPUS y WAV.
- Selector de carpeta de destino.
- Descarga individual o listas de reproducción.
- Barra de progreso y avisos visuales.

## Desarrollo

- `bootstrap.py`: prepara el entorno e inicia la aplicación.
- `src/gui.py`: interfaz gráfica.
- `src/cli.py`: versión de terminal.
- `requirements.txt`: dependencias Python.
- `Windows/` y `Linux/`: lanzadores.

## Aviso

Sonora es una interfaz para yt-dlp. El usuario es responsable de comprobar que tiene los derechos y permisos necesarios para descargar y utilizar cada contenido.

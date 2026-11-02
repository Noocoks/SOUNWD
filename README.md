# ♫ Music Downloader

Aplicación de terminal sencilla y guiada para descargar audio de vídeos y listas de reproducción de YouTube y YouTube Music mediante [yt-dlp](https://github.com/yt-dlp/yt-dlp).

> Utiliza la herramienta únicamente con contenido que tengas derecho a descargar y respeta las condiciones de la plataforma y las licencias aplicables. No descarga música desde Spotify.

## Características

- Interfaz de terminal con colores y paneles gracias a Rich.
- Descarga de audio individual o listas de reproducción.
- Formatos: MP3, M4A, FLAC, OPUS y WAV.
- Selección de carpeta de destino.
- Indicador de progreso.
- Compatible con Windows y Linux.

## Requisitos

- Python 3.10 o superior.
- FFmpeg y ffprobe instalados y disponibles en el PATH.
- Conexión a Internet.

## Instalación

Clona el repositorio y entra en la carpeta:

```bash
git clone https://github.com/Noocoks/music-downloader.git
cd music-downloader
```

Crea un entorno virtual (recomendado):

**Windows (PowerShell):**
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Instala las dependencias:

```bash
python -m pip install -r requirements.txt
```

Instala FFmpeg según tu sistema operativo y asegúrate de que los comandos `ffmpeg` y `ffprobe` funcionan desde la terminal.

## Iniciar

- **Windows:** ejecuta `Windows/iniciar.bat`.
- **Linux:** ejecuta `bash Linux/iniciar.sh`.

También puedes iniciar directamente con:

```bash
python -m src.main
```

## Desarrollo

Las dependencias de Python están en `requirements.txt`. Las contribuciones y sugerencias son bienvenidas.

## Aviso

Este proyecto es una interfaz de usuario para yt-dlp. El usuario es responsable de comprobar que tiene los derechos y permisos necesarios para descargar y utilizar cada contenido.

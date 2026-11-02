# ♫ Sonora — Music Downloader

Sonora es una aplicación de escritorio en Python con una interfaz gráfica sencilla para gestionar descargas de audio mediante [yt-dlp](https://github.com/yt-dlp/yt-dlp).

> Utiliza Sonora únicamente con contenido que tengas derecho a descargar y respeta las condiciones de la plataforma y las licencias aplicables. Sonora no descarga música desde Spotify.

## Características actuales

- Interfaz gráfica oscura con [CustomTkinter](https://customtkinter.tomschimansky.com/).
- Descarga de audio desde enlaces de YouTube y YouTube Music.
- Formatos MP3, M4A/AAC, FLAC, OPUS y WAV.
- Selector de carpeta de destino.
- Descarga de vídeos individuales o listas de reproducción.
- Barra de progreso y avisos de errores.
- Compatible con Windows y Linux (pendiente de pruebas en ambos sistemas).

## Requisitos

- Python 3.10 o superior.
- FFmpeg y ffprobe instalados y disponibles en el PATH.
- Conexión a Internet.

## Instalación y ejecución

Clona el repositorio:

```bash
git clone https://github.com/Noocoks/music-downloader.git
cd music-downloader
```

### Windows

Ejecuta `Windows/iniciar.bat`. El lanzador instala las dependencias de Python y abre la interfaz gráfica.

### Linux

Ejecuta:

```bash
bash Linux/iniciar.sh
```

El lanzador instala las dependencias de Python y abre la interfaz gráfica.

### Inicio manual

También puedes crear un entorno virtual, instalar las dependencias y ejecutar:

```bash
python -m pip install -r requirements.txt
python -m src.gui
```

Instala FFmpeg según tu sistema operativo y comprueba que `ffmpeg` y `ffprobe` funcionan desde la terminal.

## Estructura

- `src/gui.py`: aplicación gráfica Sonora.
- `src/cli.py`: versión de terminal.
- `requirements.txt`: dependencias Python.
- `Windows/` y `Linux/`: lanzadores por sistema operativo.

## Aviso

Sonora es una interfaz para yt-dlp. El usuario es responsable de comprobar que tiene los derechos y permisos necesarios para descargar y utilizar cada contenido.

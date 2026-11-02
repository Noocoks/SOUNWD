# SOUNWD. — Your sound. Your moments.

**SOUNWD** es tu pequeño espacio para guardar los sonidos que forman parte de tus momentos. Una aplicación de escritorio sencilla, con una interfaz tranquila y personalizable, construida con Python, CustomTkinter y yt-dlp.

> Utiliza SOUNWD únicamente con contenido que tengas derecho a descargar y respeta las condiciones de la plataforma y las licencias aplicables. SOUNWD no descarga música desde Spotify.

## Abrir SOUNWD

Estamos preparando versiones independientes para Windows y Linux. Cuando la compilación esté disponible, podrás descargarlas desde [Actions](https://github.com/Noocoks/music-downloader/actions), en los artefactos de la ejecución más reciente. La compilación debe finalizar correctamente antes de que aparezcan.

### Windows — doble clic

1. Instala Python 3.10 o superior desde [python.org](https://www.python.org/downloads/) (activa Python Launcher durante la instalación).
2. Abre la carpeta del proyecto.
3. Haz doble clic en **Windows/Abrir Sonora.vbs**.

La primera vez aparecerá una ventana de preparación. SOUNWD creará un entorno aislado e instalará sus dependencias. En los siguientes inicios abrirá directamente.

### Linux — acceso directo

Necesitas Python 3.10 o superior y los componentes Tkinter/venv de tu distribución (en Ubuntu y derivadas: `python3-tk` y `python3-venv`).

1. Abre la carpeta del proyecto.
2. Ejecuta **Linux/Instalar acceso directo.sh** desde el gestor de archivos (si aparece una opción, elige «Ejecutar»).
3. Abre **SOUNWD.desktop** desde el Escritorio.

La primera vez aparecerá la ventana de preparación y se instalarán automáticamente las dependencias Python en un entorno aislado.

## Tu música, a tu manera

- Interfaz gráfica oscura y serena, con tonos lavanda.
- Enlaces de YouTube y YouTube Music.
- Formatos MP3, M4A/AAC, FLAC, OPUS y WAV.
- Carpeta de destino elegible.
- Descargas individuales o listas de reproducción.
- Barra de progreso y avisos claros.

## Desarrollo

- `bootstrap.py`: prepara el entorno e inicia la aplicación.
- `src/gui.py`: interfaz gráfica SOUNWD.
- `src/cli.py`: versión de terminal.
- `requirements.txt`: dependencias Python.
- `Windows/` y `Linux/`: lanzadores.

## Aviso

SOUNWD utiliza yt-dlp como herramienta de descarga. El usuario es responsable de comprobar que tiene los derechos y permisos necesarios para descargar y utilizar cada contenido.

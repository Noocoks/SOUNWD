# SOUNWD. — Your sound. Your moments.

**SOUNWD** guarda en tu ordenador el audio de enlaces compatibles de YouTube y YouTube Music. Está pensado para que usarlo sea tan sencillo como copiar, pegar y pulsar un botón.

> Usa SOUNWD solo con contenido que tengas derecho a descargar. Respeta los derechos de autor, las licencias y las condiciones de cada plataforma. No descarga música desde Spotify.

## Descargar SOUNWD

No necesitas instalar Python ni abrir una terminal si descargas la aplicación ya compilada.

1. Entra en [Descargas de SOUNWD](https://github.com/Noocoks/music-downloader/actions).
2. Abre la ejecución más reciente que tenga una marca verde de éxito.
3. Baja hasta **Artifacts** y descarga el archivo de tu sistema:
   - **SOUNWD-Windows** para Windows.
   - **SOUNWD-Linux** para Linux.
4. Extrae el ZIP en una carpeta de tu elección.

### Windows

Haz doble clic en **SOUNWD.exe**. Si Windows muestra SmartScreen, comprueba que lo has descargado de este repositorio y elige «Más información» → «Ejecutar de todas formas» si confías en el archivo.

### Linux

Haz clic derecho sobre **SOUNWD**, abre Propiedades → Permisos y activa «Permitir ejecutar el archivo como un programa». Después, haz doble clic y selecciona «Ejecutar».

## Cómo usarlo

1. Copia el enlace del audio en YouTube.
2. Pégalo en el recuadro de SOUNWD.
3. Pulsa **Guardar audio**.
4. Cuando termine, pulsa **Abrir mi carpeta de música**.

¡Eso es todo! Por defecto, los archivos se guardan en la carpeta **Descargas** (Downloads) y en formato **MP3**. Puedes cambiar ambas cosas directamente desde la pantalla principal.

La pantalla principal está pensada para todo el mundo: pega el enlace, elige el formato y la carpeta y pulsa **Guardar audio**. La opción **Descargar la lista completa** también está a la vista.

Si ya conoces yt-dlp, abre **Opciones avanzadas (yt-dlp)** para configurar directamente parámetros como el selector de formato (`-f`), la plantilla del nombre (`-o`), los elementos de una lista (`--playlist-items`), el límite de velocidad (`--limit-rate`), los reintentos (`--retries`) y los subtítulos (`--write-subs`, `--sub-langs`). En escritorio también puedes incrustar portada y metadatos; estas funciones requieren FFmpeg. Los campos avanzados son opcionales: si los dejas vacíos, SOUNWD usa sus valores habituales.

## Qué incluye

- Interfaz sencilla y tranquila, con tonos lavanda.
- Formato MP3 predeterminado; también M4A, FLAC, OPUS y WAV.
- Carpeta de destino personalizable, con Descargas como ubicación inicial.
- Preferencia de calidad (máxima, alta o normal) y formato del nombre de archivo.
- Interfaz dividida entre opciones básicas visibles y parámetros avanzados de yt-dlp.
- Preferencias guardadas automáticamente para la próxima vez.
- Descargas individuales o listas de reproducción.
- Indicador de progreso y mensajes fáciles de entender.
- Aplicaciones independientes compiladas para Windows y Linux.
- Versión Android en desarrollo, con interfaz Kivy inspirada en el escritorio y compilación APK automática mediante GitHub Actions.

## Desarrollo

- `src/gui.py`: interfaz gráfica.
- `src/cli.py`: versión de terminal.
- `bootstrap.py`: instalador de dependencias para desarrollo.
- `requirements.txt`: dependencias Python.
- `.github/workflows/build.yml`: compilación automática de las aplicaciones de escritorio.
- `android/main.py` y `android/buildozer.spec`: aplicación móvil y configuración de Android.
- `.github/workflows/android.yml`: compilación automática de la APK.

SOUNWD utiliza yt-dlp para obtener audio. En Android, esta primera versión conserva el formato disponible en origen: la conversión a MP3/FLAC/WAV con FFmpeg todavía no está integrada. Por ese motivo, las opciones de incrustar portada y metadatos no se ofrecen en Android. La APK se publica como artefacto de GitHub Actions cuando la compilación termina correctamente.
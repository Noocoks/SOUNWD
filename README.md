# SOUNWD — Your sound. Your moments.

**SOUNWD** guarda en tu ordenador el audio de enlaces compatibles de YouTube y YouTube Music. Está pensado para que usarlo sea tan sencillo como copiar, pegar y pulsar un botón.

> Usa SOUNWD solo con contenido que tengas derecho a descargar. Respeta los derechos de autor, las licencias y las condiciones de cada plataforma. No descarga música desde Spotify.

## Identidad visual y recursos

SOUNWD utiliza una única imagen maestra para mantener coherentes los iconos en todas las plataformas. La fuente oficial es `icon/sounwd-master.png`.

Para regenerar los recursos de Android, Windows, Linux, macOS y web/PWA tras cambiar esa imagen:

```bash
python -m pip install Pillow
python tools/generate_icons.py
```

Los recursos derivados se guardan en `assets/generated/`. No edites esos archivos a mano: el generador los reemplaza. Consulta [icon/README.md](icon/README.md) para conocer las salidas y el proceso.

**Importante:** reemplaza únicamente `icon/sounwd-master.png`; conserva su nombre y ruta. Los workflows regeneran los formatos correspondientes antes de empaquetar.

## Descargar SOUNWD

Consulta las compilaciones disponibles en [GitHub Actions](https://github.com/Noocoks/SOUNWD/actions). Abre una ejecución completada correctamente y descarga el artefacto de tu sistema en la sección **Artifacts**.

- **Windows:** artefacto SOUNWD-Windows.
- **Linux:** artefacto SOUNWD-Linux.
- **Android beta:** artefacto sounwd-beta-debug desde el workflow SOUNWD Android Beta.

## Cómo usarlo

1. Copia el enlace del audio en YouTube.
2. Pégalo en el recuadro de SOUNWD.
3. Pulsa **Guardar audio**.
4. Cuando termine, pulsa **Abrir mi carpeta de música**.

Por defecto, los archivos se guardan en **Descargas** y en formato **MP3**. Puedes cambiar ambas cosas desde la pantalla principal.

## Qué incluye

- Formato MP3 predeterminado; también M4A, FLAC, OPUS y WAV.
- Carpeta de destino personalizable.
- Preferencia de calidad y formato del nombre de archivo.
- Descargas individuales o listas de reproducción.
- Indicador de progreso y mensajes fáciles de entender.
- Aplicaciones de escritorio para Windows y Linux.
- Beta Android nativa en Kotlin, actualmente centrada en validar la instalación y la identidad visual.

## Desarrollo

- `src/gui.py`: interfaz gráfica de escritorio.
- `src/cli.py`: versión de terminal.
- `bootstrap.py`: instalador de dependencias.
- `android/main.py` y `android/buildozer.spec`: versión Android Kivy heredada.
- `beta-android/`: beta Android nativa Kotlin/Gradle.
- `tools/generate_icons.py`: generador multiplataforma de iconos.
- `.github/workflows/build.yml`: compilación Windows/Linux.
- `.github/workflows/android-beta.yml`: compilación Android beta.

SOUNWD utiliza yt-dlp para obtener audio. Usa la aplicación solo con contenido que tengas derecho a guardar.

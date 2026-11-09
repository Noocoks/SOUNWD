# SOUNWD Android — beta visual

Aplicación Android nativa Kotlin/Gradle. Esta beta conserva la pantalla funcional ya validada y no incorpora todavía descargas ni funciones de audio.

## Identidad visual centralizada

La imagen maestra vive en la raíz del repositorio: `icon/sounwd-master.png`. No hay que editar iconos Android por separado.

Al ejecutar `python tools/generate_icons.py`, se generan automáticamente:
- Logo completo para mostrar dentro de la app.
- Icono adaptativo para Android 8.0 o posterior.
- Iconos launcher PNG para densidades mdpi, hdpi, xhdpi, xxhdpi y xxxhdpi.

El workflow **SOUNWD Android Beta** ejecuta este generador y después compila el APK. Para cambiar la marca, sustituye únicamente la imagen maestra y vuelve a ejecutar el workflow.

## Compilar localmente

Desde la raíz del repositorio:

```bash
python -m pip install Pillow
python tools/generate_icons.py
cd beta-android
gradle assembleDebug
```

El APK de depuración se genera en `app/build/outputs/apk/debug/app-debug.apk`.

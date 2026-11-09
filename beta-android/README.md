# SOUNWD Android — beta visual

La aplicación Android beta activa es el proyecto Kotlin/Gradle situado en la raíz del repositorio (`app/`). Esta carpeta `beta-android/` conserva una copia histórica de la pantalla inicial y no es el proyecto que compila GitHub Actions.

## Compilación

Desde la raíz del repositorio:

```bash
python -m pip install Pillow
python tools/generate_icons.py
gradle assembleDebug
```

El APK se genera en `app/build/outputs/apk/debug/app-debug.apk`. Para la compilación automatizada, utiliza el workflow **SOUNWD Android Beta** y descarga el artefacto `sounwd-beta-debug`.

## Identidad visual

La única fuente maestra es `icon/sounwd-master.png`. El generador crea el logo de la pantalla y los recursos del launcher Android a partir de esa imagen. No edites los recursos generados individualmente.

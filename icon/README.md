# Identidad visual SOUNWD

## Única fuente maestra

La única imagen que debes sustituir para renovar toda la iconografía es:

`icon/sounwd-master.png`

La imagen maestra oficial ya está incorporada al repositorio. Para futuras actualizaciones, reemplaza ese PNG manteniendo el mismo nombre y ruta. Se recomienda una resolución mínima de 1024 × 1024.

## Regenerar todos los formatos

Desde la raíz del repositorio:

```bash
python -m pip install Pillow
python tools/generate_icons.py
```

El generador produce recursos para Android (logo dentro de la app, adaptive icon y densidades mdpi–xxxhdpi), Windows (.ico multirresolución), Linux (PNG), macOS (.icns) y web/PWA (favicons y tamaños de instalación) dentro de `assets/generated/`.

No edites manualmente los archivos generados: se sobrescriben en cada ejecución. Edita o reemplaza solo `icon/sounwd-master.png`.

## Integración

El workflow de Android ejecuta el generador desde la raíz del repositorio e instala los recursos en `app/src/main/res/` antes de compilar. El icono de la pantalla principal y el icono del launcher proceden del mismo PNG maestro.

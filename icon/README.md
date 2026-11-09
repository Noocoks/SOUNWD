# Identidad visual SOUNWD

## Única fuente maestra

La única imagen que debes sustituir para renovar toda la iconografía es:

`icon/sounwd-master.png`

Coloca ahí la imagen maestra aprobada, en PNG y preferiblemente con resolución mínima de 1024 × 1024. Mantén el nombre y la ruta.

## Regenerar todos los formatos

Desde la raíz del repositorio:

```bash
python -m pip install Pillow
python tools/generate_icons.py
```

El generador produce recursos para Android (adaptive icon y densidades mdpi–xxxhdpi), Windows (.ico multirresolución), Linux (PNG), macOS (.icns) y web/PWA (favicons y tamaños de instalación) dentro de `assets/generated/`.

No edites manualmente los archivos generados: se sobrescriben en cada ejecución. Edita o reemplaza solo `icon/sounwd-master.png`.

## Integración

Los workflows de escritorio y Android ejecutan el generador antes de empaquetar. Android usa además `assets/generated/android/drawable-nodpi/sounwd_master.png` en la pantalla y los recursos launcher generados.

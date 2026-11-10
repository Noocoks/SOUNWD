# Identidad visual SOUNWD

## Imagen maestra única

La fuente oficial es `icon/sounwd-master.png`. Para actualizar la identidad visual, sustituye ese archivo conservando su nombre y ruta. Se recomienda PNG cuadrado de al menos 1024 × 1024 píxeles.

## Regeneración

Desde la raíz del repositorio:

```bash
python -m pip install Pillow
python tools/generate_icons.py
python -m unittest discover -s tools -p 'test_*.py' -v
```

El generador crea recursos en `assets/generated/` para:

- Android 10+: logo de la app y capas foreground/monochrome en `drawable-nodpi`, adaptive launcher icon en `mipmap-anydpi` y PNG de respaldo para mdpi, hdpi, xhdpi, xxhdpi y xxxhdpi. El fondo negro de la master se convierte en transparencia para el icono monocromo de Android 13+.
- Windows: ICO multirresolución.
- Linux: PNG de 512 × 512.
- macOS: ICNS.
- Web/PWA: favicon y PNG de 16, 32, 48, 180, 192 y 512 píxeles.

Los recursos generados se eliminan y reconstruyen en cada ejecución para evitar restos de versiones anteriores. No los edites manualmente.

## Integración actual

El workflow **SOUNWD Android Beta** ejecuta pruebas del generador, instala los recursos mediante `tools/install_android_icons.py`, verifica el manifest y el icono monocromo, ejecuta Android Lint y compila APK debug/release. Los formatos de escritorio y web se generan, pero su empaquetado debe integrarse en los workflows de publicación de cada plataforma; generar un archivo no significa que ya esté incluido en un instalador.

# Identidad visual SOUNWD

## Imagen maestra única

La única fuente oficial es \`icon/sounwd-master.png\`. Para cambiar el aspecto de SOUNWD, sustituye esa imagen manteniendo el nombre y la ruta. Debe ser un PNG cuadrado, de al menos 128 × 128 px y no superar 20 MiB, 8192 px por lado ni 25 millones de píxeles.

## Regeneración

Desde la raíz del repositorio:

\`\`\`bash
python -m pip install Pillow
python assets/build_brand_assets.py
python tests/test_brand_assets.py
\`\`\`

El generador valida la imagen maestra y produce derivados para Windows (ICO), Linux (PNG de distintos tamaños) y Android Kivy (launcher/adaptive e imagen interna). También actualiza \`assets/sounwd.png\` como derivado de compatibilidad para el escritorio y el empaquetado existente. No edites los derivados manualmente.

Los workflows de escritorio y Android regeneran los recursos desde esta fuente antes de compilar. La beta Kotlin se mantiene separada y no sustituye la aplicación Android Kivy funcional.

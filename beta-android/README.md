# SOUNWD Android — beta visual

Esta beta parte de la aplicación Android nativa mínima que ya compilaba correctamente. Se ha mantenido esa base Kotlin/Android, sin incorporar Kivy, Buildozer, yt-dlp, permisos de red ni funciones de descarga.

## Alcance de esta etapa

- Identidad visual SOUNWD: grafito casi negro, carmesí, blanco y gris metálico.
- Calavera estilizada dentro de la pantalla y como icono de la aplicación.
- Icono adaptativo para Android 8.0 o posterior y recurso vectorial de compatibilidad para versiones anteriores.
- Pantalla inicial estática, desplazable y sin dependencias externas.
- No hay todavía descargas ni funciones de audio. Primero validamos que la aplicación se instale y abra de forma fiable.

## Compilar

Abre esta carpeta como proyecto en Android Studio y ejecuta `assembleDebug`.

El workflow **SOUNWD Android Beta** compila el APK de depuración y lo publica como artefacto de GitHub Actions.

# Política de seguridad de SOUNWD

## Informar de vulnerabilidades

Comunica posibles vulnerabilidades de forma privada mediante **GitHub Security Advisories → Report a vulnerability** en este repositorio. No publiques en incidencias públicas instrucciones de explotación, credenciales, tokens, datos personales ni enlaces privados.

## Componentes cubiertos

Esta política cubre la aplicación de escritorio Python, el descargador Android Kivy heredado, la beta Kotlin independiente, el generador de recursos gráficos y los workflows de CI.

## Controles actuales

- Los enlaces de descarga deben usar HTTPS y uno de los dominios oficiales exactos de YouTube. Se rechazan credenciales, puertos no estándar, espacios, caracteres de control y dominios similares.
- Las plantillas de salida se limitan a un único nombre de archivo y a campos yt-dlp permitidos. Se rechazan rutas, traversal, campos desconocidos y nombres reservados de Windows.
- El escritorio descarga primero en una ubicación temporal y publica únicamente archivos de audio regulares, sin sobrescribir archivos existentes.
- Android Kivy mantiene las descargas en el almacenamiento privado de la aplicación, valida que los ficheros exportados estén dentro de ese directorio y aplica límites por fichero, lote y espacio disponible.
- El generador de marca valida la imagen maestra, limita tamaño y dimensiones, rechaza enlaces simbólicos y escribe los recursos derivados de forma atómica.
- CI ejecuta pruebas de regresión, auditoría de dependencias con pip-audit, análisis CodeQL de Python y OSV-Scanner.

## Desarrollo seguro de Android

Android debe seguir el principio de mínimo privilegio. No añadas permisos de almacenamiento amplio, accesibilidad, cámara, micrófono, ubicación ni superposición si una función no los necesita. Mantén TLS activo, no uses código dinámico ni comandos de shell construidos con datos del usuario y trata títulos, metadatos, subtítulos y nombres remotos como contenido no confiable.

Cualquier nuevo servicio, receptor, proveedor, WebView, SDK, acceso a ficheros o integración nativa debe incluir una revisión de amenazas y pruebas antes de integrarse.

## Límites

Estas medidas reducen la superficie de ataque, pero no demuestran que el software sea invulnerable. yt-dlp, FFmpeg, extractores y servicios externos procesan contenido remoto no confiable y deben mantenerse actualizados. Los APK de depuración no son releases de producción. Una release necesita firma protegida y un proceso de publicación independiente.

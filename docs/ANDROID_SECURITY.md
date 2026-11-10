# Arquitectura de seguridad Android

## Estado actual

La aplicación Android de producción es la versión Kivy en \`android/\`. La beta Kotlin de \`beta-android/\` es un proyecto separado y no sustituye al descargador funcional.

## Límites de seguridad

- **Mínimo privilegio:** conserva únicamente los permisos que requiere la función actual. No solicites almacenamiento total ni permisos preventivos.
- **Almacenamiento privado:** descarga y procesa en el directorio privado de SOUNWD. Exporta solo después de una acción explícita del usuario.
- **Red:** acepta únicamente HTTPS y dominios exactos de YouTube. Mantén la verificación TLS activa y rechaza credenciales, puertos no estándar y hosts parecidos.
- **Sin ejecución dinámica:** no uses \`eval\`, \`exec\`, \`shell=True\` ni comandos construidos a partir de datos externos. Los argumentos para procesos deben ser listas y ejecutables fijos.
- **Contenido hostil:** títulos, nombres de canal, miniaturas, subtítulos y metadatos remotos no son confiables. Limita longitudes y nunca los uses como rutas.
- **Límites de recursos:** limita el tamaño de cada archivo, el tamaño total del lote, el número de elementos y reserva espacio libre para el sistema.
- **Publicación segura:** antes de exportar, comprueba que el archivo sea regular, no sea un enlace simbólico y permanezca dentro del almacenamiento privado de la aplicación.

## Dependencias Android

Las dependencias de ejecución de Android están fijadas en `android/buildozer.spec` y reflejadas en `android/requirements-audit.txt` para que los cambios de versiones sean explícitos y puedan revisarse con OSV-Scanner. `androidstorage4kivy` se conserva por compatibilidad con el flujo de exportación actual, pero su upstream está archivado; es un riesgo de mantenimiento conocido. No se sustituye por un puente nativo hasta contar con pruebas de compilación e instalación en dispositivo físico.

## Cambios futuros

Antes de añadir nuevas funciones, define qué permisos necesitan y por qué. Prefiere MediaStore o Storage Access Framework para exportaciones. No añadas servicios, receptores, proveedores, WebViews, código nativo ni SDK de terceros sin una revisión de amenazas, pruebas de permisos denegados y pruebas de traversal, symlinks y sobrescritura.

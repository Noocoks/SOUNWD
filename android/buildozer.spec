[app]
title = SOUNWD
package.name = sounwd
package.domain = org.sounwd
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
icon.filename = assets/generated/android/icon.png
icon.adaptive_foreground.filename = assets/generated/android/foreground.png
icon.adaptive_background.filename = assets/generated/android/background.png
version = 0.1.0
requirements = python3==3.12.10,hostpython3==3.12.10,kivy==2.3.1,yt-dlp==2026.10.26
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.allow_backup = False
android.extra_manifest_application_arguments = manifest_application_arguments.xml
android.res_xml = network_security_config.xml
android.add_src = ../beta-android/app/src/main/java
android.api = 35
android.minapi = 29
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True
p4a.bootstrap = sdl2
p4a.branch = master
p4a.commit = 58d21141f17c889bf8585f5665921d72028f8831
p4a.local_recipes = p4a-recipes
log_level = 2

[buildozer]
warn_on_root = 1

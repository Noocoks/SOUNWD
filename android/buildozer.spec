[app]
title = SOUNWD
package.name = sounwd
package.domain = org.sounwd
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1.0
requirements = python3==3.12.10,hostpython3==3.12.10,kivy,yt-dlp,androidstorage4kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 24
# NDK r28c enables 16 KB ELF page alignment by default.
android.ndk = 28c
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

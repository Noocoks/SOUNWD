[app]
title = SOUNWD
package.name = sounwd
package.domain = org.sounwd
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1.0
requirements = python3,kivy,yt-dlp,androidstorage4kivy
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 35
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True
p4a.bootstrap = sdl2
p4a.branch = master
log_level = 2

[buildozer]
warn_on_root = 1

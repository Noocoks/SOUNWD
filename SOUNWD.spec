# -*- mode: python ; coding: utf-8 -*-
"""Cross-platform one-file build with an early bootloader splash screen."""
import os
from PyInstaller.utils.hooks import collect_all
from PyInstaller.building.splash import Splash

deno = os.environ.get("DENO_PATH")
if not deno or not os.path.isfile(deno):
    raise RuntimeError("DENO_PATH must point to the Deno executable before building SOUNWD.")

datas = [("assets/sounwd.png", "assets"), ("assets/sounwd.ico", "assets")]
binaries = [(deno, ".")]
hiddenimports = ["yt_dlp_support", "PIL.ImageTk", "PIL._tkinter_finder"]

for package in ("customtkinter", "imageio_ffmpeg", "yt_dlp", "yt_dlp_ejs"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    ["src/gui.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

splash = Splash(
    "assets/sounwd-splash.png",
    binaries=a.binaries,
    datas=a.datas,
    text_pos=(112, 315),
    text_size=10,
    text_color="#B5BAC0",
    text_default="Iniciando SOUNWD...",
    always_on_top=True,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    splash,
    splash.binaries,
    a.binaries,
    a.datas,
    [],
    name="SOUNWD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/sounwd.ico" if os.name == "nt" else None,
)

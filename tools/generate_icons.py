#!/usr/bin/env python3
"""Generate every SOUNWD platform icon from icon/sounwd-master.png.

Install: python -m pip install Pillow
Run:     python tools/generate_icons.py
"""
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "icon" / "sounwd-master.png"
OUT = ROOT / "assets" / "generated"
BACKGROUND = (9, 9, 11, 255)


def square_cover(image: Image.Image, size: int) -> Image.Image:
    image = ImageOps.fit(image.convert("RGBA"), (size, size), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    return image


def square_contain(image: Image.Image, size: int, safe: float = 1.0) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    max_side = int(size * safe)
    art = image.copy()
    art.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    canvas.alpha_composite(art, ((size - art.width) // 2, (size - art.height) // 2))
    return canvas


def save_android(master: Image.Image) -> None:
    root = OUT / "android"
    (root / "drawable-nodpi").mkdir(parents=True, exist_ok=True)
    (root / "drawable").mkdir(parents=True, exist_ok=True)
    (root / "mipmap-anydpi-v26").mkdir(parents=True, exist_ok=True)
    master.save(root / "drawable-nodpi" / "sounwd_master.png", optimize=True)
    square_contain(master, 432, 0.64).save(root / "drawable" / "sounwd_launcher_foreground.png", optimize=True)
    (root / "mipmap-anydpi-v26" / "ic_launcher.xml").write_text(
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/sounwd_icon_background" />\n'
        '    <foreground android:drawable="@drawable/sounwd_launcher_foreground" />\n'
        '</adaptive-icon>\n',
        encoding="utf-8",
    )
    for density, pixels in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        folder = root / f"mipmap-{density}"
        folder.mkdir(parents=True, exist_ok=True)
        square_cover(master, pixels).save(folder / "ic_launcher.png", optimize=True)


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(
            f"Missing master image: {SOURCE.relative_to(ROOT)}. "
            "Put the approved master artwork at that exact path and rerun."
        )
    with Image.open(SOURCE) as opened:
        master = opened.convert("RGBA")
    if master.width < 256 or master.height < 256:
        raise SystemExit("Master image must be at least 256 x 256 pixels.")

    OUT.mkdir(parents=True, exist_ok=True)
    master.save(OUT / "sounwd-master.png", optimize=True)

    # Windows executable icon: multi-resolution ICO.
    windows = OUT / "windows"
    windows.mkdir(parents=True, exist_ok=True)
    square_cover(master, 256).save(
        windows / "SOUNWD.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    # Linux desktop icon and macOS ICNS share the same master artwork.
    linux = OUT / "linux"
    linux.mkdir(parents=True, exist_ok=True)
    square_cover(master, 512).save(linux / "sounwd.png", optimize=True)
    macos = OUT / "macos"
    macos.mkdir(parents=True, exist_ok=True)
    square_cover(master, 1024).save(macos / "SOUNWD.icns", format="ICNS")

    # Web/PWA favicons.
    web = OUT / "web"
    web.mkdir(parents=True, exist_ok=True)
    for pixels in (16, 32, 48, 180, 192, 512):
        square_cover(master, pixels).save(web / f"icon-{pixels}.png", optimize=True)
    square_cover(master, 32).save(web / "favicon.ico", format="ICO")

    save_android(master)
    print(f"Generated SOUNWD icons from {SOURCE.relative_to(ROOT)} into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

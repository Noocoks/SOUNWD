#!/usr/bin/env python3
"""Generate SOUNWD platform icons from the single master PNG.

Usage:
    python -m pip install Pillow
    python tools/generate_icons.py
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps

ROOT: Final = Path(__file__).resolve().parents[1]
SOURCE: Final = ROOT / "icon" / "sounwd-master.png"
OUT: Final = ROOT / "assets" / "generated"
MIN_SIZE: Final = 256
MAX_DIMENSION: Final = 8192
MAX_PIXELS: Final = 25_000_000


def square_cover(image: Image.Image, size: int) -> Image.Image:
    """Fill a square canvas, cropping equally around the center."""
    return ImageOps.fit(
        image.convert("RGBA"),
        (size, size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )


def square_contain(image: Image.Image, size: int, safe_area: float = 1.0) -> Image.Image:
    """Fit the full artwork inside a transparent square canvas."""
    if not 0 < safe_area <= 1:
        raise ValueError("safe_area must be greater than 0 and at most 1")

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    max_side = round(size * safe_area)
    artwork = image.convert("RGBA").copy()
    artwork.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    canvas.alpha_composite(
        artwork,
        ((size - artwork.width) // 2, (size - artwork.height) // 2),
    )
    return canvas


def save_android(master: Image.Image, output: Path) -> None:
    """Write Android in-app, adaptive launcher, monochrome and density assets."""
    root = output / "android"
    nodpi = root / "drawable-nodpi"
    adaptive = root / "mipmap-anydpi"
    for directory in (nodpi, adaptive):
        directory.mkdir(parents=True, exist_ok=True)

    master.save(nodpi / "sounwd_mark.png", optimize=True)
    square_contain(master, 432, safe_area=0.64).save(
        nodpi / "sounwd_launcher_foreground.png", optimize=True
    )

    # Android themed icons use alpha as a tint mask. The approved master has
    # a black background, so derive the mask from visible non-black artwork.
    monochrome = Image.new("RGBA", master.size, (255, 255, 255, 0))
    source_pixels = master.convert("RGBA").load()
    mask_pixels = []
    for y in range(master.height):
        for x in range(master.width):
            red, green, blue, source_alpha = source_pixels[x, y]
            alpha = min(max(red, green, blue), source_alpha)
            mask_pixels.append((255, 255, 255, alpha if alpha > 8 else 0))
    monochrome.putdata(mask_pixels)
    monochrome.save(nodpi / "sounwd_launcher_monochrome.png", optimize=True)

    (adaptive / "ic_launcher.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '    <background android:drawable="@color/sounwd_icon_background" />\n'
        '    <foreground android:drawable="@drawable/sounwd_launcher_foreground" />\n'
        '    <monochrome android:drawable="@drawable/sounwd_launcher_monochrome" />\n'
        '</adaptive-icon>\n',
        encoding="utf-8",
    )



def generate(source: Path = SOURCE, output: Path = OUT) -> None:
    """Validate the master artwork and regenerate all platform assets."""
    if not source.is_file():
        raise FileNotFoundError(
            f"Master image not found: {source}. "
            "Place the approved image at icon/sounwd-master.png."
        )

    if source.is_symlink():
        raise ValueError("The master image must not be a symbolic link.")

    with Image.open(source) as opened:
        if opened.format != "PNG":
            raise ValueError("The master artwork must be a PNG file.")
        width, height = opened.size
        if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_PIXELS:
            raise ValueError(
                f"Master image exceeds the safe limit ({MAX_DIMENSION}px per side "
                f"and {MAX_PIXELS:,} total pixels): {width}x{height}."
            )
        if min(opened.size) < MIN_SIZE:
            raise ValueError(
                f"Master image must be at least {MIN_SIZE}x{MIN_SIZE}; "
                f"received {width}x{height}."
            )
        opened.load()
        master = opened.convert("RGBA")

    if min(master.size) < MIN_SIZE:
        raise ValueError(
            f"Master image must be at least {MIN_SIZE}x{MIN_SIZE}; "
            f"received {master.width}x{master.height}."
        )

    # Only clean the fixed generated-assets directory. Never recursively delete
    # an arbitrary caller-supplied path.
    if output.is_symlink():
        raise ValueError("The generated-assets output directory must not be a symbolic link.")
    if output.exists() and output.resolve() == OUT.resolve():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    master.save(output / "sounwd-master.png", optimize=True)

    windows = output / "windows"
    windows.mkdir()
    square_cover(master, 256).save(
        windows / "SOUNWD.ico",
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )

    linux = output / "linux"
    linux.mkdir()
    square_cover(master, 512).save(linux / "sounwd.png", optimize=True)

    macos = output / "macos"
    macos.mkdir()
    square_cover(master, 1024).save(macos / "SOUNWD.icns", format="ICNS")

    web = output / "web"
    web.mkdir()
    for pixels in (16, 32, 48, 180, 192, 512):
        square_cover(master, pixels).save(
            web / f"icon-{pixels}.png", optimize=True
        )
    square_cover(master, 32).save(web / "favicon.ico", format="ICO")

    save_android(master, output)


def main() -> None:
    generate()
    print(f"Generated SOUNWD icons from {SOURCE.relative_to(ROOT)} into {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""Generate every SOUNWD platform icon from one canonical brand image.

Source of truth: assets/sounwd.png. Generated files are build outputs and are
intentionally not committed; each desktop/Android workflow recreates them.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets" / "sounwd.png"
GENERATED = ROOT / "assets" / "generated"
ANDROID_GENERATED = ROOT / "android" / "assets" / "generated" / "android"
SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512)
BG = (9, 9, 11, 255)


def load_master() -> Image.Image:
    if not MASTER.is_file():
        raise FileNotFoundError(f"Canonical SOUNWD image missing: {MASTER}")
    with Image.open(MASTER) as source:
        if source.width != source.height:
            raise ValueError(f"Brand master must be square, got {source.size}")
        if source.width < 128:
            raise ValueError(f"Brand master must be at least 128px, got {source.size}")
        return source.convert("RGBA")


def contain_on_background(master: Image.Image, size: int, *, padding: float = 0.12) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), BG)
    inner = max(1, round(size * (1 - 2 * padding)))
    artwork = ImageOps.contain(master, (inner, inner), method=Image.Resampling.LANCZOS)
    canvas.alpha_composite(artwork, ((size - artwork.width) // 2, (size - artwork.height) // 2))
    return canvas


def main() -> None:
    master = load_master()
    for size in SIZES:
        folder = GENERATED / "linux" / f"{size}x{size}"
        folder.mkdir(parents=True, exist_ok=True)
        # Linux theme icon uses the transparent master without a platform tile.
        master.resize((size, size), Image.Resampling.LANCZOS).save(
            folder / "sounwd.png", optimize=True
        )

    ico_sizes = [(size, size) for size in SIZES if size <= 256]
    master.save(GENERATED / "sounwd.ico", format="ICO", sizes=ico_sizes)

    ANDROID_GENERATED.mkdir(parents=True, exist_ok=True)
    # Android's legacy launcher icon is a square tile with generous safe-area
    # padding so OEM launchers can apply their own rounded/circular masks.
    contain_on_background(master, 512).save(
        ANDROID_GENERATED / "icon.png", optimize=True
    )
    # Keep a standalone transparent foreground for future adaptive-icon wiring.
    ImageOps.contain(master, (384, 384), method=Image.Resampling.LANCZOS).save(
        ANDROID_GENERATED / "foreground.png", optimize=True
    )
    Image.new("RGBA", (512, 512), BG).save(
        ANDROID_GENERATED / "background.png", optimize=True
    )

    print(f"Brand master: {MASTER} ({master.width}x{master.height})")
    print(f"Generated Windows ICO: {GENERATED / 'sounwd.ico'}")
    print(f"Generated Linux PNG sizes: {', '.join(map(str, SIZES))}")
    print(f"Generated Android launcher icon: {ANDROID_GENERATED / 'icon.png'}")


if __name__ == "__main__":
    main()

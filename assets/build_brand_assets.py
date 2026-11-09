"""Generate all SOUNWD platform assets from the sole canonical PNG."""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets" / "sounwd.png"
GENERATED = ROOT / "assets" / "generated"
ANDROID_GENERATED = ROOT / "android" / "assets" / "generated" / "android"
SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512)
BG = (9, 9, 11, 255)


def main():
    if not MASTER.is_file():
        raise FileNotFoundError(f"Canonical SOUNWD image missing: {MASTER}")
    with Image.open(MASTER) as source:
        if source.width != source.height or source.width < 128:
            raise ValueError(f"Canonical brand master must be square and >=128px, got {source.size}")
        master = source.convert("RGBA")

    for size in SIZES:
        folder = GENERATED / "linux" / f"{size}x{size}"
        folder.mkdir(parents=True, exist_ok=True)
        master.resize((size, size), Image.Resampling.LANCZOS).save(folder / "sounwd.png", optimize=True)

    ico_sizes = [(size, size) for size in SIZES if size <= 256]
    master.save(ROOT / "assets" / "sounwd.ico", format="ICO", sizes=ico_sizes)
    (GENERATED).mkdir(parents=True, exist_ok=True)
    master.save(GENERATED / "sounwd.ico", format="ICO", sizes=ico_sizes)

    ANDROID_GENERATED.mkdir(parents=True, exist_ok=True)
    tile = Image.new("RGBA", (512, 512), BG)
    artwork = ImageOps.contain(master, (390, 390), method=Image.Resampling.LANCZOS)
    tile.alpha_composite(artwork, ((512-artwork.width)//2, (512-artwork.height)//2))
    tile.save(ANDROID_GENERATED / "icon.png", optimize=True)

    foreground = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    artwork = ImageOps.contain(master, (300, 300), method=Image.Resampling.LANCZOS)
    foreground.alpha_composite(artwork, ((432-artwork.width)//2, (432-artwork.height)//2))
    foreground.save(ANDROID_GENERATED / "foreground.png", optimize=True)
    Image.new("RGBA", (432, 432), BG).save(ANDROID_GENERATED / "background.png", optimize=True)
    master.save(ANDROID_GENERATED / "brand.png", optimize=True)

    print(f"Generated Windows ICO, Linux PNGs ({', '.join(map(str, SIZES))}) and Android launcher/adaptive assets from {MASTER}")


if __name__ == "__main__":
    main()

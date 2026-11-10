"""Generate platform icon assets from the canonical, untrusted-at-build-time PNG."""
from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets" / "sounwd.png"
GENERATED = ROOT / "assets" / "generated"
ANDROID_GENERATED = ROOT / "android" / "assets" / "generated" / "android"
SIZES = (16, 24, 32, 48, 64, 96, 128, 192, 256, 512)
BG = (9, 9, 11, 255)
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_DIMENSION = 8192
MAX_PIXELS = 25_000_000
MIN_DIMENSION = 128

Image.MAX_IMAGE_PIXELS = MAX_PIXELS
warnings.simplefilter("error", Image.DecompressionBombWarning)


def _reject_symlink_chain(path: Path) -> None:
    current = path
    while current != ROOT and ROOT in current.parents:
        if current.is_symlink():
            raise ValueError(f"Symbolic links are not allowed in asset paths: {current}")
        current = current.parent
    if current != ROOT and path != ROOT:
        raise ValueError(f"Asset path escapes repository root: {path}")


def _safe_directory(path: Path) -> Path:
    _reject_symlink_chain(path)
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"Generated asset directory escapes repository root: {path}")
    path.mkdir(parents=True, exist_ok=True)
    _reject_symlink_chain(path)
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError(f"Generated asset directory escapes repository root: {path}")
    if not path.is_dir():
        raise ValueError(f"Generated asset path is not a directory: {path}")
    return path


def _safe_output_file(path: Path) -> Path:
    _safe_directory(path.parent)
    _reject_symlink_chain(path)
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(ROOT):
        raise ValueError(f"Generated asset file escapes repository root: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Generated asset path is not a regular file: {path}")
    if path.is_symlink():
        raise ValueError(f"Generated asset file must not be a symbolic link: {path}")
    return path


def _save_atomic(image: Image.Image, path: Path, image_format: str, **kwargs) -> None:
    _safe_output_file(path)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        image.save(temporary, format=image_format, **kwargs)
        os.chmod(temporary, 0o644)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_master() -> Image.Image:
    _reject_symlink_chain(MASTER)
    if not MASTER.is_file():
        raise FileNotFoundError(f"Canonical SOUNWD image missing: {MASTER}")
    if MASTER.stat().st_size <= 0 or MASTER.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(
            f"Canonical image must be between 1 byte and {MAX_FILE_BYTES // (1024 * 1024)} MiB."
        )
    with Image.open(MASTER) as source:
        if source.format != "PNG":
            raise ValueError("Canonical brand master must be a PNG file.")
        width, height = source.size
        if width != height or min(width, height) < MIN_DIMENSION:
            raise ValueError(
                f"Canonical brand master must be square and >= {MIN_DIMENSION}px, got {source.size}"
            )
        if width > MAX_DIMENSION or height > MAX_DIMENSION or width * height > MAX_PIXELS:
            raise ValueError(
                f"Canonical brand master exceeds {MAX_DIMENSION}px per side "
                f"or {MAX_PIXELS:,} pixels: {source.size}"
            )
        source.load()
        return source.convert("RGBA")


def main() -> None:
    master = _load_master()
    _safe_directory(GENERATED)
    _safe_directory(ANDROID_GENERATED)

    for size in SIZES:
        folder = _safe_directory(GENERATED / "linux" / f"{size}x{size}")
        derivative = master.resize((size, size), Image.Resampling.LANCZOS)
        _save_atomic(derivative, folder / "sounwd.png", "PNG", optimize=True)

    ico_sizes = [(size, size) for size in SIZES if size <= 256]
    _save_atomic(master, ROOT / "assets" / "sounwd.ico", "ICO", sizes=ico_sizes)
    _save_atomic(master, GENERATED / "sounwd.ico", "ICO", sizes=ico_sizes)

    tile = Image.new("RGBA", (512, 512), BG)
    artwork = ImageOps.contain(master, (390, 390), method=Image.Resampling.LANCZOS)
    tile.alpha_composite(artwork, ((512 - artwork.width) // 2, (512 - artwork.height) // 2))
    _save_atomic(tile, ANDROID_GENERATED / "icon.png", "PNG", optimize=True)

    foreground = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    artwork = ImageOps.contain(master, (300, 300), method=Image.Resampling.LANCZOS)
    foreground.alpha_composite(
        artwork, ((432 - artwork.width) // 2, (432 - artwork.height) // 2)
    )
    _save_atomic(foreground, ANDROID_GENERATED / "foreground.png", "PNG", optimize=True)
    background = Image.new("RGBA", (432, 432), BG)
    _save_atomic(background, ANDROID_GENERATED / "background.png", "PNG", optimize=True)
    _save_atomic(master, ANDROID_GENERATED / "brand.png", "PNG", optimize=True)

    print(
        "Generated Windows ICO, Linux PNGs "
        f"({', '.join(map(str, SIZES))}) and Android launcher/adaptive assets from {MASTER}"
    )


if __name__ == "__main__":
    main()

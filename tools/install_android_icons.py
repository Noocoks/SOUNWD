#!/usr/bin/env python3
"""Generate and safely install Android resources from the approved master icon."""
from __future__ import annotations

import shutil
from pathlib import Path

from generate_icons import OUT, ROOT, generate

RES = ROOT / "app" / "src" / "main" / "res"


def copy_resource(source: Path, destination_dir: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise FileNotFoundError(f"Expected generated Android resource is missing or unsafe: {source}")
    if destination_dir.is_symlink():
        raise ValueError(f"Android resource directory must not be a symbolic link: {destination_dir}")
    destination_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination_dir / source.name)


def install() -> None:
    generate()
    generated = OUT / "android"

    # Remove obsolete resources before copying the new master-derived assets.
    for old in (
        RES / "mipmap-anydpi-v26" / "ic_launcher.xml",
        RES / "mipmap-anydpi" / "ic_launcher.xml",
        RES / "drawable" / "sounwd_mark.xml",
    ):
        if old.is_symlink() or old.is_file():
            old.unlink()
    obsolete_dir = RES / "mipmap-anydpi-v26"
    if obsolete_dir.is_dir() and not obsolete_dir.is_symlink():
        try:
            obsolete_dir.rmdir()
        except OSError:
            raise RuntimeError(f"Obsolete Android resource directory is not empty: {obsolete_dir}")

    for name in (
        "sounwd_mark.png",
        "sounwd_launcher_foreground.png",
        "sounwd_launcher_monochrome.png",
    ):
        copy_resource(generated / "drawable-nodpi" / name, RES / "drawable-nodpi")

    copy_resource(generated / "mipmap-anydpi" / "ic_launcher.xml", RES / "mipmap-anydpi")
    for density in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
        copy_resource(
            generated / f"mipmap-{density}" / "ic_launcher.png",
            RES / f"mipmap-{density}",
        )

    required = (
        RES / "drawable-nodpi" / "sounwd_mark.png",
        RES / "drawable-nodpi" / "sounwd_launcher_foreground.png",
        RES / "drawable-nodpi" / "sounwd_launcher_monochrome.png",
        RES / "mipmap-anydpi" / "ic_launcher.xml",
        RES / "mipmap-mdpi" / "ic_launcher.png",
        RES / "mipmap-xxxhdpi" / "ic_launcher.png",
    )
    if any(not item.is_file() or item.stat().st_size == 0 for item in required):
        raise RuntimeError("Android icon installation is incomplete")
    if (RES / "mipmap-anydpi-v26").exists():
        raise RuntimeError("Obsolete API 26 launcher resource directory remains")


if __name__ == "__main__":
    install()
    print("Android master-derived launcher and in-app assets installed.")

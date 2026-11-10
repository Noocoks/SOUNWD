"""Verify deterministic platform derivatives and hostile-input rejection."""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sounwd_brand_assets", ROOT / "assets" / "build_brand_assets.py"
)
brand = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brand)

# Run once against the repository master, then verify all platform outputs.
brand.main()
master = Image.open(ROOT / "assets" / "sounwd.png").convert("RGBA")
generated = ROOT / "assets" / "generated"
for size in brand.SIZES:
    image = Image.open(generated / "linux" / f"{size}x{size}" / "sounwd.png").convert("RGBA")
    assert image.size == (size, size), (size, image.size)
    expected = master.resize((size, size), Image.Resampling.LANCZOS)
    assert ImageChops.difference(image, expected).getbbox() is None, size

ico = Image.open(ROOT / "assets" / "sounwd.ico")
assert ico.format == "ICO"
android = ROOT / "android" / "assets" / "generated" / "android"
for name in ("icon.png", "foreground.png", "background.png", "brand.png"):
    assert (android / name).is_file(), name
assert Image.open(android / "brand.png").convert("RGBA").size == master.size
assert Image.open(android / "icon.png").size == (512, 512)

desktop_spec = (ROOT / "SOUNWD.spec").read_text(encoding="utf-8")
assert '("assets/sounwd.ico", "assets")' in desktop_spec, "Windows runtime ICO must be bundled"
buildozer_spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
for setting in (
    "icon.filename = assets/generated/android/icon.png",
    "icon.adaptive_foreground.filename = assets/generated/android/foreground.png",
    "icon.adaptive_background.filename = assets/generated/android/background.png",
):
    assert setting in buildozer_spec, setting
main_source = (ROOT / "android" / "main.py").read_text(encoding="utf-8")
assert 'self.label("◖♪"' not in main_source
assert 'generated" / "android" / "brand.png' in main_source
assert "BG=(9/255,9/255,11/255,1)" in main_source
assert "LAVENDER=(178/255,15/255,50/255,1)" in main_source


class BrandAssetSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self.old = (brand.ROOT, brand.MASTER, brand.GENERATED, brand.ANDROID_GENERATED)
        brand.ROOT = self.root
        brand.MASTER = self.assets / "sounwd.png"
        brand.GENERATED = self.assets / "generated"
        brand.ANDROID_GENERATED = self.root / "android" / "assets" / "generated" / "android"
        Image.new("RGBA", (128, 128), (20, 20, 20, 255)).save(brand.MASTER, format="PNG")

    def tearDown(self):
        brand.ROOT, brand.MASTER, brand.GENERATED, brand.ANDROID_GENERATED = self.old
        self.temp.cleanup()

    def test_rejects_non_png_master(self):
        Image.new("RGB", (128, 128), "red").save(brand.MASTER, format="JPEG")
        with self.assertRaises(ValueError):
            brand.main()

    def test_rejects_oversized_master_dimensions(self):
        Image.new("RGBA", (brand.MAX_DIMENSION + 1, 128)).save(brand.MASTER, format="PNG")
        with self.assertRaises(ValueError):
            brand.main()

    def test_rejects_oversized_master_file_before_decoding(self):
        brand.MASTER.write_bytes(b"x" * (brand.MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError):
            brand.main()

    def test_rejects_symlinked_master(self):
        if os.name == "nt":
            self.skipTest("Creating file symlinks may require Windows Developer Mode.")
        real = self.assets / "real.png"
        Image.new("RGBA", (128, 128)).save(real, format="PNG")
        brand.MASTER.unlink()
        brand.MASTER.symlink_to(real)
        with self.assertRaises(ValueError):
            brand.main()

    def test_rejects_symlinked_generated_directory(self):
        if os.name == "nt":
            self.skipTest("Creating directory symlinks may require Windows Developer Mode.")
        outside = self.root / "outside"
        outside.mkdir()
        brand.GENERATED.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            brand.main()

    def test_rejects_symlinked_generated_file(self):
        if os.name == "nt":
            self.skipTest("Creating file symlinks may require Windows Developer Mode.")
        folder = brand.GENERATED / "linux" / "16x16"
        folder.mkdir(parents=True)
        outside = self.root / "outside.png"
        Image.new("RGBA", (16, 16)).save(outside, format="PNG")
        (folder / "sounwd.png").symlink_to(outside)
        with self.assertRaises(ValueError):
            brand.main()


if __name__ == "__main__":
    unittest.main(verbosity=2)

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("brand_assets", ROOT / "assets" / "build_brand_assets.py")
brand = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(brand)


class BrandGeneratorSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = (brand.ROOT, brand.MASTER, brand.GENERATED, brand.ANDROID_GENERATED)
        brand.ROOT = self.root
        brand.MASTER = self.root / "icon" / "sounwd-master.png"
        brand.GENERATED = self.root / "assets" / "generated"
        brand.ANDROID_GENERATED = self.root / "android" / "assets" / "generated" / "android"
        brand.MASTER.parent.mkdir(parents=True)
        Image.new("RGBA", (256, 256), (20, 20, 20, 255)).save(brand.MASTER)

    def tearDown(self):
        brand.ROOT, brand.MASTER, brand.GENERATED, brand.ANDROID_GENERATED = self.old
        self.temp.cleanup()

    def test_rejects_non_png_master(self):
        Image.new("RGB", (256, 256)).save(brand.MASTER, format="JPEG")
        with self.assertRaises(ValueError):
            brand._load_master()

    def test_rejects_oversized_master_file(self):
        brand.MASTER.write_bytes(b"x" * (brand.MAX_FILE_BYTES + 1))
        with self.assertRaises(ValueError):
            brand._load_master()

    def test_rejects_symlinked_master(self):
        if os.name == "nt":
            self.skipTest("Symlink creation may require Developer Mode.")
        real = self.root / "real.png"
        Image.new("RGBA", (256, 256)).save(real)
        brand.MASTER.unlink()
        brand.MASTER.symlink_to(real)
        with self.assertRaises(ValueError):
            brand._load_master()

    def test_rejects_symlinked_generated_directory(self):
        if os.name == "nt":
            self.skipTest("Symlink creation may require Developer Mode.")
        outside = self.root / "outside"
        outside.mkdir()
        brand.GENERATED.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            brand._safe_directory(brand.GENERATED)


if __name__ == "__main__":
    unittest.main(verbosity=2)

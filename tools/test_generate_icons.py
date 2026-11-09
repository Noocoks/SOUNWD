"""Regression tests for the SOUNWD icon generator."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from generate_icons import generate


class IconGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "master.png"
        self.output = self.root / "generated"

        # Deliberately non-square RGBA artwork to exercise crop/alpha handling.
        image = Image.new("RGBA", (640, 480), (20, 10, 30, 255))
        image.putpixel((0, 0), (255, 0, 0, 0))
        image.save(self.source)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generates_all_platform_families(self):
        generate(self.source, self.output)

        expected = [
            "windows/SOUNWD.ico",
            "linux/sounwd.png",
            "macos/SOUNWD.icns",
            "web/favicon.ico",
            "web/icon-16.png",
            "web/icon-32.png",
            "web/icon-48.png",
            "web/icon-180.png",
            "web/icon-192.png",
            "web/icon-512.png",
            "android/drawable-nodpi/sounwd_master.png",
            "android/drawable/sounwd_mark.png",
            "android/drawable/sounwd_launcher_foreground.png",
            "android/mipmap-anydpi-v26/ic_launcher.xml",
            "android/mipmap-mdpi/ic_launcher.png",
            "android/mipmap-hdpi/ic_launcher.png",
            "android/mipmap-xhdpi/ic_launcher.png",
            "android/mipmap-xxhdpi/ic_launcher.png",
            "android/mipmap-xxxhdpi/ic_launcher.png",
        ]
        for relative in expected:
            with self.subTest(resource=relative):
                target = self.output / relative
                self.assertTrue(target.is_file(), f"Missing generated resource: {relative}")
                self.assertGreater(target.stat().st_size, 0)

    def test_android_adaptive_icon_is_well_formed_xml(self):
        generate(self.source, self.output)
        xml_path = self.output / "android/mipmap-anydpi-v26/ic_launcher.xml"
        root = ET.parse(xml_path).getroot()
        self.assertEqual(root.tag, "adaptive-icon")
        self.assertEqual(len(root), 2)

    def test_rejects_too_small_master(self):
        tiny = self.root / "tiny.png"
        Image.new("RGB", (128, 128)).save(tiny)
        with self.assertRaisesRegex(ValueError, "at least 256x256"):
            generate(tiny, self.output)

    def test_rejects_missing_master(self):
        with self.assertRaises(FileNotFoundError):
            generate(self.root / "missing.png", self.output)


if __name__ == "__main__":
    unittest.main()

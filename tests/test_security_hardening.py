import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from security import validate_youtube_url, validate_output_template
sys.path.insert(0, str(ROOT / "android"))
from android_security import is_supported_youtube_url, is_safe_private_file, safe_output_template


class HardenedInputTests(unittest.TestCase):
    def test_android_manifest_build_config_disables_backup(self):
        spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
        self.assertRegex(spec, r"(?m)^android\\.allow_backup\\s*=\\s*False\\s*$")
        sitecustomize = (ROOT / "android" / "sitecustomize.py").read_text(encoding="utf-8")
        self.assertNotIn("sys.argv", sitecustomize)
        self.assertNotIn("ANDROID_PRIVATE", sitecustomize)
        self.assertNotIn("ANDROID_ARGUMENT", sitecustomize)
        self.assertNotIn("sys.path", sitecustomize)

    def test_url_allowlist_and_parser_confusion(self):
        for host in ("youtube.com", "www.youtube.com", "music.youtube.com", "m.youtube.com", "youtu.be"):
            value = f"https://{host}/watch?v=abc"
            self.assertTrue(validate_youtube_url(value))
            self.assertTrue(is_supported_youtube_url(value))
        rejected = (
            "http://youtube.com/watch?v=x",
            "https://youtube.com.evil.example/watch?v=x",
            "https://youtube.com@evil.example/watch?v=x",
            "https://user:pass@youtube.com/watch?v=x",
            "https://youtube.com:444/watch?v=x",
            "https://youtube.com./watch?v=x",
            "https://evil.youtube.com/watch?v=x",
            " https://youtube.com/watch?v=x",
            "https://youtube.com/\nwatch",
            "https://youtube.com/\u200bwatch",
            "https://youtube.com\\@evil.example/x",
        )
        for value in rejected:
            with self.subTest(value=value):
                self.assertFalse(validate_youtube_url(value))
                self.assertFalse(is_supported_youtube_url(value))

    def test_private_path_rejects_symlinks_and_external_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "private"
            root.mkdir()
            inside = root / "audio.mp3"
            outside = Path(temp) / "outside.mp3"
            inside.write_bytes(b"audio")
            outside.write_bytes(b"outside")
            self.assertTrue(is_safe_private_file(inside, root))
            self.assertFalse(is_safe_private_file(outside, root))
            if sys.platform != "win32":
                link = root / "linked.mp3"
                link.symlink_to(outside)
                self.assertFalse(is_safe_private_file(link, root))

    def test_safe_filename_templates(self):
        valid = "%(title)s - %(uploader)s.%(ext)s"
        self.assertEqual(validate_output_template(valid), valid)
        self.assertEqual(safe_output_template(valid), valid)
        for value in ("../escape.mp3", "/tmp/escape.mp3", "folder/file.mp3",
                      "%(filepath)s", "CON.mp3", "LPT1.%(ext)s",
                      "%(title)s;touch bad", "%(title)s\\..\\evil"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_output_template(value)
                with self.assertRaises(ValueError):
                    safe_output_template(value)


if __name__ == "__main__":
    unittest.main(verbosity=2)

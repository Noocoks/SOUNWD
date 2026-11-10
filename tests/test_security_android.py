import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "android"))
from android_security import is_supported_youtube_url, safe_output_template, validate_advanced_options


class AndroidSecurityTests(unittest.TestCase):
    def test_url_validation(self):
        self.assertTrue(is_supported_youtube_url("https://youtu.be/abc"))
        self.assertTrue(is_supported_youtube_url("https://music.youtube.com/watch?v=abc"))
        for value in (
            "http://youtube.com/watch?v=x",
            "https://youtube.com.evil.test/watch?v=x",
            "https://evil.youtube.com/watch?v=x",
            "https://youtube.com@evil.test/watch?v=x",
            "https://youtube.com:444/watch?v=x",
            "https://user:pass@youtube.com/watch?v=x",
            "https://youtube.com/\nwatch",
        ):
            with self.subTest(value=value):
                self.assertFalse(is_supported_youtube_url(value))

    def test_safe_output_template(self):
        self.assertEqual(safe_output_template(""), "%(title)s.%(ext)s")
        self.assertEqual(safe_output_template("%(title)s - %(uploader)s.%(ext)s"),
                         "%(title)s - %(uploader)s.%(ext)s")
        for value in ("../escape.%(ext)s", "folder/file.%(ext)s",
                      "%(filepath)s.%(ext)s", "%(title)s\\..\\escape"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    safe_output_template(value)

    def test_advanced_options_are_bounded(self):
        for options in (
            {"retries": "999"},
            {"limit_rate": "1M;touch"},
            {"playlist_items": "1;rm -rf /"},
            {"ydl_format": "best;touch"},
            {"subtitle_langs": "en;rm"},
        ):
            with self.subTest(options=options):
                with self.assertRaises(ValueError):
                    validate_advanced_options(options)


if __name__ == "__main__":
    unittest.main()

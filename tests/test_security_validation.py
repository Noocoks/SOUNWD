import tempfile
import unittest
from pathlib import Path

from security import copy_downloaded_files, validate_advanced_options, validate_output_template, validate_youtube_url


class UrlValidationTests(unittest.TestCase):
    def test_accepts_supported_https_hosts(self):
        for host in ("youtube.com", "www.youtube.com", "music.youtube.com", "m.youtube.com", "youtu.be"):
            with self.subTest(host=host):
                self.assertTrue(validate_youtube_url(f"https://{host}/watch?v=abc"))

    def test_rejects_http_credentials_ports_and_host_suffix_attacks(self):
        invalid = (
            "http://youtube.com/watch?v=x",
            "https://youtube.com.evil.test/watch?v=x",
            "https://youtube.com@evil.test/watch?v=x",
            "https://user:pass@youtube.com/watch?v=x",
            "https://youtube.com:444/watch?v=x",
            "https://evil.youtube.com/watch?v=x",
            "https://youtube.com./watch?v=x",
        )
        for url in invalid:
            with self.subTest(url=url):
                self.assertFalse(validate_youtube_url(url))

    def test_rejects_control_chars_and_oversized_urls(self):
        self.assertFalse(validate_youtube_url("https://youtube.com/\nwatch"))
        self.assertFalse(validate_youtube_url("https://youtube.com/" + "a" * 2050))


class OutputTemplateTests(unittest.TestCase):
    def test_accepts_safe_templates(self):
        self.assertEqual(validate_output_template(""), "%(title)s.%(ext)s")
        self.assertEqual(validate_output_template("%(title)s - %(uploader)s.%(ext)s"), "%(title)s - %(uploader)s.%(ext)s")

    def test_rejects_traversal_absolute_paths_and_unknown_fields(self):
        for value in ("../evil.%(ext)s", "/tmp/evil.%(ext)s", "folder/file.%(ext)s",
                      "%(title)s\\..\\evil.%(ext)s", "%(filepath)s", "%(title)s/%(id)s"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_output_template(value)

    def test_rejects_unsafe_advanced_options(self):
        with self.assertRaises(ValueError):
            validate_advanced_options({"retries": "999"})
        with self.assertRaises(ValueError):
            validate_advanced_options({"ratelimit": "1M;touch"})
        with self.assertRaises(ValueError):
            validate_advanced_options({"playlist_items": "1;rm -rf /"})


class SafePublicationTests(unittest.TestCase):
    def test_never_overwrites_existing_file_and_ignores_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging, output = root / "staging", root / "output"
            staging.mkdir()
            output.mkdir()
            (staging / "song.mp3").write_bytes(b"new")
            (output / "song.mp3").write_bytes(b"old")
            (staging / "notes.txt").write_text("not audio")
            try:
                (staging / "linked.mp3").symlink_to(output / "song.mp3")
            except (OSError, NotImplementedError):
                pass
            saved = copy_downloaded_files(staging, output)
            self.assertEqual(len(saved), 1)
            self.assertEqual((output / "song.mp3").read_bytes(), b"old")
            self.assertEqual((output / "song (1).mp3").read_bytes(), b"new")
            self.assertFalse((output / "notes.txt").exists())


if __name__ == "__main__":
    unittest.main()

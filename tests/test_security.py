from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from security import (build_output_path, validate_advanced_options,
                      validate_output_template, validate_youtube_url)


class URLValidationTests(unittest.TestCase):
    def test_official_https_hosts(self):
        for url in (
            "https://youtube.com/watch?v=abc",
            "https://www.youtube.com/watch?v=abc",
            "https://music.youtube.com/watch?v=abc",
            "https://youtu.be/abc",
        ):
            self.assertEqual(validate_youtube_url(url), url)

    def test_rejects_http_userinfo_ports_and_lookalikes(self):
        bad = (
            "http://youtube.com/watch?v=x",
            "https://youtube.com.evil.example/watch?v=x",
            "https://youtube.com@evil.example/watch?v=x",
            "https://user:pass@youtube.com/watch?v=x",
            "https://youtube.com:444/watch?v=x",
            "https://youtube.com./watch?v=x",
            "https://youtube.com\\@evil.example/x",
            " https://youtube.com/watch?v=x",
            "https://youtube.com/\nmalicious",
            "file:///etc/passwd",
        )
        for url in bad:
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_youtube_url(url)


class OutputTemplateTests(unittest.TestCase):
    def test_allows_basic_filename_templates(self):
        for value in ("%(title)s.%(ext)s", "%(title)s - %(uploader)s.%(ext)s",
                      "%(playlist_index)s - %(title)s.%(ext)s"):
            self.assertEqual(validate_output_template(value), value)
        self.assertEqual(validate_output_template("Música - %(title)s.%(ext)s"), "Música - %(title)s.%(ext)s")

    def test_rejects_path_traversal_and_expression_injection(self):
        for value in ("../%(title)s.%(ext)s", "..\\evil.mp3", "/tmp/evil.mp3",
                      "C:evil.mp3", "%(unknown)s.mp3", "%(title)s/%(ext)s",
                      "%(title)s;touch bad", "%(title)s\x00.mp3", "CON.mp3"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_output_template(value)

    def test_output_confined_to_selected_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "downloads"
            root.mkdir()
            result = build_output_path(root, "%(title)s.%(ext)s")
            self.assertEqual(result.parent, root.resolve())

    def test_symlink_directory_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root, outside = base / "root", base / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "link").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                build_output_path(root, "link/evil.mp3")


class AdvancedOptionTests(unittest.TestCase):
    def test_bounds_and_rejects_injection_like_values(self):
        safe = validate_advanced_options({
            "format": "bestaudio/best", "outtmpl": "%(title)s.%(ext)s",
            "playlist_items": "1,3,5-8", "ratelimit": "2M",
            "retries": "10", "subtitleslangs": "es,en",
        })
        self.assertEqual(safe["retries"], 10)
        for key, value in (("playlist_items", "1;rm -rf /"),
                           ("ratelimit", "$(curl evil)"), ("retries", "999"),
                           ("subtitleslangs", "../../etc/passwd"),
                           ("format", "https://evil.example/file")):
            data = {"format": "bestaudio", "outtmpl": "%(title)s.%(ext)s",
                    "playlist_items": "", "ratelimit": "", "retries": "",
                    "subtitleslangs": ""}
            data[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_advanced_options(data)


if __name__ == "__main__":
    unittest.main()

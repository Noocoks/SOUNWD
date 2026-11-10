"""Security regression checks for the legacy Android downloader and Python entry points."""
from pathlib import Path
import ast
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from security import validate_youtube_url, validate_output_template


class AndroidPermissionTests(unittest.TestCase):
    def test_legacy_android_declares_only_internet_permission(self):
        spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
        lines = [line.split("=", 1)[1].strip() for line in spec.splitlines()
                 if line.strip().startswith("android.permissions")]
        self.assertEqual(lines, ["INTERNET"])
        self.assertNotIn("MANAGE_EXTERNAL_STORAGE", spec)
        self.assertNotIn("READ_EXTERNAL_STORAGE", spec)
        self.assertNotIn("WRITE_EXTERNAL_STORAGE", spec)

    def test_android_targets_supported_api_floor(self):
        spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
        self.assertRegex(spec, r"(?m)^android\.minapi\s*=\s*(2[9]|[3-9][0-9])\s*$")

    def test_kivy_download_path_uses_validation_and_private_storage(self):
        source = (ROOT / "android" / "main.py").read_text(encoding="utf-8")
        self.assertIn("validate_youtube_url(value)", source)
        self.assertIn("validate_advanced_options(", source)
        self.assertIn("build_output_path(self.private_dir", source)
        self.assertIn("is_path_within(p,self.private_dir)", source)
        self.assertIn("is_path_within(file_path,self.private_dir)", source)

    def test_android_and_desktop_validation_helpers_stay_identical(self):
        desktop = (ROOT / "src" / "security.py").read_bytes()
        android = (ROOT / "android" / "security.py").read_bytes()
        self.assertEqual(desktop, android)


class UnsafeExecutionTests(unittest.TestCase):
    def test_application_python_has_no_dynamic_eval_or_shell_true(self):
        roots = (ROOT / "src", ROOT / "android")
        for folder in roots:
            for path in folder.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        name = node.func.id if isinstance(node.func, ast.Name) else ""
                        if name in {"eval", "exec"}:
                            self.fail(f"Dynamic {name} call in {path}:{node.lineno}")
                        if any(isinstance(arg, ast.keyword) and arg.arg == "shell"
                               and isinstance(arg.value, ast.Constant) and arg.value.value is True
                               for arg in node.keywords):
                            self.fail(f"shell=True in {path}:{node.lineno}")


if __name__ == "__main__":
    unittest.main()

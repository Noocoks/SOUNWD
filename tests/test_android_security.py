"""Security regression checks for the legacy Android downloader and Python entry points."""
from pathlib import Path
import ast
import sys
import unittest
import xml.etree.ElementTree as ET

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
        self.assertIn("android.add_src = ../beta-android/app/src/main/java", spec)
        self.assertRegex(spec, r"(?m)^android\.allow_backup\s*=\s*False\s*$")
        self.assertIn("android.extra_manifest_application_arguments = manifest_application_arguments.xml", spec)
        self.assertIn("android.res_xml = network_security_config.xml", spec)
        args = (ROOT / "android" / "manifest_application_arguments.xml").read_text(encoding="utf-8")
        self.assertIn('android:usesCleartextTraffic="false"', args)
        self.assertIn('android:networkSecurityConfig="@xml/network_security_config"', args)
        network = ET.parse(ROOT / "android" / "network_security_config.xml").getroot()
        base = network.find("base-config")
        self.assertEqual(base.get("cleartextTrafficPermitted"), "false")
        self.assertEqual(base.find("trust-anchors/certificates").get("src"), "system")
        self.assertNotIn("androidstorage4kivy", spec)

    def test_android_targets_supported_api_floor(self):
        spec = (ROOT / "android" / "buildozer.spec").read_text(encoding="utf-8")
        self.assertRegex(spec, r"(?m)^android\.minapi\s*=\s*(2[9]|[3-9][0-9])\s*$")

    def test_kivy_download_path_uses_validation_and_private_storage(self):
        source = (ROOT / "android" / "main.py").read_text(encoding="utf-8")
        self.assertIn("validate_youtube_url(value)", source)
        self.assertIn("validate_advanced_options(", source)
        self.assertIn("build_output_path(self.private_dir", source)
        self.assertIn("is_path_within(p,self.private_dir)", source)
        self.assertNotIn("androidstorage4kivy", source)

    def test_native_mediastore_bridge_enforces_storage_boundary(self):
        source = (ROOT / "beta-android" / "app" / "src" / "main" / "java" / "org" / "sounwd" / "sounwd" / "SounwdMediaStore.java").read_text(encoding="utf-8")
        for invariant in (
            "Files.isSymbolicLink", "getCanonicalFile", "IS_PENDING",
            "MAX_AUDIO_BYTES", "MAX_EXPORTED_FILES", "EXPORTED_URIS.contains(value)", "beginExportBatch",
            "FLAG_GRANT_READ_URI_PERMISSION", "MediaStore.Audio.Media.EXTERNAL_CONTENT_URI",
        ):
            self.assertIn(invariant, source)

    def test_android_startup_log_does_not_dump_arguments_or_environment(self):
        source = (ROOT / "android" / "sitecustomize.py").read_text(encoding="utf-8")
        self.assertNotIn("sys.argv", source)
        self.assertNotIn('ANDROID_PRIVATE={!r}', source)
        self.assertNotIn('ANDROID_ARGUMENT={!r}', source)
        self.assertNotIn("sys.path={!r}", source)

    def test_android_and_desktop_validation_helpers_stay_identical(self):
        desktop = (ROOT / "src" / "security.py").read_bytes()
        android = (ROOT / "android" / "security.py").read_bytes()
        self.assertEqual(desktop, android)


    def test_native_kotlin_beta_manifest_is_minimal(self):
        manifest = ROOT / "beta-android" / "app" / "src" / "main" / "AndroidManifest.xml"
        root = ET.parse(manifest).getroot()
        android = "{http://schemas.android.com/apk/res/android}"
        self.assertEqual(root.findall("uses-permission"), [])
        app = root.find("application")
        self.assertIsNotNone(app)
        self.assertEqual(app.get(android + "allowBackup"), "false")
        self.assertEqual(app.get(android + "usesCleartextTraffic"), "false")
        activities = app.findall("activity")
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].get(android + "exported"), "true")
        filters = activities[0].findall("intent-filter")
        self.assertEqual(len(filters), 1)
        actions = [node.get(android + "name") for node in filters[0].findall("action")]
        categories = [node.get(android + "name") for node in filters[0].findall("category")]
        self.assertEqual(actions, ["android.intent.action.MAIN"])
        self.assertEqual(categories, ["android.intent.category.LAUNCHER"])

    def test_native_kotlin_beta_minimum_sdk_is_android_10(self):
        gradle = (ROOT / "beta-android" / "app" / "build.gradle.kts").read_text(encoding="utf-8")
        self.assertIn("minSdk = 29", gradle)

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
                        attr = node.func.attr if isinstance(node.func, ast.Attribute) else ""
                        if name in {"eval", "exec"} or (attr in {"eval", "exec"}):
                            self.fail(f"Dynamic {name or attr} call in {path}:{node.lineno}")
                        if isinstance(node.func, ast.Attribute) and node.func.attr in {"system", "popen"}:
                            if isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
                                self.fail(f"OS shell API {node.func.attr} in {path}:{node.lineno}")
                        if any(isinstance(arg, ast.keyword) and arg.arg == "shell"
                               and isinstance(arg.value, ast.Constant) and arg.value.value is True
                               for arg in node.keywords):
                            self.fail(f"shell=True in {path}:{node.lineno}")


if __name__ == "__main__":
    unittest.main()

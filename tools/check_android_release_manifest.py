"""Inspect the merged release manifest, not just the source manifest."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"
candidates = list((ROOT / "app" / "build" / "intermediates").rglob("AndroidManifest.xml"))
release_manifests = [
    path for path in candidates
    if "release" in path.parts and "merged" in path.parts
]
assert release_manifests, "No merged release manifest found; release manifest processing must run"
for path in release_manifests:
    root = ET.parse(path).getroot()
    application = root.find("application")
    assert application is not None, f"Missing application in {path}"
    assert application.get(ANDROID + "debuggable", "false").lower() != "true", f"Release manifest is debuggable: {path}"
    assert application.get(ANDROID + "usesCleartextTraffic", "false").lower() != "true", f"Release manifest allows cleartext: {path}"
    permissions = [n.get(ANDROID + "name") for n in root.findall("uses-permission")]
    assert not permissions, f"Unexpected permissions in minimal release: {permissions}"
print(f"Verified {len(release_manifests)} merged release manifest(s).")

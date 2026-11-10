"""Inspect the merged release manifest, not just the source manifest."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"
candidates = list((ROOT / "app" / "build" / "intermediates").rglob("AndroidManifest.xml"))
release_manifests = [
    path for path in candidates
    if "release" in path.parts and any(part.startswith("merged") for part in path.parts)
]
assert release_manifests, "No merged release manifest found; release manifest processing must run"

for path in release_manifests:
    root = ET.parse(path).getroot()
    uses_sdk = root.find("uses-sdk")
    assert uses_sdk is not None, f"Missing uses-sdk in {path}"
    assert uses_sdk.get(ANDROID + "minSdkVersion") == "29", f"Unexpected minimum API in {path}"
    assert uses_sdk.get(ANDROID + "targetSdkVersion") == "36", f"Unexpected target API in {path}"

    application = root.find("application")
    assert application is not None, f"Missing application in {path}"
    assert application.get(ANDROID + "debuggable", "false").lower() != "true", f"Release manifest is debuggable: {path}"
    assert application.get(ANDROID + "allowBackup", "true").lower() == "false", f"Release manifest enables backup: {path}"
    assert application.get(ANDROID + "usesCleartextTraffic", "true").lower() == "false", f"Release manifest allows cleartext: {path}"
    assert application.get(ANDROID + "networkSecurityConfig") == "@xml/network_security_config", f"Missing network security config: {path}"

    permissions = [n.get(ANDROID + "name") for n in root.findall("uses-permission")]
    assert not permissions, f"Unexpected permissions in minimal release: {permissions}"

    activities = application.findall("activity")
    assert len(activities) == 1, f"Unexpected exported activities in {path}"
    activity = activities[0]
    assert activity.get(ANDROID + "exported") == "true", f"Launcher activity must be explicitly exported: {path}"
    filters = activity.findall("intent-filter")
    assert len(filters) == 1, f"Unexpected launcher intent filters in {path}"
    actions = [n.get(ANDROID + "name") for n in filters[0].findall("action")]
    categories = [n.get(ANDROID + "name") for n in filters[0].findall("category")]
    assert actions == ["android.intent.action.MAIN"], f"Unexpected exported actions: {actions}"
    assert categories == ["android.intent.category.LAUNCHER"], f"Unexpected exported categories: {categories}"

    for component in ("service", "receiver", "provider"):
        assert not application.findall(component), f"Unexpected component in {path}: {component}"

print(f"Verified {len(release_manifests)} merged release manifest(s).")

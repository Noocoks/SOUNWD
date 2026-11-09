"""Fail-closed checks for the deliberately minimal Android beta manifest."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "src" / "main" / "AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"

root = ET.parse(MANIFEST).getroot()
assert root.tag == "manifest", "Unexpected manifest root"

permissions = [
    node.get(ANDROID + "name")
    for node in root.findall("uses-permission")
]
assert not permissions, f"Unexpected Android permissions in minimal beta: {permissions}"

application = root.find("application")
assert application is not None, "Missing application declaration"
assert application.get(ANDROID + "allowBackup") == "false", "App backup must remain disabled"
assert application.get(ANDROID + "usesCleartextTraffic") == "false", "Cleartext HTTP must remain disabled"
assert application.get(ANDROID + "debuggable", "false").lower() != "true", "Manifest must not force debuggable=true"

activities = application.findall("activity")
assert len(activities) == 1, f"Expected only the launcher activity, found {len(activities)}"
activity = activities[0]
assert activity.get(ANDROID + "exported") == "true", "Launcher activity must declare exported explicitly"
filters = activity.findall("intent-filter")
assert len(filters) == 1, "Only the launcher intent filter is allowed"
actions = [x.get(ANDROID + "name") for x in filters[0].findall("action")]
categories = [x.get(ANDROID + "name") for x in filters[0].findall("category")]
assert actions == ["android.intent.action.MAIN"], f"Unexpected exported actions: {actions}"
assert categories == ["android.intent.category.LAUNCHER"], f"Unexpected exported categories: {categories}"

for component in ("service", "receiver", "provider"):
    assert not application.findall(component), f"Unexpected exported-capable component: {component}"

print("Android manifest security checks passed.")

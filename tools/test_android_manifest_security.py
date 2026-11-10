"""Fail-closed checks for the deliberately minimal Android beta manifest."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "src" / "main" / "AndroidManifest.xml"
ANDROID = "{http://schemas.android.com/apk/res/android}"

root = ET.parse(MANIFEST).getroot()
assert root.tag == "manifest", "Unexpected manifest root"
gradle_text = (ROOT / "app" / "build.gradle.kts").read_text(encoding="utf-8")
assert "minSdk = 29" in gradle_text, "Android 10 (API 29) must remain the minimum supported version"
assert "targetSdk = 36" in gradle_text, "Android 16 (API 36) must remain the current target"

permissions = [
    node.get(ANDROID + "name")
    for node in root.findall("uses-permission")
]
assert not permissions, f"Unexpected Android permissions in minimal beta: {permissions}"

application = root.find("application")
assert application is not None, "Missing application declaration"
assert application.get(ANDROID + "allowBackup") == "false", "App backup must remain disabled"
assert application.get(ANDROID + "fullBackupContent") == "@xml/backup_rules", "Legacy backup rules must be explicit"
assert application.get(ANDROID + "dataExtractionRules") == "@xml/data_extraction_rules", "Android 12+ extraction rules must be explicit"
for rules_path, expected_root in (
    (ROOT / "app" / "src" / "main" / "res" / "xml" / "backup_rules.xml", "full-backup-content"),
    (ROOT / "app" / "src" / "main" / "res" / "xml" / "data_extraction_rules.xml", "data-extraction-rules"),
):
    rules_root = ET.parse(rules_path).getroot()
    assert rules_root.tag == expected_root, f"Invalid backup rules: {rules_path}"
    excludes = rules_root.findall(".//exclude")
    assert len(excludes) >= 5, f"Backup rules must exclude all app data: {rules_path}"
    assert {item.get("domain") for item in excludes} >= {"root", "file", "database", "sharedpref", "external"}, f"Incomplete backup exclusions: {rules_path}"
assert application.get(ANDROID + "usesCleartextTraffic") == "false", "Cleartext HTTP must remain disabled"
assert application.get(ANDROID + "networkSecurityConfig") == "@xml/network_security_config", "Explicit network security config is required"
network_config = ROOT / "app" / "src" / "main" / "res" / "xml" / "network_security_config.xml"
network_root = ET.parse(network_config).getroot()
assert network_root.tag == "network-security-config", "Invalid network security config"
base = network_root.find("base-config")
assert base is not None and base.get("cleartextTrafficPermitted") == "false", "Base config must reject cleartext"
anchors = base.find("trust-anchors")
assert anchors is not None, "System trust anchors must be explicit"
certificates = anchors.findall("certificates")
assert len(certificates) == 1 and certificates[0].get("src") == "system", "Only system CAs may be trusted"

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

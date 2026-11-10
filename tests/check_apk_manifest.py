"""Inspect the final Android APK manifest, not just buildozer.spec."""
from pathlib import Path
import os
import re
import subprocess
import sys

def fail(message: str) -> None:
    raise SystemExit("APK security check failed: " + message)

if len(sys.argv) != 2:
    fail("usage: check_apk_manifest.py path/to/app.apk")

apk = Path(sys.argv[1]).resolve()
if not apk.is_file():
    fail("APK does not exist")

sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or Path.home() / ".buildozer" / "android" / "platform" / "android-sdk")
build_tools = sorted((sdk / "build-tools").glob("*/aapt"), reverse=True)
if not build_tools:
    fail("Android aapt executable not found")
aapt = str(build_tools[0])

def run(*args: str) -> str:
    if args == ("dump", "xmltree"):
        command = [aapt, "dump", "xmltree", str(apk), "AndroidManifest.xml"]
    else:
        command = [aapt, *args, str(apk)]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout

permissions_output = run("dump", "permissions")
permissions = set(re.findall(r"uses-permission[^:]*: name='([^']+)'", permissions_output))
if permissions != {"android.permission.INTERNET"}:
    fail(f"unexpected Android permissions: {sorted(permissions)}")

badging = run("dump", "badging")
target = re.search(r"targetSdkVersion:'(\d+)'", badging)
if not target or int(target.group(1)) < 28:
    fail("target SDK must be 28+ so cleartext defaults to disabled")

manifest = run("dump", "xmltree")
backup = re.search(r"A: android:allowBackup\([^)]*\)=\(type 0x12\)0x([0-9a-fA-F]+)", manifest)
if not backup or int(backup.group(1), 16) != 0:
    fail("android:allowBackup is not explicitly false")

cleartext = re.search(r"A: android:usesCleartextTraffic\([^)]*\)=\(type 0x12\)0x([0-9a-fA-F]+)", manifest)
if not cleartext or int(cleartext.group(1), 16) != 0:
    fail("android:usesCleartextTraffic must be explicitly false")
if "android:networkSecurityConfig" not in manifest:
    fail("Android network security config is not attached to the application")

network_config = subprocess.run(
    [aapt, "dump", "xmltree", str(apk), "res/xml/network_security_config.xml"],
    check=True, capture_output=True, text=True,
).stdout
network_cleartext = re.search(
    r"A: cleartextTrafficPermitted\([^)]*\)=\(type 0x12\)0x([0-9a-fA-F]+)",
    network_config,
)
if not network_cleartext or int(network_cleartext.group(1), 16) != 0:
    fail("network security resource does not prohibit cleartext traffic")

for component in ("service", "receiver", "provider"):
    if re.search(rf"^\s*E: {component}\s*$", manifest, re.MULTILINE):
        fail(f"unexpected Android {component} component")

if len(re.findall(r"^\s*E: activity\s*$", manifest, re.MULTILINE)) != 1:
    fail("expected only the single launcher activity")

print("APK manifest security checks passed: INTERNET only, backup disabled, cleartext disabled, one activity, no services/receivers/providers.")

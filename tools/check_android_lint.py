"""Print every Android Lint finding and fail on errors/fatals."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "app" / "build" / "reports" / "lint-results-debug.xml"
if not REPORT.is_file():
    raise SystemExit(f"Android Lint XML report was not generated: {REPORT}")

root = ET.parse(REPORT).getroot()
issues = root.findall(".//issue")
blocking = []
for issue in issues:
    severity = issue.get("severity", "Warning")
    issue_id = issue.get("id", "Unknown")
    message = issue.get("message", "").strip()
    location = issue.find("location")
    file_name = location.get("file", "") if location is not None else ""
    line = location.find("line") if location is not None else None
    line_text = f":{line.get('number')}" if line is not None else ""
    print(f"{severity}: {issue_id}: {file_name}{line_text}: {message}")
    if severity.lower() in {"error", "fatal"}:
        blocking.append(issue)

print(f"Android Lint: {len(issues)} issue(s), {len(blocking)} blocking.")
if blocking:
    sys.exit(1)

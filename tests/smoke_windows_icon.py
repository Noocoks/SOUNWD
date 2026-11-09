"""Check the built Windows executable actually contains an extractable app icon."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: smoke_windows_icon.py PATH_TO_EXE")

exe = Path(sys.argv[1]).resolve()
if not exe.is_file():
    raise AssertionError(f"Windows executable not found: {exe}")

shell32 = ctypes.WinDLL("shell32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
large = (wintypes.HICON * 1)()
small = (wintypes.HICON * 1)()
shell32.ExtractIconExW.argtypes = [
    wintypes.LPCWSTR, ctypes.c_int,
    ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.HICON),
    wintypes.UINT,
]
shell32.ExtractIconExW.restype = wintypes.UINT
user32.DestroyIcon.argtypes = [wintypes.HICON]
user32.DestroyIcon.restype = wintypes.BOOL

count = shell32.ExtractIconExW(str(exe), 0, large, small, 1)
try:
    if count < 1 or not large[0] or not small[0]:
        raise AssertionError(
            "The packaged EXE does not expose both large and small embedded icons"
        )
finally:
    if large[0]:
        user32.DestroyIcon(large[0])
    if small[0]:
        user32.DestroyIcon(small[0])

print("Windows executable icon OK: large and small embedded icons are extractable")

"""SOUNWD Android compatibility override for CPython's grp extension.

Android's Bionic libc does not provide the glibc group-enumeration APIs
(setgrent/getgrent/endgrent). CPython's configure step in this p4a release
incorrectly enables grp, which then fails under the Android NDK compiler.
The app does not use grp, so omit that optional stdlib extension.
"""
import importlib.util
from pathlib import Path

import pythonforandroid


_p4a_root = Path(pythonforandroid.__file__).resolve().parent
_base_path = _p4a_root / "recipes" / "python3" / "__init__.py"
_spec = importlib.util.spec_from_file_location(
    "pythonforandroid.recipes._sounwd_python3_base", _base_path
)
_base_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base_module)
_BasePython3Recipe = _base_module.Python3Recipe


class SounwdPython3Recipe(_BasePython3Recipe):
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        source_dir = Path(self.get_build_dir(arch.arch))
        candidates = (
            source_dir / "Modules" / "Setup.stdlib.in",
            source_dir / "Modules" / "Setup",
        )
        for setup_file in candidates:
            if not setup_file.exists():
                continue
            original = setup_file.read_text(encoding="utf-8")
            patched_lines = []
            changed = False
            for line in original.splitlines():
                if "grp grpmodule.c" in line and not line.lstrip().startswith("#"):
                    patched_lines.append(
                        "# SOUNWD: disabled on Android (Bionic lacks getgrent APIs)"
                    )
                    patched_lines.append("#" + line)
                    changed = True
                else:
                    patched_lines.append(line)
            if changed:
                setup_file.write_text(
                    "\n".join(patched_lines) + "\n", encoding="utf-8"
                )
        from pythonforandroid.logger import info
        info("SOUNWD: Android-incompatible CPython grp extension disabled")


recipe = SounwdPython3Recipe()

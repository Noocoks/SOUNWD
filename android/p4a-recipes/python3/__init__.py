"""SOUNWD CPython recipe and safe recreation of p4a's host venv."""
import importlib.util
import os
import shutil
from pathlib import Path

import pythonforandroid
import pythonforandroid.build as _p4a_build


# python-for-android reuses build/venv for each target architecture. Running
# "python -m venv venv" on an existing environment does NOT clear it: ensurepip
# overlays the bundled pip files on the upgraded pip from the previous arch.
# This leaves mixed pip modules (e.g. installer.py from one version and
# spinners.py from another), causing open_rich_spinner ImportError.
if not getattr(_p4a_build.shprint, "_sounwd_venv_clear_fix", False):
    _original_shprint = _p4a_build.shprint

    def _sounwd_shprint(command, *args, **kwargs):
        arg_strings = [str(arg) for arg in args]
        is_venv_creation = (
            len(arg_strings) >= 2
            and arg_strings[0] == "-m"
            and arg_strings[1] == "venv"
        )

        if is_venv_creation:
            # p4a runs this command with cwd set to its shared build directory.
            # Delete the old environment before ensurepip lays down a new one.
            venv_dir = Path.cwd() / "venv"
            if venv_dir.is_dir():
                shutil.rmtree(venv_dir)

            # --clear is a second line of defence if p4a changes its call shape.
            if "--clear" not in arg_strings:
                args = (*args, "--clear")

            from pythonforandroid.logger import info
            info("SOUNWD: removed previous host venv before recreating it")

        return _original_shprint(command, *args, **kwargs)

    _sounwd_shprint._sounwd_venv_clear_fix = True
    _p4a_build.shprint = _sounwd_shprint


_p4a_root = Path(pythonforandroid.__file__).resolve().parent
_base_path = _p4a_root / "recipes" / "python3" / "__init__.py"
_spec = importlib.util.spec_from_file_location(
    "_sounwd_base_python3_recipe", _base_path
)
_base_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base_module)
_BasePython3Recipe = _base_module.Python3Recipe


class SounwdPython3Recipe(_BasePython3Recipe):
    def get_recipe_dir(self):
        return str(_base_path.parent)

    # Android Bionic does not provide glibc's group-enumeration APIs.
    configure_args = list(_BasePython3Recipe.configure_args) + [
        "ac_cv_header_grp_h=no",
        "ac_cv_func_getgrgid=no",
        "ac_cv_func_getgrgid_r=no",
        "ac_cv_func_getgrouplist=no",
        "ac_cv_func_initgroups=no",
    ]

    def apply_patches(self, arch, build_dir=None):
        super().apply_patches(arch, build_dir=build_dir)

        source_dir = Path(build_dir or self.get_build_dir(arch.arch))
        setup_template = source_dir / "Modules" / "Setup.stdlib.in"
        if not setup_template.is_file():
            raise RuntimeError(
                "SOUNWD Android patch: CPython Modules/Setup.stdlib.in not found"
            )

        original = setup_template.read_text(encoding="utf-8")
        patched_lines = []
        changed = False
        for line in original.splitlines():
            if line.lstrip().startswith("@MODULE_GRP_TRUE@grp grpmodule.c"):
                patched_lines.append(
                    "# SOUNWD: grp disabled; Android Bionic has no getgrent APIs"
                )
                patched_lines.append("#" + line)
                changed = True
            else:
                patched_lines.append(line)

        if not changed and "SOUNWD: grp disabled" not in original:
            raise RuntimeError(
                "SOUNWD Android patch: expected CPython grp module line not found"
            )

        if changed:
            setup_template.write_text(
                "\n".join(patched_lines) + "\n", encoding="utf-8"
            )

        from pythonforandroid.logger import info
        info("SOUNWD: disabled unsupported CPython grp extension for Android")


recipe = SounwdPython3Recipe()

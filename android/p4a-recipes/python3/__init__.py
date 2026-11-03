"""Android-specific Python recipe: disable CPython's grp extension.

Android's Bionic libc does not expose the glibc group-enumeration APIs used
by CPython's grp module. SOUNWD does not need grp, so omit it from the
stdlib build configuration before CPython's configure/make steps.
"""
import importlib.util
from pathlib import Path

import pythonforandroid
import pythonforandroid.build as _p4a_build


# python-for-android 58d2114 passes the target's PYTHONPATH into the
# host-side pip self-upgrade. That can mix the target and host pip modules,
# producing an inconsistent pip install (e.g. missing open_rich_spinner).
# Keep the target PYTHONPATH for later cross-compilation, but isolate this
# one host-side bootstrap command.
if not getattr(_p4a_build.shprint, "_sounwd_pip_env_fix", False):
    _original_shprint = _p4a_build.shprint

    def _sounwd_shprint(command, *args, **kwargs):
        command_text = " ".join(str(part) for part in (command, *args))
        if "pip install -U pip" in command_text:
            env = kwargs.get("_env")
            if env is not None and "PYTHONPATH" in env:
                env = dict(env)
                env.pop("PYTHONPATH", None)
                kwargs["_env"] = env
                from pythonforandroid.logger import info
                info("SOUNWD: isolated host pip upgrade from target PYTHONPATH")
        return _original_shprint(command, *args, **kwargs)

    _sounwd_shprint._sounwd_pip_env_fix = True
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
        # Keep upstream patch files available; this local recipe only
        # overrides behaviour and does not duplicate python-for-android patches.
        return str(_base_path.parent)

    # CPython's setup.py enables grp when grp.h is detected. Android's
    # NDK header exists on some API levels but its glibc enumeration APIs
    # do not, so force the configure test off for every Android ABI.
    configure_args = list(_BasePython3Recipe.configure_args) + [
        "ac_cv_header_grp_h=no",
        "ac_cv_func_getgrgid=no",
        "ac_cv_func_getgrgid_r=no",
        "ac_cv_func_getgrouplist=no",
        "ac_cv_func_initgroups=no",
    ]

    def apply_patches(self, arch, build_dir=None):
        # Apply the upstream python-for-android patches first.
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

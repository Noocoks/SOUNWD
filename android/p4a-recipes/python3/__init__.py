"""SOUNWD's Android-specific python-for-android recipe fixes."""
import importlib.util
from pathlib import Path

import pythonforandroid
import pythonforandroid.build as _p4a_build


# p4a runs a host-side venv while cross-compilation environment variables are
# active. If PYTHONPATH/PYTHONHOME leak into "python -m venv", pip in the new
# venv can be assembled from incompatible host/target modules. Isolate the
# venv creation itself (not merely the later pip upgrade).
if not getattr(_p4a_build.shprint, "_sounwd_host_env_fix", False):
    _original_shprint = _p4a_build.shprint

    def _sounwd_shprint(command, *args, **kwargs):
        command_text = " ".join(str(part) for part in (command, *args))
        env = kwargs.get("_env")

        if "python -m venv venv" in command_text or "pip install -U pip" in command_text:
            if env is not None:
                env = dict(env)
                env.pop("PYTHONPATH", None)
                env.pop("PYTHONHOME", None)
                kwargs["_env"] = env

            # Also protect shell-invoked commands when sh inherits the parent
            # environment instead of receiving an explicit _env dictionary.
            rewritten = []
            for part in args:
                value = str(part)
                value = value.replace(
                    "python -m venv venv",
                    "env -u PYTHONPATH -u PYTHONHOME python -m venv venv",
                )
                value = value.replace(
                    "source venv/bin/activate && pip install -U pip",
                    "unset PYTHONPATH PYTHONHOME; "
                    "source venv/bin/activate && python -m pip install -U pip",
                )
                rewritten.append(value)
            args = tuple(rewritten)

            from pythonforandroid.logger import info
            info("SOUNWD: isolated host venv/pip from target Python environment")

        return _original_shprint(command, *args, **kwargs)

    _sounwd_shprint._sounwd_host_env_fix = True
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

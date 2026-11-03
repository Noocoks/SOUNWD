"""SOUNWD CPython recipe: clean p4a host venv and isolate pip."""
import importlib.util
import shutil
from pathlib import Path

import pythonforandroid
import pythonforandroid.build as _p4a_build


# p4a 58d2114 recreates build/venv for each target architecture but invokes
# "python -m venv venv" without --clear. ensurepip then overlays pip files
# onto the previous architecture's upgraded pip, leaving a mixed installation.
# It also injects the target site-packages as PYTHONPATH while upgrading pip.
if not getattr(_p4a_build.shprint, "_sounwd_host_venv_fix", False):
    _original_shprint = _p4a_build.shprint

    def _sounwd_shprint(command, *args, **kwargs):
        arg_strings = [str(arg) for arg in args]
        is_venv_creation = (
            len(arg_strings) >= 2
            and arg_strings[0] == "-m"
            and arg_strings[1] == "venv"
        )
        command_text = " ".join([str(command), *arg_strings])
        is_pip_upgrade = "pip install -U pip" in command_text

        if is_venv_creation:
            venv_dir = Path.cwd() / "venv"
            if venv_dir.is_dir():
                shutil.rmtree(venv_dir)
            if "--clear" not in arg_strings:
                args = (*args, "--clear")
            from pythonforandroid.logger import info
            info("SOUNWD: clean host venv created for this architecture")

        if is_pip_upgrade:
            # p4a sets PYTHONPATH to the Android target's site-packages here.
            # That path must never be used to import the host pip being upgraded.
            env = kwargs.get("_env")
            if env is not None:
                env = dict(env)
                env.pop("PYTHONPATH", None)
                env.pop("PYTHONHOME", None)
                kwargs["_env"] = env

            rewritten = []
            for part in args:
                value = str(part).replace(
                    "source venv/bin/activate && pip install -U pip",
                    "unset PYTHONPATH PYTHONHOME; "
                    "source venv/bin/activate && python -m pip install -U pip",
                )
                rewritten.append(value)
            args = tuple(rewritten)
            from pythonforandroid.logger import info
            info("SOUNWD: host pip upgrade isolated from target site-packages")

        return _original_shprint(command, *args, **kwargs)

    _sounwd_shprint._sounwd_host_venv_fix = True
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

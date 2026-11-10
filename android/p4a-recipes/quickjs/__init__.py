"""Build a small native QuickJS-NG runtime for Android's yt-dlp EJS solver."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import sh
from pythonforandroid.logger import info
from pythonforandroid.recipe import Recipe
from pythonforandroid.toolchain import shprint


class QuickJSRecipe(Recipe):
    version = "v0.18.0"
    url = "https://github.com/quickjs-ng/quickjs/archive/refs/tags/{version}.tar.gz"
    depends = ["python3"]
    archs = ["arm64-v8a"]

    def build_arch(self, arch):
        source_dir = Path(self.get_build_dir(arch.arch))
        build_dir = source_dir / "android-build"
        ndk_dir = Path(self.ctx.ndk.ndk_dir)
        toolchain = ndk_dir / "build" / "cmake" / "android.toolchain.cmake"
        if not toolchain.is_file():
            raise RuntimeError(f"Android NDK CMake toolchain not found: {toolchain}")

        api = int(self.ctx.ndk_api)
        env = self.get_recipe_env(arch)
        shprint(
            sh.cmake,
            "-S", str(source_dir),
            "-B", str(build_dir),
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
            f"-DANDROID_ABI={arch.arch}",
            f"-DANDROID_PLATFORM=android-{api}",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DQJS_ENABLE_INSTALL=OFF",
            "-DQJS_BUILD_EXAMPLES=OFF",
            "-DQJS_BUILD_CLI_STATIC=OFF",
            "-DQJS_BUILD_CLI_WITH_MIMALLOC=OFF",
            "-DBUILD_SHARED_LIBS=OFF",
            _env=env,
        )
        shprint(
            sh.cmake,
            "--build", str(build_dir),
            "--target", "qjs_exe",
            "--parallel", str(max(1, min(os.cpu_count() or 2, 4))),
            _env=env,
        )

        executable = build_dir / "qjs"
        if not executable.is_file():
            raise RuntimeError(f"QuickJS build completed without the qjs executable: {executable}")

        target_root = Path(self.ctx.get_python_install_dir(arch.arch))
        site_packages = sorted(target_root.glob("lib/python*/site-packages"))
        if len(site_packages) != 1 or not site_packages[0].is_dir():
            raise RuntimeError(
                "Could not identify the target Python site-packages directory for QuickJS installation"
            )

        runtime_dir = site_packages[0] / "sounwd_runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        target = runtime_dir / "qjs"
        shutil.copy2(executable, target)
        target.chmod(0o755)
        info(f"SOUNWD: installed Android QuickJS runtime at {target}")


recipe = QuickJSRecipe()

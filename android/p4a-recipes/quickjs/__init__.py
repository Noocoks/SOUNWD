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
    version = "d7215b0ad3fc2c562e8317fd9bca058fd4863804"
    url = "https://github.com/quickjs-ng/quickjs/archive/{version}.tar.gz"
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
            "-DCMAKE_EXE_LINKER_FLAGS=-Wl,-z,max-page-size=16384",
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

        # python-for-android's get_python_install_dir() is already the
        # target import root (get_site_packages_dir() returns this path).
        target_root = Path(self.ctx.get_python_install_dir(arch.arch))
        if not target_root.is_dir():
            raise RuntimeError(f"Target Python install directory does not exist: {target_root}")

        runtime_dir = target_root / "sounwd_runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)
        init_file = runtime_dir / "__init__.py"
        init_file.write_text('"""Bundled SOUNWD JavaScript runtime."""\n', encoding="utf-8")
        target = runtime_dir / "qjs"
        shutil.copy2(executable, target)
        target.chmod(0o755)
        info(f"SOUNWD: installed Android QuickJS runtime at {target}")


recipe = QuickJSRecipe()

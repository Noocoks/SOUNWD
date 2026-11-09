"""Verify the packaged desktop app paints its main window and dismisses the splash."""
from __future__ import annotations

import os
import signal
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: smoke_packaged_startup.py PATH_TO_APP")

    executable = Path(sys.argv[1]).resolve()
    if not executable.is_file():
        raise AssertionError(f"Packaged application not found: {executable}")

    with tempfile.TemporaryDirectory(prefix="sounwd-startup-") as temp_dir:
        ready_file = Path(temp_dir) / "ready"
        env = os.environ.copy()
        env["SOUNWD_SMOKE_READY_FILE"] = str(ready_file)
        popen_options = {}
        if os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            popen_options["start_new_session"] = True

        process = subprocess.Popen(
            [str(executable)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            **popen_options,
        )
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                if ready_file.is_file():
                    if process.poll() is not None:
                        raise AssertionError(
                            f"SOUNWD exited immediately after startup (code {process.returncode})"
                        )
                    print("Packaged startup OK: main window rendered and splash handoff completed")
                    return 0
                if process.poll() is not None:
                    raise AssertionError(
                        f"SOUNWD exited before becoming ready (code {process.returncode})"
                    )
                time.sleep(0.2)
            raise AssertionError("SOUNWD did not finish startup within 25 seconds")
        finally:
            if process.poll() is None:
                if os.name == "nt":
                    # PyInstaller one-file starts a child process; terminate the
                    # complete process tree, not only the bootloader parent.
                    subprocess.run(
                        ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                else:
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if os.name == "nt":
                        subprocess.run(
                            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                        )
                    else:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())

"""Early Android runtime diagnostics for SOUNWD.

Python imports sitecustomize during interpreter initialization (before main.py)
when the application directory is on sys.path. This catches failures that occur
before the Kivy application entry point is reached.
"""
from __future__ import annotations

import os
import sys
import threading
import traceback
from pathlib import Path

_LOG = None


def _open_log():
    candidates = [
        "/data/user/0/org.sounwd.sounwd/files/app",
        os.environ.get("ANDROID_PRIVATE"),
        os.environ.get("ANDROID_ARGUMENT"),
        os.environ.get("HOME"),
        os.getcwd(),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            folder = Path(candidate)
            if folder.is_file():
                continue
            folder.mkdir(parents=True, exist_ok=True)
            stream = (folder / "sounwd-startup.log").open(
                "w", encoding="utf-8", buffering=1
            )
            stream.write("\n=== SOUNWD Python runtime bootstrap ===\n")
            stream.write("cwd={!r}\n".format(os.getcwd()))
            stream.write("executable={!r}\n".format(sys.executable))
            stream.write("version={!r}\n".format(sys.version))
            stream.write("argv={!r}\n".format(sys.argv))
            stream.write("ANDROID_PRIVATE={!r}\n".format(
                os.environ.get("ANDROID_PRIVATE")
            ))
            stream.write("ANDROID_ARGUMENT={!r}\n".format(
                os.environ.get("ANDROID_ARGUMENT")
            ))
            stream.write("sys.path={!r}\n".format(sys.path))
            stream.flush()
            return stream
        except Exception:
            continue
    return None


_LOG = _open_log()


def _write(message):
    if _LOG is None:
        return
    try:
        _LOG.write("[SOUNWD bootstrap] " + str(message) + "\n")
        _LOG.flush()
    except Exception:
        pass


def _exception_hook(exc_type, exc_value, exc_tb):
    _write("UNCAUGHT MAIN-THREAD EXCEPTION")
    if _LOG is not None:
        traceback.print_exception(exc_type, exc_value, exc_tb, file=_LOG)
        _LOG.flush()
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _thread_exception_hook(args):
    _write("UNCAUGHT THREAD EXCEPTION: {}".format(args.thread.name))
    if _LOG is not None:
        traceback.print_exception(
            args.exc_type, args.exc_value, args.exc_traceback, file=_LOG
        )
        _LOG.flush()


if _LOG is not None:
    sys.excepthook = _exception_hook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_exception_hook
    _write("sitecustomize loaded before application main.py")
else:
    # This marker may still appear in Android's native log if file storage
    # cannot be reached. Keep this module independent of Kivy and pyjnius.
    try:
        os.write(2, b"[SOUNWD] sitecustomize loaded; private log unavailable\\n")
    except Exception:
        pass

from __future__ import annotations

import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".sonora-env"
REQUIREMENTS = ROOT / "requirements.txt"


class SetupWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Sonora · Preparando")
        self.root.geometry("470x245")
        self.root.resizable(False, False)
        self.root.configure(bg="#10131D")
        self.root.eval("tk::PlaceWindow . center")

        tk.Label(self.root, text="♫  SONORA", bg="#10131D", fg="#C4B5FD",
                 font=("Segoe UI", 23, "bold")).pack(pady=(24, 5))
        tk.Label(self.root, text="Estamos preparando tu espacio musical",
                 bg="#10131D", fg="#F5F3FF",
                 font=("Segoe UI", 11)).pack()
        self.status = tk.Label(self.root, text="Comprobando los componentes…",
                               bg="#10131D", fg="#A5A9BA",
                               font=("Segoe UI", 9))
        self.status.pack(pady=(20, 8))
        self.bar = ttk.Progressbar(self.root, mode="indeterminate", length=380)
        self.bar.pack()
        self.bar.start(12)
        tk.Label(self.root, text="Solo la primera vez puede tardar unos minutos.",
                 bg="#10131D", fg="#777C91",
                 font=("Segoe UI", 8)).pack(pady=15)

    def set_status(self, value: str) -> None:
        self.root.after(0, lambda: self.status.configure(text=value))

    def finish(self, error: str | None = None) -> None:
        def close() -> None:
            self.bar.stop()
            self.root.destroy()
            if error:
                messagebox.showerror("No se pudo iniciar Sonora", error)
        self.root.after(0, close)

    def run(self) -> None:
        self.root.mainloop()


def worker(window: SetupWindow) -> None:
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError("Sonora necesita Python 3.10 o superior. Instala una versión reciente de Python y vuelve a abrir Sonora.")

        if os.name == "nt":
            python = VENV / "Scripts" / "python.exe"
            pythonw = VENV / "Scripts" / "pythonw.exe"
        else:
            python = VENV / "bin" / "python"
            pythonw = python

        if not python.exists():
            window.set_status("Creando un entorno seguro para Sonora…")
            subprocess.run([sys.executable, "-m", "venv", str(VENV)],
                           check=True, cwd=ROOT)

        window.set_status("Instalando los componentes necesarios…")
        subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                        "-r", str(REQUIREMENTS)],
                       check=True, cwd=ROOT)

        window.set_status("Abriendo Sonora…")
        subprocess.Popen([str(pythonw), str(ROOT / "src" / "gui.py")],
                         cwd=ROOT, close_fds=True)
        window.finish()
    except subprocess.CalledProcessError as error:
        window.finish(
            "No se han podido instalar los componentes necesarios.\n\n"
            "Comprueba tu conexión a Internet y vuelve a abrir Sonora.\n\n"
            f"Detalle: {error}"
        )
    except Exception as error:
        window.finish(f"{error}")


def main() -> None:
    window = SetupWindow()
    threading.Thread(target=worker, args=(window,), daemon=True).start()
    window.run()


if __name__ == "__main__":
    main()

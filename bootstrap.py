from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".sounwd-env"
REQUIREMENTS = ROOT / "requirements.txt"


class SetupWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("SOUNWD · Preparando")
        self.root.geometry("470x245")
        self.root.resizable(False, False)
        self.root.configure(bg="#191824")
        self.root.eval("tk::PlaceWindow . center")

        tk.Label(self.root, text="◖♪  SOUNWD", bg="#191824", fg="#C6B5E8",
                 font=("Segoe UI", 23, "bold")).pack(pady=(24, 5))
        tk.Label(self.root, text="Tu espacio musical estará listo en un momento",
                 bg="#191824", fg="#F2EDF8",
                 font=("Segoe UI", 11)).pack()
        self.status = tk.Label(self.root, text="Comprobando los componentes…",
                               bg="#191824", fg="#AAA3B5",
                               font=("Segoe UI", 9))
        self.status.pack(pady=(20, 8))
        self.bar = ttk.Progressbar(self.root, mode="indeterminate", length=380)
        self.bar.pack()
        self.bar.start(12)
        tk.Label(self.root, text="Solo la primera vez puede tardar unos minutos.",
                 bg="#191824", fg="#898294",
                 font=("Segoe UI", 8)).pack(pady=15)

    def set_status(self, value: str) -> None:
        self.root.after(0, lambda: self.status.configure(text=value))

    def finish(self, error: str | None = None) -> None:
        def close() -> None:
            self.bar.stop()
            self.root.destroy()
            if error:
                messagebox.showerror("No se pudo iniciar SOUNWD", error)
        self.root.after(0, close)

    def run(self) -> None:
        self.root.mainloop()


def worker(window: SetupWindow) -> None:
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError("SOUNWD necesita Python 3.10 o superior. Instala una versión reciente de Python y vuelve a abrir SOUNWD.")

        if os.name == "nt":
            python = VENV / "Scripts" / "python.exe"
            pythonw = VENV / "Scripts" / "pythonw.exe"
        else:
            python = VENV / "bin" / "python"
            pythonw = python

        if not python.exists():
            window.set_status("Creando un entorno seguro para SOUNWD…")
            subprocess.run([sys.executable, "-m", "venv", "--clear", str(VENV)],
                           check=True, cwd=ROOT)

        # Reinstala/actualiza dependencias solo cuando cambia requirements.txt.
        requirements_hash = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
        stamp = VENV / ".requirements.sha256"
        installed_hash = stamp.read_text(encoding="ascii").strip() if stamp.exists() else ""
        if installed_hash != requirements_hash:
            window.set_status("Instalando o actualizando los componentes necesarios…")
            subprocess.run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
                            "-r", str(REQUIREMENTS)],
                           check=True, cwd=ROOT)
            stamp.write_text(requirements_hash, encoding="ascii")


        window.set_status("Abriendo SOUNWD…")
        subprocess.Popen([str(pythonw), str(ROOT / "src" / "gui.py")],
                         cwd=ROOT, close_fds=True)
        window.finish()
    except subprocess.CalledProcessError as error:
        window.finish(
            "No se han podido instalar los componentes necesarios.\n\n"
            "Comprueba tu conexión a Internet y vuelve a abrir SOUNWD.\n\n"
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

@echo off
setlocal
cd /d "%~dp0\.."
py -m pip install -r requirements.txt
py -m src.gui
if errorlevel 1 (
  echo.
  echo SOUNWD ha terminado con un error.
  pause
)

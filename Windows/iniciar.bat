@echo off
setlocal
cd /d "%~dp0\.."
python -m src.main
if errorlevel 1 (
  echo.
  echo El programa ha terminado con un error.
)
pause

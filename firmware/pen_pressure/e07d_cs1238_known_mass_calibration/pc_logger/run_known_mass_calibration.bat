@echo off
setlocal
cd /d "%~dp0"

py -3 -c "import serial, matplotlib" >nul 2>nul
if errorlevel 1 (
  echo Installing the calibration application's Python packages...
  py -3 -m pip install -r requirements.txt
  if errorlevel 1 (
    echo.
    echo Installation failed. Install Python 3 with the Python Launcher, then run this file again.
    pause
    exit /b 1
  )
)

pyw -3 known_mass_calibration_gui.py
if errorlevel 1 (
  echo.
  echo The calibration application could not start.
  pause
)

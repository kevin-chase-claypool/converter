@echo off
setlocal
set "SCRIPT_DIR=%~dp0"

py -3 -c "import serial, matplotlib" >nul 2>nul
if errorlevel 1 (
  echo Installing the required Python packages: pyserial and matplotlib
  py -3 -m pip install -r "%SCRIPT_DIR%requirements.txt"
  if errorlevel 1 (
    echo Could not install the required packages. Close this window after reading the error.
    pause
    exit /b 1
  )
)

start "Force Calibration Test" /wait pyw -3 "%SCRIPT_DIR%force_calibration_gui.py"
exit /b %ERRORLEVEL%

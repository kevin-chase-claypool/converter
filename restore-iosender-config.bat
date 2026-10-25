@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\restore_iosender_config.ps1" -Launch
set "restore_status=%errorlevel%"
if not "%restore_status%"=="0" echo ioSender config restore failed. Close ioSender and try again.
pause
exit /b %restore_status%

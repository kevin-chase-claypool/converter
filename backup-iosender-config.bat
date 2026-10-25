@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\backup_iosender_config.ps1"
set "backup_status=%errorlevel%"
if not "%backup_status%"=="0" echo ioSender config backup failed.
pause
exit /b %backup_status%

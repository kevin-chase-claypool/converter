@echo off
cd /d "%~dp0software"
python qt_kaleidoscope.pyw > kaleidoscope_debug.log 2>&1

@echo off
cd /d "%~dp0software"
python qt_svg_to_gcode.pyw > qt_debug.log 2>&1

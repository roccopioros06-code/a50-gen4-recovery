@echo off
cd /d "%~dp0"
title A50 Gen 4 recovery tool
echo  A50 Gen 4 recovery tool - free, use at your own risk.
echo  If it saved your headset: https://paypal.me/d4rky06
taskkill /IM "ASTRO Command Center.exe" /F >nul 2>&1
set PY=python
python --version >nul 2>&1 || set PY=py
%PY% -c "import pywinusb" >nul 2>&1 || %PY% -m pip install pywinusb
:menu
echo.
echo  1 - Diagnose (read-only)
echo  2 - Fix BASE Avnera chip
echo  3 - Fix HEADSET Avnera chip (headset on and docked)
echo  4 - Exit
choice /c 1234 /n /m "Choice: "
if errorlevel 4 goto :eof
if errorlevel 3 ( %PY% a50_tool.py fix-headset & goto menu )
if errorlevel 2 ( %PY% a50_tool.py fix-base & goto menu )
%PY% a50_tool.py info
goto menu

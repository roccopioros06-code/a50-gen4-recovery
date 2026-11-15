@echo off
cd /d "%~dp0"
set PY=
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY=%%D
if defined PY (
  set PYEXE="%PY%\python.exe"
  set PYW="%PY%\pythonw.exe"
) else (
  set PYEXE=py
  set PYW=pyw
)
%PYEXE% -c "import pywinusb" >nul 2>&1 || %PYEXE% -m pip install pywinusb
%PYEXE% -c "import customtkinter as c, sys; sys.exit(0 if c.__version__.startswith('5.') else 1)" >nul 2>&1 || %PYEXE% -m pip install "customtkinter==5.2.2"
%PYEXE% -c "import PIL" >nul 2>&1 || %PYEXE% -m pip install pillow
%PYEXE% -c "import pystray" >nul 2>&1 || %PYEXE% -m pip install pystray
taskkill /F /FI "WINDOWTITLE eq A50 Control*" >nul 2>&1
start "" %PYW% a50_control.py --replace

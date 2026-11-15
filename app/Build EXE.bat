@echo off
rem Builds "A50 Control.exe" (no Python needed to run it). Requires Python only on the PC that builds it.
cd /d "%~dp0"
set HERE=%~dp0
set PY=
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if not defined PY set PY=py
echo Installing build tools...
%PY% -m pip install --upgrade pyinstaller || goto :fail
%PY% -m pip install pywinusb pillow pystray "customtkinter==5.2.2" || goto :fail
echo Building A50 Control.exe ...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --name "A50 Control" ^
  --icon "%HERE%a50_control.ico" --add-data "%HERE%a50_control.ico;." ^
  --paths "%HERE%..\tool" --hidden-import a50_tool --hidden-import a50_update --hidden-import a50_control_classic --hidden-import pystray._win32 ^
  --collect-data customtkinter --workpath build --distpath dist --specpath build ^
  "%HERE%a50_control.py" || goto :fail
copy /Y "dist\A50 Control.exe" "%USERPROFILE%\Desktop\A50 Control.exe" >nul
echo.
echo Done: "dist\A50 Control.exe" (a copy was placed on your Desktop).
pause
exit /b 0
:fail
echo.
echo BUILD FAILED - send the text above.
pause
exit /b 1

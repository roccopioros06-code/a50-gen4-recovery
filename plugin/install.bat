@echo off
net session >nul 2>&1 || (echo Run as administrator: right-click install.bat ^> "Run as administrator". & pause & exit /b 1)
set ACC=%ProgramFiles(x86)%\Astro Gaming\ASTRO Command Center
if not exist "%ACC%\ASTRO Command Center.exe" (echo ACC not found in "%ACC%". & pause & exit /b 1)
taskkill /IM "ASTRO Command Center.exe" /F >nul 2>&1
copy /Y "%~dp0HID.DLL" "%ACC%\HID.DLL" && echo Plugin installed in "%ACC%".
pause

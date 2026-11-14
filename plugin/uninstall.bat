@echo off
net session >nul 2>&1 || (echo Run as administrator: right-click uninstall.bat ^> "Run as administrator". & pause & exit /b 1)
set ACC=%ProgramFiles(x86)%\Astro Gaming\ASTRO Command Center
taskkill /IM "ASTRO Command Center.exe" /F >nul 2>&1
del /q "%ACC%\HID.DLL" && echo Plugin removed, ACC is back to stock.
pause

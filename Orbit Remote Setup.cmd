@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    py -3 "%~dp0tools\windows_setup_gui.pyw"
) else (
    python "%~dp0tools\windows_setup_gui.pyw"
)
if errorlevel 1 (
    echo Orbit Setup could not start. Install Python 3.10 or newer with Tkinter.
    pause
)
endlocal

@echo off
:: Z++ Ultra - Single-command installer for Windows
:: Just copy-paste: .\install.ps1
:: Or: powershell -ExecutionPolicy Bypass -File install.ps1

:: This batch file launches the PowerShell installer
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\setup.ps1"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Installation failed. Make sure PowerShell is available.
    pause
)

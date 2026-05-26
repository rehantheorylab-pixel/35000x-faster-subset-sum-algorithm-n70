@echo off
cd /d "%~dp0"

:: Try the EXE first (pre-built, no Rust needed)
if exist "%~dp0zpp.exe" (
    "%~dp0zpp.exe" %*
    exit /b %ERRORLEVEL%
)

:: Fallback to Python
echo Z++.py not found or zpp.exe not available
echo Run: python Z++.py
if exist "%~dp0Z++.py" (
    python "%~dp0Z++.py" %*
) else (
    echo Error: Neither zpp.exe nor Z++.py found
    exit /b 1
)

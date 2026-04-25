@echo off
echo ============================================
echo   Queue Runner - Install
echo ============================================
echo.

REM Check for Python 3.11
py -3.11 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.11 not found.
    echo         Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/2] Python 3.11 found.

REM Check for aider
py -3.11 -c "import aider" >nul 2>&1
if errorlevel 1 (
    echo [!] aider-chat not installed. Installing...
    py -3.11 -m pip install aider-chat
) else (
    echo [2/2] aider-chat already installed.
)

REM Check for ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Ollama not found in PATH.
    echo           Install from https://ollama.com
) else (
    echo [OK] Ollama found.
)

echo.
echo ============================================
echo   Install complete.
echo   Copy the queue/ folder into your repo.
echo   Then run: start.bat C:\path\to\your\repo
echo ============================================
pause

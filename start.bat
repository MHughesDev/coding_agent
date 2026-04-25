@echo off
echo ============================================
echo   Queue Runner - Start
echo ============================================

REM Set Ollama env vars
set OLLAMA_API_BASE=http://127.0.0.1:11434
set OLLAMA_FLASH_ATTENTION=1
set OLLAMA_KV_CACHE_TYPE=q8_0

REM Determine repo path
if "%~1"=="" (
    echo Usage: start.bat C:\path\to\your\repo
    echo        start.bat C:\path\to\your\repo --once
    echo        start.bat C:\path\to\your\repo --dry-run
    pause
    exit /b 1
)

set REPO_PATH=%~1
set EXTRA_ARGS=%2 %3

echo   Repo: %REPO_PATH%
echo   Args: %EXTRA_ARGS%
echo.

REM Run the queue runner
py -3.11 "%~dp0queue_runner.py" --repo "%REPO_PATH%" %EXTRA_ARGS%

pause

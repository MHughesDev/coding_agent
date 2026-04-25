@echo off
REM ============================================
REM   Queue Runner - Start Headless (Background)
REM   Runs without a console window.
REM ============================================

REM Set Ollama env vars
set OLLAMA_API_BASE=http://127.0.0.1:11434
set OLLAMA_FLASH_ATTENTION=1
set OLLAMA_KV_CACHE_TYPE=q8_0

if "%~1"=="" (
    echo Usage: start_headless.bat C:\path\to\your\repo
    pause
    exit /b 1
)

set REPO_PATH=%~1

echo Starting Queue Runner in background for: %REPO_PATH%
echo Check queue\logs\ for output.

REM Use pythonw.exe (no console window) via py launcher
start "" /B py -3.11 "%~dp0queue_runner.py" --repo "%REPO_PATH%"

echo Queue Runner started. Close this window.
timeout /t 3

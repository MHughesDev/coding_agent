@echo off
echo ============================================
echo   Queue Runner - Stop
echo ============================================
echo.
echo Stopping all queue_runner.py processes...

REM Find and kill the queue runner python process
taskkill /F /FI "WINDOWTITLE eq *queue_runner*" >nul 2>&1

REM Also search for the python process running queue_runner
for /f "tokens=2" %%a in ('wmic process where "commandline like '%%queue_runner%%'" get processid /format:list ^| find "="') do (
    echo Killing PID: %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo Queue Runner stopped.
echo Note: Ollama is still running. To stop it too: taskkill /IM ollama.exe /F
pause

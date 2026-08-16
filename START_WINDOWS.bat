@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PY=py"
) else (
  set "PY=python"
)

echo Python detected:
%PY% --version

if not exist .venv (
  echo [1/4] Creating Python virtual environment...
  %PY% -m venv .venv || goto :error
) else (
  echo [1/4] Reusing existing virtual environment...
)

echo [2/4] Activating environment...
call .venv\Scripts\activate.bat || goto :error

echo [3/4] Installing / checking dependencies...
python -m pip install --upgrade pip setuptools wheel
python -m pip install --prefer-binary -r requirements.txt || goto :error

echo [4/4] Starting InsightFlow AI...
echo.
echo Open http://127.0.0.1:8000 in your browser.
echo Press Ctrl+C in this window to stop the server.
echo.
start "" http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
goto :eof

:error
echo.
echo Startup failed.
echo Please copy the last 30 lines above and send them to ChatGPT.
pause
exit /b 1

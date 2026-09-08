@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Please run START_WINDOWS.bat once to install the project, then run this file again.
  pause
  exit /b 2
)
echo This check uses your saved .env and consumes SerpAPI and model quota.
echo Default: one US magnetic power bank study; up to 8 SerpAPI search requests.
echo No demo data is used. Results stay on this computer.
echo.
.venv\Scripts\python.exe verify_real_research.py
set "INSIGHTFLOW_CHECK_EXIT=%ERRORLEVEL%"
if exist LIVE_CHECK_RESULT.txt start "" notepad.exe LIVE_CHECK_RESULT.txt
echo.
pause
exit /b %INSIGHTFLOW_CHECK_EXIT%

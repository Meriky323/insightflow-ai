@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  echo [InsightFlow] Creating virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt >nul
if not exist .env copy .env.example .env >nul
echo.
echo InsightFlow AI is starting at http://127.0.0.1:8000
echo Portfolio home: http://127.0.0.1:8000/
echo Flagship case:  http://127.0.0.1:8000/?demo=1
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
endlocal

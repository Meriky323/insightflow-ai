@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo =========================================================
echo InsightFlow AI - Install Git + Publish to GitHub
echo Target: https://github.com/Meriky323/insightflow-ai
echo =========================================================
echo.

rem ---- Locate Git if already installed ----
set "GITEXE="
if exist "%ProgramFiles%\Git\cmd\git.exe" set "GITEXE=%ProgramFiles%\Git\cmd\git.exe"
if exist "%LocalAppData%\Programs\Git\cmd\git.exe" set "GITEXE=%LocalAppData%\Programs\Git\cmd\git.exe"

if not defined GITEXE (
  where git >nul 2>nul
  if not errorlevel 1 set "GITEXE=git"
)

rem ---- Install Git if missing ----
if not defined GITEXE (
  echo [1/7] Git was not found. Installing Git for Windows...
  where winget >nul 2>nul
  if errorlevel 1 (
    echo.
    echo [ERROR] Windows Package Manager ^(winget^) was not found.
    echo A browser will open to the official Git for Windows page.
    start "" "https://git-scm.com/download/win"
    echo Install Git with the default options, then run this file again.
    pause
    exit /b 1
  )

  winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
  if errorlevel 1 (
    echo.
    echo [ERROR] Git installation failed or was cancelled.
    pause
    exit /b 1
  )

  if exist "%ProgramFiles%\Git\cmd\git.exe" set "GITEXE=%ProgramFiles%\Git\cmd\git.exe"
  if exist "%LocalAppData%\Programs\Git\cmd\git.exe" set "GITEXE=%LocalAppData%\Programs\Git\cmd\git.exe"

  if not defined GITEXE (
    echo.
    echo Git seems installed, but this window cannot locate it yet.
    echo Close this window and double-click this file once more.
    pause
    exit /b 1
  )
) else (
  echo [1/7] Git already installed.
)

echo [2/7] Git detected:
"%GITEXE%" --version || goto :error

echo [3/7] Preparing local repository...
if not exist ".git" (
  "%GITEXE%" init || goto :error
)
"%GITEXE%" branch -M main || goto :error

echo [4/7] Setting commit identity...
"%GITEXE%" config user.name "Meriky323" || goto :error
"%GITEXE%" config user.email "284194644+Meriky323@users.noreply.github.com" || goto :error

echo [5/7] Adding project files...
"%GITEXE%" add -A || goto :error
"%GITEXE%" diff --cached --quiet
if errorlevel 1 (
  "%GITEXE%" commit -m "Launch InsightFlow AI portfolio" || goto :error
) else (
  echo No new file changes to commit.
)

echo [6/7] Connecting GitHub repository...
"%GITEXE%" remote get-url origin >nul 2>nul
if errorlevel 1 (
  "%GITEXE%" remote add origin https://github.com/Meriky323/insightflow-ai.git || goto :error
) else (
  "%GITEXE%" remote set-url origin https://github.com/Meriky323/insightflow-ai.git || goto :error
)

echo [7/7] Uploading to GitHub...
echo.
echo If a GitHub sign-in window opens, approve it once.
echo Keep this window open until SUCCESS appears.
echo.
"%GITEXE%" push -u origin main || goto :error

echo.
echo =========================================================
echo SUCCESS
echo GitHub repository:
echo https://github.com/Meriky323/insightflow-ai
echo =========================================================
pause
exit /b 0

:error
echo.
echo =========================================================
echo FAILED
echo Take a screenshot of the last lines and send it to ChatGPT.
echo =========================================================
pause
exit /b 1

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo =========================================================
echo InsightFlow AI - One Click Publish to GitHub
echo Target: https://github.com/Meriky323/insightflow-ai
echo =========================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows was not found.
  echo Please install Git for Windows, then double-click this file again.
  echo https://git-scm.com/download/win
  pause
  exit /b 1
)

echo [1/6] Git detected:
git --version

echo [2/6] Preparing local repository...
if not exist ".git" (
  git init || goto :error
)
git branch -M main || goto :error

echo [3/6] Setting commit identity...
git config user.name "Meriky323" || goto :error
git config user.email "284194644+Meriky323@users.noreply.github.com" || goto :error

echo [4/6] Adding project files...
git add -A || goto :error

git diff --cached --quiet
if errorlevel 1 (
  git commit -m "Launch InsightFlow AI portfolio" || goto :error
) else (
  echo No new file changes to commit.
)

echo [5/6] Connecting GitHub repository...
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin https://github.com/Meriky323/insightflow-ai.git || goto :error
) else (
  git remote set-url origin https://github.com/Meriky323/insightflow-ai.git || goto :error
)

echo [6/6] Uploading to GitHub...
echo.
echo If GitHub opens a browser, approve the sign-in once.
echo Do NOT close this window while the upload is running.
echo.
git push -u origin main || goto :error

echo.
echo =========================================================
echo SUCCESS

echo GitHub repository:
echo https://github.com/Meriky323/insightflow-ai
echo =========================================================
echo.
echo Next step: deploy this repository on Railway.
pause
exit /b 0

:error
echo.
echo =========================================================
echo UPLOAD FAILED

echo Please take a screenshot of the bottom of this window and send it to ChatGPT.
echo =========================================================
pause
exit /b 1

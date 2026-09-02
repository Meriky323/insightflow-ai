@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo InsightFlow AI - CHECK FIRST, THEN DEPLOY v1.5
echo Live: https://insightflow-ai.up.railway.app/
echo Repo: https://github.com/Meriky323/insightflow-ai
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows is not installed.
  echo Install it from https://git-scm.com/download/win then run this file again.
  pause
  exit /b 1
)

echo [1/8] Checking whether the full v1.5 website is already live...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$h='https://insightflow-ai.up.railway.app/api/health'; try { $j=(Invoke-WebRequest -UseBasicParsing -Uri $h -TimeoutSec 12).Content ^| ConvertFrom-Json; if($j.version -eq '1.5.0'){exit 0}else{exit 1} } catch { exit 1 }"
if not errorlevel 1 (
  echo A v1.5 health endpoint is already live. Running full verification before touching GitHub...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY_LIVE_WEBSITE.ps1"
  if not errorlevel 1 (
    echo.
    echo ============================================================
    echo ALREADY COMPLETE - NOTHING WAS CHANGED
    echo https://insightflow-ai.up.railway.app/
    echo ============================================================
    start "" "https://insightflow-ai.up.railway.app/"
    pause
    exit /b 0
  )
)

echo [2/8] Preparing local Git repository...
if not exist ".git" git init >nul 2>nul

git config user.name "Meriky323"
git config user.email "284194644+Meriky323@users.noreply.github.com"

git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin https://github.com/Meriky323/insightflow-ai.git
) else (
  git remote set-url origin https://github.com/Meriky323/insightflow-ai.git
)

echo [3/8] Reading current GitHub main branch...
git fetch origin main || goto :error

echo [4/8] Comparing this v1.5 website with GitHub main...
rem Keep the extracted v1.5 working tree while basing the commit on current GitHub main.
git reset --mixed origin/main >nul || goto :error
git add -A || goto :error

git diff --cached --quiet
if not errorlevel 1 (
  echo GitHub already contains the same files. No commit is needed.
  goto :verify
)

echo [5/8] Showing files that will change...
git diff --cached --stat

echo [6/8] Creating deployment commit...
git commit -m "Deploy InsightFlow v1.5 recruiter-ready website" || goto :error

echo [7/8] Pushing to GitHub main...
echo A GitHub sign-in window may open once. Approve it to continue.
git push origin HEAD:main || goto :error

:verify
echo [8/8] Waiting for Railway and verifying every critical website surface...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY_LIVE_WEBSITE.ps1"
if errorlevel 1 goto :verifywarn

echo.
echo ============================================================
echo SUCCESS - COMPLETE v1.5 WEBSITE IS LIVE
echo https://insightflow-ai.up.railway.app/
echo ============================================================
start "" "https://insightflow-ai.up.railway.app/"
pause
exit /b 0

:verifywarn
echo.
echo GitHub update completed, but the full Railway verification did not pass before timeout.
echo Railway may still be deploying. Do not put the link on your resume until VERIFY_LIVE_WEBSITE.ps1 shows PASS.
echo.
pause
exit /b 0

:error
echo.
echo ============================================================
echo DEPLOY FAILED

echo No force push was used. Your GitHub history was not rewritten.
echo Take a screenshot of the error above if you need help.
echo ============================================================
pause
exit /b 1

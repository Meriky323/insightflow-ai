@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "GIT_PAGER=cat"
set "PAGER=cat"

echo ============================================================
echo InsightFlow AI - FINAL v1.6 BILINGUAL RECRUITER WEBSITE
echo Live: https://insightflow-ai.up.railway.app/
echo Repo: https://github.com/Meriky323/insightflow-ai
echo ============================================================
echo.

where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows is not installed.
  echo Install it from https://git-scm.com/download/win and run this file again.
  pause
  exit /b 1
)

echo [1/7] Quick-checking the live version...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$h='https://insightflow-ai.up.railway.app/api/health'; try { $j=(Invoke-WebRequest -UseBasicParsing -Uri $h -TimeoutSec 12).Content ^| ConvertFrom-Json; if($j.version -eq '1.6.0' -and $j.bilingual_ui){exit 0}else{exit 1} } catch { exit 1 }"
if not errorlevel 1 (
  echo v1.6 health is already live. Skipping GitHub and running the full verifier once.
  goto :verify
)

echo.
echo [2/7] Preparing Git repository...
if not exist ".git" git init >nul 2>nul
git config user.name "Meriky323"
git config user.email "284194644+Meriky323@users.noreply.github.com"
git remote get-url origin >nul 2>nul
if errorlevel 1 (
  git remote add origin https://github.com/Meriky323/insightflow-ai.git
) else (
  git remote set-url origin https://github.com/Meriky323/insightflow-ai.git
)

echo [3/7] Reading current GitHub main...
git fetch origin main || goto :error

echo [4/7] Building a normal commit on top of current main...
git reset --mixed origin/main >nul || goto :error
git add -A || goto :error
git diff --cached --quiet
if not errorlevel 1 (
  echo GitHub already contains these v1.6 files. Skipping commit.
  goto :verify
)

echo Files changing in this final deployment:
git --no-pager diff --cached --stat

echo [5/7] Creating v1.6 deployment commit...
git commit -m "Deploy InsightFlow v1.6 bilingual recruiter website" || goto :error

echo [6/7] Pushing to GitHub main...
echo A GitHub sign-in window may open once. Approve it to continue.
git push origin HEAD:main || goto :error

:verify
echo [7/7] Waiting for Railway and running full live verification...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY_LIVE_WEBSITE.ps1"
if errorlevel 1 goto :verifywarn

echo.
echo ============================================================
echo SUCCESS - INSIGHTFLOW v1.6 IS READY FOR YOUR RESUME
echo https://insightflow-ai.up.railway.app/
echo ============================================================
start "" "https://insightflow-ai.up.railway.app/"
pause
exit /b 0

:verifywarn
echo.
echo GitHub is updated, but Railway did not pass every live check yet.
echo Do not redeploy repeatedly. Wait a few minutes, then double-click VERIFY_LIVE_WEBSITE.ps1.
echo Only use the link on your resume after it prints PASS.
pause
exit /b 0

:error
echo.
echo ============================================================
echo DEPLOY FAILED
echo No force push was used and Git history was not rewritten.
echo Take a screenshot of the last lines if you need help.
echo ============================================================
pause
exit /b 1

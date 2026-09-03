@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "GIT_PAGER=cat"
set "PAGER=cat"

echo ============================================================
echo InsightFlow 2.0 - EVIDENCE EDITORIAL PRODUCT REFRESH
echo Live: https://insightflow-ai.up.railway.app/
echo Repo: https://github.com/Meriky323/insightflow-ai
echo ============================================================
echo.
where git >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Git for Windows is not installed.
  pause
  exit /b 1
)

echo [1/7] Checking whether 2.0 is already live...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='https://insightflow-ai.up.railway.app/api/health'; try {$j=(Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 12).Content ^| ConvertFrom-Json; if($j.version -eq '2.0.0' -and $j.evidence_thread){exit 0}else{exit 1}} catch {exit 1}"
if not errorlevel 1 goto :verify

echo [2/7] Preparing Git repository...
if not exist ".git" git init >nul 2>nul
git config user.name "Meriky323"
git config user.email "284194644+Meriky323@users.noreply.github.com"
git remote get-url origin >nul 2>nul
if errorlevel 1 (git remote add origin https://github.com/Meriky323/insightflow-ai.git) else (git remote set-url origin https://github.com/Meriky323/insightflow-ai.git)

echo [3/7] Reading GitHub main...
git fetch origin main || goto :error

echo [4/7] Building normal commit on top of current main...
git reset --mixed origin/main >nul || goto :error
git add -A || goto :error
git diff --cached --quiet
if not errorlevel 1 goto :verify
git --no-pager diff --cached --stat

echo [5/7] Creating deployment commit...
git commit -m "Deploy InsightFlow 2.0 evidence editorial refresh" || goto :error

echo [6/7] Pushing to GitHub main...
git push origin HEAD:main || goto :error

:verify
echo [7/7] Waiting for Railway and running live verification...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY_LIVE_WEBSITE.ps1"
if errorlevel 1 goto :verifywarn
echo.
echo ============================================================
echo SUCCESS - INSIGHTFLOW 2.0 IS READY FOR YOUR RESUME
echo https://insightflow-ai.up.railway.app/
echo ============================================================
start "" "https://insightflow-ai.up.railway.app/"
pause
exit /b 0

:verifywarn
echo GitHub is updated, but the live verifier has not passed every check yet.
echo Do not redeploy repeatedly. Run VERIFY_LIVE_WEBSITE.ps1 again after Railway finishes.
pause
exit /b 0

:error
echo DEPLOY FAILED. No force push was used and Git history was not rewritten.
pause
exit /b 1

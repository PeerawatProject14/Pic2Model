@echo off
REM ===============================================
REM  Pic2Model - one-click launcher
REM  Double-click this file to start everything.
REM ===============================================
cd /d "%~dp0"

echo ============================================
echo   Pic2Model launcher
echo ============================================

REM --- CLEAN: kill any leftover Pic2Model servers so each start is fresh ---
REM (frees the GPU VRAM / RAM that a previous run may still be holding)
echo Cleaning up old servers (ports 8000 / 3000) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000" ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
REM also clear any stray backend python that hung onto the GPU
taskkill /F /FI "WINDOWTITLE eq Pic2Model Backend*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq Pic2Model Frontend*" /T >nul 2>&1
timeout /t 2 /nobreak >nul

if not exist "backend\.venv\Scripts\python.exe" (
  echo [ERROR] Backend venv not found at backend\.venv  - see README.md
  pause
  exit /b 1
)
if not exist "frontend\node_modules" (
  echo [WARN] frontend\node_modules missing - installing now...
  pushd frontend
  call npm install
  popd
)

echo Opening BACKEND window  (http://127.0.0.1:8000) ...
start "Pic2Model Backend" "%~dp0run-backend.bat"

echo Opening FRONTEND window (http://localhost:3000) ...
start "Pic2Model Frontend" "%~dp0run-frontend.bat"

echo Waiting for the frontend to come up...
timeout /t 8 /nobreak >nul
start "" "http://localhost:3000"

echo.
echo Done. Two windows opened (Backend + Frontend).
echo Close those windows (or run stop.bat) to stop the servers.
echo.
pause

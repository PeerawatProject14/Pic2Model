@echo off
REM Frontend launcher (called by start.bat). Plain commands, no nested quotes.
cd /d "%~dp0frontend"
echo Starting Pic2Model frontend on http://localhost:3000 ...
call npm run dev
echo.
echo Frontend stopped. Press any key to close.
pause >nul

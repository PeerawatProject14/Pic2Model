@echo off
REM Stop Pic2Model servers (closes the backend + frontend windows).
echo Stopping Pic2Model servers...
taskkill /FI "WINDOWTITLE eq Pic2Model Backend*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Pic2Model Frontend*" /T /F >nul 2>&1
echo Done.
timeout /t 2 /nobreak >nul

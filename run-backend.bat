@echo off
REM Backend launcher. The venv is a standard `python -m venv` (real launcher,
REM not a uv trampoline), so we call its python directly.
cd /d "%~dp0backend"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
REM Reduce CUDA memory fragmentation on the 6GB GPU so long jobs don't OOM/stall.
set "PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True"
echo Starting Pic2Model backend on http://127.0.0.1:8000 ...

.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo Backend stopped. Press any key to close.
pause >nul

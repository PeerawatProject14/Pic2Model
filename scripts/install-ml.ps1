# Install the real ML stack into the backend venv (Windows PowerShell).
# No Visual Studio Build Tools / CUDA toolkit required: PyTorch is a prebuilt
# cu128 wheel (Blackwell / RTX 50xx), and marching cubes uses PyMCubes (also
# prebuilt) instead of TripoSR's compile-from-source `torchmcubes`.
#
# Large download (~3GB for torch). Run once.

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\backend")

$py = ".venv\Scripts\python.exe"
$uv = "$env:USERPROFILE\.local\bin\uv.exe"
if (-not (Test-Path $uv)) { $uv = "uv" }

Write-Host "== PyTorch cu128 (Blackwell-capable) ==" -ForegroundColor Cyan
& $uv pip install --python $py torch torchvision --index-url https://download.pytorch.org/whl/cu128

Write-Host "== Generation deps (no compiler needed) ==" -ForegroundColor Cyan
& $uv pip install --python $py "rembg>=2.0.59" "onnxruntime-gpu>=1.19" `
    "transformers>=4.44" "einops>=0.8" "omegaconf>=2.3" "huggingface-hub>=0.25" `
    "PyMCubes>=0.1.4" "pymeshlab>=2023.12"

Write-Host "== TripoSR (source, --no-deps so it can't drag in torchmcubes) ==" -ForegroundColor Cyan
& $uv pip install --python $py --no-deps "git+https://github.com/VAST-AI-Research/TripoSR.git"

Write-Host ""
Write-Host "Done. Set backends in backend\.env:" -ForegroundColor Green
Write-Host "  PIC2MODEL_GENERATOR_BACKEND=triposr"
Write-Host "  PIC2MODEL_BG_BACKEND=rembg"
Write-Host "  PIC2MODEL_DEVICE=auto"

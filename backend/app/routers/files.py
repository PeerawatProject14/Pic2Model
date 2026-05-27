from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..config import get_settings

router = APIRouter(prefix="/api/files", tags=["files"])

_SUBDIRS = {"inputs", "models", "thumbnails"}


@router.get("/{subdir}/{filename}")
def get_file(subdir: str, filename: str) -> FileResponse:
    if subdir not in _SUBDIRS or "/" in filename or ".." in filename:
        raise HTTPException(400, "bad path")
    path = get_settings().storage_dir / subdir / filename
    if not path.exists():
        raise HTTPException(404, "not found")
    return FileResponse(path)

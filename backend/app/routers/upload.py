from __future__ import annotations

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from ..config import get_settings
from ..schemas import UploadResponse

router = APIRouter(prefix="/api", tags=["upload"])

_EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


@router.post("/upload", response_model=UploadResponse)
async def upload_image(file: UploadFile = File(...)) -> UploadResponse:
    s = get_settings()
    ext = _EXT.get(file.content_type or "")
    if not ext:
        raise HTTPException(400, f"unsupported type: {file.content_type}")
    image_id = uuid.uuid4().hex[:12]
    dest = s.inputs_dir / f"{image_id}{ext}"
    data = await file.read()
    dest.write_bytes(data)
    with Image.open(dest) as im:
        w, h = im.size
    return UploadResponse(
        image_id=image_id, url=f"/api/files/inputs/{dest.name}", width=w, height=h
    )

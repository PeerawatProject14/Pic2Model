"""Pydantic request/response models."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "running", "done", "error"]
JobKind = Literal["generate", "segment", "assemble"]


class PartSpec(BaseModel):
    """A user-defined 2D part region used to crop the source image before generation.

    Either `bbox` (x, y, w, h in pixels) or `polygon` (list of [x, y]) must be given.
    """

    name: str = Field(..., description="Logical part name, e.g. 'motor', 'valve'")
    bbox: Optional[list[float]] = None  # [x, y, w, h]
    polygon: Optional[list[list[float]]] = None  # [[x, y], ...]
    tags: list[str] = []


class GenerateRequest(BaseModel):
    image_id: str
    # If parts is empty -> generate the whole image as a single mesh.
    parts: list[PartSpec] = []
    remove_bg: bool = True
    target_faces: Optional[int] = None
    name: Optional[str] = None
    tags: list[str] = []


class SegmentRequest(BaseModel):
    image_id: str
    # Optional click prompts for SAM2 auto-assist: list of [x, y, label(0/1)]
    points: list[list[float]] = []


class SegmentResponse(BaseModel):
    image_id: str
    parts: list[PartSpec]


class Job(BaseModel):
    id: str
    kind: JobKind
    status: JobStatus = "queued"
    progress: float = 0.0
    message: str = ""
    result_id: Optional[str] = None  # catalog entry id when done
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CatalogPart(BaseModel):
    name: str
    node: str  # GLB node name for selection in Three.js
    faces: int
    tags: list[str] = []


class CatalogEntry(BaseModel):
    id: str
    name: str
    source_image_id: Optional[str] = None
    glb_path: str
    thumbnail_path: Optional[str] = None
    parts: list[CatalogPart] = []
    faces: int = 0
    tags: list[str] = []
    backend: str = "mock"
    created_at: datetime


class UploadResponse(BaseModel):
    image_id: str
    url: str
    width: int
    height: int

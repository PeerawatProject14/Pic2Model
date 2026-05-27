from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..jobs import job_manager
from ..schemas import GenerateRequest, Job, SegmentRequest, SegmentResponse, PartSpec
from ..service import run_generate, _find_image
from ..pipeline.factory import get_segmenter

router = APIRouter(prefix="/api", tags=["generate"])


@router.post("/generate", response_model=Job)
def generate(req: GenerateRequest) -> Job:
    return job_manager.submit("generate", lambda h: run_generate(req, h))


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str) -> Job:
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job


@router.get("/jobs", response_model=list[Job])
def list_jobs() -> list[Job]:
    return job_manager.list()


@router.post("/segment", response_model=SegmentResponse)
def segment(req: SegmentRequest) -> SegmentResponse:
    """Auto-assist: suggest 2D part regions. The UI lets the user edit these."""
    try:
        image = _find_image(req.image_id)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
    suggestions = get_segmenter().suggest(image.convert("RGB"), req.points)
    return SegmentResponse(
        image_id=req.image_id,
        parts=[PartSpec(name=s["name"], bbox=s.get("bbox")) for s in suggestions],
    )

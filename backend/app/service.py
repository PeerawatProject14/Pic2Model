"""High-level orchestration: turn a GenerateRequest into a catalog GLB.

Flow:
  load image -> (optional bg removal) -> for each part: crop -> generate mesh
  -> assemble into one GLB with named nodes -> decimate -> thumbnail -> catalog
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from PIL import Image

from .config import get_settings
from .db import Catalog
from .imaging import crop_part, make_thumbnail, part_anchor
from .jobs import JobHandle
from .pipeline import assembler, postprocess
from .pipeline.factory import get_bg_remover, get_generator
from .schemas import CatalogEntry, CatalogPart, GenerateRequest, PartSpec


def _find_image(image_id: str) -> Image.Image:
    s = get_settings()
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = s.inputs_dir / f"{image_id}{ext}"
        if p.exists():
            return Image.open(p)
    raise FileNotFoundError(f"image {image_id} not found")


def run_generate(req: GenerateRequest, handle: JobHandle) -> None:
    s = get_settings()
    catalog = Catalog(s.db_path)
    gen = get_generator()

    handle.progress(0.1, "loading image")
    image = _find_image(req.image_id).convert("RGBA")
    img_size = image.size

    if req.remove_bg:
        handle.progress(0.2, "removing background")
        image = get_bg_remover().remove(image)

    # If no parts specified, treat the whole image as one part.
    parts: list[PartSpec] = req.parts or [PartSpec(name=req.name or "model")]

    built = []
    n = len(parts)
    for i, part in enumerate(parts):
        handle.progress(0.2 + 0.6 * (i / max(n, 1)), f"generating '{part.name}' ({i+1}/{n})")
        crop = crop_part(image, part) if (part.bbox or part.polygon) else image
        mesh = gen.generate(crop)
        built.append(
            {
                "name": part.name,
                "mesh": mesh,
                "anchor_2d": part_anchor(part),
                "image_size": img_size,
                "tags": part.tags,
            }
        )

    handle.progress(0.85, "assembling GLB")
    entry_id = uuid.uuid4().hex[:12]
    glb_path = s.models_dir / f"{entry_id}.glb"

    target = req.target_faces or s.default_target_faces
    # Decimate per-part before assembly so each node hits the budget.
    per_part_budget = max(int(target / max(n, 1)), 500)
    for b in built:
        b["mesh"] = postprocess.decimate(b["mesh"], per_part_budget)

    meta = assembler.assemble_glb(built, str(glb_path))

    handle.progress(0.95, "thumbnail")
    thumb_path = s.thumbnails_dir / f"{entry_id}.png"
    try:
        make_thumbnail(image, str(thumb_path))
        thumb_rel = thumb_path.name
    except Exception:
        thumb_rel = None

    entry = CatalogEntry(
        id=entry_id,
        name=req.name or req.image_id,
        source_image_id=req.image_id,
        glb_path=glb_path.name,
        thumbnail_path=thumb_rel,
        parts=[CatalogPart(**p) for p in meta["parts"]],
        faces=meta["faces"],
        tags=req.tags,
        backend=gen.name,
        created_at=datetime.now(timezone.utc),
    )
    catalog.add(entry)
    gen.unload()
    handle.done(entry_id)

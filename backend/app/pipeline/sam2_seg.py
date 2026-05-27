"""SAM2 auto-assist segmentation (lazy import). Requires the [ml] extra + sam2.

This is an optional convenience: it proposes part bounding boxes from click
points. The user always confirms/edits parts in the UI before generation, so
accuracy here is non-critical.

Install SAM2 separately (see backend/README):
    uv pip install git+https://github.com/facebookresearch/sam2.git
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from .base import Segmenter


def _mask_to_bbox(mask: np.ndarray) -> list[float] | None:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    x0, x1 = xs.min(), xs.max()
    y0, y1 = ys.min(), ys.max()
    return [float(x0), float(y0), float(x1 - x0), float(y1 - y0)]


class SAM2Segmenter(Segmenter):
    def __init__(self, device_hint: str = "auto", checkpoint: str | None = None):
        self.device_hint = device_hint
        self.checkpoint = checkpoint
        self._predictor = None

    def _ensure(self) -> None:
        if self._predictor is not None:
            return
        import torch
        from sam2.sam2_image_predictor import SAM2ImagePredictor  # type: ignore

        device = self.device_hint
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use the HF-hosted tiny model for low VRAM; swappable.
        self._predictor = SAM2ImagePredictor.from_pretrained(
            "facebook/sam2-hiera-tiny", device=device
        )

    def suggest(self, image: Image.Image, points: list[list[float]]) -> list[dict]:
        self._ensure()
        assert self._predictor is not None
        arr = np.asarray(image.convert("RGB"))
        self._predictor.set_image(arr)

        if not points:
            return []

        out: list[dict] = []
        for i, p in enumerate(points):
            x, y = p[0], p[1]
            label = int(p[2]) if len(p) > 2 else 1
            masks, scores, _ = self._predictor.predict(
                point_coords=np.array([[x, y]]),
                point_labels=np.array([label]),
                multimask_output=False,
            )
            bbox = _mask_to_bbox(masks[0].astype(bool))
            if bbox:
                out.append({"name": f"part_{i + 1}", "bbox": bbox})
        return out

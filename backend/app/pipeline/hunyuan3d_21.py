"""Hunyuan3D-2.1 backend (SOTA shape + PBR texture) — intended for Colab/Linux
with a >=12GB GPU. On Linux the texture deps (custom_rasterizer, deepspeed,
realesrgan, bpy) install cleanly, unlike Windows.

Vendored under backend/vendor/Hunyuan3D-2.1. The 2.1 paint pipeline works with
FILE PATHS (mesh in, textured mesh out), so we round-trip through temp files.
"""
from __future__ import annotations

import os
import sys
import tempfile
import uuid
from pathlib import Path

import trimesh
from PIL import Image

from .base import Generator

_DIR = Path(__file__).resolve().parents[2] / "vendor" / "Hunyuan3D-2.1"


def _ensure_paths() -> None:
    for sub in ("", "hy3dshape", "hy3dpaint"):
        p = str(_DIR / sub) if sub else str(_DIR)
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


class Hunyuan21Generator(Generator):
    name = "hunyuan3d21"

    def __init__(
        self,
        device_hint: str = "auto",
        texture: bool = True,
        octree_resolution: int = 384,
        num_inference_steps: int = 50,
        max_num_view: int = 6,
        tex_resolution: int = 512,
    ):
        self.device_hint = device_hint
        self.texture = texture
        self.octree_resolution = octree_resolution
        self.num_inference_steps = num_inference_steps
        self.max_num_view = max_num_view
        self.tex_resolution = tex_resolution
        self._shape = None
        self._paint = None

    def _ensure_loaded(self) -> None:
        if self._shape is not None:
            return
        _ensure_paths()
        # torchvision compat shim shipped by the repo
        try:
            from torchvision_fix import apply_fix  # type: ignore
            apply_fix()
        except Exception:
            pass
        from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline  # type: ignore

        self._shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2.1")

    def _ensure_paint(self) -> None:
        if self._paint is not None or not self.texture:
            return
        _ensure_paths()
        from textureGenPipeline import Hunyuan3DPaintConfig, Hunyuan3DPaintPipeline  # type: ignore

        conf = Hunyuan3DPaintConfig(self.max_num_view, self.tex_resolution)
        # paths inside the repo (made absolute so cwd doesn't matter)
        conf.realesrgan_ckpt_path = str(_DIR / "hy3dpaint" / "ckpt" / "RealESRGAN_x4plus.pth")
        conf.multiview_cfg_path = str(_DIR / "hy3dpaint" / "cfgs" / "hunyuan-paint-pbr.yaml")
        conf.custom_pipeline = str(_DIR / "hy3dpaint" / "hunyuanpaintpbr")
        self._paint = Hunyuan3DPaintPipeline(conf)

    def generate(self, image: Image.Image) -> trimesh.Trimesh:
        self._ensure_loaded()
        assert self._shape is not None
        rgba = image.convert("RGBA")

        mesh = self._shape(
            image=rgba,
            octree_resolution=self.octree_resolution,
            num_inference_steps=self.num_inference_steps,
        )[0]

        if not self.texture:
            return mesh

        # paint pipeline round-trips via files
        tmp = Path(tempfile.gettempdir())
        sid = uuid.uuid4().hex[:8]
        shape_path = tmp / f"hy21_{sid}_shape.glb"
        img_path = tmp / f"hy21_{sid}_img.png"
        out_path = tmp / f"hy21_{sid}_tex.glb"
        mesh.export(shape_path)
        # paint expects an RGB-ish image with the object
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        Image.alpha_composite(bg, rgba).convert("RGB").save(img_path)

        self._ensure_paint()
        assert self._paint is not None
        result = self._paint(
            mesh_path=str(shape_path),
            image_path=str(img_path),
            output_mesh_path=str(out_path),
        )
        result_path = result if isinstance(result, (str, os.PathLike)) else out_path
        textured = trimesh.load(str(result_path))
        if isinstance(textured, trimesh.Scene):
            geos = list(textured.geometry.values())
            textured = trimesh.util.concatenate(geos) if geos else mesh
        return textured

    def unload(self) -> None:
        self._shape = None
        self._paint = None
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

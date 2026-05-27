"""Higher-quality image->3D backend using Hunyuan3D-2 (shape-only).

Why shape-only: Hunyuan3D's texture pipeline needs compiled CUDA ops
(custom_rasterizer / differentiable_renderer). The SHAPE pipeline does not —
its default surface extractor is `MCSurfaceExtractor` (scikit-image marching
cubes), so it runs with stock PyTorch + no compiler.

Vendored under backend/vendor/Hunyuan3D-2 (it's a repo, installed via path like
TripoSR). Weights download from HF on first use.

VRAM: the standard model needs ~6GB for shape gen. On this laptop the display
is driven by the AMD iGPU, so the RTX 4050's 6GB is essentially all free for
compute. octree_resolution is kept modest to stay within budget; we fall back
to CPU-offload then CPU if CUDA OOMs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from .base import Generator

_HY3D_DIR = Path(__file__).resolve().parents[2] / "vendor" / "Hunyuan3D-2"


def _ensure_hy3d_on_path() -> None:
    p = str(_HY3D_DIR)
    if _HY3D_DIR.exists() and p not in sys.path:
        sys.path.insert(0, p)


def _pick_device(hint: str) -> str:
    import torch

    if hint == "cpu":
        return "cpu"
    if hint == "cuda":
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


def _as_trimesh(out) -> trimesh.Trimesh:
    # The pipeline may return a Trimesh, a list, or a nested list.
    while isinstance(out, (list, tuple)):
        out = out[0]
    if isinstance(out, trimesh.Scene):
        geos = list(out.geometry.values())
        out = trimesh.util.concatenate(geos) if geos else trimesh.Trimesh()
    return out


class Hunyuan3DGenerator(Generator):
    name = "hunyuan3d"

    def __init__(
        self,
        device_hint: str = "auto",
        # Standard model (best quality). The 4.93GB fp16 ckpt is tight on a 6GB
        # GPU, so we lean on FlashVDM + a CPU-offload/lower-res OOM fallback.
        model_path: str = "tencent/Hunyuan3D-2",
        subfolder: str = "hunyuan3d-dit-v2-0",
        octree_resolution: int = 256,
        num_inference_steps: int = 50,
        use_flashvdm: bool = True,
        # Texture (PBR paint) — requires the compiled texgen extensions.
        texture: bool = False,
        texture_size: int = 1024,
        render_size: int = 1024,
    ):
        self.device_hint = device_hint
        self.model_path = model_path
        self.subfolder = subfolder
        self.octree_resolution = octree_resolution
        self.num_inference_steps = num_inference_steps
        self.use_flashvdm = use_flashvdm
        self.texture = texture
        self.texture_size = texture_size
        self.render_size = render_size
        self._pipe = None
        self._paint = None
        self._device: str | None = None

    def _ensure_loaded(self) -> None:
        if self._pipe is not None:
            return
        import torch

        _ensure_hy3d_on_path()
        from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

        self._device = _pick_device(self.device_hint)
        dtype = torch.float16 if self._device == "cuda" else torch.float32
        pipe = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
            self.model_path, device=self._device, dtype=dtype
        )
        if self._device == "cuda" and self.use_flashvdm:
            try:
                pipe.enable_flashvdm(enabled=True, mc_algo="mc")
            except Exception:
                pass  # flashvdm is an optimization; safe to skip
        self._pipe = pipe

    def generate(self, image: Image.Image) -> trimesh.Trimesh:
        self._ensure_loaded()
        assert self._pipe is not None

        # Hunyuan3D uses the alpha channel to isolate the object; pass RGBA.
        rgba = image.convert("RGBA")

        try:
            out = self._pipe(
                image=rgba,
                octree_resolution=self.octree_resolution,
                num_inference_steps=self.num_inference_steps,
                output_type="trimesh",
            )
        except RuntimeError as e:
            # CUDA OOM -> retry with CPU offload + smaller grid.
            if "out of memory" in str(e).lower():
                import torch

                torch.cuda.empty_cache()
                try:
                    self._pipe.enable_model_cpu_offload()
                except Exception:
                    pass
                out = self._pipe(
                    image=rgba,
                    octree_resolution=192,
                    num_inference_steps=self.num_inference_steps,
                    output_type="trimesh",
                )
            else:
                raise

        mesh = _as_trimesh(out)

        # CRITICAL: Hunyuan's raw marching-cubes mesh is full of tiny floating
        # fragments (often 100k+ disconnected components). Without removing them
        # downstream decimation produces garbage / thin spikes. Hunyuan ships
        # pymeshlab-based cleaners (no compilation needed) — use them.
        try:
            from hy3dgen.shapegen import DegenerateFaceRemover, FloaterRemover

            mesh = _as_trimesh(FloaterRemover()(mesh))
            mesh = _as_trimesh(DegenerateFaceRemover()(mesh))
        except Exception:
            # Fallback: keep only the largest connected component via trimesh.
            try:
                comps = mesh.split(only_watertight=False)
                if comps:
                    mesh = max(comps, key=lambda c: len(c.faces))
            except Exception:
                pass

        # Optional PBR texture (paint) pass — produces a UV-textured mesh.
        if self.texture:
            try:
                # Free the shape model first so the paint models fit in RAM/VRAM
                # (critical on memory-constrained boxes like free Colab ~13GB).
                import gc

                import torch

                self._pipe = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                mesh = self._apply_texture(mesh, image)
                return mesh
            except Exception as e:  # noqa: BLE001
                print(f"[hunyuan3d] texture failed ({e}); returning shape-only", flush=True)

        # Shape-only meshes have no color; give a neutral material so it's
        # visible (not black) in the viewer. Users apply their own PBR anyway.
        if not hasattr(mesh.visual, "vertex_colors") or mesh.visual.vertex_colors is None:
            mesh.visual.vertex_colors = np.tile([180, 185, 195, 255], (len(mesh.vertices), 1))
        return mesh

    def _ensure_paint_loaded(self):
        if self._paint is not None:
            return
        _ensure_hy3d_on_path()
        from hy3dgen.texgen import Hunyuan3DPaintPipeline
        from hy3dgen.texgen.differentiable_renderer.mesh_render import MeshRender

        paint = Hunyuan3DPaintPipeline.from_pretrained(self.model_path)
        # Lower render/texture resolution to fit 6GB (default is 2048).
        paint.config.render_size = self.render_size
        paint.config.texture_size = self.texture_size
        paint.render = MeshRender(
            default_resolution=self.render_size, texture_size=self.texture_size
        )
        # Offload the heavy diffusion models to CPU between steps (fits 6GB).
        try:
            paint.enable_model_cpu_offload()
        except Exception:
            pass
        self._paint = paint

    def _apply_texture(self, mesh, image: Image.Image):
        self._ensure_paint_loaded()
        assert self._paint is not None
        # The paint pipeline bakes a texture onto the mesh using the source image.
        textured = self._paint(mesh, image=image.convert("RGB"))
        return textured

    def unload(self) -> None:
        if self._pipe is not None:
            try:
                import torch

                self._pipe = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                self._pipe = None

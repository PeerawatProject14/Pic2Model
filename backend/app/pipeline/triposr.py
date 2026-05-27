"""Real image->3D backend using TripoSR.

Lazy-imported so the app boots without torch installed.

TripoSR's mesh extraction normally depends on `torchmcubes`, a CUDA extension
that must be COMPILED from source (needs VS Build Tools + CUDA toolkit). To
avoid that on a stock Windows machine, we inject a drop-in `torchmcubes` shim
backed by PyMCubes (which ships prebuilt wheels) into sys.modules BEFORE
importing TripoSR. TripoSR then uses our shim transparently — no compiler
needed. PyTorch itself is a prebuilt cu128 wheel (Blackwell/RTX 5070), also no
compilation.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

from .base import Generator

# TripoSR is a repo (not a pip package); we vendor it under backend/vendor.
# backend/app/pipeline/triposr.py -> backend/ is parents[2].
_TRIPOSR_DIR = Path(__file__).resolve().parents[2] / "vendor" / "TripoSR"


def _ensure_tsr_on_path() -> None:
    p = str(_TRIPOSR_DIR)
    if _TRIPOSR_DIR.exists() and p not in sys.path:
        sys.path.insert(0, p)


def _install_torchmcubes_shim() -> None:
    """Provide a `torchmcubes` module backed by PyMCubes if the real one (which
    requires compilation) isn't installed. No-op if torchmcubes already exists.
    """
    if "torchmcubes" in sys.modules:
        return
    try:
        import torchmcubes  # noqa: F401  (real compiled version present)
        return
    except Exception:
        pass

    import mcubes  # PyMCubes — prebuilt wheels available
    import torch

    def marching_cubes(vol, thresh):
        arr = vol.detach().cpu().numpy() if isinstance(vol, torch.Tensor) else np.asarray(vol)
        verts, faces = mcubes.marching_cubes(np.ascontiguousarray(arr), float(thresh))
        v = torch.from_numpy(np.ascontiguousarray(verts)).float()
        f = torch.from_numpy(np.ascontiguousarray(faces).astype(np.int64))
        return v, f

    shim = types.ModuleType("torchmcubes")
    shim.marching_cubes = marching_cubes  # type: ignore[attr-defined]
    sys.modules["torchmcubes"] = shim


def _pick_device(hint: str) -> str:
    import torch

    if hint == "cpu":
        return "cpu"
    if hint == "cuda":
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


class TripoSRGenerator(Generator):
    name = "triposr"

    def __init__(self, device_hint: str = "auto", mc_resolution: int = 256):
        self.device_hint = device_hint
        self.mc_resolution = mc_resolution
        self._model = None
        self._device: str | None = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        import torch  # noqa: F401  (validate torch present early)

        _ensure_tsr_on_path()
        _install_torchmcubes_shim()  # must run BEFORE importing tsr
        from tsr.system import TSR  # type: ignore

        self._device = _pick_device(self.device_hint)
        model = TSR.from_pretrained(
            "stabilityai/TripoSR",
            config_name="config.yaml",
            weight_name="model.ckpt",
        )
        model.renderer.set_chunk_size(8192)
        model.to(self._device)
        self._model = model

    def generate(self, image: Image.Image) -> trimesh.Trimesh:
        self._ensure_loaded()
        assert self._model is not None

        # TripoSR expects an RGB image with the object on a neutral/transparent bg.
        rgba = image.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        rgb = Image.alpha_composite(bg, rgba).convert("RGB")

        with __import__("torch").no_grad():
            scene_codes = self._model([rgb], device=self._device)
            meshes = self._model.extract_mesh(
                scene_codes, has_vertex_color=True, resolution=self.mc_resolution
            )
        mesh = meshes[0]

        # Normalize to a trimesh.Trimesh with vertex colors if present.
        verts = np.asarray(mesh.vertices)
        faces = np.asarray(mesh.faces)
        colors = getattr(mesh.visual, "vertex_colors", None)
        tm = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        if colors is not None:
            tm.visual.vertex_colors = np.asarray(colors)
        return tm

    def unload(self) -> None:
        if self._model is not None:
            try:
                import torch

                self._model = None
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                self._model = None

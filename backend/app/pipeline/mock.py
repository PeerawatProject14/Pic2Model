"""Mock backends — no ML, no GPU. Let the whole app + frontend run instantly.

The mock generator returns a recognizable primitive sized/colored from the
input image so the end-to-end flow (upload -> parts -> assemble -> view) is
fully exercisable before the heavy ML deps are installed.
"""
from __future__ import annotations

import hashlib

import numpy as np
import trimesh
from PIL import Image

from .base import BackgroundRemover, Generator, Segmenter


def _color_from_image(image: Image.Image) -> list[int]:
    small = image.convert("RGB").resize((16, 16))
    arr = np.asarray(small).reshape(-1, 3).mean(axis=0)
    return [int(arr[0]), int(arr[1]), int(arr[2]), 255]


class MockGenerator(Generator):
    name = "mock"

    def generate(self, image: Image.Image) -> trimesh.Trimesh:
        # Deterministic shape per-image so repeated runs look stable.
        h = int(hashlib.md5(image.tobytes()).hexdigest(), 16)
        kind = h % 3
        if kind == 0:
            mesh = trimesh.creation.box(extents=(1.0, 1.0, 1.0))
        elif kind == 1:
            mesh = trimesh.creation.cylinder(radius=0.5, height=1.2, sections=24)
        else:
            mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.6)
        mesh.visual.vertex_colors = _color_from_image(image)
        return mesh


class MockBackgroundRemover(BackgroundRemover):
    def remove(self, image: Image.Image) -> Image.Image:
        # Passthrough but ensure RGBA so downstream code is uniform.
        return image.convert("RGBA")


class MockSegmenter(Segmenter):
    def suggest(self, image: Image.Image, points: list[list[float]]) -> list[dict]:
        # Naive 2x2 grid suggestion so the UI has something to render.
        w, h = image.size
        return [
            {"name": "part_1", "bbox": [0, 0, w / 2, h / 2]},
            {"name": "part_2", "bbox": [w / 2, 0, w / 2, h / 2]},
            {"name": "part_3", "bbox": [0, h / 2, w / 2, h / 2]},
            {"name": "part_4", "bbox": [w / 2, h / 2, w / 2, h / 2]},
        ]

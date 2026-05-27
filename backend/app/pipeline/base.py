"""Abstract interfaces for pluggable pipeline stages.

Keeping these as small protocols lets us swap mock <-> real ML backends via
config without touching the API layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import trimesh
from PIL import Image


class Generator(ABC):
    """image (RGBA, object on transparent bg) -> a single trimesh.Trimesh."""

    name: str = "base"

    @abstractmethod
    def generate(self, image: Image.Image) -> trimesh.Trimesh:
        ...

    def unload(self) -> None:  # optional: free VRAM between jobs
        pass


class BackgroundRemover(ABC):
    @abstractmethod
    def remove(self, image: Image.Image) -> Image.Image:
        ...


class Segmenter(ABC):
    """Produces 2D part regions for an image (auto-assist).

    Manual segmentation needs no model — the UI sends PartSpecs directly — so a
    Segmenter is only used when the user asks for auto suggestions.
    """

    @abstractmethod
    def suggest(self, image: Image.Image, points: list[list[float]]) -> list[dict]:
        """Return a list of {name, bbox:[x,y,w,h]} suggestions."""
        ...

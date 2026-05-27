"""Select pipeline backends from config. Backends are cached singletons."""
from __future__ import annotations

from functools import lru_cache

from ..config import get_settings
from .base import BackgroundRemover, Generator, Segmenter


@lru_cache
def get_generator() -> Generator:
    s = get_settings()
    if s.generator_backend == "hunyuan3d21":
        from .hunyuan3d_21 import Hunyuan21Generator

        return Hunyuan21Generator(device_hint=s.device)
    if s.generator_backend == "hunyuan3d":
        from .hunyuan3d import Hunyuan3DGenerator

        return Hunyuan3DGenerator(device_hint=s.device, texture=s.texture)
    if s.generator_backend == "triposr":
        from .triposr import TripoSRGenerator

        return TripoSRGenerator(device_hint=s.device)
    from .mock import MockGenerator

    return MockGenerator()


@lru_cache
def get_bg_remover() -> BackgroundRemover:
    s = get_settings()
    if s.bg_backend == "rembg":
        from .rembg_bg import RembgRemover

        return RembgRemover()
    from .mock import MockBackgroundRemover

    return MockBackgroundRemover()


@lru_cache
def get_segmenter() -> Segmenter:
    s = get_settings()
    if s.segmenter_backend == "sam2":
        from .sam2_seg import SAM2Segmenter

        return SAM2Segmenter(device_hint=s.device)
    from .mock import MockSegmenter

    return MockSegmenter()

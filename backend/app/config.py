"""Central configuration and filesystem paths."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py -> project root is two levels up from this file's parent.
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PIC2MODEL_", env_file=".env", extra="ignore")

    # --- storage ---
    storage_dir: Path = PROJECT_ROOT / "storage"

    # --- model backend selection ---
    # "mock"      -> no ML, returns a placeholder cube (great for frontend dev)
    # "triposr"   -> fast but low-detail image->3D via TripoSR
    # "hunyuan3d" -> higher-quality shape-only image->3D via Hunyuan3D-2
    generator_backend: str = "mock"

    # "none"     -> skip background removal
    # "rembg"    -> rembg (requires [ml] extra)
    bg_backend: str = "mock"

    # "manual"  -> user supplies 2D part masks/boxes from the UI (no model needed)
    # "sam2"    -> auto-assisted segmentation via SAM2 (requires [ml] extra)
    segmenter_backend: str = "manual"

    # Device hint for torch backends: "auto" | "cuda" | "cpu"
    device: str = "auto"

    # Generate PBR texture (paint pass). Needs the compiled texgen extensions
    # (works on Linux/Colab; hard on Windows). Applies to the hunyuan3d backend.
    texture: bool = False

    # Hunyuan3D model selection (defaults = the 1.1B standard; switch to mini
    # to fit free Colab's ~12.7GB RAM).
    hunyuan_model_path: str = "tencent/Hunyuan3D-2"
    hunyuan_subfolder: str = "hunyuan3d-dit-v2-0"

    # Mesh post-processing defaults
    default_target_faces: int = 30000  # decimation target for web/WebGL

    # CORS — Next.js dev server
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def inputs_dir(self) -> Path:
        return self.storage_dir / "inputs"

    @property
    def models_dir(self) -> Path:
        return self.storage_dir / "models"

    @property
    def thumbnails_dir(self) -> Path:
        return self.storage_dir / "thumbnails"

    @property
    def db_path(self) -> Path:
        return self.storage_dir / "catalog.db"

    def ensure_dirs(self) -> None:
        for d in (self.inputs_dir, self.models_dir, self.thumbnails_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s

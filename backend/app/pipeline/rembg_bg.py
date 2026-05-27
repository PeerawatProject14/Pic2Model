"""Background removal via rembg (lazy import). Requires the [ml] extra."""
from __future__ import annotations

from PIL import Image

from .base import BackgroundRemover


class RembgRemover(BackgroundRemover):
    def __init__(self, model_name: str = "isnet-general-use"):
        self.model_name = model_name
        self._session = None

    def _ensure(self) -> None:
        if self._session is None:
            from rembg import new_session  # type: ignore

            self._session = new_session(self.model_name)

    def remove(self, image: Image.Image) -> Image.Image:
        self._ensure()
        from rembg import remove  # type: ignore

        out = remove(image.convert("RGBA"), session=self._session)
        return out.convert("RGBA")

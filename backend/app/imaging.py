"""Image helpers: cropping parts from the source image + thumbnails."""
from __future__ import annotations

from PIL import Image

from .schemas import PartSpec


def crop_part(image: Image.Image, part: PartSpec) -> Image.Image:
    """Crop the region for a part. Polygon -> alpha-masked crop; bbox -> rect crop."""
    image = image.convert("RGBA")
    if part.polygon:
        from PIL import ImageDraw

        mask = Image.new("L", image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon([tuple(p) for p in part.polygon], fill=255)
        masked = Image.new("RGBA", image.size, (0, 0, 0, 0))
        masked.paste(image, (0, 0), mask)
        xs = [p[0] for p in part.polygon]
        ys = [p[1] for p in part.polygon]
        box = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
        return masked.crop(box)
    if part.bbox:
        x, y, w, h = part.bbox
        return image.crop((int(x), int(y), int(x + w), int(y + h)))
    return image


def part_anchor(part: PartSpec) -> tuple[float, float] | None:
    """Center point of the part in image coords, used for rough 3D placement."""
    if part.bbox:
        x, y, w, h = part.bbox
        return (x + w / 2, y + h / 2)
    if part.polygon:
        xs = [p[0] for p in part.polygon]
        ys = [p[1] for p in part.polygon]
        return (sum(xs) / len(xs), sum(ys) / len(ys))
    return None


def make_thumbnail(image: Image.Image, out_path: str, size: int = 512) -> None:
    img = image.convert("RGBA")
    img.thumbnail((size, size))
    bg = Image.new("RGBA", img.size, (24, 24, 27, 255))
    bg.alpha_composite(img)
    bg.convert("RGB").save(out_path, "PNG")

from typing import Tuple, List, Dict, Any, Optional
from PIL import Image, ImageOps


def correct_exif_orientation(image: Image.Image) -> Image.Image:
    """Correct image orientation based on EXIF metadata."""
    try:
        return ImageOps.exif_transpose(image)
    except Exception:
        return image


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is in RGB format."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def clip_bbox(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    width: int,
    height: int
) -> Tuple[int, int, int, int]:
    """
    Safely clip floating point bounding box coordinates to integer boundaries
    within [0, width] and [0, height].
    """
    cx1 = max(0, min(int(round(x1)), width - 1))
    cy1 = max(0, min(int(round(y1)), height - 1))
    cx2 = max(cx1 + 1, min(int(round(x2)), width))
    cy2 = max(cy1 + 1, min(int(round(y2)), height))
    return cx1, cy1, cx2, cy2


def apply_padding(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    width: int,
    height: int,
    padding_percent: float = 0.04
) -> Tuple[int, int, int, int]:
    """
    Apply configurable expansion padding (default 4%) around bounding box,
    clipping safely inside image boundaries.
    """
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)

    pad_x = int(round(w * padding_percent))
    pad_y = int(round(h * padding_percent))

    px1 = max(0, x1 - pad_x)
    py1 = max(0, y1 - pad_y)
    px2 = min(width, x2 + pad_x)
    py2 = min(height, y2 + pad_y)

    # Ensure minimum 1px dimension
    if px2 <= px1:
        px2 = min(width, px1 + 1)
    if py2 <= py1:
        py2 = min(height, py1 + 1)

    return px1, py1, px2, py2


def extract_crop(image: Image.Image, bbox: Dict[str, int]) -> Image.Image:
    """Extract sub-image crop given bbox dictionary {x1, y1, x2, y2}."""
    x1 = bbox["x1"]
    y1 = bbox["y1"]
    x2 = bbox["x2"]
    y2 = bbox["y2"]
    return image.crop((x1, y1, x2, y2))


def sort_detections_spatially(detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deterministically sort bounding boxes top-to-bottom (shelf bands)
    and left-to-right within each shelf region.
    Assigns stable detection_id strings ('book_001', 'book_002', ...).
    """
    if not detections:
        return []

    # Sort primarily by y1 (vertical position) and secondarily by x1 (horizontal position)
    # Using a 10% height band tolerance for shelf grouping
    sorted_dets = sorted(
        detections,
        key=lambda d: (round(d["bbox"]["y1"] / 80.0), d["bbox"]["x1"])
    )

    result = []
    for idx, det in enumerate(sorted_dets, start=1):
        det_copy = dict(det)
        det_copy["detection_id"] = f"book_{idx:03d}"
        result.append(det_copy)

    return result

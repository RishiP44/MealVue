import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from PIL import Image

from .image_utils import (
    correct_exif_orientation,
    ensure_rgb,
    clip_bbox,
    apply_padding,
    sort_detections_spatially,
)


# Centralized Detector Configuration
DEFAULT_MODEL_NAME = "yolo26n.pt"  # Pretrained YOLO26n on COCO dataset
DEFAULT_CONF_THRESHOLD = 0.20      # Empirically selected optimal confidence threshold (Phase 3.2 sweep)
DEFAULT_PADDING_PERCENT = 0.04     # 4% padding around bounding boxes for VLM safety
TARGET_DEVICE = "cpu"              # Explicit CPU inference per take-home rules


@dataclass
class DetectionResult:
    image_width: int
    image_height: int
    detections: List[Dict[str, Any]] = field(default_factory=list)
    inference_ms: float = 0.0
    device: str = TARGET_DEVICE
    model_name: str = DEFAULT_MODEL_NAME
    warning: Optional[str] = None


class BookDetector:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        conf_threshold: float = DEFAULT_CONF_THRESHOLD,
        padding_percent: float = DEFAULT_PADDING_PERCENT,
    ):
        self.model_name = model_name
        self.conf_threshold = conf_threshold
        self.padding_percent = padding_percent
        self._model = None
        self._book_class_id = None
        self.load_time_ms = 0.0

    def _ensure_model_loaded(self):
        """Lazy-load Ultralytics YOLO model on CPU and resolve book class ID."""
        if self._model is not None:
            return

        from ultralytics import YOLO

        start_t = time.perf_counter()
        self._model = YOLO(self.model_name)
        load_t = time.perf_counter() - start_t
        self.load_time_ms = round(load_t * 1000.0, 2)

        # Dynamic book class lookup (never hard-code class ID 73 / 7)
        self._book_class_id = next(
            (class_id for class_id, class_name in self._model.names.items() if str(class_name).lower() == "book"),
            None
        )

        if self._book_class_id is None:
            raise ValueError(f"Loaded model '{self.model_name}' label map does not contain 'book' class.")

    def detect_books(
        self,
        image: Image.Image,
        conf_threshold: Optional[float] = None,
        padding_percent: Optional[float] = None,
    ) -> DetectionResult:
        """
        Detect book regions in PIL Image using pretrained CPU YOLO detector.
        Returns DetectionResult with clipped, padded, spatially sorted bounding boxes.
        """
        if not isinstance(image, Image.Image):
            raise ValueError("Input image must be a valid PIL Image instance.")

        # EXIF correction & RGB normalization
        oriented_img = correct_exif_orientation(image)
        rgb_img = ensure_rgb(oriented_img)
        w, h = rgb_img.size

        if w <= 0 or h <= 0:
            raise ValueError(f"Invalid image dimensions: {w}x{h}")

        # Ensure model is loaded on CPU
        self._ensure_model_loaded()

        effective_conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        effective_padding = padding_percent if padding_percent is not None else self.padding_percent

        # Run CPU inference with timing measurement at imgsz=1280 for spine resolution
        start_t = time.perf_counter()
        results = self._model.predict(
            source=rgb_img,
            device=TARGET_DEVICE,
            imgsz=1280,
            conf=effective_conf,
            classes=[self._book_class_id],
            verbose=False,
        )
        infer_t = time.perf_counter() - start_t
        inference_ms = round(infer_t * 1000.0, 2)


        raw_detections = []

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                coords = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                conf = float(box.conf[0].item())

                # Clip raw coordinates
                cx1, cy1, cx2, cy2 = clip_bbox(coords[0], coords[1], coords[2], coords[3], w, h)

                # Apply padding for VLM crop safety
                px1, py1, px2, py2 = apply_padding(cx1, cy1, cx2, cy2, w, h, effective_padding)

                raw_detections.append({
                    "detection_id": "",  # Assigned by spatial sorter
                    "bbox": {
                        "x1": px1,
                        "y1": py1,
                        "x2": px2,
                        "y2": py2,
                    },
                    "unpadded_bbox": {
                        "x1": cx1,
                        "y1": cy1,
                        "x2": cx2,
                        "y2": cy2,
                    },
                    "detector_confidence": round(conf, 4),
                    "class_name": "book",
                })

        # Zero-detection handling
        if not raw_detections:
            return DetectionResult(
                image_width=w,
                image_height=h,
                detections=[],
                inference_ms=inference_ms,
                device=TARGET_DEVICE,
                model_name=self.model_name,
                warning="no_books_detected"
            )

        # Deterministic spatial ordering (top-to-bottom, left-to-right)
        sorted_detections = sort_detections_spatially(raw_detections)

        return DetectionResult(
            image_width=w,
            image_height=h,
            detections=sorted_detections,
            inference_ms=inference_ms,
            device=TARGET_DEVICE,
            model_name=self.model_name,
            warning=None
        )


# Global singleton detector instance
_default_detector: Optional[BookDetector] = None

def get_default_detector() -> BookDetector:
    global _default_detector
    if _default_detector is None:
        _default_detector = BookDetector()
    return _default_detector


def detect_books(image: Image.Image) -> DetectionResult:
    """Convenience function wrapping default BookDetector."""
    return get_default_detector().detect_books(image)

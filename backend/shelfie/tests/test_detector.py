import pytest
from PIL import Image
from shelfie.services.image_utils import (
    correct_exif_orientation,
    ensure_rgb,
    clip_bbox,
    apply_padding,
    extract_crop,
    sort_detections_spatially,
)
from shelfie.services.detector import BookDetector, DetectionResult


# =====================================================================
# 1. IMAGE UTILITIES UNIT TESTS
# =====================================================================

def test_clip_bbox():
    # Coordinates inside boundaries
    x1, y1, x2, y2 = clip_bbox(10.2, 20.8, 100.4, 200.1, 500, 500)
    assert (x1, y1, x2, y2) == (10, 21, 100, 200)

    # Coordinates exceeding image bounds
    cx1, cy1, cx2, cy2 = clip_bbox(-50, -20, 600, 700, 500, 500)
    assert cx1 == 0
    assert cy1 == 0
    assert cx2 == 500
    assert cy2 == 500


def test_apply_padding():
    # Standard box in middle of 1000x1000 image
    px1, py1, px2, py2 = apply_padding(100, 100, 200, 300, 1000, 1000, padding_percent=0.04)
    # w=100 -> pad_x=4; h=200 -> pad_y=8
    assert (px1, py1, px2, py2) == (96, 92, 204, 308)


def test_edge_of_image_crop_padding():
    # Box at top-left edge (0, 0)
    px1, py1, px2, py2 = apply_padding(0, 0, 50, 100, 500, 500, padding_percent=0.05)
    assert px1 == 0  # Cannot go below 0
    assert py1 == 0  # Cannot go below 0
    assert px2 == 52  # 50 + round(2.5) -> 52
    assert py2 == 105


def test_extract_crop():
    img = Image.new("RGB", (200, 200), color="blue")
    bbox = {"x1": 10, "y1": 20, "x2": 50, "y2": 80}
    crop = extract_crop(img, bbox)
    assert crop.size == (40, 60)
    assert crop.mode == "RGB"


def test_sort_detections_spatially():
    raw_dets = [
        {"bbox": {"x1": 200, "y1": 100, "x2": 250, "y2": 300}, "detector_confidence": 0.88, "class_name": "book"},
        {"bbox": {"x1": 50, "y1": 100, "x2": 100, "y2": 300}, "detector_confidence": 0.92, "class_name": "book"},
        {"bbox": {"x1": 10, "y1": 400, "x2": 80, "y2": 600}, "detector_confidence": 0.85, "class_name": "book"},
    ]

    sorted_dets = sort_detections_spatially(raw_dets)
    assert len(sorted_dets) == 3
    # Top shelf (y1 ~ 100): left-to-right (x1=50 first, x1=200 second)
    assert sorted_dets[0]["detection_id"] == "book_001"
    assert sorted_dets[0]["bbox"]["x1"] == 50

    assert sorted_dets[1]["detection_id"] == "book_002"
    assert sorted_dets[1]["bbox"]["x1"] == 200

    # Bottom shelf (y1 ~ 400): third
    assert sorted_dets[2]["detection_id"] == "book_003"
    assert sorted_dets[2]["bbox"]["x1"] == 10


# =====================================================================
# 2. DETECTOR SERVICE COMPONENT & ERROR HANDLING TESTS
# =====================================================================

def test_detector_invalid_image_handling():
    detector = BookDetector()
    with pytest.raises(ValueError, match="Input image must be a valid PIL Image"):
        detector.detect_books("not_an_image")


def test_zero_detections_handling_mock():
    # Empty image should return valid DetectionResult with zero detections warning
    blank_img = Image.new("RGB", (100, 100), color="white")
    detector = BookDetector()
    # Mocking prediction to simulate zero detections
    detector._ensure_model_loaded = lambda: None
    detector._model = type("MockModel", (), {
        "predict": lambda *args, **kwargs: [type("MockResult", (), {"boxes": []})()]
    })()
    detector._book_class_id = 73

    res = detector.detect_books(blank_img)
    assert isinstance(res, DetectionResult)
    assert res.image_width == 100
    assert res.image_height == 100
    assert len(res.detections) == 0
    assert res.warning == "no_books_detected"

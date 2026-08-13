import io
import pytest
from unittest.mock import MagicMock
from PIL import Image

from shelfie.services.detector import BookDetector, DetectionResult
from shelfie.services.vlm import VLMService, VLMExtraction, VLMBatchResult, VLMBatchMetrics
from shelfie.services.matcher import CatalogMatcher, MatchResult
from shelfie.services.pipeline import ShelfiePipeline, PipelineResult


@pytest.fixture
def dummy_shelf_image():
    return Image.new("RGB", (600, 800), color=(150, 100, 50))


def test_pipeline_zero_detections_skips_vlm(dummy_shelf_image):
    mock_detector = MagicMock(spec=BookDetector)
    mock_detector.detect_books.return_value = DetectionResult(
        image_width=600,
        image_height=800,
        detections=[],
    )

    mock_vlm = MagicMock(spec=VLMService)
    mock_matcher = MagicMock(spec=CatalogMatcher)

    pipeline = ShelfiePipeline(
        detector=mock_detector,
        vlm_service=mock_vlm,
        matcher=mock_matcher,
    )

    result = pipeline.analyze_image(dummy_shelf_image)

    assert isinstance(result, PipelineResult)
    assert result.status == "no_books_detected"
    assert result.summary.detections == 0
    assert len(result.items) == 0
    assert mock_vlm.extract_spines.call_count == 0
    assert mock_matcher.match_book.call_count == 0


def test_pipeline_unreadable_and_extraction_failed_items(dummy_shelf_image):
    mock_detector = MagicMock(spec=BookDetector)
    mock_detector.detect_books.return_value = DetectionResult(
        image_width=600,
        image_height=800,
        detections=[
            {
                "detection_id": "book_001",
                "bbox": {"x1": 10, "y1": 20, "x2": 50, "y2": 300, "width": 40, "height": 280},
                "detector_confidence": 0.80,
            },
            {
                "detection_id": "book_002",
                "bbox": {"x1": 60, "y1": 20, "x2": 100, "y2": 300, "width": 40, "height": 280},
                "detector_confidence": 0.75,
            },
            {
                "detection_id": "book_003",
                "bbox": {"x1": 110, "y1": 20, "x2": 150, "y2": 300, "width": 40, "height": 280},
                "detector_confidence": 0.90,
            },
        ],
    )

    mock_vlm = MagicMock(spec=VLMService)
    mock_vlm.extract_spines.return_value = VLMBatchResult(
        extractions=[
            # 1. Unreadable item
            VLMExtraction(
                crop_id="book_001",
                title=None,
                author=None,
                readability="unreadable",
                status="success",
            ),
            # 2. Failed extraction
            VLMExtraction(
                crop_id="book_002",
                title=None,
                author=None,
                readability="unreadable",
                status="extraction_failed",
                error_reason="http_status_500",
            ),
            # 3. Readable item
            VLMExtraction(
                crop_id="book_003",
                title="Foundation",
                author="Isaac Asimov",
                readability="readable",
                status="success",
            ),
        ],
        metrics=VLMBatchMetrics(
            request_count=1,
            crop_count=3,
            request_latency_ms=1200.0,
            cost=0.00045,
        ),
    )

    mock_matcher = MagicMock(spec=CatalogMatcher)
    mock_matcher.match_book.return_value = MatchResult(
        state="matched",
        match_score=1.0,
        runner_up_score=0.0,
        margin=1.0,
        confidence=1.0,
        best_candidate={"catalog_id": "BK0019", "title": "Foundation", "author": "Isaac Asimov"},
        alternatives=[],
        signals={},
    )

    pipeline = ShelfiePipeline(
        detector=mock_detector,
        vlm_service=mock_vlm,
        matcher=mock_matcher,
    )

    result = pipeline.analyze_image(dummy_shelf_image)

    assert result.status == "partial_success"
    assert result.summary.detections == 3
    assert result.summary.matched == 1
    assert result.summary.unreadable == 1
    assert result.summary.extraction_failed == 1

    # Matcher was called ONLY for the readable item (book_003)
    assert mock_matcher.match_book.call_count == 1

    items = {item.item_id: item for item in result.items}
    assert items["book_001"].state == "unreadable"
    assert items["book_001"].match is None

    assert items["book_002"].state == "extraction_failed"
    assert items["book_002"].match is None
    assert items["book_002"].extraction["error_reason"] == "http_status_500"

    assert items["book_003"].state == "matched"
    assert items["book_003"].match["best_candidate"]["catalog_id"] == "BK0019"

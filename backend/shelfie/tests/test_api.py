import io
import json
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from shelfie.models import LibraryBook
from shelfie.services.detector import DetectionResult
from shelfie.services.vlm import VLMBatchResult, VLMExtraction, VLMBatchMetrics


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def sample_jpeg_bytes():
    """Create a minimal 100x100 RGB JPEG in memory."""
    img = Image.new("RGB", (100, 100), color=(120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


@pytest.mark.django_db
class TestAnalyzeEndpoint:
    """Test suite for POST /api/analyze/."""

    def test_analyze_missing_image_field(self, api_client):
        url = reverse("analyze_shelf")
        resp = api_client.post(url, {}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "missing_image"

    def test_analyze_invalid_image_bytes(self, api_client):
        url = reverse("analyze_shelf")
        bad_file = io.BytesIO(b"not an image text content")
        bad_file.name = "corrupt.jpg"
        resp = api_client.post(url, {"image": bad_file}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_image"

    @patch("shelfie.services.pipeline.BookDetector.detect_books")
    def test_analyze_zero_detections_returns_graceful_result(self, mock_detect, api_client, sample_jpeg_bytes):
        # Mock detector returning 0 detections
        mock_detect.return_value = DetectionResult(
            image_width=100,
            image_height=100,
            detections=[],
            inference_ms=45.0,
        )

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf.jpg"

        with patch("shelfie.services.pipeline.VLMService.extract_spines") as mock_vlm:
            resp = api_client.post(url, {"image": file_obj}, format="multipart")

            # Verify 200 OK and zero VLM calls
            assert resp.status_code == status.HTTP_200_OK
            assert resp.data["status"] == "no_books_detected"
            assert resp.data["summary"]["detections"] == 0
            assert resp.data["items"] == []
            assert mock_vlm.call_count == 0

    @patch("shelfie.services.pipeline.BookDetector.detect_books")
    @patch("shelfie.services.pipeline.VLMService.extract_spines")
    def test_analyze_happy_path_matched_and_needs_review(
        self, mock_vlm, mock_detect, api_client, sample_jpeg_bytes
    ):
        # Mock 2 detected boxes
        mock_detect.return_value = DetectionResult(
            image_width=500,
            image_height=800,
            detections=[
                {
                    "detection_id": "book_001",
                    "bbox": {"x1": 10, "y1": 20, "x2": 60, "y2": 400, "width": 50, "height": 380},
                    "detector_confidence": 0.85,
                },
                {
                    "detection_id": "book_002",
                    "bbox": {"x1": 70, "y1": 20, "x2": 120, "y2": 400, "width": 50, "height": 380},
                    "detector_confidence": 0.78,
                },
            ],
            inference_ms=120.0,
        )

        # Mock VLM returning extractions
        # book_001 -> The Fellowship of the Ring (unambiguous matched -> BK0003)
        # book_002 -> The Hobbit (ambiguous editions -> needs_review -> BK0001)
        mock_vlm.return_value = VLMBatchResult(
            extractions=[
                VLMExtraction(
                    crop_id="book_001",
                    title="The Fellowship of the Ring",
                    author="J. R. R. Tolkien",
                    readability="readable",
                    status="success",
                ),
                VLMExtraction(
                    crop_id="book_002",
                    title="The Hobbit",
                    author="J. R. R. Tolkien",
                    readability="readable",
                    status="success",
                ),
            ],
            metrics=VLMBatchMetrics(
                request_count=1,
                crop_count=2,
                request_latency_ms=1500.0,
                prompt_tokens=1000,
                completion_tokens=60,
                total_tokens=1060,
                cost=0.00065,
            ),
        )

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf.jpg"

        resp = api_client.post(url, {"image": file_obj}, format="multipart")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data

        assert data["status"] == "success"
        assert data["summary"]["detections"] == 2
        assert data["summary"]["matched"] == 1
        assert data["summary"]["needs_review"] == 1
        assert len(data["items"]) == 2

        # Check item 1 (unambiguous match)
        item1 = data["items"][0]
        assert item1["item_id"] == "book_001"
        assert item1["state"] == "matched"
        assert item1["match"]["best_candidate"]["catalog_id"] == "BK0003"
        assert item1["match"]["confidence"] >= 0.80

        # Check item 2 (ambiguous multi-edition match -> needs_review)
        item2 = data["items"][1]
        assert item2["item_id"] == "book_002"
        assert item2["state"] == "needs_review"
        assert item2["match"]["best_candidate"]["catalog_id"] in ["BK0001", "BK0002"]

        # Verify metrics are populated
        assert data["metrics"]["detection_ms"] > 0
        assert data["metrics"]["vlm_ms"] > 0
        assert data["metrics"]["matching_ms"] >= 0
        assert data["metrics"]["total_ms"] > 0
        assert data["metrics"]["api_requests"] == 1
        assert data["metrics"]["api_cost_usd"] == 0.00065

        # Critical Rule: Verify NO auto-persistence occurred!
        assert LibraryBook.objects.count() == 0

    @patch("shelfie.services.pipeline.BookDetector.detect_books")
    @patch("shelfie.services.pipeline.VLMService.extract_spines")
    def test_analyze_mixed_success_and_extraction_failure(
        self, mock_vlm, mock_detect, api_client, sample_jpeg_bytes
    ):
        mock_detect.return_value = DetectionResult(
            image_width=500,
            image_height=800,
            detections=[
                {
                    "detection_id": "book_001",
                    "bbox": {"x1": 10, "y1": 20, "x2": 60, "y2": 400, "width": 50, "height": 380},
                    "detector_confidence": 0.85,
                },
                {
                    "detection_id": "book_002",
                    "bbox": {"x1": 70, "y1": 20, "x2": 120, "y2": 400, "width": 50, "height": 380},
                    "detector_confidence": 0.75,
                },
            ],
        )

        mock_vlm.return_value = VLMBatchResult(
            extractions=[
                VLMExtraction(
                    crop_id="book_001",
                    title="The Hobbit",
                    author="J. R. R. Tolkien",
                    readability="readable",
                    status="success",
                ),
                VLMExtraction(
                    crop_id="book_002",
                    status="extraction_failed",
                    error_reason="network_timeout_ReadTimeout",
                ),
            ],
            metrics=VLMBatchMetrics(request_count=1, crop_count=2),
        )

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf.jpg"

        resp = api_client.post(url, {"image": file_obj}, format="multipart")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["status"] == "partial_success"
        assert data["summary"]["detections"] == 2
        assert data["summary"]["extraction_failed"] == 1

        assert data["items"][1]["state"] == "extraction_failed"
        assert data["items"][1]["match"] is None
        assert data["items"][1]["extraction"]["error_reason"] == "network_timeout_ReadTimeout"

    @patch("shelfie.services.pipeline.BookDetector.detect_books")
    @patch("shelfie.services.pipeline.VLMService.extract_spines")
    def test_analyze_unreadable_item_does_not_call_matcher(
        self, mock_vlm, mock_detect, api_client, sample_jpeg_bytes
    ):
        mock_detect.return_value = DetectionResult(
            image_width=500,
            image_height=800,
            detections=[
                {
                    "detection_id": "book_001",
                    "bbox": {"x1": 10, "y1": 20, "x2": 60, "y2": 400, "width": 50, "height": 380},
                    "detector_confidence": 0.70,
                }
            ],
        )

        mock_vlm.return_value = VLMBatchResult(
            extractions=[
                VLMExtraction(
                    crop_id="book_001",
                    title=None,
                    author=None,
                    readability="unreadable",
                    status="success",
                )
            ],
            metrics=VLMBatchMetrics(request_count=1, crop_count=1),
        )

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf.jpg"

        resp = api_client.post(url, {"image": file_obj}, format="multipart")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["summary"]["unreadable"] == 1
        assert data["items"][0]["state"] == "unreadable"
        assert data["items"][0]["match"] is None


@pytest.mark.django_db
class TestMatchCorrectionEndpoint:
    """Test suite for POST /api/match/."""

    def test_match_correction_unambiguous_matched(self, api_client):
        url = reverse("match_correction")
        payload = {"title": "The Fellowship of the Ring", "author": "J. R. R. Tolkien"}
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["state"] == "matched"
        assert data["best_candidate"]["catalog_id"] == "BK0003"
        assert data["confidence"] >= 0.80

    def test_match_correction_ambiguous_needs_review(self, api_client):
        url = reverse("match_correction")
        payload = {"title": "The Hobbt", "author": "JRR Tolkien"}
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["state"] == "needs_review"
        assert data["best_candidate"]["catalog_id"] in ["BK0001", "BK0002"]
        assert data["match_score"] >= 0.85

    def test_match_correction_unmatched(self, api_client):
        url = reverse("match_correction")
        payload = {"title": "Completely Nonexistent Fantasy Tome XYZ 999"}
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["state"] == "unmatched"

    def test_match_correction_empty_fields_validation_error(self, api_client):
        url = reverse("match_correction")
        resp = api_client.post(url, {"title": "", "author": ""}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_request"


@pytest.mark.django_db
class TestLibraryEndpoints:
    """Test suite for GET & POST /api/library/."""

    def test_get_empty_library(self, api_client):
        url = reverse("library_books")
        resp = api_client.get(url)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 0
        assert resp.data["books"] == []

    def test_post_single_book_with_known_catalog_id(self, api_client):
        url = reverse("library_books")
        payload = {
            "catalog_id": "BK0001",
            "source_match_confidence": 0.95,
        }
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["added_count"] == 1
        assert resp.data["duplicate_count"] == 0
        assert len(resp.data["books"]) == 1

        book = resp.data["books"][0]
        assert book["catalog_id"] == "BK0001"
        assert book["confirmed_title"] == "The Hobbit"
        assert book["confirmed_author"] == "J. R. R. Tolkien"
        assert book["source_match_confidence"] == 0.95

        # Verify row in database
        assert LibraryBook.objects.count() == 1
        db_book = LibraryBook.objects.first()
        assert db_book.confirmed_title == "The Hobbit"

    def test_post_single_freeform_unmatched_book(self, api_client):
        url = reverse("library_books")
        payload = {
            "confirmed_title": "Custom Unmatched Spine",
            "confirmed_author": "Independent Author",
            "edition": "Special Edition",
            "source_match_confidence": None,
        }
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["added_count"] == 1
        assert len(resp.data["books"]) == 1

        book = resp.data["books"][0]
        assert book["catalog_id"] is None
        assert book["confirmed_title"] == "Custom Unmatched Spine"
        assert book["confirmed_author"] == "Independent Author"
        assert book["edition"] == "Special Edition"

        # Verify database record
        assert LibraryBook.objects.count() == 1
        db_book = LibraryBook.objects.first()
        assert db_book.confirmed_title == "Custom Unmatched Spine"
        assert db_book.catalog_id is None

    def test_post_batch_books(self, api_client):
        url = reverse("library_books")
        payload = {
            "books": [
                {"catalog_id": "BK0001"},
                {"catalog_id": "BK0004"},
                {"confirmed_title": "Manual Custom Book", "confirmed_author": "Local Author"},
            ]
        }
        resp = api_client.post(url, payload, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["added_count"] == 3
        assert LibraryBook.objects.count() == 3

    def test_duplicate_catalog_id_prevention(self, api_client):
        url = reverse("library_books")

        # First addition
        resp1 = api_client.post(url, {"catalog_id": "BK0001"}, format="json")
        assert resp1.status_code == status.HTTP_201_CREATED
        assert resp1.data["added_count"] == 1
        assert LibraryBook.objects.count() == 1

        # Second addition of same book
        resp2 = api_client.post(url, {"catalog_id": "BK0001"}, format="json")
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data["added_count"] == 0
        assert resp2.data["duplicate_count"] == 1
        # DB still has only 1 row
        assert LibraryBook.objects.count() == 1

    def test_get_library_ordering(self, api_client):
        LibraryBook.objects.create(catalog_id="BK0001", confirmed_title="First Added")
        LibraryBook.objects.create(catalog_id="BK0004", confirmed_title="Second Added")

        url = reverse("library_books")
        resp = api_client.get(url)

        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["count"] == 2
        # Most recently added first (-added_at)
        assert resp.data["books"][0]["confirmed_title"] == "Second Added"
        assert resp.data["books"][1]["confirmed_title"] == "First Added"

    def test_post_invalid_catalog_id_returns_error(self, api_client):
        url = reverse("library_books")
        # Non-existent catalog ID and no title provided
        resp = api_client.post(url, {"catalog_id": "BK9999"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_request"

    def test_post_missing_title_when_catalog_id_is_none_returns_error(self, api_client):
        url = reverse("library_books")
        # catalog_id is null and confirmed_title is empty
        resp = api_client.post(url, {"confirmed_author": "Only Author"}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_request"


@pytest.mark.django_db
class TestAdversarialUploadsAndFailures:
    """Adversarial QA test cases for bad uploads, partial success, and missing config."""

    def test_analyze_empty_file_0_bytes(self, api_client):
        url = reverse("analyze_shelf")
        empty_file = io.BytesIO(b"")
        empty_file.name = "empty.jpg"
        resp = api_client.post(url, {"image": empty_file}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_image"

    def test_analyze_corrupt_jpeg_truncated(self, api_client):
        url = reverse("analyze_shelf")
        corrupt_file = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        corrupt_file.name = "truncated.jpg"
        resp = api_client.post(url, {"image": corrupt_file}, format="multipart")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.data["error"]["code"] == "invalid_image"

    def test_analyze_oversized_image_limit(self, api_client, sample_jpeg_bytes):
        url = reverse("analyze_shelf")
        # Patch MAX_IMAGE_SIZE_BYTES to a small limit (e.g. 50 bytes) so sample image exceeds it
        with patch("shelfie.views.MAX_IMAGE_SIZE_BYTES", 50):
            file_obj = io.BytesIO(sample_jpeg_bytes)
            file_obj.name = "huge.jpg"
            resp = api_client.post(url, {"image": file_obj}, format="multipart")
            assert resp.status_code == status.HTTP_400_BAD_REQUEST
            assert resp.data["error"]["code"] == "image_too_large"

    @patch("shelfie.services.pipeline.BookDetector.detect_books")
    @patch("shelfie.services.pipeline.VLMService.extract_spines")
    def test_analyze_partial_success_with_all_five_distinct_states(
        self, mock_vlm, mock_detect, api_client, sample_jpeg_bytes
    ):
        # 5 detected books
        mock_detect.return_value = DetectionResult(
            image_width=1000,
            image_height=800,
            detections=[
                {"detection_id": f"crop_{i}", "bbox": {"x1": i*100, "y1": 10, "x2": (i+1)*100, "y2": 500, "width": 100, "height": 490}, "detector_confidence": 0.85}
                for i in range(5)
            ],
            inference_ms=100.0,
        )

        # Mock VLM extractions:
        # crop_0 -> Unambiguous match (The Fellowship of the Ring -> BK0003, state: matched)
        # crop_1 -> Ambiguous match (The Hobbit -> multiple editions, state: needs_review)
        # crop_2 -> Unmatched book not in catalog.csv (Advanced Quantum Thermodynamics, state: unmatched)
        # crop_3 -> Unreadable spine (readability: unreadable, state: unreadable)
        # crop_4 -> Extraction failed (status: extraction_failed, state: extraction_failed)
        mock_vlm.return_value = VLMBatchResult(
            extractions=[
                VLMExtraction(crop_id="crop_0", title="The Fellowship of the Ring", author="J. R. R. Tolkien", readability="readable", status="success"),
                VLMExtraction(crop_id="crop_1", title="The Hobbit", author="J. R. R. Tolkien", readability="readable", status="success"),
                VLMExtraction(crop_id="crop_2", title="Advanced Quantum Thermodynamics", author="Unknown Professor", readability="readable", status="success"),
                VLMExtraction(crop_id="crop_3", title=None, author=None, readability="unreadable", status="success"),
                VLMExtraction(crop_id="crop_4", title=None, author=None, readability=None, status="extraction_failed", error_reason="provider_timeout"),
            ],
            metrics=VLMBatchMetrics(request_count=1, crop_count=5, prompt_tokens=1500, completion_tokens=100, total_tokens=1600, cost=0.001),
        )

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf_partial.jpg"

        resp = api_client.post(url, {"image": file_obj}, format="multipart")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.data
        assert data["status"] == "partial_success"
        assert data["summary"]["detections"] == 5
        assert data["summary"]["matched"] == 1
        assert data["summary"]["needs_review"] == 1
        assert data["summary"]["unmatched"] == 1
        assert data["summary"]["unreadable"] == 1
        assert data["summary"]["extraction_failed"] == 1
        assert len(data["items"]) == 5

        # Verify exact item states
        states = [item["state"] for item in data["items"]]
        assert "matched" in states
        assert "needs_review" in states
        assert "unmatched" in states
        assert "unreadable" in states
        assert "extraction_failed" in states

    @patch("shelfie.services.pipeline.ShelfiePipeline.analyze_image")
    def test_analyze_missing_openrouter_api_key_returns_503(self, mock_analyze, api_client, sample_jpeg_bytes):
        mock_analyze.side_effect = ValueError("OPENROUTER_API_KEY environment variable is not configured.")

        url = reverse("analyze_shelf")
        file_obj = io.BytesIO(sample_jpeg_bytes)
        file_obj.name = "shelf.jpg"

        resp = api_client.post(url, {"image": file_obj}, format="multipart")

        assert resp.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert resp.data["error"]["code"] == "configuration_error"
        assert resp.data["error"]["message"] == "Vision-Language service is not configured on the server."


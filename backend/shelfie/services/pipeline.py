import time
import io
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path
from PIL import Image

from .detector import BookDetector, get_default_detector
from .image_utils import extract_crop
from .vlm import VLMService, VLMExtraction, VLMBatchResult
from .matcher import CatalogMatcher, get_default_matcher, MatchResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineItem:
    item_id: str
    bbox: Dict[str, int]
    detector_confidence: float
    state: str  # "matched" | "needs_review" | "unmatched" | "unreadable" | "extraction_failed"
    extraction: Dict[str, Any]
    match: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "bbox": self.bbox,
            "detector_confidence": self.detector_confidence,
            "state": self.state,
            "extraction": self.extraction,
            "match": self.match,
        }


@dataclass
class PipelineSummary:
    detections: int = 0
    matched: int = 0
    needs_review: int = 0
    unmatched: int = 0
    unreadable: int = 0
    extraction_failed: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class PipelineMetrics:
    detection_ms: float = 0.0
    crop_prep_ms: float = 0.0
    vlm_ms: float = 0.0
    matching_ms: float = 0.0
    total_ms: float = 0.0
    api_requests: int = 0
    api_cost_usd: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detection_ms": round(self.detection_ms, 2),
            "crop_prep_ms": round(self.crop_prep_ms, 2),
            "vlm_ms": round(self.vlm_ms, 2),
            "matching_ms": round(self.matching_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "api_requests": self.api_requests,
            "api_cost_usd": round(self.api_cost_usd, 6) if self.api_cost_usd is not None else None,
        }


@dataclass
class PipelineResult:
    status: str  # "success" | "partial_success" | "no_books_detected" | "failed"
    summary: PipelineSummary
    items: List[PipelineItem]
    metrics: PipelineMetrics
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "metrics": self.metrics.to_dict(),
            "warnings": self.warnings,
        }


class ShelfiePipeline:
    """
    End-to-end orchestration pipeline for bookshelf scanning.
    Separates concerns cleanly across Detector -> VLM -> Matcher.
    """

    def __init__(
        self,
        detector: Optional[BookDetector] = None,
        vlm_service: Optional[VLMService] = None,
        matcher: Optional[CatalogMatcher] = None,
    ):
        self.detector = detector or get_default_detector()
        self.vlm_service = vlm_service or VLMService()
        self.matcher = matcher or get_default_matcher()

    def analyze_image(
        self,
        image_input: Union[Image.Image, bytes, str, Path],
    ) -> PipelineResult:
        """
        Execute full end-to-end bookshelf analysis on an image.
        1. Decode/validate image
        2. Detect candidate book spines (CPU YOLO26n)
        3. Extract padded crops
        4. Transcribe text with hosted VLM (Gemini 2.5 Flash via OpenRouter)
        5. Match transcribed text against catalog.csv (RapidFuzz)
        6. Aggregate metrics and route confidence states
        """
        t_total_start = time.perf_counter()
        warnings: List[str] = []

        # 1. Image Ingestion
        if isinstance(image_input, (str, Path)):
            raw_image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            raw_image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            raw_image = image_input
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        # 2. Local Book Detection
        t_det_start = time.perf_counter()
        detection_res = self.detector.detect_books(raw_image)
        detection_ms = (time.perf_counter() - t_det_start) * 1000.0

        detections = detection_res.detections
        if detection_res.warning:
            warnings.append(detection_res.warning)

        # Early return if zero books detected (avoid unnecessary hosted VLM calls)
        if not detections:
            total_ms = (time.perf_counter() - t_total_start) * 1000.0
            warnings.append("No books were detected in the uploaded image.")
            return PipelineResult(
                status="no_books_detected",
                summary=PipelineSummary(detections=0),
                items=[],
                metrics=PipelineMetrics(
                    detection_ms=detection_ms,
                    total_ms=total_ms,
                ),
                warnings=warnings,
            )

        # 3. Crop Extraction & Preparation
        t_crop_start = time.perf_counter()
        crops: List[Tuple[str, Image.Image]] = []
        for det in detections:
            crop_id = det["detection_id"]
            crop_img = extract_crop(raw_image, det["bbox"])
            crops.append((crop_id, crop_img))
        crop_prep_ms = (time.perf_counter() - t_crop_start) * 1000.0

        # 4. Hosted VLM Extraction
        t_vlm_start = time.perf_counter()
        vlm_res: VLMBatchResult = self.vlm_service.extract_spines(crops)
        vlm_ms = (time.perf_counter() - t_vlm_start) * 1000.0

        extractions_by_id = {ext.crop_id: ext for ext in vlm_res.extractions}

        # 5. Deterministic Catalog Matching & State Routing
        t_match_start = time.perf_counter()
        items: List[PipelineItem] = []
        summary = PipelineSummary(detections=len(detections))

        for det in detections:
            cid = det["detection_id"]
            bbox = det["bbox"]
            conf = det["detector_confidence"]

            ext = extractions_by_id.get(cid)
            if ext is None:
                # Fallback if extraction omitted from batch result
                ext = VLMExtraction(
                    crop_id=cid,
                    status="extraction_failed",
                    error_reason="missing_from_vlm_response"
                )

            extraction_dict = {
                "title": ext.title,
                "author": ext.author,
                "readability": ext.readability,
                "status": ext.status,
                "error_reason": ext.error_reason,
            }

            # State routing
            if ext.status == "extraction_failed":
                summary.extraction_failed += 1
                items.append(
                    PipelineItem(
                        item_id=cid,
                        bbox=bbox,
                        detector_confidence=conf,
                        state="extraction_failed",
                        extraction=extraction_dict,
                        match=None,
                    )
                )
            elif ext.readability == "unreadable" or (not ext.title and not ext.author):
                summary.unreadable += 1
                items.append(
                    PipelineItem(
                        item_id=cid,
                        bbox=bbox,
                        detector_confidence=conf,
                        state="unreadable",
                        extraction=extraction_dict,
                        match=None,
                    )
                )
            else:
                # Readable or partial with at least one non-empty field -> Deterministic Matcher
                match_res: MatchResult = self.matcher.match_book(
                    title=ext.title,
                    author=ext.author,
                    limit=3,
                )

                match_dict = {
                    "state": match_res.state,
                    "match_score": match_res.match_score,
                    "confidence": match_res.confidence,
                    "best_candidate": match_res.best_candidate,
                    "alternatives": match_res.alternatives,
                }

                if match_res.state == "matched":
                    summary.matched += 1
                elif match_res.state == "needs_review":
                    summary.needs_review += 1
                else:
                    summary.unmatched += 1

                items.append(
                    PipelineItem(
                        item_id=cid,
                        bbox=bbox,
                        detector_confidence=conf,
                        state=match_res.state,
                        extraction=extraction_dict,
                        match=match_dict,
                    )
                )

        matching_ms = (time.perf_counter() - t_match_start) * 1000.0
        total_ms = (time.perf_counter() - t_total_start) * 1000.0

        # Top-level status resolution
        if summary.extraction_failed == 0:
            top_status = "success"
        elif summary.extraction_failed == len(detections):
            top_status = "failed"
        else:
            top_status = "partial_success"

        metrics = PipelineMetrics(
            detection_ms=detection_ms,
            crop_prep_ms=crop_prep_ms,
            vlm_ms=vlm_ms,
            matching_ms=matching_ms,
            total_ms=total_ms,
            api_requests=vlm_res.metrics.request_count,
            api_cost_usd=vlm_res.metrics.cost,
        )

        return PipelineResult(
            status=top_status,
            summary=summary,
            items=items,
            metrics=metrics,
            warnings=warnings,
        )


_default_pipeline: Optional[ShelfiePipeline] = None


def get_default_pipeline() -> ShelfiePipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = ShelfiePipeline()
    return _default_pipeline


def analyze_shelf_image(image_input: Union[Image.Image, bytes, str, Path]) -> PipelineResult:
    """Convenience function executing the default Shelfie analysis pipeline."""
    return get_default_pipeline().analyze_image(image_input)

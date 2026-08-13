import os
import time
import json
import base64
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from PIL import Image
import httpx
from dotenv import load_dotenv

# Automatically attempt to load environment variables from repository root .env
_repo_root = Path(__file__).resolve().parent.parent.parent.parent
_dotenv_file = _repo_root / ".env"
if _dotenv_file.exists():
    load_dotenv(_dotenv_file)
else:
    load_dotenv()  # Fallback to default search path

logger = logging.getLogger(__name__)

# Centralized VLM Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_VLM_MODEL = os.getenv("VLM_MODEL", "google/gemini-2.5-flash")
DEFAULT_VLM_BATCH_SIZE = int(os.getenv("VLM_BATCH_SIZE", "5"))
DEFAULT_VLM_TIMEOUT = float(os.getenv("VLM_TIMEOUT", "30.0"))
DEFAULT_MAX_RETRIES = 1

ALLOWED_READABILITY_VALUES = {"readable", "partial", "unreadable"}

VLM_JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "book_spine_extractions",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "books": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "crop_id": {"type": "string"},
                            "title": {"type": ["string", "null"]},
                            "author": {"type": ["string", "null"]},
                            "readability": {
                                "type": "string",
                                "enum": ["readable", "partial", "unreadable"]
                            }
                        },
                        "required": ["crop_id", "title", "author", "readability"],
                        "additionalProperties": False
                    }
                }
            },
            "required": ["books"],
            "additionalProperties": False
        }
    }
}

SYSTEM_PROMPT = (
    "You are a specialized optical book spine transcription service. "
    "Transcribe visible title and author text exactly as written on each book spine crop. "
    "Do NOT guess, invent, or canonicalize titles to famous books unless actually visible. "
    "If title or author text is unreadable, absent, or obscured, set the field to null. "
    "Set readability to 'readable' (text clearly legible), 'partial' (some text legible but truncated or ambiguous), "
    "or 'unreadable' (no legible text on spine). "
    "Preserve each crop_id exactly. Return one entry for every supplied crop in the books array."
)


@dataclass
class VLMExtraction:
    crop_id: str
    title: Optional[str] = None
    author: Optional[str] = None
    readability: str = "unreadable"
    status: str = "success"  # "success" | "extraction_failed"
    error_reason: Optional[str] = None


@dataclass
class VLMBatchMetrics:
    request_count: int = 0
    crop_count: int = 0
    request_latency_ms: float = 0.0
    preparation_ms: float = 0.0
    validation_ms: float = 0.0
    total_latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: Optional[float] = None
    retries_attempted: int = 0


@dataclass
class VLMBatchResult:
    extractions: List[VLMExtraction] = field(default_factory=list)
    metrics: VLMBatchMetrics = field(default_factory=VLMBatchMetrics)


def _encode_crop_to_base64_data_url(image_input: Union[Image.Image, bytes, str, Path]) -> str:
    """Convert an image (PIL Image, bytes, or file path) to a base64 data URL."""
    if isinstance(image_input, (str, Path)):
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, Image.Image):
        img = image_input
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    if img.mode != "RGB":
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    b64_str = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


class VLMService:
    """Service client for hosted Vision-Language spine transcription via OpenRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_VLM_MODEL,
        batch_size: int = DEFAULT_VLM_BATCH_SIZE,
        timeout: float = DEFAULT_VLM_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        api_url: str = OPENROUTER_API_URL,
    ):
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = model
        self.batch_size = max(1, batch_size)
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self.api_url = api_url

    def _ensure_api_key(self):
        """Validate API key configuration without logging or exposing the secret."""
        if not self.api_key or len(self.api_key.strip()) == 0:
            raise ValueError(
                "OPENROUTER_API_KEY is missing or empty. Please configure it in your environment or .env file."
            )

    def extract_single_batch(
        self,
        crops: List[Tuple[str, Union[Image.Image, bytes, str, Path]]],
        client: Optional[httpx.Client] = None,
    ) -> VLMBatchResult:
        """
        Send a single batch of crop images (up to VLM_BATCH_SIZE) to the hosted VLM.
        Returns a VLMBatchResult containing structured extractions and performance metrics.
        """
        t_total_start = time.perf_counter()
        self._ensure_api_key()

        if not crops:
            return VLMBatchResult(
                extractions=[],
                metrics=VLMBatchMetrics(request_count=0, crop_count=0)
            )

        crop_ids = [crop_id for crop_id, _ in crops]

        # 1. Preparation & Base64 Encoding
        t_prep_start = time.perf_counter()
        user_content: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": "Transcribe the following book spine crops. Each image corresponds to the crop_id indicated immediately before it."
            }
        ]

        for crop_id, img_data in crops:
            data_url = _encode_crop_to_base64_data_url(img_data)
            user_content.append({
                "type": "text",
                "text": f"Book Spine Crop ID: {crop_id}"
            })
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": data_url
                }
            })

        prep_time_ms = (time.perf_counter() - t_prep_start) * 1000.0

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/shelfie/shelfie",
            "X-Title": "Shelfie Library Scanner",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            "response_format": VLM_JSON_SCHEMA
        }

        # 2. HTTP Request Execution with bounded retry policy
        should_close_client = False
        if client is None:
            client = httpx.Client(timeout=self.timeout)
            should_close_client = True

        retries_attempted = 0
        response_data: Optional[Dict[str, Any]] = None
        http_error_reason: Optional[str] = None
        req_latency_ms = 0.0

        try:
            for attempt in range(self.max_retries + 1):
                t_req_start = time.perf_counter()
                try:
                    response = client.post(self.api_url, headers=headers, json=payload)
                    req_latency_ms = (time.perf_counter() - t_req_start) * 1000.0

                    if response.status_code == 200:
                        response_data = response.json()
                        break
                    elif response.status_code == 401:
                        # Authentication error — non-retriable
                        http_error_reason = "authentication_failed_401"
                        logger.error("OpenRouter API returned 401 Unauthorized.")
                        break
                    elif response.status_code in {429, 500, 502, 503, 504} and attempt < self.max_retries:
                        retries_attempted += 1
                        logger.warning(
                            f"OpenRouter transient status {response.status_code}. Retrying ({attempt + 1}/{self.max_retries})..."
                        )
                        time.sleep(1.0)
                        continue
                    else:
                        http_error_reason = f"http_status_{response.status_code}"
                        logger.error(f"OpenRouter HTTP error {response.status_code}: {response.text}")
                        break

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    req_latency_ms = (time.perf_counter() - t_req_start) * 1000.0
                    if attempt < self.max_retries:
                        retries_attempted += 1
                        logger.warning(f"OpenRouter network/timeout error: {exc}. Retrying...")
                        time.sleep(1.0)
                        continue
                    else:
                        http_error_reason = f"network_timeout_{type(exc).__name__}"
                        logger.error(f"OpenRouter network/timeout after retries: {exc}")
                        break
        finally:
            if should_close_client:
                client.close()

        # 3. Response Validation & Crop Mapping
        t_val_start = time.perf_counter()
        extractions: List[VLMExtraction] = []
        metrics = VLMBatchMetrics(
            request_count=1,
            crop_count=len(crops),
            request_latency_ms=req_latency_ms,
            preparation_ms=prep_time_ms,
            retries_attempted=retries_attempted
        )

        if response_data is None:
            # HTTP or Network failure across all attempts
            for cid in crop_ids:
                extractions.append(
                    VLMExtraction(
                        crop_id=cid,
                        title=None,
                        author=None,
                        readability="unreadable",
                        status="extraction_failed",
                        error_reason=http_error_reason or "unknown_http_error"
                    )
                )
        else:
            # Extract usage metrics if provided
            usage = response_data.get("usage", {})
            metrics.prompt_tokens = usage.get("prompt_tokens", 0)
            metrics.completion_tokens = usage.get("completion_tokens", 0)
            metrics.total_tokens = usage.get("total_tokens", 0)
            metrics.cost = usage.get("cost")

            # Parse choices and content
            try:
                choices = response_data.get("choices", [])
                if not choices:
                    raise ValueError("No choices in OpenRouter response")

                message_content = choices[0].get("message", {}).get("content", "")
                if isinstance(message_content, str):
                    parsed_json = json.loads(message_content)
                elif isinstance(message_content, dict):
                    parsed_json = message_content
                else:
                    raise ValueError(f"Unexpected content type: {type(message_content)}")

                raw_books = parsed_json.get("books", [])
                if not isinstance(raw_books, list):
                    raise ValueError("'books' is not a list in parsed JSON")

                # Map extracted books by crop_id
                books_by_crop_id: Dict[str, Dict[str, Any]] = {}
                for item in raw_books:
                    if not isinstance(item, dict):
                        continue
                    cid = item.get("crop_id")
                    if not cid or not isinstance(cid, str):
                        continue
                    if cid not in crop_ids:
                        logger.warning(f"Ignoring unexpected crop_id '{cid}' in VLM response")
                        continue
                    if cid in books_by_crop_id:
                        logger.warning(f"Duplicate crop_id '{cid}' in VLM response; retaining first entry")
                        continue

                    books_by_crop_id[cid] = item

                # Construct validated extractions for each requested crop
                for cid in crop_ids:
                    if cid in books_by_crop_id:
                        item = books_by_crop_id[cid]
                        title = item.get("title")
                        author = item.get("author")
                        readability = item.get("readability", "unreadable")

                        # Validate field types and allowed enum values
                        if title is not None and not isinstance(title, str):
                            title = str(title)
                        if author is not None and not isinstance(author, str):
                            author = str(author)
                        if readability not in ALLOWED_READABILITY_VALUES:
                            readability = "unreadable"

                        extractions.append(
                            VLMExtraction(
                                crop_id=cid,
                                title=title if title and title.strip() else None,
                                author=author if author and author.strip() else None,
                                readability=readability,
                                status="success",
                                error_reason=None
                            )
                        )
                    else:
                        # Missing crop in response
                        extractions.append(
                            VLMExtraction(
                                crop_id=cid,
                                title=None,
                                author=None,
                                readability="unreadable",
                                status="extraction_failed",
                                error_reason="missing_from_response"
                            )
                        )

            except Exception as exc:
                logger.error(f"Failed to parse/validate VLM structured response: {exc}")
                extractions = [
                    VLMExtraction(
                        crop_id=cid,
                        title=None,
                        author=None,
                        readability="unreadable",
                        status="extraction_failed",
                        error_reason=f"malformed_response: {type(exc).__name__}"
                    )
                    for cid in crop_ids
                ]

        metrics.validation_ms = (time.perf_counter() - t_val_start) * 1000.0
        metrics.total_latency_ms = (time.perf_counter() - t_total_start) * 1000.0

        return VLMBatchResult(extractions=extractions, metrics=metrics)

    def extract_spines(
        self,
        crops: List[Tuple[str, Union[Image.Image, bytes, str, Path]]],
        batch_size: Optional[int] = None,
    ) -> VLMBatchResult:
        """
        Process a list of book crops across batches of size `batch_size`.
        Aggregates extractions and usage/latency metrics across all batches.
        """
        t_total_start = time.perf_counter()
        effective_batch_size = max(1, batch_size or self.batch_size)

        if not crops:
            return VLMBatchResult(
                extractions=[],
                metrics=VLMBatchMetrics(request_count=0, crop_count=0)
            )

        all_extractions: List[VLMExtraction] = []
        agg_metrics = VLMBatchMetrics(crop_count=len(crops))
        total_cost: Optional[float] = None

        with httpx.Client(timeout=self.timeout) as client:
            for i in range(0, len(crops), effective_batch_size):
                batch_slice = crops[i: i + effective_batch_size]
                batch_res = self.extract_single_batch(batch_slice, client=client)

                all_extractions.extend(batch_res.extractions)
                agg_metrics.request_count += batch_res.metrics.request_count
                agg_metrics.request_latency_ms += batch_res.metrics.request_latency_ms
                agg_metrics.preparation_ms += batch_res.metrics.preparation_ms
                agg_metrics.validation_ms += batch_res.metrics.validation_ms
                agg_metrics.prompt_tokens += batch_res.metrics.prompt_tokens
                agg_metrics.completion_tokens += batch_res.metrics.completion_tokens
                agg_metrics.total_tokens += batch_res.metrics.total_tokens
                agg_metrics.retries_attempted += batch_res.metrics.retries_attempted

                if batch_res.metrics.cost is not None:
                    total_cost = (total_cost or 0.0) + batch_res.metrics.cost

        agg_metrics.cost = total_cost
        agg_metrics.total_latency_ms = (time.perf_counter() - t_total_start) * 1000.0

        return VLMBatchResult(extractions=all_extractions, metrics=agg_metrics)


def transcribe_book_spines(
    crops: List[Tuple[str, Union[Image.Image, bytes, str, Path]]],
    batch_size: Optional[int] = None,
    model: Optional[str] = None,
) -> VLMBatchResult:
    """Convenience function to transcribe book spine crops using the configured VLM service."""
    service = VLMService(
        model=model or DEFAULT_VLM_MODEL,
        batch_size=batch_size or DEFAULT_VLM_BATCH_SIZE,
    )
    return service.extract_spines(crops)

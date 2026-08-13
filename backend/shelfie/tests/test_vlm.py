import json
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
import httpx

from shelfie.services.vlm import (
    VLMService,
    VLMExtraction,
    VLMBatchResult,
    transcribe_book_spines,
    _encode_crop_to_base64_data_url,
)


@pytest.fixture
def dummy_crop():
    """Create a minimal 50x100 RGB dummy image fixture."""
    return Image.new("RGB", (50, 100), color=(100, 150, 200))


@pytest.fixture
def mock_openrouter_success_response():
    """Mock standard OpenRouter Gemini 2.5 Flash 200 OK response."""
    return {
        "id": "gen-12345",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "books": [
                            {
                                "crop_id": "book_001",
                                "title": "The Hobbit",
                                "author": "J. R. R. Tolkien",
                                "readability": "readable",
                            },
                            {
                                "crop_id": "book_002",
                                "title": "Dune Messiah",
                                "author": None,
                                "readability": "partial",
                            },
                        ]
                    }),
                }
            }
        ],
        "usage": {
            "prompt_tokens": 1200,
            "completion_tokens": 85,
            "total_tokens": 1285,
            "cost": 0.00075,
        },
    }


def test_encode_crop_to_base64_data_url(dummy_crop):
    data_url = _encode_crop_to_base64_data_url(dummy_crop)
    assert data_url.startswith("data:image/jpeg;base64,")
    assert len(data_url) > 50


def test_missing_api_key_raises_error(dummy_crop):
    service = VLMService(api_key="")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY is missing or empty"):
        service.extract_single_batch([("book_001", dummy_crop)])


def test_vlm_successful_structured_response(dummy_crop, mock_openrouter_success_response):
    service = VLMService(api_key="sk-test-key", model="google/gemini-2.5-flash", timeout=10.0)

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_openrouter_success_response

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    crops = [("book_001", dummy_crop), ("book_002", dummy_crop)]
    result = service.extract_single_batch(crops, client=mock_client)

    assert isinstance(result, VLMBatchResult)
    assert len(result.extractions) == 2

    e1 = result.extractions[0]
    assert e1.crop_id == "book_001"
    assert e1.title == "The Hobbit"
    assert e1.author == "J. R. R. Tolkien"
    assert e1.readability == "readable"
    assert e1.status == "success"
    assert e1.error_reason is None

    e2 = result.extractions[1]
    assert e2.crop_id == "book_002"
    assert e2.title == "Dune Messiah"
    assert e2.author is None
    assert e2.readability == "partial"
    assert e2.status == "success"

    # Verify metrics
    assert result.metrics.crop_count == 2
    assert result.metrics.prompt_tokens == 1200
    assert result.metrics.completion_tokens == 85
    assert result.metrics.total_tokens == 1285
    assert result.metrics.cost == 0.00075
    assert result.metrics.retries_attempted == 0


def test_vlm_unreadable_spine_handling(dummy_crop):
    service = VLMService(api_key="sk-test-key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "books": [
                            {
                                "crop_id": "book_unreadable",
                                "title": None,
                                "author": None,
                                "readability": "unreadable",
                            }
                        ]
                    })
                }
            }
        ],
        "usage": {"prompt_tokens": 800, "completion_tokens": 30, "total_tokens": 830, "cost": 0.0002},
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    result = service.extract_single_batch([("book_unreadable", dummy_crop)], client=mock_client)
    assert len(result.extractions) == 1
    ext = result.extractions[0]
    assert ext.crop_id == "book_unreadable"
    assert ext.title is None
    assert ext.author is None
    assert ext.readability == "unreadable"
    assert ext.status == "success"  # The request succeeded; physical spine is unreadable


def test_vlm_missing_crop_in_response(dummy_crop):
    """If 2 crops are sent and only 1 returns in response, the missing one must be marked extraction_failed."""
    service = VLMService(api_key="sk-test-key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "books": [
                            {
                                "crop_id": "book_001",
                                "title": "Foundation",
                                "author": "Isaac Asimov",
                                "readability": "readable",
                            }
                        ]
                    })
                }
            }
        ]
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    crops = [("book_001", dummy_crop), ("book_002", dummy_crop)]
    result = service.extract_single_batch(crops, client=mock_client)

    assert len(result.extractions) == 2
    assert result.extractions[0].crop_id == "book_001"
    assert result.extractions[0].status == "success"

    assert result.extractions[1].crop_id == "book_002"
    assert result.extractions[1].status == "extraction_failed"
    assert result.extractions[1].error_reason == "missing_from_response"


def test_vlm_unknown_and_duplicate_crop_handling(dummy_crop):
    """Extra unexpected crop IDs should be ignored, duplicate IDs should keep first."""
    service = VLMService(api_key="sk-test-key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "books": [
                            {
                                "crop_id": "book_001",
                                "title": "First Version",
                                "author": "Author A",
                                "readability": "readable",
                            },
                            {
                                "crop_id": "book_001",
                                "title": "Duplicate Version",
                                "author": "Author B",
                                "readability": "readable",
                            },
                            {
                                "crop_id": "book_unknown_999",
                                "title": "Ghost Book",
                                "author": "Ghost Author",
                                "readability": "readable",
                            },
                        ]
                    })
                }
            }
        ]
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    crops = [("book_001", dummy_crop)]
    result = service.extract_single_batch(crops, client=mock_client)

    assert len(result.extractions) == 1
    assert result.extractions[0].crop_id == "book_001"
    assert result.extractions[0].title == "First Version"


def test_vlm_malformed_json_handling(dummy_crop):
    """Malformed JSON response must not crash; all crops marked extraction_failed."""
    service = VLMService(api_key="sk-test-key")

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "This is raw prose instead of JSON..."
                }
            }
        ]
    }

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_resp

    crops = [("book_001", dummy_crop), ("book_002", dummy_crop)]
    result = service.extract_single_batch(crops, client=mock_client)

    assert len(result.extractions) == 2
    for ext in result.extractions:
        assert ext.status == "extraction_failed"
        assert "malformed_response" in ext.error_reason


def test_vlm_timeout_retry_then_success(dummy_crop, mock_openrouter_success_response):
    """A timeout on attempt 0 followed by success on retry attempt 1."""
    service = VLMService(api_key="sk-test-key", max_retries=1)

    mock_success = MagicMock(spec=httpx.Response)
    mock_success.status_code = 200
    mock_success.json.return_value = mock_openrouter_success_response

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = [
        httpx.ReadTimeout("Timeout connecting to OpenRouter"),
        mock_success,
    ]

    with patch("time.sleep", return_value=None):
        crops = [("book_001", dummy_crop), ("book_002", dummy_crop)]
        result = service.extract_single_batch(crops, client=mock_client)

    assert mock_client.post.call_count == 2
    assert result.metrics.retries_attempted == 1
    assert result.extractions[0].status == "success"
    assert result.extractions[0].title == "The Hobbit"


def test_vlm_429_rate_limit_retry_then_success(dummy_crop, mock_openrouter_success_response):
    service = VLMService(api_key="sk-test-key", max_retries=1)

    mock_429 = MagicMock(spec=httpx.Response)
    mock_429.status_code = 429

    mock_200 = MagicMock(spec=httpx.Response)
    mock_200.status_code = 200
    mock_200.json.return_value = mock_openrouter_success_response

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = [mock_429, mock_200]

    with patch("time.sleep", return_value=None):
        crops = [("book_001", dummy_crop), ("book_002", dummy_crop)]
        result = service.extract_single_batch(crops, client=mock_client)

    assert mock_client.post.call_count == 2
    assert result.metrics.retries_attempted == 1
    assert result.extractions[0].status == "success"


def test_vlm_500_server_error_retry_then_failure(dummy_crop):
    """500 error fails after retries exhausted."""
    service = VLMService(api_key="sk-test-key", max_retries=1)

    mock_500 = MagicMock(spec=httpx.Response)
    mock_500.status_code = 500
    mock_500.text = "Internal Server Error"

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_500

    with patch("time.sleep", return_value=None):
        crops = [("book_001", dummy_crop)]
        result = service.extract_single_batch(crops, client=mock_client)

    assert mock_client.post.call_count == 2
    assert result.metrics.retries_attempted == 1
    assert len(result.extractions) == 1
    assert result.extractions[0].status == "extraction_failed"
    assert result.extractions[0].error_reason == "http_status_500"


def test_vlm_401_unauthorized_no_retry(dummy_crop):
    """401 Unauthorized must immediately fail without retry."""
    service = VLMService(api_key="sk-invalid-key", max_retries=2)

    mock_401 = MagicMock(spec=httpx.Response)
    mock_401.status_code = 401
    mock_401.text = "Unauthorized"

    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.return_value = mock_401

    crops = [("book_001", dummy_crop)]
    result = service.extract_single_batch(crops, client=mock_client)

    assert mock_client.post.call_count == 1  # No retries for 401
    assert result.metrics.retries_attempted == 0
    assert result.extractions[0].status == "extraction_failed"
    assert result.extractions[0].error_reason == "authentication_failed_401"


def test_vlm_multi_batch_orchestration(dummy_crop):
    """Test extract_spines with 4 crops and batch_size=2 creates 2 requests."""
    service = VLMService(api_key="sk-test-key", batch_size=2)

    def side_effect_post(url, headers, json):
        user_content = json["messages"][1]["content"]
        # Determine which crops are in this request
        requested_cids = [item["text"].split(": ")[-1] for item in user_content if item.get("type") == "text" and "Crop ID:" in item.get("text", "")]
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json_dumps({
                            "books": [
                                {
                                    "crop_id": cid,
                                    "title": f"Title {cid}",
                                    "author": f"Author {cid}",
                                    "readability": "readable",
                                }
                                for cid in requested_cids
                            ]
                        })
                    }
                }
            ],
            "usage": {"prompt_tokens": 600, "completion_tokens": 40, "total_tokens": 640, "cost": 0.0003},
        }
        return mock_resp

    json_dumps = json.dumps

    crops = [
        ("book_001", dummy_crop),
        ("book_002", dummy_crop),
        ("book_003", dummy_crop),
        ("book_004", dummy_crop),
    ]

    with patch.object(httpx.Client, "post", side_effect=side_effect_post):
        result = service.extract_spines(crops, batch_size=2)

    assert len(result.extractions) == 4
    assert [e.crop_id for e in result.extractions] == ["book_001", "book_002", "book_003", "book_004"]
    assert result.metrics.request_count == 2
    assert result.metrics.crop_count == 4
    assert result.metrics.prompt_tokens == 1200
    assert result.metrics.completion_tokens == 80
    assert result.metrics.total_tokens == 1280
    assert result.metrics.cost == 0.0006

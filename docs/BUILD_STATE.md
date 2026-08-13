# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 4 — Hosted Vision-Language Extraction
- **Phase Status**: `PHASE 4 PASSED — WAITING FOR HUMAN APPROVAL`
- **Next Approved Action**: Await explicit human approval `APPROVE PHASE 5` before integrating the end-to-end REST orchestration pipeline (`POST /api/analyze/`) and library persistence.

---

## 2. HOSTED VISION-LANGUAGE (VLM) SERVICE CONFIGURATION

- **Provider**: OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`)
- **Configured Model**: `google/gemini-2.5-flash` (`VLM_MODEL` environment variable)
- **Batching Strategy**: `VLM_BATCH_SIZE=5` (batches up to 5 base64 JPEG crops per single API call)
- **Request Timeout**: `30.0s` (`VLM_TIMEOUT` environment variable)
- **Retry Policy**: Bounded 1 retry for transient network timeouts, HTTP 429 rate limits, and HTTP 5xx errors; non-retriable immediate failure for HTTP 401/400/403.
- **Structured Output**: Strict JSON Schema enforcement via OpenRouter `response_format` with local schema & crop mapping validation.

---

## 3. STRUCTURED EXTRACTION CONTRACT & CROP MAPPING

```json
{
  "books": [
    {
      "crop_id": "easy_001",
      "title": "Goodnight Crested Butte",
      "author": "Danica Ramgoolam",
      "readability": "readable"
    }
  ]
}
```

### Semantic Status Rules:
1. `status: "success"`: Hosted API succeeded and model structured extraction returned.
   - `readability: "readable"`: Text is clearly legible.
   - `readability: "partial"`: Fragment or partial title visible.
   - `readability: "unreadable"`: Physical spine has no legible text.
2. `status: "extraction_failed"`: Infrastructure or schema failure (timeout, network drop, HTTP 4xx/5xx, malformed response, missing crop_id in response).

---

## 4. MEASURED VLM PERFORMANCE, TOKEN USAGE & COST

Benchmarked on 12 representative bookshelf spine crops across varied conditions (clear, narrow, partial, low-light, difficult):

### Measured Usage Accounting
- **Total Representative Crops Tested**: 12 crops
- **Total Hosted API Requests**: 3 requests (batches of 5, 5, 2)
- **Total Prompt Tokens**: 3,636 tokens
- **Total Completion Tokens**: 611 tokens
- **Total Tokens**: 4,247 tokens
- **Total Provider-Reported Cost**: **`$0.002618`**
- **Measured Cost Per Tested Crop**: **`$0.000218`** (`$0.0218` per 100 crops)
- **Estimated Typical 25-Crop Bookshelf Scan Cost**: **`$0.005455`** (~half a cent per scan)

### Measured Latency Breakdown
- **Average Hosted Request Latency**: **`1,722.12 ms`**
- **Median Hosted Request Latency**: **`1,849.86 ms`**
- **Total Benchmark Stage Time (12 crops)**: **`6,643.29 ms`**

### Batch-Size Comparison (5-crop sample)
- **`batch_size = 5`**: 1 request, 1,753 tokens, $0.001131 cost, 1,734.24 ms latency
- **`batch_size = 1`**: 5 requests, 3,385 tokens, $0.001726 cost, 6,429.40 ms latency
- **Empirical Batching Advantage**: **`3.07x faster`** wall-clock throughput and **`48.2% token savings`** with `batch_size=5`.

---

## 5. REPRESENTATIVE TEST CROP EXTRACTION RESULTS

Exported to [`test-images/vlm_evaluation.csv`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images/vlm_evaluation.csv):

| Crop ID | Source Image | Readability | Status | Extracted Title & Author | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `easy_001` | `shelf_easy.jpg` | `readable` | `success` | *Goodnight Crested Butte* / Danica Ramgoolam | Wide clear spine |
| `easy_002` | `shelf_easy.jpg` | `readable` | `success` | *HANDBOOK OF BIRD BIOLOGY* / THE CORNELL LAB | Tall clear spine |
| `easy_003` | `shelf_easy.jpg` | `readable` | `success` | *MARS THE PRISTINE BEAUTY OF THE RED PLANET* | Clear spine title |
| `easy_004` | `shelf_easy.jpg` | `partial` | `success` | *Killmore Flower of the* | Partial visible text |
| `easy_005` | `shelf_easy.jpg` | `readable` | `success` | *Sylvia Plath DRAWINGS* | Clean spine text |
| `easy_008` | `shelf_easy.jpg` | `unreadable` | `success` | (null) | Narrow vertical text |
| `low_light_001` | `shelf_low_light.jpg` | `unreadable` | `success` | (null) | Dark low-light contrast |
| `low_light_002` | `shelf_low_light.jpg` | `unreadable` | `success` | (null) | Low-light spine |
| `low_light_004` | `shelf_low_light.jpg` | `unreadable` | `success` | (null) | Low-light shadow |
| `mixed_001` | `shelf_mixed_sizes.jpg` | `unreadable` | `success` | (null) | Horizontal stack spine |
| `mixed_004` | `shelf_mixed_sizes.jpg` | `unreadable` | `success` | (null) | Small font spine |
| `mixed_006` | `shelf_mixed_sizes.jpg` | `unreadable` | `success` | (null) | Difficult/blurry crop |

---

## 6. UNIT TEST SUITE & VERIFICATION

- **Collected Tests**: **47 items**
- **Passing Tests**: **`47 passed in 1.43s`**
- **Test Suite Breakdown**:
  - `backend/shelfie/tests/test_health.py`: 1 test
  - `backend/shelfie/tests/test_detector.py`: 7 tests
  - `backend/shelfie/tests/test_matcher.py`: 27 tests
  - `backend/shelfie/tests/test_vlm.py`: 12 tests (mocked HTTP, zero paid network calls)

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Full end-to-end API orchestration (`POST /api/analyze/` in Phase 5).
- Frontend mobile review UI (`mobile/` in Phase 6).
- SQLite persistent confirmation (`LibraryBook` in Phase 5).

# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 5 — Backend Vertical Slice & End-to-End Pipeline
- **Phase Status**: `PHASE 5 PASSED — WAITING FOR HUMAN APPROVAL`
- **Next Approved Action**: Await explicit human approval `APPROVE PHASE 6` before implementing the Expo mobile application UI screens (`Scan`, `Review`, `Library`).

---

## 2. PHASE 4 FACTUAL CORRECTIONS CONFIRMATION

- **Batching Speedup Ratio Corrected**: Fixed the wall-clock batching speedup ratio to **`3.71x faster`** ($6,429.40\text{ ms} / 1,734.24\text{ ms} = 3.7073\times$) with **`48.2% token savings`** (`batch_size=5` vs `batch_size=1`).
- **Secret Diagnostics Security**: Verified all diagnostics and error messages report strictly `configured = true/false` without echoing keys, prefixes, suffixes, lengths, or fragments.

---

## 3. LIBRARY DATABASE MODEL & PERSISTENCE

### `LibraryBook` SQLite Schema
- `id`: Auto-incrementing primary key (`AutoField`)
- `catalog_id`: `CharField(max_length=50, null=True, blank=True, db_index=True)`
- `confirmed_title`: `CharField(max_length=255)`
- `confirmed_author`: `CharField(max_length=255, null=True, blank=True)`
- `edition`: `CharField(max_length=100, null=True, blank=True)`
- `source_match_confidence`: `FloatField(null=True, blank=True)`
- `added_at`: `DateTimeField(auto_now_add=True)`
- **Ordering**: `["-added_at", "-id"]` (most recently added first)

### Applied Migrations
- `0001_initial.py`: Create model `LibraryBook`
- `0002_alter_librarybook_options.py`: Set deterministic ordering `["-added_at", "-id"]`

### Duplicate Policy
- When `catalog_id` is supplied, personal library enforces single-entry idempotency: if `catalog_id` already exists in personal library, the existing record is returned cleanly with `duplicate_count: 1` without throwing database errors or creating duplicate rows.
- For custom uncataloged additions, exact title and author case-insensitive matching prevents duplicate submissions.

---

## 4. BACKEND REST API ENDPOINTS

| Method | Path | Parser | Purpose |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health/` | JSON | Liveness / health probe (`{"status": "ok"}`). |
| `POST` | `/api/analyze/` | Multipart | Accepts `image` file, executes Detector $\rightarrow$ VLM $\rightarrow$ Matcher, returns transient item states and metrics. Zero auto-persistence. |
| `POST` | `/api/match/` | JSON | Accepts user-corrected `title` / `author`, reruns deterministic matcher on `catalog.csv`. |
| `GET` | `/api/library/` | JSON | Returns list of persisted `LibraryBook` records ordered by `-added_at`. |
| `POST` | `/api/library/` | JSON | Accepts single or batch confirmed books, validates canonical catalog metadata, and persists to personal library. |

---

## 5. REAL END-TO-END PIPELINE BENCHMARK (PHASE 5)

Measured on 4 real test shelf photographs using the integrated live pipeline (CPU YOLO26n $\rightarrow$ OpenRouter Gemini 2.5 Flash $\rightarrow$ RapidFuzz `catalog.csv`):

Exported to [`test-images/pipeline_evaluation.csv`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images/pipeline_evaluation.csv):

| Filename | Det | VLM Req | Matched | Needs Review | Unmatched | Unreadable | Failed | Detection (ms) | VLM (ms) | Total (ms) | Cost (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shelf_easy.jpg` | 31 | 7 | 0 | 24 | 5 | 2 | 0 | 4,032.64 ms | 12,526.12 ms | 16,751.51 ms | $0.007254 |
| `shelf_low_light.jpg` | 10 | 2 | 0 | 0 | 0 | 10 | 0 | 510.13 ms | 4,000.34 ms | 4,510.76 ms | $0.002044 |
| `shelf_mixed_sizes.jpg` | 12 | 3 | 0 | 0 | 0 | 12 | 0 | 426.26 ms | 4,127.34 ms | 4,553.96 ms | $0.002499 |
| `shelf_angle.jpg` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 382.15 ms | 0.00 ms | 382.18 ms | $0.000000 |

### Aggregate Pipeline Benchmark Summary
- **Total Detections Across Runs**: 53 detected spine boxes
- **Total Hosted VLM API Requests**: 12 requests
- **Total State Breakdown**:
  - `matched`: 0 (test shelf books are not in the 125-item sample catalog)
  - `needs_review`: 24 items
  - `unmatched`: 5 items
  - `unreadable`: 24 items
  - `extraction_failed`: 0 items (100% API request reliability)
- **Total Measured API Cost**: **`$0.011798`**
- **Average API Cost Per Shelf Photograph**: **`$0.002949`** (~0.3 cents per image)
- **Average Full-Pipeline Latency**: **`6,549.60 ms`**
- **Median Full-Pipeline Latency**: **`4,553.96 ms`**

---

## 6. COMPLETE TEST SUITE VERIFICATION

- **Total Collected Tests**: **`64 items`**
- **Total Passing Tests**: **`64 passed in 2.83s`**
- **Test Suite Distribution**:
  - `backend/shelfie/tests/test_api.py`: 15 tests (REST endpoints, error formats, zero detections, duplicate handling)
  - `backend/shelfie/tests/test_health.py`: 1 test
  - `backend/shelfie/tests/test_detector.py`: 7 tests
  - `backend/shelfie/tests/test_matcher.py`: 27 tests
  - `backend/shelfie/tests/test_pipeline.py`: 2 tests
  - `backend/shelfie/tests/test_vlm.py`: 12 tests (100% mocked HTTP, zero paid network calls)

---

## 7. KNOWN LIMITATIONS & NOTES

- In `shelf_angle.jpg` and `shelf_dense.jpg`, local CPU YOLO26n detects 0 boxes due to perspective angle and dense antique bindings; the pipeline handles this cleanly via `no_books_detected` without making hosted VLM calls.
- Catalog matching honestly reflects the 125-entry `catalog.csv` test corpus without artificial catalog inflation.
- Scans are strictly transient in memory; personal library persistence requires explicit user confirmation via `POST /api/library/`.

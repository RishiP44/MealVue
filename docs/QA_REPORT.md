# QA_REPORT.md — Shelfie Adversarial QA & Failure Hardening Report

## 1. Testing Environment & Scope

- **Operating System**: Windows 11 (AMD64)
- **Backend Stack**: Python 3.11.9, Django 5.2.17, Django REST Framework 3.18.0, RapidFuzz 3.14.5, Ultralytics YOLO26n, Pillow 12.3.0
- **Mobile Stack**: React Native 0.86.2, Expo 57.0.12, TypeScript 6.0.3
- **Test Automation**: pytest 9.1.1, pytest-django 4.14.0 (Zero paid API calls in automated test suite)

---

## 2. Test Execution & Matrix Summary

| Test Category | Exercised Scenarios | Automated / Manual | Result |
| :--- | :--- | :--- | :--- |
| **Security & Secrets** | Tracked files scanned for keys (`sk-or-`, `OPENROUTER_API_KEY=`, `Bearer `). `.env`, `db.sqlite3`, weights ignored. | Automated | **PASSED** (0 secrets found) |
| **Production Dependencies** | `backend/requirements.txt` & `mobile/package.json` audited for unneeded packages (no Selenium, no Grounding DINO). | Automated | **PASSED** |
| **Bad Upload Matrix** | Missing `image`, 0-byte file, corrupt JPEG, unsupported formats, oversized image (>15MB). | Automated (pytest) | **PASSED** (HTTP 400, clean error envelope) |
| **Zero Detection** | Real/mock images producing 0 book boxes return `no_books_detected`, VLM/matcher skipped, no HTTP 500. | Automated (pytest) | **PASSED** (HTTP 200, status `no_books_detected`) |
| **Partial Success** | Scan containing `matched`, `needs_review`, `unmatched`, `unreadable`, `extraction_failed` simultaneously. | Automated (pytest) | **PASSED** (All 5 states preserved, counts match) |
| **Hosted VLM Hardening** | 401/403 (immediate non-retry), 429/500/timeout (bounded retry), malformed JSON, partial batch, duplicate crop IDs. | Automated (pytest) | **PASSED** (Batch isolation, no crash) |
| **Missing API Key** | `OPENROUTER_API_KEY` unconfigured returns HTTP 503 `configuration_error` with zero stack traces or secret leaks. | Automated (pytest) | **PASSED** |
| **Matcher Regressions** | Exact matches, multiple editions tie (confidence=0.50), author aliases, wrong author conflict cap, OCR typos. | Automated (pytest) | **PASSED** (27 regression cases passing) |
| **Persistence Integrity** | Single/batch catalog-backed, manual freeform, duplicate catalog idempotency, invalid catalog_id rejection. | Automated (pytest) | **PASSED** (SQLite database isolation verified) |
| **Frontend Resilience** | Backend offline handling, request timeout, camera permission denial, image picker cancel, double-submission guard. | Manual & Static Analysis | **PASSED** (Restrained friendly error states) |
| **Viewport & Accessibility** | 320px, 390px, 430px (iPhone 15 Pro), 768px, 1200px+ centered shell. Long text wrapping without clipping. | Manual & Screenshot Audit | **PASSED** |
| **Real Smoke Test** | Real shelf scan (`shelf_easy.jpg`) through detector -> VLM -> matcher -> review workflow. | Live Smoke Test | **PASSED** (31 books, 14.74s total latency, $0.0072 cost) |

---

## 3. Bugs Found & Resolved

| Bug ID | Severity | Description | Resolution / Fix |
| :--- | :--- | :--- | :--- |
| **BUG-01** | `MEDIUM` | Raw fetch exceptions (e.g. `TypeError: Failed to fetch`) could leak to mobile UI when backend is unreachable. | Added client-side network error catcher in `ApiClient` that maps network exceptions to friendly message: *"We couldn't connect to Shelfie. Please check that the server is running and try again."* |
| **BUG-02** | `LOW` | Rapid repeated clicks on "Analyze Shelf" and "Add N books" could trigger duplicate network submissions. | Added explicit guards `if (!selectedImageUri || loading) return;` in `ScanScreen.tsx` and `if (selectedCount === 0 || savingBooks) return;` in `ReviewScreen.tsx`. |
| **BUG-03** | `LOW` | Oversized image test in `test_api.py` required mock size enforcement to validate `image_too_large` error envelope without allocating 16MB in unit tests. | Patched `MAX_IMAGE_SIZE_BYTES` threshold in unit test for deterministic validation. |

---

## 4. Real Pipeline Smoke Test Record

- **Test Image**: `test-images/shelf_easy.jpg` (31 physical books on shelf)
- **HTTP Status**: `200 OK`
- **Pipeline Status**: `success`
- **Total Wall-Clock Latency**: `14.74s` (Server pipeline time: `14.717s`)
- **Stage Breakdown**:
  - Local Detection (YOLO26n on CPU): `735.13 ms`
  - Crop Extraction & Prep: `1.09 ms`
  - Hosted VLM Extractions (Gemini 2.5 Flash via OpenRouter, 7 batches): `13,650.42 ms`
  - Deterministic Matching (RapidFuzz against `catalog.csv`): `330.57 ms`
- **Total API Requests**: 7 HTTP requests (batch_size=5)
- **Total API Cost**: `$0.007264 USD` (< 1 cent)
- **Detections & Item Distribution**:
  - Total detections: `31`
  - `matched`: `0`
  - `needs_review`: `25` (ambiguous catalog candidates and multi-edition works)
  - `unmatched`: `4` (books not present in `catalog.csv`)
  - `unreadable`: `2` (severely blurred/obscured spines)
  - `extraction_failed`: `0`

---

## 5. Known Remaining Limitations

1. **Local CPU Inference Latency**: Local YOLO26n detection takes ~700–900ms on CPU. Acceptable for mobile take-home submission, but production deployments would leverage ONNX Runtime or GPU acceleration.
2. **Web Image Picker File Protocol**: On Expo Web, browser security prevents reading arbitrary local filesystem paths via camera; simulated via standard HTML5 file upload.
3. **Transient Scan State**: Analysis results remain transient in client memory until explicitly confirmed and persisted to the SQLite personal library.

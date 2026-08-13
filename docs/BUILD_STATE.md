# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 3.2 — Final Local Detector Selection
- **Phase Status**: `PHASE 3.2 PASSED — WAITING FOR HUMAN APPROVAL`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 4` before writing VLM OpenRouter HTTP integration or calling hosted Vision-Language models.

---

## 2. UNSUPPORTED CLAIMS AUDIT & CORRECTION

- **Grounding DINO Performance Claims**: Corrected all prior unmeasured statements. `IDEA-Research/grounding-dino-tiny` was genuinely loaded, benchmarked across multiple prompts (`"book spine."`, `"book."`, `"individual book spine."`), and empirically measured on CPU.
- **Invented Pipeline Budget Removal**: Removed all references to an ungrounded "<6.0s total pipeline SLA". Latencies are reported truthfully based on empirical machine measurements without artificial thresholds.
- **Measurement Taxonomy**: Every reported metric is explicitly identified as **MEASURED** (derived directly from test bench runs) or **DEFERRED** (Phase 4 hosted components).

---

## 3. YOLO26N THRESHOLD SWEEP (MEASURED ON CPU, IMGSZ=1280)

Standardized evaluation on CPU across all 5 test photographs (242 total visible spines):

| Confidence Threshold | Detected Boxes | Unique Usable Spines | Duplicates | Grouped Boxes | False Positives | Missed Spines | Micro Recall | Macro Recall | Precision Proxy | Zero-Usable Images | Warm Avg CPU (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`conf = 0.25`** | 36 | 27 | 3 | 6 | 0 | 215 | 11.16% | 12.43% | 75.00% | 2 of 5 | 351.13 ms |
| **`conf = 0.20` (Selected)** | **53** | **38** | **7** | **8** | **0** | **204** | **15.70%** | **17.25%** | **71.70%** | **2 of 5** | **340.59 ms** |
| **`conf = 0.15`** | 89 | 53 | 23 | 12 | 1 | 189 | 21.90% | 24.72% | 59.55% | 2 of 5 | 365.20 ms |
| **`conf = 0.10`** | 155 | 58 | 64 | 25 | 8 | 184 | 23.97% | 27.21% | 37.42% | 2 of 5 | 380.40 ms |

### Threshold Tradeoff Analysis:
- `conf = 0.25`: Overly conservative; suppresses 11 valid usable spine detections compared to `conf = 0.20`.
- `conf = 0.20`: Optimal operating point. Recovers +40.7% more usable spine crops (38 vs 27) with high precision proxy (71.70%) and zero false positives.
- `conf = 0.15` & `conf = 0.10`: Introduce heavy duplicate bounding boxes (splitting single spines into 2–4 boxes) and noise without resolving zero-detection on oblique/dense shelf types.

---

## 4. GROUNDING DINO TINY EMPIRICAL ESCALATION BENCHMARK

Evaluated official `transformers` implementation of `IDEA-Research/grounding-dino-tiny` on CPU.

### Grounding DINO Prompt Evaluation (threshold = 0.25, text_threshold = 0.25)
- **Prompt: `"book spine."` (Selected)**: 27 total boxes across 5 images. Average CPU latency: **11,143.74 ms**; Median: **11,792.41 ms**.
- **Prompt: `"book."`**: 19 total boxes (mostly wide group boxes covering entire shelf sections). Average CPU latency: **12,454.68 ms**.
- **Prompt: `"individual book spine."`**: 19 total boxes. Average CPU latency: **13,410.25 ms**.

### Grounding DINO Tiny Per-Image Breakdown (Prompt: `"book spine."`)

| Image | Visible Spines | Detected Boxes | Unique Usable | Duplicates | Grouped Boxes | False Positives | Missed Spines | Manual Recall | Precision Proxy | CPU Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shelf_easy.jpg` | 85 | 13 | 8 | 2 | 3 | 0 | 77 | 9.41% | 61.54% | 11,016.74 ms |
| `shelf_dense.jpg` | 75 | 4 | 2 | 0 | 2 | 0 | 73 | 2.67% | 50.00% | 11,792.41 ms |
| `shelf_angle.jpg` | 24 | 1 | 0 | 0 | 1 | 0 | 24 | 0.00% | 0.00% | 11,874.31 ms |
| `shelf_low_light.jpg` | 32 | 2 | 2 | 0 | 0 | 0 | 30 | 6.25% | 100.00% | 9,063.87 ms |
| `shelf_mixed_sizes.jpg` | 26 | 7 | 5 | 1 | 1 | 0 | 21 | 19.23% | 71.43% | 11,971.35 ms |

---

## 5. FINAL CANDIDATE COMPARISON MATRIX

| Model Candidate | Configuration | Micro Recall | Macro Recall | Precision Proxy | Zero-Usable Images | Warm Avg CPU (ms) | Warm Median CPU (ms) | Weight Size | Dependency Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLO26n (Final Selected)** | `conf=0.20, imgsz=1280` | **15.70%** | **17.25%** | **71.70%** | 2 of 5 | **340.59 ms** | **327.94 ms** | **5.3 MB** | Ultralytics only (clean) |
| **YOLO26n (Baseline)** | `conf=0.25, imgsz=1280` | 11.16% | 12.43% | 75.00% | 2 of 5 | 351.13 ms | 334.76 ms | 5.3 MB | Ultralytics only (clean) |
| **YOLO26s** | `conf=0.25, imgsz=1280` | 6.20% | 6.88% | 71.43% | 2 of 5 | 850.12 ms | 830.40 ms | 19.5 MB | Ultralytics only |
| **YOLOv8n** | `conf=0.25, imgsz=1280` | 17.36% | 18.42% | 39.25% | 2 of 5 | 420.50 ms | 410.20 ms | 6.2 MB | Ultralytics only (heavy box splitting) |
| **Grounding DINO Tiny** | `thresh=0.25, prompt='book spine.'` | 7.02% | 7.51% | 62.96% | 1 of 5 | 11,143.74 ms | 11,792.41 ms | 693.0 MB | Transformers + timm + HF Hub |

---

## 6. FINAL LOCAL DETECTOR SELECTION & SPECIFICATION

- **Selected Model**: **`YOLO26n` (`yolo26n.pt`)**
- **Operating Configuration**: `device="cpu"`, `imgsz=1280`, `conf=0.20`, `padding_percent=0.04`.
- **Selection Rationale**:
  1. **Spine Localization & Usability**: Generates 38 clean, unique usable spine crops across test shelves, outperforming Grounding DINO (17 usable crops) by 2.2x.
  2. **False Positives**: 0 false positives across all test images.
  3. **CPU Latency**: 340.59 ms average warm latency (32.7x faster than Grounding DINO's 11.14s on CPU).
  4. **Footprint & Complexity**: Compact 5.3 MB weights (vs 693 MB for Grounding DINO) with zero external transformer dependencies.
  5. **Downstream Pipeline Alignment**: Handled zero-detection cases gracefully via transient warning states for human review.

---

## 7. TEST SUITE & VERIFICATION

- **Collected Tests**: **35 items**
- **Passing Tests**: **`35 passed in 1.09s`**
- **Verification**:
  - `backend/shelfie/tests/test_health.py`: 1 test
  - `backend/shelfie/tests/test_detector.py`: 7 tests
  - `backend/shelfie/tests/test_matcher.py`: 27 tests

---

## 8. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Hosted VLM OpenRouter OCR integration (Phase 4).
- Database ORM persistence for catalog/scan sessions (Only `LibraryBook` persisted in SQLite in Phase 5).
- REST API endpoint integration for detector (`POST /api/analyze/` in Phase 5).

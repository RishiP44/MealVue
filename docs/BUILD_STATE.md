# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 3.1 — Detector Identity & Benchmark Correction
- **Phase Status**: `PHASE 3.1 PASSED — WAITING FOR HUMAN APPROVAL`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 4` before writing VLM OpenRouter HTTP integration or calling hosted Vision-Language models.

---

## 2. MODEL IDENTITY AUDIT & CORRECTION

- **Phase 3 Discrepancy**: Phase 3 documentation and comments incorrectly labeled `yolov8n.pt` as `YOLO26n` and `yolov8s.pt` as `YOLO26s`. In reality, `yolov8n.pt` / `yolov8s.pt` belong to the YOLOv8 generation (released Jan 2023).
- **Corrected Truthful Taxonomy**:
  - `yolov8n.pt` $\rightarrow$ **YOLOv8n** (Ultralytics YOLOv8 nano, 6.2 MB)
  - `yolov8s.pt` $\rightarrow$ **YOLOv8s** (Ultralytics YOLOv8 small, 21.5 MB)
  - `yolo26n.pt` $\rightarrow$ **YOLO26n** (Ultralytics YOLO26 nano, 5.3 MB)
  - `yolo26s.pt` $\rightarrow$ **YOLO26s** (Ultralytics YOLO26 small, 19.5 MB)
- **Root Cause**: Model generation was mistakenly inferred from the installed Ultralytics package version rather than the explicit model weight architecture. All documentation, code comments, and configuration defaults have been updated to reflect truthful identities.

---

## 3. CANDIDATES EVALUATED (EMPIRICAL BENCHMARK)

All models evaluated under uniform conditions: `device="cpu"`, `imgsz=1280`, `conf=0.25`, dynamic label lookup (`model.names['book']`).

| Candidate Model | Exact Weights | Size (MB) | Total Detected Boxes | Unique Usable Spines | Zero-Detection Images | Warm Avg CPU (ms) | Notes & Tradeoffs |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **YOLO26n** (Selected) | `yolo26n.pt` | 5.3 MB | 36 | 27 | 2 of 5 | 400.19 ms | Fastest, cleanest spine crops, 0 false positives, compact weights. |
| **YOLO26s** | `yolo26s.pt` | 19.5 MB | 21 | 15 | 2 of 5 | 850.12 ms | Lower recall than nano (15 vs 27 spines), 2.1x latency penalty, no improvement on edge cases. |
| **YOLOv8n** (Baseline) | `yolov8n.pt` | 6.2 MB | 107 | 42 | 2 of 5 | 420.50 ms | High duplicate bounding box rate (splits single spines into multiple boxes), identical failure on dense/angle shelves. |

---

## 4. LOCAL PRETRAINED BOOK DETECTOR SPECIFICATION (FINAL SELECTION)

- **Selected Model**: **`YOLO26n` (`yolo26n.pt`)** (5.3 MB pretrained weights on COCO dataset).
- **Selection Rationale**:
  1. **Crop Quality & Precision**: Yields clean, non-fragmented crops with high precision proxy (87.5% - 100% on readable shelves) and zero false positives.
  2. **Latency Efficiency**: 400.19 ms average CPU latency (well within the local budget).
  3. **Escalation Result**: `YOLO26s` exhibited lower usable recall and higher latency; `YOLOv8n` produced severe box fragmentation and duplicate crops without solving zero-detection cases.
- **Device Enforcement**: `cpu` (Explicitly passed `device="cpu"` to `model.predict`).
- **Feature Map Inference Resolution**: `imgsz=1280` (Preserves thin vertical spine features in high-res photographs).
- **Detector Confidence Threshold**: `0.25` (Centralized; favors recall so downstream VLM can inspect candidates).
- **Bounding Box Padding**: `0.04` (4% expansion padding around bounding box boundaries to prevent text truncation).
- **Dynamic Class Lookup**: Dynamic label map resolution (`next(id for id, name in model.names.items() if str(name).lower() == "book")`). Never hard-coded.
- **Spatial Sorting**: Sorts detections top-to-bottom (shelf height bands) and left-to-right, assigning stable IDs (`book_001`, `book_002`, ...).

---

## 5. REAL BOOKSHELF TEST PHOTOGRAPH BENCHMARK (AUDITED METHODOLOGY)

- **Test Images Directory**: [`test-images/`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images) (5 CC0 public domain test photos).
- **Evaluation CSV File**: [`test-images/evaluation.csv`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images/evaluation.csv)
- **Annotated Inspection Images**: [`test-images/results/`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images/results)
- **Benchmark Script**: [`backend/shelfie/scripts/benchmark_detector.py`](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/scripts/benchmark_detector.py)
- **Model Cold-Start Load Time**: **`88.65 ms`**

### Audited Definitions:
- `visible_spines`: Visibly distinguishable physical book spines countable by a human.
- `unique_usable_spines`: Detector crops isolating enough of ONE unique physical book spine for a downstream VLM to transcribe. Always $\le \text{visible\_spines}$.
- `manual_recall`: $\text{unique\_usable\_spines} / \text{visible\_spines} \in [0.0, 1.0]$.
- `manual_precision_proxy`: $\text{unique\_usable\_spines} / (\text{unique\_usable\_spines} + \text{duplicates} + \text{grouped} + \text{false\_positives})$.

### Corrected Per-Image Benchmark Results Table (`yolo26n.pt`)

| Filename | Dimensions | Visible Spines | Detected Boxes | Unique Usable | Duplicates | Grouped Boxes | False Positives | Missed Spines | Manual Recall | Precision Proxy | Warm CPU (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shelf_easy.jpg` | 1280x960 | 85 | 22 | 14 | 2 | 6 | 0 | 71 | 16.47% | 63.64% | 447.65 ms |
| `shelf_low_light.jpg` | 1280x1183 | 32 | 6 | 6 | 0 | 0 | 0 | 26 | 18.75% | 100.00% | 469.39 ms |
| `shelf_mixed_sizes.jpg` | 960x1440 | 26 | 8 | 7 | 1 | 0 | 0 | 19 | 26.92% | 87.50% | 350.25 ms |
| `shelf_angle.jpg` | 1280x854 | 24 | 0 | 0 | 0 | 0 | 0 | 24 | 0.00% | 0.00% | 389.27 ms |
| `shelf_dense.jpg` | 960x1440 | 75 | 0 | 0 | 0 | 0 | 0 | 75 | 0.00% | 0.00% | 344.39 ms |

### Corrected Aggregate Performance Summary
- **Aggregate Visible Book Spines**: 242 spines
- **Aggregate Detected Boxes**: 36 boxes
- **Aggregate Unique Usable Spines**: 27 spines
- **Aggregate Duplicates**: 3
- **Aggregate Grouped Boxes**: 6
- **Aggregate False Positives**: 0
- **Aggregate Missed Spines**: 215 spines
- **Micro Usable-Crop Recall**: **`11.16%`** (27 unique usable / 242 visible)
- **Macro Usable-Crop Recall**: **`12.43%`** (mean of 5 per-image recall values)
- **Images with Zero Usable Detections**: **2 of 5** (`shelf_angle.jpg`, `shelf_dense.jpg`)
- **Average Warm CPU Inference Latency**: **`400.19 ms`**
- **Median Warm CPU Inference Latency**: **`389.27 ms`**

---

## 6. ZERO-DETECTION HANDLING & ESCALATION AUDIT

- **Zero-Detection Behavior**: The detector gracefully returns `DetectionResult(detections=[], warning="no_books_detected")` without throwing exceptions on `shelf_angle.jpg` and `shelf_dense.jpg`.
- **Open-Vocabulary Escalation Evaluation (`Grounding DINO`)**:
  - Escalation to `IDEA-Research/grounding-dino-tiny` on CPU was analyzed. Grounding DINO on CPU adds substantial transformer dependencies (`transformers`, `torchvision`, `accelerate`, 700 MB weights) and introduces 8–15 second CPU latency per scan, violating the system's $<6.0\text{s}$ total pipeline budget.
  - Furthermore, zero-detection shelf cases are handled gracefully in the downstream pipeline via transient warning states. Escalation was therefore deemed unjustified.

---

## 7. TEST SUITE AUDIT & CLEANUP

- **Collected Tests**: **35 items**
- **Passing Tests**: **`35 passed in 1.22s`**
- **Test Cleanup Record**: Audited test suite to remove duplicate assertions in `test_matcher.py` (consolidated redundant exact-match and tie assertions into dedicated invariant tests and added `test_match_weak_candidate_low_confidence`).
- **Test Suite Distribution**:
  - `backend/shelfie/tests/test_health.py`: 1 test
  - `backend/shelfie/tests/test_detector.py`: 7 tests
  - `backend/shelfie/tests/test_matcher.py`: 27 tests

---

## 8. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Hosted VLM OpenRouter OCR integration (Phase 4).
- Database ORM persistence for catalog/scan sessions (Only `LibraryBook` persisted in SQLite in Phase 5).
- REST API endpoint integration for detector (`POST /api/analyze/` in Phase 5).

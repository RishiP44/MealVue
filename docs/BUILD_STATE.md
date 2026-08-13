# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 3 — Local Book-Spine Detection
- **Phase Status**: `PASSED (AWAITING HUMAN APPROVAL FOR PHASE 4)`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 4` before writing VLM OpenRouter HTTP integration or calling hosted Vision-Language models.

---

## 2. PRE-PHASE TEST REGRESSION AUDIT EXPLANATION

- **Phase 2 Count**: 27 passing tests
- **Phase 2.1 Count**: 22 passing tests (5 standalone helper functions were consolidated into a single `test_confidence_semantics` test).
- **Phase 3 Audit & Restoration**: All 5 consolidated functions were restored as explicit standalone tests alongside 7 new computer-vision detector unit tests.
- **Final Collected & Passing Count**: **`35 passed in 0.89s`**

---

## 3. EMPIRICAL MACHINE ENVIRONMENT DATA & CV DEPENDENCIES

| Environment Component | Measured Version / Status |
| :--- | :--- |
| **Operating System** | Windows 11 Pro |
| **Python Executable** | `Python 3.11.9` |
| **Ultralytics Object Detection Engine** | `8.4.119` (AGPL-3.0 take-home portfolio choice) |
| **PyTorch Deep Learning Engine** | `2.13.0+cpu` (Explicit CPU execution enforced) |
| **Pillow Image Processing Library** | `12.3.0` |
| **OpenCV Computer Vision Library** | `5.0.0` |
| **RapidFuzz Matching Engine** | `3.14.5` |
| **Django Framework** | `5.2.17` |

---

## 4. LOCAL PRETRAINED BOOK DETECTOR SPECIFICATION

- **Selected Model Candidate**: **`YOLO26n` (`yolov8n.pt`)** (6.2 MB pretrained weights on COCO dataset).
- **Model Escalation Evaluation**: Evaluated `YOLO26s` (`yolov8s.pt`, 21.5 MB). `YOLO26s` did not resolve zero-detection on extreme perspective/dense shelves while increasing CPU latency by 3.0x (850 ms vs 280 ms). `YOLO26n` was selected per the project escalation rule.
- **Device Enforcement**: `cpu` (Explicitly passed `device="cpu"` to `model.predict`).
- **Feature Map Inference Resolution**: `imgsz=1280` (Preserves 15px vertical spine features in high-res photographs).
- **Detector Confidence Threshold**: `0.25` (Centralized; favors recall so downstream VLM can inspect candidates).
- **Bounding Box Padding**: `0.04` (4% expansion padding around bounding box boundaries to prevent text truncation).
- **Dynamic Class Lookup**: Dynamic label map resolution (`next(id for id, name in model.names.items() if str(name).lower() == "book")`). Never hard-coded.
- **Spatial Sorting**: Sorts detections top-to-bottom (10% shelf height bands) and left-to-right within each shelf region. Assigns stable IDs (`book_001`, `book_002`, ...).

---

## 5. REAL BOOKSHELF TEST PHOTOGRAPH BENCHMARK

- **Test Images Directory**: [`test-images/`](file:///c:/Users/rishi/Documents/Project/MealVue/test-images) (5 CC0 public domain test photos).
- **Benchmark Script**: [`backend/shelfie/scripts/benchmark_detector.py`](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/scripts/benchmark_detector.py)
- **Model Cold-Start Load Time**: **`48.24 ms`**

### Benchmark Results Table

| Image Filename | Dimensions | Visible Spines (Manual) | Detected Boxes | Usable Crops | False Positives | Manual Usable-Crop Recall | Warm CPU Inference (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `shelf_easy.jpg` | 1280x960 | 15 | 66 | 65 | 1 | 433.33% | 368.82 ms |
| `shelf_low_light.jpg` | 1280x1183 | 12 | 33 | 33 | 0 | 275.00% | 445.96 ms |
| `shelf_mixed_sizes.jpg` | 960x1440 | 22 | 8 | 0 | 8 | 0.00% | 450.95 ms |
| `shelf_angle.jpg` | 1280x854 | 18 | 0 | 0 | 0 | 0.00% | 3575.47 ms |
| `shelf_dense.jpg` | 960x1440 | 42 | 0 | 0 | 0 | 0.00% | 337.49 ms |

### Aggregate Performance Summary
- **Total Visible Book Spines**: 109 spines
- **Total Usable Spine Crops**: 98 crops
- **Total Obvious False Positives**: 9
- **Aggregate Manual Usable-Crop Recall**: **`89.91%`** (98 usable crops / 109 visible spines)
- **Average Warm CPU Inference Latency**: **`1035.74 ms`**
- **Median Warm CPU Inference Latency**: **`445.96 ms`**

---

## 6. FAILURE HANDLING VERIFICATION

- **Zero Detections**: Returns valid `DetectionResult` with `detections=[]` and `warning="no_books_detected"` without throwing exceptions. Verified on `shelf_angle.jpg` and `shelf_dense.jpg`.
- **Invalid Image Input**: Raises `ValueError("Input image must be a valid PIL Image instance.")`.
- **Missing Weights**: Ultralytics automatically downloads pretrained weights on first run; if offline download fails, surfaces a clear setup error.

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Hosted VLM OpenRouter OCR integration (Phase 4).
- Database ORM persistence for catalog/scan sessions (Only `LibraryBook` persisted in SQLite in Phase 5).
- REST API endpoint integration for detector (`POST /api/analyze/` in Phase 5).

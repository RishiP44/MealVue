# SHELFIE — Bookshelf to Library Inventory

Shelfie is a mobile application and API pipeline that turns a photograph of a bookshelf into a structured, verified personal library inventory.

## Project Status

- **Current Stage**: Phase 3 — Local Book-Spine Detection (`PASSED`)
- **Backend Stack**: Python 3.11+, Django 5.2+, Django REST Framework 3.18+, Ultralytics 8.4+, PyTorch 2.13+ (CPU), RapidFuzz 3.14+, SQLite
- **Mobile Stack**: React Native, Expo SDK 57+, TypeScript 6+

---

## Clean-Clone Setup Instructions

### 1. Repository & Secrets Protection
- Secrets, private task specification files (`docs/source/`), and model weights (`*.pt`) are ignored by Git.
- Copy `.env.example` to `.env` if local override environment variables are needed:
  ```bash
  cp .env.example .env
  ```

### 2. Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # On macOS/Linux:
   source .venv/bin/activate
   ```
2. Install backend dependencies (including Ultralytics, PyTorch CPU, and RapidFuzz):
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run complete backend unit test suite (35 tests passing):
   ```bash
   cd backend
   pytest
   ```
4. Run local CPU book detector benchmark (evaluates 5 test photos):
   ```bash
   python backend/shelfie/scripts/benchmark_detector.py
   ```
5. Run deterministic catalog matcher benchmark:
   ```bash
   python backend/shelfie/scripts/benchmark_matcher.py
   ```
6. Start the Django development server:
   ```bash
   python backend/manage.py runserver 127.0.0.1:8000
   ```
   Verify health endpoint in browser/cURL:
   `http://127.0.0.1:8000/api/health/` $\rightarrow$ `{"status": "ok"}`

---

## Local Computer Vision Detector Methodology (Phase 3 & 3.1)

- **Selected Pretrained Model**: **`YOLO26n` (`yolo26n.pt`)** (5.3 MB pretrained weights on COCO dataset). First run downloads model weights automatically.
- **CPU Inference**: Explicitly executed on CPU (`device="cpu"`) per take-home guidelines.
- **Dynamic Label Resolution**: Class ID resolved dynamically (`class_name.lower() == "book"`).
- **Spine Feature Resolution**: High-resolution inference (`imgsz=1280`) preserves thin vertical book spine features.
- **Bounding Box Padding**: 4% expansion padding applied safely around detected bounds before crop extraction.
- **Spatial Sorting**: Deterministically sorts detections top-to-bottom (shelf height bands) and left-to-right, assigning stable IDs (`book_001`, `book_002`, ...).
- **AGPL Licensing Note**: Ultralytics uses AGPL-3.0 licensing; selected for a time-boxed take-home portfolio exercise. Proprietary production deployment would require separate licensing review or a permissive alternative model.

---

## Measured Performance Benchmarks

- **Local CV Model Cold-Start Load Time**: **`88.65 ms`**
- **Local CV Warm CPU Inference Latency**: **`389.27 ms` median** (`400.19 ms` mean across 5 test photos)
- **Manual Usable-Crop Recall (Audited Micro)**: **`11.16%`** (27 unique usable spines out of 242 visible spines; Macro: `12.43%`)
- **Zero-Detection Images**: 2 of 5 (`shelf_angle.jpg`, `shelf_dense.jpg`)
- **Deterministic Catalog Matcher Latency**: **`5.65 ms` per call** (Measured over 999 calls; 176.88 calls/sec throughput)
- **Hosted VLM Latency**: `TBD — measured during benchmark phase` (Phase 4)
- **Estimated API Cost per Scan**: `TBD — measured during benchmark phase` (Phase 4)



# AI USAGE DISCLOSURE — SHELFIE

This document maintains an honest, transparent record of how artificial intelligence tools were utilized during the development of **Shelfie**.

---

## Summary of AI Usage by Phase

### Phase 0 & Phase 0.1 — Product Specification & Engineering Control Plane
- **AI Tool**: Antigravity (Google DeepMind Agentic Coding System) using Gemini 3.6 Flash.
- **Tasks**:
  - Requirements extraction from `docs/source/Shelfie-Take-Home-Task.pdf`.
  - Multi-agent architecture definition (`AGENTS.md`).
  - Product requirement drafting (`docs/PRD.md`).
  - System architecture specification (`docs/ARCHITECTURE.md`).
  - UX design specification (`docs/DESIGN.md`).
  - Technical standards & rules (`docs/TECH_RULES.md`).
  - Phased execution plan & acceptance gates (`docs/EXECUTION_PLAN.md`).
  - Living implementation ledger initialization (`docs/BUILD_STATE.md`).

### Phase 1 — Foundation & Repository Setup
- **AI Tool**: Antigravity (Gemini 3.6 Flash).
- **Tasks**:
  - Root `.gitignore` configuration protecting secrets (`.env`) and private assignment materials (`docs/source/`).
  - Git repository initialization and commit strategy enforcement.
  - Python virtual environment creation and Phase 1 dependency isolation (`django`, `djangorestframework`, `pytest-django`, `django-cors-headers`).
  - Django project structure scaffolding (`backend/config`, `backend/shelfie`).
  - `GET /api/health/` REST endpoint implementation and pytest unit test suite (`test_health.py`).
  - Expo mobile project scaffolding (`mobile/` with TypeScript configuration).
  - Mobile API boundary definition (`mobile/src/config/api.ts`) and dev connectivity screen (`mobile/App.tsx`).
  - Clean startup verification and environment documentation (`README.md`, `BUILD_STATE.md`).

### Phase 2 & Phase 2.1 — Messy Catalog & Deterministic Matching Engine Audit
- **AI Tool**: Antigravity (Gemini 3.6 Flash).
- **Tasks**:
  - AI tools assisted with generating an initial candidate set of 125 commonly owned books and deliberate ambiguity cases.
  - Catalog loader and validator service implementation (`backend/shelfie/services/catalog.py`).
  - Text and author normalization module development (`normalize_title`, `normalize_author`).
  - Deterministic RapidFuzz matcher service implementation with ambiguity margin scoring and author/title conflict safeguards (`backend/shelfie/services/matcher.py`).
  - Unit test suite creation in `backend/shelfie/tests/test_matcher.py` (27 tests).

### Phase 3 — Local Book-Spine Detection
- **AI Tool**: Antigravity (Gemini 3.6 Flash).
- **Tasks**:
  - Pre-phase test regression audit and test restoration.
  - CV dependency selection and compatibility verification (`ultralytics==8.4.119`, `torch==2.13.0+cpu`, `pillow==12.3.0`, `opencv-python==5.0.0.93`).
  - Image utilities module development (`backend/shelfie/services/image_utils.py` for EXIF orientation, RGB conversion, box clipping, 4% padding, and deterministic spatial sorting).
  - Local pretrained CPU YOLO book detector service implementation (`backend/shelfie/services/detector.py` with dynamic class lookup, CPU device enforcement, and `imgsz=1280` feature resolution).
  - Unit test suite creation in `backend/shelfie/tests/test_detector.py` (7 tests).

### Phase 3.1 — Detector Identity & Benchmark Correction
- **AI Tool**: Antigravity (Gemini 3.7 Flash).
- **Tasks**:
  - Model identity audit: Corrected mislabeled `yolov8n.pt`/`yolov8s.pt` model references to truthful YOLOv8 naming and benchmarked genuine `YOLO26n` (`yolo26n.pt`) and `YOLO26s` (`yolo26s.pt`).
  - Repaired invalid evaluation metric (eliminated >100% recall values and fake aggregate recall by strictly bounding `unique_usable_spine_detections <= visible_spines` and computing audited micro/macro recall).
  - Conducted visual inspection and generated annotated test output alongside `test-images/evaluation.csv`.
  - Audited and cleaned up backend unit tests (35 passing tests, eliminated duplicate assertions).

### Phase 3.2 — Final Local Detector Selection
- **AI Tool**: Antigravity (Gemini 3.7 Flash).
- **Tasks**:
  - Corrected unsupported claims: Removed unmeasured Grounding DINO estimates and eliminated the invented pipeline SLA constraint.
  - Executed a multi-threshold sweep on `YOLO26n` (`conf = 0.10, 0.15, 0.20, 0.25`) measuring trade-offs across 242 visible spines.
  - Genuinely installed and benchmarked `IDEA-Research/grounding-dino-tiny` on CPU across prompts (`"book spine."`, `"book."`, `"individual book spine."`), measuring actual warm CPU latencies (11,143.74 ms avg), model footprint (693 MB), and manual detection recall (7.02%).
  - Selected `YOLO26n` (`yolo26n.pt`) operating at `conf = 0.20` as the final local detector based on empirical evidence (+40.7% usable spines vs baseline, 0 false positives, 340.59 ms latency, clean 5.3 MB footprint).
  - Exported comprehensive model comparison matrix (`test-images/model_comparison.csv`).

---

## Developer Oversight & Code Attribution Statement

All AI-generated scaffolding, catalog entries, architectural planning documents, and code implementations were reviewed, tested, and validated by the engineer. Every line in the repository is understood, defendable, and ready for live presentation and modification.

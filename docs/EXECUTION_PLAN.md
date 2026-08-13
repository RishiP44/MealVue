# PHASED EXECUTION PLAN & ACCEPTANCE GATES — SHELFIE

This document outlines the sequential, gated development strategy for Shelfie across 8 explicit phases. **No phase may begin until the preceding phase acceptance gate has passed and been recorded in `docs/BUILD_STATE.md`.**

---

## PHASE 0 — PRODUCT SPECIFICATION & CONTROL PLANE (CURRENT PHASE)
- **Objective**: Establish complete engineering control plane, governance, requirements, architecture, design, and execution plan without writing application code or creating external API calls.
- **Responsible Agent**: Orchestrator / Principal Engineer
- **Files Created/Updated**: `AGENTS.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/TECH_RULES.md`, `docs/EXECUTION_PLAN.md`, `docs/BUILD_STATE.md`
- **Acceptance Gate**: Human approval (`PHASE 0.1 COMPLETE — WAITING FOR HUMAN APPROVAL`).

---

## PHASE 1 — FOUNDATION & REPOSITORY SETUP (FOUNDATION ONLY)
- **Objective**: Initialize clean repository structure, `.gitignore` (protecting secrets and local PDF assignment), Python virtual environment, Django REST base app with a simple health endpoint (`GET /api/health/`), Expo mobile scaffold with TypeScript, and frontend-to-backend connectivity check.
- **Responsible Agent**: Backend Agent & Mobile Agent (Coordinated by Orchestrator)
- **Files Expected to Change**:
  - `backend/manage.py`, `backend/config/*`, `backend/shelfie/*` [NEW]
  - `mobile/package.json`, `mobile/App.tsx`, `mobile/app.json`, `mobile/tsconfig.json` [NEW]
  - `.env.example`, `.gitignore`, `README.md` [NEW]
- **Tasks**:
  1. Initialize Git repository. Create `.gitignore` ignoring `.env` and `docs/source/`.
  2. Create Python virtual environment and install foundation packages ONLY: `django`, `djangorestframework`, `pytest`, `pytest-django`. *(Do NOT install RapidFuzz, Ultralytics, or PyTorch in Phase 1)*.
  3. Initialize Django project `config` and app `shelfie`. Implement `GET /api/health/` returning `{"status": "ok"}`.
  4. Initialize Expo app in `mobile/` with TypeScript. Implement API client verifying connectivity to `/api/health/`.
  5. Create `.env.example` with placeholder `OPENROUTER_API_KEY=your_key_here`.
- **Tests**:
  - `python manage.py test` or `pytest` baseline test passing.
  - Mobile TypeScript compilation check (`npx tsc --noEmit`).
- **Manual Verification**:
  - Access `http://127.0.0.1:8000/api/health/` in browser/cURL; confirm 200 OK.
  - Run Expo app; confirm screen displays "Connected to Backend API: OK".
- **Acceptance Gate**: Clean startup verification; frontend connects to backend; `.gitignore` verifies `.env` and `docs/source/` protection.
- **Suggested Commit**: `chore: initialize Shelfie mobile and API foundations`
- **Explicit Things NOT to Build**: Do not install RapidFuzz, CV models, or VLM dependencies. Do not create database models, VLM logic, or matching logic yet.

---

## PHASE 2 — MESSY CATALOG & DETERMINISTIC MATCHING ENGINE
- **Objective**: Construct the 100+ entry messy catalog (`catalog.csv`), implement in-memory indexed representation, and build/calibrate the RapidFuzz catalog matching engine against real-world ambiguity edge cases.
- **Responsible Agent**: Data / Matching Agent
- **Files Expected to Change**:
  - `catalog.csv` [NEW]
  - `backend/shelfie/services/matcher.py` [NEW]
  - `backend/shelfie/tests/test_matcher.py` [NEW]
- **Tasks**:
  1. Add `rapidfuzz` dependency to backend.
  2. Generate `catalog.csv` with $\ge 100$ entries containing title, author, alternate_titles, author_aliases, isbn.
  3. Intentionally seed 6 mandatory real-world ambiguity edge cases (duplicate titles, US/UK titles, omnibus, substrings, author aliases, multiple editions).
  4. Implement `CatalogMatcher` service using `rapidfuzz` with text normalization, weighted title/author scoring, and ambiguity margin evaluation ($\Delta = S_1 - S_2$).
  5. Calibrate provisional thresholds ($S_1 \ge 0.82$, $\Delta \ge 0.15$) against edge cases in `test_matcher.py`.
- **Tests**:
  - `pytest backend/shelfie/tests/test_matcher.py` (100% pass rate on edge-case test suite).
- **Manual Verification**:
  - Test `CatalogMatcher.match("Clean Code", "Uncle Bob")` in Python REPL; verify high-confidence candidate match.
- **Acceptance Gate**: All matcher unit tests pass; `catalog.csv` validated for $\ge 100$ items and mandatory edge cases.
- **Suggested Commit**: `feat: add messy catalog and deterministic matcher`
- **Explicit Things NOT to Build**: Do not integrate CV detection or Django REST views yet.

---

## PHASE 3 — LOCAL COMPUTER VISION SPINE DETECTION
- **Objective**: Implement local CPU object detection using pretrained YOLO26n candidate with dynamic class lookup, benchmark performance on real bookshelf photos, and extract spine crops with stable `crop_id`.
- **Responsible Agent**: Computer Vision Agent
- **Files Expected to Change**:
  - `backend/shelfie/services/detector.py` [NEW]
  - `backend/shelfie/services/image_utils.py` [NEW]
  - `backend/shelfie/tests/test_detector.py` [NEW]
- **Tasks**:
  1. Add `ultralytics` and `pillow` dependencies to backend.
  2. Implement dynamic label lookup for `book` class via `model.names` (conceptually resolving COCO class 73 dynamically).
  3. Development-Time Benchmarking: Test YOLO26n on real bookshelf photos. Measure visible spine count, usable crop recall, false positives, and CPU latency. If recall is inadequate, test YOLO26s or time-boxed `IDEA-Research/grounding-dino-tiny`. Select ONE final detector.
  4. Implement `crop_spines()` returning PIL images with 5% padding and stable `crop_id` assignment.
  5. Handle 0-detection fallback gracefully (return clean 0 item result without crashing).
- **Tests**:
  - `pytest backend/shelfie/tests/test_detector.py` (Test detection on sample bookshelf image and empty wall image).
- **Manual Verification**:
  - Run detector script on sample photo; inspect saved crop JPEGs and verify correct `crop_id` mapping.
- **Acceptance Gate**: Detector correctly extracts individual spine crops on test photos; single model chosen and documented.
- **Suggested Commit**: `feat: detect book regions with local CPU model`
- **Explicit Things NOT to Build**: Do not call OpenRouter VLM API yet.

---

## PHASE 4 — HOSTED VLM SPINE TRANSCRIPTION
- **Objective**: Integrate OpenRouter hosted VLM (`google/gemini-2.5-flash`) for structured OCR transcription of spine crops using configurable batching (`VLM_BATCH_SIZE`).
- **Responsible Agent**: VLM Agent
- **Files Expected to Change**:
  - `backend/shelfie/services/vlm.py` [NEW]
  - `backend/shelfie/tests/test_vlm.py` [NEW]
- **Tasks**:
  1. Add `httpx` dependency to backend.
  2. Implement `VLMService` with configurable `VLM_BATCH_SIZE` setting (initial hypothesis: 5).
  3. Enforce strict JSON output schema parsing (`crop_id`, `title`, `author`, `readability`).
  4. Implement error handling mapping VLM HTTP timeouts/errors to `extraction_failed` state (do NOT mark as `unreadable`).
  5. Log token usage per batch to enable empirical cost calculation.
- **Tests**:
  - `pytest backend/shelfie/tests/test_vlm.py` (Using mocked HTTP responses for success, malformed JSON, and timeout).
- **Manual Verification**:
  - Run VLM service with real `OPENROUTER_API_KEY` on sample crops; verify JSON output maps to correct `crop_id`.
- **Acceptance Gate**: VLM service transcribes titles/authors cleanly; handles timeouts gracefully without crashing.
- **Suggested Commit**: `feat: extract spine metadata through hosted VLM`
- **Explicit Things NOT to Build**: Do not build mobile UI screens yet.

---

## PHASE 5 — BACKEND API VERTICAL SLICE & MINIMAL PERSISTENCE
- **Objective**: Assemble Django ORM minimal model (`LibraryBook`), serializers, REST API endpoints (`POST /api/analyze/`, `POST /api/match/`, `GET /api/library/`, `POST /api/library/`), and transient scan orchestration.
- **Responsible Agent**: Architecture / Backend Agent
- **Files Expected to Change**:
  - `backend/shelfie/models.py` [MODIFY]
  - `backend/shelfie/serializers.py` [NEW]
  - `backend/shelfie/views.py` [MODIFY]
  - `backend/shelfie/urls.py` [MODIFY]
  - `backend/shelfie/tests/test_api.py` [NEW]
- **Tasks**:
  1. Define minimal `LibraryBook` model (`catalog_id`, `confirmed_title`, `confirmed_author`, `confirmed_at`). Run migrations.
  2. Build `POST /api/analyze/` view orchestrating Detector $\rightarrow$ VLM $\rightarrow$ Matcher pipeline. Return 5 granular item states.
  3. Build `POST /api/match/` view for optional review match reruns.
  4. Build `GET /api/library/` and `POST /api/library/` (supporting batch submission).
- **Tests**:
  - `pytest backend/shelfie/tests/test_api.py` (End-to-end REST API integration tests).
- **Manual Verification**:
  - Post bookshelf image to `/api/analyze/` via Postman/cURL; verify response array with 5 granular item states and transient payload.
- **Acceptance Gate**: End-to-end API pipeline executes cleanly from image upload to candidate matching and library persistence.
- **Suggested Commit**: `feat: build scan pipeline API and library persistence`
- **Explicit Things NOT to Build**: Do not create `ScanSession` or `ScanItem` ORM models.

---

## PHASE 6 — MOBILE PRODUCT & 5-STATE HUMAN-IN-THE-LOOP REVIEW
- **Objective**: Build clean Expo mobile UI incorporating Scan, Processing progress overlay, 5-State Results/Review screen, and Personal Library view.
- **Responsible Agent**: Product / UX Agent & Mobile Agent
- **Files Expected to Change**:
  - `mobile/src/screens/*` [NEW]
  - `mobile/src/components/*` [NEW]
  - `mobile/src/services/api.ts` [NEW]
  - `mobile/App.tsx` [MODIFY]
- **Tasks**:
  1. Build `LibraryScreen` displaying saved library books with empty state.
  2. Build `ScanScreen` integrating Expo camera capture and photo picker.
  3. Build `ProcessingScreen` overlay with step progress tracking.
  4. Build `ReviewScreen` displaying items grouped into 5 explicit states (`matched`, `needs_review`, `unmatched`, `unreadable`, `extraction_failed`).
  5. Connect API client to Django backend (`POST /api/analyze/`, `POST /api/library/`).
- **Tests**:
  - Mobile TypeScript compilation check (`npx tsc --noEmit`).
- **Manual Verification**:
  - Run app on Expo simulator/device. Complete user journey: Capture photo $\rightarrow$ Process $\rightarrow$ Review items across states $\rightarrow$ Save confirmed books $\rightarrow$ View in Library.
- **Acceptance Gate**: Mobile user journey is 100% functional, responsive, and handles all 5 UI states cleanly.
- **Suggested Commit**: `feat: connect scan pipeline to review workflow`
- **Explicit Things NOT to Build**: No custom animations, dark mode toggles, or social sharing screens.

---

## PHASE 7 — ADVERSARIAL QA, FAILURE HARDENING & BENCHMARKING
- **Objective**: Attack system assumptions, test adversarial edge cases, measure exact empirical latency/cost numbers on real test photos, and populate benchmark tables in `docs/BUILD_STATE.md` and `README.md`.
- **Responsible Agent**: QA / Adversarial Agent
- **Files Expected to Change**:
  - `backend/shelfie/tests/test_adversarial.py` [NEW]
  - `docs/BUILD_STATE.md` [MODIFY]
  - `docs/test_photos/` [NEW]
- **Tasks**:
  1. Collect real test bookshelf photographs (committed to `docs/test_photos/`).
  2. Execute adversarial test suite covering:
     - Zero books in image (blank wall)
     - Degraded / blurry photo
     - VLM timeout / invalid API key simulation (verifying transition to `extraction_failed`, not `unreadable`)
     - Malformed VLM output handling
  3. Measure exact empirical latency (detection ms, VLM ms, matcher ms) and API cost per scan; update `docs/BUILD_STATE.md` and `README.md` (replacing `TBD` markers).
- **Tests**:
  - `pytest backend/shelfie/tests/` (Full test suite passing).
- **Manual Verification**:
  - Disconnect API key / simulate network error; confirm mobile app transitions crops to `extraction_failed` without crashing.
- **Acceptance Gate**: All adversarial tests pass; zero unhandled crashes; empirical benchmark tables populated.
- **Suggested Commit**: `test: harden inference failure paths and record latency benchmarks`
- **Explicit Things NOT to Build**: Do not rewrite core architecture during QA.

---

## PHASE 8 — RELEASE, DOCUMENTATION & PRESENTATION PREPARATION
- **Objective**: Create clean-clone README setup guide, honest `AI_USAGE.md`, final audit of commit history, and presentation rehearsal.
- **Responsible Agent**: Release Agent & Orchestrator
- **Files Expected to Change**:
  - `README.md` [MODIFY]
  - `AI_USAGE.md` [NEW]
  - `docs/BUILD_STATE.md` [MODIFY]
- **Tasks**:
  1. Write detailed `README.md` containing: clean-clone setup instructions, architecture overview, measured latency & cost numbers, catalog methodology, key decisions/tradeoffs, AGPL-3.0 license note, and unfinished work notes.
  2. Write honest `AI_USAGE.md` detailing AI coding tools used and specific areas of leverage.
  3. Execute clean clone verification test in isolated directory.
  4. Perform final git commit audit and freeze repository.
- **Tests**:
  - Clean clone automated setup test.
- **Manual Verification**:
  - Perform 30-minute live presentation dry run (10 min demo, 10 min architecture Q&A, 10 min live code mod simulation).
- **Acceptance Gate**: Project setup works flawlessly on clean machine from README instructions.
- **Suggested Commit**: `docs: add benchmarks architecture and setup`

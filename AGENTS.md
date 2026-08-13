# AGENTS.md — SHELFIE OPERATIONAL CONSTITUTION & MULTI-AGENT GOVERNANCE

## 1. SOURCE-OF-TRUTH HIERARCHY

All agents operating in this repository must adhere strictly to the following authority hierarchy:

1. **`docs/source/Shelfie-Take-Home-Task.pdf`**: Absolute highest authority. Any conflict between generated documentation/code and the PDF assignment is resolved in favor of the PDF assignment.
2. **`AGENTS.md` (This document)**: Operational governance, agent boundaries, security, and repository policies.
3. **Planning & Architecture Artifacts (`docs/*.md`)**: System design, product specifications, technology choices, and execution plans.
4. **Implementation Code & Tests**: Derived artifacts enforcing the specs.

*Rule: Agents MUST NOT silently invent or alter requirements. Distinguish explicitly between REQUIRED, CHOSEN DESIGN, ASSUMPTION, DEFERRED, and OUT OF SCOPE.*

---

## 2. MULTI-AGENT ROLES & RESPONSIBILITIES

| Agent Role | Scope & Responsibilities | Key File Ownership / Boundaries |
| :--- | :--- | :--- |
| **Principal / Orchestrator** | Final decision authority, cross-agent coordination, phase-gate enforcement, shared configuration approval. | Governance docs (`AGENTS.md`, `docs/*`), root files (`README.md`, `AI_USAGE.md`) |
| **Requirements Agent** | Requirement extraction, assignment compliance, verification against PDF spec. | `docs/PRD.md`, compliance matrices |
| **Product / UX Agent** | Mobile app flow design, human-in-the-loop review UI, error/empty states, user experience polish. | `docs/DESIGN.md`, `mobile/src/screens/**`, `mobile/src/components/**` |
| **Architecture Agent** | End-to-end system context, API contracts, data models, error formats, boundaries. | `docs/ARCHITECTURE.md`, `backend/shelfie/models.py`, `backend/shelfie/urls.py`, `backend/shelfie/views.py` |
| **Computer Vision Agent** | Local object detection service (YOLO26n candidate), dynamic class lookup, CPU inference strategy, crop generation. | `backend/shelfie/services/detector.py`, `backend/shelfie/services/image_utils.py` |
| **VLM Agent** | Hosted vision-language integration (OpenRouter `google/gemini-2.5-flash`), structured JSON extraction, configurable batching. | `backend/shelfie/services/vlm.py` |
| **Data / Matching Agent** | Canonical catalog construction (`catalog.csv`), deterministic RapidFuzz matching engine, provisional scoring thresholds. | `catalog.csv`, `backend/shelfie/services/matcher.py`, `backend/shelfie/tests/test_matcher.py` |
| **QA / Adversarial Agent** | Edge-case test suites, failure simulation, reliability validation, latency/cost verification. | `backend/shelfie/tests/**`, `docs/BUILD_STATE.md` validation tables |
| **Release Agent** | Clean-clone setup verification, README presentation preparation, commit history audit, delivery packaging. | `README.md`, `AI_USAGE.md`, `.env.example` |

---

## 3. STRICT FILE OWNERSHIP MATRIX & SHARED-FILE RESTRICTIONS

### 3.1 Ownership Matrix

* **CV Domain**: `backend/shelfie/services/detector.py`, `backend/shelfie/services/image_utils.py`
* **VLM & Matching Domain**: `backend/shelfie/services/vlm.py`, `backend/shelfie/services/matcher.py`, `catalog.csv`
* **Backend Core Domain**: `backend/shelfie/models.py`, `backend/shelfie/serializers.py`, `backend/shelfie/views.py`, `backend/shelfie/urls.py`, `backend/manage.py`
* **Mobile Domain**: `mobile/**`
* **QA Domain**: `backend/shelfie/tests/**`
* **Governance & Delivery**: `AGENTS.md`, `docs/**`, `README.md`, `AI_USAGE.md`, `.env.example`, `.gitignore`

### 3.2 Shared-File Controls
Modifications to shared configuration files (`backend/config/settings.py`, `mobile/app.json`, `package.json`, `pyproject.toml` / `requirements.txt`, root `.env.example`, `.gitignore`) **MUST** be proposed to and applied via the Principal / Orchestrator agent to prevent race conditions and conflicting dependencies.

---

## 4. IMPLEMENTATION & ARCHITECTURAL RULES

1. **No Fine-Tuning / No Training**: Off-the-shelf pretrained models only (YOLO26n candidate, hosted Gemini 2.5 Flash).
2. **Dynamic Class Lookup**: Never hard-code numeric class IDs (e.g., COCO `book` is class 73 in Ultralytics, but must be looked up dynamically via `model.names`).
3. **Separation of Concerns**:
   - Detector identifies **WHERE** books are (bounding box crop coordinates).
   - VLM transcribes **WHAT** text is visible on each crop (`crop_id`, `title`, `author`, `readability`).
   - Matcher decides **WHICH** canonical catalog entry corresponds to the transcription.
   - Human decides **WHAT** to do with low-confidence / unreadable / unmatched items.
   - Database persists **CONFIRMED** items only (`LibraryBook`).
   - *Never allow VLM self-reported certainty to replace deterministic catalog matching.*
4. **Distinct Product & Failure States**: Explicitly represent `matched`, `needs_review`, `unmatched`, `unreadable`, and `extraction_failed`. Never obscure timeouts or provider errors as `unreadable`.
5. **Graceful Failure & Partial Success**: A failure on a single crop or VLM timeout must never crash the scan or the app. Process readable items and route failed items gracefully.
6. **Simplified Persistence**: Keep `catalog.csv` file-backed; load into an in-memory index for matching. Keep scan/review state transient. Persist only confirmed books in SQLite (`LibraryBook`).
7. **License Transparency**: Note that YOLO26 is AGPL-3.0 licensed; this is an explicit take-home/portfolio tradeoff. Proprietary production would require separate license review or a permissive alternative.
8. **Measured Metrics Only**: Do not invent performance or cost numbers. Mark unmeasured values as `TBD — measured during benchmark phase`.

---

## 5. SECURITY & ENVIRONMENT RULES

1. **Zero Secret Leakage**: NEVER write API keys, tokens, or credentials into source code, config files, tests, documentation, commit messages, screenshots, or AI logs.
2. **Git Ignore Rules**: `.env` and `docs/source/` (including the PDF assignment) MUST be listed in `.gitignore` and kept local.
3. **Environment Variables Only**: All keys (e.g., `OPENROUTER_API_KEY`) must be loaded from system environment or `.env` file. Provide placeholders only in `.env.example`.

---

## 6. GIT & COMMIT STRATEGY

1. **Incremental & Meaningful**: Commits must represent complete, working, testable vertical milestones (tied to Phase Gates).
2. **No Monolithic Uploads**: Single-commit repositories count heavily against evaluation.
3. **Post-Submission Freeze**: Once submitted/sent to evaluators, stop committing immediately. Any commit after the deadline will penalize the submission.
4. **Commit Message Standard**: Use conventional format: `feat: ...`, `test: ...`, `docs: ...`, `chore: ...`, `refactor: ...`.

---

## 7. PHASE-GATE & SCOPE CONTROL RULES

1. **Strict Phase Gating**: Do not start Phase $N+1$ until all acceptance criteria and tests for Phase $N$ are satisfied and recorded in `docs/BUILD_STATE.md`.
2. **Isolated Dependency Addition**: Add dependencies strictly in the phase where they are required (Phase 1: Django/Expo foundation only; Phase 2: RapidFuzz; Phase 3: CV models; Phase 4: VLM HTTP client).
3. **Prohibited Scope**:
   - NO user authentication / registration.
   - NO multi-tenant databases / user profiles / ScanSession ORM models.
   - NO deployment infrastructure (Docker/K8s/AWS/Cloud hosting).
   - NO social features / sharing / book reviews.
   - NO complex administrative dashboards or unnecessary UI animations.
4. **Eight-Hour Budget Discipline**: Focus entirely on a solid, defendable, working core slice over feature breadth.

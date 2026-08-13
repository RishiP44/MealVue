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
  - AI tools assisted with generating an initial candidate set of 125 commonly owned books and deliberate ambiguity cases (multi-editions, US/UK alternate titles, shared titles across different authors, omnibus vs single volumes, substring collisions, and author aliases). Entries were structurally formatted via `csv.writer` and validated.
  - Catalog loader and validator service implementation (`backend/shelfie/services/catalog.py`).
  - Text and author normalization module development (`normalize_title`, `normalize_author`).
  - Deterministic RapidFuzz matcher service implementation with ambiguity margin scoring and author/title conflict safeguards (`backend/shelfie/services/matcher.py`).
  - Phase 2.1 quality corrections: Corrected coauthor attributions (`Andrew Hunt and David Thomas`, `Erich Gamma et al.`, `CLRS`), title correction (*Island* by Aldous Huxley), removed historical slur from alternate titles, audited `work_id` consistency, separated `match_score` from decision `confidence` heuristic, penalized ties to low decision confidence (0.5000), and added wrong-author and adversarial substring test cases.
  - Unit test suite creation in `backend/shelfie/tests/test_matcher.py` (22 tests covering all catalog ambiguity categories, invariants, and adversarial edge cases).
  - Matcher benchmarking script development (`backend/shelfie/scripts/benchmark_matcher.py`) and empirical latency measurement.

---

## Developer Oversight & Code Attribution Statement

All AI-generated scaffolding, catalog entries, architectural planning documents, and code implementations were reviewed, tested, and validated by the engineer. Every line in the repository is understood, defendable, and ready for live presentation and modification.

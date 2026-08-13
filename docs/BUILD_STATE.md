# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 0.1 — Architecture Correction & Scope Hardening
- **Phase Status**: `COMPLETED (AWAITING HUMAN APPROVAL)`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 1` before creating codebase, installing dependencies, or making implementation commits.
- **Phase 0.1 Deliverables Updated**:
  - `AGENTS.md` — Governance, dynamic class lookup, license transparency, secret protection
  - `docs/PRD.md` — Product requirements, 5 granular failure states, minimal persistence, API surface
  - `docs/ARCHITECTURE.md` — End-to-end architecture, development-time benchmarking, REST API, DB model
  - `docs/DESIGN.md` — Mobile UI spec, 5 UI review states, design system tokens
  - `docs/TECH_RULES.md` — Technical standards, dynamic label lookup rule, phased dependency isolation
  - `docs/EXECUTION_PLAN.md` — 8 gated phases, Phase 1 foundation scope isolation, acceptance criteria
  - `docs/BUILD_STATE.md` — (This document) Living implementation ledger

---

## 2. ARCHITECTURE DECISIONS SUMMARY

| ADR ID | Decision Summary | Rationale / Tradeoff |
| :--- | :--- | :--- |
| **ADR-01** | Local CPU Detector Candidate (YOLO26n) with Dynamic Lookup | Development-time benchmarking workflow. Dynamic `model.names` lookup for `book` (class 73 in COCO). AGPL-3.0 portfolio tradeoff. |
| **ADR-02** | Hosted VLM via OpenRouter (`google/gemini-2.5-flash`) | Configurable `VLM_BATCH_SIZE` with stable `crop_id`. Decouples VLM text legibility from catalog match confidence. |
| **ADR-03** | RapidFuzz Catalog Matcher + Provisional Thresholds | Matches against in-memory index of file-backed `catalog.csv`. Thresholds calibrated in Phase 2 against catalog edge cases. |
| **ADR-04** | 5 Granular Product & Failure States | Explicitly separates `matched`, `needs_review`, `unmatched`, `unreadable`, and `extraction_failed`. Network/VLM timeouts $\rightarrow$ `extraction_failed`. |
| **ADR-05** | Simplified Persistence Strategy | `catalog.csv` is file-backed. Scan/review state is transient. SQLite persists confirmed books only (`LibraryBook` ORM model). |
| **ADR-06** | Minimal REST API Surface | `POST /api/analyze/`, `POST /api/match/`, `GET /api/library/`, `POST /api/library/`. |

---

## 3. LATENCY & PERFORMANCE BENCHMARK LEDGER

*Note: All benchmark numbers are marked as `TBD — measured during benchmark phase`. Target budgets vs measured results are explicitly distinguished below.*

### Performance Budgets (Target Goals)
- **Target CPU Spine Inference Latency**: $< 1.5$ seconds
- **Target Hosted VLM Latency**: $< 3.0$ seconds
- **Target Total Roundtrip Latency**: $< 6.0$ seconds
- **Target Per-Scan API Cost**: $< \$0.005$ USD

### Measured Empirical Results (Populated in Phase 7)

| Test Image ID | Image Resolution | CPU Spine Detect (ms) | Crop & Prep (ms) | Hosted VLM (ms) | RapidFuzz Match (ms) | Total Pipeline (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *photo_01.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD |
| *photo_02.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD |
| *photo_03.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD |
| *photo_04.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD |

---

## 4. API COST LEDGER

*Note: API costs will be dynamically computed and recorded during live scan executions in Phase 4 and Phase 7.*

| Scan Run ID | Crops Sent | VLM Model | Input Tokens | Output Tokens | Total Cost (USD) | Cost / Book |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *scan_test_01* | *Pending Phase 7* | `gemini-2.5-flash` | TBD | TBD | TBD | TBD |
| *scan_test_02* | *Pending Phase 7* | `gemini-2.5-flash` | TBD | TBD | TBD | TBD |
| *scan_test_03* | *Pending Phase 7* | `gemini-2.5-flash` | TBD | TBD | TBD | TBD |

---

## 5. TEST PHOTOGRAPH ACCURACY LEDGER

| Photo Name | Books Visible | Spines Detected | VLM Read OK | Matched High Conf | Needs Review | Unmatched / Error | End-to-End Precision |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *shelf_dense_1.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD | TBD |
| *shelf_angled_2.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD | TBD |
| *shelf_worn_3.jpg* | *Pending Phase 7* | TBD | TBD | TBD | TBD | TBD | TBD |

---

## 6. RISKS & UNRESOLVED QUESTIONS

1. **COCO Spine Separation (CV Risk)**:
   - *Risk*: Closed-set COCO detector candidate may merge adjacent vertical book spines.
   - *Mitigation Plan*: Benchmark YOLO26n on real test photos in Phase 3. If recall is inadequate, evaluate YOLO26s or time-boxed `IDEA-Research/grounding-dino-tiny`. Select ONE final detector.
2. **OpenRouter Rate Limits & Timeout Handling**:
   - *Risk*: VLM HTTP requests may time out or fail.
   - *Mitigation Plan*: Set strict 10s timeout in `httpx`. Map provider timeouts explicitly to `extraction_failed` state (not `unreadable`), allowing user to retry crop or tag manually.
3. **Ambiguity Margin Calibration**:
   - *Risk*: Initial scoring thresholds ($S_1 \ge 0.82$, $\Delta \ge 0.15$) are provisional hypotheses.
   - *Mitigation Plan*: Calibrate thresholds against `test_matcher.py` test suite in Phase 2 across the 6 mandatory catalog ambiguity patterns.

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- User authentication & registration (Single local user mode).
- Cloud deployment & hosting (Runs locally via Expo & Django `manage.py`).
- Third-party book APIs (Google Books / Goodreads live integration).
- Custom model training / fine-tuning (Strict off-the-shelf weights).
- ORM persistence for catalog and transient scan sessions (`catalog.csv` file-backed, transient scan state, `LibraryBook` SQLite model only).
- Automatic runtime model switching (Single detector selected at development time).
- Social sharing, reading tracking, or public user profiles.

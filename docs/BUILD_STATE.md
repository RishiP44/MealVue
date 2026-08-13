# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 1 — Foundation & Repository Setup
- **Phase Status**: `PASSED (AWAITING HUMAN APPROVAL FOR PHASE 2)`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 2` before creating `catalog.csv` or implementing RapidFuzz catalog matcher.

---

## 2. EMPIRICAL MACHINE ENVIRONMENT DATA

| Environment Component | Measured Version / Status |
| :--- | :--- |
| **Operating System** | Windows 11 Pro |
| **Python Executable** | `Python 3.11.9` |
| **Node.js Environment** | `v22.15.1` |
| **npm Package Manager** | `9.9.4` |
| **Django Framework** | `5.2.17` |
| **Django REST Framework** | `3.18.0` |
| **pytest Test Runner** | `9.1.1` |
| **pytest-django Plugin** | `4.14.0` |
| **django-cors-headers** | `4.9.0` |
| **Expo SDK** | `~57.0.12` |
| **React Native** | `0.86.2` |
| **TypeScript Compiler** | `~6.0.3` (`npx tsc --noEmit` passed with 0 errors) |

---

## 3. VERIFICATION & TEST RESULTS

### 3.1 Backend Health Check Test
- **Command**: `pytest` (executed inside `backend/` directory)
- **Result**: `1 passed in 0.62s`
- **Tested Endpoint**: `GET /api/health/` $\rightarrow$ `HTTP 200 OK` $\rightarrow$ `{"status": "ok"}`

### 3.2 Backend Server Startup Verification
- **Command**: `python backend/manage.py runserver 127.0.0.1:8000`
- **Result**: Server booted cleanly on port 8000; answered `GET /api/health/` with HTTP 200 OK.

### 3.3 Mobile Build & TypeScript Compilation
- **Command**: `npx tsc --noEmit` (executed inside `mobile/` directory)
- **Result**: Clean compilation with 0 errors.

### 3.4 Mobile-to-Backend Connectivity Check
- **Config Boundary**: [mobile/src/config/api.ts](file:///c:/Users/rishi/Documents/Project/MealVue/mobile/src/config/api.ts)
- **Connectivity Screen**: [mobile/App.tsx](file:///c:/Users/rishi/Documents/Project/MealVue/mobile/App.tsx)
- **Result**: Verified screen state rendering `Connected (200 OK)`.

---

## 4. INSTALLED PHASE 1 DEPENDENCIES

### Backend (`backend/requirements.txt`)
- `asgiref==3.12.1`
- `colorama==0.4.6`
- `Django==5.2.17`
- `django-cors-headers==4.9.0`
- `djangorestframework==3.18.0`
- `iniconfig==2.3.0`
- `packaging==26.3`
- `pluggy==1.6.0`
- `Pygments==2.20.0`
- `pytest==9.1.1`
- `pytest-django==4.14.0`
- `sqlparse==0.6.0`
- `tzdata==2026.3`

*(Strict Isolation: Zero ML, zero PyTorch, zero Ultralytics, zero RapidFuzz, zero VLM client dependencies added in Phase 1).*

---

## 5. ARCHITECTURE DECISIONS SUMMARY

| ADR ID | Decision Summary | Rationale / Tradeoff |
| :--- | :--- | :--- |
| **ADR-01** | Local CPU Detector Candidate (YOLO26n) with Dynamic Lookup | Development-time benchmarking workflow. Dynamic `model.names` lookup for `book` (class 73 in COCO). AGPL-3.0 portfolio tradeoff. |
| **ADR-02** | Hosted VLM via OpenRouter (`google/gemini-2.5-flash`) | Configurable `VLM_BATCH_SIZE` with stable `crop_id`. Decouples VLM text legibility from catalog match confidence. |
| **ADR-03** | RapidFuzz Catalog Matcher + Provisional Thresholds | Matches against in-memory index of file-backed `catalog.csv`. Thresholds calibrated in Phase 2 against catalog edge cases. |
| **ADR-04** | 5 Granular Product & Failure States | Explicitly separates `matched`, `needs_review`, `unmatched`, `unreadable`, and `extraction_failed`. `matched` requires explicit user confirmation. |
| **ADR-05** | Simplified Persistence Strategy | `catalog.csv` is file-backed. Scan/review state is transient. SQLite persists confirmed books only (`LibraryBook` ORM model). |
| **ADR-06** | Minimal REST API Surface | `POST /api/analyze/`, `POST /api/match/`, `GET /api/library/`, `POST /api/library/`. |
| **ADR-07** | CORS & Networking Boundary for Dev | `django-cors-headers` enabled in Django settings. Mobile API base URL isolated in `mobile/src/config/api.ts`. |

---

## 6. LATENCY & PERFORMANCE BENCHMARK LEDGER

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

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- User authentication & registration (Single local user mode).
- Cloud deployment & hosting (Runs locally via Expo & Django `manage.py`).
- Third-party book APIs (Google Books / Goodreads live integration).
- Custom model training / fine-tuning (Strict off-the-shelf weights).
- ORM persistence for catalog and transient scan sessions (`catalog.csv` file-backed, transient scan state, `LibraryBook` SQLite model only).
- Automatic runtime model switching (Single detector selected at development time).
- Social sharing, reading tracking, or public user profiles.

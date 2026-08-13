# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 2.1 — Match Confidence & Catalog Quality Audit
- **Phase Status**: `PASSED (AWAITING HUMAN APPROVAL FOR PHASE 3)`
- **Next Approved Action**: Await explicit human command `APPROVE PHASE 3` before installing Ultralytics/PyTorch or implementing local computer vision spine detection.

---

## 2. EMPIRICAL MACHINE ENVIRONMENT DATA & DEPENDENCIES

| Environment Component | Measured Version / Status |
| :--- | :--- |
| **Operating System** | Windows 11 Pro |
| **Python Executable** | `Python 3.11.9` |
| **RapidFuzz Matching Engine** | `3.14.5` (C++ accelerated fuzzy string matching) |
| **Django Framework** | `5.2.17` |
| **Django REST Framework** | `3.18.0` |
| **pytest Test Runner** | `9.1.1` |
| **pytest-django Plugin** | `4.14.0` |
| **Node.js / Expo** | `v22.15.1` / `~57.0.12` |

---

## 3. CANONICAL CATALOG SPECIFICATION (`catalog.csv`)

- **Location**: [`catalog.csv`](file:///c:/Users/rishi/Documents/Project\MealVue/catalog.csv)
- **Total Valid Entries**: 125 canonical book records
- **Schema Columns**: `catalog_id`, `work_id`, `title`, `author`, `alternate_titles`, `author_aliases`, `edition`, `publication_year`
- **Bibliographic Quality Fixes**: Corrected Aldous Huxley's novel title to *Island*; removed historical slur from alternate titles; corrected coauthor attributions (`Andrew Hunt and David Thomas`, `Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides`, `Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein`, `Harold Abelson and Gerald Jay Sussman`, `Brian Herbert and Kevin J. Anderson`, `Jim Collins and Jerry I. Porras`, `Steven D. Levitt and Stephen J. Dubner`); enforced `work_id` consistency across editions.

---

## 4. DETERMINISTIC MATCHING ALGORITHM & CONFIDENCE SEMANTICS

### 4.1 Match Score vs Decision Confidence Separation
- `match_score`: Similarity strength of top candidate ($S_1$, composite of $0.70 \times S_{title} + 0.30 \times S_{author}$).
- `runner_up_score`: Similarity strength of second candidate ($S_2$).
- `margin`: Separation $\Delta = S_1 - S_2$.
- `confidence`: Decision confidence heuristic bounded in $[0, 1]$:
  $$\text{confidence} = S_1 \times \left(0.50 + 0.50 \times \min\left(1.0, \frac{\Delta}{\text{MIN\_MARGIN}}\right)\right)$$
- An exact tie ($S_1=1.0, S_2=1.0, \Delta=0.0$) yields $\text{confidence} = 0.5000$ (low decision confidence) and routes to `needs_review`.

### 4.2 Thresholds (Heuristically Tuned Against Phase 2 Test Matrix)
- `MATCH_THRESHOLD = 0.80`: Minimum top `match_score` for direct addition candidate.
- `REVIEW_THRESHOLD = 0.45`: Minimum top `match_score` for human review suggestion.
- `MIN_MARGIN = 0.12`: Minimum separation $\Delta = S_1 - S_2$ between top candidate and runner-up.

---

## 5. VERIFICATION, TESTS & EMPIRICAL BENCHMARK

### 5.1 Test Suite Results
- **Command**: `pytest` (executed inside `backend/`)
- **Result**: `22 passed in 0.77s` ([test_matcher.py](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/tests/test_matcher.py) + `test_health.py`)
- **Test Matrix**: Covered catalog `work_id` consistency, mandatory ambiguity categories, normalization, exact/typo matching, author aliases, `Lastname, Firstname` parsing, shared titles with distinct authors, omnibus vs single volumes, adversarial substring collisions (`Dune Messiah`, `Foundation Empire`, `Clean Coder`), wrong-author guards (`1984` by Huxley, `Inferno` by Asimov), confidence semantics, tie penalties, and order invariance.

### 5.2 Deterministic Matcher Latency Benchmark
- **Benchmark Script**: [benchmark_matcher.py](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/scripts/benchmark_matcher.py)
- **Total Repeated Matcher Calls**: 999 calls across 9 representative test query types
- **Catalog Size**: 125 entries
- **Total Elapsed Time**: `5.6478 seconds`
- **Measured Average Latency**: **`5.6535 ms` per call**
- **Measured Throughput**: **`176.88` calls / second**

---

## 6. REPRESENTATIVE MATCHER TEST RESULTS (9 REQUESTED CASES)

| Query Title | Query Author | Winner Catalog ID & Title | match_score | runner_up | margin | confidence | Result State |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *Designing Data-Intensive Applications* | *Martin Kleppmann* | `BK0059` — Designing Data-Intensive Applications | 1.0000 | 0.4500 | 0.5500 | **1.0000** | **`matched`** |
| *Sapens: Brief History* | *Yuval N Harari* | `BK0063` — Sapiens | 0.8165 | 0.7385 | 0.0780 | **0.6736** | **`needs_review`** |
| *The Golden Compass* | *Philip Pullman* | `BK0012` — Northern Lights | 1.0000 | 1.0000 | 0.0000 | **0.5000** | **`needs_review`** |
| *1984* | *Eric Arthur Blair* | `BK0041` — 1984 | 1.0000 | 0.3000 | 0.7000 | **1.0000** | **`matched`** |
| *Island* | *Aldous Huxley* | `BK0027` — Island | 1.0000 | 0.4863 | 0.5137 | **1.0000** | **`matched`** |
| *Dune Messiah* | *Frank Herbert* | `BK0017` — Dune Messiah | 1.0000 | 0.8250 | 0.1750 | **1.0000** | **`matched`** |
| *The Hobbit* | *J. R. R. Tolkien* | `BK0001` — The Hobbit | 1.0000 | 1.0000 | 0.0000 | **0.5000** | **`needs_review`** |
| *Quantum Mechanical Superconductivity* | *Unknown* | N/A | 0.3855 | 0.3746 | 0.0109 | **0.2103** | **`unmatched`** |
| *1984* | *Aldous Huxley* | `BK0041` — 1984 | 0.4500 | 0.3000 | 0.1500 | **0.4500** | **`needs_review`** |

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Local CV Spine Detection (Phase 3).
- Hosted VLM OpenRouter OCR integration (Phase 4).
- Database ORM persistence for catalog/scan sessions (Only `LibraryBook` persisted in SQLite in Phase 5).
- REST API endpoint integration for matcher (`POST /api/analyze/` in Phase 5).

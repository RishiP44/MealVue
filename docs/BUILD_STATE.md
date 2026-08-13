# LIVING IMPLEMENTATION LEDGER — SHELFIE

## 1. CURRENT EXECUTIVE STATUS

- **Current Phase**: Phase 2 — Messy Catalog & Deterministic Matching Engine
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

- **Location**: [`catalog.csv`](file:///c:/Users/rishi/Documents/Project/MealVue/catalog.csv)
- **Total Valid Entries**: 125 canonical book records
- **Schema Columns**: `catalog_id`, `work_id`, `title`, `author`, `alternate_titles`, `author_aliases`, `edition`, `publication_year`
- **Delimiters**: Pipe (`|`) for multiple alternate titles/aliases; CSV RFC-4180 standard quotes.
- **Alternate Title Count**: 14 entries with alternate titles
- **Author Alias Count**: 48 entries with author aliases

### Representative Ambiguity Edge Cases In Catalog
1. **Category A (Multi-editions)**:
   - `BK0001` (*The Hobbit*, Paperback UK) vs `BK0002` (*The Hobbit*, 75th Anniversary Edition)
   - `BK0023` (*Clean Code*, 1st Ed) vs `BK0024` (*Clean Code*, Special Collector Ed)
   - `BK0052` (*The Pragmatic Programmer*, 1st Ed) vs `BK0053` (20th Anniversary Ed)
2. **Category B (Alternate Published Titles)**:
   - `BK0007` (*Harry Potter and the Philosopher's Stone*, alt: *Harry Potter and the Sorcerer's Stone*)
   - `BK0012` (*Northern Lights*, alt: *The Golden Compass*)
   - `BK0014` (*And Then There Were None*, alt: *Ten Little Indians*)
3. **Category C (Same Title, Different Authors)**:
   - `BK0027` (*The Island* by Aldous Huxley) vs `BK0028` (*The Island* by Victoria Hislop) vs `BK0029` (*The Island* by Peter Benchley)
   - `BK0030` (*Nemesis* by Isaac Asimov) vs `BK0031` (*Nemesis* by Agatha Christie) vs `BK0032` (*Nemesis* by Philip Roth)
   - `BK0033` (*Inferno* by Dante Alighieri) vs `BK0034` (*Inferno* by Dan Brown)
4. **Category D (Omnibus vs Individual Volumes)**:
   - `BK0006` (*The Lord of the Rings Omnibus*) vs `BK0003` (*The Fellowship of the Ring*)
   - `BK0022` (*The Foundation Trilogy Omnibus*) vs `BK0019` (*Foundation*)
   - `BK0094` (*A Song of Ice and Fire: Books 1-3*) vs `BK0091` (*A Game of Thrones*)
5. **Category E (Substring Collisions)**:
   - `BK0015` (*Dune*) vs `BK0017` (*Dune Messiah*) vs `BK0018` (*Dune House Atreides*)
   - `BK0019` (*Foundation*) vs `BK0020` (*Foundation and Empire*)
   - `BK0023` (*Clean Code*) vs `BK0025` (*The Clean Coder*) vs `BK0026` (*Clean Architecture*)
6. **Category F (Author Variants & Aliases)**:
   - `J. R. R. Tolkien` $\leftrightarrow$ `J.R.R. Tolkien` $\leftrightarrow$ `John Ronald Reuel Tolkien` $\leftrightarrow$ `Tolkien, J. R. R.`
   - `George Orwell` $\leftrightarrow$ `Eric Arthur Blair`
   - `Robert C. Martin` $\leftrightarrow$ `Uncle Bob` $\leftrightarrow` `Martin, Robert C.`

---

## 4. DETERMINISTIC MATCHING ALGORITHM & THRESHOLDS

### 4.1 Normalization Strategy
- `normalize_title()`: Strips diacritics/accents via Unicode NFKD, lowercases, replaces `&` with `and`, retains alphanumeric and spaces only, collapses repeated whitespace.
- `normalize_author()`: Strips accents, lowercases, converts `Lastname, Firstname` to `Firstname Lastname`, removes dots in initials (`J. R. R.` $\rightarrow$ `j r r`), collapses whitespace.

### 4.2 Scoring Formula & Substring Safeguards
- Title similarity ($S_{title}$): Evaluates input against canonical title and all alternate titles using $0.65 \times \text{token\_set\_ratio} + 0.35 \times \text{token\_sort\_ratio}$. The `token_sort_ratio` component penalizes extra word length mismatches, preventing raw substring inflation (`"Dune"` vs `"Dune Messiah"`).
- Author similarity ($S_{author}$): Evaluates input against canonical author and all aliases.
- Base Composite Score:
  $$\text{Composite} = (0.70 \times S_{title}) + (0.30 \times S_{author})$$
- Author Conflict Guard: If title score $S_{title} \ge 0.60$ but author score $S_{author} < 0.35$ (meaning author is explicitly wrong/conflicting), composite score is capped at $0.48$.
- Missing Author Modifier: If author is missing, score is $S_{title} \times 0.85$, capped at $0.78$ to force ambiguous titles into review.

### 4.3 Calibrated Thresholds ([matcher.py](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/services/matcher.py#L10-L12))
- `MATCH_THRESHOLD = 0.80`: Minimum top score $S_1$ required for `matched` state.
- `REVIEW_THRESHOLD = 0.45`: Minimum top score $S_1$ required for `needs_review` state.
- `MIN_MARGIN = 0.12`: Minimum separation $\Delta = S_1 - S_2$ between top candidate and runner-up.
- **State Classification Logic**:
  - `matched`: $S_1 \ge 0.80$ AND $\Delta \ge 0.12$
  - `needs_review`: $S_1 \ge 0.45$ (and fails matched criteria)
  - `unmatched`: $S_1 < 0.45$

---

## 5. VERIFICATION, TESTS & EMPIRICAL BENCHMARK

### 5.1 Test Suite Results
- **Command**: `pytest` (executed inside `backend/`)
- **Result**: `27 passed in 0.92s` ([test_matcher.py](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/tests/test_matcher.py) + `test_health.py`)
- **Test Matrix**: Covered exact matches, typos, alternate titles, author aliases, `Lastname, Firstname` parsing, shared titles with distinct authors, omnibus vs single volumes, substring collisions, missing fields, runner-up margin routing, noisy OCR input, and structural invariants.

### 5.2 Deterministic Matcher Latency Benchmark
- **Benchmark Script**: [benchmark_matcher.py](file:///c:/Users/rishi/Documents/Project/MealVue/backend/shelfie/scripts/benchmark_matcher.py)
- **Total Repeated Matcher Calls**: 1,000 calls across 8 representative test query types
- **Catalog Size**: 125 entries
- **Total Elapsed Time**: `5.2447 seconds`
- **Measured Average Latency**: **`5.2447 ms` per call**
- **Measured Throughput**: **`190.67` calls / second**

---

## 6. REPRESENTATIVE MATCHER TEST RESULTS

| Query Title | Query Author | Winner Catalog ID & Title | Score ($S_1$) | Margin ($\Delta$) | Result State |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *Designing Data-Intensive Applications* | *Martin Kleppmann* | `BK0059` — Designing Data-Intensive Applications | 1.0000 | 0.5022 | `matched` |
| *Sapens: Brief History* | *Yuval N Harari* | `BK0063` — Sapiens | 0.8265 | 0.0546 | `needs_review` |
| *The Golden Compass* | *Philip Pullman* | `BK0012` — Northern Lights | 1.0000 | 0.0000 | `needs_review` |
| *1984* | *Eric Arthur Blair* | `BK0041` — 1984 | 1.0000 | 0.7000 | `matched` |
| *The Island* | *Aldous Huxley* | `BK0027` — The Island | 1.0000 | 0.4157 | `matched` |
| *Dune Messiah* | *Frank Herbert* | `BK0017` — Dune Messiah | 1.0000 | 0.1225 | `matched` |
| *The Hobbit* | *J. R. R. Tolkien* | `BK0001` — The Hobbit | 1.0000 | 0.0000 | `needs_review` |
| *Quantum Mechanical Superconductivity* | *Unknown* | N/A | 0.3855 | 0.0109 | `unmatched` |

---

## 7. DEFERRED SCOPE & OUT-OF-SCOPE RECORD

- Local CV Spine Detection (Phase 3).
- Hosted VLM OpenRouter OCR integration (Phase 4).
- Database ORM persistence for catalog/scan sessions (Only `LibraryBook` persisted in SQLite in Phase 5).
- REST API endpoint integration for matcher (`POST /api/analyze/` in Phase 5).

# TECHNICAL RULES & CODING STANDARDS — SHELFIE

## 1. TECH STACK & APPROVED DEPENDENCIES

### 1.1 Language & Framework Versions
- **Python**: `3.11+`
- **Backend Framework**: `Django 5.x` + `Django REST Framework 3.15+`
- **Database**: `SQLite` (Minimal ORM: `LibraryBook` model only)
- **Node.js**: `20.x LTS`
- **Frontend Framework**: `React Native` (via `Expo SDK 51+`)
- **TypeScript**: `5.x+` (Strict mode enabled)

### 1.2 Phased Dependency Addition Philosophy
To keep failures isolated, dependencies MUST be added strictly in the phase where they are first needed:
- **Phase 1 (Foundation)**: `django`, `djangorestframework`, `pytest`, `pytest-django`. (NO ML, NO RapidFuzz, NO VLM client).
- **Phase 2 (Catalog & Matcher)**: `rapidfuzz`.
- **Phase 3 (Local CV Detector)**: `ultralytics`, `pillow`.
- **Phase 4 (Hosted VLM)**: `httpx`.

---

## 2. DIRECTORY CONVENTIONS & FILE OWNERSHIP

### 2.1 Backend Layout (`backend/`)
```text
backend/
├── manage.py
├── config/                  # Django project settings and URLs
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── shelfie/                 # App module
    ├── apps.py
    ├── models.py            # LibraryBook ORM model ONLY (Scan state transient)
    ├── serializers.py       # Serializers for /api/analyze/ and /api/library/
    ├── views.py             # AnalyzeView, MatchView, LibraryView
    ├── urls.py              # Minimal API routing
    ├── services/            # SOLID Service Layer
    │   ├── __init__.py
    │   ├── detector.py      # Dynamic class lookup & CPU spine detector
    │   ├── vlm.py           # OpenRouter VLM client with VLM_BATCH_SIZE
    │   ├── matcher.py       # In-memory catalog.csv RapidFuzz matcher
    │   └── image_utils.py   # Crop extraction with stable crop_id
    └── tests/
        ├── test_matcher.py  # RapidFuzz edge-case tests
        ├── test_detector.py # CV fallback & crop bounding tests
        ├── test_vlm.py      # VLM parsing & error handling tests
        └── test_api.py      # End-to-end REST API tests
```

---

## 3. CORE TECHNICAL & IMPLEMENTATION RULES

### 3.1 Dynamic Label Lookup Rule
Never hard-code numeric class IDs (e.g. COCO class 73 for `book` in Ultralytics). Dynamic resolution is mandatory:
```python
book_class_id = next(
    class_id for class_id, name in model.names.items()
    if name.lower() == "book"
)
```

### 3.2 Model Selection & Licensing
- Primary candidate: `Ultralytics YOLO26n` (CPU inference).
- Development-time benchmarking workflow: Start with YOLO26n $\rightarrow$ test on real bookshelf photos $\rightarrow$ evaluate recall/false-positives/latency $\rightarrow$ try YOLO26s if recall inadequate $\rightarrow$ time-boxed `IDEA-Research/grounding-dino-tiny` if closed-set fails $\rightarrow$ select ONE final model.
- License Note: YOLO26 is AGPL-3.0 licensed. Document this explicit take-home tradeoff.

### 3.3 Decoupling VLM Certainty from Catalog Matching
- `VLM extraction certainty != catalog match confidence`.
- VLM transcribes text (`crop_id`, `title`, `author`, `readability`). Matcher owns catalog match confidence.

### 3.4 Configurable VLM Batch Size & Stable Tracking
- Define configurable setting `VLM_BATCH_SIZE` (initial hypothesis: 5).
- Every crop payload must retain a stable `crop_id` to map VLM output back to detection bounding boxes.

### 3.5 Granular Failure-State Taxonomy
Must explicitly categorize items into 5 distinct states:
1. `matched` (High confidence match)
2. `needs_review` (Ambiguous candidate)
3. `unmatched` (No candidate found)
4. `unreadable` (Illegible physical spine)
5. `extraction_failed` (VLM timeout, network error, or malformed JSON)

*Rule: Never label a network timeout or provider error as `unreadable`.*

---

## 4. SECRET MANAGEMENT & GIT PROTECTION

1. `OPENROUTER_API_KEY` must be read strictly from `os.getenv("OPENROUTER_API_KEY")`.
2. `.gitignore` MUST list `.env` and `docs/source/` (including `Shelfie-Take-Home-Task.pdf`).
3. `.env.example` contains placeholders only (`OPENROUTER_API_KEY=your_key_here`).
4. Zero credentials in code, documentation, logs, tests, or commit history.

---

## 5. PERFORMANCE METRIC REPORTING RULE

- Do not invent performance or cost numbers.
- Mark all unmeasured latency and cost metrics as `TBD — measured during benchmark phase`.
- Distinguish explicitly between **TARGET / BUDGET** (e.g. Total Latency $<6.0\text{s}$, Cost $<\$0.005$) and **MEASURED RESULT** (populated in Phase 7).

# SHELFIE — Bookshelf to Library Inventory

Shelfie is a mobile application and API pipeline that turns a photograph of a bookshelf into a structured, verified personal library inventory.

## Project Status

- **Current Stage**: Phase 2 — Messy Catalog & Deterministic Matching Engine (`PASSED`)
- **Backend Stack**: Python 3.11+, Django 5.2+, Django REST Framework 3.18+, RapidFuzz 3.14+, SQLite
- **Mobile Stack**: React Native, Expo SDK 57+, TypeScript 6+

---

## Clean-Clone Setup Instructions

### 1. Repository & Secrets Protection
- Secrets and private task specification files (`docs/source/`, `.env`) are ignored by Git.
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
2. Install backend dependencies (including RapidFuzz 3.14):
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run backend unit test suite (27 tests passing):
   ```bash
   cd backend
   pytest
   ```
4. Run deterministic catalog matcher benchmark:
   ```bash
   python backend/shelfie/scripts/benchmark_matcher.py
   ```
5. Start the Django development server:
   ```bash
   python backend/manage.py runserver 127.0.0.1:8000
   ```
   Verify health endpoint in browser/cURL:
   `http://127.0.0.1:8000/api/health/` $\rightarrow$ `{"status": "ok"}`

### 3. Mobile Setup
1. Navigate to the mobile directory:
   ```bash
   cd mobile
   ```
2. Install JavaScript dependencies:
   ```bash
   npm install
   ```
3. Verify TypeScript compilation:
   ```bash
   npx tsc --noEmit
   ```
4. Start the Expo development client:
   ```bash
   npx expo start
   ```

---

## Development Networking Configuration

The mobile app configures its backend base URL in [`mobile/src/config/api.ts`](file:///c:/Users/rishi/Documents/Project/MealVue/mobile/src/config/api.ts).

- **Web / iOS Simulator**: Uses `http://127.0.0.1:8000`.
- **Android Emulator**: Set `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`.
- **Physical Device (Expo Go)**: Set `EXPO_PUBLIC_API_URL=http://<YOUR_LOCAL_LAN_IP>:8000` (e.g. `http://192.168.1.50:8000`).

---

## Catalog & Deterministic Matching Methodology

- **Canonical Catalog (`catalog.csv`)**: 125 entries covering popular fiction, classics, sci-fi/fantasy, tech, business, biography, psychology, history, and philosophy.
- **Deliberate Ambiguity Edge Cases**:
  - **Multiple Editions**: *The Hobbit* (UK Paperback vs 75th Anniversary Edition), *Clean Code* (1st Ed vs Special Collector Ed).
  - **Alternate Titles**: *Northern Lights* / *The Golden Compass*, *Harry Potter and the Philosopher's Stone* / *Sorcerer's Stone*.
  - **Same Title, Different Authors**: *The Island* (Aldous Huxley vs Victoria Hislop vs Peter Benchley), *Nemesis* (Isaac Asimov vs Agatha Christie vs Philip Roth).
  - **Omnibus vs Individual Volumes**: *The Lord of the Rings Omnibus* vs *The Fellowship of the Ring*.
  - **Substring Collisions**: *Dune* vs *Dune Messiah* vs *Dune House Atreides*.
  - **Author Representations**: Initials, accents, transliterations, *Lastname, Firstname* ordering, and aliases (*George Orwell* / *Eric Arthur Blair*, *Robert C. Martin* / *Uncle Bob*).
- **Matching Algorithm**: RapidFuzz fuzzy token ratio scoring with custom author conflict caps, missing field modifiers, and calibrated ambiguity margin routing ($S_1 \ge 0.80$, $\Delta \ge 0.12$).

---

## Measured Performance Benchmarks

- **Deterministic Catalog Matcher Latency**: **`5.24 ms` per call** (Measured over 1,000 calls across 125 catalog entries; 190.67 calls/sec throughput)
- **Local CV Latency**: `TBD — measured during benchmark phase` (Phase 3)
- **Hosted VLM Latency**: `TBD — measured during benchmark phase` (Phase 4)
- **Estimated API Cost per Scan**: `TBD — measured during benchmark phase` (Phase 4)

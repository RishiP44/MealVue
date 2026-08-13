# SHELFIE — Bookshelf to Library Inventory

Shelfie is a mobile application and API pipeline that turns a photograph of a bookshelf into a structured, verified personal library inventory.

## Project Status

- **Current Stage**: Phase 1 — Foundation & Repository Setup (`PASSED`)
- **Backend Stack**: Python 3.11+, Django 5.2+, Django REST Framework 3.18+, SQLite
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
2. Install Phase 1 foundation dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Run backend unit test suite:
   ```bash
   cd backend
   pytest
   ```
4. Start the Django development server:
   ```bash
   python manage.py runserver 127.0.0.1:8000
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

## Benchmarks & Methodology (Phase 7 TBD)

- **Local CV Latency**: `TBD — measured during benchmark phase`
- **Hosted VLM Latency**: `TBD — measured during benchmark phase`
- **Catalog Matching Latency**: `TBD — measured during benchmark phase`
- **Estimated API Cost per Scan**: `TBD — measured during benchmark phase`

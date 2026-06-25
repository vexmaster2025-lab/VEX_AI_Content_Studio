# VEX AI Content Studio MVP

Monorepo containing:
- `backend/`: FastAPI backend with PostgreSQL, Redis, Stripe, JWT auth, validation, and error handling
- `admin/`: Next.js admin dashboard with responsive dark/light theme and content management UI
- `mobile/`: Flutter app with auth, dashboard, theming, and backend integration

## Run Backend
1. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
2. Copy `backend/.env.example` to `backend/.env` and configure env vars.
3. Run:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Run Admin Dashboard
1. Install dependencies:
   ```bash
   cd admin
   npm install
   ```
2. Copy `admin/.env.example` to `admin/.env`.
3. Run:
   ```bash
   npm run dev
   ```

## Run Flutter App
1. Install dependencies:
   ```bash
   cd mobile
   flutter pub get
   ```
2. Copy `mobile/.env.example` to `mobile/.env`.
3. Run:
   ```bash
   flutter run
   ```

## Local Services
For development, use PostgreSQL and Redis. A sample `docker-compose.yml` is included for backend dependencies.

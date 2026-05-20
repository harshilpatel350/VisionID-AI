# VisionID AI – Face Registry & Recognition Platform

VisionID AI is a local-first, full-stack face registry and recognition platform built with:

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS, Framer Motion, React Query, Zustand, Recharts
- **Backend:** FastAPI, SQLAlchemy 2, Alembic, OpenCV, InsightFace, ONNX Runtime, FAISS, MySQL
- **Auth:** JWT + bcrypt password hashing
- **Realtime:** WebSockets for webcam recognition
- **Exports:** CSV + Excel
- **Database:** MySQL schema + migrations

## What is included

- Complete frontend and backend source tree
- MySQL schema
- Alembic migration
- REST API + WebSocket API
- Dashboard, registry, recognition studio, live webcam, search, analytics, settings, admin UI
- Local configuration files with no `.env` requirement
- Windows launch scripts
- Test examples
- Production-style folder structure

## Running locally

### 1) MySQL
Create a database named `visionid_ai` in MySQL 8+.

### 2) Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

Backend defaults are stored in `backend/config/settings.json`.

### 3) Frontend
```bash
cd frontend
npm install
npm run dev
```

Open the frontend at `http://localhost:3000`.

## Default login

The app seeds an admin user if the database is empty:

- Email: `admin@visionid.ai`
- Password: `Admin@12345`

Change this immediately after first sign-in.

## Notes

- No FFmpeg is used anywhere in the project.
- Face recognition uses InsightFace as the primary engine, with an OpenCV-compatible pipeline and FAISS vector search.
- Webcam frames are processed with browser media APIs and WebSockets.
- If InsightFace model weights are not yet present locally, the library may download them on first use.

## Project structure

See `docs/API.md` for API details and `database/schema.sql` for the MySQL schema.

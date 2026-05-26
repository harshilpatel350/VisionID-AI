# VisionID AI – Advanced Face Registry & Recognition Platform

VisionID AI is a production-grade, local-first face registry and recognition platform featuring real-time multi-face tracking, biometric liveness detection, emotional/mood analytics, and a premium futuristic dark theme.

## Architecture & Technology Stack

- **Frontend:** Next.js 16 (App Router), TypeScript, Tailwind CSS, Framer Motion (micro-animations), React Query, Zustand, Recharts
- **Backend:** FastAPI, SQLAlchemy 2, SQLite (default, zero-configuration) / MySQL support, OpenCV, InsightFace, DeepFace, ONNX Runtime, FAISS (vector similarity index)
- **Advanced AI Pipeline:**
  - **Centroid FaceTracker:** Multi-face tracking trails over live webcam streams.
  - **Liveness Detection:** Micro-movement and blink-rate analysis to detect photo replay spoofing.
  - **Emotion Classification:** Real-time facial expression mapping (Happy, Sad, Angry, Surprise, Fear, Disgust, Neutral).
  - **Low-Light Detail Recovery:** Adaptive histogram equalization & gamma correction for dark room captures.
- **Biometric Security:** Strict username + password authentication, JWT session persistence, Axios global interceptors for automatic session termination (401 handling), and global SQLite connection thread-safety.

---

## Key Features & Workspace Pages

1. **Dashboard:** Unified command center showcasing real-time metric counters, daily activity area charts, confidence levels, and active scan logs.
2. **Recognition Studio:** A premium image drag-and-drop workbench that overlays face bounding boxes on uploaded images using percentage coordinate mapping, displaying liveness, mood, and matching scores.
3. **Face Registry:** Add new identities, capture face samples via camera/file upload, specify demographics (Age, Gender, Tags, Notes), and automatically resolve/prevent duplicates.
4. **Live Webcam Tracking:** Real-time video websocket stream illustrating glowing bounding boxes, tracking ID indicators, and real-time scanning logs.
5. **Group Crowd Analyzer:** Drag-and-drop crowd photos to count total faces, map coordinates, and analyze group mood aggregates.
6. **Unknown Faces Panel:** Operator review screen to browse unidentified targets that tripped the camera, allowing operators to dismiss logs or register them.
7. **Emotion Analytics:** Deep analytics on collected emotional data points, visualizing mood distributions and percentages.

---

## Running Locally

### 1) Run Launcher (Windows)
Double-click `run.bat` at the root of the project. The script will automatically:
- Create a Python virtual environment (`venv`) and install dependencies in `backend/`.
- Install Node dependencies in `frontend/`.
- Start both FastAPI (Port `8001`) and Next.js (Port `3000`) concurrently.

### 2) Manual Start

#### Backend Setup
```bash
cd backend
python -m venv venv
# Activate virtual environment:
# Windows: venv\Scripts\activate.bat  |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m app.main
```
*Note: SQLite is configured by default. Database tables are generated automatically on startup.*

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open the application at **`http://localhost:3000`**.

---

## Default Login Credentials

The system seeds an administrator account upon initial database initialization:

- **Username:** `admin`
- **Password:** `Admin@12345`

*Note: The platform utilizes strict username-based login. Remember to change the password or create operator/viewer accounts in the Admin panel after first sign-in.*

---

## Notes & Architecture Decisions

- **No FFmpeg dependency:** The video processing pipeline runs natively on top of OpenCV decode-streams to simplify installation.
- **FAISS Vector Indexing:** Face embeddings are cached in memory using FAISS to speed up matches. If the index isn't found on disk, the system builds it dynamically from face samples.
- **First-run Download:** InsightFace and DeepFace will automatically download their pre-trained model weights on their first run. This may cause a slight delay when executing your first scan or webcam session.
- **Local-First Privacy:** All image files, embeddings, and telemetry logs remain on your local database and file storage directory (`backend/storage`).

---

## Project Structure

- `backend/app/ai/`: Face tracking, emotion detection, liveness, and enhancement modules.
- `backend/app/services/`: Database business logic (Faces, Group upload, Mood metrics, Audits).
- `frontend/src/app/`: Next.js pages styled with the **Violet & Lavender** futuristic CSS system.
- `frontend/src/components/`: Reusable charts, webcam handlers, and interactive layout shell.
- `docs/API.md`: Standard REST/WS API schema endpoints.

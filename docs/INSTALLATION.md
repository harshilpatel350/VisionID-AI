# Installation Guide

## Prerequisites
- Python 3.12+
- Node.js 20+
- MySQL 8+
- Windows 10/11 or Linux

## Backend
```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

The backend reads its configuration from `backend/config/settings.json`.

## Frontend
```bash
cd frontend
npm install
npm run dev
```

## Default admin
- Email: `admin@visionid.local`
- Password: `Admin@12345`

## Notes
- No `.env` file is required.
- No FFmpeg is used.
- Webcam detection uses the browser camera plus WebSockets.

# Yelp Clone Fullstack

A full-stack Yelp-like application built with **FastAPI** (backend) and **React** (frontend).

## Team

| Area | Owner |
|---|---|
| Backend (API, Auth, DB models, Routes) | Dipin |
| Frontend (React UI, Components, Pages) | Chaitanya |
| AI Assistant (routes + service) | Chaitanya |

## Project Structure

```
yelp-prototype/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry point
│   │   ├── config.py         # App settings
│   │   ├── auth.py           # JWT & password utilities
│   │   ├── models/           # SQLAlchemy DB models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── restaurants.py
│   │   │   ├── reviews.py
│   │   │   ├── favorites.py
│   │   │   ├── owner.py
│   │   │   └── ai_assistant.py
│   │   └── services/
│   │       └── ai_service.py
│   └── requirements.txt
└── frontend/
    └── src/
        ├── components/
        ├── pages/
        ├── services/
        ├── context/
        └── App.jsx
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

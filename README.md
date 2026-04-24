# Yelp Clone Fullstack

A full-stack Yelp-like restaurant discovery platform built with **FastAPI** (backend) and **React** (frontend), featuring AI-powered restaurant recommendations.

## Team

| Name | Role | Contributions |
|---|---|---|
| **Dipin Jassal** | Backend Lead | Auth system (JWT + bcrypt), database schema, all API routes, bug fixes, Swagger docs, seed data, testing |
| **Chaitanya Uppalapati** | Frontend Lead | React UI, all pages and components, routing, AI chat widget, owner dashboard frontend |

---

## What Each Person Did

### Dipin Jassal — Backend

- Designed and implemented the MySQL database schema (`schema.sql`) with all tables: users, restaurants, reviews, favorites, conversation history, user preferences
- Built FastAPI backend with full REST API:
  - **Auth** — JWT login/logout, bcrypt password hashing, role-based access (user/owner)
  - **Users** — profile management, avatar upload, preferences (cuisine, dietary, ambiance, price), activity history
  - **Restaurants** — CRUD with search, filters (cuisine, city, price tier, keyword), pagination, soft-delete
  - **Reviews** — create/update/delete with photo upload, avg rating recalculation, one review per user per restaurant
  - **Favorites** — add/remove/list favorite restaurants
  - **Owner** — claim restaurants, manage listings, analytics dashboard, view all reviews
  - **AI Assistant** — LangGraph ReAct agent with OpenAI GPT-4o-mini and Tavily web search
- Fixed all backend bugs: bcrypt/passlib incompatibility, joinedload for username display, enum serialization, route import errors, duplicate mounts
- Added Swagger documentation (`summary=` on all routes, accessible at `/docs`)
- Wrote automated test suite (`test_api.py`) covering 30+ endpoint scenarios
- Seeded 15 Bay Area restaurants and 30 reviews per restaurant with realistic data (`seed_reviews.py`)
- Configured `.env` with OpenAI and Tavily API keys for AI assistant

### Chaitanya Uppalapati — Frontend

- Built full React (Vite) frontend with React Router for all pages
- **Pages**: Home/Explore, Restaurant Detail, Write Review, Favorites, Profile, History, Login, Signup, Owner Dashboard, Owner Manage, Add Restaurant, Not Found
- **Components**: Navbar, Restaurant Card, Review Card, Star Rating, Chat Widget (AI), Protected Route
- Implemented JWT auth context (`AuthContext`) with login/signup/logout flow
- Built floating AI chat widget with session management and restaurant recommendation cards
- Owner dashboard with stat cards, ratings distribution bar chart, recent reviews, and restaurant management
- Restaurant detail page with hero image, amenities, hours, claim banner for owners
- Profile page with preferences tab (cuisine, dietary, ambiance, price range chip selectors)
- Axios API service layer with auth token injection

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, MySQL (PyMySQL) |
| Auth | JWT (python-jose), bcrypt |
| Frontend | React 18, Vite, React Router v6 |
| HTTP Client | Axios |
| AI | LangGraph, OpenAI GPT-4o-mini, Tavily Search |
| Styling | Custom CSS (dark theme) |

---

## Project Structure

```
yelp-clone-fullstack/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point, CORS, route registration
│   │   ├── config.py            # Settings via pydantic-settings (.env)
│   │   ├── auth.py              # JWT creation/verification, bcrypt hashing
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── models/              # ORM models: User, Restaurant, Review, Favorite, etc.
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── routes/
│   │   │   ├── auth.py          # POST /auth/register, /auth/login, /auth/logout
│   │   │   ├── users.py         # GET/PUT /users/me, preferences, avatar, history
│   │   │   ├── restaurants.py   # CRUD + search /restaurants/
│   │   │   ├── reviews.py       # CRUD + photo upload /reviews/
│   │   │   ├── favorites.py     # GET/POST/DELETE /favorites/
│   │   │   ├── owner.py         # /owner/claim, /owner/dashboard, /owner/analytics
│   │   │   └── ai_assistant.py  # POST /ai/chat
│   │   └── services/
│   │       └── ai_service.py    # LangGraph ReAct agent, search tool, conversation history
│   ├── schema.sql               # Full DB schema + Bay Area restaurant seed data
│   ├── seed_reviews.py          # Seeds 30 reviews per restaurant with realistic names
│   ├── test_api.py              # Automated end-to-end API test suite
│   └── requirements.txt
└── frontend/
    └── src/
        ├── App.jsx              # Routes + ProtectedRoute
        ├── context/
        │   └── AuthContext.jsx  # Global auth state, login/logout/signup
        ├── services/
        │   └── api.js           # Axios instance with JWT interceptor
        ├── components/
        │   ├── Navbar.jsx
        │   ├── RestaurantCard.jsx
        │   ├── ReviewCard.jsx
        │   ├── StarRating.jsx
        │   └── ChatWidget.jsx   # Floating AI chat with restaurant cards
        └── pages/
            ├── ExplorePage.jsx          # Home + restaurant search/filter
            ├── RestaurantDetailPage.jsx # Detail, reviews, claim banner
            ├── WriteReviewPage.jsx      # Submit review with photo upload
            ├── ProfilePage.jsx          # Profile + preferences tabs
            ├── FavoritesPage.jsx
            ├── HistoryPage.jsx
            ├── OwnerDashboardPage.jsx   # Analytics, rating distribution, recent reviews
            ├── OwnerManagePage.jsx      # Edit restaurant profile/hours/photos
            ├── AddRestaurantPage.jsx
            ├── LoginPage.jsx
            └── SignupPage.jsx
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Fill in: DATABASE_URL, SECRET_KEY, OPENAI_API_KEY, TAVILY_API_KEY

# Run schema + seed data
mysql -u root -p < schema.sql

# Start server
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## Key Features

- **Restaurant discovery** — search by cuisine, city, price tier, keyword
- **Reviews** — star ratings, comments, photo uploads (up to 5 per review)
- **Favorites** — save and manage favorite restaurants
- **AI Assistant** — floating chat powered by GPT-4o-mini; searches the local DB and web, personalizes recommendations based on saved preferences
- **Owner portal** — claim restaurants, manage profiles/hours/photos, view analytics dashboard
- **User preferences** — set cuisine, dietary, ambiance, price preferences used by the AI

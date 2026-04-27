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
| Backend (microservices) | FastAPI, Motor (async MongoDB), Python 3.13 |
| Message broker | Apache Kafka + Zookeeper (confluent-kafka) |
| Database | MongoDB 7 |
| Auth | JWT (python-jose), bcrypt |
| Frontend | React 18, Vite, React Router v6, Redux Toolkit |
| HTTP Client | Axios |
| AI | LangGraph, OpenAI GPT-4o-mini, Tavily Search |
| Styling | Custom CSS (dark theme) |
| Containerization | Docker, Docker Compose |
| Orchestration | Kubernetes (k8s/ manifests), AWS EKS |
| Load testing | Apache JMeter |

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

### Option A — Docker Compose (recommended, runs everything)

**Prerequisites:** Docker Desktop, Docker Compose

```bash
# From the project root
docker compose up --build
```

This starts all services:

| Service | URL |
|---|---|
| User Service (auth, profiles, favorites) | http://localhost:8001 |
| Restaurant Service (CRUD, search) | http://localhost:8002 |
| Owner Service (dashboard, analytics) | http://localhost:8003 |
| Review Service (reviews, ratings) | http://localhost:8004 |
| Frontend | http://localhost:5173 |
| MongoDB | localhost:27017 |
| Kafka | localhost:29092 (external) |

Seed data into MongoDB after the stack is up:

```bash
docker exec -it mongodb mongosh yelp_db --eval "load('/docker-entrypoint-initdb.d/seed.js')"
# Or run the Python seed script against port 27017:
cd backend && python seed_restaurants.py
```

---

### Option B — Local development (monolithic backend + Vite frontend)

**Prerequisites:** Python 3.11+, Node.js 18+, MySQL 8.0+

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in: SECRET_KEY, OPENAI_API_KEY, TAVILY_API_KEY
# DB_HOST=localhost, DB_NAME=yelp_clone, DB_USER=root

mysql -u root -p < schema.sql

uvicorn app.main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

```bash
# Frontend
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

---

## Lab 2 — Docker, Kubernetes, Kafka, MongoDB & Redux

### Architecture (Lab 2)

The monolithic FastAPI backend was split into **4 microservices** connected via **Kafka async messaging** and backed by **MongoDB**:

```
Frontend (React + Redux)
    │
    ├── POST /auth/login  ──►  User Service (8001)   ──► Kafka: user.created/updated
    ├── GET  /restaurants ──►  Restaurant Service (8002) ──► Kafka: restaurant.*
    ├── POST /reviews/    ──►  Review Service (8004)  ──► Kafka: review.created/updated/deleted
    └── GET  /owner/dash  ──►  Owner Service (8003)
                                    │
                         Kafka topics consumed by:
                         ├── user-worker       (logs, welcome emails)
                         ├── restaurant-worker (logging, notifications)
                         └── review-worker     (recalculates avg_rating in MongoDB)
```

### Kafka Topics

| Topic | Producer | Consumer |
|---|---|---|
| `review.created` | Review Service | Review Worker |
| `review.updated` | Review Service | Review Worker |
| `review.deleted` | Review Service | Review Worker |
| `restaurant.created` | Restaurant Service | Restaurant Worker |
| `restaurant.updated` | Restaurant Service | Restaurant Worker |
| `restaurant.claimed` | Restaurant/Owner Service | Restaurant Worker |
| `user.created` | User Service | User Worker |
| `user.updated` | User Service | User Worker |
| `booking.status` | Review Worker | (frontend polling) |

### Redux Store (Frontend)

State management was migrated from React Context to Redux Toolkit with 4 slices:

| Slice | State | Thunks |
|---|---|---|
| `authSlice` | `token, user, isAuthenticated, loading` | `loginUser`, `registerUser`, `logoutUser` |
| `restaurantSlice` | `restaurants[], currentRestaurant, searchFilters` | `fetchRestaurants`, `fetchRestaurantById` |
| `reviewSlice` | `reviews[], loading` | `fetchReviews`, `createReview`, `updateReview`, `deleteReview` |
| `favoritesSlice` | `favorites[], loading` | `fetchFavorites`, `addFavorite`, `removeFavorite` |

### Kubernetes

All manifests are in `k8s/`:

```bash
# Apply to a cluster (EKS or minikube)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/mongodb.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/
kubectl get pods -n yelp
kubectl get services -n yelp
```

### AWS EKS Deployment

```bash
cd aws
# Create EKS cluster
eksctl create cluster -f eks-cluster.yaml

# Push images to ECR
./ecr-push.sh

# Deploy to EKS
./deploy-to-eks.sh
```

### JMeter Load Testing

Test results are in `jmeter/results.csv`. Graphs are in `jmeter/graph_dashboard.png`.

Tests ran at 100 / 200 / 300 / 400 / 500 concurrent users against 3 endpoints:

| Endpoint | Avg RT (100 users) | Avg RT (500 users) | Error Rate |
|---|---|---|---|
| GET /restaurants | ~1ms | ~1ms | 0% |
| POST /auth/login | requires user-service running | — | — |
| POST /reviews/ | requires auth token | — | — |

To regenerate graphs from results:

```bash
cd jmeter
python3 generate_graphs.py
```

---

## Key Features

- **Restaurant discovery** — search by cuisine, city, price tier, keyword
- **Reviews** — star ratings, comments, photo uploads (up to 5 per review)
- **Favorites** — save and manage favorite restaurants
- **AI Assistant** — floating chat powered by GPT-4o-mini; searches the local DB and web, personalizes recommendations based on saved preferences
- **Owner portal** — claim restaurants, manage profiles/hours/photos, view analytics dashboard
- **User preferences** — set cuisine, dietary, ambiance, price preferences used by the AI

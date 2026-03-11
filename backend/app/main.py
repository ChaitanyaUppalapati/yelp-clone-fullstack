from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, users, restaurants, reviews, favorites, owner
from app.routes import ai_assistant

app = FastAPI(
    title="Yelp Clone API",
    description="A full-stack Yelp-like application built with FastAPI and MySQL.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite / CRA dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,         prefix="/auth",         tags=["Auth"])
app.include_router(users.router,        prefix="/users",        tags=["Users"])
app.include_router(restaurants.router,  prefix="/restaurants",  tags=["Restaurants"])
app.include_router(reviews.router,      prefix="/reviews",      tags=["Reviews"])
app.include_router(favorites.router,    prefix="/favorites",    tags=["Favorites"])
app.include_router(owner.router,        prefix="/owner",        tags=["Owner"])
app.include_router(ai_assistant.router, prefix="/ai",           tags=["AI Assistant"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Yelp Clone API is running"}

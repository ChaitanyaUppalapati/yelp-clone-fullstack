import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routes import auth, users, restaurants, reviews, favorites, owner
from app.routes import ai_assistant


# Ensure upload directories exist
os.makedirs("uploads/avatars", exist_ok=True)
os.makedirs("uploads/reviews", exist_ok=True)

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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],  # Vite / CRA dev
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


app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "ok", "message": "Yelp Clone API is running"}

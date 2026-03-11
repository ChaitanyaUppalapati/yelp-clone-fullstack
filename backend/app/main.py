from fastapi import FastAPI
from app.config import settings
from app.routes import auth, users, restaurants, reviews, favorites, owner

app = FastAPI(title="Yelp Clone API")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(restaurants.router, prefix="/restaurants", tags=["Restaurants"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
app.include_router(owner.router, prefix="/owner", tags=["Owner"])


@app.get("/")
def root():
    return {"message": "Welcome to the Yelp Clone API"}

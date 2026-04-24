import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.restaurants import router as restaurants_router

os.makedirs("uploads/restaurants", exist_ok=True)

app = FastAPI(
    title="Restaurant Service",
    description="Restaurant CRUD, search, filtering, and photo uploads.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(restaurants_router, prefix="/restaurants", tags=["Restaurants"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "restaurant-service"}

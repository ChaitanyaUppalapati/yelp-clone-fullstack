import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.auth import router as auth_router
from routes.users import router as users_router

os.makedirs("uploads/avatars", exist_ok=True)

app = FastAPI(
    title="User Service",
    description="Auth, profiles, preferences, favorites, and activity history.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "user-service"}

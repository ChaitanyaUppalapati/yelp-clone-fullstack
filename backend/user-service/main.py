import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routes.auth import router as auth_router, ensure_session_ttl_index
from routes.users import router as users_router
from routes.ai import router as ai_router

os.makedirs("uploads/avatars", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_session_ttl_index()
    yield


app = FastAPI(
    title="User Service",
    description="Auth, profiles, preferences, favorites, and activity history.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "user-service"}

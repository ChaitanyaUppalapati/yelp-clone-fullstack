from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta, timezone
import uuid

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.auth import (
    hash_password, verify_password, create_access_token,
    get_token_user_id, ACCESS_TOKEN_EXPIRE_MINUTES,
)
from shared.database import get_db
from shared.kafka_producer import publish
from models import UserCreate, UserOut, Token

router = APIRouter()

SESSION_TTL_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES


async def _ensure_session_ttl_index():
    """Create TTL index on sessions.expires_at once at startup."""
    db = get_db()
    await db.sessions.create_index("expires_at", expireAfterSeconds=0)


@router.on_event("startup")
async def startup():
    await _ensure_session_ttl_index()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserCreate):
    db = get_db()
    if await db.users.find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = payload.model_dump()
    doc["password_hash"] = hash_password(doc.pop("password"))
    doc["created_at"] = datetime.now(timezone.utc)
    doc["updated_at"] = datetime.now(timezone.utc)
    doc["profile_picture"] = None
    doc["about_me"] = None
    doc["languages"] = None
    doc["gender"] = None

    result = await db.users.insert_one(doc)
    doc["_id"] = result.inserted_id

    publish("user.created", {"user_id": str(result.inserted_id), "email": doc["email"]})
    return UserOut.from_doc(doc)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = get_db()
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": str(user["_id"])})
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=SESSION_TTL_MINUTES)

    # Store session in MongoDB — TTL index on expires_at auto-deletes expired docs
    await db.sessions.insert_one({
        "session_id": uuid.uuid4().hex,
        "user_id": str(user["_id"]),
        "token": token,
        "created_at": now,
        "expires_at": expires_at,
    })

    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=200)
async def logout(user_id: str = Depends(get_token_user_id)):
    db = get_db()
    # Invalidate all active sessions for this user
    await db.sessions.delete_many({"user_id": user_id})
    return {"message": "Successfully logged out"}

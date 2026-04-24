import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from bson import ObjectId
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.auth import get_token_user_id
from shared.database import get_db
from shared.kafka_producer import publish
from models import UserOut, UserUpdate, UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesOut

UPLOAD_DIR = "uploads/avatars"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

router = APIRouter()


async def _get_user_doc(user_id: str):
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserOut)
async def get_me(user_id: str = Depends(get_token_user_id)):
    return UserOut.from_doc(await _get_user_doc(user_id))


@router.put("/me", response_model=UserOut)
async def update_me(payload: UserUpdate, user_id: str = Depends(get_token_user_id)):
    db = get_db()
    updates = payload.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.utcnow()
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    publish("user.updated", {"user_id": user_id})
    return UserOut.from_doc(await _get_user_doc(user_id))


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    user_id: str = Depends(get_token_user_id),
):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(contents)

    db = get_db()
    picture_url = f"/uploads/avatars/{filename}"
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": picture_url, "updated_at": datetime.utcnow()}},
    )
    return UserOut.from_doc(await _get_user_doc(user_id))


@router.get("/me/preferences", response_model=UserPreferencesOut)
async def get_preferences(user_id: str = Depends(get_token_user_id)):
    db = get_db()
    prefs = await db.user_preferences.find_one({"user_id": user_id})
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return UserPreferencesOut.from_doc(prefs)


@router.post("/me/preferences", response_model=UserPreferencesOut, status_code=201)
async def create_preferences(
    payload: UserPreferencesCreate,
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    if await db.user_preferences.find_one({"user_id": user_id}):
        raise HTTPException(status_code=400, detail="Preferences already exist; use PUT to update")
    doc = {"user_id": user_id, **payload.model_dump()}
    result = await db.user_preferences.insert_one(doc)
    doc["_id"] = result.inserted_id
    return UserPreferencesOut.from_doc(doc)


@router.put("/me/preferences", response_model=UserPreferencesOut)
async def update_preferences(
    payload: UserPreferencesUpdate,
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    prefs = await db.user_preferences.find_one({"user_id": user_id})
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found; use POST to create")
    await db.user_preferences.update_one(
        {"user_id": user_id},
        {"$set": payload.model_dump(exclude_none=True)},
    )
    updated = await db.user_preferences.find_one({"user_id": user_id})
    return UserPreferencesOut.from_doc(updated)


@router.get("/me/history")
async def get_history(user_id: str = Depends(get_token_user_id)):
    db = get_db()
    reviews_cursor = db.reviews.find({"user_id": user_id}).sort("created_at", -1)
    reviews = []
    async for rev in reviews_cursor:
        rest = await db.restaurants.find_one({"_id": ObjectId(rev["restaurant_id"])})
        reviews.append({
            "id": str(rev["_id"]),
            "restaurant_id": rev["restaurant_id"],
            "restaurant_name": rest["name"] if rest else "Unknown",
            "rating": rev["rating"],
            "comment": rev.get("comment"),
            "created_at": rev.get("created_at"),
        })

    restaurants_cursor = db.restaurants.find({"added_by": user_id}).sort("created_at", -1)
    restaurants = []
    async for r in restaurants_cursor:
        restaurants.append({
            "id": str(r["_id"]),
            "name": r["name"],
            "cuisine_type": r.get("cuisine_type"),
            "city": r.get("city"),
            "avg_rating": float(r.get("avg_rating") or 0),
            "review_count": r.get("review_count") or 0,
            "pricing_tier": r.get("pricing_tier"),
            "created_at": r.get("created_at"),
        })

    return {"reviews": reviews, "restaurants_added": restaurants}


@router.get("/me/favorites")
async def list_favorites(user_id: str = Depends(get_token_user_id)):
    db = get_db()
    cursor = db.favorites.find({"user_id": user_id})
    favs = []
    async for f in cursor:
        favs.append({
            "id": str(f["_id"]),
            "user_id": f["user_id"],
            "restaurant_id": f["restaurant_id"],
            "created_at": f.get("created_at"),
        })
    return favs


@router.post("/me/favorites/{restaurant_id}", status_code=201)
async def add_favorite(restaurant_id: str, user_id: str = Depends(get_token_user_id)):
    db = get_db()
    existing = await db.favorites.find_one({"user_id": user_id, "restaurant_id": restaurant_id})
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")
    doc = {"user_id": user_id, "restaurant_id": restaurant_id, "created_at": datetime.utcnow()}
    result = await db.favorites.insert_one(doc)
    return {"id": str(result.inserted_id), **doc}


@router.delete("/me/favorites/{restaurant_id}", status_code=204)
async def remove_favorite(restaurant_id: str, user_id: str = Depends(get_token_user_id)):
    db = get_db()
    result = await db.favorites.delete_one({"user_id": user_id, "restaurant_id": restaurant_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str):
    return UserOut.from_doc(await _get_user_doc(user_id))

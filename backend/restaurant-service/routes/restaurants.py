import uuid
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from bson import ObjectId
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.auth import get_token_user_id
from shared.database import get_db
from shared.kafka_producer import publish
from models import RestaurantCreate, RestaurantUpdate, RestaurantOut

UPLOAD_DIR = "uploads/restaurants"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

router = APIRouter()


@router.get("/", response_model=List[RestaurantOut])
async def list_restaurants(
    q: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    pricing_tier: Optional[int] = Query(None, ge=1, le=4),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
):
    db = get_db()
    query: dict = {"is_active": True}

    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if cuisine:
        query["cuisine_type"] = {"$regex": cuisine, "$options": "i"}
    if pricing_tier:
        query["pricing_tier"] = pricing_tier
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"cuisine_type": {"$regex": q, "$options": "i"}},
        ]

    cursor = db.restaurants.find(query).sort("avg_rating", -1).skip(skip).limit(limit)
    return [RestaurantOut.from_doc(r) async for r in cursor]


@router.get("/{restaurant_id}", response_model=RestaurantOut)
async def get_restaurant(restaurant_id: str):
    db = get_db()
    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return RestaurantOut.from_doc(r)


@router.post("/", response_model=RestaurantOut, status_code=201)
async def create_restaurant(
    payload: RestaurantCreate,
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    doc = payload.model_dump()
    doc["owner_id"] = user_id
    doc["added_by"] = user_id
    doc["avg_rating"] = 0.0
    doc["review_count"] = 0
    doc["is_active"] = True
    doc["photos"] = []
    doc["created_at"] = datetime.utcnow()

    result = await db.restaurants.insert_one(doc)
    doc["_id"] = result.inserted_id

    publish("restaurant.created", {"restaurant_id": str(result.inserted_id), "owner_id": user_id})
    return RestaurantOut.from_doc(doc)


@router.post("/{restaurant_id}/claim", response_model=RestaurantOut)
async def claim_restaurant(restaurant_id: str, user_id: str = Depends(get_token_user_id)):
    db = get_db()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user or user.get("role") != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id), "is_active": True})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.get("owner_id") == user_id:
        raise HTTPException(status_code=400, detail="You already own this restaurant")

    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"owner_id": user_id}},
    )
    publish("restaurant.claimed", {"restaurant_id": restaurant_id, "new_owner_id": user_id})
    updated = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    return RestaurantOut.from_doc(updated)


@router.post("/{restaurant_id}/photos", response_model=RestaurantOut)
async def upload_photos(
    restaurant_id: str,
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    r = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.get("owner_id") != user_id:
        raise HTTPException(status_code=403, detail="Not the owner")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    existing = list(r.get("photos") or [])

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a valid image")
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{file.filename} exceeds 10MB")
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        filename = f"{restaurant_id}_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(contents)
        existing.append(f"/uploads/restaurants/{filename}")

    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"photos": existing}},
    )
    updated = await db.restaurants.find_one({"_id": ObjectId(restaurant_id)})
    return RestaurantOut.from_doc(updated)

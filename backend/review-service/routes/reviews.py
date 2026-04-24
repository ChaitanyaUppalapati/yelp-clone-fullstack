import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from bson import ObjectId
from datetime import datetime

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from shared.auth import get_token_user_id
from shared.database import get_db
from shared.kafka_producer import publish
from models import ReviewCreate, ReviewUpdate, ReviewOut

UPLOAD_DIR = "uploads/reviews"
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

router = APIRouter()


@router.get("/restaurant/{restaurant_id}", response_model=List[ReviewOut])
async def get_reviews(restaurant_id: str, skip: int = 0, limit: int = 20):
    db = get_db()
    cursor = (
        db.reviews.find({"restaurant_id": restaurant_id})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [ReviewOut.from_doc(r) async for r in cursor]


@router.post("/", response_model=ReviewOut, status_code=201)
async def create_review(
    payload: ReviewCreate,
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    existing = await db.reviews.find_one({
        "user_id": user_id,
        "restaurant_id": payload.restaurant_id,
    })
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this restaurant")

    doc = payload.model_dump()
    doc["user_id"] = user_id
    doc["photos"] = []
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()

    result = await db.reviews.insert_one(doc)
    doc["_id"] = result.inserted_id

    publish("review.created", {
        "review_id": str(result.inserted_id),
        "restaurant_id": payload.restaurant_id,
        "user_id": user_id,
        "rating": payload.rating,
    })
    return ReviewOut.from_doc(doc)


@router.put("/{review_id}", response_model=ReviewOut)
async def update_review(
    review_id: str,
    payload: ReviewUpdate,
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    old_rating = review.get("rating")
    updates = payload.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.utcnow()

    await db.reviews.update_one({"_id": ObjectId(review_id)}, {"$set": updates})

    if "rating" in updates and updates["rating"] != old_rating:
        publish("review.updated", {
            "review_id": review_id,
            "restaurant_id": review["restaurant_id"],
            "old_rating": old_rating,
            "new_rating": updates["rating"],
        })

    updated = await db.reviews.find_one({"_id": ObjectId(review_id)})
    return ReviewOut.from_doc(updated)


@router.post("/{review_id}/photos", response_model=ReviewOut)
async def upload_review_photos(
    review_id: str,
    files: List[UploadFile] = File(...),
    user_id: str = Depends(get_token_user_id),
):
    db = get_db()
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 photos per review")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    existing = list(review.get("photos") or [])

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a valid image")
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"{file.filename} exceeds 10MB limit")
        ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
        filename = f"{review_id}_{uuid.uuid4().hex}.{ext}"
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(contents)
        existing.append(f"/uploads/reviews/{filename}")

    await db.reviews.update_one(
        {"_id": ObjectId(review_id)},
        {"$set": {"photos": existing, "updated_at": datetime.utcnow()}},
    )
    updated = await db.reviews.find_one({"_id": ObjectId(review_id)})
    return ReviewOut.from_doc(updated)


@router.delete("/{review_id}", status_code=204)
async def delete_review(review_id: str, user_id: str = Depends(get_token_user_id)):
    db = get_db()
    review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    await db.reviews.delete_one({"_id": ObjectId(review_id)})
    publish("review.deleted", {
        "review_id": review_id,
        "restaurant_id": review["restaurant_id"],
        "rating": review.get("rating"),
    })

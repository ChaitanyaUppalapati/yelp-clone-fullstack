import uuid
import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.auth import get_current_user
from app.models.review import Review
from app.models.restaurant import Restaurant
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
UPLOAD_DIR = "uploads/reviews"

router = APIRouter()


@router.get("/restaurant/{restaurant_id}", response_model=list[ReviewOut], summary="List all reviews for a restaurant")
def get_reviews(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all reviews for a restaurant."""
    return (
        db.query(Review)
        .options(joinedload(Review.user))
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED, summary="Submit a review for a restaurant")
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit a review (one per user per restaurant)."""
    if current_user.role == "owner":
        raise HTTPException(status_code=403, detail="Owner accounts cannot submit reviews")

    restaurant = (
        db.query(Restaurant)
        .filter(Restaurant.id == payload.restaurant_id, Restaurant.is_active == True)
        .first()
    )
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.restaurant_id == payload.restaurant_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="You have already reviewed this restaurant")

    review = Review(user_id=current_user.id, **payload.model_dump())
    db.add(review)

    # Update restaurant aggregate stats
    total = restaurant.avg_rating * restaurant.review_count + payload.rating
    restaurant.review_count += 1
    restaurant.avg_rating = round(total / restaurant.review_count, 2)

    db.commit()
    db.refresh(review)
    return review


@router.put("/{review_id}", response_model=ReviewOut, summary="Update your own review")
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update your own review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # Recalculate avg_rating if rating changed
    if payload.rating is not None and payload.rating != review.rating:
        restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
        if restaurant and restaurant.review_count > 0:
            old_total = float(restaurant.avg_rating) * restaurant.review_count
            new_total = old_total - review.rating + payload.rating
            restaurant.avg_rating = round(new_total / restaurant.review_count, 2)

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(review, field, value)
    db.commit()
    db.refresh(review)
    return review


@router.post("/{review_id}/photos", response_model=ReviewOut, summary="Attach photos to a review")
async def upload_review_photos(
    review_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Attach up to 5 photos to your own review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 photos per review")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    existing = list(review.photos or [])

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

    review.photos = existing
    db.commit()
    db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete your own review")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete your own review."""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    # Recalculate avg_rating after deletion
    restaurant = db.query(Restaurant).filter(Restaurant.id == review.restaurant_id).first()
    if restaurant:
        new_count = restaurant.review_count - 1
        if new_count <= 0:
            restaurant.avg_rating = 0
            restaurant.review_count = 0
        else:
            old_total = float(restaurant.avg_rating) * restaurant.review_count
            restaurant.avg_rating = round((old_total - review.rating) / new_count, 2)
            restaurant.review_count = new_count

    db.delete(review)
    db.commit()

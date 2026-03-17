from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.review import Review
from app.models.restaurant import Restaurant
from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate

router = APIRouter()


@router.get("/restaurant/{restaurant_id}", response_model=list[ReviewOut])
def get_reviews(
    restaurant_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all reviews for a restaurant."""
    return (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip).limit(limit).all()
    )


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Submit a review (one per user per restaurant)."""
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
    restaurant = db.query(Restaurant).filter(Restaurant.id == payload.restaurant_id).first()
    if restaurant:
        total = restaurant.avg_rating * restaurant.review_count + payload.rating
        restaurant.review_count += 1
        restaurant.avg_rating = round(total / restaurant.review_count, 2)

    db.commit()
    db.refresh(review)
    return review


@router.put("/{review_id}", response_model=ReviewOut)
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


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
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

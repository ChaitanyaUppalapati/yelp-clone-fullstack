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
    db.delete(review)
    db.commit()

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import require_owner
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.restaurant import RestaurantOut, RestaurantUpdate, RestaurantListOut
from app.schemas.review import ReviewOut

router = APIRouter()


@router.get("/restaurants", response_model=list[RestaurantListOut])
def owner_restaurants(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """List all restaurants owned by the authenticated user."""
    return (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    )


@router.put("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Update a restaurant you own."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/restaurants/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Soft-delete (deactivate) a restaurant you own."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    r.is_active = False
    db.commit()


@router.get("/dashboard")
def owner_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Analytics dashboard for the owner's restaurants."""
    restaurants = (
        db.query(Restaurant)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    )
    restaurant_ids = [r.id for r in restaurants]

    if not restaurant_ids:
        return {
            "restaurant_count": 0,
            "total_reviews": 0,
            "overall_avg_rating": 0.0,
            "rating_distribution": {str(i): 0 for i in range(1, 6)},
            "restaurants": [],
            "recent_reviews": [],
        }

    # Total reviews + overall avg across all owned restaurants
    stats = (
        db.query(
            func.count(Review.id).label("total_reviews"),
            func.avg(Review.rating).label("overall_avg"),
        )
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .one()
    )

    # Rating distribution (1–5 star counts)
    dist_rows = (
        db.query(Review.rating, func.count(Review.id).label("cnt"))
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .group_by(Review.rating)
        .all()
    )
    distribution = {str(i): 0 for i in range(1, 6)}
    for row in dist_rows:
        distribution[str(row.rating)] = row.cnt

    # 5 most recent reviews
    recent = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .limit(5)
        .all()
    )

    # Per-restaurant summary
    restaurant_summaries = [
        {
            "id": r.id,
            "name": r.name,
            "avg_rating": float(r.avg_rating),
            "review_count": r.review_count,
            "is_active": r.is_active,
        }
        for r in restaurants
    ]

    return {
        "restaurant_count": len(restaurants),
        "total_reviews": stats.total_reviews or 0,
        "overall_avg_rating": round(float(stats.overall_avg or 0), 2),
        "rating_distribution": distribution,
        "restaurants": restaurant_summaries,
        "recent_reviews": [
            {
                "id": rv.id,
                "restaurant_id": rv.restaurant_id,
                "user_id": rv.user_id,
                "rating": rv.rating,
                "comment": rv.comment,
                "created_at": rv.created_at,
            }
            for rv in recent
        ],
    }


@router.get("/reviews", response_model=list[ReviewOut])
def owner_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_owner),
):
    """Paginated list of all reviews for the owner's restaurants."""
    restaurant_ids = [
        r.id
        for r in db.query(Restaurant.id)
        .filter(Restaurant.owner_id == current_user.id)
        .all()
    ]
    if not restaurant_ids:
        return []
    return (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

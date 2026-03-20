from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, require_owner
from app.models.restaurant import Restaurant
from app.models.review import Review
from app.schemas.restaurant import RestaurantOut, RestaurantUpdate, RestaurantListOut

router = APIRouter()


@router.put("/claim/{restaurant_id}", response_model=RestaurantOut)
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Claim an existing restaurant listing as the owner."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only restaurant owners can claim listings")
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.is_active == True).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this restaurant")
    r.owner_id = current_user.id
    db.commit()
    db.refresh(r)
    return r


@router.get("/analytics")
def owner_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return analytics for all restaurants owned by the current user."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    restaurants = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    if not restaurants:
        return {"total_restaurants": 0, "total_reviews": 0, "avg_rating": 0.0,
                "ratings_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "recent_reviews": []}

    rest_ids = [r.id for r in restaurants]

    # Ratings distribution across all owned restaurants
    all_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(rest_ids))
        .order_by(Review.created_at.desc())
        .all()
    )

    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rev in all_reviews:
        distribution[rev.rating] = distribution.get(rev.rating, 0) + 1

    total_reviews = len(all_reviews)
    avg_rating = (
        round(sum(r.rating for r in all_reviews) / total_reviews, 2) if total_reviews else 0.0
    )

    # Recent reviews (last 10 across all owned restaurants)
    recent = []
    rest_name_map = {r.id: r.name for r in restaurants}
    for rev in all_reviews[:10]:
        recent.append({
            "id": rev.id,
            "restaurant_id": rev.restaurant_id,
            "restaurant_name": rest_name_map.get(rev.restaurant_id, "Unknown"),
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at.isoformat() if rev.created_at else None,
        })

    return {
        "total_restaurants": len(restaurants),
        "total_reviews": total_reviews,
        "avg_rating": avg_rating,
        "ratings_distribution": distribution,
        "recent_reviews": recent,
    }


@router.get("/restaurants", response_model=list[RestaurantListOut])
def owner_restaurants(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
):
    """Soft-delete (deactivate) a restaurant you own."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not the owner of this restaurant")
    r.is_active = False
    db.commit()

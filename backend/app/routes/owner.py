from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, require_owner
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantOut, RestaurantUpdate, RestaurantListOut

router = APIRouter()


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

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantOut, RestaurantListOut

router = APIRouter()


@router.get("/", response_model=list[RestaurantListOut])
def list_restaurants(
    city:        Optional[str] = Query(None),
    cuisine:     Optional[str] = Query(None),
    pricing_tier: Optional[int] = Query(None, ge=1, le=4),
    skip:        int = Query(0, ge=0),
    limit:       int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """List restaurants with optional filters."""
    q = db.query(Restaurant).filter(Restaurant.is_active == True)
    if city:
        q = q.filter(Restaurant.city.ilike(f"%{city}%"))
    if cuisine:
        q = q.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if pricing_tier:
        q = q.filter(Restaurant.pricing_tier == pricing_tier)
    return q.order_by(Restaurant.avg_rating.desc()).offset(skip).limit(limit).all()


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Get a single restaurant by ID."""
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return r


@router.post("/", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new restaurant listing (any authenticated user)."""
    r = Restaurant(
        owner_id=current_user.id,
        added_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

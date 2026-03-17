from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models.restaurant import Restaurant
from app.schemas.restaurant import RestaurantCreate, RestaurantOut, RestaurantListOut

router = APIRouter()


@router.get("/", response_model=list[RestaurantListOut])
def list_restaurants(
    name:         Optional[str] = Query(None),
    cuisine:      Optional[str] = Query(None),
    keyword:      Optional[str] = Query(None),
    city:         Optional[str] = Query(None),
    zip_code:     Optional[str] = Query(None),
    pricing_tier: Optional[int] = Query(None, ge=1, le=4),
    skip:         int = Query(0, ge=0),
    limit:        int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """List/search restaurants with optional filters."""
    q = db.query(Restaurant).filter(Restaurant.is_active == True)
    if name:
        q = q.filter(Restaurant.name.ilike(f"%{name}%"))
    if cuisine:
        q = q.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if keyword:
        q = q.filter(
            Restaurant.name.ilike(f"%{keyword}%") |
            Restaurant.description.ilike(f"%{keyword}%") |
            Restaurant.cuisine_type.ilike(f"%{keyword}%")
        )
    if city:
        q = q.filter(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        q = q.filter(Restaurant.zip_code == zip_code)
    if pricing_tier:
        q = q.filter(Restaurant.pricing_tier == pricing_tier)
    return q.order_by(Restaurant.avg_rating.desc()).offset(skip).limit(limit).all()


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    """Get a single restaurant by ID, including its reviews."""
    r = (
        db.query(Restaurant)
        .options(joinedload(Restaurant.reviews))
        .filter(Restaurant.id == restaurant_id)
        .first()
    )
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


@router.post("/{restaurant_id}/claim", response_model=RestaurantOut)
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Claim ownership of a restaurant (owner role only)."""
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")

    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id, Restaurant.is_active == True).first()
    if not r:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if r.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this restaurant")

    r.owner_id = current_user.id
    db.commit()
    db.refresh(r)
    return r

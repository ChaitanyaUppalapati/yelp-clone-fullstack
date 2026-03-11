from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.favorite import Favorite
from app.schemas.favorite import FavoriteOut

router = APIRouter()


@router.get("/", response_model=list[FavoriteOut])
def list_favorites(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List the current user's favorite restaurants."""
    return db.query(Favorite).filter(Favorite.user_id == current_user.id).all()


@router.post("/{restaurant_id}", response_model=FavoriteOut, status_code=status.HTTP_201_CREATED)
def add_favorite(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Add a restaurant to favorites."""
    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.restaurant_id == restaurant_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Already in favorites")

    fav = Favorite(user_id=current_user.id, restaurant_id=restaurant_id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return fav


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Remove a restaurant from favorites."""
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == current_user.id, Favorite.restaurant_id == restaurant_id)
        .first()
    )
    if not fav:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(fav)
    db.commit()

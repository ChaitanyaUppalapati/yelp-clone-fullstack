from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserPreferences
from app.schemas.user import UserOut, UserUpdate, UserPreferencesCreate, UserPreferencesOut, UserPreferencesUpdate

router = APIRouter()


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the authenticated user's profile."""
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


# ---------------------------------------------------------------------------
# User preferences
# ---------------------------------------------------------------------------
@router.get("/me/preferences", response_model=UserPreferencesOut)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return prefs


@router.post("/me/preferences", response_model=UserPreferencesOut, status_code=status.HTTP_201_CREATED)
def create_preferences(
    payload: UserPreferencesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Preferences already exist; use PUT to update")
    prefs = UserPreferences(user_id=current_user.id, **payload.model_dump())
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


@router.put("/me/preferences", response_model=UserPreferencesOut)
def update_preferences(
    payload: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        raise HTTPException(status_code=404, detail="Preferences not found; use POST to create")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


# ---------------------------------------------------------------------------
# Public user lookup
# ---------------------------------------------------------------------------
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Public profile lookup."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User, UserPreferences
from app.models.review import Review
from app.models.restaurant import Restaurant
from app.schemas.user import UserOut, UserUpdate, UserPreferencesCreate, UserPreferencesOut, UserPreferencesUpdate
from app.schemas.review import ReviewOut
from app.schemas.restaurant import RestaurantListOut

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
UPLOAD_DIR = "uploads/avatars"

router = APIRouter()


# ---------------------------------------------------------------------------
# Current user
# ---------------------------------------------------------------------------
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.post("/me/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a profile picture. Accepts JPEG, PNG, WebP, or GIF."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed (JPEG, PNG, WebP, GIF)")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(contents)

    current_user.profile_picture = f"/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
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
# User history
# ---------------------------------------------------------------------------
@router.get("/me/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the user's review history and restaurants they added."""
    reviews = (
        db.query(Review)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )
    reviews_out = []
    for rev in reviews:
        rest = db.query(Restaurant).filter(Restaurant.id == rev.restaurant_id).first()
        reviews_out.append({
            "id": rev.id,
            "restaurant_id": rev.restaurant_id,
            "restaurant_name": rest.name if rest else "Unknown",
            "rating": rev.rating,
            "comment": rev.comment,
            "created_at": rev.created_at.isoformat() if rev.created_at else None,
        })

    restaurants_added = (
        db.query(Restaurant)
        .filter(Restaurant.added_by == current_user.id)
        .order_by(Restaurant.created_at.desc())
        .all()
    )
    restaurants_out = []
    for r in restaurants_added:
        restaurants_out.append({
            "id": r.id,
            "name": r.name,
            "cuisine_type": r.cuisine_type,
            "city": r.city,
            "avg_rating": float(r.avg_rating or 0),
            "review_count": r.review_count or 0,
            "pricing_tier": r.pricing_tier,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"reviews": reviews_out, "restaurants_added": restaurants_out}


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

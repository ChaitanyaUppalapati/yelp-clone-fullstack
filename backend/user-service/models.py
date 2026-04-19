from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId


def new_id() -> str:
    return str(ObjectId())


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "US"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[List[str]] = None
    gender: Optional[str] = None
    profile_picture: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict) -> "UserOut":
        doc["id"] = str(doc.pop("_id", doc.get("id", "")))
        return cls(**doc)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserPreferencesCreate(BaseModel):
    cuisine_preferences: Optional[List[str]] = None
    price_range: Optional[int] = Field(None, ge=1, le=4)
    preferred_locations: Optional[List[str]] = None
    search_radius: Optional[int] = 10
    dietary_needs: Optional[List[str]] = None
    ambiance_preferences: Optional[List[str]] = None
    sort_preference: Optional[str] = "rating"


class UserPreferencesUpdate(UserPreferencesCreate):
    pass


class UserPreferencesOut(UserPreferencesCreate):
    id: str
    user_id: str

    @classmethod
    def from_doc(cls, doc: dict) -> "UserPreferencesOut":
        doc["id"] = str(doc.pop("_id", doc.get("id", "")))
        return cls(**doc)

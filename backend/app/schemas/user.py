from __future__ import annotations
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    name:     str       = Field(..., min_length=1, max_length=120)
    email:    EmailStr
    password: str       = Field(..., min_length=8)
    role:     str       = "user"  # "user" | "owner"
    phone:    str | None = None
    city:     str | None = None
    state:    str | None = None
    country:  str        = "US"


class UserLogin(BaseModel):
    email:    EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type:   str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------
class UserUpdate(BaseModel):
    name:            str | None = None
    phone:           str | None = None
    about_me:        str | None = None
    city:            str | None = None
    state:           str | None = None
    country:         str | None = None
    languages:       list[str] | None = None
    gender:          str | None = None
    profile_picture: str | None = None


class UserOut(BaseModel):
    id:              int
    role:            str
    name:            str
    email:           str
    phone:           str | None
    about_me:        str | None
    city:            str | None
    state:           str | None
    country:         str | None
    languages:       list[str] | None
    gender:          str | None
    profile_picture: str | None
    created_at:      datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User Preferences
# ---------------------------------------------------------------------------
class UserPreferencesCreate(BaseModel):
    cuisine_preferences:  list[str] | None = None
    price_range:          int | None = Field(None, ge=1, le=4)
    preferred_locations:  list[str] | None = None
    search_radius:        float | None = 10.0
    dietary_needs:        list[str] | None = None
    ambiance_preferences: list[str] | None = None
    sort_preference:      str = "rating"


class UserPreferencesUpdate(UserPreferencesCreate):
    pass


class UserPreferencesOut(BaseModel):
    id:                   int
    user_id:              int
    cuisine_preferences:  list[str] | None
    price_range:          int | None
    preferred_locations:  list[str] | None
    search_radius:        float | None
    dietary_needs:        list[str] | None
    ambiance_preferences: list[str] | None
    sort_preference:      str
    updated_at:           datetime

    model_config = {"from_attributes": True}

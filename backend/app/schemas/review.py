from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    restaurant_id: int
    rating:        int  = Field(..., ge=1, le=5)
    comment:       str | None = None
    photos:        list[str] | None = None


class ReviewUpdate(BaseModel):
    rating:  int | None = Field(None, ge=1, le=5)
    comment: str | None = None
    photos:  list[str] | None = None


class ReviewOut(BaseModel):
    id:            int
    user_id:       int
    restaurant_id: int
    rating:        int
    comment:       str | None
    photos:        list[str] | None
    created_at:    datetime
    updated_at:    datetime

    model_config = {"from_attributes": True}

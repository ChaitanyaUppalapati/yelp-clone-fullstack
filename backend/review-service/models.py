from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    restaurant_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: str
    restaurant_id: str
    user_id: str
    rating: int
    comment: Optional[str] = None
    photos: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict) -> "ReviewOut":
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id", doc.get("id", "")))
        return cls(**doc)

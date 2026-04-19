from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RestaurantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "US"
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[int] = Field(None, ge=1, le=4)
    amenities: Optional[List[str]] = None


class RestaurantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[int] = Field(None, ge=1, le=4)
    amenities: Optional[List[str]] = None


class RestaurantOut(BaseModel):
    id: str
    owner_id: Optional[str] = None
    added_by: Optional[str] = None
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[dict] = None
    pricing_tier: Optional[int] = None
    amenities: Optional[List[str]] = None
    avg_rating: float = 0.0
    review_count: int = 0
    is_active: bool = True
    photos: Optional[List[str]] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_doc(cls, doc: dict) -> "RestaurantOut":
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id", doc.get("id", "")))
        return cls(**doc)

from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field


class RestaurantCreate(BaseModel):
    name:                str       = Field(..., min_length=1, max_length=255)
    cuisine_type:        str | None = None
    description:         str | None = None
    address_line:        str | None = None
    city:                str | None = None
    state:               str | None = None
    country:             str        = "US"
    zip_code:            str | None = None
    latitude:            float | None = None
    longitude:           float | None = None
    phone:               str | None = None
    website:             str | None = None
    email:               str | None = None
    hours_of_operation:  dict[str, str] | None = None
    pricing_tier:        int | None = Field(None, ge=1, le=4)
    amenities:           list[str] | None = None
    photos:              list[str] | None = None


class RestaurantUpdate(BaseModel):
    name:                str | None = None
    cuisine_type:        str | None = None
    description:         str | None = None
    address_line:        str | None = None
    city:                str | None = None
    state:               str | None = None
    country:             str | None = None
    zip_code:            str | None = None
    latitude:            float | None = None
    longitude:           float | None = None
    phone:               str | None = None
    website:             str | None = None
    email:               str | None = None
    hours_of_operation:  dict[str, str] | None = None
    pricing_tier:        int | None = Field(None, ge=1, le=4)
    amenities:           list[str] | None = None
    photos:              list[str] | None = None
    is_active:           bool | None = None


class RestaurantOut(BaseModel):
    id:                  int
    owner_id:            int
    added_by:            int
    name:                str
    cuisine_type:        str | None
    description:         str | None
    address_line:        str | None
    city:                str | None
    state:               str | None
    country:             str | None
    zip_code:            str | None
    latitude:            Decimal | None
    longitude:           Decimal | None
    phone:               str | None
    website:             str | None
    email:               str | None
    hours_of_operation:  dict[str, str] | None
    pricing_tier:        int | None
    amenities:           list[str] | None
    photos:              list[str] | None
    avg_rating:          Decimal
    review_count:        int
    is_active:           bool
    created_at:          datetime
    updated_at:          datetime

    model_config = {"from_attributes": True}


class RestaurantListOut(BaseModel):
    """Lightweight version for list/search endpoints."""
    id:           int
    name:         str
    cuisine_type: str | None
    city:         str | None
    state:        str | None
    pricing_tier: int | None
    avg_rating:   Decimal
    review_count: int
    photos:       list[str] | None

    model_config = {"from_attributes": True}

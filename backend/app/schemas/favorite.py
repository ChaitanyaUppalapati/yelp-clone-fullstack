from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class FavoriteOut(BaseModel):
    id:            int
    user_id:       int
    restaurant_id: int
    created_at:    datetime

    model_config = {"from_attributes": True}

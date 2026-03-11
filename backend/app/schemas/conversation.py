from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class ConversationMessageCreate(BaseModel):
    session_id: str          # UUID passed by client
    message:    str


class ConversationMessageOut(BaseModel):
    id:         int
    user_id:    int
    session_id: str
    role:       str   # "user" | "assistant" | "system"
    message:    str
    created_at: datetime

    model_config = {"from_attributes": True}

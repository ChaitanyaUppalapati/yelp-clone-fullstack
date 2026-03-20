import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.services.ai_service import AIService

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI assistant chat endpoint.
    Accepts a user message and optional session_id for multi-turn conversations.
    Returns a conversational response with optional restaurant recommendations.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    session_id = payload.session_id or str(uuid.uuid4())

    try:
        service = AIService(db=db, user_id=current_user.id)
        result = await service.chat(session_id=session_id, message=payload.message.strip())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI assistant error: {str(e)}",
        )

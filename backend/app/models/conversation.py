import enum
from sqlalchemy import Column, Integer, String, Text, Enum, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.database import Base


class MessageRole(str, enum.Enum):
    user      = "user"
    assistant = "assistant"
    system    = "system"


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id         = Column(Integer, primary_key=True, autoincrement=True, unsigned=True)
    user_id    = Column(Integer, nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)  # UUID
    role       = Column(Enum(MessageRole), nullable=False)
    message    = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="conversations")

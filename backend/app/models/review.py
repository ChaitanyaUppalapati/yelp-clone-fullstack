from sqlalchemy import Column, Integer, SmallInteger, Text, JSON, TIMESTAMP, func, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False, index=True)
    rating        = Column(SmallInteger, nullable=False)   # 1-5
    comment       = Column(Text,    nullable=True)
    photos        = Column(JSON,    nullable=True)
    created_at    = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at    = Column(TIMESTAMP, nullable=False, server_default=func.now(),
                           onupdate=func.now())

    # Relationships
    user       = relationship("User",       foreign_keys=[user_id],
                              back_populates="reviews")
    restaurant = relationship("Restaurant", foreign_keys=[restaurant_id],
                              back_populates="reviews")

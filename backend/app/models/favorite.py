from sqlalchemy import Column, Integer, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.database import Base


class Favorite(Base):
    __tablename__ = "favorites"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    user_id       = Column(Integer, nullable=False, index=True)
    restaurant_id = Column(Integer, nullable=False, index=True)
    created_at    = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relationships
    user       = relationship("User",       foreign_keys=[user_id],
                              back_populates="favorites")
    restaurant = relationship("Restaurant", foreign_keys=[restaurant_id],
                              back_populates="favorites")

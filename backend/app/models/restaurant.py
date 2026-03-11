from sqlalchemy import (
    Column, Integer, String, Text, JSON, Numeric,
    TIMESTAMP, SmallInteger, Boolean, func
)
from sqlalchemy.orm import relationship

from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id                  = Column(Integer, primary_key=True, autoincrement=True, unsigned=True)
    owner_id            = Column(Integer, nullable=False, index=True)
    added_by            = Column(Integer, nullable=False)
    name                = Column(String(255), nullable=False)
    cuisine_type        = Column(String(100), nullable=True, index=True)
    description         = Column(Text,        nullable=True)
    # Address
    address_line        = Column(String(255), nullable=True)
    city                = Column(String(100), nullable=True, index=True)
    state               = Column(String(100), nullable=True)
    country             = Column(String(100), nullable=True, default="US")
    zip_code            = Column(String(20),  nullable=True)
    latitude            = Column(Numeric(10, 7), nullable=True)
    longitude           = Column(Numeric(10, 7), nullable=True)
    # Contact
    phone               = Column(String(30),  nullable=True)
    website             = Column(String(512), nullable=True)
    email               = Column(String(255), nullable=True)
    # Operational
    hours_of_operation  = Column(JSON,        nullable=True)
    pricing_tier        = Column(SmallInteger, nullable=True, default=2)  # 1-4
    amenities           = Column(JSON,        nullable=True)
    photos              = Column(JSON,        nullable=True)
    # Aggregated stats
    avg_rating          = Column(Numeric(3, 2), default=0.00)
    review_count        = Column(Integer,       default=0)
    is_active           = Column(Boolean,       default=True)
    created_at          = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at          = Column(TIMESTAMP, nullable=False, server_default=func.now(),
                                 onupdate=func.now())

    # Relationships
    owner   = relationship("User", foreign_keys=[owner_id], back_populates="owned_restaurants")
    adder   = relationship("User", foreign_keys=[added_by], back_populates="added_restaurants")
    reviews   = relationship("Review",   back_populates="restaurant",
                             cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="restaurant",
                             cascade="all, delete-orphan")

import enum
from sqlalchemy import (
    Column, Integer, String, Text, Enum, JSON,
    TIMESTAMP, func
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    owner = "owner"


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True, unsigned=True)
    role            = Column(Enum(UserRole), nullable=False, default=UserRole.user)
    name            = Column(String(120), nullable=False)
    email           = Column(String(255), nullable=False, unique=True, index=True)
    password_hash   = Column(String(255), nullable=False)
    phone           = Column(String(30),  nullable=True)
    about_me        = Column(Text,        nullable=True)
    city            = Column(String(100), nullable=True, index=True)
    state           = Column(String(100), nullable=True)
    country         = Column(String(100), nullable=True, default="US")
    languages       = Column(JSON,        nullable=True)   # ["English","Spanish"]
    gender          = Column(String(30),  nullable=True)
    profile_picture = Column(String(512), nullable=True)
    created_at      = Column(TIMESTAMP,   nullable=False, server_default=func.now())
    updated_at      = Column(TIMESTAMP,   nullable=False, server_default=func.now(),
                             onupdate=func.now())

    # Relationships
    preferences         = relationship("UserPreferences", back_populates="user",
                                       uselist=False, cascade="all, delete-orphan")
    owned_restaurants   = relationship("Restaurant", foreign_keys="Restaurant.owner_id",
                                       back_populates="owner")
    added_restaurants   = relationship("Restaurant", foreign_keys="Restaurant.added_by",
                                       back_populates="adder")
    reviews             = relationship("Review",    back_populates="user",
                                       cascade="all, delete-orphan")
    favorites           = relationship("Favorite",  back_populates="user",
                                       cascade="all, delete-orphan")
    conversations       = relationship("ConversationHistory", back_populates="user",
                                       cascade="all, delete-orphan")


class SortPreference(str, enum.Enum):
    rating       = "rating"
    distance     = "distance"
    price_asc    = "price_asc"
    price_desc   = "price_desc"
    most_reviewed = "most_reviewed"


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id                    = Column(Integer, primary_key=True, autoincrement=True, unsigned=True)
    user_id               = Column(Integer, nullable=False, unique=True, index=True)
    cuisine_preferences   = Column(JSON,    nullable=True)
    price_range           = Column(Integer, nullable=True)   # 1-4
    preferred_locations   = Column(JSON,    nullable=True)
    search_radius         = Column(Integer, nullable=True, default=10)  # miles
    dietary_needs         = Column(JSON,    nullable=True)
    ambiance_preferences  = Column(JSON,    nullable=True)
    sort_preference       = Column(Enum(SortPreference), nullable=False,
                                   default=SortPreference.rating)
    updated_at            = Column(TIMESTAMP, nullable=False, server_default=func.now(),
                                   onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="preferences")

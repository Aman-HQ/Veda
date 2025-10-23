"""
User model for authentication and user management.
"""
import uuid
from sqlalchemy import Column, String, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..db.base import Base


class User(Base):
    """User model for storing user information and authentication data."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    name = Column(String(256), nullable=True)
    role = Column(String(50), default="user")
    refresh_tokens = Column(JSON, default=list)  # Store refresh tokens metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )

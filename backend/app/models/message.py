"""
Message model for storing individual messages in conversations.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy.orm import relationship

from ..db.base import Base


class Message(Base):
    """Message model for storing individual messages in conversations."""
    
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("conversations.id", ondelete="CASCADE"), 
        nullable=False
    )
    sender = Column(String(50), nullable=False)  # "user" or "assistant"
    content = Column(TEXT, nullable=False)
    status = Column(String(50), default="sent")  # "sent", "delivered", "error", "incomplete"
    message_metadata = Column(JSON, nullable=True)  # Store additional data like file URLs, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
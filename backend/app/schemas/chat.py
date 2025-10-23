"""
Pydantic schemas for chat-related endpoints.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


# Message Schemas
class MessageBase(BaseModel):
    """Base message schema with common fields."""
    sender: str = Field(..., pattern="^(user|assistant)$", description="Message sender: 'user' or 'assistant'")
    content: str = Field(..., min_length=1, description="Message content")
    status: str = "sent"
    message_metadata: Optional[Dict[str, Any]] = None


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., min_length=1, description="Message content")
    type: str = Field(default="text", pattern="^(text|image|audio)$", description="Message type")
    message_metadata: Optional[Dict[str, Any]] = None


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = None
    status: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None


class Message(MessageBase):
    """Schema for message data returned by API."""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageInDB(MessageBase):
    """Schema for message data stored in database."""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# Conversation Schemas
class ConversationBase(BaseModel):
    """Base conversation schema with common fields."""
    title: Optional[str] = Field(None, max_length=512, description="Conversation title")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, max_length=512, description="Conversation title")


class Conversation(ConversationBase):
    """Schema for conversation data returned by API."""
    id: UUID
    user_id: UUID
    messages_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(Conversation):
    """Schema for conversation with messages included."""
    messages: List[Message] = []
    
    class Config:
        from_attributes = True


class ConversationInDB(ConversationBase):
    """Schema for conversation data stored in database."""
    id: UUID
    user_id: UUID
    messages_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str = Field(..., pattern="^(chunk|done|error|resume)$")
    conversation_id: Optional[UUID] = None
    message_id: Optional[UUID] = None
    data: Optional[str] = None
    message: Optional[Message] = None
    error: Optional[str] = None
    last_message_id: Optional[UUID] = None  # For resume functionality


class ChatStreamChunk(BaseModel):
    """Schema for streaming chat chunks."""
    type: str = "chunk"
    message_id: UUID
    data: str


class ChatStreamDone(BaseModel):
    """Schema for streaming completion."""
    type: str = "done"
    message: Message


class ChatStreamError(BaseModel):
    """Schema for streaming errors."""
    type: str = "error"
    error: str


# File Upload Schemas
class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    url: str
    type: str = Field(..., pattern="^(image|audio)$")
    filename: str
    size: int
    mime_type: str


class ImageUploadRequest(BaseModel):
    """Schema for image upload metadata."""
    filename: str
    mime_type: str
    size: int
    width: Optional[int] = None
    height: Optional[int] = None


class AudioUploadRequest(BaseModel):
    """Schema for audio upload metadata."""
    filename: str
    mime_type: str
    size: int
    duration: Optional[float] = None

"""
Pydantic schemas for request/response validation.
Import all schemas here for easy access.
"""

from .auth import (
    User, UserCreate, UserUpdate, UserInDB,
    Token, TokenData, LoginRequest, RefreshTokenRequest,
    GoogleOAuthRequest, PasswordResetRequest, PasswordResetConfirm
)
from .chat import (
    Message, MessageCreate, MessageUpdate, MessageInDB,
    Conversation, ConversationCreate, ConversationUpdate, 
    ConversationWithMessages, ConversationInDB,
    WebSocketMessage, ChatStreamChunk, ChatStreamDone, ChatStreamError,
    FileUploadResponse, ImageUploadRequest, AudioUploadRequest
)

__all__ = [
    # Auth schemas
    "User", "UserCreate", "UserUpdate", "UserInDB",
    "Token", "TokenData", "LoginRequest", "RefreshTokenRequest",
    "GoogleOAuthRequest", "PasswordResetRequest", "PasswordResetConfirm",
    
    # Chat schemas
    "Message", "MessageCreate", "MessageUpdate", "MessageInDB",
    "Conversation", "ConversationCreate", "ConversationUpdate", 
    "ConversationWithMessages", "ConversationInDB",
    "WebSocketMessage", "ChatStreamChunk", "ChatStreamDone", "ChatStreamError",
    "FileUploadResponse", "ImageUploadRequest", "AudioUploadRequest"
]

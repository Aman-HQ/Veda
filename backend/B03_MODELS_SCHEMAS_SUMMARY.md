# B03 - Models & Schemas (PostgreSQL + SQLAlchemy) - Implementation Summary

## Overview
Successfully implemented comprehensive ORM models and Pydantic schemas for the Veda Healthcare Chatbot backend, following the specifications in `docs/plan.md`.

## Completed Tasks ✅

### 1. ORM Models Created
Created three main SQLAlchemy models with proper relationships and constraints:

#### **User Model** (`app/models/user.py`)
- **Table**: `users`
- **Fields**:
  - `id`: UUID primary key
  - `email`: Unique, indexed string (256 chars)
  - `hashed_password`: Nullable string (for OAuth users)
  - `name`: Optional string (256 chars)
  - `role`: String with default "user"
  - `refresh_tokens`: JSON array for token metadata
  - `created_at`: Timestamp with timezone
- **Relationships**: One-to-many with Conversations (cascade delete)

#### **Conversation Model** (`app/models/conversation.py`)
- **Table**: `conversations`
- **Fields**:
  - `id`: UUID primary key
  - `user_id`: Foreign key to users.id (CASCADE delete)
  - `title`: Optional string (512 chars)
  - `messages_count`: Integer counter (default 0)
  - `created_at`: Timestamp with timezone
- **Relationships**: 
  - Many-to-one with User
  - One-to-many with Messages (cascade delete, ordered by created_at)

#### **Message Model** (`app/models/message.py`)
- **Table**: `messages`
- **Fields**:
  - `id`: UUID primary key
  - `conversation_id`: Foreign key to conversations.id (CASCADE delete)
  - `sender`: String ("user" or "assistant")
  - `content`: TEXT field for message content
  - `status`: String (default "sent")
  - `message_metadata`: JSON field for additional data (renamed from `metadata` to avoid SQLAlchemy conflict)
  - `created_at`: Timestamp with timezone
- **Relationships**: Many-to-one with Conversation

### 2. Pydantic Schemas Created

#### **Authentication Schemas** (`app/schemas/auth.py`)
- `UserBase`, `UserCreate`, `UserUpdate`, `UserInDB`, `User`
- `Token`, `TokenData`, `LoginRequest`, `RefreshTokenRequest`
- `GoogleOAuthRequest`, `PasswordResetRequest`, `PasswordResetConfirm`

#### **Chat Schemas** (`app/schemas/chat.py`)
- **Message schemas**: `MessageBase`, `MessageCreate`, `MessageUpdate`, `Message`, `MessageInDB`
- **Conversation schemas**: `ConversationBase`, `ConversationCreate`, `ConversationUpdate`, `Conversation`, `ConversationWithMessages`, `ConversationInDB`
- **WebSocket schemas**: `WebSocketMessage`, `ChatStreamChunk`, `ChatStreamDone`, `ChatStreamError`
- **File upload schemas**: `FileUploadResponse`, `ImageUploadRequest`, `AudioUploadRequest`

### 3. Database Migration
- Generated and applied migration: `3164f08f586f_add_conversation_and_message_models.py`
- Updated existing tables with new columns and constraints
- All foreign key relationships and indexes created properly

### 4. Dependencies Added
- `email-validator==2.1.1` for Pydantic EmailStr validation

## Key Technical Decisions

### 1. Resolved SQLAlchemy Conflicts
- **Issue**: `metadata` column name conflicted with SQLAlchemy's reserved attribute
- **Solution**: Renamed to `message_metadata` in both model and schemas

### 2. Fixed Pydantic v2 Compatibility
- **Issue**: `regex` parameter deprecated in Pydantic v2
- **Solution**: Updated all Field definitions to use `pattern` instead of `regex`

### 3. Avoided Circular Imports
- **Issue**: Importing models in `base.py` caused circular import errors
- **Solution**: Moved model imports to `alembic/env.py` for autogenerate support only

### 4. Proper Relationship Configuration
- **Cascade deletes**: User deletion removes all conversations and messages
- **Ordering**: Messages ordered by `created_at` in relationships
- **Foreign key constraints**: Proper CASCADE delete on foreign keys

## File Structure Created

```
backend/app/
├── models/
│   ├── __init__.py           # Exports all models
│   ├── user.py              # User ORM model
│   ├── conversation.py      # Conversation ORM model
│   └── message.py           # Message ORM model
├── schemas/
│   ├── __init__.py          # Exports all schemas
│   ├── auth.py              # Authentication schemas
│   └── chat.py              # Chat-related schemas
└── db/
    └── base.py              # SQLAlchemy Base (cleaned up)
```

## Database Schema

### Tables Created/Updated:
1. **users** - User authentication and profile data
2. **conversations** - Chat conversation metadata
3. **messages** - Individual messages in conversations

### Relationships:
- `users` 1:N `conversations` (CASCADE DELETE)
- `conversations` 1:N `messages` (CASCADE DELETE)

### Indexes:
- `users.email` (unique index)
- Foreign key indexes automatically created

## Validation Tests ✅

Created and ran comprehensive validation tests:
- ✅ All models import successfully
- ✅ All model attributes present and correct
- ✅ All schemas import and validate correctly
- ✅ Pydantic validation works for all field types
- ✅ Email validation works with EmailStr
- ✅ Pattern validation works for enums

## API Schema Examples

### User Registration
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

### Message Creation
```json
{
  "content": "Hello, I need help with my health question",
  "type": "text",
  "message_metadata": {
    "client_id": "web-app",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### WebSocket Message
```json
{
  "type": "chunk",
  "conversation_id": "uuid-here",
  "message_id": "uuid-here",
  "data": "Partial response text..."
}
```

## Next Steps
- Ready for **B04 - Auth Endpoints** implementation
- Models and schemas fully prepared for CRUD operations
- Database schema is production-ready
- All relationships and constraints properly configured

## Acceptance Criteria Met ✅

- [x] ORM models map correctly to PostgreSQL
- [x] Basic CRUD operations supported through SQLAlchemy
- [x] Relationships between User, Conversation, and Message work
- [x] Pydantic schemas mirror ORM fields
- [x] UUID primary keys and proper timestamps
- [x] JSON columns for metadata storage
- [x] Foreign key constraints with CASCADE delete
- [x] Alembic migrations generate and apply successfully
- [x] All imports work without circular dependency issues

## Technical Notes

- **UUID Usage**: All primary keys use UUID4 for better distributed system support
- **Timezone Awareness**: All timestamps use `timezone=True` for proper timezone handling
- **JSON Storage**: Flexible metadata storage using PostgreSQL JSON columns
- **Async Ready**: All models compatible with async SQLAlchemy operations
- **Type Safety**: Full type hints and Pydantic validation for API safety

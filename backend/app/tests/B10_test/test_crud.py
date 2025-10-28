"""
B10 Integration Tests - Database CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


@pytest.mark.asyncio
class TestUserCRUD:
    """Test user CRUD operations."""
    
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user = User(
            email="newuser@example.com",
            hashed_password=get_password_hash("password123"),
            name="New User"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.name == "New User"
        assert user.role == "user"  # default role
    
    async def test_read_user(self, db_session: AsyncSession, test_user):
        """Test reading a user."""
        from app.models.user import User
        
        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )
        user = result.scalars().first()
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    async def test_update_user(self, db_session: AsyncSession, test_user):
        """Test updating a user."""
        from app.models.user import User
        
        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )
        user = result.scalars().first()
        
        user.name = "Updated Name"
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.name == "Updated Name"
    
    async def test_delete_user(self, db_session: AsyncSession):
        """Test deleting a user."""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        user = User(
            email="deleteme@example.com",
            hashed_password=get_password_hash("password123"),
            name="Delete Me"
        )
        db_session.add(user)
        await db_session.commit()
        user_id = user.id
        
        await db_session.delete(user)
        await db_session.commit()
        
        result = await db_session.execute(
            select(User).where(User.id == user_id)
        )
        deleted_user = result.scalars().first()
        
        assert deleted_user is None
    
    async def test_user_unique_email(self, db_session: AsyncSession, test_user):
        """Test that email must be unique."""
        from app.models.user import User
        from app.core.security import get_password_hash
        from sqlalchemy.exc import IntegrityError
        
        duplicate_user = User(
            email=test_user.email,  # Same email
            hashed_password=get_password_hash("password123"),
            name="Duplicate"
        )
        db_session.add(duplicate_user)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


@pytest.mark.asyncio
class TestConversationCRUD:
    """Test conversation CRUD operations."""
    
    async def test_create_conversation(self, db_session: AsyncSession, test_user):
        """Test creating a conversation."""
        from app.models.conversation import Conversation
        
        conversation = Conversation(
            user_id=test_user.id,
            title="Test Conversation"
        )
        db_session.add(conversation)
        await db_session.commit()
        await db_session.refresh(conversation)
        
        assert conversation.id is not None
        assert conversation.user_id == test_user.id
        assert conversation.title == "Test Conversation"
        assert conversation.messages_count == 0
    
    async def test_list_user_conversations(self, db_session: AsyncSession, test_user):
        """Test listing conversations for a user."""
        from app.models.conversation import Conversation
        
        # Create multiple conversations
        for i in range(3):
            conv = Conversation(
                user_id=test_user.id,
                title=f"Conversation {i+1}"
            )
            db_session.add(conv)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Conversation).where(Conversation.user_id == test_user.id)
        )
        conversations = result.scalars().all()
        
        assert len(conversations) >= 3
    
    async def test_update_conversation(self, db_session: AsyncSession, test_conversation):
        """Test updating a conversation."""
        from app.models.conversation import Conversation
        
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == test_conversation.id)
        )
        conv = result.scalars().first()
        
        conv.title = "Updated Title"
        await db_session.commit()
        await db_session.refresh(conv)
        
        assert conv.title == "Updated Title"
    
    async def test_delete_conversation(self, db_session: AsyncSession, test_user):
        """Test deleting a conversation."""
        from app.models.conversation import Conversation
        
        conv = Conversation(
            user_id=test_user.id,
            title="Delete Me"
        )
        db_session.add(conv)
        await db_session.commit()
        conv_id = conv.id
        
        await db_session.delete(conv)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        deleted_conv = result.scalars().first()
        
        assert deleted_conv is None
    
    async def test_conversation_cascade_delete(self, db_session: AsyncSession, test_user):
        """Test that deleting a user cascades to conversations."""
        from app.models.user import User
        from app.models.conversation import Conversation
        from app.core.security import get_password_hash
        
        # Create user with conversation
        user = User(
            email="cascade@example.com",
            hashed_password=get_password_hash("password123"),
            name="Cascade User"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        conv = Conversation(user_id=user.id, title="Test")
        db_session.add(conv)
        await db_session.commit()
        conv_id = conv.id
        
        # Delete user
        await db_session.delete(user)
        await db_session.commit()
        
        # Conversation should be deleted
        result = await db_session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        deleted_conv = result.scalars().first()
        
        assert deleted_conv is None


@pytest.mark.asyncio
class TestMessageCRUD:
    """Test message CRUD operations."""
    
    async def test_create_message(self, db_session: AsyncSession, test_conversation):
        """Test creating a message."""
        from app.models.message import Message
        
        message = Message(
            conversation_id=test_conversation.id,
            sender="user",
            content="Test message"
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.id is not None
        assert message.conversation_id == test_conversation.id
        assert message.sender == "user"
        assert message.content == "Test message"
        assert message.status == "sent"
    
    async def test_list_conversation_messages(self, db_session: AsyncSession, test_conversation):
        """Test listing messages in a conversation."""
        from app.models.message import Message
        
        # Create multiple messages
        for i in range(5):
            msg = Message(
                conversation_id=test_conversation.id,
                sender="user" if i % 2 == 0 else "assistant",
                content=f"Message {i+1}"
            )
            db_session.add(msg)
        await db_session.commit()
        
        result = await db_session.execute(
            select(Message)
            .where(Message.conversation_id == test_conversation.id)
            .order_by(Message.created_at)
        )
        messages = result.scalars().all()
        
        assert len(messages) >= 5
    
    async def test_update_message_status(self, db_session: AsyncSession, test_message):
        """Test updating message status."""
        from app.models.message import Message
        
        result = await db_session.execute(
            select(Message).where(Message.id == test_message.id)
        )
        msg = result.scalars().first()
        
        msg.status = "delivered"
        await db_session.commit()
        await db_session.refresh(msg)
        
        assert msg.status == "delivered"
    
    async def test_message_with_metadata(self, db_session: AsyncSession, test_conversation):
        """Test creating message with metadata."""
        from app.models.message import Message
        
        metadata = {
            "flagged": True,
            "keywords": ["test", "example"],
            "model": "medgemma-4b-it"
        }
        
        message = Message(
            conversation_id=test_conversation.id,
            sender="assistant",
            content="Response with metadata",
            metadata=metadata
        )
        db_session.add(message)
        await db_session.commit()
        await db_session.refresh(message)
        
        assert message.metadata is not None
        assert message.metadata["flagged"] is True
        assert "keywords" in message.metadata
    
    async def test_message_cascade_delete(self, db_session: AsyncSession, test_user):
        """Test that deleting a conversation cascades to messages."""
        from app.models.conversation import Conversation
        from app.models.message import Message
        
        # Create conversation with messages
        conv = Conversation(user_id=test_user.id, title="Test")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)
        
        msg = Message(
            conversation_id=conv.id,
            sender="user",
            content="Test"
        )
        db_session.add(msg)
        await db_session.commit()
        msg_id = msg.id
        
        # Delete conversation
        await db_session.delete(conv)
        await db_session.commit()
        
        # Message should be deleted
        result = await db_session.execute(
            select(Message).where(Message.id == msg_id)
        )
        deleted_msg = result.scalars().first()
        
        assert deleted_msg is None

"""
CRUD operations for Conversation model.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.conversation import Conversation
from ..models.message import Message
from ..schemas.chat import ConversationCreate, ConversationUpdate


class ConversationCRUD:
    """CRUD operations for Conversation model."""

    @staticmethod
    async def get_by_id(db: AsyncSession, conversation_id: UUID, user_id: UUID) -> Optional[Conversation]:
        """
        Get conversation by ID, ensuring it belongs to the user.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID for ownership verification
            
        Returns:
            Conversation if found and owned by user, None otherwise
        """
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_with_messages(
        db: AsyncSession, 
        conversation_id: UUID, 
        user_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> Optional[Conversation]:
        """
        Get conversation with messages, ensuring it belongs to the user.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID for ownership verification
            limit: Maximum number of messages to load
            offset: Number of messages to skip
            
        Returns:
            Conversation with messages if found and owned by user
        """
        # First get the conversation
        conversation = await ConversationCRUD.get_by_id(db, conversation_id, user_id)
        if not conversation:
            return None
        
        # Then get messages separately with pagination
        messages_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        messages = messages_result.scalars().all()
        
        # Manually set the messages relationship
        conversation.messages = messages
        return conversation

    @staticmethod
    async def list_by_user(
        db: AsyncSession, 
        user_id: UUID, 
        skip: int = 0, 
        limit: int = 20
    ) -> List[Conversation]:
        """
        List conversations for a user, ordered by most recent.
        
        Args:
            db: Database session
            user_id: User UUID
            skip: Number of conversations to skip
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversations ordered by creation date (newest first)
        """
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession, 
        conversation_create: ConversationCreate, 
        user_id: UUID
    ) -> Conversation:
        """
        Create a new conversation.
        
        Args:
            db: Database session
            conversation_create: Conversation creation data
            user_id: User UUID
            
        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            title=conversation_create.title,
            messages_count=0
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def update(
        db: AsyncSession, 
        conversation: Conversation, 
        conversation_update: ConversationUpdate
    ) -> Conversation:
        """
        Update conversation information.
        
        Args:
            db: Database session
            conversation: Conversation to update
            conversation_update: Update data
            
        Returns:
            Updated conversation
        """
        update_data = conversation_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        await db.commit()
        await db.refresh(conversation)
        return conversation

    @staticmethod
    async def delete(db: AsyncSession, conversation: Conversation) -> bool:
        """
        Delete a conversation and all its messages (cascade).
        
        Args:
            db: Database session
            conversation: Conversation to delete
            
        Returns:
            True if deleted successfully
        """
        await db.delete(conversation)
        await db.commit()
        return True

    @staticmethod
    async def increment_message_count(
        db: AsyncSession, 
        conversation_id: UUID, 
        increment: int = 1
    ) -> bool:
        """
        Increment the message count for a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            increment: Number to increment by (default 1)
            
        Returns:
            True if updated successfully
        """
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()
        
        if conversation:
            conversation.messages_count += increment
            await db.commit()
            return True
        return False

    @staticmethod
    async def get_message_count(db: AsyncSession, conversation_id: UUID) -> int:
        """
        Get the actual message count for a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            
        Returns:
            Number of messages in the conversation
        """
        result = await db.execute(
            select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def update_message_count(db: AsyncSession, conversation_id: UUID) -> bool:
        """
        Update the message count to match actual messages in the conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            
        Returns:
            True if updated successfully
        """
        actual_count = await ConversationCRUD.get_message_count(db, conversation_id)
        
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalars().first()
        
        if conversation:
            conversation.messages_count = actual_count
            await db.commit()
            return True
        return False

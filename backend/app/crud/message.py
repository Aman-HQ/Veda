"""
CRUD operations for Message model.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.message import Message
from ..models.conversation import Conversation
from ..schemas.chat import MessageCreate, MessageUpdate


class MessageCRUD:
    """CRUD operations for Message model."""

    @staticmethod
    async def get_by_id(db: AsyncSession, message_id: UUID) -> Optional[Message]:
        """
        Get message by ID.
        
        Args:
            db: Database session
            message_id: Message UUID
            
        Returns:
            Message if found, None otherwise
        """
        result = await db.execute(select(Message).where(Message.id == message_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_id_with_conversation(
        db: AsyncSession, 
        message_id: UUID, 
        user_id: UUID
    ) -> Optional[Message]:
        """
        Get message by ID with conversation, ensuring user owns the conversation.
        
        Args:
            db: Database session
            message_id: Message UUID
            user_id: User UUID for ownership verification
            
        Returns:
            Message with conversation if found and user owns conversation
        """
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(
                Message.id == message_id,
                Conversation.user_id == user_id
            )
            .options(selectinload(Message.conversation))
        )
        return result.scalars().first()

    @staticmethod
    async def list_by_conversation(
        db: AsyncSession, 
        conversation_id: UUID, 
        user_id: UUID,
        skip: int = 0, 
        limit: int = 50,
        order_desc: bool = False
    ) -> List[Message]:
        """
        List messages in a conversation, ensuring user owns the conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID for ownership verification
            skip: Number of messages to skip
            limit: Maximum number of messages to return
            order_desc: If True, order by newest first; if False, oldest first
            
        Returns:
            List of messages in the conversation
        """
        # First verify user owns the conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = conv_result.scalars().first()
        
        if not conversation:
            return []
        
        # Get messages
        query = select(Message).where(Message.conversation_id == conversation_id)
        
        if order_desc:
            query = query.order_by(Message.created_at.desc())
        else:
            query = query.order_by(Message.created_at.asc())
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create(
        db: AsyncSession, 
        message_create: MessageCreate, 
        conversation_id: UUID,
        sender: str = "user"
    ) -> Message:
        """
        Create a new message in a conversation.
        
        Args:
            db: Database session
            message_create: Message creation data
            conversation_id: Conversation UUID
            sender: Message sender ("user" or "assistant")
            
        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            sender=sender,
            content=message_create.content,
            status="sent",
            message_metadata=message_create.message_metadata or {}
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def create_with_transaction(
        db: AsyncSession,
        conversation_id: UUID,
        sender: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "sent"
    ) -> Message:
        """
        Create a message with explicit transaction handling.
        This follows the pattern shown in the plan.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            sender: Message sender ("user" or "assistant")
            content: Message content
            metadata: Optional message metadata
            status: Message status
            
        Returns:
            Created message
        """
        async with db.begin():
            message = Message(
                conversation_id=conversation_id,
                sender=sender,
                content=content,
                status=status,
                message_metadata=metadata or {}
            )
            db.add(message)
        
        # After context, transaction is committed
        await db.refresh(message)
        return message

    @staticmethod
    async def update(
        db: AsyncSession, 
        message: Message, 
        message_update: MessageUpdate
    ) -> Message:
        """
        Update message information.
        
        Args:
            db: Database session
            message: Message to update
            message_update: Update data
            
        Returns:
            Updated message
        """
        update_data = message_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(message, field, value)
        
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def update_status(
        db: AsyncSession, 
        message_id: UUID, 
        status: str
    ) -> Optional[Message]:
        """
        Update message status.
        
        Args:
            db: Database session
            message_id: Message UUID
            status: New status
            
        Returns:
            Updated message if found, None otherwise
        """
        result = await db.execute(select(Message).where(Message.id == message_id))
        message = result.scalars().first()
        
        if message:
            message.status = status
            await db.commit()
            await db.refresh(message)
            return message
        return None

    @staticmethod
    async def delete(db: AsyncSession, message: Message) -> bool:
        """
        Delete a message.
        
        Args:
            db: Database session
            message: Message to delete
            
        Returns:
            True if deleted successfully
        """
        await db.delete(message)
        await db.commit()
        return True

    @staticmethod
    async def delete_by_conversation(
        db: AsyncSession, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> int:
        """
        Delete all messages in a conversation, ensuring user owns the conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            user_id: User UUID for ownership verification
            
        Returns:
            Number of messages deleted
        """
        # First verify user owns the conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conversation = conv_result.scalars().first()
        
        if not conversation:
            return 0
        
        # Delete messages
        result = await db.execute(
            delete(Message).where(Message.conversation_id == conversation_id)
        )
        await db.commit()
        
        return result.rowcount

    @staticmethod
    async def get_latest_by_conversation(
        db: AsyncSession, 
        conversation_id: UUID, 
        limit: int = 1
    ) -> List[Message]:
        """
        Get the latest messages from a conversation.
        
        Args:
            db: Database session
            conversation_id: Conversation UUID
            limit: Number of latest messages to return
            
        Returns:
            List of latest messages
        """
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def search_messages(
        db: AsyncSession,
        user_id: UUID,
        search_term: str,
        limit: int = 20
    ) -> List[Message]:
        """
        Search messages by content across all user's conversations.
        
        Args:
            db: Database session
            user_id: User UUID
            search_term: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching messages
        """
        result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(
                Conversation.user_id == user_id,
                Message.content.ilike(f"%{search_term}%")
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
            .options(selectinload(Message.conversation))
        )
        return result.scalars().all()

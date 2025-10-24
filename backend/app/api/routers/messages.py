"""
API endpoints for message management.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...crud.message import MessageCRUD
from ...crud.conversation import ConversationCRUD
from ...schemas.chat import (
    Message, 
    MessageCreate, 
    MessageUpdate
)
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("/{conversation_id}/messages", response_model=List[Message])
async def list_messages(
    conversation_id: UUID,
    skip: int = Query(0, ge=0, description="Number of messages to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    order_desc: bool = Query(False, description="Order by newest first if True"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages from a conversation.
    
    Args:
        conversation_id: Conversation UUID
        skip: Number of messages to skip for pagination
        limit: Maximum number of messages to return
        order_desc: If True, order by newest first; if False, oldest first
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of messages in the conversation
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
    messages = await MessageCRUD.list_by_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        order_desc=order_desc
    )
    
    # If no messages returned, verify the conversation exists and is owned by user
    if not messages:
        conversation = await ConversationCRUD.get_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    
    return messages


@router.post("/{conversation_id}/messages", response_model=Message, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: UUID,
    message_create: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new message in a conversation.
    
    Args:
        conversation_id: Conversation UUID
        message_create: Message creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created message
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
    # Verify conversation exists and is owned by user
    conversation = await ConversationCRUD.get_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Create the message
    message = await MessageCRUD.create(
        db=db,
        message_create=message_create,
        conversation_id=conversation_id,
        sender="user"  # Default to user, can be overridden for assistant messages
    )
    
    # Increment conversation message count
    await ConversationCRUD.increment_message_count(db, conversation_id, 1)
    
    return message


@router.get("/messages/{message_id}", response_model=Message)
async def get_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific message by ID.
    
    Args:
        message_id: Message UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Message details
        
    Raises:
        HTTPException: If message not found or not owned by user
    """
    message = await MessageCRUD.get_by_id_with_conversation(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    return message


@router.put("/messages/{message_id}", response_model=Message)
async def update_message(
    message_id: UUID,
    message_update: MessageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a message.
    
    Args:
        message_id: Message UUID
        message_update: Message update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated message
        
    Raises:
        HTTPException: If message not found or not owned by user
    """
    message = await MessageCRUD.get_by_id_with_conversation(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    updated_message = await MessageCRUD.update(
        db=db,
        message=message,
        message_update=message_update
    )
    
    return updated_message


@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: UUID,
    status_value: str = Query(..., description="New message status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update message status.
    
    Args:
        message_id: Message UUID
        status_value: New status value
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If message not found or not owned by user
    """
    # Verify message exists and user owns the conversation
    message = await MessageCRUD.get_by_id_with_conversation(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    updated_message = await MessageCRUD.update_status(
        db=db,
        message_id=message_id,
        status=status_value
    )
    
    if not updated_message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message status"
        )
    
    return {"message": "Status updated successfully", "new_status": status_value}


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a message.
    
    Args:
        message_id: Message UUID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If message not found or not owned by user
    """
    message = await MessageCRUD.get_by_id_with_conversation(
        db=db,
        message_id=message_id,
        user_id=current_user.id
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    conversation_id = message.conversation_id
    
    # Delete the message
    await MessageCRUD.delete(db=db, message=message)
    
    # Decrement conversation message count
    await ConversationCRUD.increment_message_count(db, conversation_id, -1)


@router.delete("/{conversation_id}/messages", response_model=dict)
async def delete_all_messages(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete all messages in a conversation.
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Number of messages deleted
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
    deleted_count = await MessageCRUD.delete_by_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if deleted_count == 0:
        # Check if conversation exists
        conversation = await ConversationCRUD.get_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    
    # Reset conversation message count
    await ConversationCRUD.update_message_count(db, conversation_id)
    
    return {
        "conversation_id": str(conversation_id),
        "deleted_count": deleted_count,
        "message": f"Deleted {deleted_count} messages"
    }


@router.get("/{conversation_id}/messages/latest", response_model=List[Message])
async def get_latest_messages(
    conversation_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Number of latest messages to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the latest messages from a conversation.
    
    Args:
        conversation_id: Conversation UUID
        limit: Number of latest messages to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of latest messages
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
    # Verify conversation exists and is owned by user
    conversation = await ConversationCRUD.get_by_id(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = await MessageCRUD.get_latest_by_conversation(
        db=db,
        conversation_id=conversation_id,
        limit=limit
    )
    
    return messages


@router.get("/search", response_model=List[Message])
async def search_messages(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Search messages across all user's conversations.
    
    Args:
        q: Search term
        limit: Maximum number of results
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of matching messages
    """
    messages = await MessageCRUD.search_messages(
        db=db,
        user_id=current_user.id,
        search_term=q,
        limit=limit
    )
    
    return messages

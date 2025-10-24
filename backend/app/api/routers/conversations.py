"""
API endpoints for conversation management.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...crud.conversation import ConversationCRUD
from ...crud.message import MessageCRUD
from ...schemas.chat import (
    Conversation, 
    ConversationCreate, 
    ConversationUpdate,
    ConversationWithMessages
)
from ...api.deps import get_current_user
from ...models.user import User

router = APIRouter()


@router.get("/", response_model=List[Conversation])
async def list_conversations(
    skip: int = Query(0, ge=0, description="Number of conversations to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of conversations to return"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of conversations for the current user.
    
    Args:
        skip: Number of conversations to skip for pagination
        limit: Maximum number of conversations to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List of conversations ordered by creation date (newest first)
    """
    conversations = await ConversationCRUD.list_by_user(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return conversations


@router.post("/", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_create: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new conversation for the current user.
    
    Args:
        conversation_create: Conversation creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Created conversation
    """
    conversation = await ConversationCRUD.create(
        db=db,
        conversation_create=conversation_create,
        user_id=current_user.id
    )
    return conversation


@router.get("/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific conversation by ID.
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Conversation details
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
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
    
    return conversation


@router.get("/{conversation_id}/with-messages", response_model=ConversationWithMessages)
async def get_conversation_with_messages(
    conversation_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a conversation with its messages.
    
    Args:
        conversation_id: Conversation UUID
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Conversation with messages
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
    conversation_data = await ConversationCRUD.get_with_messages(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )
    
    if not conversation_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation_data


@router.put("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: UUID,
    conversation_update: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a conversation.
    
    Args:
        conversation_id: Conversation UUID
        conversation_update: Conversation update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated conversation
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
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
    
    updated_conversation = await ConversationCRUD.update(
        db=db,
        conversation=conversation,
        conversation_update=conversation_update
    )
    
    return updated_conversation


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages.
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
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
    
    await ConversationCRUD.delete(db=db, conversation=conversation)


@router.post("/{conversation_id}/update-message-count", response_model=dict)
async def update_conversation_message_count(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the message count for a conversation to match actual messages.
    This is a utility endpoint for data consistency.
    
    Args:
        conversation_id: Conversation UUID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Updated message count information
        
    Raises:
        HTTPException: If conversation not found or not owned by user
    """
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
    
    # Get actual message count
    actual_count = await ConversationCRUD.get_message_count(db, conversation_id)
    old_count = conversation.messages_count
    
    # Update the count
    success = await ConversationCRUD.update_message_count(db, conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message count"
        )
    
    return {
        "conversation_id": str(conversation_id),
        "old_count": old_count,
        "new_count": actual_count,
        "updated": True
    }

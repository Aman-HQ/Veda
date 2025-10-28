"""
API endpoints for message management.
"""
import logging
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
from ...services.chat_manager import ChatManager
from ...services.moderation import moderate_content

router = APIRouter()
logger = logging.getLogger(__name__)


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
    
    # Moderate content before creating message
    moderation_result = moderate_content(
        message_create.content,
        context={
            "user_id": str(current_user.id),
            "conversation_id": str(conversation_id),
            "endpoint": "create_message"
        }
    )
    
    # Block high-severity content
    if not moderation_result.is_safe and moderation_result.action == "block":
        logger.warning(
            f"Message blocked by moderation: user={current_user.id}, "
            f"severity={moderation_result.severity}, "
            f"keywords={moderation_result.matched_keywords}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Content blocked by moderation",
                "severity": moderation_result.severity,
                "reason": moderation_result.message,
                "matched_keywords": moderation_result.matched_keywords
            }
        )
    
    # Log flagged content (medium severity) but allow it
    if moderation_result.action == "flag":
        logger.info(
            f"Message flagged by moderation: user={current_user.id}, "
            f"severity={moderation_result.severity}, "
            f"keywords={moderation_result.matched_keywords}"
        )
    
    # Create the message with atomic count increment
    message = await MessageCRUD.create_with_count_increment(
        db=db,
        message_create=message_create,
        conversation_id=conversation_id,
        sender="user"  # Default to user, can be overridden for assistant messages
    )
    
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
    
    # Delete the message with atomic count decrement
    await MessageCRUD.delete_with_count_decrement(db=db, message=message)


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


@router.post("/{conversation_id}/messages/chat", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_chat_message(
    conversation_id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a chat message and get AI response (non-streaming).
    
    This endpoint handles the full chat pipeline including:
    - Text, audio, and image input processing
    - AI response generation via LLM provider
    - Message persistence with healthcare disclaimer
    
    Args:
        conversation_id: Conversation UUID
        payload: Message payload with text, audio, or image data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        Chat response with user and assistant message details
        
    Raises:
        HTTPException: If conversation not found or processing fails
    """
    try:
        # Extract payload data
        text = payload.get("text")
        audio = payload.get("audio")  # base64 encoded audio data
        image = payload.get("image")  # base64 encoded image data
        client_message_id = payload.get("client_message_id")
        
        # Validate input
        if not any([text, audio, image]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of text, audio, or image must be provided"
            )
        
        # Convert base64 data to bytes if provided
        audio_bytes = None
        image_bytes = None
        
        if audio:
            import base64
            try:
                audio_bytes = base64.b64decode(audio)
            except (ValueError, base64.binascii.Error) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid audio data format"
                ) from e
        
        if image:
            import base64
            try:
                image_bytes = base64.b64decode(image)
            except (ValueError, base64.binascii.Error) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid image data format"
                ) from e
        
        # Create chat manager and process message
        chat_manager = ChatManager(db)
        
        result = await chat_manager.handle_user_message(
            conversation_id=str(conversation_id),
            user_id=str(current_user.id),
            text=text,
            audio=audio_bytes,
            image=image_bytes,
            client_message_id=client_message_id
        )
        
        return {
            "success": True,
            "user_message_id": result["user_message_id"],
            "assistant_message_id": result["assistant_message_id"],
            "response": result["response"],
            "conversation_id": result["conversation_id"],
            "message": "Chat message processed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat processing failed. Please try again."
        ) from e


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

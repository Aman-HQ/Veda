"""
WebSocket router for real-time chat streaming.
Handles WebSocket connections for conversation streaming with authentication.
"""

import json
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.session import get_db
from ...core.security import verify_token
from ...crud.user import UserCRUD
from ...crud.conversation import ConversationCRUD
from ...services.chat_manager import ChatManager, WebSocketStreamer, stream_cache
from ...models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, conversation_id: str, user_id: str):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        connection_key = f"{user_id}:{conversation_id}"
        self.active_connections[connection_key] = websocket
        logger.info(f"WebSocket connected: {connection_key}")
        
    def disconnect(self, conversation_id: str, user_id: str):
        """Remove WebSocket connection."""
        connection_key = f"{user_id}:{conversation_id}"
        if connection_key in self.active_connections:
            del self.active_connections[connection_key]
            logger.info(f"WebSocket disconnected: {connection_key}")
            
    async def send_personal_message(self, message: dict, conversation_id: str, user_id: str):
        """Send message to specific user's WebSocket."""
        connection_key = f"{user_id}:{conversation_id}"
        if connection_key in self.active_connections:
            websocket = self.active_connections[connection_key]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {connection_key}: {e}")
                self.disconnect(conversation_id, user_id)


# Global connection manager
manager = ConnectionManager()


async def get_current_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate user from JWT token for WebSocket connection.
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    try:
        # Verify the token
        payload = verify_token(token, token_type="access")
        if payload is None:
            return None
        
        # Extract user ID from token
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = UUID(user_id_str)
        
        # Get user from database
        user = await UserCRUD.get_by_id(db, user_id)
        return user
        
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        return None


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time chat streaming.
    
    URL: ws://host/ws/conversations/{conversation_id}?token=<JWT>
    
    Protocol:
    - Client sends: {"type": "message", "text": "...", "client_message_id": "..."}
    - Server sends: {"type": "chunk", "messageId": "...", "data": "..."}
    - Server sends: {"type": "done", "message": {...}}
    - Server sends: {"type": "error", "error": "..."}
    - Client sends: {"type": "resume", "conversationId": "...", "lastMessageId": "..."}
    """
    
    # Authenticate user
    user = await get_current_user_from_token(token, db)
    if not user:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Verify conversation access
    try:
        conversation = await ConversationCRUD.get_by_id(db, conversation_id)
        if not conversation or str(conversation.user_id) != str(user.id):
            await websocket.close(code=4003, reason="Conversation not found or access denied")
            return
    except Exception as e:
        logger.error(f"Conversation verification error: {e}")
        await websocket.close(code=4000, reason="Server error")
        return
    
    # Connect WebSocket
    await manager.connect(websocket, conversation_id, str(user.id))
    
    # Create chat manager and streamer
    chat_manager = ChatManager(db)
    ws_streamer = WebSocketStreamer(websocket, conversation_id)
    
    try:
        while True:
            # Wait for client message
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
            except json.JSONDecodeError:
                await ws_streamer.send_error("Invalid JSON format")
                continue
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break
            
            # Handle different message types
            message_type = message.get("type")
            
            if message_type == "message":
                # Handle new user message
                await handle_user_message(
                    message=message,
                    chat_manager=chat_manager,
                    ws_streamer=ws_streamer,
                    conversation_id=conversation_id,
                    user_id=str(user.id)
                )
                
            elif message_type == "resume":
                # Handle connection resume
                await handle_resume_request(
                    message=message,
                    ws_streamer=ws_streamer,
                    conversation_id=conversation_id
                )
                
            elif message_type == "ping":
                # Handle ping for connection keepalive
                await websocket.send_json({"type": "pong"})
                
            else:
                await ws_streamer.send_error(f"Unknown message type: {message_type}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected normally: {user.id}:{conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(conversation_id, str(user.id))


async def handle_user_message(
    message: Dict[str, Any],
    chat_manager: ChatManager,
    ws_streamer: WebSocketStreamer,
    conversation_id: str,
    user_id: str
):
    """Handle incoming user message via WebSocket."""
    
    try:
        # Extract message data
        text = message.get("text")
        client_message_id = message.get("client_message_id")
        
        # Validate input
        if not text:
            await ws_streamer.send_error("Message text is required")
            return
        
        # Process message through chat manager
        result = await chat_manager.handle_user_message(
            conversation_id=conversation_id,
            user_id=user_id,
            text=text,
            ws_streamer=ws_streamer,
            client_message_id=client_message_id
        )
        
        # Handle duplicate message
        if result.get("duplicate"):
            await ws_streamer.send_error("Duplicate message ignored")
            return
            
        logger.info(f"Message processed successfully: {result.get('user_message_id')}")
        
    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        await ws_streamer.send_error(f"Message processing failed: {str(e)}")


async def handle_resume_request(
    message: Dict[str, Any],
    ws_streamer: WebSocketStreamer,
    conversation_id: str
):
    """Handle WebSocket reconnection and resume request."""
    
    try:
        last_message_id = message.get("lastMessageId")
        
        # Check if we have cached content for resumption
        if last_message_id:
            cached_content = stream_cache.get_stream(conversation_id, last_message_id)
            if cached_content:
                # Resume streaming from cached content
                await ws_streamer.send_chunk(last_message_id, cached_content)
                await ws_streamer.send_done(last_message_id, cached_content)
                logger.info(f"Resumed stream from cache: {last_message_id}")
                return
        
        # Send resume acknowledgment
        await ws_streamer.websocket.send_json({
            "type": "resume_ack",
            "conversationId": conversation_id,
            "message": "Connection resumed successfully"
        })
        
        logger.info(f"WebSocket resumed: {conversation_id}")
        
    except Exception as e:
        logger.error(f"Error handling resume request: {e}")
        await ws_streamer.send_error("Resume failed")


# Background task to cleanup expired cache entries
async def cleanup_expired_cache():
    """Background task to clean up expired stream cache entries."""
    while True:
        try:
            stream_cache.cleanup_expired()
            await asyncio.sleep(60)  # Run every minute
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(60)


# Function to start background cleanup task
def start_cleanup_task():
    """Start the cleanup task if there's a running event loop."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(cleanup_expired_cache())
    except RuntimeError:
        # No running event loop, task will be started when the app starts
        pass

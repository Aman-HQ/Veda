"""
Chat Manager service for handling conversation flow and WebSocket streaming.
Manages message persistence and coordinates with LLM provider.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from .llm_provider import LLMProvider
from ..models.conversation import Conversation
from ..models.message import Message
from ..models.user import User
from ..crud.message import MessageCRUD
from ..crud.conversation import ConversationCRUD
import logging

logger = logging.getLogger(__name__)


class WebSocketStreamer:
    """Helper class to handle WebSocket streaming protocol."""
    
    def __init__(self, websocket, conversation_id: str):
        self.websocket = websocket
        self.conversation_id = conversation_id
        self.message_buffer = ""
        
    async def send_chunk(self, message_id: str, chunk: str):
        """Send a chunk of the streaming response."""
        try:
            await self.websocket.send_json({
                "type": "chunk",
                "messageId": message_id,
                "conversationId": self.conversation_id,
                "data": chunk
            })
            self.message_buffer += chunk
        except Exception as e:
            logger.error(f"Error sending chunk: {e}")
            
    async def send_done(self, message_id: str, full_message: str):
        """Send completion signal with full message."""
        try:
            await self.websocket.send_json({
                "type": "done",
                "messageId": message_id,
                "conversationId": self.conversation_id,
                "message": {
                    "id": message_id,
                    "content": full_message,
                    "sender": "assistant",
                    "timestamp": datetime.utcnow().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error sending done: {e}")
            
    async def send_error(self, error_message: str):
        """Send error message."""
        try:
            await self.websocket.send_json({
                "type": "error",
                "conversationId": self.conversation_id,
                "error": error_message
            })
        except Exception as e:
            logger.error(f"Error sending error: {e}")


class ChatManager:
    """
    Manages chat conversations, message persistence, and streaming.
    """
    
    def __init__(self, db: AsyncSession, provider: Optional[LLMProvider] = None):
        self.db = db
        self.provider = provider or LLMProvider()
        
    async def handle_user_message(
        self,
        conversation_id: str,
        user_id: str,
        text: Optional[str] = None,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None,
        ws_streamer: Optional[WebSocketStreamer] = None,
        client_message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming user message and generate response.
        
        Args:
            conversation_id: ID of the conversation
            user_id: ID of the user sending the message
            text: Text content of the message
            audio: Audio data (for voice input)
            image: Image data (for image input)
            ws_streamer: WebSocket streamer for real-time responses
            client_message_id: Client-provided message ID for idempotency
            
        Returns:
            Dictionary with response details
        """
        try:
            # Validate conversation exists and user has access
            conversation = await ConversationCRUD.get_by_id(self.db, conversation_id)
            if not conversation or str(conversation.user_id) != str(user_id):
                error_msg = "Conversation not found or access denied"
                if ws_streamer:
                    await ws_streamer.send_error(error_msg)
                raise ValueError(error_msg)
            
            # Check for duplicate message (idempotency)
            if client_message_id:
                existing_message = await self._check_duplicate_message(conversation_id, client_message_id)
                if existing_message:
                    logger.info(f"Duplicate message ignored: {client_message_id}")
                    return {"message_id": str(existing_message.id), "duplicate": True}
            
            # Persist user message
            user_message = await self._create_user_message(
                conversation_id=conversation_id,
                text=text,
                audio=audio,
                image=image,
                client_message_id=client_message_id
            )
            
            # Generate assistant response
            if ws_streamer:
                # Streaming response
                assistant_message_id = str(uuid.uuid4())
                response_content = await self._handle_streaming_response(
                    conversation_id=conversation_id,
                    user_message=user_message,
                    ws_streamer=ws_streamer,
                    assistant_message_id=assistant_message_id,
                    text=text,
                    audio=audio,
                    image=image
                )
            else:
                # Non-streaming response
                response_content = await self.provider.process_pipeline(
                    text=text,
                    audio=audio,
                    image=image
                )
                
                # Persist assistant message
                assistant_message = await self._create_assistant_message(
                    conversation_id=conversation_id,
                    content=response_content
                )
                assistant_message_id = str(assistant_message.id)
            
            # Update conversation metadata
            await self._update_conversation_stats(conversation_id)
            
            return {
                "user_message_id": str(user_message.id),
                "assistant_message_id": assistant_message_id,
                "response": response_content,
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            if ws_streamer:
                await ws_streamer.send_error(f"Processing error: {str(e)}")
            raise
    
    async def _handle_streaming_response(
        self,
        conversation_id: str,
        user_message: Message,
        ws_streamer: WebSocketStreamer,
        assistant_message_id: str,
        text: Optional[str] = None,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None
    ) -> str:
        """Handle streaming response generation and persistence."""
        
        full_response = ""
        
        try:
            # Stream response chunks
            async for chunk in self.provider.process_pipeline_stream(
                text=text,
                audio=audio,
                image=image
            ):
                await ws_streamer.send_chunk(assistant_message_id, chunk)
                full_response += chunk
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
            
            # Send completion signal
            await ws_streamer.send_done(assistant_message_id, full_response)
            
            # Persist the complete assistant message
            assistant_message = await self._create_assistant_message(
                conversation_id=conversation_id,
                content=full_response,
                message_id=assistant_message_id
            )
            
            return full_response
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_msg = "Stream interrupted due to technical difficulties"
            await ws_streamer.send_error(error_msg)
            
            # Save partial message with error flag
            if full_response:
                await self._create_assistant_message(
                    conversation_id=conversation_id,
                    content=full_response + "\n\n[Response incomplete due to technical error]",
                    message_id=assistant_message_id,
                    status="incomplete"
                )
            
            raise
    
    async def _create_user_message(
        self,
        conversation_id: str,
        text: Optional[str] = None,
        audio: Optional[bytes] = None,
        image: Optional[bytes] = None,
        client_message_id: Optional[str] = None
    ) -> Message:
        """Create and persist user message."""
        
        # Determine message content and metadata
        content = text or ""
        metadata = {}
        
        if audio:
            metadata["has_audio"] = True
            metadata["audio_size"] = len(audio)
            content = content or "[Voice message]"
            
        if image:
            metadata["has_image"] = True
            metadata["image_size"] = len(image)
            content = content or "[Image message]"
            
        if client_message_id:
            metadata["client_message_id"] = client_message_id
        
        # Create message
        message = Message(
            conversation_id=uuid.UUID(conversation_id),
            sender="user",
            content=content,
            message_metadata=metadata,
            status="sent"
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(f"User message created: {message.id}")
        return message
    
    async def _create_assistant_message(
        self,
        conversation_id: str,
        content: str,
        message_id: Optional[str] = None,
        status: str = "sent"
    ) -> Message:
        """Create and persist assistant message."""
        
        message = Message(
            id=uuid.UUID(message_id) if message_id else uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            sender="assistant",
            content=content,
            message_metadata={"disclaimer": True},
            status=status
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        logger.info(f"Assistant message created: {message.id}")
        return message
    
    async def _check_duplicate_message(
        self,
        conversation_id: str,
        client_message_id: str
    ) -> Optional[Message]:
        """Check if message with client_message_id already exists."""
        
        result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == uuid.UUID(conversation_id),
                Message.message_metadata.op('->>')('client_message_id') == client_message_id
            )
        )
        return result.scalars().first()
    
    async def _update_conversation_stats(self, conversation_id: str):
        """Update conversation statistics."""
        
        try:
            # Get message count
            result = await self.db.execute(
                select(func.count(Message.id)).where(
                    Message.conversation_id == uuid.UUID(conversation_id)
                )
            )
            message_count = result.scalar() or 0
            
            # Update conversation
            conversation = await ConversationCRUD.get_by_id(self.db, conversation_id)
            if conversation:
                conversation.messages_count = message_count
                await self.db.commit()
                
        except Exception as e:
            logger.exception("Error updating conversation stats")


class StreamCache:
    """Simple in-memory cache for stream resumption."""
    
    def __init__(self):
        self._cache = {}
        
    def store_stream(self, conversation_id: str, message_id: str, content: str, ttl: int = 30):
        """Store stream content for resumption."""
        import time
        self._cache[f"{conversation_id}:{message_id}"] = {
            "content": content,
            "expires": time.time() + ttl
        }
        
    def get_stream(self, conversation_id: str, message_id: str) -> Optional[str]:
        """Retrieve cached stream content."""
        import time
        key = f"{conversation_id}:{message_id}"
        
        if key in self._cache:
            cached = self._cache[key]
            if time.time() < cached["expires"]:
                return cached["content"]
            else:
                del self._cache[key]
                
        return None
        
    def cleanup_expired(self):
        """Remove expired cache entries."""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, value in self._cache.items()
            if current_time >= value["expires"]
        ]
        for key in expired_keys:
            del self._cache[key]


# Global stream cache instance
stream_cache = StreamCache()

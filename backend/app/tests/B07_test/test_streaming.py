"""
Tests for B07 - Streaming (WebSocket) functionality.
Tests WebSocket streaming, chat manager, and LLM provider integration.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.llm_provider import LLMProvider
from app.services.chat_manager import ChatManager, WebSocketStreamer
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


class TestLLMProvider:
    """Test LLM Provider functionality."""
    
    @pytest.mark.asyncio
    async def test_dev_mode_response(self):
        """Test LLM provider in development mode."""
        provider = LLMProvider(use_dev_mode=True)
        
        response = await provider.process_pipeline(text="Hello, I have a headache")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "⚠️" in response  # Check disclaimer is included
        assert "medical" in response.lower() or "health" in response.lower()
    
    @pytest.mark.asyncio
    async def test_dev_mode_streaming(self):
        """Test LLM provider streaming in development mode."""
        provider = LLMProvider(use_dev_mode=True)
        
        chunks = []
        async for chunk in provider.process_pipeline_stream(text="Test message"):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "⚠️" in full_response  # Check disclaimer is included
    
    @pytest.mark.asyncio
    async def test_audio_processing(self):
        """Test audio input processing."""
        provider = LLMProvider(use_dev_mode=True)
        
        # Simulate audio bytes
        fake_audio = b"fake_audio_data"
        response = await provider.process_pipeline(audio=fake_audio)
        
        assert "voice message" in response.lower() or "audio" in response.lower()
        assert "⚠️" in response
    
    @pytest.mark.asyncio
    async def test_image_processing(self):
        """Test image input processing."""
        provider = LLMProvider(use_dev_mode=True)
        
        # Simulate image bytes
        fake_image = b"fake_image_data"
        response = await provider.process_pipeline(image=fake_image)
        
        assert "image" in response.lower()
        assert "⚠️" in response


class TestChatManager:
    """Test Chat Manager functionality."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user object."""
        user = User(
            id="550e8400-e29b-41d4-a716-446655440000",
            email="test@example.com",
            name="Test User"
        )
        return user
    
    @pytest.fixture
    def mock_conversation(self):
        """Mock conversation object."""
        conversation = Conversation(
            id="550e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440000",
            title="Test Conversation",
            messages_count="0"
        )
        return conversation
    
    @pytest.mark.asyncio
    async def test_handle_user_message_without_streaming(self, mock_db, mock_user, mock_conversation):
        """Test handling user message without WebSocket streaming."""
        
        # Mock CRUD operations
        with patch('app.services.chat_manager.ConversationCRUD') as mock_conv_crud, \
             patch('app.services.chat_manager.MessageCRUD') as mock_msg_crud:
            
            mock_conv_crud.get_by_id.return_value = mock_conversation
            mock_msg_crud.create_with_count_increment.return_value = Message(
                id="550e8400-e29b-41d4-a716-446655440002",
                conversation_id=mock_conversation.id,
                sender="user",
                content="Test message"
            )
            
            chat_manager = ChatManager(mock_db)
            
            result = await chat_manager.handle_user_message(
                conversation_id=str(mock_conversation.id),
                user_id=str(mock_user.id),
                text="Hello, I have a question about my health"
            )
            
            assert "user_message_id" in result
            assert "assistant_message_id" in result
            assert "response" in result
            assert "conversation_id" in result
    
    @pytest.mark.asyncio
    async def test_websocket_streamer(self):
        """Test WebSocket streamer functionality."""
        
        # Mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        conversation_id = "550e8400-e29b-41d4-a716-446655440001"
        
        streamer = WebSocketStreamer(mock_websocket, conversation_id)
        
        # Test sending chunk
        await streamer.send_chunk("msg_id", "Hello ")
        mock_websocket.send_json.assert_called_with({
            "type": "chunk",
            "messageId": "msg_id",
            "conversationId": conversation_id,
            "data": "Hello "
        })
        
        # Test sending done
        await streamer.send_done("msg_id", "Hello world")
        mock_websocket.send_json.assert_called_with({
            "type": "done",
            "messageId": "msg_id",
            "conversationId": conversation_id,
            "message": {
                "id": "msg_id",
                "content": "Hello world",
                "sender": "assistant",
                "timestamp": pytest.approx(str, abs=1)  # Allow timestamp variation
            }
        })
        
        # Test sending error
        await streamer.send_error("Test error")
        mock_websocket.send_json.assert_called_with({
            "type": "error",
            "conversationId": conversation_id,
            "error": "Test error"
        })


class TestWebSocketIntegration:
    """Test WebSocket integration."""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is properly registered."""
        client = TestClient(app)
        
        # Check that the WebSocket route exists in the app
        websocket_routes = [route for route in app.routes if hasattr(route, 'path') and 'ws' in route.path]
        assert len(websocket_routes) > 0
        
        # Check specific WebSocket route
        ws_route_paths = [route.path for route in websocket_routes]
        assert any('/ws/conversations/{conversation_id}' in path for path in ws_route_paths)


class TestStreamingProtocol:
    """Test streaming protocol compliance."""
    
    @pytest.mark.asyncio
    async def test_streaming_protocol_format(self):
        """Test that streaming messages follow the correct protocol format."""
        
        # Mock WebSocket
        mock_websocket = AsyncMock(spec=WebSocket)
        conversation_id = "test_conv_id"
        
        streamer = WebSocketStreamer(mock_websocket, conversation_id)
        
        # Test chunk format
        await streamer.send_chunk("msg_123", "Hello")
        
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "chunk"
        assert call_args["messageId"] == "msg_123"
        assert call_args["conversationId"] == conversation_id
        assert call_args["data"] == "Hello"
        
        # Test done format
        await streamer.send_done("msg_123", "Hello world")
        
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "done"
        assert call_args["messageId"] == "msg_123"
        assert "message" in call_args
        assert call_args["message"]["content"] == "Hello world"
        assert call_args["message"]["sender"] == "assistant"
        
        # Test error format
        await streamer.send_error("Test error message")
        
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["error"] == "Test error message"


class TestHealthcareDisclaimer:
    """Test healthcare disclaimer functionality."""
    
    @pytest.mark.asyncio
    async def test_disclaimer_in_responses(self):
        """Test that healthcare disclaimer is included in all responses."""
        provider = LLMProvider(use_dev_mode=True)
        
        # Test text response
        response = await provider.process_pipeline(text="I have a headache")
        assert "⚠️" in response
        assert "medical" in response.lower()
        assert "healthcare" in response.lower() or "doctor" in response.lower()
        
        # Test streaming response
        chunks = []
        async for chunk in provider.process_pipeline_stream(text="I feel sick"):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        assert "⚠️" in full_response
        assert "medical" in full_response.lower()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

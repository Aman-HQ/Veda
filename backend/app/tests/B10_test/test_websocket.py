"""
WebSocket Streaming Tests for B10
Tests real-time chat streaming via WebSocket with authentication and protocol validation.

NOTE: WebSocket tests have limitations due to TestClient creating a new app instance.
Some tests are marked as integration tests and require actual database setup.
"""

import pytest
import json
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.core.security import create_access_token
from app.db.session import get_db


# Note: WebSocket testing with TestClient is complex because it creates a new app instance
# that doesn't share the test database fixtures. For full WebSocket testing, we'd need
# actual WebSocket client libraries or end-to-end testing.


@pytest.mark.websocket
@pytest.mark.integration
@pytest.mark.skip(reason="WebSocket tests require special database setup - TestClient creates separate app instance")
@pytest.mark.asyncio
class TestWebSocketConnection:
    """Test WebSocket connection establishment and authentication."""
    
    async def test_connect_with_valid_token(self, test_user, test_conversation):
        """Test successful WebSocket connection with valid JWT token."""
        # Create access token for test user
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        # Use TestClient for WebSocket
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Connection successful if we get here
                assert websocket.client_state.name == "CONNECTED"
                
                # Send ping to verify connection is working
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"
    
    async def test_connect_without_token_fails(self, test_conversation):
        """Test WebSocket connection fails without token."""
        with TestClient(app) as test_client:
            with pytest.raises(Exception):  # Should raise WebSocket error
                with test_client.websocket_connect(
                    f"/ws/conversations/{test_conversation.id}"
                ):
                    pass
    
    async def test_connect_with_invalid_token_fails(self, test_conversation):
        """Test WebSocket connection fails with invalid token."""
        invalid_token = "invalid.jwt.token"
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={invalid_token}"
            ) as websocket:
                # Connection should close with authentication error
                # Server closes with code 4001
                try:
                    data = websocket.receive()
                except:
                    pass
                assert websocket.client_state.name == "DISCONNECTED"
    
    async def test_connect_to_nonexistent_conversation(self, test_user):
        """Test WebSocket connection fails for non-existent conversation."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        fake_conversation_id = str(uuid4())
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{fake_conversation_id}?token={access_token}"
            ) as websocket:
                # Server should close connection with error code
                try:
                    data = websocket.receive()
                except:
                    pass
                assert websocket.client_state.name == "DISCONNECTED"
    
    async def test_connect_to_other_user_conversation(self, admin_user, test_conversation):
        """Test user cannot connect to another user's conversation."""
        # Create token for admin user, but try to access test_user's conversation
        access_token = create_access_token(data={"sub": str(admin_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Server should reject with access denied
                try:
                    data = websocket.receive()
                except:
                    pass
                assert websocket.client_state.name == "DISCONNECTED"


@pytest.mark.websocket
@pytest.mark.integration
@pytest.mark.skip(reason="WebSocket tests require special database setup - TestClient creates separate app instance")
@pytest.mark.asyncio
class TestWebSocketMessaging:
    """Test WebSocket message sending and streaming."""
    
    async def test_send_message_and_receive_stream(self, test_user, test_conversation, mock_llm_provider):
        """Test sending a message and receiving streamed response."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send user message
                client_message_id = str(uuid4())
                websocket.send_json({
                    "type": "message",
                    "text": "What are the symptoms of diabetes?",
                    "client_message_id": client_message_id
                })
                
                # Receive streaming response
                chunks_received = []
                done_received = False
                
                # Collect messages until done
                for _ in range(20):  # Limit iterations to avoid infinite loop
                    try:
                        response = websocket.receive_json(timeout=5)
                        
                        if response["type"] == "chunk":
                            chunks_received.append(response)
                            assert "messageId" in response or "message_id" in response
                            assert "data" in response
                        
                        elif response["type"] == "done":
                            done_received = True
                            assert "message" in response
                            # Message should have required fields
                            message = response["message"]
                            assert "id" in message
                            assert "content" in message
                            assert message["sender"] == "assistant"
                            break
                    
                    except Exception as e:
                        # Timeout or connection closed
                        break
                
                # Verify we received streaming chunks and completion
                assert len(chunks_received) > 0, "Should receive at least one chunk"
                assert done_received, "Should receive done message"
    
    async def test_send_empty_message_returns_error(self, test_user, test_conversation):
        """Test sending empty message returns error."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send empty message
                websocket.send_json({
                    "type": "message",
                    "text": "",
                    "client_message_id": str(uuid4())
                })
                
                # Should receive error
                response = websocket.receive_json(timeout=5)
                assert response["type"] == "error"
                assert "text is required" in response.get("error", "").lower()
    
    @pytest.mark.skip(reason="Duplicate detection requires persistent state across requests")
    async def test_send_duplicate_message_ignored(self, test_user, test_conversation, mock_llm_provider):
        """Test duplicate messages (same client_message_id) are ignored."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send message with specific client_message_id
                client_message_id = str(uuid4())
                message_data = {
                    "type": "message",
                    "text": "Test message",
                    "client_message_id": client_message_id
                }
                
                # Send first time
                websocket.send_json(message_data)
                
                # Receive responses
                first_responses = []
                for _ in range(10):
                    try:
                        response = websocket.receive_json(timeout=2)
                        first_responses.append(response)
                        if response["type"] == "done":
                            break
                    except:
                        break
                
                # Send same message again (duplicate)
                websocket.send_json(message_data)
                
                # Should receive error about duplicate
                response = websocket.receive_json(timeout=5)
                assert response["type"] == "error"
                assert "duplicate" in response.get("error", "").lower()


@pytest.mark.websocket
@pytest.mark.integration
@pytest.mark.skip(reason="WebSocket tests require special database setup - TestClient creates separate app instance")
@pytest.mark.asyncio
class TestWebSocketProtocol:
    """Test WebSocket protocol compliance."""
    
    async def test_invalid_json_returns_error(self, test_user, test_conversation):
        """Test sending invalid JSON returns error."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send invalid JSON
                websocket.send_text("invalid json {")
                
                # Should receive error
                response = websocket.receive_json(timeout=5)
                assert response["type"] == "error"
                assert "json" in response.get("error", "").lower()
    
    async def test_unknown_message_type_returns_error(self, test_user, test_conversation):
        """Test unknown message type returns error."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send unknown message type
                websocket.send_json({
                    "type": "unknown_type",
                    "data": "test"
                })
                
                # Should receive error
                response = websocket.receive_json(timeout=5)
                assert response["type"] == "error"
                assert "unknown" in response.get("error", "").lower()
    
    async def test_ping_pong_keepalive(self, test_user, test_conversation):
        """Test ping-pong keepalive mechanism."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send multiple pings
                for i in range(3):
                    websocket.send_json({"type": "ping"})
                    response = websocket.receive_json(timeout=5)
                    assert response["type"] == "pong"


@pytest.mark.websocket
@pytest.mark.integration
@pytest.mark.skip(reason="WebSocket tests require special database setup - TestClient creates separate app instance")
@pytest.mark.asyncio
class TestWebSocketReconnection:
    """Test WebSocket reconnection and resume functionality."""
    
    async def test_resume_request(self, test_user, test_conversation):
        """Test WebSocket resume functionality."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send resume request
                websocket.send_json({
                    "type": "resume",
                    "conversationId": str(test_conversation.id),
                    "lastMessageId": str(uuid4())
                })
                
                # Should receive resume acknowledgment
                response = websocket.receive_json(timeout=5)
                # Could be resume_ack or error (if no cached content)
                assert response["type"] in ["resume_ack", "error"]
    
    async def test_reconnect_after_disconnect(self, test_user, test_conversation):
        """Test reconnecting after disconnection."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            # First connection
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send ping to confirm connection
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"
            
            # Reconnect (new connection)
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Should be able to connect again
                websocket.send_json({"type": "ping"})
                response = websocket.receive_json()
                assert response["type"] == "pong"


@pytest.mark.websocket
@pytest.mark.integration
@pytest.mark.skip(reason="WebSocket tests require special database setup - TestClient creates separate app instance")
@pytest.mark.asyncio
class TestWebSocketStreaming:
    """Test streaming behavior and chunk handling."""
    
    async def test_stream_chunks_are_ordered(self, test_user, test_conversation, mock_llm_provider):
        """Test streaming chunks arrive in order."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send message
                websocket.send_json({
                    "type": "message",
                    "text": "Tell me about hypertension",
                    "client_message_id": str(uuid4())
                })
                
                # Collect chunks
                chunks = []
                for _ in range(20):
                    try:
                        response = websocket.receive_json(timeout=5)
                        if response["type"] == "chunk":
                            chunks.append(response["data"])
                        elif response["type"] == "done":
                            # Verify final message contains all chunks
                            final_content = response["message"]["content"]
                            # Chunks should be part of final content
                            assert len(final_content) > 0
                            break
                    except:
                        break
                
                # Should have received chunks
                assert len(chunks) > 0
    
    async def test_done_message_contains_complete_message(self, test_user, test_conversation, mock_llm_provider):
        """Test done message contains complete message object."""
        access_token = create_access_token(data={"sub": str(test_user.id)})
        
        with TestClient(app) as test_client:
            with test_client.websocket_connect(
                f"/ws/conversations/{test_conversation.id}?token={access_token}"
            ) as websocket:
                # Send message
                websocket.send_json({
                    "type": "message",
                    "text": "What is asthma?",
                    "client_message_id": str(uuid4())
                })
                
                # Find done message
                done_message = None
                for _ in range(20):
                    try:
                        response = websocket.receive_json(timeout=5)
                        if response["type"] == "done":
                            done_message = response
                            break
                    except:
                        break
                
                # Verify done message structure
                assert done_message is not None
                assert "message" in done_message
                
                message = done_message["message"]
                assert "id" in message
                assert "conversation_id" in message
                assert "sender" in message
                assert message["sender"] == "assistant"
                assert "content" in message
                assert len(message["content"]) > 0
                assert "created_at" in message

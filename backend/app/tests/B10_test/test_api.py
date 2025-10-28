"""
B10 Integration Tests - API Endpoints
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "securepass123",
                "name": "New User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "New User"
        assert "hashed_password" not in data
    
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with duplicate email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,
                "password": "password123",
                "name": "Duplicate"
            }
        )
        
        assert response.status_code == 400
    
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
    
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "notexist@test.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 401
    
    async def test_get_current_user(self, client: AsyncClient, auth_headers, test_user):
        """Test getting current user information."""
        response = await client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["name"] == test_user.name
    
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test accessing /me without auth fails."""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    async def test_refresh_token(self, client: AsyncClient, test_user):
        """Test refreshing access token."""
        # First login to get refresh token
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "testpassword123"
            }
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data


@pytest.mark.asyncio
class TestConversationEndpoints:
    """Test conversation endpoints."""
    
    async def test_list_conversations(self, client: AsyncClient, auth_headers, test_conversation):
        """Test listing user's conversations."""
        response = await client.get(
            "/api/conversations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_list_conversations_unauthorized(self, client: AsyncClient):
        """Test listing conversations without auth fails."""
        response = await client.get("/api/conversations")
        
        assert response.status_code == 401
    
    async def test_create_conversation(self, client: AsyncClient, auth_headers):
        """Test creating a new conversation."""
        response = await client.post(
            "/api/conversations",
            headers=auth_headers,
            json={"title": "New Conversation"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Conversation"
    
    async def test_get_conversation(self, client: AsyncClient, auth_headers, test_conversation):
        """Test getting a specific conversation."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_conversation.id)
    
    async def test_get_conversation_unauthorized(self, client: AsyncClient, test_conversation):
        """Test getting conversation without auth fails."""
        response = await client.get(f"/api/conversations/{test_conversation.id}")
        
        assert response.status_code == 401
    
    async def test_delete_conversation(self, client: AsyncClient, auth_headers, test_user, db_session):
        """Test deleting a conversation."""
        from app.models.conversation import Conversation
        
        # Create a conversation to delete
        conv = Conversation(user_id=test_user.id, title="Delete Me")
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)
        
        response = await client.delete(
            f"/api/conversations/{conv.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
    
    async def test_cannot_access_other_user_conversation(
        self, client: AsyncClient, auth_headers, admin_user, db_session
    ):
        """Test that users cannot access other users' conversations."""
        from app.models.conversation import Conversation
        
        # Create conversation for admin user
        admin_conv = Conversation(user_id=admin_user.id, title="Admin Conv")
        db_session.add(admin_conv)
        await db_session.commit()
        await db_session.refresh(admin_conv)
        
        # Try to access with regular user auth
        response = await client.get(
            f"/api/conversations/{admin_conv.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [403, 404]


@pytest.mark.asyncio
class TestMessageEndpoints:
    """Test message endpoints."""
    
    async def test_list_messages(self, client: AsyncClient, auth_headers, test_conversation, test_message):
        """Test listing messages in a conversation."""
        response = await client.get(
            f"/api/{test_conversation.id}/messages",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    async def test_create_message(self, client: AsyncClient, auth_headers, test_conversation, mock_llm_provider):
        """Test creating a new message."""
        response = await client.post(
            f"/api/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content": "Hello, this is a test message"
            }
        )
        
        # Should return 201 with the created message
        assert response.status_code in [200, 201]
        data = response.json()
        assert "content" in data
        assert data["sender"] == "user"
    
    async def test_create_message_unauthorized(self, client: AsyncClient, test_conversation):
        """Test creating message without auth fails."""
        response = await client.post(
            f"/api/{test_conversation.id}/messages",
            json={"content": "Test"}
        )
        
        assert response.status_code == 401
    
    @pytest.mark.skip(reason="Moderation not yet implemented in message creation endpoint")
    async def test_create_message_blocked_by_moderation(
        self, client: AsyncClient, auth_headers, test_conversation
    ):
        """Test that high-severity content is blocked."""
        response = await client.post(
            f"/api/{test_conversation.id}/messages",
            headers=auth_headers,
            json={
                "content": "I want to kill myself"
            }
        )
        
        # Should return error or be blocked
        assert response.status_code in [400, 403]


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test health check endpoint."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

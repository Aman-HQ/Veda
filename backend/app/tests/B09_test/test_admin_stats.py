"""
Test suite for admin statistics and observability endpoints.
Tests /api/admin/stats, /api/admin/metrics, and related functionality.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.security import create_access_token


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin user for testing."""
    admin = User(
        email="admin@test.com",
        name="Admin User",
        role="admin",
        hashed_password="hashed_password_here"
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession):
    """Create a regular user for testing."""
    user = User(
        email="user@test.com",
        name="Regular User",
        role="user",
        hashed_password="hashed_password_here"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(admin_user: User):
    """Create access token for admin user."""
    return create_access_token({"sub": str(admin_user.id)})


@pytest_asyncio.fixture
async def user_token(regular_user: User):
    """Create access token for regular user."""
    return create_access_token({"sub": str(regular_user.id)})


@pytest_asyncio.fixture
async def sample_data(db_session: AsyncSession, regular_user: User):
    """Create sample conversations and messages for testing."""
    # Create conversations
    conv1 = Conversation(
        user_id=regular_user.id,
        title="Test Conversation 1",
        messages_count=0
    )
    conv2 = Conversation(
        user_id=regular_user.id,
        title="Test Conversation 2",
        messages_count=0
    )
    db_session.add_all([conv1, conv2])
    await db_session.commit()
    await db_session.refresh(conv1)
    await db_session.refresh(conv2)
    
    # Create messages
    today = datetime.utcnow()
    yesterday = today - timedelta(days=1)
    
    messages = [
        Message(
            conversation_id=conv1.id,
            sender="user",
            content="Hello",
            status="sent",
            created_at=today
        ),
        Message(
            conversation_id=conv1.id,
            sender="assistant",
            content="Hi there",
            status="sent",
            created_at=today
        ),
        Message(
            conversation_id=conv2.id,
            sender="user",
            content="Test message",
            status="sent",
            created_at=yesterday
        ),
        Message(
            conversation_id=conv2.id,
            sender="user",
            content="Flagged content",
            status="flagged",
            created_at=today
        ),
    ]
    
    db_session.add_all(messages)
    conv1.messages_count = 2
    conv2.messages_count = 2
    await db_session.commit()
    
    return {
        "conversations": [conv1, conv2],
        "messages": messages
    }


@pytest.mark.asyncio
async def test_admin_stats_requires_auth(client: AsyncClient):
    """Test that admin stats endpoint requires authentication."""
    response = await client.get("/api/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_stats_requires_admin_role(client: AsyncClient, user_token: str):
    """Test that admin stats endpoint requires admin role."""
    response = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_admin_stats_success(
    client: AsyncClient,
    admin_token: str,
    sample_data: dict
):
    """Test successful retrieval of admin statistics."""
    response = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "overview" in data
    assert "moderation" in data
    assert "system_health" in data
    assert "time_range" in data
    assert "generated_at" in data
    
    # Check overview data
    overview = data["overview"]
    assert "total_users" in overview
    assert "total_conversations" in overview
    assert "total_messages" in overview
    assert "user_messages_recent" in overview
    assert "assistant_messages_recent" in overview
    
    # Verify counts (at least our test data)
    assert overview["total_conversations"] >= 2
    assert overview["total_messages"] >= 4


@pytest.mark.asyncio
async def test_admin_stats_with_custom_days(
    client: AsyncClient,
    admin_token: str,
    sample_data: dict
):
    """Test admin stats with custom time range."""
    response = await client.get(
        "/api/admin/stats?days=30",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["time_range"]["days"] == 30


@pytest.mark.asyncio
async def test_admin_metrics_success(
    client: AsyncClient,
    admin_token: str,
    sample_data: dict
):
    """Test successful retrieval of real-time metrics."""
    response = await client.get(
        "/api/admin/metrics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "uptime" in data
    assert "conversations" in data
    assert "messages" in data
    assert "system_resources" in data
    assert "timestamp" in data
    
    # Check uptime
    uptime = data["uptime"]
    assert "seconds" in uptime
    assert "formatted" in uptime
    assert "started_at" in uptime
    assert uptime["seconds"] >= 0
    
    # Check conversations
    assert "active_last_24h" in data["conversations"]
    
    # Check messages
    messages = data["messages"]
    assert "today" in messages
    assert "flagged_total" in messages
    assert "flagged_last_24h" in messages
    assert messages["flagged_total"] >= 1  # We created a flagged message
    
    # Check system resources
    resources = data["system_resources"]
    assert "process" in resources
    assert "system" in resources
    assert "memory_mb" in resources["process"]
    assert "cpu_percent" in resources["process"]


@pytest.mark.asyncio
async def test_admin_metrics_requires_admin(client: AsyncClient, user_token: str):
    """Test that metrics endpoint requires admin role."""
    response = await client.get(
        "/api/admin/metrics",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_moderation_stats(client: AsyncClient, admin_token: str):
    """Test moderation statistics endpoint."""
    response = await client.get(
        "/api/admin/moderation/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "health" in data
    assert "rules_breakdown" in data
    assert "generated_at" in data
    
    # Check rules breakdown
    rules = data["rules_breakdown"]
    assert isinstance(rules, dict)
    # Should have high, medium, low severity levels
    assert "high" in rules or "medium" in rules or "low" in rules


@pytest.mark.asyncio
async def test_reload_moderation_rules(client: AsyncClient, admin_token: str):
    """Test reloading moderation rules."""
    response = await client.post(
        "/api/admin/moderation/reload-rules",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Should succeed or fail gracefully if rules file doesn't exist
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "new_rule_count" in data
        assert "reloaded_at" in data


@pytest.mark.asyncio
async def test_get_users_list(
    client: AsyncClient,
    admin_token: str,
    admin_user: User,
    regular_user: User
):
    """Test retrieving users list."""
    response = await client.get(
        "/api/admin/users?limit=10&offset=0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    assert len(data) >= 2  # At least admin and regular user
    
    # Check user structure
    if len(data) > 0:
        user = data[0]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert "role" in user
        assert "created_at" in user
        assert "conversation_count" in user


@pytest.mark.asyncio
async def test_get_flagged_conversations(
    client: AsyncClient,
    admin_token: str,
    sample_data: dict
):
    """Test retrieving flagged conversations."""
    response = await client.get(
        "/api/admin/conversations/flagged?limit=50",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    # Should have at least one flagged conversation from sample data
    assert len(data) >= 1
    
    if len(data) > 0:
        conv = data[0]
        assert "conversation_id" in conv
        assert "title" in conv
        assert "flagged_messages" in conv
        assert isinstance(conv["flagged_messages"], list)


@pytest.mark.asyncio
async def test_system_health(client: AsyncClient, admin_token: str):
    """Test system health check endpoint."""
    response = await client.get(
        "/api/admin/system/health",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "overall_status" in data
    assert data["overall_status"] in ["healthy", "degraded"]
    assert "components" in data
    assert "checked_at" in data
    
    # Check components
    components = data["components"]
    assert "llm_provider" in components
    assert "rag_pipeline" in components
    assert "moderation_service" in components


@pytest.mark.asyncio
async def test_update_user_role(
    client: AsyncClient,
    admin_token: str,
    regular_user: User,
    db_session: AsyncSession
):
    """Test updating user role."""
    response = await client.post(
        f"/api/admin/users/{regular_user.id}/role?new_role=moderator",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["old_role"] == "user"
    assert data["new_role"] == "moderator"
    
    # Verify in database
    result = await db_session.execute(
        select(User).where(User.id == regular_user.id)
    )
    updated_user = result.scalar_one()
    assert updated_user.role == "moderator"


@pytest.mark.asyncio
async def test_update_user_role_invalid_role(
    client: AsyncClient,
    admin_token: str,
    regular_user: User
):
    """Test updating user role with invalid role."""
    response = await client.post(
        f"/api/admin/users/{regular_user.id}/role?new_role=superuser",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 400
    assert "Invalid role" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_user_role_nonexistent_user(
    client: AsyncClient,
    admin_token: str
):
    """Test updating role for nonexistent user."""
    fake_user_id = "00000000-0000-0000-0000-000000000000"
    response = await client.post(
        f"/api/admin/users/{fake_user_id}/role?new_role=moderator",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_pagination_users_list(client: AsyncClient, admin_token: str):
    """Test pagination in users list endpoint."""
    # Get first page
    response1 = await client.get(
        "/api/admin/users?limit=1&offset=0",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1) <= 1
    
    # Get second page
    response2 = await client.get(
        "/api/admin/users?limit=1&offset=1",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    
    # If both have data, they should be different users
    if len(data1) > 0 and len(data2) > 0:
        assert data1[0]["id"] != data2[0]["id"]

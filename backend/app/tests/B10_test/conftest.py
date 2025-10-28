"""
Pytest configuration and fixtures for B10 comprehensive test suite.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import TypeDecorator, CHAR, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid
import tempfile
import shutil
from pathlib import Path

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.services.llm_provider import LLMProvider


# Test database URL (use in-memory SQLite for speed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# SQLite UUID type decorator
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid.UUID):
                return value
            else:
                return uuid.UUID(value)


@pytest.fixture(scope="module")
def event_loop():
    """Create an event loop for the test module."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def db_engine():
    """Create a test database engine."""
    # Import all models to ensure they're registered with Base.metadata
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message
    
    # Use StaticPool to ensure same connection is reused for in-memory database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    
    # Monkey-patch all UUID columns to use GUID for SQLite
    async with engine.begin() as conn:
        # Before creating tables, replace UUID types with GUID
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if hasattr(column.type, '__class__') and column.type.__class__.__name__ == 'UUID':
                    column.type = GUID()
        
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        
        # Clean up all data within the same session
        try:
            await session.execute(text("DELETE FROM messages"))
            await session.execute(text("DELETE FROM conversations"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception:
            # If there's an error (e.g., from a failed test), rollback first
            await session.rollback()
            # Try cleanup again
            try:
                await session.execute(text("DELETE FROM messages"))
                await session.execute(text("DELETE FROM conversations"))
                await session.execute(text("DELETE FROM users"))
                await session.commit()
            except Exception:
                # If cleanup still fails, just rollback and continue
                await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True  # Follow 307 redirects automatically
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    # Check if user already exists
    result = await db_session.execute(
        select(User).where(User.email == "test@example.com")
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return existing_user
    
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        name="Test User",
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession):
    """Create an admin user."""
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy import select
    
    # Check if user already exists
    result = await db_session.execute(
        select(User).where(User.email == "admin@example.com")
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return existing_user
    
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        name="Admin User",
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user):
    """Generate authentication headers for test user."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(admin_user):
    """Generate authentication headers for admin user."""
    from app.core.security import create_access_token
    
    access_token = create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest_asyncio.fixture
async def test_conversation(db_session: AsyncSession, test_user):
    """Create a test conversation."""
    from app.models.conversation import Conversation
    
    conversation = Conversation(
        user_id=test_user.id,
        title="Test Conversation"
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest_asyncio.fixture
async def test_message(db_session: AsyncSession, test_conversation):
    """Create a test message."""
    from app.models.message import Message
    
    message = Message(
        conversation_id=test_conversation.id,
        sender="user",
        content="Test message content",
        status="sent"
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


@pytest.fixture
def tmp_upload_dir():
    """Create a temporary upload directory."""
    tmp_dir = Path(tempfile.mkdtemp())
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def mock_llm_provider(monkeypatch):
    """Mock LLM provider for testing without actual model calls."""
    
    class MockLLMProvider:
        async def process_pipeline(self, audio=None, text=None, image=None, opts=None):
            """Return canned response."""
            if text:
                return f"Mock response to: {text}"
            elif audio:
                return "Mock response to audio input"
            elif image:
                return "Mock response to image input"
            return "Mock default response"
        
        async def stream_response(self, text, callback):
            """Stream mock response in chunks."""
            response = f"Mock streaming response to: {text}"
            chunk_size = 10
            for i in range(0, len(response), chunk_size):
                await callback(response[i:i+chunk_size])
    
    return MockLLMProvider()

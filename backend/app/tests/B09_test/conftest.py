"""
Pytest configuration for B09 admin and observability tests.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import TypeDecorator, CHAR, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import uuid

from app.main import app
from app.db.base import Base
from app.db.session import get_db


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
    from sqlalchemy.pool import StaticPool
    
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,  # Use StaticPool instead of NullPool for :memory:
        connect_args={"check_same_thread": False},  # Allow SQLite to be used across threads
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
    # Create session factory
    async_session = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create a session
    async with async_session() as session:
        yield session
        
        # Clean up all data within the same session to ensure tables exist
        await session.execute(text("DELETE FROM messages"))
        await session.execute(text("DELETE FROM conversations"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

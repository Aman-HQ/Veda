"""
Database initialization utilities.
Handles table creation and initial setup.
"""
from sqlalchemy.ext.asyncio import AsyncEngine
from .base import Base
from .session import engine


async def init_db(engine_override: AsyncEngine = None):
    """
    Initialize database by creating all tables.
    
    Note: In production, use Alembic migrations instead.
    This is primarily for development and testing.
    
    Args:
        engine_override: Optional engine to use instead of default
    """
    target_engine = engine_override or engine
    
    async with target_engine.begin() as conn:
        # Import all models here to ensure they're registered
        # This will be populated once models are created
        # from ..models import user, conversation, message
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created successfully")


async def drop_db(engine_override: AsyncEngine = None):
    """
    Drop all database tables.
    
    WARNING: This will delete all data! Use only in development/testing.
    
    Args:
        engine_override: Optional engine to use instead of default
    """
    target_engine = engine_override or engine
    
    async with target_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("✓ Database tables dropped successfully")


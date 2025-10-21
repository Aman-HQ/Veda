"""
Database session management.
Provides async SQLAlchemy engine and session factory.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from ..core import config

# Create async engine
# echo=True for development (logs SQL), set to False in production
engine = create_async_engine(
    config.DATABASE_URL,
    echo=config.DEBUG,
    future=True,
    pool_pre_ping=True,  # Verify connections before using them
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent expired objects after commit
    autoflush=False,  # Manual control of when to flush
    autocommit=False,  # Always use explicit commits
)


async def get_db():
    """
    Dependency for FastAPI routes to get database session.
    
    Yields:
        AsyncSession: Database session
        
    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


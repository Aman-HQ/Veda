"""
CRUD operations for User model.
"""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..models.user import User
from ..schemas.auth import UserCreate, UserUpdate
from ..core.security import get_password_hash, verify_password


class UserCRUD:
    """CRUD operations for User model."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def create(db: AsyncSession, user_create: UserCreate) -> User:
        """Create a new user."""
        # Hash the password
        hashed_password = get_password_hash(user_create.password)
        
        # Create user instance
        user = User(
            email=user_create.email,
            hashed_password=hashed_password,
            name=user_create.name,
            role=user_create.role
        )
        
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError("User registration failed due to duplicate email") from None

    @staticmethod
    async def create_oauth_user(db: AsyncSession, email: str, name: str) -> User:
        """Create a new user from OAuth (no password)."""
        user = User(
            email=email,
            name=name,
            hashed_password=None,  # OAuth users don't have passwords
            role="user"
        )
        
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user
        except IntegrityError:
            await db.rollback()
            raise ValueError("User registration failed due to duplicate email") from None
    @staticmethod
    async def update(db: AsyncSession, user: User, user_update: UserUpdate) -> User:
        """Update user information."""
        update_data = user_update.model_dump(exclude_unset=True)

        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))  

        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(db: AsyncSession, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = await UserCRUD.get_by_email(db, email)
        if not user or not user.hashed_password:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    @staticmethod
    async def update_refresh_tokens(db: AsyncSession, user: User, refresh_tokens: List[dict]) -> User:
        """Update user's refresh tokens list."""
        user.refresh_tokens = refresh_tokens
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_all(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users (admin function)."""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def delete(db: AsyncSession, user: User) -> bool:
        """Delete a user."""
        await db.delete(user)
        await db.commit()
        return True

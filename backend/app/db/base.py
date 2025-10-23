"""
SQLAlchemy declarative base and metadata.
All models should import Base from this module.
Ensure all models are imported here for Alembic autogenerate.
"""
from sqlalchemy.ext.declarative import declarative_base

# Create declarative base for all models
Base = declarative_base()

# Import all models here to ensure they're registered with Base.metadata
# This is needed for Alembic autogenerate to work properly
from app.models import User, Conversation, Message # noqa: F401


"""
SQLAlchemy declarative base and metadata.
All models should import Base from this module.
"""
from sqlalchemy.ext.declarative import declarative_base

# Create declarative base for all models
Base = declarative_base()

# Note: Models are imported in alembic/env.py for autogenerate support
# This avoids circular import issues


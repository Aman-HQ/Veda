from logging.config import fileConfig
import os
import sys

from sqlalchemy import create_engine, pool
from alembic import context

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.core.config import DATABASE_URL

# Import all models to ensure they're registered with Base.metadata
from app.models.user import User  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# Import all models here to ensure they're registered with Base.metadata
# This will be updated when we create the models
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use sync database URL for offline mode
    sync_database_url = DATABASE_URL.replace('+asyncpg', '')
    
    context.configure(
        url=sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use sync engine for autogenerate by replacing +asyncpg with +psycopg2
    sync_database_url = DATABASE_URL.replace('+asyncpg', '')
    
    connectable = create_engine(
        sync_database_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

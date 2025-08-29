"""
Alembic environment configuration for Fortune VTuber database migrations

Supports both SQLite (development) and MariaDB (production) with proper metadata detection.
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from alembic import context

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import models to ensure metadata is populated
from fortune_vtuber.models.base import Base
from fortune_vtuber.models import *  # Import all models
from fortune_vtuber.config.settings import get_settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from settings or config"""
    try:
        settings = get_settings()
        return settings.get_database_url()
    except Exception:
        # Fallback to config file
        return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite specific options
        render_as_batch=True,  # Required for SQLite ALTER TABLE support
        compare_type=True,     # Compare column types
        compare_server_default=True,  # Compare server defaults
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with connection"""
    # Determine database type for migration options
    database_url = get_database_url()
    is_sqlite = database_url.startswith(("sqlite:", "sqlite+aiosqlite:"))
    
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # SQLite specific options
        render_as_batch=is_sqlite,  # Required for SQLite ALTER TABLE support
        compare_type=True,
        compare_server_default=True,
        # Include schemas in autogenerate (for MySQL/MariaDB)
        include_schemas=not is_sqlite,
        # Transaction per migration for better error handling
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    """Run migrations in async mode for async engines"""
    database_url = get_database_url()
    
    # Convert sync URL to async if needed
    if database_url.startswith("sqlite:///"):
        async_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif database_url.startswith("mysql://"):
        async_url = database_url.replace("mysql://", "mysql+aiomysql://")
    elif database_url.startswith("mariadb://"):
        async_url = database_url.replace("mariadb://", "mysql+aiomysql://")
    else:
        async_url = database_url

    connectable = create_async_engine(async_url)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    database_url = get_database_url()
    
    # Check if we need async mode
    if database_url.startswith(("sqlite+aiosqlite:", "mysql+aiomysql:")):
        asyncio.run(run_async_migrations())
        return
    
    # Sync mode for traditional URLs
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


# Auto-detect and run appropriate migration mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
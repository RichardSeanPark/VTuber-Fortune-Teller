"""
Database configuration and session management

SQLAlchemy database setup with SQLite/MariaDB support and connection management.
"""

from typing import AsyncGenerator, Optional
import asyncio
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import event, text, create_engine
from sqlalchemy.engine import Engine
import logging
logger = logging.getLogger(__name__)

from .settings import get_settings


Base = declarative_base()


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[AsyncEngine] = None
        self._sync_engine: Optional[Engine] = None
        self._sessionmaker = None
        self._sync_sessionmaker = None
    
    def _is_sqlite(self, database_url: str) -> bool:
        """Check if database URL is for SQLite"""
        return database_url.startswith(("sqlite:", "sqlite+aiosqlite:"))
        
    async def initialize(self) -> None:
        """Initialize database connection"""
        try:
            database_url = self.settings.get_database_url()
            logger.info(f"Initializing database connection: {database_url.split('@')[0]}...")
            
            # Create async engine with conditional pooling
            engine_kwargs = {
                "echo": self.settings.database.echo,
                "future": True
            }
            
            # Only add pooling parameters for non-SQLite databases
            if not self._is_sqlite(database_url):
                engine_kwargs.update({
                    "pool_size": self.settings.database.pool_size,
                    "max_overflow": self.settings.database.max_overflow,
                    "pool_timeout": self.settings.database.pool_timeout,
                    "pool_recycle": self.settings.database.pool_recycle,
                })
            
            self._engine = create_async_engine(database_url, **engine_kwargs)
            
            # Create sync engine for FastAPI dependencies
            sync_database_url = database_url.replace("+aiosqlite", "").replace("postgresql+asyncpg", "postgresql")
            self._sync_engine = create_engine(sync_database_url, **{k: v for k, v in engine_kwargs.items() if k != "future"})
            
            # Configure SQLite-specific settings
            if self._is_sqlite(database_url):
                await self._configure_sqlite()
                self._configure_sync_sqlite()
            
            # Create session factories
            self._sessionmaker = sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            self._sync_sessionmaker = sessionmaker(
                bind=self._sync_engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # Test connection
            await self._test_connection()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _configure_sqlite(self) -> None:
        """Configure SQLite-specific settings"""
        if not self._engine:
            return
            
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and features"""
            cursor = dbapi_connection.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set journal mode to WAL for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Set synchronous mode to NORMAL for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Set cache size (negative value means KB)
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB
            
            # Enable automatic index creation
            cursor.execute("PRAGMA automatic_index=ON")
            
            # Set temporary storage to memory for better performance
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Set memory mapped I/O size (256MB)
            cursor.execute("PRAGMA mmap_size=268435456")
            
            # Set WAL auto checkpoint
            cursor.execute("PRAGMA wal_autocheckpoint=1000")
            
            # Optimize page size (4KB is usually optimal)
            cursor.execute("PRAGMA page_size=4096")
            
            cursor.close()
    
    def _configure_sync_sqlite(self) -> None:
        """Configure SQLite-specific settings for sync engine"""
        if not self._sync_engine:
            return
            
        @event.listens_for(self._sync_engine, "connect")
        def set_sqlite_pragma_sync(dbapi_connection, connection_record):
            """Set SQLite pragmas for better performance and features"""
            cursor = dbapi_connection.cursor()
            
            # Enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Set journal mode to WAL for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Set synchronous mode to NORMAL for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Set cache size (negative value means KB)
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB
            
            # Enable automatic index creation
            cursor.execute("PRAGMA automatic_index=ON")
            
            # Set temporary storage to memory for better performance
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            # Set memory mapped I/O size (256MB)
            cursor.execute("PRAGMA mmap_size=268435456")
            
            # Set WAL auto checkpoint
            cursor.execute("PRAGMA wal_autocheckpoint=1000")
            
            # Optimize page size (4KB is usually optimal)
            cursor.execute("PRAGMA page_size=4096")
            
            cursor.close()
    
    async def _test_connection(self) -> None:
        """Test database connection"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            logger.debug("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def create_tables(self) -> None:
        """Create all database tables"""
        if not self._sync_engine:
            raise RuntimeError("Database engine not initialized")
        
        try:
            # Import all models to ensure they're registered
            from ..models import Base, User, ChatSession, ChatMessage, FortuneSession, TarotCardDB, ZodiacInfo, Live2DModel, ContentCache, SystemSetting, UserAnalytics
            
            # Create tables using sync engine with the correct Base
            Base.metadata.create_all(self._sync_engine)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        
        if not self.settings.is_development():
            raise RuntimeError("Cannot drop tables in non-development environment")
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            
            logger.warning("All database tables dropped")
            
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None
        
        if self._sync_engine:
            self._sync_engine.dispose()
            self._sync_engine = None
            self._sync_sessionmaker = None
            
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self._sessionmaker:
            raise RuntimeError("Database not initialized")
        
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def get_session_direct(self) -> AsyncSession:
        """Get database session directly (for dependency injection)"""
        if not self._sessionmaker:
            raise RuntimeError("Database not initialized")
        
        return self._sessionmaker()
    
    def get_sync_session(self) -> Session:
        """Get synchronous database session"""
        if not self._sync_sessionmaker:
            raise RuntimeError("Database not initialized")
        
        return self._sync_sessionmaker()
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        return self._engine
    
    async def execute_raw_sql(self, sql: str, params: dict = None) -> any:
        """Execute raw SQL query"""
        async with self.get_session() as session:
            result = await session.execute(text(sql), params or {})
            return result


# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection functions
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection function for FastAPI (async)"""
    async with db_manager.get_session() as session:
        yield session


def get_db():
    """Dependency injection function for FastAPI (sync)"""
    session = db_manager.get_sync_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_database_engine() -> AsyncEngine:
    """Get database engine for dependency injection"""
    return db_manager.engine


# Database lifecycle management
async def init_database() -> None:
    """Initialize database (called during app startup)"""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database() -> None:
    """Close database connections (called during app shutdown)"""
    await db_manager.close()


# Database utilities
async def check_database_health() -> dict:
    """Check database health status"""
    try:
        async with db_manager.get_session() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1 as health_check"))
            health_check = result.scalar()
            
            # Get connection info
            if db_manager._is_sqlite(db_manager.settings.get_database_url()):
                # SQLite specific queries
                result = await session.execute(text("PRAGMA integrity_check"))
                integrity = result.scalar()
                
                result = await session.execute(text("PRAGMA journal_mode"))
                journal_mode = result.scalar()
                
                return {
                    "status": "healthy" if health_check == 1 else "unhealthy",
                    "database_type": "sqlite",
                    "integrity_check": integrity,
                    "journal_mode": journal_mode
                }
            else:
                # MariaDB/MySQL specific queries
                result = await session.execute(text("SELECT VERSION() as version"))
                version = result.scalar()
                
                result = await session.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
                connections = result.fetchone()
                
                return {
                    "status": "healthy" if health_check == 1 else "unhealthy",
                    "database_type": "mariadb",
                    "version": version,
                    "connections": connections[1] if connections else "unknown"
                }
                
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


async def reset_database() -> None:
    """Reset database (development only)"""
    if not db_manager.settings.is_development():
        raise RuntimeError("Database reset only allowed in development environment")
    
    logger.warning("Resetting database...")
    await db_manager.drop_tables()
    await db_manager.create_tables()
    logger.info("Database reset completed")


# Migration utilities
async def run_migrations() -> None:
    """Run database migrations (placeholder for Alembic integration)"""
    # This will be implemented with Alembic
    logger.info("Database migrations completed")


# Connection pool monitoring
async def get_connection_pool_status() -> dict:
    """Get connection pool status"""
    if not db_manager._engine:
        return {"status": "not_initialized"}
    
    pool = db_manager._engine.pool
    
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid()
    }


# Development helpers
async def seed_database() -> None:
    """Seed database with initial data (development)"""
    if not db_manager.settings.is_development():
        logger.warning("Database seeding skipped in non-development environment")
        return
    
    try:
        # from ..models.seed_data import seed_initial_data
        # await seed_initial_data(db_manager)
        logger.info("Database seeded successfully (placeholder)")
    except ImportError:
        logger.warning("No seed data module found")
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        raise


if __name__ == "__main__":
    # Simple test script
    async def test_database():
        await init_database()
        health = await check_database_health()
        print(f"Database health: {health}")
        pool_status = await get_connection_pool_status()
        print(f"Connection pool: {pool_status}")
        await close_database()
    
    asyncio.run(test_database())
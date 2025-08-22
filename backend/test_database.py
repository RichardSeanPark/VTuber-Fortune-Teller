#!/usr/bin/env python3
"""
Simple database test script

Test database connection, table creation, and basic operations.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fortune_vtuber.config.database import db_manager
from fortune_vtuber.services.database_service import database_service
from fortune_vtuber.services.cache_service import cache_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_connection():
    """Test basic database connection"""
    logger.info("Testing basic database connection...")
    
    try:
        # Initialize database
        await db_manager.initialize()
        
        # Check health
        health = await db_manager.check_database_health()
        logger.info(f"Database health: {health}")
        
        # Create tables
        await db_manager.create_tables()
        logger.info("Tables created successfully")
        
        # Test basic query
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1 as test"))
            value = result.scalar()
            assert value == 1
            logger.info("Basic query test passed")
        
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def test_cache_service():
    """Test cache service"""
    logger.info("Testing cache service...")
    
    try:
        # Test basic cache operations
        cache_service.set("test_key", {"data": "test_value"}, 60)
        
        value = cache_service.get("test_key")
        assert value is not None
        assert value["data"] == "test_value"
        
        # Test cache stats
        stats = cache_service.get_stats()
        logger.info(f"Cache stats: {stats}")
        
        logger.info("Cache service test passed")
        return True
        
    except Exception as e:
        logger.error(f"Cache service test failed: {e}")
        return False


async def test_database_optimization():
    """Test database optimization"""
    logger.info("Testing database optimization...")
    
    try:
        # Test SQLite optimization
        async with db_manager.get_session() as session:
            await database_service.optimize_sqlite_connection(session)
        
        # Get database info
        db_info = await database_service.get_database_info()
        logger.info(f"Database info: {db_info}")
        
        # Check if WAL mode is enabled
        if db_info.get('journal_mode') == 'wal':
            logger.info("WAL mode enabled successfully")
        else:
            logger.warning("WAL mode not enabled")
        
        return True
        
    except Exception as e:
        logger.error(f"Database optimization test failed: {e}")
        return False


async def test_basic_table_operations():
    """Test basic table operations"""
    logger.info("Testing basic table operations...")
    
    try:
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # Test creating a simple record in system_settings table
            await session.execute(text("""
                INSERT OR REPLACE INTO system_settings 
                (setting_key, setting_value, setting_type, description, is_public)
                VALUES ('test_setting', 'test_value', 'string', 'Test setting', 0)
            """))
            
            # Test reading the record
            result = await session.execute(text("""
                SELECT setting_value FROM system_settings 
                WHERE setting_key = 'test_setting'
            """))
            
            value = result.scalar()
            assert value == 'test_value'
            
            logger.info("Basic table operations test passed")
            
        return True
        
    except Exception as e:
        logger.error(f"Basic table operations test failed: {e}")
        return False


async def main():
    """Main test function"""
    logger.info("Starting database tests...")
    
    tests = [
        ("Basic Connection", test_basic_connection),
        ("Cache Service", test_cache_service),
        ("Database Optimization", test_database_optimization),
        ("Table Operations", test_basic_table_operations),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} test...")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results[test_name] = result
            logger.info(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ {test_name}: FAILED - {e}")
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASSED ✅" if result else "FAILED ❌"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Database is working correctly.")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) failed. Please check the logs.")
    
    # Cleanup
    try:
        await db_manager.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
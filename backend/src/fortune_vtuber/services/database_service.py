"""
Database service with SQLite optimization and connection management

Provides database operations with SQLite-specific optimizations and monitoring.
"""

import sqlite3
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import logging

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.engine import Engine

from ..config.database import db_manager
from .cache_service import cache_service, cached_query

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service with SQLite optimization and monitoring"""
    
    def __init__(self):
        self.stats = {
            'queries_executed': 0,
            'query_time_total': 0.0,
            'slow_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'connection_count': 0
        }
        self.slow_query_threshold = 1.0  # seconds
        
        # Setup database event listeners for monitoring
        self._setup_monitoring()
        self._initialized = False
    
    async def initialize(self):
        """Initialize database service"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("DatabaseService initialized")
    
    async def shutdown(self):
        """Shutdown database service"""
        self._initialized = False
        logger.info("DatabaseService shutdown")
    
    def _setup_monitoring(self):
        """Setup SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query start time"""
            context._query_start_time = time.time()
            self.stats['queries_executed'] += 1
        
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Record query execution time"""
            if hasattr(context, '_query_start_time'):
                query_time = time.time() - context._query_start_time
                self.stats['query_time_total'] += query_time
                
                if query_time > self.slow_query_threshold:
                    self.stats['slow_queries'] += 1
                    logger.warning(f"Slow query detected ({query_time:.3f}s): {statement[:100]}...")
    
    async def optimize_sqlite_connection(self, session: AsyncSession):
        """Apply SQLite-specific optimizations"""
        try:
            optimizations = [
                # Enable foreign key constraints
                "PRAGMA foreign_keys = ON",
                
                # Set journal mode to WAL for better concurrency
                "PRAGMA journal_mode = WAL",
                
                # Set synchronous mode to NORMAL for better performance
                "PRAGMA synchronous = NORMAL",
                
                # Set cache size to 64MB
                "PRAGMA cache_size = -64000",
                
                # Enable automatic index creation
                "PRAGMA automatic_index = ON",
                
                # Set temp store to memory for better performance
                "PRAGMA temp_store = MEMORY",
                
                # Set mmap size to 268MB for memory-mapped I/O
                "PRAGMA mmap_size = 268435456",
                
                # Optimize page size (4KB is usually optimal)
                "PRAGMA page_size = 4096",
                
                # Set WAL autocheckpoint
                "PRAGMA wal_autocheckpoint = 1000"
            ]
            
            for pragma in optimizations:
                await session.execute(text(pragma))
                
            logger.debug("Applied SQLite optimizations")
            
        except Exception as e:
            logger.error(f"Failed to apply SQLite optimizations: {e}")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """Get SQLite database information"""
        try:
            async with db_manager.get_session() as session:
                # Basic database info
                info_queries = {
                    'user_version': "PRAGMA user_version",
                    'schema_version': "PRAGMA schema_version",
                    'page_count': "PRAGMA page_count",
                    'page_size': "PRAGMA page_size",
                    'cache_size': "PRAGMA cache_size",
                    'journal_mode': "PRAGMA journal_mode",
                    'synchronous': "PRAGMA synchronous",
                    'foreign_keys': "PRAGMA foreign_keys",
                    'temp_store': "PRAGMA temp_store",
                    'mmap_size': "PRAGMA mmap_size",
                    'wal_autocheckpoint': "PRAGMA wal_autocheckpoint"
                }
                
                info = {}
                for key, query in info_queries.items():
                    result = await session.execute(text(query))
                    info[key] = result.scalar()
                
                # Calculate database size
                database_size_mb = (info['page_count'] * info['page_size']) / (1024 * 1024)
                info['database_size_mb'] = round(database_size_mb, 2)
                
                return info
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}
    
    async def analyze_database(self) -> Dict[str, Any]:
        """Analyze database for optimization opportunities"""
        try:
            async with db_manager.get_session() as session:
                analysis = {
                    'table_info': {},
                    'index_usage': {},
                    'recommendations': []
                }
                
                # Get table information
                tables_result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                )
                
                for (table_name,) in tables_result:
                    # Table info
                    table_info_result = await session.execute(text(f"PRAGMA table_info({table_name})"))
                    columns = table_info_result.fetchall()
                    
                    # Table stats
                    count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.scalar()
                    
                    analysis['table_info'][table_name] = {
                        'columns': len(columns),
                        'row_count': row_count,
                        'column_details': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'not_null': bool(col[3]),
                                'default_value': col[4],
                                'primary_key': bool(col[5])
                            }
                            for col in columns
                        ]
                    }
                    
                    # Check for missing indexes on foreign keys
                    foreign_keys_result = await session.execute(text(f"PRAGMA foreign_key_list({table_name})"))
                    for fk in foreign_keys_result:
                        fk_column = fk[3]  # 'from' column
                        
                        # Check if there's an index on this foreign key
                        index_check = await session.execute(
                            text(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}' AND sql LIKE '%{fk_column}%'")
                        )
                        
                        if not index_check.fetchone():
                            analysis['recommendations'].append(
                                f"Consider adding index on {table_name}.{fk_column} (foreign key)"
                            )
                
                # Get index usage statistics
                indexes_result = await session.execute(
                    text("SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
                )
                
                for index_name, table_name in indexes_result:
                    analysis['index_usage'][index_name] = {
                        'table': table_name,
                        'created': True  # Basic info, SQLite doesn't provide usage stats
                    }
                
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to analyze database: {e}")
            return {}
    
    async def vacuum_database(self) -> Dict[str, Any]:
        """Vacuum database to reclaim space and optimize"""
        try:
            start_time = time.time()
            
            async with db_manager.get_session() as session:
                # Get size before vacuum
                before_info = await self.get_database_info()
                before_size = before_info.get('database_size_mb', 0)
                
                # Perform VACUUM
                await session.execute(text("VACUUM"))
                
                # Get size after vacuum
                after_info = await self.get_database_info()
                after_size = after_info.get('database_size_mb', 0)
                
                elapsed_time = time.time() - start_time
                space_reclaimed = before_size - after_size
                
                result = {
                    'success': True,
                    'elapsed_seconds': round(elapsed_time, 2),
                    'size_before_mb': before_size,
                    'size_after_mb': after_size,
                    'space_reclaimed_mb': round(space_reclaimed, 2),
                    'space_reclaimed_percent': round((space_reclaimed / before_size * 100) if before_size > 0 else 0, 2)
                }
                
                logger.info(f"Database vacuum completed: {space_reclaimed:.2f}MB reclaimed in {elapsed_time:.2f}s")
                return result
                
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Analyze slow queries (requires query log)"""
        # Note: SQLite doesn't have built-in slow query log
        # This would need to be implemented with application-level logging
        
        slow_queries = []
        
        # For now, return analysis based on stats
        if self.stats['slow_queries'] > 0:
            slow_queries.append({
                'type': 'summary',
                'slow_query_count': self.stats['slow_queries'],
                'total_queries': self.stats['queries_executed'],
                'slow_query_percentage': round(
                    (self.stats['slow_queries'] / self.stats['queries_executed'] * 100)
                    if self.stats['queries_executed'] > 0 else 0, 2
                ),
                'average_query_time': round(
                    (self.stats['query_time_total'] / self.stats['queries_executed'])
                    if self.stats['queries_executed'] > 0 else 0, 3
                ),
                'recommendation': 'Consider adding indexes or optimizing queries that take longer than 1 second'
            })
        
        return slow_queries
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            db_info = await self.get_database_info()
            analysis = await self.analyze_database()
            cache_stats = cache_service.get_stats()
            
            return {
                'database_info': db_info,
                'query_stats': {
                    'queries_executed': self.stats['queries_executed'],
                    'total_query_time': round(self.stats['query_time_total'], 3),
                    'average_query_time': round(
                        (self.stats['query_time_total'] / self.stats['queries_executed'])
                        if self.stats['queries_executed'] > 0 else 0, 3
                    ),
                    'slow_queries': self.stats['slow_queries'],
                    'slow_query_threshold': self.slow_query_threshold
                },
                'table_stats': analysis.get('table_info', {}),
                'index_stats': analysis.get('index_usage', {}),
                'recommendations': analysis.get('recommendations', []),
                'cache_stats': cache_stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}
    
    async def optimize_database(self) -> Dict[str, Any]:
        """Perform comprehensive database optimization"""
        try:
            start_time = time.time()
            results = {
                'optimizations_applied': [],
                'errors': []
            }
            
            async with db_manager.get_session() as session:
                try:
                    # Apply SQLite optimizations
                    await self.optimize_sqlite_connection(session)
                    results['optimizations_applied'].append('SQLite connection optimizations')
                except Exception as e:
                    results['errors'].append(f"SQLite optimization error: {e}")
                
                try:
                    # Analyze tables to update statistics
                    await session.execute(text("ANALYZE"))
                    results['optimizations_applied'].append('Database statistics updated')
                except Exception as e:
                    results['errors'].append(f"ANALYZE error: {e}")
                
                try:
                    # Rebuild indexes (not needed for SQLite usually, but good practice)
                    await session.execute(text("REINDEX"))
                    results['optimizations_applied'].append('Indexes rebuilt')
                except Exception as e:
                    results['errors'].append(f"REINDEX error: {e}")
            
            # Clear expired cache entries
            try:
                expired_cleared = cache_service.cleanup_expired()
                results['optimizations_applied'].append(f'Cleared {expired_cleared} expired cache entries')
            except Exception as e:
                results['errors'].append(f"Cache cleanup error: {e}")
            
            elapsed_time = time.time() - start_time
            results['elapsed_seconds'] = round(elapsed_time, 2)
            results['success'] = len(results['errors']) == 0
            
            logger.info(f"Database optimization completed in {elapsed_time:.2f}s with {len(results['errors'])} errors")
            return results
            
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
            return {
                'success': False,
                'error': str(e),
                'elapsed_seconds': 0
            }
    
    async def backup_database(self, backup_path: str) -> Dict[str, Any]:
        """Create database backup"""
        try:
            start_time = time.time()
            
            # For SQLite, we can use the backup API
            # This is a simple file copy for SQLite
            import shutil
            
            # Get current database path
            database_url = db_manager.settings.get_database_url()
            if database_url.startswith('sqlite:///'):
                db_path = database_url.replace('sqlite:///', '')
                
                # Create backup
                shutil.copy2(db_path, backup_path)
                
                elapsed_time = time.time() - start_time
                
                return {
                    'success': True,
                    'backup_path': backup_path,
                    'elapsed_seconds': round(elapsed_time, 2),
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Backup only supported for SQLite databases'
                }
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global database service instance
database_service = DatabaseService()
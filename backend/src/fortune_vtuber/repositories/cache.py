"""
Content cache repository
"""

from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session

from .base import BaseRepository, RepositoryError
from ..models.cache import ContentCache


class ContentCacheRepository(BaseRepository[ContentCache]):
    """Repository for ContentCache"""
    
    def __init__(self, session: Session):
        super().__init__(ContentCache, session)
    
    async def get_cache(self, cache_key: str) -> Optional[ContentCache]:
        """Get cache by key if valid"""
        try:
            result = await self.session.execute(
                select(ContentCache).where(ContentCache.cache_key == cache_key)
            )
            cache = result.scalar_one_or_none()
            
            if not cache:
                return None
            
            if cache.is_expired:
                # Clean up expired cache
                await self.session.delete(cache)
                await self.session.flush()
                return None
            
            return cache
        except Exception as e:
            raise RepositoryError(f"Failed to get cache: {e}")
    
    async def set_cache(self, cache_key: str, cache_type: str, 
                       content: Dict[str, Any], ttl_hours: int = 24) -> ContentCache:
        """Set cache content"""
        try:
            # Remove existing cache with same key
            await self.session.execute(
                delete(ContentCache).where(ContentCache.cache_key == cache_key)
            )
            
            # Create new cache entry
            cache = ContentCache(
                cache_key=cache_key,
                cache_type=cache_type,
                expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
            )
            cache.content_dict = content
            
            self.session.add(cache)
            await self.session.flush()
            
            return cache
        except Exception as e:
            raise RepositoryError(f"Failed to set cache: {e}")
    
    async def get_or_set_cache(self, cache_key: str, cache_type: str,
                              content_generator: Callable[[], Dict[str, Any]], 
                              ttl_hours: int = 24) -> Dict[str, Any]:
        """Get cache or set if not exists"""
        try:
            cache = await self.get_cache(cache_key)
            
            if cache:
                return cache.access()
            
            # Generate new content
            content = content_generator()
            
            # Set cache
            cache = await self.set_cache(cache_key, cache_type, content, ttl_hours)
            
            return cache.access()
        except Exception as e:
            raise RepositoryError(f"Failed to get or set cache: {e}")
    
    async def find_by_type(self, cache_type: str, include_expired: bool = False) -> List[ContentCache]:
        """Find caches by type"""
        try:
            query = select(ContentCache).where(ContentCache.cache_type == cache_type)
            
            if not include_expired:
                query = query.where(ContentCache.expires_at > datetime.utcnow())
            
            result = await self.session.execute(
                query.order_by(ContentCache.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find caches by type: {e}")
    
    async def cleanup_expired(self) -> int:
        """Clean up expired caches"""
        try:
            result = await self.session.execute(
                delete(ContentCache).where(
                    ContentCache.expires_at < datetime.utcnow()
                )
            )
            
            count = result.rowcount
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup expired caches: {e}")
    
    async def cleanup_by_type(self, cache_type: str) -> int:
        """Clean up caches by type"""
        try:
            result = await self.session.execute(
                delete(ContentCache).where(ContentCache.cache_type == cache_type)
            )
            
            count = result.rowcount
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup caches by type: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Total cache count
            total_count = await self.count()
            
            # Valid cache count
            valid_count_result = await self.session.execute(
                select(func.count(ContentCache.id)).where(
                    ContentCache.expires_at > datetime.utcnow()
                )
            )
            valid_count = valid_count_result.scalar() or 0
            
            # Expired cache count
            expired_count = total_count - valid_count
            
            # Cache by type
            type_stats_result = await self.session.execute(
                select(
                    ContentCache.cache_type,
                    func.count(ContentCache.id).label('count'),
                    func.sum(ContentCache.access_count).label('total_access')
                ).group_by(ContentCache.cache_type)
            )
            
            # Most accessed caches
            top_accessed_result = await self.session.execute(
                select(ContentCache)
                .where(ContentCache.expires_at > datetime.utcnow())
                .order_by(ContentCache.access_count.desc())
                .limit(10)
            )
            
            return {
                'total_count': total_count,
                'valid_count': valid_count,
                'expired_count': expired_count,
                'hit_rate': (valid_count / total_count * 100) if total_count > 0 else 0,
                'by_type': {
                    stat.cache_type: {
                        'count': stat.count,
                        'total_access': stat.total_access or 0
                    }
                    for stat in type_stats_result.all()
                },
                'top_accessed': [
                    {
                        'cache_key': cache.cache_key,
                        'cache_type': cache.cache_type,
                        'access_count': cache.access_count,
                        'created_at': cache.created_at.isoformat()
                    }
                    for cache in top_accessed_result.scalars()
                ]
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get cache statistics: {e}")
"""
In-memory caching service for SQLite performance optimization

Implements intelligent caching strategy with TTL and memory management for SQLite database optimization.
"""

import json
import time
import threading
from typing import Any, Dict, Optional, Callable, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at

    @property
    def ttl_remaining(self) -> float:
        """Get remaining TTL in seconds"""
        return max(0, self.expires_at - time.time())

    def access(self) -> Any:
        """Access cache entry and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class CacheService:
    """In-memory caching service with intelligent eviction and SQLite optimization"""

    def __init__(self, max_size_mb: int = 64, default_ttl_seconds: int = 3600):
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0,
            'size_bytes': 0
        }

        # Start background cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_worker, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"CacheService initialized with {max_size_mb}MB max size, {default_ttl_seconds}s default TTL")
    
    async def initialize(self):
        """Initialize cache service (async compatibility)"""
        logger.info("CacheService initialization completed")
    
    async def shutdown(self):
        """Shutdown cache service and cleanup"""
        self.clear()
        logger.info("CacheService shutdown completed")

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            self._stats['total_requests'] += 1

            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            entry = self._cache[key]

            if entry.is_expired:
                self._remove_entry(key)
                self._stats['misses'] += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._stats['hits'] += 1

            return entry.access()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl

        with self._lock:
            now = time.time()
            size_bytes = self._calculate_size(value)

            # Remove existing entry if present
            if key in self._cache:
                self._remove_entry(key)

            # Check if we need to evict entries
            while self._needs_eviction(size_bytes):
                if not self._evict_lru():
                    logger.warning(f"Failed to make space for cache entry: {key}")
                    return False

            # Create new entry
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + ttl_seconds,
                access_count=0,
                last_accessed=now,
                size_bytes=size_bytes
            )

            self._cache[key] = entry
            self._stats['size_bytes'] += size_bytes

            logger.debug(f"Cached {key} with TTL {ttl_seconds}s, size {size_bytes} bytes")
            return True

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_entry(key)
                logger.debug(f"Deleted cache key: {key}")
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired:
                self._remove_entry(key)
                return False

            return True

    def clear(self) -> int:
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._stats['size_bytes'] = 0
            logger.info(f"Cleared {count} cache entries")
            return count

    def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern"""
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]

            for key in keys_to_remove:
                self._remove_entry(key)

            logger.info(f"Cleared {len(keys_to_remove)} cache entries matching pattern: {pattern}")
            return len(keys_to_remove)

    def get_or_set(self, key: str, generator: Callable[[], Any], 
                   ttl_seconds: Optional[int] = None) -> Any:
        """Get value from cache or set it using generator function"""
        value = self.get(key)
        if value is not None:
            return value

        # Generate new value
        try:
            new_value = generator()
            self.set(key, new_value, ttl_seconds)
            return new_value
        except Exception as e:
            logger.error(f"Failed to generate cache value for key {key}: {e}")
            raise

    def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache"""
        with self._lock:
            result = {}
            for key in keys:
                value = self.get(key)
                if value is not None:
                    result[key] = value
            return result

    def set_multi(self, items: Dict[str, Any], ttl_seconds: Optional[int] = None) -> int:
        """Set multiple values in cache"""
        success_count = 0
        for key, value in items.items():
            if self.set(key, value, ttl_seconds):
                success_count += 1
        return success_count

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            hit_rate = (
                self._stats['hits'] / self._stats['total_requests'] * 100
                if self._stats['total_requests'] > 0 else 0
            )

            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'evictions': self._stats['evictions'],
                'total_requests': self._stats['total_requests'],
                'hit_rate_percent': round(hit_rate, 2),
                'current_entries': len(self._cache),
                'size_bytes': self._stats['size_bytes'],
                'size_mb': round(self._stats['size_bytes'] / (1024 * 1024), 2),
                'max_size_mb': round(self.max_size_bytes / (1024 * 1024), 2),
                'memory_usage_percent': round(
                    self._stats['size_bytes'] / self.max_size_bytes * 100, 2
                )
            }

    def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about cache entry"""
        with self._lock:
            if key not in self._cache:
                return None

            entry = self._cache[key]
            return {
                'key': key,
                'created_at': datetime.fromtimestamp(entry.created_at).isoformat(),
                'expires_at': datetime.fromtimestamp(entry.expires_at).isoformat(),
                'age_seconds': entry.age_seconds,
                'ttl_remaining': entry.ttl_remaining,
                'access_count': entry.access_count,
                'last_accessed': datetime.fromtimestamp(entry.last_accessed).isoformat() if entry.last_accessed else None,
                'size_bytes': entry.size_bytes,
                'is_expired': entry.is_expired
            }

    def get_all_keys(self, include_expired: bool = False) -> List[str]:
        """Get all cache keys"""
        with self._lock:
            if include_expired:
                return list(self._cache.keys())

            return [
                key for key, entry in self._cache.items()
                if not entry.is_expired
            ]

    def cleanup_expired(self) -> int:
        """Manually cleanup expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]

            for key in expired_keys:
                self._remove_entry(key)

            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            return len(expired_keys)

    # Private methods

    def _remove_entry(self, key: str) -> None:
        """Remove cache entry and update stats"""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._stats['size_bytes'] -= entry.size_bytes

    def _needs_eviction(self, new_entry_size: int) -> bool:
        """Check if eviction is needed for new entry"""
        return (self._stats['size_bytes'] + new_entry_size) > self.max_size_bytes

    def _evict_lru(self) -> bool:
        """Evict least recently used entry"""
        if not self._cache:
            return False

        # Find LRU entry (first in OrderedDict)
        lru_key = next(iter(self._cache))
        self._remove_entry(lru_key)
        self._stats['evictions'] += 1

        logger.debug(f"Evicted LRU cache entry: {lru_key}")
        return True

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes"""
        try:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (dict, list)):
                return len(json.dumps(value, ensure_ascii=False).encode('utf-8'))
            elif isinstance(value, (int, float)):
                return 8  # Approximate size
            elif isinstance(value, bool):
                return 1
            else:
                # Fallback for other types
                return len(str(value).encode('utf-8'))
        except Exception:
            return 100  # Default size if calculation fails

    def _cleanup_worker(self) -> None:
        """Background thread for periodic cleanup"""
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                expired_count = self.cleanup_expired()
                if expired_count > 0:
                    logger.debug(f"Background cleanup removed {expired_count} expired entries")
            except Exception as e:
                logger.error(f"Error in cache cleanup worker: {e}")


# Global cache instance
cache_service = CacheService()


# Utility functions for SQLite optimization
def get_cache_key(*args, **kwargs) -> str:
    """Generate cache key from arguments"""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        key_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}:{value}")
    
    return ":".join(key_parts)


def cached_query(ttl_seconds: int = 3600):
    """Decorator for caching query results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"query:{func.__name__}:{get_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for query: {func.__name__}")
                return result
            
            # Execute query and cache result
            logger.debug(f"Cache miss for query: {func.__name__}")
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache entries matching pattern"""
    return cache_service.clear_pattern(pattern)


def warm_cache(cache_entries: List[Tuple[str, Callable, int]]) -> Dict[str, bool]:
    """Warm cache with predefined entries"""
    results = {}
    
    for key, generator, ttl in cache_entries:
        try:
            value = generator()
            success = cache_service.set(key, value, ttl)
            results[key] = success
            logger.debug(f"Cache warming {'succeeded' if success else 'failed'} for key: {key}")
        except Exception as e:
            logger.error(f"Failed to warm cache for key {key}: {e}")
            results[key] = False
    
    return results
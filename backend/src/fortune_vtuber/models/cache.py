"""
Content caching models for performance optimization
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import Column, String, Text, Integer, DateTime, CheckConstraint, Index, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from .base import BaseModel as SQLBaseModel


class ContentCache(SQLBaseModel):
    """Content cache model for storing frequently accessed data"""
    
    __tablename__ = 'content_cache'
    
    # Cache Identification
    cache_key = Column(
        String(255),
        unique=True,
        nullable=False,
        comment="Unique cache key"
    )
    
    cache_type = Column(
        String(50),
        nullable=False,
        comment="Type of cached content"
    )
    
    # Cache Content (JSON string for SQLite)
    content = Column(
        Text,
        nullable=False,
        comment="Cached content as JSON string"
    )
    
    # Cache Lifecycle
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="Cache expiration timestamp"
    )
    
    # Access Tracking
    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times cache was accessed"
    )
    
    last_accessed_at = Column(
        DateTime,
        nullable=True,
        comment="Last access timestamp"
    )
    
    # Add check constraint
    __table_args__ = (
        CheckConstraint(
            cache_type.in_([
                'daily_fortune', 'zodiac_weekly', 'zodiac_monthly', 
                'tarot_cards', 'zodiac_info', 'system_config',
                'user_profile', 'live2d_config', 'api_response'
            ]),
            name='check_cache_type'
        ),
        # Add indexes for performance
        Index('idx_cache_key_type', cache_key, cache_type),
        Index('idx_cache_expires_at', expires_at),
        Index('idx_cache_type_expires', cache_type, expires_at),
    )
    
    # Properties
    @property
    def content_dict(self) -> Dict[str, Any]:
        """Get content as dictionary"""
        if not self.content:
            return {}
        try:
            return json.loads(self.content)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @content_dict.setter
    def content_dict(self, value: Dict[str, Any]):
        """Set content from dictionary"""
        if value is None:
            self.content = None
        else:
            self.content = json.dumps(value, ensure_ascii=False)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if cache is valid (not expired)"""
        return not self.is_expired
    
    @property
    def time_to_expire(self) -> Optional[timedelta]:
        """Get time until expiration"""
        if self.is_expired:
            return None
        return self.expires_at - datetime.utcnow()
    
    @property
    def time_since_created(self) -> timedelta:
        """Get time since creation"""
        return datetime.utcnow() - self.created_at
    
    @property
    def time_since_accessed(self) -> Optional[timedelta]:
        """Get time since last access"""
        if not self.last_accessed_at:
            return None
        return datetime.utcnow() - self.last_accessed_at
    
    def extend_ttl(self, hours: int = 24):
        """Extend cache TTL"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def set_ttl(self, hours: int = 24):
        """Set cache TTL from now"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
    
    def invalidate(self):
        """Invalidate cache (mark as expired)"""
        self.expires_at = datetime.utcnow() - timedelta(seconds=1)
    
    def access(self) -> Dict[str, Any]:
        """Access cache content and update access tracking"""
        self.access_count += 1
        self.last_accessed_at = datetime.utcnow()
        return self.content_dict
    
    @classmethod
    def get_cache(cls, session: Session, cache_key: str) -> Optional['ContentCache']:
        """Get cache by key if valid"""
        cache = session.query(cls).filter(cls.cache_key == cache_key).first()
        
        if not cache:
            return None
        
        if cache.is_expired:
            # Clean up expired cache
            session.delete(cache)
            session.flush()
            return None
        
        return cache
    
    @classmethod
    def set_cache(cls, session: Session, cache_key: str, cache_type: str, 
                 content: Dict[str, Any], ttl_hours: int = 24) -> 'ContentCache':
        """Set cache content"""
        # Remove existing cache with same key
        existing = session.query(cls).filter(cls.cache_key == cache_key).first()
        if existing:
            session.delete(existing)
            session.flush()
        
        # Create new cache entry
        cache = cls(
            cache_key=cache_key,
            cache_type=cache_type,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        cache.content_dict = content
        
        session.add(cache)
        session.flush()
        
        return cache
    
    @classmethod
    def get_or_set_cache(cls, session: Session, cache_key: str, cache_type: str,
                        content_generator, ttl_hours: int = 24) -> Dict[str, Any]:
        """Get cache or set if not exists"""
        cache = cls.get_cache(session, cache_key)
        
        if cache:
            return cache.access()
        
        # Generate new content
        content = content_generator() if callable(content_generator) else content_generator
        
        # Set cache
        cache = cls.set_cache(session, cache_key, cache_type, content, ttl_hours)
        
        return cache.access()
    
    @classmethod
    def find_by_type(cls, session: Session, cache_type: str, 
                    include_expired: bool = False) -> List['ContentCache']:
        """Find caches by type"""
        query = session.query(cls).filter(cls.cache_type == cache_type)
        
        if not include_expired:
            query = query.filter(cls.expires_at > datetime.utcnow())
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def cleanup_expired(cls, session: Session) -> int:
        """Clean up expired caches"""
        expired_caches = session.query(cls).filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_caches)
        for cache in expired_caches:
            session.delete(cache)
        
        session.flush()
        return count
    
    @classmethod
    def cleanup_by_type(cls, session: Session, cache_type: str) -> int:
        """Clean up caches by type"""
        caches = session.query(cls).filter(cls.cache_type == cache_type).all()
        
        count = len(caches)
        for cache in caches:
            session.delete(cache)
        
        session.flush()
        return count
    
    @classmethod
    def get_cache_stats(cls, session: Session) -> Dict[str, Any]:
        """Get cache statistics"""
        # Total cache count
        total_count = session.query(cls).count()
        
        # Valid cache count
        valid_count = session.query(cls).filter(
            cls.expires_at > datetime.utcnow()
        ).count()
        
        # Expired cache count
        expired_count = total_count - valid_count
        
        # Cache by type
        type_stats = session.query(
            cls.cache_type,
            func.count(cls.id).label('count'),
            func.sum(cls.access_count).label('total_access')
        ).group_by(cls.cache_type).all()
        
        # Most accessed caches
        top_accessed = session.query(cls).filter(
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.access_count.desc()).limit(10).all()
        
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
                for stat in type_stats
            },
            'top_accessed': [
                {
                    'cache_key': cache.cache_key,
                    'cache_type': cache.cache_type,
                    'access_count': cache.access_count,
                    'created_at': cache.created_at.isoformat()
                }
                for cache in top_accessed
            ]
        }
    
    @classmethod
    def generate_cache_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from components"""
        # Convert all arguments to strings
        key_parts = [prefix]
        
        # Add positional arguments
        for arg in args:
            key_parts.append(str(arg))
        
        # Add keyword arguments (sorted for consistency)
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)
    
    def __repr__(self) -> str:
        return f"<ContentCache(key={self.cache_key}, type={self.cache_type}, expires={self.expires_at})>"


# Pydantic models for API
class ContentCacheCreate(BaseModel):
    """Content cache creation model"""
    
    cache_key: str = Field(..., min_length=1, max_length=255)
    cache_type: str = Field(..., pattern=r'^(daily_fortune|zodiac_weekly|zodiac_monthly|tarot_cards|zodiac_info|system_config|user_profile|live2d_config|api_response)$')
    content: Dict[str, Any]
    ttl_hours: int = Field(24, ge=1, le=8760)  # 1 hour to 1 year


class ContentCacheResponse(BaseModel):
    """Content cache response model"""
    
    id: int
    cache_key: str
    cache_type: str
    content: Dict[str, Any]
    expires_at: datetime
    access_count: int
    last_accessed_at: Optional[datetime]
    is_expired: bool
    is_valid: bool
    time_to_expire: Optional[str]  # Human readable
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CacheStatsResponse(BaseModel):
    """Cache statistics response model"""
    
    total_count: int
    valid_count: int
    expired_count: int
    hit_rate: float
    by_type: Dict[str, Dict[str, int]]
    top_accessed: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True


class CacheKeyRequest(BaseModel):
    """Cache key generation request"""
    
    prefix: str = Field(..., min_length=1, max_length=50)
    args: List[str] = Field(default_factory=list)
    kwargs: Dict[str, str] = Field(default_factory=dict)


class CacheKeyResponse(BaseModel):
    """Cache key generation response"""
    
    cache_key: str
    prefix: str
    components: List[str]
    
    class Config:
        from_attributes = True
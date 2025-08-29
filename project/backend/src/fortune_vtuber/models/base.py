"""
Base SQLAlchemy model with common fields and utilities
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Session
from pydantic import BaseModel


Base = declarative_base()


class TimestampMixin:
    """Mixin for timestamp fields"""
    
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Record creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Record last update timestamp"
    )


class UUIDMixin:
    """Mixin for UUID field"""
    
    uuid = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        comment="External UUID identifier"
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Soft delete flag"
    )
    
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp"
    )


class BaseModel(Base, TimestampMixin):
    """Base model with common fields and methods"""
    
    __abstract__ = True
    
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key"
    )
    
    @declared_attr
    def __tablename__(cls):
        """Generate table name from class name"""
        # Convert CamelCase to snake_case
        import re
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    
    @hybrid_property
    def created_at_utc(self) -> datetime:
        """Get created_at in UTC"""
        if self.created_at.tzinfo is None:
            return self.created_at.replace(tzinfo=timezone.utc)
        return self.created_at.astimezone(timezone.utc)
    
    @hybrid_property
    def updated_at_utc(self) -> datetime:
        """Get updated_at in UTC"""
        if self.updated_at.tzinfo is None:
            return self.updated_at.replace(tzinfo=timezone.utc)
        return self.updated_at.astimezone(timezone.utc)
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """Convert model to dictionary"""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name in exclude:
                continue
                
            value = getattr(self, column.name)
            
            # Handle datetime serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            
            result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None):
        """Update model from dictionary"""
        exclude = exclude or ['id', 'created_at', 'updated_at']
        
        for key, value in data.items():
            if key in exclude:
                continue
                
            if hasattr(self, key):
                setattr(self, key, value)
    
    @classmethod
    def create(cls, session: Session, **kwargs):
        """Create new instance"""
        instance = cls(**kwargs)
        session.add(instance)
        session.flush()  # Get ID without committing
        return instance
    
    def save(self, session: Session):
        """Save instance to database"""
        session.add(self)
        session.flush()
        return self
    
    def delete(self, session: Session, soft: bool = True):
        """Delete instance (soft or hard)"""
        if soft and hasattr(self, 'is_deleted'):
            self.is_deleted = True
            self.deleted_at = datetime.now(timezone.utc)
            session.add(self)
        else:
            session.delete(self)
        session.flush()
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class UUIDBaseModel(BaseModel, UUIDMixin):
    """Base model with UUID support"""
    
    __abstract__ = True
    
    def __repr__(self) -> str:
        """String representation with UUID"""
        return f"<{self.__class__.__name__}(id={self.id}, uuid={self.uuid})>"


class SoftDeleteBaseModel(BaseModel, SoftDeleteMixin):
    """Base model with soft delete support"""
    
    __abstract__ = True
    
    @classmethod
    def active(cls, session: Session):
        """Get only non-deleted records"""
        return session.query(cls).filter(cls.is_deleted == False)
    
    @classmethod
    def deleted(cls, session: Session):
        """Get only deleted records"""
        return session.query(cls).filter(cls.is_deleted == True)


class FullBaseModel(UUIDBaseModel, SoftDeleteMixin):
    """Full featured base model with UUID and soft delete"""
    
    __abstract__ = True
    
    @classmethod
    def active(cls, session: Session):
        """Get only non-deleted records"""
        return session.query(cls).filter(cls.is_deleted == False)


# Pydantic models for API serialization
try:
    from pydantic import BaseModel as PydanticBaseModel
    
    class BaseResponse(PydanticBaseModel):
        """Base response model"""
        
        id: int
        created_at: datetime
        updated_at: datetime
        
        class Config:
            from_attributes = True


    class UUIDResponse(BaseResponse):
        """Response model with UUID"""
        
        uuid: str


    class TimestampResponse(PydanticBaseModel):
        """Response model with only timestamps"""
        
        created_at: datetime
        updated_at: datetime
        
        class Config:
            from_attributes = True

except ImportError:
    # Pydantic not available, skip response models
    BaseResponse = None
    UUIDResponse = None
    TimestampResponse = None


# Utility functions
def generate_uuid() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
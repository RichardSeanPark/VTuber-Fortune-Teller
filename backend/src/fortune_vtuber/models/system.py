"""
System configuration and analytics models
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
import json

from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel, Field, validator

from .base import BaseModel as SQLBaseModel


class SystemSetting(SQLBaseModel):
    """System configuration settings"""
    
    __tablename__ = 'system_settings'
    
    # Setting Identification
    setting_key = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="Unique setting key"
    )
    
    # Setting Value
    setting_value = Column(
        Text,
        nullable=True,
        comment="Setting value (can be string, JSON, etc.)"
    )
    
    setting_type = Column(
        String(20),
        default='string',
        nullable=False,
        comment="Type of setting value"
    )
    
    # Setting Metadata
    description = Column(
        Text,
        nullable=True,
        comment="Setting description"
    )
    
    is_public = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether setting can be exposed to client"
    )
    
    # Add check constraint
    __table_args__ = (
        CheckConstraint(
            setting_type.in_(['string', 'integer', 'boolean', 'json', 'float']),
            name='check_setting_type'
        ),
        Index('idx_setting_key', setting_key),
        Index('idx_setting_public', is_public),
    )
    
    # Properties
    @property
    def typed_value(self) -> Union[str, int, bool, float, Dict[str, Any], None]:
        """Get value with proper type conversion"""
        if self.setting_value is None:
            return None
        
        try:
            if self.setting_type == 'integer':
                return int(self.setting_value)
            elif self.setting_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes', 'on')
            elif self.setting_type == 'float':
                return float(self.setting_value)
            elif self.setting_type == 'json':
                return json.loads(self.setting_value)
            else:  # string
                return self.setting_value
        except (ValueError, json.JSONDecodeError):
            return self.setting_value
    
    @typed_value.setter
    def typed_value(self, value: Union[str, int, bool, float, Dict[str, Any], None]):
        """Set value with automatic type detection"""
        if value is None:
            self.setting_value = None
            return
        
        if isinstance(value, bool):
            self.setting_type = 'boolean'
            self.setting_value = str(value).lower()
        elif isinstance(value, int):
            self.setting_type = 'integer'
            self.setting_value = str(value)
        elif isinstance(value, float):
            self.setting_type = 'float'
            self.setting_value = str(value)
        elif isinstance(value, (dict, list)):
            self.setting_type = 'json'
            self.setting_value = json.dumps(value, ensure_ascii=False)
        else:
            self.setting_type = 'string'
            self.setting_value = str(value)
    
    @classmethod
    def get_setting(cls, session: Session, key: str, default: Any = None) -> Any:
        """Get setting value by key"""
        setting = session.query(cls).filter(cls.setting_key == key).first()
        return setting.typed_value if setting else default
    
    @classmethod
    def set_setting(cls, session: Session, key: str, value: Any, 
                   description: str = None, is_public: bool = False) -> 'SystemSetting':
        """Set setting value"""
        setting = session.query(cls).filter(cls.setting_key == key).first()
        
        if setting:
            setting.typed_value = value
            if description is not None:
                setting.description = description
            setting.is_public = is_public
        else:
            setting = cls(
                setting_key=key,
                description=description,
                is_public=is_public
            )
            setting.typed_value = value
            session.add(setting)
        
        session.flush()
        return setting
    
    @classmethod
    def get_public_settings(cls, session: Session) -> Dict[str, Any]:
        """Get all public settings"""
        settings = session.query(cls).filter(cls.is_public == True).all()
        return {setting.setting_key: setting.typed_value for setting in settings}
    
    @classmethod
    def get_all_settings(cls, session: Session) -> Dict[str, Any]:
        """Get all settings (admin only)"""
        settings = session.query(cls).all()
        return {setting.setting_key: setting.typed_value for setting in settings}
    
    @classmethod
    def bulk_update_settings(cls, session: Session, settings_dict: Dict[str, Any]):
        """Bulk update multiple settings"""
        for key, value in settings_dict.items():
            cls.set_setting(session, key, value)
        session.flush()
    
    @classmethod
    def delete_setting(cls, session: Session, key: str) -> bool:
        """Delete setting by key"""
        setting = session.query(cls).filter(cls.setting_key == key).first()
        if setting:
            session.delete(setting)
            session.flush()
            return True
        return False
    
    def __repr__(self) -> str:
        return f"<SystemSetting(key={self.setting_key}, type={self.setting_type}, public={self.is_public})>"


class UserAnalytics(SQLBaseModel):
    """User analytics and event tracking"""
    
    __tablename__ = 'user_analytics'
    
    # User Association (optional for anonymous events)
    user_uuid = Column(
        String(36),
        ForeignKey('users.uuid', ondelete='SET NULL'),
        nullable=True,
        comment="Associated user UUID"
    )
    
    # Session Association (optional)
    session_id = Column(
        String(36),
        ForeignKey('chat_sessions.session_id', ondelete='CASCADE'),
        nullable=True,
        comment="Associated session ID"
    )
    
    # Event Information
    event_type = Column(
        String(50),
        nullable=False,
        comment="Type of event"
    )
    
    event_data = Column(
        Text,
        nullable=True,
        comment="Event data as JSON string"
    )
    
    # Client Information
    ip_address = Column(
        String(45),  # IPv6 support
        nullable=True,
        comment="Client IP address"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="Client User-Agent string"
    )
    
    # Add check constraint
    __table_args__ = (
        CheckConstraint(
            event_type.in_([
                'session_start', 'session_end', 'fortune_request', 
                'message_sent', 'error_occurred', 'page_view',
                'api_call', 'live2d_interaction', 'user_registration',
                'user_login', 'user_logout', 'cache_hit', 'cache_miss'
            ]),
            name='check_event_type'
        ),
        Index('idx_analytics_user_uuid', user_uuid),
        Index('idx_analytics_session_id', session_id),
        Index('idx_analytics_event_type', event_type),
        Index('idx_analytics_created_at', 'created_at'),
        Index('idx_analytics_event_date', event_type, 'created_at'),
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="analytics",
        foreign_keys=[user_uuid]
    )
    
    chat_session = relationship(
        "ChatSession",
        back_populates="analytics",
        foreign_keys=[session_id]
    )
    
    # Properties
    @property
    def event_data_dict(self) -> Dict[str, Any]:
        """Get event data as dictionary"""
        if not self.event_data:
            return {}
        try:
            return json.loads(self.event_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @event_data_dict.setter
    def event_data_dict(self, value: Dict[str, Any]):
        """Set event data from dictionary"""
        if value is None:
            self.event_data = None
        else:
            self.event_data = json.dumps(value, ensure_ascii=False)
    
    @classmethod
    def log_event(cls, session: Session, event_type: str, 
                 user_uuid: str = None, session_id: str = None,
                 event_data: Dict[str, Any] = None, 
                 ip_address: str = None, user_agent: str = None) -> 'UserAnalytics':
        """Log analytics event"""
        event = cls(
            user_uuid=user_uuid,
            session_id=session_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if event_data:
            event.event_data_dict = event_data
        
        session.add(event)
        session.flush()
        
        return event
    
    @classmethod
    def get_user_events(cls, session: Session, user_uuid: str, 
                       event_type: str = None, limit: int = 100) -> List['UserAnalytics']:
        """Get user events"""
        query = session.query(cls).filter(cls.user_uuid == user_uuid)
        
        if event_type:
            query = query.filter(cls.event_type == event_type)
        
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_session_events(cls, session: Session, session_id: str) -> List['UserAnalytics']:
        """Get session events"""
        return session.query(cls).filter(
            cls.session_id == session_id
        ).order_by(cls.created_at.asc()).all()
    
    @classmethod
    def get_event_stats(cls, session: Session, days: int = 7) -> Dict[str, Any]:
        """Get event statistics"""
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total events by type
        event_counts = session.query(
            cls.event_type,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(cls.event_type).all()
        
        # Daily event counts
        daily_counts = session.query(
            func.date(cls.created_at).label('date'),
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(func.date(cls.created_at)).all()
        
        # Unique users
        unique_users = session.query(
            func.count(func.distinct(cls.user_uuid))
        ).filter(
            cls.created_at >= cutoff_date,
            cls.user_uuid.isnot(None)
        ).scalar()
        
        # Unique sessions
        unique_sessions = session.query(
            func.count(func.distinct(cls.session_id))
        ).filter(
            cls.created_at >= cutoff_date,
            cls.session_id.isnot(None)
        ).scalar()
        
        return {
            'period_days': days,
            'total_events': sum(count.count for count in event_counts),
            'unique_users': unique_users or 0,
            'unique_sessions': unique_sessions or 0,
            'events_by_type': {
                count.event_type: count.count 
                for count in event_counts
            },
            'daily_events': {
                str(count.date): count.count 
                for count in daily_counts
            }
        }
    
    @classmethod
    def cleanup_old_events(cls, session: Session, days: int = 90) -> int:
        """Clean up old analytics events"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_events = session.query(cls).filter(
            cls.created_at < cutoff_date
        ).all()
        
        count = len(old_events)
        for event in old_events:
            session.delete(event)
        
        session.flush()
        return count
    
    def __repr__(self) -> str:
        return f"<UserAnalytics(event={self.event_type}, user={self.user_uuid}, session={self.session_id})>"


# Pydantic models for API
class SystemSettingCreate(BaseModel):
    """System setting creation model"""
    
    setting_key: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9_.-]+$')
    setting_value: Optional[Union[str, int, bool, float, Dict[str, Any]]] = None
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = Field(False)


class SystemSettingUpdate(BaseModel):
    """System setting update model"""
    
    setting_value: Optional[Union[str, int, bool, float, Dict[str, Any]]] = None
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = None


class SystemSettingResponse(BaseModel):
    """System setting response model"""
    
    id: int
    setting_key: str
    setting_value: Optional[Union[str, int, bool, float, Dict[str, Any]]]
    setting_type: str
    description: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserAnalyticsCreate(BaseModel):
    """User analytics creation model"""
    
    user_uuid: Optional[str] = Field(None, min_length=36, max_length=36)
    session_id: Optional[str] = Field(None, min_length=36, max_length=36)
    event_type: str = Field(..., pattern=r'^(session_start|session_end|fortune_request|message_sent|error_occurred|page_view|api_call|live2d_interaction|user_registration|user_login|user_logout|cache_hit|cache_miss)$')
    event_data: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=1000)


class UserAnalyticsResponse(BaseModel):
    """User analytics response model"""
    
    id: int
    user_uuid: Optional[str]
    session_id: Optional[str]
    event_type: str
    event_data: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalyticsStatsResponse(BaseModel):
    """Analytics statistics response model"""
    
    period_days: int
    total_events: int
    unique_users: int
    unique_sessions: int
    events_by_type: Dict[str, int]
    daily_events: Dict[str, int]
    
    class Config:
        from_attributes = True


class PublicSettingsResponse(BaseModel):
    """Public settings response model"""
    
    settings: Dict[str, Any]
    
    class Config:
        from_attributes = True
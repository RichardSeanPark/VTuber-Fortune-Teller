"""
User model for fortune telling application
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import Column, String, Text, Boolean, DateTime, Date, Time, Integer, CheckConstraint, Index, ForeignKey
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel, Field, validator

from .base import UUIDBaseModel, SoftDeleteMixin, BaseModel as SQLBaseModel


class User(UUIDBaseModel, SoftDeleteMixin):
    """User model for storing user information"""
    
    __tablename__ = 'users'
    
    # Basic Information
    name = Column(
        String(50),
        nullable=True,
        comment="User display name"
    )
    
    # Birth Information for Fortune Telling
    birth_date = Column(
        String(10),  # YYYY-MM-DD format for SQLite compatibility
        nullable=True,
        comment="Birth date in YYYY-MM-DD format"
    )
    
    birth_time = Column(
        String(8),   # HH:MM:SS format for SQLite compatibility
        nullable=True,
        comment="Birth time in HH:MM:SS format"
    )
    
    birth_location = Column(
        String(100),
        nullable=True,
        comment="Birth location for astrology"
    )
    
    # Zodiac Sign
    zodiac_sign = Column(
        String(20),
        nullable=True,
        comment="Zodiac sign"
    )
    
    # User Preferences (JSON string for SQLite)
    preferences = Column(
        Text,
        nullable=True,
        comment="User preferences as JSON string"
    )
    
    # Activity Tracking
    last_access = Column(
        DateTime,
        nullable=True,
        comment="Last access timestamp"
    )
    
    last_active_at = Column(
        DateTime,
        nullable=True,
        comment="Last activity timestamp"
    )
    
    access_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times user has accessed the service"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="User account status"
    )
    
    is_anonymous = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is an anonymous user"
    )
    
    # Add check constraint for zodiac signs and performance indexes
    __table_args__ = (
        CheckConstraint(
            zodiac_sign.in_([
                'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
            ]),
            name='check_zodiac_sign'
        ),
        # Performance indexes for common queries
        Index('idx_users_uuid', 'uuid'),
        Index('idx_users_active', 'is_active', 'is_deleted'),
        Index('idx_users_last_active', 'last_active_at'),
        Index('idx_users_zodiac', 'zodiac_sign'),
        Index('idx_users_birth_date', 'birth_date'),
    )
    
    # Relationships
    chat_sessions = relationship(
        "ChatSession",
        back_populates="user",
        foreign_keys="ChatSession.user_uuid",
        primaryjoin="User.uuid == ChatSession.user_uuid",
        cascade="all, delete-orphan"
    )
    
    fortune_sessions = relationship(
        "FortuneSession", 
        back_populates="user",
        foreign_keys="FortuneSession.user_uuid",
        primaryjoin="User.uuid == FortuneSession.user_uuid",
        cascade="all, delete-orphan"
    )
    
    analytics = relationship(
        "UserAnalytics",
        back_populates="user",
        foreign_keys="UserAnalytics.user_uuid",
        primaryjoin="User.uuid == UserAnalytics.user_uuid",
        cascade="all, delete-orphan"
    )
    
    user_sessions = relationship(
        "UserSession",
        back_populates="user",
        foreign_keys="UserSession.user_uuid",
        primaryjoin="User.uuid == UserSession.user_uuid",
        cascade="all, delete-orphan"
    )
    
    preferences_rel = relationship(
        "UserPreferences",
        back_populates="user",
        foreign_keys="UserPreferences.user_uuid",
        primaryjoin="User.uuid == UserPreferences.user_uuid",
        cascade="all, delete-orphan",
        uselist=False
    )
    
    # Properties
    @property
    def preferences_dict(self) -> Dict[str, Any]:
        """Get preferences as dictionary"""
        if not self.preferences:
            return {}
        try:
            return json.loads(self.preferences)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @preferences_dict.setter
    def preferences_dict(self, value: Dict[str, Any]):
        """Set preferences from dictionary"""
        if value is None:
            self.preferences = None
        else:
            self.preferences = json.dumps(value, ensure_ascii=False)
    
    @property
    def birth_date_obj(self) -> Optional[date]:
        """Get birth_date as date object"""
        if not self.birth_date:
            return None
        try:
            return datetime.strptime(self.birth_date, "%Y-%m-%d").date()
        except ValueError:
            return None
    
    @birth_date_obj.setter
    def birth_date_obj(self, value: Optional[date]):
        """Set birth_date from date object"""
        if value is None:
            self.birth_date = None
        else:
            self.birth_date = value.strftime("%Y-%m-%d")
    
    @property
    def age(self) -> Optional[int]:
        """Calculate age from birth date"""
        if not self.birth_date_obj:
            return None
        
        today = date.today()
        age = today.year - self.birth_date_obj.year
        
        # Adjust if birthday hasn't occurred this year
        if today < self.birth_date_obj.replace(year=today.year):
            age -= 1
            
        return max(0, age)
    
    def get_fortune_preference(self, key: str, default: Any = None) -> Any:
        """Get specific fortune preference"""
        prefs = self.preferences_dict
        return prefs.get('fortune', {}).get(key, default)
    
    def set_fortune_preference(self, key: str, value: Any):
        """Set specific fortune preference"""
        prefs = self.preferences_dict
        if 'fortune' not in prefs:
            prefs['fortune'] = {}
        prefs['fortune'][key] = value
        self.preferences_dict = prefs
    
    def update_last_active(self):
        """Update last active timestamp"""
        self.last_active_at = datetime.utcnow()
    
    @classmethod
    def find_by_uuid(cls, session: Session, user_uuid: str) -> Optional['User']:
        """Find user by UUID"""
        return session.query(cls).filter(
            cls.uuid == user_uuid,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def find_active_users(cls, session: Session, limit: int = 100) -> List['User']:
        """Find active users"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_deleted == False
        ).order_by(cls.last_active_at.desc()).limit(limit).all()
    
    @classmethod
    def find_by_zodiac(cls, session: Session, zodiac_sign: str) -> List['User']:
        """Find users by zodiac sign"""
        return session.query(cls).filter(
            cls.zodiac_sign == zodiac_sign,
            cls.is_deleted == False
        ).all()
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with privacy options"""
        result = super().to_dict()
        
        # Add computed properties
        result['age'] = self.age
        result['preferences'] = self.preferences_dict
        
        # Remove sensitive data unless explicitly requested
        if not include_sensitive:
            sensitive_fields = ['birth_date', 'birth_time', 'birth_location']
            for field in sensitive_fields:
                result.pop(field, None)
        
        return result
    
    def __repr__(self) -> str:
        return f"<User(uuid={self.uuid}, name={self.name}, zodiac={self.zodiac_sign})>"


# Pydantic models for API
class UserCreate(BaseModel):
    """User creation model"""
    
    name: Optional[str] = Field(None, max_length=50)
    birth_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    birth_time: Optional[str] = Field(None, pattern=r'^\d{2}:\d{2}:\d{2}$')
    birth_location: Optional[str] = Field(None, max_length=100)
    zodiac_sign: Optional[str] = Field(None, pattern=r'^(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)$')
    preferences: Optional[Dict[str, Any]] = None
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError('Birth date must be in YYYY-MM-DD format')
    
    @validator('birth_time')
    def validate_birth_time(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%H:%M:%S")
            return v
        except ValueError:
            raise ValueError('Birth time must be in HH:MM:SS format')


class UserUpdate(BaseModel):
    """User update model"""
    
    name: Optional[str] = Field(None, max_length=50)
    birth_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    birth_time: Optional[str] = Field(None, pattern=r'^\d{2}:\d{2}:\d{2}$')
    birth_location: Optional[str] = Field(None, max_length=100)
    zodiac_sign: Optional[str] = Field(None, pattern=r'^(aries|taurus|gemini|cancer|leo|virgo|libra|scorpio|sagittarius|capricorn|aquarius|pisces)$')
    preferences: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model"""
    
    id: int
    uuid: str
    name: Optional[str]
    zodiac_sign: Optional[str]
    age: Optional[int]
    preferences: Dict[str, Any]
    last_active_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """User detail response model with sensitive data"""
    
    birth_date: Optional[str]
    birth_time: Optional[str]
    birth_location: Optional[str]


class UserListResponse(BaseModel):
    """User list response model"""
    
    users: List[UserResponse]
    total: int
    page: int
    page_size: int


class UserSession(UUIDBaseModel):
    """User session model for authentication"""
    
    __tablename__ = 'user_sessions'
    
    session_id = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="Unique session identifier"
    )
    
    user_uuid = Column(
        String(36),
        ForeignKey('users.uuid'),
        nullable=False,
        comment="Reference to user"
    )
    
    session_type = Column(
        String(20),
        default="web",
        nullable=False,
        comment="Type of session (web, mobile, etc.)"
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="Session expiration time"
    )
    
    last_activity = Column(
        DateTime,
        nullable=True,
        comment="Last activity in this session"
    )
    
    ended_at = Column(
        DateTime,
        nullable=True,
        comment="Session end time"
    )
    
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Session status"
    )
    
    session_metadata = Column(
        Text,
        nullable=True,
        comment="Session metadata as JSON"
    )
    
    # Performance indexes
    __table_args__ = (
        Index('idx_user_sessions_session_id', 'session_id'),
        Index('idx_user_sessions_user_uuid', 'user_uuid'),
        Index('idx_user_sessions_active', 'is_active', 'expires_at'),
        Index('idx_user_sessions_type', 'session_type'),
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="user_sessions",
        foreign_keys=[user_uuid]
    )
    
    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        if not self.session_metadata:
            return {}
        try:
            return json.loads(self.session_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value: Dict[str, Any]):
        """Set metadata from dictionary"""
        if value is None:
            self.session_metadata = None
        else:
            self.session_metadata = json.dumps(value, ensure_ascii=False)
    
    @classmethod
    def find_by_session_id(cls, session: Session, session_id: str) -> Optional['UserSession']:
        """Find session by session ID"""
        return session.query(cls).filter(cls.session_id == session_id).first()
    
    @classmethod
    def find_active_session(cls, session: Session, user_uuid: str, session_type: str = "web") -> Optional['UserSession']:
        """Find active session for user and type"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid,
            cls.session_type == session_type,
            cls.is_active == True,
            cls.expires_at > datetime.now()
        ).first()
    
    @classmethod
    def find_active_sessions_by_user(cls, session: Session, user_uuid: str) -> List['UserSession']:
        """Find all active sessions for a user"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid,
            cls.is_active == True,
            cls.expires_at > datetime.now()
        ).all()
    
    @classmethod
    def find_sessions_by_user(cls, session: Session, user_uuid: str, limit: int = 50) -> List['UserSession']:
        """Find all sessions for a user"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def find_expired_sessions(cls, session: Session) -> List['UserSession']:
        """Find expired sessions"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.expires_at < datetime.now()
        ).all()


class UserPreferences(UUIDBaseModel):
    """User preferences model"""
    
    __tablename__ = 'user_preferences'
    
    user_uuid = Column(
        String(36),
        ForeignKey('users.uuid'),
        unique=True,
        nullable=False,
        comment="Reference to user"
    )
    
    fortune_types = Column(
        Text,
        nullable=True,
        comment="Preferred fortune types as JSON array"
    )
    
    notification_time = Column(
        String(5),
        default="09:00",
        nullable=True,
        comment="Notification time in HH:MM format"
    )
    
    theme = Column(
        String(20),
        default="light",
        nullable=False,
        comment="UI theme preference"
    )
    
    language = Column(
        String(5),
        default="ko",
        nullable=False,
        comment="Language preference"
    )
    
    timezone = Column(
        String(50),
        default="Asia/Seoul",
        nullable=False,
        comment="Timezone preference"
    )
    
    privacy_settings = Column(
        Text,
        nullable=True,
        comment="Privacy settings as JSON"
    )
    
    # Performance indexes
    __table_args__ = (
        Index('idx_user_preferences_user_uuid', 'user_uuid'),
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="preferences_rel",
        foreign_keys=[user_uuid]
    )
    
    @property
    def fortune_types_list(self) -> List[str]:
        """Get fortune types as list"""
        if not self.fortune_types:
            return ["daily", "tarot"]
        try:
            return json.loads(self.fortune_types)
        except (json.JSONDecodeError, TypeError):
            return ["daily", "tarot"]
    
    @fortune_types_list.setter
    def fortune_types_list(self, value: List[str]):
        """Set fortune types from list"""
        if value is None:
            self.fortune_types = None
        else:
            self.fortune_types = json.dumps(value, ensure_ascii=False)
    
    @property
    def privacy_settings_dict(self) -> Dict[str, Any]:
        """Get privacy settings as dictionary"""
        if not self.privacy_settings:
            return {
                "save_history": True,
                "personalization": True,
                "analytics": False
            }
        try:
            return json.loads(self.privacy_settings)
        except (json.JSONDecodeError, TypeError):
            return {
                "save_history": True,
                "personalization": True,
                "analytics": False
            }
    
    @privacy_settings_dict.setter
    def privacy_settings_dict(self, value: Dict[str, Any]):
        """Set privacy settings from dictionary"""
        if value is None:
            self.privacy_settings = None
        else:
            self.privacy_settings = json.dumps(value, ensure_ascii=False)
    
    @classmethod
    def find_by_user_uuid(cls, session: Session, user_uuid: str) -> Optional['UserPreferences']:
        """Find preferences by user UUID"""
        return session.query(cls).filter(cls.user_uuid == user_uuid).first()
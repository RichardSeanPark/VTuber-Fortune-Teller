"""
Chat models for WebSocket communication and message storage
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from enum import Enum

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel, Field, validator

from .base import UUIDBaseModel, SoftDeleteMixin


class MessageType(str, Enum):
    """Chat message type enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FORTUNE = "fortune"
    LIVE2D_ACTION = "live2d_action"
    ERROR = "error"


class ChatSession(UUIDBaseModel):
    """Chat session model for managing user conversations"""
    
    __tablename__ = 'chat_sessions'
    
    # Session Identification
    session_id = Column(
        String(36),
        unique=True,
        nullable=False,
        comment="Session UUID for WebSocket identification"
    )
    
    # User Association (optional for anonymous sessions)
    user_uuid = Column(
        String(36),
        ForeignKey('users.uuid', ondelete='SET NULL'),
        nullable=True,
        comment="Associated user UUID"
    )
    
    # Session Configuration
    character_name = Column(
        String(50),
        default='미라',
        nullable=False,
        comment="Live2D character name"
    )
    
    session_type = Column(
        String(20),
        default='anonymous',
        nullable=False,
        comment="Session type: anonymous or registered"
    )
    
    # Session Lifecycle
    started_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Session start timestamp"
    )
    
    ended_at = Column(
        DateTime,
        nullable=True,
        comment="Session end timestamp"
    )
    
    expires_at = Column(
        DateTime,
        nullable=True,
        comment="Session expiration timestamp"
    )
    
    status = Column(
        String(20),
        default='active',
        nullable=False,
        comment="Session status: active, expired, closed"
    )
    
    # Active flag for quick queries
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether session is currently active"
    )
    
    # Session Metadata (JSON string for SQLite)
    session_metadata = Column(
        Text,
        nullable=True,
        comment="Session metadata as JSON string"
    )
    
    # Add check constraints and performance indexes
    __table_args__ = (
        CheckConstraint(
            session_type.in_(['anonymous', 'registered']),
            name='check_session_type'
        ),
        CheckConstraint(
            status.in_(['active', 'expired', 'closed']),
            name='check_session_status'
        ),
        # Performance indexes for common queries
        Index('idx_chat_sessions_session_id', 'session_id'),
        Index('idx_chat_sessions_user_uuid', 'user_uuid'),
        Index('idx_chat_sessions_status', 'status'),
        Index('idx_chat_sessions_active', 'is_active'),
        Index('idx_chat_sessions_created', 'started_at'),
        Index('idx_chat_sessions_expires', 'expires_at'),
        Index('idx_chat_sessions_user_status', 'user_uuid', 'status'),
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="chat_sessions",
        foreign_keys=[user_uuid],
        primaryjoin="ChatSession.user_uuid == User.uuid"
    )
    
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    fortune_sessions = relationship(
        "FortuneSession",
        back_populates="chat_session",
        cascade="all, delete-orphan"
    )
    
    analytics = relationship(
        "UserAnalytics",
        back_populates="chat_session",
        cascade="all, delete-orphan"
    )
    
    # Properties
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
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get session duration"""
        if self.ended_at:
            return self.ended_at - self.started_at
        return datetime.utcnow() - self.started_at
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        if self.status in ['expired', 'closed']:
            return True
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False
    
    @property
    def is_active_computed(self) -> bool:
        """Check if session is computationally active"""
        return self.status == 'active' and not self.is_expired
    
    @property
    def message_count(self) -> int:
        """Get message count"""
        return len(self.messages) if self.messages else 0
    
    def extend_session(self, hours: int = 24):
        """Extend session expiration"""
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        if self.status == 'expired':
            self.status = 'active'
    
    def close_session(self):
        """Close the session"""
        self.status = 'closed'
        self.ended_at = datetime.utcnow()
    
    def expire_session(self):
        """Mark session as expired"""
        self.status = 'expired'
        self.ended_at = datetime.utcnow()
    
    @classmethod
    def find_by_session_id(cls, session: Session, session_id: str) -> Optional['ChatSession']:
        """Find session by session_id"""
        return session.query(cls).filter(cls.session_id == session_id).first()
    
    @classmethod
    def find_active_sessions(cls, session: Session, limit: int = 100) -> List['ChatSession']:
        """Find active sessions"""
        return session.query(cls).filter(
            cls.status == 'active'
        ).order_by(cls.started_at.desc()).limit(limit).all()
    
    @classmethod
    def find_user_sessions(cls, session: Session, user_uuid: str, limit: int = 10) -> List['ChatSession']:
        """Find user's recent sessions"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid
        ).order_by(cls.started_at.desc()).limit(limit).all()
    
    @classmethod
    def cleanup_expired_sessions(cls, session: Session, cutoff_hours: int = 24) -> int:
        """Clean up expired sessions"""
        cutoff_time = datetime.utcnow() - timedelta(hours=cutoff_hours)
        
        expired_sessions = session.query(cls).filter(
            cls.status == 'active',
            cls.expires_at < cutoff_time
        ).all()
        
        count = 0
        for chat_session in expired_sessions:
            chat_session.expire_session()
            count += 1
        
        return count
    
    def __repr__(self) -> str:
        return f"<ChatSession(session_id={self.session_id}, status={self.status}, user={self.user_uuid})>"


class ChatMessage(UUIDBaseModel, SoftDeleteMixin):
    """Chat message model for storing conversation history"""
    
    __tablename__ = 'chat_messages'
    
    # Message Identification
    message_id = Column(
        String(36),
        unique=True,
        nullable=False,
        comment="Message UUID"
    )
    
    # Session Association
    session_id = Column(
        String(36),
        ForeignKey('chat_sessions.session_id', ondelete='CASCADE'),
        nullable=False,
        comment="Associated session ID"
    )
    
    # Message Content
    sender_type = Column(
        String(20),
        nullable=False,
        comment="Message sender: user or assistant"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="Message content"
    )
    
    content_type = Column(
        String(20),
        default='text',
        nullable=False,
        comment="Content type: text, fortune_result, system"
    )
    
    # Live2D Integration
    live2d_emotion = Column(
        String(20),
        nullable=True,
        comment="Live2D emotion for this message"
    )
    
    live2d_motion = Column(
        String(50),
        nullable=True,
        comment="Live2D motion for this message"
    )
    
    # Audio Support
    audio_url = Column(
        String(255),
        nullable=True,
        comment="TTS audio file URL"
    )
    
    # Message Metadata (JSON string for SQLite)
    message_metadata = Column(
        Text,
        nullable=True,
        comment="Message metadata as JSON string"
    )
    
    # Add check constraints and performance indexes
    __table_args__ = (
        CheckConstraint(
            sender_type.in_(['user', 'assistant']),
            name='check_sender_type'
        ),
        CheckConstraint(
            content_type.in_(['text', 'fortune_result', 'system']),
            name='check_content_type'
        ),
        # Performance indexes for common queries
        Index('idx_chat_messages_session_id', 'session_id'),
        Index('idx_chat_messages_created', 'created_at'),
        Index('idx_chat_messages_sender', 'sender_type'),
        Index('idx_chat_messages_content_type', 'content_type'),
        Index('idx_chat_messages_session_created', 'session_id', 'created_at'),
    )
    
    # Relationships
    session = relationship(
        "ChatSession",
        back_populates="messages",
        foreign_keys=[session_id]
    )
    
    # Properties
    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        if not self.message_metadata:
            return {}
        try:
            return json.loads(self.message_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value: Dict[str, Any]):
        """Set metadata from dictionary"""
        if value is None:
            self.message_metadata = None
        else:
            self.message_metadata = json.dumps(value, ensure_ascii=False)
    
    @property
    def is_user_message(self) -> bool:
        """Check if message is from user"""
        return self.sender_type == 'user'
    
    @property
    def is_assistant_message(self) -> bool:
        """Check if message is from assistant"""
        return self.sender_type == 'assistant'
    
    @property
    def has_audio(self) -> bool:
        """Check if message has audio"""
        return bool(self.audio_url)
    
    @property
    def has_live2d_animation(self) -> bool:
        """Check if message has Live2D animation"""
        return bool(self.live2d_emotion or self.live2d_motion)
    
    @classmethod
    def find_session_messages(cls, session: Session, session_id: str, 
                            limit: int = 100, include_deleted: bool = False) -> List['ChatMessage']:
        """Find messages for a session"""
        query = session.query(cls).filter(cls.session_id == session_id)
        
        if not include_deleted:
            query = query.filter(cls.is_deleted == False)
        
        return query.order_by(cls.created_at.asc()).limit(limit).all()
    
    @classmethod
    def find_by_message_id(cls, session: Session, message_id: str) -> Optional['ChatMessage']:
        """Find message by message_id"""
        return session.query(cls).filter(
            cls.message_id == message_id,
            cls.is_deleted == False
        ).first()
    
    @classmethod
    def find_recent_messages(cls, session: Session, session_id: str, 
                           count: int = 10) -> List['ChatMessage']:
        """Find recent messages for context"""
        return session.query(cls).filter(
            cls.session_id == session_id,
            cls.is_deleted == False
        ).order_by(cls.created_at.desc()).limit(count).all()
    
    @classmethod
    def cleanup_old_messages(cls, session: Session, days: int = 90) -> int:
        """Clean up old messages (soft delete)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_messages = session.query(cls).filter(
            cls.created_at < cutoff_date,
            cls.is_deleted == False
        ).all()
        
        count = 0
        for message in old_messages:
            message.delete(session, soft=True)
            count += 1
        
        return count
    
    def to_websocket_format(self) -> Dict[str, Any]:
        """Convert message to WebSocket format"""
        return {
            'message_id': self.message_id,
            'sender_type': self.sender_type,
            'content': self.content,
            'content_type': self.content_type,
            'live2d_emotion': self.live2d_emotion,
            'live2d_motion': self.live2d_motion,
            'audio_url': self.audio_url,
            'metadata': self.metadata_dict,
            'timestamp': self.created_at.isoformat()
        }
    
    def __repr__(self) -> str:
        return f"<ChatMessage(message_id={self.message_id}, sender={self.sender_type}, session={self.session_id})>"


# Pydantic models for API
class ChatSessionCreate(BaseModel):
    """Chat session creation model"""
    
    session_id: str = Field(..., min_length=36, max_length=36)
    user_uuid: Optional[str] = Field(None, min_length=36, max_length=36)
    character_name: str = Field('미라', max_length=50)
    session_type: str = Field('anonymous', pattern=r'^(anonymous|registered)$')
    expires_hours: int = Field(24, ge=1, le=168)  # 1 hour to 1 week
    metadata: Optional[Dict[str, Any]] = None


class ChatSessionResponse(BaseModel):
    """Chat session response model"""
    
    id: int
    session_id: str
    user_uuid: Optional[str]
    character_name: str
    session_type: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime]
    expires_at: Optional[datetime]
    message_count: int
    duration: Optional[str]  # Human readable duration
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessageCreate(BaseModel):
    """Chat message creation model"""
    
    message_id: str = Field(..., min_length=36, max_length=36)
    session_id: str = Field(..., min_length=36, max_length=36)
    sender_type: str = Field(..., pattern=r'^(user|assistant)$')
    content: str = Field(..., min_length=1, max_length=10000)
    content_type: str = Field('text', pattern=r'^(text|fortune_result|system)$')
    live2d_emotion: Optional[str] = Field(None, max_length=20)
    live2d_motion: Optional[str] = Field(None, max_length=50)
    audio_url: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class ChatMessageResponse(BaseModel):
    """Chat message response model"""
    
    id: int
    message_id: str
    session_id: str
    sender_type: str
    content: str
    content_type: str
    live2d_emotion: Optional[str]
    live2d_motion: Optional[str]
    audio_url: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Chat history response model"""
    
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]
    total_messages: int
    
    class Config:
        from_attributes = True
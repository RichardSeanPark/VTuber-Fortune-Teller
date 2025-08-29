"""
Live2D model configuration and management
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json

from sqlalchemy import Column, String, Text, Boolean, CheckConstraint, DateTime, Integer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from .base import BaseModel as SQLBaseModel


class Live2DModel(SQLBaseModel):
    """Live2D model configuration"""
    
    __tablename__ = 'live2d_models'
    
    # Model Identification
    model_name = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique model identifier"
    )
    
    display_name = Column(
        String(50),
        nullable=False,
        comment="Display name for the model"
    )
    
    # Model Assets
    model_path = Column(
        String(255),
        nullable=False,
        comment="Path to model3.json file"
    )
    
    # Emotion and Motion Configuration (JSON strings for SQLite)
    emotions = Column(
        Text,
        nullable=False,
        comment="Emotion mappings as JSON string"
    )
    
    motions = Column(
        Text,
        nullable=False,
        comment="Motion mappings as JSON string"
    )
    
    # Default Settings
    default_emotion = Column(
        String(20),
        default='neutral',
        nullable=False,
        comment="Default emotion state"
    )
    
    # Model Information
    description = Column(
        Text,
        nullable=True,
        comment="Model description"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Model availability status"
    )
    
    # Properties
    @property
    def emotions_dict(self) -> Dict[str, Any]:
        """Get emotions as dictionary"""
        if not self.emotions:
            return {}
        try:
            return json.loads(self.emotions)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @emotions_dict.setter
    def emotions_dict(self, value: Dict[str, Any]):
        """Set emotions from dictionary"""
        if value is None:
            self.emotions = None
        else:
            self.emotions = json.dumps(value, ensure_ascii=False)
    
    @property
    def motions_dict(self) -> Dict[str, Any]:
        """Get motions as dictionary"""
        if not self.motions:
            return {}
        try:
            return json.loads(self.motions)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @motions_dict.setter
    def motions_dict(self, value: Dict[str, Any]):
        """Set motions from dictionary"""
        if value is None:
            self.motions = None
        else:
            self.motions = json.dumps(value, ensure_ascii=False)
    
    @property
    def available_emotions(self) -> List[str]:
        """Get list of available emotions"""
        return list(self.emotions_dict.keys())
    
    @property
    def available_motions(self) -> List[str]:
        """Get list of available motions"""
        return list(self.motions_dict.keys())
    
    def get_emotion_value(self, emotion_name: str) -> Optional[int]:
        """Get emotion value by name"""
        return self.emotions_dict.get(emotion_name)
    
    def get_motion_path(self, motion_name: str) -> Optional[str]:
        """Get motion file path by name"""
        return self.motions_dict.get(motion_name)
    
    def has_emotion(self, emotion_name: str) -> bool:
        """Check if emotion exists"""
        return emotion_name in self.emotions_dict
    
    def has_motion(self, motion_name: str) -> bool:
        """Check if motion exists"""
        return motion_name in self.motions_dict
    
    def get_random_emotion(self) -> Optional[str]:
        """Get random emotion name"""
        emotions = self.available_emotions
        if not emotions:
            return None
        import random
        return random.choice(emotions)
    
    def get_random_motion(self) -> Optional[str]:
        """Get random motion name"""
        motions = self.available_motions
        if not motions:
            return None
        import random
        return random.choice(motions)
    
    def get_emotion_for_context(self, context: str) -> str:
        """Get appropriate emotion for context"""
        # Define emotion mappings for different contexts
        context_emotion_map = {
            'fortune_telling': 'mystical',
            'greeting': 'joy',
            'thinking': 'thinking',
            'concern': 'concern',
            'surprise': 'surprise',
            'comfort': 'comfort',
            'playful': 'playful',
            'default': self.default_emotion
        }
        
        emotion = context_emotion_map.get(context, self.default_emotion)
        
        # Fallback to default if emotion doesn't exist
        if not self.has_emotion(emotion):
            emotion = self.default_emotion
        
        # Final fallback to first available emotion
        if not self.has_emotion(emotion) and self.available_emotions:
            emotion = self.available_emotions[0]
        
        return emotion
    
    def get_motion_for_context(self, context: str) -> Optional[str]:
        """Get appropriate motion for context"""
        # Define motion mappings for different contexts
        context_motion_map = {
            'greeting': 'greeting',
            'fortune_telling': 'crystal_gaze',
            'tarot_reading': 'card_draw',
            'blessing': 'blessing',
            'special': 'special_reading',
            'thinking': 'thinking_pose'
        }
        
        motion = context_motion_map.get(context)
        
        # Return motion if it exists, otherwise None
        return motion if motion and self.has_motion(motion) else None
    
    @classmethod
    def find_by_name(cls, session: Session, model_name: str) -> Optional['Live2DModel']:
        """Find model by name"""
        return session.query(cls).filter(
            cls.model_name == model_name,
            cls.is_active == True
        ).first()
    
    @classmethod
    def get_active_models(cls, session: Session) -> List['Live2DModel']:
        """Get all active models"""
        return session.query(cls).filter(cls.is_active == True).all()
    
    @classmethod
    def get_default_model(cls, session: Session) -> Optional['Live2DModel']:
        """Get default model (first active model)"""
        return session.query(cls).filter(cls.is_active == True).first()
    
    def to_client_config(self) -> Dict[str, Any]:
        """Convert to client configuration format"""
        return {
            'model_name': self.model_name,
            'display_name': self.display_name,
            'model_path': self.model_path,
            'emotions': self.emotions_dict,
            'motions': self.motions_dict,
            'default_emotion': self.default_emotion,
            'description': self.description
        }
    
    def validate_configuration(self) -> Dict[str, List[str]]:
        """Validate model configuration"""
        errors = {
            'emotions': [],
            'motions': [],
            'general': []
        }
        
        # Validate emotions
        emotions = self.emotions_dict
        if not emotions:
            errors['emotions'].append('No emotions defined')
        else:
            for emotion, value in emotions.items():
                if not isinstance(value, int) or value < 0:
                    errors['emotions'].append(f'Invalid emotion value for {emotion}: {value}')
        
        # Validate default emotion
        if self.default_emotion not in emotions:
            errors['general'].append(f'Default emotion "{self.default_emotion}" not found in emotions')
        
        # Validate motions
        motions = self.motions_dict
        if not motions:
            errors['motions'].append('No motions defined')
        else:
            for motion, path in motions.items():
                if not isinstance(path, str) or not path:
                    errors['motions'].append(f'Invalid motion path for {motion}: {path}')
        
        # Remove empty error lists
        return {k: v for k, v in errors.items() if v}
    
    def __repr__(self) -> str:
        return f"<Live2DModel(name={self.model_name}, active={self.is_active})>"


class Live2DSessionModel(SQLBaseModel):
    """Live2D session database model"""
    
    __tablename__ = 'live2d_sessions'
    
    # Session Identification
    session_id = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="Unique session identifier"
    )
    
    user_uuid = Column(
        String(36),
        nullable=True,
        comment="Associated user UUID"
    )
    
    # Model State
    model_name = Column(
        String(50),
        nullable=False,
        default="mira",
        comment="Current Live2D model being used"
    )
    
    current_emotion = Column(
        String(20),
        nullable=False,
        default="neutral",
        comment="Current emotion state"
    )
    
    current_motion = Column(
        String(50),
        nullable=True,
        comment="Current motion being played"
    )
    
    # Session Management
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Session active status"
    )
    
    last_emotion_change = Column(
        DateTime,
        nullable=True,
        comment="When emotion was last changed"
    )
    
    last_motion_change = Column(
        DateTime,
        nullable=True,
        comment="When motion was last changed"
    )
    
    # Session Metadata
    session_metadata = Column(
        Text,
        nullable=True,
        comment="Session metadata as JSON string"
    )
    
    @property
    def metadata_dict(self) -> Dict[str, Any]:
        """Get metadata as dictionary"""
        if self.session_metadata:
            try:
                return json.loads(self.session_metadata)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    @metadata_dict.setter
    def metadata_dict(self, value: Dict[str, Any]):
        """Set metadata from dictionary"""
        if value:
            self.session_metadata = json.dumps(value)
        else:
            self.session_metadata = None
    
    @classmethod
    def find_by_session_id(cls, session: Session, session_id: str) -> Optional['Live2DSessionModel']:
        """Find session by session ID"""
        return session.query(cls).filter(cls.session_id == session_id).first()
    
    @classmethod
    def find_active_session(cls, session: Session, user_uuid: str) -> Optional['Live2DSessionModel']:
        """Find active session for user"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid,
            cls.is_active == True
        ).first()
    
    @classmethod
    def find_inactive_sessions(cls, session: Session, cutoff_time: datetime) -> List['Live2DSessionModel']:
        """Find inactive sessions older than cutoff time"""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.updated_at < cutoff_time
        ).all()
    
    @classmethod
    def cleanup_inactive_sessions(cls, session: Session, cutoff_time: datetime) -> int:
        """Deactivate inactive sessions and return count"""
        sessions = cls.find_inactive_sessions(session, cutoff_time)
        count = len(sessions)
        
        for live2d_session in sessions:
            live2d_session.is_active = False
        
        return count
    
    def __repr__(self) -> str:
        return f"<Live2DSessionModel(session_id={self.session_id}, active={self.is_active})>"


# Pydantic models for API
class Live2DModelCreate(BaseModel):
    """Live2D model creation model"""
    
    model_name: str = Field(..., min_length=1, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    display_name: str = Field(..., min_length=1, max_length=50)
    model_path: str = Field(..., min_length=1, max_length=255)
    emotions: Dict[str, int] = Field(..., min_items=1)
    motions: Dict[str, str] = Field(..., min_items=1)
    default_emotion: str = Field('neutral', min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = Field(True)
    
    @validator('emotions')
    def validate_emotions(cls, v):
        for emotion, value in v.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError(f'Invalid emotion value for {emotion}: {value}')
        return v
    
    @validator('motions')
    def validate_motions(cls, v):
        for motion, path in v.items():
            if not isinstance(path, str) or not path:
                raise ValueError(f'Invalid motion path for {motion}: {path}')
        return v
    
    @validator('default_emotion')
    def validate_default_emotion(cls, v, values):
        if 'emotions' in values and v not in values['emotions']:
            raise ValueError(f'Default emotion "{v}" not found in emotions')
        return v


class Live2DModelUpdate(BaseModel):
    """Live2D model update model"""
    
    display_name: Optional[str] = Field(None, min_length=1, max_length=50)
    model_path: Optional[str] = Field(None, min_length=1, max_length=255)
    emotions: Optional[Dict[str, int]] = None
    motions: Optional[Dict[str, str]] = None
    default_emotion: Optional[str] = Field(None, min_length=1, max_length=20)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class Live2DModelResponse(BaseModel):
    """Live2D model response model"""
    
    id: int
    model_name: str
    display_name: str
    model_path: str
    emotions: Dict[str, int]
    motions: Dict[str, str]
    default_emotion: str
    description: Optional[str]
    is_active: bool
    available_emotions: List[str]
    available_motions: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class Live2DModelListResponse(BaseModel):
    """Live2D model list response model"""
    
    models: List[Live2DModelResponse]
    total: int
    active_count: int
    
    class Config:
        from_attributes = True


class Live2DAnimationRequest(BaseModel):
    """Live2D animation request model"""
    
    emotion: Optional[str] = Field(None, max_length=20)
    motion: Optional[str] = Field(None, max_length=50)
    context: Optional[str] = Field(None, max_length=50)
    duration: Optional[int] = Field(None, ge=100, le=10000)  # milliseconds


class Live2DAnimationResponse(BaseModel):
    """Live2D animation response model"""
    
    model_name: str
    emotion: Optional[str]
    emotion_value: Optional[int]
    motion: Optional[str]
    motion_path: Optional[str]
    duration: Optional[int]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class Live2DConfigResponse(BaseModel):
    """Live2D client configuration response"""
    
    model_name: str
    display_name: str
    model_path: str
    emotions: Dict[str, int]
    motions: Dict[str, str]
    default_emotion: str
    description: Optional[str]


class Live2DSession(BaseModel):
    """Live2D session model for tracking character state"""
    
    session_id: str
    user_uuid: Optional[str] = None
    model_name: str = "mira"
    current_emotion: str = "neutral"
    current_motion: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
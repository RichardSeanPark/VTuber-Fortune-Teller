"""
Fortune-related models for tarot, zodiac, and fortune sessions
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
from enum import Enum

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, CheckConstraint, Index, func
from sqlalchemy.orm import relationship, Session
from pydantic import BaseModel, Field, validator

from .base import UUIDBaseModel, BaseModel as SQLBaseModel


class FortuneType(str, Enum):
    """Fortune type enumeration"""
    DAILY = "daily"
    TAROT = "tarot"
    ZODIAC = "zodiac"
    ORIENTAL = "oriental"


class QuestionType(str, Enum):
    """Question type enumeration"""
    LOVE = "love"
    MONEY = "money"
    HEALTH = "health"
    WORK = "work"
    GENERAL = "general"


class FortuneCategory(str, Enum):
    """Fortune category enumeration"""
    LOVE = "love"
    MONEY = "money"
    HEALTH = "health"
    WORK = "work"
    GENERAL = "general"
    LUCK = "luck"
    STUDY = "study"
    FAMILY = "family"


class ZodiacSign(str, Enum):
    """Zodiac sign enumeration"""
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


class SajuElement(str, Enum):
    """Saju (Four Pillars) element enumeration"""
    WOOD = "wood"
    FIRE = "fire"
    EARTH = "earth"
    METAL = "metal"
    WATER = "water"


class LuckyElement(BaseModel):
    """Lucky element model for fortunes"""
    
    colors: Optional[List[str]] = None
    numbers: Optional[List[int]] = None
    items: Optional[List[str]] = None
    # Keep original fields for backward compatibility
    color: Optional[str] = None
    number: Optional[int] = None
    direction: Optional[str] = None
    item: Optional[str] = None
    time: Optional[str] = None


# Engine-specific models for fortune results
class FortuneCategory(BaseModel):
    """Fortune category result model"""
    score: int = Field(..., ge=0, le=100)
    grade: str
    description: str


class TarotCard(BaseModel):
    """Tarot card model for fortune engines"""
    position: str
    card_name: str
    card_meaning: str
    interpretation: str
    is_reversed: bool = False
    keywords: List[str] = []
    image_url: Optional[str] = None


class SajuElement(BaseModel):
    """Saju element model for oriental fortune"""
    pillar: str
    heavenly_stem: str
    earthly_branch: str
    element: str
    meaning: str


class FortuneResult(BaseModel):
    """Complete fortune result model"""
    fortune_id: Optional[str] = None  # UUID for external reference
    fortune_type: FortuneType
    date: str  # ISO format date
    overall_fortune: FortuneCategory
    categories: Optional[Dict[str, FortuneCategory]] = None
    tarot_cards: Optional[List[TarotCard]] = None
    saju_elements: Optional[List[SajuElement]] = None
    element_balance: Optional[Dict[str, int]] = None
    zodiac_info: Optional[Dict[str, Any]] = None
    lucky_elements: Optional[LuckyElement] = None
    advice: Optional[str] = None
    warnings: Optional[List[str]] = None
    question: Optional[str] = None
    question_type: Optional[str] = None
    live2d_emotion: Optional[str] = None
    live2d_motion: Optional[str] = None
    content: Optional[Dict[str, Any]] = None  # For backward compatibility
    created_at: Optional[datetime] = None  # Creation timestamp


class TarotSuit(str, Enum):
    """Tarot suit enumeration"""
    MAJOR = "major"
    WANDS = "wands"
    CUPS = "cups"
    SWORDS = "swords"
    PENTACLES = "pentacles"


class FortuneSession(UUIDBaseModel):
    """Fortune session model for storing fortune readings"""
    
    __tablename__ = 'fortune_sessions'
    
    # Fortune Identification
    fortune_id = Column(
        String(36),
        unique=True,
        nullable=False,
        comment="Fortune UUID for external reference"
    )
    
    # Session Association (optional)
    session_id = Column(
        String(36),
        ForeignKey('chat_sessions.session_id', ondelete='SET NULL'),
        nullable=True,
        comment="Associated chat session ID"
    )
    
    # User Association (optional)
    user_uuid = Column(
        String(36),
        ForeignKey('users.uuid', ondelete='SET NULL'),
        nullable=True,
        comment="Associated user UUID"
    )
    
    # Fortune Configuration
    fortune_type = Column(
        String(20),
        nullable=False,
        comment="Type of fortune reading"
    )
    
    question = Column(
        Text,
        nullable=True,
        comment="User's question (for tarot readings)"
    )
    
    question_type = Column(
        String(20),
        nullable=True,
        comment="Category of question"
    )
    
    # Fortune Result (JSON string for SQLite)
    result = Column(
        Text,
        nullable=False,
        comment="Fortune result as JSON string"
    )
    
    # Caching
    cached_until = Column(
        DateTime,
        nullable=True,
        comment="Cache expiration timestamp"
    )
    
    # Add check constraints and performance indexes
    __table_args__ = (
        CheckConstraint(
            fortune_type.in_(['daily', 'tarot', 'zodiac', 'oriental']),
            name='check_fortune_type'
        ),
        CheckConstraint(
            question_type.in_(['love', 'money', 'health', 'work', 'general']),
            name='check_question_type'
        ),
        # Performance indexes for common queries
        Index('idx_fortune_sessions_fortune_id', 'fortune_id'),
        Index('idx_fortune_sessions_user_uuid', 'user_uuid'),
        Index('idx_fortune_sessions_session_id', 'session_id'),
        Index('idx_fortune_sessions_type', 'fortune_type'),
        Index('idx_fortune_sessions_cache', 'cached_until'),
        Index('idx_fortune_sessions_user_type', 'user_uuid', 'fortune_type'),
        Index('idx_fortune_sessions_created', 'created_at'),
    )
    
    # Relationships
    chat_session = relationship(
        "ChatSession",
        back_populates="fortune_sessions",
        foreign_keys=[session_id]
    )
    
    user = relationship(
        "User",
        back_populates="fortune_sessions",
        foreign_keys=[user_uuid]
    )
    
    # Properties
    @property
    def result_dict(self) -> Dict[str, Any]:
        """Get result as dictionary"""
        if not self.result:
            return {}
        try:
            return json.loads(self.result)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @result_dict.setter
    def result_dict(self, value: Dict[str, Any]):
        """Set result from dictionary"""
        if value is None:
            self.result = None
        else:
            self.result = json.dumps(value, ensure_ascii=False)
    
    @property
    def is_cached(self) -> bool:
        """Check if fortune is cached and valid"""
        if not self.cached_until:
            return False
        return datetime.utcnow() < self.cached_until
    
    @property
    def cache_remaining(self) -> Optional[timedelta]:
        """Get remaining cache time"""
        if not self.cached_until:
            return None
        remaining = self.cached_until - datetime.utcnow()
        return remaining if remaining.total_seconds() > 0 else None
    
    def set_cache_ttl(self, hours: int = 24):
        """Set cache TTL"""
        self.cached_until = datetime.utcnow() + timedelta(hours=hours)
    
    def invalidate_cache(self):
        """Invalidate cache"""
        self.cached_until = datetime.utcnow() - timedelta(seconds=1)
    
    @classmethod
    def find_by_fortune_id(cls, session: Session, fortune_id: str) -> Optional['FortuneSession']:
        """Find fortune by fortune_id"""
        return session.query(cls).filter(cls.fortune_id == fortune_id).first()
    
    @classmethod
    def find_user_fortunes(cls, session: Session, user_uuid: str, 
                          limit: int = 10) -> List['FortuneSession']:
        """Find user's recent fortunes"""
        return session.query(cls).filter(
            cls.user_uuid == user_uuid
        ).order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def find_cached_fortune(cls, session: Session, user_uuid: str, 
                           fortune_type: str, question_type: str = None) -> Optional['FortuneSession']:
        """Find cached fortune for user"""
        query = session.query(cls).filter(
            cls.user_uuid == user_uuid,
            cls.fortune_type == fortune_type,
            cls.cached_until > datetime.utcnow()
        )
        
        if question_type:
            query = query.filter(cls.question_type == question_type)
        
        return query.order_by(cls.created_at.desc()).first()
    
    @classmethod
    def cleanup_expired_cache(cls, session: Session) -> int:
        """Clean up expired cached fortunes"""
        expired_fortunes = session.query(cls).filter(
            cls.cached_until < datetime.utcnow()
        ).all()
        
        count = len(expired_fortunes)
        for fortune in expired_fortunes:
            session.delete(fortune)
        
        return count
    
    def __repr__(self) -> str:
        return f"<FortuneSession(fortune_id={self.fortune_id}, type={self.fortune_type}, user={self.user_uuid})>"


class TarotCardDB(SQLBaseModel):
    """Tarot card master data"""
    
    __tablename__ = 'tarot_cards'
    
    # Card Identification
    card_name = Column(
        String(50),
        unique=True,
        nullable=False,
        comment="Card name in English"
    )
    
    card_name_ko = Column(
        String(50),
        nullable=False,
        comment="Card name in Korean"
    )
    
    card_number = Column(
        Integer,
        nullable=True,
        comment="Card number (for numbered cards)"
    )
    
    suit = Column(
        String(20),
        nullable=False,
        comment="Tarot suit"
    )
    
    # Card Meanings
    upright_meaning = Column(
        Text,
        nullable=True,
        comment="Upright card meaning"
    )
    
    reversed_meaning = Column(
        Text,
        nullable=True,
        comment="Reversed card meaning"
    )
    
    # Interpretations by Category
    general_interpretation = Column(
        Text,
        nullable=True,
        comment="General interpretation"
    )
    
    love_interpretation = Column(
        Text,
        nullable=True,
        comment="Love and relationship interpretation"
    )
    
    career_interpretation = Column(
        Text,
        nullable=True,
        comment="Career and work interpretation"
    )
    
    health_interpretation = Column(
        Text,
        nullable=True,
        comment="Health interpretation"
    )
    
    # Visual Assets
    image_url = Column(
        String(255),
        nullable=True,
        comment="Card image URL"
    )
    
    # Add check constraint
    __table_args__ = (
        CheckConstraint(
            suit.in_(['major', 'wands', 'cups', 'swords', 'pentacles']),
            name='check_tarot_suit'
        ),
    )
    
    def get_interpretation(self, question_type: str, is_reversed: bool = False) -> str:
        """Get interpretation based on question type and orientation"""
        # Get base meaning
        base_meaning = self.reversed_meaning if is_reversed else self.upright_meaning
        
        # Get specific interpretation
        interpretation_map = {
            'love': self.love_interpretation,
            'work': self.career_interpretation,
            'health': self.health_interpretation,
            'general': self.general_interpretation
        }
        
        specific = interpretation_map.get(question_type, self.general_interpretation)
        
        # Combine meanings
        parts = [part for part in [base_meaning, specific] if part]
        return " ".join(parts) if parts else "카드의 의미를 해석하고 있습니다."
    
    @classmethod
    def find_by_name(cls, session: Session, card_name: str) -> Optional['TarotCardDB']:
        """Find card by name"""
        return session.query(cls).filter(
            cls.card_name.ilike(f"%{card_name}%")
        ).first()
    
    @classmethod
    def find_by_suit(cls, session: Session, suit: str) -> List['TarotCardDB']:
        """Find cards by suit"""
        return session.query(cls).filter(cls.suit == suit).all()
    
    @classmethod
    def get_random_cards(cls, session: Session, count: int = 3) -> List['TarotCardDB']:
        """Get random cards for reading"""
        return session.query(cls).order_by(func.random()).limit(count).all()
    
    def __repr__(self) -> str:
        return f"<TarotCardDB(name={self.card_name}, suit={self.suit})>"


class ZodiacInfo(SQLBaseModel):
    """Zodiac sign information"""
    
    __tablename__ = 'zodiac_info'
    
    # Sign Identification
    sign = Column(
        String(20),
        unique=True,
        nullable=False,
        comment="Zodiac sign in English"
    )
    
    sign_ko = Column(
        String(20),
        nullable=False,
        comment="Zodiac sign in Korean"
    )
    
    # Basic Information
    date_range = Column(
        String(50),
        nullable=True,
        comment="Date range for the sign"
    )
    
    element = Column(
        String(20),
        nullable=True,
        comment="Element (fire, earth, air, water)"
    )
    
    ruling_planet = Column(
        String(20),
        nullable=True,
        comment="Ruling planet"
    )
    
    # Characteristics (JSON strings for SQLite)
    personality_traits = Column(
        Text,
        nullable=True,
        comment="Personality traits as JSON string"
    )
    
    strengths = Column(
        Text,
        nullable=True,
        comment="Strengths as JSON string"
    )
    
    weaknesses = Column(
        Text,
        nullable=True,
        comment="Weaknesses as JSON string"
    )
    
    compatible_signs = Column(
        Text,
        nullable=True,
        comment="Compatible signs as JSON string"
    )
    
    lucky_colors = Column(
        Text,
        nullable=True,
        comment="Lucky colors as JSON string"
    )
    
    lucky_numbers = Column(
        Text,
        nullable=True,
        comment="Lucky numbers as JSON string"
    )
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint(
            sign.in_([
                'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
            ]),
            name='check_zodiac_sign'
        ),
        CheckConstraint(
            element.in_(['fire', 'earth', 'air', 'water']),
            name='check_zodiac_element'
        ),
    )
    
    # Properties for JSON fields
    def _get_json_field(self, field_name: str) -> List[str]:
        """Helper to get JSON field as list"""
        value = getattr(self, field_name)
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def _set_json_field(self, field_name: str, value: List[str]):
        """Helper to set JSON field from list"""
        if value is None:
            setattr(self, field_name, None)
        else:
            setattr(self, field_name, json.dumps(value, ensure_ascii=False))
    
    @property
    def personality_traits_list(self) -> List[str]:
        return self._get_json_field('personality_traits')
    
    @personality_traits_list.setter
    def personality_traits_list(self, value: List[str]):
        self._set_json_field('personality_traits', value)
    
    @property
    def strengths_list(self) -> List[str]:
        return self._get_json_field('strengths')
    
    @strengths_list.setter
    def strengths_list(self, value: List[str]):
        self._set_json_field('strengths', value)
    
    @property
    def weaknesses_list(self) -> List[str]:
        return self._get_json_field('weaknesses')
    
    @weaknesses_list.setter
    def weaknesses_list(self, value: List[str]):
        self._set_json_field('weaknesses', value)
    
    @property
    def compatible_signs_list(self) -> List[str]:
        return self._get_json_field('compatible_signs')
    
    @compatible_signs_list.setter
    def compatible_signs_list(self, value: List[str]):
        self._set_json_field('compatible_signs', value)
    
    @property
    def lucky_colors_list(self) -> List[str]:
        return self._get_json_field('lucky_colors')
    
    @lucky_colors_list.setter
    def lucky_colors_list(self, value: List[str]):
        self._set_json_field('lucky_colors', value)
    
    @property
    def lucky_numbers_list(self) -> List[int]:
        """Get lucky numbers as list of integers"""
        value = self.lucky_numbers
        if not value:
            return []
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @lucky_numbers_list.setter
    def lucky_numbers_list(self, value: List[int]):
        """Set lucky numbers from list of integers"""
        if value is None:
            self.lucky_numbers = None
        else:
            self.lucky_numbers = json.dumps(value)
    
    @classmethod
    def find_by_sign(cls, session: Session, sign: str) -> Optional['ZodiacInfo']:
        """Find zodiac info by sign"""
        return session.query(cls).filter(cls.sign == sign.lower()).first()
    
    @classmethod
    def find_by_element(cls, session: Session, element: str) -> List['ZodiacInfo']:
        """Find zodiac signs by element"""
        return session.query(cls).filter(cls.element == element.lower()).all()
    
    @classmethod
    def get_compatible_signs(cls, session: Session, sign: str) -> List['ZodiacInfo']:
        """Get compatible zodiac signs"""
        zodiac = cls.find_by_sign(session, sign)
        if not zodiac:
            return []
        
        compatible_list = zodiac.compatible_signs_list
        if not compatible_list:
            return []
        
        return session.query(cls).filter(cls.sign.in_(compatible_list)).all()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with parsed JSON fields"""
        result = super().to_dict()
        
        # Replace JSON strings with parsed lists
        result['personality_traits'] = self.personality_traits_list
        result['strengths'] = self.strengths_list
        result['weaknesses'] = self.weaknesses_list
        result['compatible_signs'] = self.compatible_signs_list
        result['lucky_colors'] = self.lucky_colors_list
        result['lucky_numbers'] = self.lucky_numbers_list
        
        return result
    
    def __repr__(self) -> str:
        return f"<ZodiacInfo(sign={self.sign}, element={self.element})>"


# Pydantic models for API
class FortuneSessionCreate(BaseModel):
    """Fortune session creation model"""
    
    fortune_id: str = Field(..., min_length=36, max_length=36)
    session_id: Optional[str] = Field(None, min_length=36, max_length=36)
    user_uuid: Optional[str] = Field(None, min_length=36, max_length=36)
    fortune_type: FortuneType
    question: Optional[str] = Field(None, max_length=1000)
    question_type: Optional[QuestionType] = None
    result: Dict[str, Any]
    cache_hours: int = Field(24, ge=1, le=168)


class FortuneSessionResponse(BaseModel):
    """Fortune session response model"""
    
    id: int
    fortune_id: str
    session_id: Optional[str]
    user_uuid: Optional[str]
    fortune_type: str
    question: Optional[str]
    question_type: Optional[str]
    result: Dict[str, Any]
    cached_until: Optional[datetime]
    is_cached: bool
    cache_remaining: Optional[str]  # Human readable
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TarotCardResponse(BaseModel):
    """Tarot card response model"""
    
    id: int
    card_name: str
    card_name_ko: str
    card_number: Optional[int]
    suit: str
    upright_meaning: Optional[str]
    reversed_meaning: Optional[str]
    general_interpretation: Optional[str]
    love_interpretation: Optional[str]
    career_interpretation: Optional[str]
    health_interpretation: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ZodiacInfoResponse(BaseModel):
    """Zodiac info response model"""
    
    id: int
    sign: str
    sign_ko: str
    date_range: Optional[str]
    element: Optional[str]
    ruling_planet: Optional[str]
    personality_traits: List[str]
    strengths: List[str]
    weaknesses: List[str]
    compatible_signs: List[str]
    lucky_colors: List[str]
    lucky_numbers: List[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class TarotReadingRequest(BaseModel):
    """Tarot reading request model"""
    
    question: str = Field("오늘의 운세를 알려주세요", min_length=1, max_length=1000, description="타로 질문")
    question_type: QuestionType = QuestionType.GENERAL
    card_count: int = Field(3, ge=1, le=10)
    
    @validator('question', pre=True)
    def validate_question(cls, v):
        """빈 문자열인 경우 기본 질문으로 대체"""
        if not v or (isinstance(v, str) and v.strip() == ""):
            return "오늘의 운세를 알려주세요"
        return v.strip() if isinstance(v, str) else v
    

class TarotReadingResponse(BaseModel):
    """Tarot reading response model"""
    
    fortune_id: str
    question: str
    question_type: str
    cards: List[Dict[str, Any]]  # Card data with positions and interpretations
    interpretation: str
    advice: str
    created_at: datetime


class FortuneResultResponse(BaseModel):
    """Fortune result model for API responses"""
    
    fortune_id: str
    fortune_type: FortuneType
    content: Dict[str, Any]
    interpretation: Optional[str] = None
    advice: Optional[str] = None
    lucky_items: Optional[Dict[str, Any]] = None
    created_at: datetime
    cached_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True
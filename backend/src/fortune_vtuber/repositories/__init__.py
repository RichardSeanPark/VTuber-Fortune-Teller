"""
Repository layer for data access abstraction

Repository pattern implementation for clean data access with caching and transaction support.
"""

from .base import BaseRepository
from .user import UserRepository
from .chat import ChatSessionRepository, ChatMessageRepository
from .fortune import FortuneSessionRepository, TarotCardRepository, ZodiacInfoRepository
from .live2d import Live2DModelRepository
from .cache import ContentCacheRepository
from .system import SystemSettingRepository, UserAnalyticsRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "ChatSessionRepository",
    "ChatMessageRepository",
    "FortuneSessionRepository",
    "TarotCardRepository",
    "ZodiacInfoRepository",
    "Live2DModelRepository",
    "ContentCacheRepository",
    "SystemSettingRepository",
    "UserAnalyticsRepository"
]
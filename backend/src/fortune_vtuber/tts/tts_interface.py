"""
TTS Interface and Data Models

Base interface and data structures for TTS provider system.
Following the reference implementation patterns with Fortune-specific extensions.
"""

import abc
import os
import asyncio
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TTSProviderType(str, Enum):
    """TTS Provider Types"""
    EDGE_TTS = "edge_tts"
    SILICONFLOW_TTS = "siliconflow_tts" 
    AZURE_TTS = "azure_tts"
    OPENAI_TTS = "openai_tts"
    LOCAL_TTS = "local_tts"


class TTSCostType(str, Enum):
    """TTS Cost Types"""
    FREE = "free"
    FREE_TIER = "free_tier"
    PAID = "paid"


class TTSQuality(str, Enum):
    """TTS Quality Levels"""
    BASIC = "basic"
    HIGH = "high"
    PREMIUM = "premium"


class EmotionType(str, Enum):
    """Emotion Types for TTS adjustment"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    CALM = "calm"
    MYSTICAL = "mystical"
    WORRIED = "worried"
    PLAYFUL = "playful"


@dataclass
class TTSProviderConfig:
    """TTS Provider Configuration"""
    provider_id: str
    name: str
    cost_type: TTSCostType
    quality: TTSQuality
    supported_languages: List[str]
    supported_voices: Dict[str, List[str]]  # language -> voice names
    api_required: bool = False
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    default_voice: Optional[str] = None
    max_text_length: int = 5000
    rate_limit_per_minute: int = 60
    additional_config: Dict[str, Any] = field(default_factory=dict)
    
    def is_available(self) -> bool:
        """Check if provider is available"""
        if self.api_required and not self.api_key:
            return False
        return True
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports language"""
        return language in self.supported_languages
    
    def get_voices_for_language(self, language: str) -> List[str]:
        """Get available voices for language"""
        return self.supported_voices.get(language, [])


@dataclass
class TTSRequest:
    """TTS Request Data"""
    text: str
    language: str = "ko-KR"
    voice: Optional[str] = None
    emotion: Optional[EmotionType] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    enable_lipsync: bool = True
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    cache_key: Optional[str] = None
    provider_override: Optional[str] = None
    additional_params: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate request data"""
        if not self.text or not self.text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(self.text) > 10000:  # Reasonable limit
            raise ValueError("Text too long (max 10000 characters)")
        
        if not 0.5 <= self.speed <= 2.0:
            raise ValueError("Speed must be between 0.5 and 2.0")
        
        if not 0.5 <= self.pitch <= 2.0:
            raise ValueError("Pitch must be between 0.5 and 2.0")
        
        if not 0.1 <= self.volume <= 2.0:
            raise ValueError("Volume must be between 0.1 and 2.0")


@dataclass 
class LipSyncData:
    """Lip sync data for Live2D integration"""
    phonemes: List[tuple]  # (timestamp, phoneme, duration)
    mouth_shapes: List[tuple]  # (timestamp, mouth_parameters)
    duration: float  # Changed from total_duration for consistency
    frame_rate: Optional[float] = 30.0  # Added frame rate
    
    # Backward compatibility property
    @property
    def total_duration(self) -> float:
        return self.duration
    
    @classmethod
    def empty(cls, duration: float = 0.0) -> 'LipSyncData':
        """Create empty lipsync data"""
        return cls(
            phonemes=[],
            mouth_shapes=[],
            duration=duration,
            frame_rate=30.0
        )


@dataclass
class TTSResult:
    """TTS Generation Result"""
    audio_data: bytes
    audio_format: str
    duration: float
    provider: str
    voice_used: str
    language: str
    text_processed: str
    lip_sync_data: Optional[LipSyncData] = None
    cached: bool = False
    generation_time: float = 0.0
    cost_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def file_size(self) -> int:
        """Get audio file size in bytes"""
        return len(self.audio_data) if self.audio_data else 0
    
    def save_to_file(self, filepath: str) -> str:
        """Save audio data to file"""
        try:
            with open(filepath, 'wb') as f:
                f.write(self.audio_data)
            return filepath
        except Exception as e:
            logger.error(f"Failed to save audio file: {e}")
            raise


class TTSProviderError(Exception):
    """Base exception for TTS provider errors"""
    pass


class TTSProviderUnavailableError(TTSProviderError):
    """Raised when TTS provider is unavailable"""
    pass


class TTSProviderRateLimitError(TTSProviderError):
    """Raised when rate limit is exceeded"""
    pass


class TTSProviderAPIError(TTSProviderError):
    """Raised when API call fails"""
    pass


class TTSInterface(metaclass=abc.ABCMeta):
    """
    Base interface for TTS providers.
    Following reference implementation patterns with async-first design.
    """
    
    def __init__(self, config: TTSProviderConfig):
        self.config = config
        self.cache_dir = "cache"
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    @abc.abstractmethod
    async def async_generate_audio(self, request: TTSRequest) -> TTSResult:
        """
        Asynchronously generate audio from text.
        
        Args:
            request: TTSRequest with generation parameters
            
        Returns:
            TTSResult with audio data and metadata
            
        Raises:
            TTSProviderError: Various provider-specific errors
        """
        raise NotImplementedError
    
    def generate_audio(self, request: TTSRequest) -> TTSResult:
        """
        Synchronous wrapper for async_generate_audio.
        
        Args:
            request: TTSRequest with generation parameters
            
        Returns:
            TTSResult with audio data and metadata
        """
        return asyncio.run(self.async_generate_audio(request))
    
    async def check_availability(self) -> bool:
        """
        Check if provider is currently available.
        
        Returns:
            bool: True if provider is available
        """
        try:
            # Basic availability check
            if not self.config.is_available():
                return False
            
            # Additional provider-specific checks can be implemented
            return await self._provider_health_check()
        except Exception as e:
            logger.warning(f"Provider {self.config.provider_id} availability check failed: {e}")
            return False
    
    async def _provider_health_check(self) -> bool:
        """Provider-specific health check - to be overridden"""
        return True
    
    def get_supported_voices(self, language: str) -> List[str]:
        """Get supported voices for language"""
        return self.config.get_voices_for_language(language)
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports language"""
        return self.config.supports_language(language)
    
    def get_optimal_voice(self, request: TTSRequest) -> str:
        """Get optimal voice for request"""
        if request.voice:
            voices = self.get_supported_voices(request.language)
            if request.voice in voices:
                return request.voice
        
        # Return default voice or first available
        return self._get_default_voice(request.language)
    
    def _get_default_voice(self, language: str) -> str:
        """Get default voice for language - to be overridden"""
        voices = self.get_supported_voices(language)
        if voices:
            return voices[0]
        
        # Fallback to config default
        return self.config.default_voice or "default"
    
    def generate_cache_filename(self, request: TTSRequest, file_extension: str = "wav") -> str:
        """Generate cache filename for request"""
        cache_key = self._generate_cache_key(request)
        filename = f"tts_{cache_key}.{file_extension}"
        return os.path.join(self.cache_dir, filename)
    
    def _generate_cache_key(self, request: TTSRequest) -> str:
        """Generate cache key from request"""
        if request.cache_key:
            return request.cache_key
        
        # Generate key from request parameters
        key_parts = [
            request.text,
            request.language,
            request.voice or "default",
            f"speed_{request.speed}",
            f"pitch_{request.pitch}",
            f"volume_{request.volume}",
            request.emotion.value if request.emotion else "neutral",
            self.config.provider_id
        ]
        
        key_string = "|".join(str(part) for part in key_parts)
        return str(hash(key_string))
    
    def remove_file(self, filepath: str, verbose: bool = True) -> None:
        """
        Remove file from filesystem.
        
        Args:
            filepath: Path to file to remove
            verbose: Whether to log removal
        """
        if not os.path.exists(filepath):
            if verbose:
                logger.warning(f"File {filepath} does not exist")
            return
        
        try:
            if verbose:
                logger.debug(f"Removing file {filepath}")
            os.remove(filepath)
        except Exception as e:
            logger.error(f"Failed to remove file {filepath}: {e}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "provider_id": self.config.provider_id,
            "name": self.config.name,
            "cost_type": self.config.cost_type.value,
            "quality": self.config.quality.value,
            "supported_languages": self.config.supported_languages,
            "api_required": self.config.api_required,
            "available": self.config.is_available(),
            "rate_limit": self.config.rate_limit_per_minute
        }
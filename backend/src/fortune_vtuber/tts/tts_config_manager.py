"""
TTS Configuration Manager

User-configurable TTS settings with intelligent provider selection and fallback chains.
Supports user preferences, cost optimization, and quality settings.
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

from .tts_interface import TTSProviderType, TTSCostType, TTSQuality, EmotionType
from .tts_factory import TTSProviderFactory, tts_factory

logger = logging.getLogger(__name__)


class TTSMode(str, Enum):
    """TTS Operation Modes"""
    COST_OPTIMIZED = "cost_optimized"      # Prefer free providers
    QUALITY_OPTIMIZED = "quality_optimized" # Prefer premium providers  
    BALANCED = "balanced"                   # Balance cost and quality
    USER_PREFERENCE = "user_preference"     # Follow user settings


@dataclass
class UserTTSPreferences:
    """User TTS preferences"""
    user_id: str
    preferred_provider: Optional[str] = None
    preferred_voice: Optional[str] = None
    preferred_language: str = "ko-KR"
    speech_speed: float = 1.0
    speech_pitch: float = 1.0
    speech_volume: float = 1.0
    tts_mode: TTSMode = TTSMode.COST_OPTIMIZED
    enable_fallback: bool = True
    enable_caching: bool = True
    custom_fallback_chain: Optional[List[str]] = None
    emotion_preferences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "user_id": self.user_id,
            "preferred_provider": self.preferred_provider,
            "preferred_voice": self.preferred_voice,
            "preferred_language": self.preferred_language,
            "speech_speed": self.speech_speed,
            "speech_pitch": self.speech_pitch,
            "speech_volume": self.speech_volume,
            "tts_mode": self.tts_mode.value,
            "enable_fallback": self.enable_fallback,
            "enable_caching": self.enable_caching,
            "custom_fallback_chain": self.custom_fallback_chain,
            "emotion_preferences": self.emotion_preferences,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserTTSPreferences':
        """Create from dictionary"""
        return cls(
            user_id=data["user_id"],
            preferred_provider=data.get("preferred_provider"),
            preferred_voice=data.get("preferred_voice"),
            preferred_language=data.get("preferred_language", "ko-KR"),
            speech_speed=data.get("speech_speed", 1.0),
            speech_pitch=data.get("speech_pitch", 1.0),
            speech_volume=data.get("speech_volume", 1.0),
            tts_mode=TTSMode(data.get("tts_mode", "cost_optimized")),
            enable_fallback=data.get("enable_fallback", True),
            enable_caching=data.get("enable_caching", True),
            custom_fallback_chain=data.get("custom_fallback_chain"),
            emotion_preferences=data.get("emotion_preferences", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )


@dataclass 
class ProviderUsageStats:
    """Provider usage statistics"""
    provider_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_characters: int = 0
    total_duration: float = 0.0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0
    
    def update_stats(self, success: bool, characters: int, 
                    duration: float, response_time: float):
        """Update usage statistics"""
        self.total_requests += 1
        self.total_characters += characters
        self.total_duration += duration
        self.last_used = datetime.now()
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update average response time
        self.average_response_time = (
            (self.average_response_time * (self.total_requests - 1) + response_time) 
            / self.total_requests
        )
        
        # Update error rate
        self.error_rate = self.failed_requests / self.total_requests if self.total_requests > 0 else 0.0


class TTSConfigManager:
    """
    TTS Configuration Manager for user preferences and provider selection.
    Implements intelligent provider selection based on cost, quality, and user preferences.
    """
    
    def __init__(self, tts_factory: TTSProviderFactory = None):
        # Import here to avoid circular imports
        from .tts_factory import tts_factory as factory_instance
        self.tts_factory = tts_factory or factory_instance
        
        # User preferences storage (in production, use database)
        self._user_preferences: Dict[str, UserTTSPreferences] = {}
        
        # Provider usage statistics
        self._provider_stats: Dict[str, ProviderUsageStats] = {}
        
        # Global configuration
        self._global_config = {
            "max_text_length": 5000,
            "cache_enabled": True,
            "fallback_enabled": True,
            "cost_optimization_enabled": True,
            "quality_threshold": TTSQuality.HIGH,
            "rate_limit_buffer": 0.8  # Use 80% of rate limit
        }
        
        # Provider availability cache
        self._availability_cache: Dict[str, Tuple[bool, datetime]] = {}
        self._availability_cache_ttl = timedelta(minutes=5)
        
        # Initialize default fallback chains
        self._initialize_default_chains()
    
    def _initialize_default_chains(self):
        """Initialize default fallback chains per mode"""
        self._default_chains = {
            TTSMode.COST_OPTIMIZED: [
                TTSProviderType.EDGE_TTS.value,
                TTSProviderType.SILICONFLOW_TTS.value,
                TTSProviderType.AZURE_TTS.value,
                TTSProviderType.OPENAI_TTS.value
            ],
            TTSMode.QUALITY_OPTIMIZED: [
                TTSProviderType.AZURE_TTS.value,
                TTSProviderType.OPENAI_TTS.value,
                TTSProviderType.SILICONFLOW_TTS.value,
                TTSProviderType.EDGE_TTS.value
            ],
            TTSMode.BALANCED: [
                TTSProviderType.EDGE_TTS.value,
                TTSProviderType.AZURE_TTS.value,
                TTSProviderType.SILICONFLOW_TTS.value,
                TTSProviderType.OPENAI_TTS.value
            ]
        }
    
    async def get_optimal_provider(self, user_id: str, 
                                 language: str = "ko-KR") -> Dict[str, Any]:
        """
        Get optimal TTS provider for user based on preferences and availability.
        
        Args:
            user_id: User identifier
            language: Target language
            
        Returns:
            Dict with provider configuration
        """
        # Get user preferences
        user_prefs = self.get_user_preferences(user_id)
        
        # Check user's preferred provider first
        if (user_prefs.tts_mode == TTSMode.USER_PREFERENCE and 
            user_prefs.preferred_provider):
            
            provider_config = await self._check_user_preferred_provider(
                user_prefs.preferred_provider, language
            )
            if provider_config:
                return provider_config
        
        # Get fallback chain based on mode
        fallback_chain = self._get_fallback_chain_for_user(user_prefs, language)
        
        # Find best available provider
        for provider_id in fallback_chain:
            if await self._is_provider_available(provider_id, language):
                config = self.tts_factory.get_provider_config(provider_id)
                if config:
                    return {
                        "provider_id": provider_id,
                        "config": config,
                        "voice": self._get_optimal_voice(config, user_prefs, language),
                        "settings": self._get_provider_settings(config, user_prefs)
                    }
        
        # No providers available
        logger.warning(f"No TTS providers available for user {user_id}, language {language}")
        return None
    
    async def _check_user_preferred_provider(self, provider_id: str, 
                                           language: str) -> Optional[Dict[str, Any]]:
        """Check if user's preferred provider is available"""
        if not await self._is_provider_available(provider_id, language):
            return None
        
        config = self.tts_factory.get_provider_config(provider_id)
        if not config or not config.supports_language(language):
            return None
        
        user_prefs = UserTTSPreferences(user_id="temp")  # Temp for voice selection
        
        return {
            "provider_id": provider_id,
            "config": config,
            "voice": self._get_optimal_voice(config, user_prefs, language),
            "settings": self._get_provider_settings(config, user_prefs)
        }
    
    def _get_fallback_chain_for_user(self, user_prefs: UserTTSPreferences, 
                                   language: str) -> List[str]:
        """Get fallback chain based on user preferences"""
        if user_prefs.custom_fallback_chain:
            return user_prefs.custom_fallback_chain
        
        # Use mode-based chain
        if user_prefs.tts_mode in self._default_chains:
            return self._default_chains[user_prefs.tts_mode]
        
        # Fallback to cost optimized
        return self._default_chains[TTSMode.COST_OPTIMIZED]
    
    async def _is_provider_available(self, provider_id: str, language: str) -> bool:
        """Check if provider is available with caching"""
        cache_key = f"{provider_id}_{language}"
        now = datetime.now()
        
        # Check cache
        if cache_key in self._availability_cache:
            is_available, cached_at = self._availability_cache[cache_key]
            if now - cached_at < self._availability_cache_ttl:
                return is_available
        
        # Perform availability check
        try:
            config = self.tts_factory.get_provider_config(provider_id)
            if not config or not config.supports_language(language):
                is_available = False
            else:
                provider = await self.tts_factory.create_provider(provider_id)
                is_available = await provider.check_availability()
            
            # Cache result
            self._availability_cache[cache_key] = (is_available, now)
            return is_available
            
        except Exception as e:
            logger.debug(f"Provider {provider_id} availability check failed: {e}")
            self._availability_cache[cache_key] = (False, now)
            return False
    
    def _get_optimal_voice(self, config, user_prefs: UserTTSPreferences, 
                          language: str) -> str:
        """Get optimal voice for user and language"""
        # Check user preference
        if user_prefs.preferred_voice:
            available_voices = config.get_voices_for_language(language)
            if user_prefs.preferred_voice in available_voices:
                return user_prefs.preferred_voice
        
        # Get language-specific default
        available_voices = config.get_voices_for_language(language)
        if available_voices:
            # Prefer neural/high-quality voices
            for voice in available_voices:
                if "neural" in voice.lower():
                    return voice
            return available_voices[0]
        
        return config.default_voice or "default"
    
    def _get_provider_settings(self, config, user_prefs: UserTTSPreferences) -> Dict[str, Any]:
        """Get provider-specific settings"""
        return {
            "speed": user_prefs.speech_speed,
            "pitch": user_prefs.speech_pitch,
            "volume": user_prefs.speech_volume,
            "api_key": config.api_key,
            "api_url": config.api_url,
            "additional_config": config.additional_config
        }
    
    def get_user_preferences(self, user_id: str) -> UserTTSPreferences:
        """Get user TTS preferences"""
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = UserTTSPreferences(user_id=user_id)
        
        return self._user_preferences[user_id]
    
    def update_user_preferences(self, user_id: str, **kwargs) -> UserTTSPreferences:
        """Update user TTS preferences"""
        prefs = self.get_user_preferences(user_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        prefs.updated_at = datetime.now()
        self._user_preferences[user_id] = prefs
        
        logger.info(f"Updated TTS preferences for user {user_id}")
        return prefs
    
    def get_user_tts_options(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available TTS options for user"""
        options = []
        
        for provider_id, config in self.tts_factory._provider_configs.items():
            if config.is_available():
                options.append({
                    "id": provider_id,
                    "name": config.name,
                    "cost_type": config.cost_type.value,
                    "quality": config.quality.value,
                    "languages": config.supported_languages,
                    "voices": config.supported_voices,
                    "api_required": config.api_required,
                    "rate_limit": config.rate_limit_per_minute,
                    "max_text_length": config.max_text_length
                })
        
        return options
    
    def record_provider_usage(self, provider_id: str, success: bool, 
                            characters: int, duration: float, 
                            response_time: float):
        """Record provider usage statistics"""
        if provider_id not in self._provider_stats:
            self._provider_stats[provider_id] = ProviderUsageStats(provider_id)
        
        stats = self._provider_stats[provider_id]
        stats.update_stats(success, characters, duration, response_time)
    
    def get_provider_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get provider usage statistics"""
        stats = {}
        
        for provider_id, provider_stats in self._provider_stats.items():
            stats[provider_id] = {
                "total_requests": provider_stats.total_requests,
                "success_rate": (provider_stats.successful_requests / 
                               provider_stats.total_requests if provider_stats.total_requests > 0 else 0),
                "error_rate": provider_stats.error_rate,
                "average_response_time": provider_stats.average_response_time,
                "total_characters": provider_stats.total_characters,
                "total_duration": provider_stats.total_duration,
                "last_used": provider_stats.last_used.isoformat() if provider_stats.last_used else None
            }
        
        return stats
    
    def get_recommended_provider(self, language: str = "ko-KR", 
                               priority: str = "cost") -> Optional[str]:
        """Get recommended provider based on priority"""
        available_providers = []
        
        for provider_id, config in self.tts_factory._provider_configs.items():
            if config.supports_language(language) and config.is_available():
                available_providers.append((provider_id, config))
        
        if not available_providers:
            return None
        
        # Sort by priority
        if priority == "cost":
            # Sort by cost type (free first)
            available_providers.sort(
                key=lambda x: (x[1].cost_type != TTSCostType.FREE,
                             x[1].cost_type != TTSCostType.FREE_TIER,
                             x[1].cost_type != TTSCostType.PAID)
            )
        elif priority == "quality":
            # Sort by quality (premium first)
            available_providers.sort(
                key=lambda x: (x[1].quality != TTSQuality.PREMIUM,
                             x[1].quality != TTSQuality.HIGH,
                             x[1].quality != TTSQuality.BASIC)
            )
        
        return available_providers[0][0] if available_providers else None
    
    def configure_provider_api(self, provider_id: str, api_key: str, 
                             api_url: Optional[str] = None):
        """Configure provider API credentials"""
        config = self.tts_factory.get_provider_config(provider_id)
        if config:
            config.api_key = api_key
            if api_url:
                config.api_url = api_url
            logger.info(f"Configured API credentials for {provider_id}")
    
    def clear_availability_cache(self):
        """Clear provider availability cache"""
        self._availability_cache.clear()
        logger.info("Cleared provider availability cache")
    
    def export_user_preferences(self, user_id: str) -> Optional[str]:
        """Export user preferences as JSON"""
        prefs = self._user_preferences.get(user_id)
        if prefs:
            return json.dumps(prefs.to_dict(), indent=2)
        return None
    
    def import_user_preferences(self, preferences_json: str) -> bool:
        """Import user preferences from JSON"""
        try:
            data = json.loads(preferences_json)
            prefs = UserTTSPreferences.from_dict(data)
            self._user_preferences[prefs.user_id] = prefs
            return True
        except Exception as e:
            logger.error(f"Failed to import user preferences: {e}")
            return False


# Global configuration manager instance
tts_config_manager = TTSConfigManager()
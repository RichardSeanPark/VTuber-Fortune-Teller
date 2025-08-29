"""
TTS Provider Factory System

Factory for creating and managing TTS providers with auto-detection and configuration.
Based on Reference implementation patterns with enhanced provider management.
"""

import asyncio
import importlib
from typing import Dict, List, Optional, Type, Any, Tuple
import logging
from enum import Enum

from .tts_interface import (
    TTSInterface, TTSProviderConfig, TTSProviderType, 
    TTSCostType, TTSQuality, TTSProviderError
)

logger = logging.getLogger(__name__)


class ProviderPriority(int, Enum):
    """Provider priority levels"""
    HIGH = 1      # Free, high quality
    MEDIUM = 2    # Free tier, good quality  
    LOW = 3       # Paid, premium quality
    FALLBACK = 4  # Basic fallback options


class TTSProviderFactory:
    """
    Factory for creating TTS providers with intelligent provider selection.
    Implements fallback chains and auto-detection following the specifications.
    """
    
    # Provider definitions following the todo specifications
    SUPPORTED_PROVIDERS = {
        TTSProviderType.EDGE_TTS: {
            "name": "Microsoft Edge TTS",
            "cost_type": TTSCostType.FREE,
            "quality": TTSQuality.HIGH,
            "priority": ProviderPriority.HIGH,
            "languages": ["ko-KR", "en-US", "ja-JP", "zh-CN"],
            "voices": {
                "ko-KR": ["ko-KR-SunHiNeural", "ko-KR-JiMinNeural", "ko-KR-InJoonNeural"],
                "en-US": ["en-US-AvaMultilingualNeural", "en-US-AriaNeural"],
                "ja-JP": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
                "zh-CN": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"]
            },
            "default_voice": "ko-KR-SunHiNeural",
            "api_required": False,
            "module_path": "fortune_vtuber.tts.providers.edge_tts",
            "class_name": "EdgeTTSProvider",
            "max_text_length": 5000,
            "rate_limit_per_minute": 60
        },
        
        TTSProviderType.SILICONFLOW_TTS: {
            "name": "SiliconFlow TTS",
            "cost_type": TTSCostType.FREE_TIER,
            "quality": TTSQuality.HIGH,
            "priority": ProviderPriority.MEDIUM,
            "languages": ["ko-KR", "en-US", "zh-CN"],
            "voices": {
                "ko-KR": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "en-US": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "zh-CN": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "default_voice": "alloy",
            "api_required": True,
            "module_path": "fortune_vtuber.tts.providers.siliconflow_tts",
            "class_name": "SiliconFlowTTSProvider",
            "max_text_length": 4000,
            "rate_limit_per_minute": 30
        },
        
        TTSProviderType.AZURE_TTS: {
            "name": "Azure Cognitive Services TTS",
            "cost_type": TTSCostType.PAID,
            "quality": TTSQuality.PREMIUM,
            "priority": ProviderPriority.LOW,
            "languages": ["ko-KR", "en-US", "ja-JP", "zh-CN"],
            "voices": {
                "ko-KR": ["ko-KR-SunHiNeural", "ko-KR-JiMinNeural", "ko-KR-BongJinNeural"],
                "en-US": ["en-US-AriaNeural", "en-US-JennyNeural", "en-US-GuyNeural"],
                "ja-JP": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
                "zh-CN": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-CN-YunyangNeural"]
            },
            "default_voice": "ko-KR-SunHiNeural",
            "api_required": True,
            "module_path": "fortune_vtuber.tts.providers.azure_tts",
            "class_name": "AzureTTSProvider",
            "max_text_length": 10000,
            "rate_limit_per_minute": 200
        },
        
        TTSProviderType.OPENAI_TTS: {
            "name": "OpenAI TTS",
            "cost_type": TTSCostType.PAID,
            "quality": TTSQuality.PREMIUM,
            "priority": ProviderPriority.LOW,
            "languages": ["ko-KR", "en-US", "ja-JP", "zh-CN", "es-ES", "fr-FR", "de-DE"],
            "voices": {
                "ko-KR": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "en-US": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "ja-JP": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
                "zh-CN": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
            },
            "default_voice": "alloy",
            "api_required": True,
            "module_path": "fortune_vtuber.tts.providers.openai_tts",
            "class_name": "OpenAITTSProvider",
            "max_text_length": 4000,
            "rate_limit_per_minute": 50
        }
    }
    
    def __init__(self):
        self._provider_instances: Dict[str, TTSInterface] = {}
        self._provider_configs: Dict[str, TTSProviderConfig] = {}
        self._availability_cache: Dict[str, bool] = {}
        self._fallback_chains: Dict[str, List[str]] = {}
        
        # Initialize provider configurations
        self._initialize_provider_configs()
        self._initialize_fallback_chains()
    
    def _initialize_provider_configs(self):
        """Initialize provider configurations"""
        for provider_type, config_dict in self.SUPPORTED_PROVIDERS.items():
            config = TTSProviderConfig(
                provider_id=provider_type.value,
                name=config_dict["name"],
                cost_type=config_dict["cost_type"],
                quality=config_dict["quality"],
                supported_languages=config_dict["languages"],
                supported_voices=config_dict["voices"],
                api_required=config_dict["api_required"],
                default_voice=config_dict["default_voice"],
                max_text_length=config_dict["max_text_length"],
                rate_limit_per_minute=config_dict["rate_limit_per_minute"],
                additional_config={
                    "module_path": config_dict["module_path"],
                    "class_name": config_dict["class_name"],
                    "priority": config_dict["priority"]
                }
            )
            self._provider_configs[provider_type.value] = config
    
    def _initialize_fallback_chains(self):
        """Initialize fallback chains per language"""
        # Default fallback chain: free → free_tier → paid
        base_chain = [
            TTSProviderType.EDGE_TTS.value,
            TTSProviderType.SILICONFLOW_TTS.value,
            TTSProviderType.AZURE_TTS.value,
            TTSProviderType.OPENAI_TTS.value
        ]
        
        # Language-specific fallback chains
        self._fallback_chains = {
            "ko-KR": base_chain,
            "en-US": base_chain,
            "ja-JP": base_chain,
            "zh-CN": base_chain,
            "default": base_chain
        }
    
    async def create_provider(self, provider_id: str, **kwargs) -> TTSInterface:
        """
        Create TTS provider instance.
        
        Args:
            provider_id: Provider identifier
            **kwargs: Additional configuration parameters
            
        Returns:
            TTSInterface: Provider instance
            
        Raises:
            TTSProviderError: If provider cannot be created
        """
        if provider_id in self._provider_instances:
            return self._provider_instances[provider_id]
        
        if provider_id not in self._provider_configs:
            raise TTSProviderError(f"Unknown provider: {provider_id}")
        
        config = self._provider_configs[provider_id]
        
        try:
            # Update config with provided kwargs
            updated_config = self._update_config_with_kwargs(config, kwargs)
            
            # Import and instantiate provider
            provider_class = self._import_provider_class(updated_config)
            provider_instance = provider_class(updated_config)
            
            # Cache instance
            self._provider_instances[provider_id] = provider_instance
            
            logger.info(f"Created TTS provider: {provider_id}")
            return provider_instance
            
        except Exception as e:
            logger.error(f"Failed to create provider {provider_id}: {e}")
            raise TTSProviderError(f"Failed to create provider {provider_id}: {e}")
    
    def _update_config_with_kwargs(self, config: TTSProviderConfig, kwargs: Dict[str, Any]) -> TTSProviderConfig:
        """Update provider config with kwargs"""
        # Create a copy of the config
        updated_config = TTSProviderConfig(
            provider_id=config.provider_id,
            name=config.name,
            cost_type=config.cost_type,
            quality=config.quality,
            supported_languages=config.supported_languages,
            supported_voices=config.supported_voices,
            api_required=config.api_required,
            api_key=kwargs.get("api_key", config.api_key),
            api_url=kwargs.get("api_url", config.api_url),
            default_voice=kwargs.get("default_voice", config.default_voice),
            max_text_length=kwargs.get("max_text_length", config.max_text_length),
            rate_limit_per_minute=kwargs.get("rate_limit_per_minute", config.rate_limit_per_minute),
            additional_config={**config.additional_config, **kwargs.get("additional_config", {})}
        )
        
        return updated_config
    
    def _import_provider_class(self, config: TTSProviderConfig) -> Type[TTSInterface]:
        """Import provider class dynamically"""
        module_path = config.additional_config["module_path"]
        class_name = config.additional_config["class_name"]
        
        try:
            module = importlib.import_module(module_path)
            provider_class = getattr(module, class_name)
            
            # Debug: Log class identity information
            logger.info(f"Factory TTSInterface id: {id(TTSInterface)}")
            logger.info(f"Provider {class_name} MRO: {provider_class.__mro__}")
            if len(provider_class.__mro__) > 1:
                base_class = provider_class.__mro__[1]  # First base class
                logger.info(f"Provider base class id: {id(base_class)}")
                logger.info(f"Classes are same object: {base_class is TTSInterface}")
            
            # Use name-based check instead of issubclass
            has_tts_interface = any(base.__name__ == 'TTSInterface' for base in provider_class.__mro__)
            if not has_tts_interface:
                raise TTSProviderError(f"Provider class {class_name} must inherit from TTSInterface")
            
            return provider_class
            
        except ImportError as e:
            logger.warning(f"Provider module {module_path} not available: {e}")
            raise TTSProviderError(f"Provider module {module_path} not available")
        except AttributeError as e:
            logger.error(f"Provider class {class_name} not found in {module_path}: {e}")
            raise TTSProviderError(f"Provider class {class_name} not found")
    
    async def get_available_providers(self, language: str = None) -> List[str]:
        """
        Get list of available providers, optionally filtered by language.
        
        Args:
            language: Optional language filter
            
        Returns:
            List[str]: Available provider IDs
        """
        available_providers = []
        
        for provider_id, config in self._provider_configs.items():
            # Check language support
            if language and not config.supports_language(language):
                continue
            
            # Check basic availability
            if not config.is_available():
                continue
            
            # Check cached availability or perform check
            is_available = await self._check_provider_availability(provider_id)
            if is_available:
                available_providers.append(provider_id)
        
        # Sort by priority (free providers first)
        available_providers.sort(key=lambda pid: self._get_provider_priority(pid))
        return available_providers
    
    async def _check_provider_availability(self, provider_id: str) -> bool:
        """Check provider availability with caching"""
        if provider_id in self._availability_cache:
            return self._availability_cache[provider_id]
        
        try:
            # Try to create provider instance for availability check
            provider = await self.create_provider(provider_id)
            is_available = await provider.check_availability()
            self._availability_cache[provider_id] = is_available
            return is_available
        except Exception as e:
            logger.debug(f"Provider {provider_id} not available: {e}")
            self._availability_cache[provider_id] = False
            return False
    
    def _get_provider_priority(self, provider_id: str) -> int:
        """Get provider priority for sorting"""
        config = self._provider_configs.get(provider_id)
        if not config:
            return 999
        
        return config.additional_config.get("priority", ProviderPriority.FALLBACK).value
    
    async def get_optimal_provider(self, language: str = "ko-KR", 
                                 user_preference: Optional[str] = None) -> Optional[str]:
        """
        Get optimal provider for given language and user preference.
        
        Args:
            language: Target language
            user_preference: User's preferred provider
            
        Returns:
            Optional[str]: Optimal provider ID or None if none available
        """
        # Check user preference first
        if user_preference:
            if user_preference in self._provider_configs:
                config = self._provider_configs[user_preference]
                if config.supports_language(language) and config.is_available():
                    is_available = await self._check_provider_availability(user_preference)
                    if is_available:
                        return user_preference
        
        # Get fallback chain for language
        fallback_chain = self._fallback_chains.get(language, self._fallback_chains["default"])
        
        # Find first available provider in chain
        for provider_id in fallback_chain:
            config = self._provider_configs.get(provider_id)
            if not config:
                continue
            
            if not config.supports_language(language):
                continue
            
            if not config.is_available():
                continue
            
            is_available = await self._check_provider_availability(provider_id)
            if is_available:
                return provider_id
        
        return None
    
    def get_fallback_chain(self, language: str = "ko-KR") -> List[str]:
        """Get fallback chain for language"""
        return self._fallback_chains.get(language, self._fallback_chains["default"]).copy()
    
    def update_fallback_chain(self, language: str, chain: List[str]):
        """Update fallback chain for language"""
        self._fallback_chains[language] = chain
        logger.info(f"Updated fallback chain for {language}: {chain}")
    
    def get_provider_config(self, provider_id: str) -> Optional[TTSProviderConfig]:
        """Get provider configuration"""
        return self._provider_configs.get(provider_id)
    
    def get_supported_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all supported providers"""
        providers_info = {}
        
        for provider_id, config in self._provider_configs.items():
            providers_info[provider_id] = {
                "name": config.name,
                "cost_type": config.cost_type.value,
                "quality": config.quality.value,
                "languages": config.supported_languages,
                "voices": config.supported_voices,
                "api_required": config.api_required,
                "available": config.is_available(),
                "priority": config.additional_config.get("priority", ProviderPriority.FALLBACK).value
            }
        
        return providers_info
    
    def clear_cache(self):
        """Clear provider instances and availability cache"""
        self._provider_instances.clear()
        self._availability_cache.clear()
        logger.info("Provider cache cleared")
    
    async def health_check_all_providers(self) -> Dict[str, bool]:
        """Perform health check on all providers"""
        results = {}
        
        for provider_id in self._provider_configs:
            try:
                is_available = await self._check_provider_availability(provider_id)
                results[provider_id] = is_available
            except Exception as e:
                logger.error(f"Health check failed for {provider_id}: {e}")
                results[provider_id] = False
        
        return results
    
    async def get_fallback_provider(self, preferred_provider: str = None, 
                                  language: str = "ko-KR") -> Optional[TTSInterface]:
        """
        Get a fallback provider when the preferred provider fails.
        
        Args:
            preferred_provider: The provider that failed
            language: Target language
            
        Returns:
            Optional[TTSInterface]: Working provider instance or None
        """
        # Get fallback chain, excluding the failed provider
        fallback_chain = self.get_fallback_chain(language)
        
        if preferred_provider and preferred_provider in fallback_chain:
            fallback_chain.remove(preferred_provider)
            # Mark the failed provider as unavailable temporarily
            self._availability_cache[preferred_provider] = False
        
        # Try each provider in the fallback chain
        for provider_id in fallback_chain:
            try:
                provider = await self.create_provider(provider_id)
                is_available = await self._check_provider_availability(provider_id)
                
                if is_available:
                    logger.info(f"Fallback to TTS provider: {provider_id}")
                    return provider
                    
            except Exception as e:
                logger.debug(f"Fallback provider {provider_id} failed: {e}")
                continue
        
        logger.error("No TTS providers available for fallback")
        return None
    
    def reset_provider_availability(self, provider_id: str):
        """Reset provider availability status (for retry logic)"""
        if provider_id in self._availability_cache:
            del self._availability_cache[provider_id]
        logger.info(f"Reset availability cache for provider: {provider_id}")


# Singleton factory instance
tts_factory = TTSProviderFactory()
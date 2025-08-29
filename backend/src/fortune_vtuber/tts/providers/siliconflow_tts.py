"""
SiliconFlow TTS Provider Implementation

SiliconFlow TTS provider implementation.
Free tier API-based TTS service with good quality Korean support.
Based on reference implementation with Fortune-specific enhancements.
"""

import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any
import logging

from ..tts_interface import TTSInterface, TTSRequest, TTSResult, TTSProviderConfig
from ..tts_interface import (
    TTSProviderError, TTSProviderUnavailableError, 
    TTSProviderAPIError, TTSProviderRateLimitError
)

logger = logging.getLogger(__name__)


class SiliconFlowTTSProvider(TTSInterface):
    """
    SiliconFlow TTS Provider
    
    Free tier API-based TTS service with decent Korean support.
    Requires API key but offers good quality as backup to Edge TTS.
    """
    
    def __init__(self, config: TTSProviderConfig):
        super().__init__(config)
        
        if not config.api_key:
            logger.warning("SiliconFlow TTS API key not provided")
        
        # SiliconFlow specific settings
        self.api_url = config.api_url or "https://api.siliconflow.cn/v1/audio/speech"
        self.api_key = config.api_key
        self.file_extension = "mp3"
        
        # Default model settings
        self.default_model = config.additional_config.get("default_model", "tts-1")
        self.default_voice = config.default_voice or "alloy"
        self.sample_rate = config.additional_config.get("sample_rate", 24000)
        self.response_format = config.additional_config.get("response_format", "mp3")
        self.default_speed = config.additional_config.get("speed", 1.0)
        self.default_gain = config.additional_config.get("gain", 0.0)
        
        # Voice mappings for different emotions/styles
        self.voice_mappings = {
            "ko-KR": {
                "neutral": "alloy",
                "gentle": "nova", 
                "energetic": "fable",
                "calm": "shimmer",
                "professional": "echo",
                "warm": "onyx",
                "default": "alloy"
            },
            "en-US": {
                "neutral": "alloy",
                "gentle": "nova",
                "energetic": "fable", 
                "calm": "shimmer",
                "professional": "echo",
                "warm": "onyx",
                "default": "alloy"
            },
            "zh-CN": {
                "neutral": "alloy",
                "gentle": "nova",
                "energetic": "fable",
                "calm": "shimmer", 
                "professional": "echo",
                "warm": "onyx",
                "default": "alloy"
            }
        }
        
        # Rate limiting
        self.last_request_time = 0.0
        self.min_request_interval = 60.0 / config.rate_limit_per_minute  # Convert to seconds
    
    async def async_generate_audio(self, request: TTSRequest) -> TTSResult:
        """Generate audio using SiliconFlow TTS API"""
        start_time = time.time()
        
        try:
            # Check API availability
            if not self.api_key:
                raise TTSProviderUnavailableError("SiliconFlow API key not configured")
            
            # Validate request
            await self._validate_request(request)
            
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Get optimal voice
            voice = self._get_optimal_voice_for_request(request)
            
            # Prepare API payload
            payload = self._build_api_payload(request, voice)
            
            # Make API request
            audio_data = await self._make_api_request(payload)
            
            # Calculate duration estimate
            duration = self._estimate_duration(request.text, request.speed)
            
            # Generate lip sync data if requested
            lip_sync_data = None
            if request.enable_lipsync:
                lip_sync_data = await self._generate_lipsync_data(request, duration)
            
            # Create result
            result = TTSResult(
                audio_data=audio_data,
                audio_format=self.response_format,
                duration=duration,
                provider=self.config.provider_id,
                voice_used=voice,
                language=request.language,
                text_processed=request.text,
                lip_sync_data=lip_sync_data,
                generation_time=time.time() - start_time,
                cost_info={
                    "provider": "siliconflow",
                    "model": self.default_model,
                    "characters": len(request.text),
                    "estimated_cost": self._calculate_estimated_cost(request.text)
                },
                metadata={
                    "model": self.default_model,
                    "voice": voice,
                    "speed": request.speed,
                    "sample_rate": self.sample_rate,
                    "response_format": self.response_format,
                    "file_size": len(audio_data)
                }
            )
            
            logger.info(f"SiliconFlow TTS generated audio: {len(audio_data)} bytes, {duration:.2f}s")
            return result
            
        except TTSProviderError:
            raise
        except Exception as e:
            logger.error(f"SiliconFlow TTS generation failed: {e}")
            raise TTSProviderAPIError(f"SiliconFlow API error: {e}")
    
    async def _validate_request(self, request: TTSRequest):
        """Validate TTS request for SiliconFlow"""
        if len(request.text) > self.config.max_text_length:
            raise TTSProviderError(f"Text too long: {len(request.text)} > {self.config.max_text_length}")
        
        if request.language not in self.config.supported_languages:
            raise TTSProviderError(f"Language {request.language} not supported by SiliconFlow")
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _get_optimal_voice_for_request(self, request: TTSRequest) -> str:
        """Get optimal voice for request"""
        language = request.language
        
        # Check if specific voice requested
        if request.voice:
            available_voices = self.get_supported_voices(language)
            if request.voice in available_voices:
                return request.voice
        
        # Map emotion to voice if available
        if request.emotion and language in self.voice_mappings:
            emotion_voice = self.voice_mappings[language].get(request.emotion.value)
            if emotion_voice:
                return emotion_voice
        
        # Get default voice for language
        if language in self.voice_mappings:
            return self.voice_mappings[language]["default"]
        
        return self.default_voice
    
    def _build_api_payload(self, request: TTSRequest, voice: str) -> Dict[str, Any]:
        """Build API request payload"""
        return {
            "model": self.default_model,
            "input": request.text,
            "voice": voice,
            "response_format": self.response_format,
            "speed": request.speed,
            # "sample_rate": self.sample_rate,  # May not be supported
            # "gain": self.default_gain,  # May not be supported
        }
    
    async def _make_api_request(self, payload: Dict[str, Any]) -> bytes:
        """Make API request to SiliconFlow"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        timeout = aiohttp.ClientTimeout(total=30.0)  # 30 second timeout
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status == 429:
                        raise TTSProviderRateLimitError("SiliconFlow API rate limit exceeded")
                    elif response.status == 401:
                        raise TTSProviderAPIError("SiliconFlow API authentication failed")
                    elif response.status == 403:
                        raise TTSProviderAPIError("SiliconFlow API access forbidden")
                    else:
                        error_text = await response.text()
                        raise TTSProviderAPIError(f"SiliconFlow API error {response.status}: {error_text}")
                        
            except aiohttp.ClientError as e:
                raise TTSProviderAPIError(f"Network error: {e}")
            except asyncio.TimeoutError:
                raise TTSProviderAPIError("SiliconFlow API request timeout")
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration"""
        # Rough estimation: ~150 words per minute for average speech
        chars_per_second = 200 / 60 / speed  # Adjust for speed
        duration = len(text) / chars_per_second
        return max(0.5, duration)
    
    def _calculate_estimated_cost(self, text: str) -> Dict[str, Any]:
        """Calculate estimated API cost"""
        # SiliconFlow typically has free tier, but may have usage limits
        return {
            "characters": len(text),
            "tier": "free" if hasattr(self, '_is_free_tier') else "unknown",
            "estimated_cost_usd": 0.0  # Free tier
        }
    
    async def _generate_lipsync_data(self, request: TTSRequest, duration: float):
        """Generate lip sync data for Live2D integration"""
        from ..tts_interface import LipSyncData
        
        # Similar implementation to Edge TTS
        phonemes = []
        mouth_shapes = []
        
        chars = list(request.text.replace(" ", ""))
        if chars:
            char_duration = duration / len(chars)
            current_time = 0.0
            
            for char in chars:
                phoneme = self._extract_vowel_sound(char)
                phonemes.append((current_time, phoneme, char_duration))
                
                mouth_params = self._get_mouth_parameters_for_phoneme(phoneme)
                mouth_shapes.append((current_time, mouth_params))
                
                current_time += char_duration
        
        return LipSyncData(
            phonemes=phonemes,
            mouth_shapes=mouth_shapes,
            duration=duration
        )
    
    def _extract_vowel_sound(self, char: str) -> str:
        """Extract vowel sound from character (simplified)"""
        korean_vowels = {
            'ㅏ': 'a', 'ㅓ': 'eo', 'ㅗ': 'o', 'ㅜ': 'u', 'ㅡ': 'eu', 'ㅣ': 'i',
            'ㅐ': 'ae', 'ㅔ': 'e', 'ㅑ': 'ya', 'ㅕ': 'yeo', 'ㅛ': 'yo', 'ㅠ': 'yu'
        }
        
        for vowel, sound in korean_vowels.items():
            if vowel in char:
                return sound
        
        return 'neutral'
    
    def _get_mouth_parameters_for_phoneme(self, phoneme: str) -> dict:
        """Get Live2D mouth parameters for phoneme"""
        mouth_mappings = {
            'a': {'ParamA': 1.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'i': {'ParamA': 0.0, 'ParamI': 1.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'u': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 1.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'e': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 1.0, 'ParamO': 0.0},
            'o': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 1.0},
            'eo': {'ParamA': 0.7, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.5, 'ParamO': 0.0},
            'neutral': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0}
        }
        
        return mouth_mappings.get(phoneme, mouth_mappings['neutral'])
    
    async def check_availability(self) -> bool:
        """Check if SiliconFlow TTS is available"""
        if not self.api_key:
            return False
        
        try:
            # Try a minimal API request to check connectivity
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Small test payload
            test_payload = {
                "model": self.default_model,
                "input": "test",
                "voice": self.default_voice,
                "response_format": self.response_format
            }
            
            timeout = aiohttp.ClientTimeout(total=10.0)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.api_url, json=test_payload, headers=headers) as response:
                    # Any response (even error) means API is reachable
                    return response.status in [200, 400, 401, 429]  # Exclude network errors
                    
        except Exception as e:
            logger.debug(f"SiliconFlow availability check failed: {e}")
            return False
    
    def get_supported_voices(self, language: str) -> list:
        """Get supported voices for language"""
        if language in self.voice_mappings:
            voices = []
            lang_voices = self.voice_mappings[language]
            for voice_type, voice in lang_voices.items():
                if voice_type != "default" and voice not in voices:
                    voices.append(voice)
            return voices
        
        return self.config.get_voices_for_language(language)
    
    async def _provider_health_check(self) -> bool:
        """SiliconFlow specific health check"""
        return await self.check_availability()
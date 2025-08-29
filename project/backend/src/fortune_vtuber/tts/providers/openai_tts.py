"""
OpenAI TTS Provider Implementation

OpenAI TTS provider implementation.
High quality TTS with modern neural voices.
Requires OpenAI API key and subscription.
"""

import asyncio
import time
from typing import Optional
import logging
import io

from ..tts_interface import TTSInterface, TTSRequest, TTSResult, TTSProviderConfig
from ..tts_interface import TTSProviderError, TTSProviderUnavailableError

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import openai
    OPENAI_TTS_AVAILABLE = True
except ImportError:
    OPENAI_TTS_AVAILABLE = False
    logger.warning("openai not available. Install with: pip install openai")


class OpenAITTSProvider(TTSInterface):
    """
    OpenAI TTS Provider
    
    High quality TTS service with modern neural voices.
    Requires OpenAI API key and subscription.
    """
    
    def __init__(self, config: TTSProviderConfig):
        super().__init__(config)
        
        if not OPENAI_TTS_AVAILABLE:
            raise TTSProviderUnavailableError("openai package not installed")
        
        if not config.api_key:
            raise TTSProviderUnavailableError("OpenAI API key required")
        
        # OpenAI TTS specific settings
        self.client = openai.OpenAI(api_key=config.api_key)
        self.default_voice = config.default_voice or "alloy"
        self.file_extension = "mp3"
        
        # Available voices
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        # Voice mappings by style
        self.voice_mappings = {
            "neutral": "alloy",
            "deep": "onyx", 
            "warm": "nova",
            "bright": "shimmer",
            "calm": "echo",
            "energetic": "fable"
        }
    
    async def async_generate_audio(self, request: TTSRequest) -> TTSResult:
        """Generate audio using OpenAI TTS"""
        start_time = time.time()
        
        try:
            # Validate request
            await self._validate_request(request)
            
            # Get optimal voice
            voice = self._get_optimal_voice_for_request(request)
            
            # Generate cache filename
            cache_file = self.generate_cache_filename(request, self.file_extension)
            
            # Prepare request parameters
            tts_params = {
                "model": "tts-1",  # or "tts-1-hd" for higher quality
                "input": request.text,
                "voice": voice,
                "response_format": "mp3"
            }
            
            # Adjust model based on quality preference
            if hasattr(request, 'quality') and request.quality == 'high':
                tts_params["model"] = "tts-1-hd"
            
            # Call OpenAI TTS API
            response = await asyncio.to_thread(
                self.client.audio.speech.create,
                **tts_params
            )
            
            # Save audio data
            response.stream_to_file(cache_file)
            
            # Read audio data
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            
            # Calculate duration
            duration = self._estimate_duration(request.text, request.speed)
            
            # Generate lip sync data if requested
            lip_sync_data = None
            if request.enable_lipsync:
                lip_sync_data = await self._generate_lipsync_data(request, duration)
            
            # Create result
            tts_result = TTSResult(
                audio_data=audio_data,
                audio_format="mp3",
                duration=duration,
                provider=self.config.provider_id,
                voice_used=voice,
                language=request.language,
                text_processed=request.text,
                lip_sync_data=lip_sync_data,
                generation_time=time.time() - start_time,
                metadata={
                    "voice": voice,
                    "model": tts_params["model"],
                    "file_size": len(audio_data)
                }
            )
            
            logger.info(f"OpenAI TTS generated audio: {len(audio_data)} bytes, {duration:.2f}s")
            return tts_result
            
        except Exception as e:
            logger.error(f"OpenAI TTS generation failed: {e}")
            if "rate_limit" in str(e).lower():
                raise TTSProviderError("OpenAI TTS rate limit exceeded")
            elif "quota" in str(e).lower():
                raise TTSProviderError("OpenAI TTS quota exceeded")
            else:
                raise TTSProviderError(f"OpenAI TTS generation failed: {e}")
    
    async def _validate_request(self, request: TTSRequest):
        """Validate TTS request for OpenAI TTS"""
        if len(request.text) > self.config.max_text_length:
            raise TTSProviderError(f"Text too long: {len(request.text)} > {self.config.max_text_length}")
        
        # OpenAI TTS supports most languages but voices are language-neutral
        if not request.text.strip():
            raise TTSProviderError("Empty text not allowed")
    
    def _get_optimal_voice_for_request(self, request: TTSRequest) -> str:
        """Get optimal voice for request"""
        # Check if specific voice requested and available
        if request.voice and request.voice in self.available_voices:
            return request.voice
        
        # Map emotion to voice if available
        if hasattr(request, 'emotion') and request.emotion:
            emotion_str = request.emotion.value if hasattr(request.emotion, 'value') else str(request.emotion)
            if emotion_str in self.voice_mappings:
                return self.voice_mappings[emotion_str]
        
        # Use default voice
        return self.default_voice
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length and speed"""
        # OpenAI TTS typical rate: ~180 words per minute
        # Adjust for different languages and speech patterns
        words = len(text.split())
        if words == 0:
            chars_per_second = 200 / 60 / speed
            duration = len(text) / chars_per_second
        else:
            words_per_second = 180 / 60 / speed
            duration = words / words_per_second
        
        return max(0.5, duration)  # Minimum 0.5 seconds
    
    async def _generate_lipsync_data(self, request: TTSRequest, duration: float):
        """Generate lip sync data for Live2D integration"""
        # Import here to avoid circular imports
        from ..tts_interface import LipSyncData
        
        # Simple phoneme analysis
        phonemes = []
        mouth_shapes = []
        
        # Basic implementation - can be enhanced with proper phonetic analysis
        words = request.text.split()
        if words:
            word_duration = duration / len(words)
            current_time = 0.0
            
            for word in words:
                # Simple vowel detection for each word
                phoneme = self._extract_dominant_vowel(word)
                phonemes.append((current_time, phoneme, word_duration))
                
                # Generate mouth shape parameters
                mouth_params = self._get_mouth_parameters_for_phoneme(phoneme)
                mouth_shapes.append((current_time, mouth_params))
                
                current_time += word_duration
        
        return LipSyncData(
            phonemes=phonemes,
            mouth_shapes=mouth_shapes,
            duration=duration
        )
    
    def _extract_dominant_vowel(self, word: str) -> str:
        """Extract dominant vowel sound from word (simplified)"""
        word_lower = word.lower()
        
        # English vowel patterns (simplified)
        vowel_patterns = {
            'a': ['a', 'ai', 'ay', 'ae'],
            'e': ['e', 'ea', 'ee', 'ei'],
            'i': ['i', 'ie', 'igh', 'y'],
            'o': ['o', 'oa', 'oo', 'ou'],
            'u': ['u', 'ue', 'ui', 'uu']
        }
        
        # Count vowel occurrences
        vowel_counts = {}
        for vowel, patterns in vowel_patterns.items():
            count = 0
            for pattern in patterns:
                count += word_lower.count(pattern)
            if count > 0:
                vowel_counts[vowel] = count
        
        # Return most frequent vowel or default
        if vowel_counts:
            return max(vowel_counts, key=vowel_counts.get)
        
        return 'neutral'  # Default
    
    def _get_mouth_parameters_for_phoneme(self, phoneme: str) -> dict:
        """Get Live2D mouth parameters for phoneme"""
        mouth_shapes = {
            'a': {'mouth_open': 0.8, 'mouth_form': 0.0},
            'e': {'mouth_open': 0.5, 'mouth_form': 0.4},
            'i': {'mouth_open': 0.2, 'mouth_form': 0.8}, 
            'o': {'mouth_open': 0.6, 'mouth_form': -0.3},
            'u': {'mouth_open': 0.3, 'mouth_form': -0.6},
            'neutral': {'mouth_open': 0.1, 'mouth_form': 0.0}
        }
        
        return mouth_shapes.get(phoneme, mouth_shapes['neutral'])
    
    def get_supported_voices(self, language: str = None) -> list:
        """Get supported voices (OpenAI voices are language-neutral)"""
        return self.available_voices.copy()
    
    def supports_language(self, language: str) -> bool:
        """Check if provider supports language (OpenAI TTS is multilingual)"""
        # OpenAI TTS supports most languages with the same set of voices
        return True
    
    async def _provider_health_check(self) -> bool:
        """OpenAI TTS specific health check"""
        try:
            # Simple test with minimal API call
            response = await asyncio.to_thread(
                self.client.audio.speech.create,
                model="tts-1",
                voice="alloy",
                input="test",
                response_format="mp3"
            )
            return response is not None
            
        except Exception as e:
            logger.debug(f"OpenAI TTS health check failed: {e}")
            return False
    
    def _get_default_voice(self, language: str) -> str:
        """Get default voice for language"""
        # Language-specific voice preferences
        language_voice_map = {
            "ko-KR": "nova",      # Warm voice for Korean
            "ja-JP": "shimmer",   # Bright voice for Japanese  
            "zh-CN": "alloy",     # Neutral voice for Chinese
            "en-US": "echo",      # Calm voice for English
            "es-ES": "nova",      # Warm voice for Spanish
            "fr-FR": "shimmer",   # Bright voice for French
            "de-DE": "echo",      # Calm voice for German
        }
        
        return language_voice_map.get(language, self.default_voice)
"""
Edge TTS Provider Implementation

Microsoft Edge TTS provider implementation.
Free, high-quality TTS with Korean voice support (ko-KR-SunHiNeural).
Based on reference implementation with Fortune-specific enhancements.
"""

import asyncio
import time
from typing import Optional
import logging

from ..tts_interface import TTSInterface, TTSRequest, TTSResult, TTSProviderConfig
from ..tts_interface import TTSProviderError, TTSProviderUnavailableError

logger = logging.getLogger(__name__)

# Optional dependency
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logger.warning("edge-tts not available. Install with: pip install edge-tts")


class EdgeTTSProvider(TTSInterface):
    """
    Microsoft Edge TTS Provider
    
    Free, high-quality TTS service with excellent Korean voice support.
    No API key required, making it ideal as primary free provider.
    """
    
    def __init__(self, config: TTSProviderConfig):
        super().__init__(config)
        
        if not EDGE_TTS_AVAILABLE:
            raise TTSProviderUnavailableError("edge-tts package not installed")
        
        # Edge TTS specific settings
        self.default_voice = config.default_voice or "ko-KR-SunHiNeural"
        self.file_extension = "mp3"
        
        # Voice mappings for different languages
        self.voice_mappings = {
            "ko-KR": {
                "female": ["ko-KR-SunHiNeural", "ko-KR-JiMinNeural"],
                "male": ["ko-KR-InJoonNeural", "ko-KR-BongJinNeural"],
                "default": "ko-KR-SunHiNeural"
            },
            "en-US": {
                "female": ["en-US-AriaNeural", "en-US-JennyNeural"],
                "male": ["en-US-GuyNeural", "en-US-DavisNeural"],  
                "default": "en-US-AvaMultilingualNeural"
            },
            "ja-JP": {
                "female": ["ja-JP-NanamiNeural", "ja-JP-AoiNeural"],
                "male": ["ja-JP-KeitaNeural", "ja-JP-DaichiNeural"],
                "default": "ja-JP-NanamiNeural"
            },
            "zh-CN": {
                "female": ["zh-CN-XiaoxiaoNeural", "zh-CN-XiaoyiNeural"],
                "male": ["zh-CN-YunxiNeural", "zh-CN-YunjianNeural"],
                "default": "zh-CN-XiaoxiaoNeural"
            }
        }
    
    async def async_generate_audio(self, request: TTSRequest) -> TTSResult:
        """Generate audio using Edge TTS"""
        start_time = time.time()
        
        try:
            logger.info(f"🔍 EdgeTTS: Starting audio generation")
            logger.info(f"🔍 EdgeTTS: Request text: '{request.text}' (length: {len(request.text)})")
            logger.info(f"🔍 EdgeTTS: Request language: {request.language}")
            logger.info(f"🔍 EdgeTTS: Request voice: {request.voice}")
            logger.info(f"🔍 EdgeTTS: Request speed: {request.speed}")
            
            # Validate request
            await self._validate_request(request)
            logger.info(f"🔍 EdgeTTS: Request validation passed")
            
            # Get optimal voice
            voice = self._get_optimal_voice_for_request(request)
            logger.info(f"🔍 EdgeTTS: Selected voice: {voice}")
            
            # Generate cache filename
            cache_file = self.generate_cache_filename(request, self.file_extension)
            logger.info(f"🔍 EdgeTTS: Cache file: {cache_file}")
            
            # Convert parameters
            rate = self._convert_speed_to_rate(request.speed)
            pitch = self._convert_pitch_to_edge_format(request.pitch)
            volume = self._convert_volume_to_edge_format(request.volume)
            logger.info(f"🔍 EdgeTTS: Parameters - rate: {rate}, pitch: {pitch}, volume: {volume}")
            
            # Create Edge TTS communication
            logger.info(f"🔍 EdgeTTS: Creating Communicate object...")
            communicate = edge_tts.Communicate(
                text=request.text,
                voice=voice,
                rate=rate,
                pitch=pitch,
                volume=volume
            )
            logger.info(f"🔍 EdgeTTS: Communicate object created successfully")
            
            # Save audio file
            logger.info(f"🔍 EdgeTTS: Starting audio synthesis...")
            await communicate.save(cache_file)
            logger.info(f"🔍 EdgeTTS: Audio synthesis completed, file saved")
            
            # Check if file exists and has content
            import os
            if not os.path.exists(cache_file):
                raise TTSProviderError("Cache file was not created")
            
            file_size = os.path.getsize(cache_file)
            logger.info(f"🔍 EdgeTTS: Cache file size: {file_size} bytes")
            
            if file_size == 0:
                raise TTSProviderError("Generated audio file is empty")
            
            # Read audio data
            logger.info(f"🔍 EdgeTTS: Reading audio data from file...")
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            
            logger.info(f"🔍 EdgeTTS: Audio data read successfully: {len(audio_data)} bytes")
            
            if len(audio_data) == 0:
                raise TTSProviderError("No audio data was read from file")
            
            # Calculate duration (rough estimate)
            duration = self._estimate_duration(request.text, request.speed)
            logger.info(f"🔍 EdgeTTS: Estimated duration: {duration:.2f}s")
            
            # Generate lip sync data if requested
            lip_sync_data = None
            if request.enable_lipsync:
                logger.info(f"🔍 EdgeTTS: Generating lip sync data...")
                lip_sync_data = await self._generate_lipsync_data(request, duration)
                logger.info(f"🔍 EdgeTTS: Lip sync data generated")
            
            # Create result
            result = TTSResult(
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
                    "rate": request.speed,
                    "pitch": request.pitch,
                    "volume": request.volume,
                    "file_size": len(audio_data)
                }
            )
            
            # Clean up cache file (optional - keep for caching)
            # self.remove_file(cache_file, verbose=False)
            
            logger.info(f"✅ Edge TTS generated audio: {len(audio_data)} bytes, {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Edge TTS generation failed: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Exception details: {str(e)}")
            import traceback
            logger.error(f"❌ Stack trace: {traceback.format_exc()}")
            
            if "blocked" in str(e).lower():
                raise TTSProviderUnavailableError("Edge TTS might be blocked in your region")
            raise TTSProviderError(f"Edge TTS generation failed: {e}")
    
    async def _validate_request(self, request: TTSRequest):
        """Validate TTS request for Edge TTS"""
        if len(request.text) > self.config.max_text_length:
            raise TTSProviderError(f"Text too long: {len(request.text)} > {self.config.max_text_length}")
        
        if request.language not in self.config.supported_languages:
            raise TTSProviderError(f"Language {request.language} not supported by Edge TTS")
    
    def _get_optimal_voice_for_request(self, request: TTSRequest) -> str:
        """Get optimal voice for request"""
        language = request.language
        
        # Check if specific voice requested and available
        if request.voice:
            available_voices = self.get_supported_voices(language)
            if request.voice in available_voices:
                return request.voice
        
        # Get default voice for language
        if language in self.voice_mappings:
            return self.voice_mappings[language]["default"]
        
        # Fallback to config default
        return self.default_voice
    
    def _convert_speed_to_rate(self, speed: float) -> str:
        """Convert speed multiplier to Edge TTS rate format"""
        if speed == 1.0:
            return "+0%"
        
        # Convert to percentage (-50% to +100%)
        percentage = int((speed - 1.0) * 100)
        percentage = max(-50, min(100, percentage))
        
        if percentage >= 0:
            return f"+{percentage}%"
        else:
            return f"{percentage}%"
    
    def _convert_pitch_to_edge_format(self, pitch: float) -> str:
        """Convert pitch multiplier to Edge TTS pitch format"""
        if pitch == 1.0:
            return "+0Hz"
        
        # Convert to Hz offset (-50Hz to +50Hz approximation)
        hz_offset = int((pitch - 1.0) * 50)
        hz_offset = max(-50, min(50, hz_offset))
        
        if hz_offset >= 0:
            return f"+{hz_offset}Hz"
        else:
            return f"{hz_offset}Hz"
    
    def _convert_volume_to_edge_format(self, volume: float) -> str:
        """Convert volume multiplier to Edge TTS volume format"""
        if volume == 1.0:
            return "+0%"
        
        # Convert to percentage (-50% to +50%)  
        percentage = int((volume - 1.0) * 100)
        percentage = max(-50, min(50, percentage))
        
        if percentage >= 0:
            return f"+{percentage}%"
        else:
            return f"{percentage}%"
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length and speed"""
        # Rough estimation: ~150 words per minute for average speech
        # Korean text: ~200 characters per minute
        chars_per_second = 200 / 60 / speed  # Adjust for speed
        duration = len(text) / chars_per_second
        return max(0.5, duration)  # Minimum 0.5 seconds
    
    async def _generate_lipsync_data(self, request: TTSRequest, duration: float):
        """Generate lip sync data for Live2D integration"""
        # Import here to avoid circular imports
        from ..tts_interface import LipSyncData
        
        # Simple phoneme analysis for Korean text
        phonemes = []
        mouth_shapes = []
        
        # Basic implementation - can be enhanced with proper phonetic analysis
        chars = list(request.text.replace(" ", ""))
        if chars:
            char_duration = duration / len(chars)
            current_time = 0.0
            
            for char in chars:
                # Simple Korean vowel detection
                phoneme = self._extract_vowel_sound(char)
                phonemes.append((current_time, phoneme, char_duration))
                
                # Generate mouth shape parameters
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
        
        # Simple vowel extraction (would need proper Korean decomposition)
        for vowel, sound in korean_vowels.items():
            if vowel in char:
                return sound
        
        # Default to neutral for consonants/unknown
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
        """Check if Edge TTS is available"""
        if not EDGE_TTS_AVAILABLE:
            return False
        
        try:
            # Try a simple test synthesis
            test_text = "안녕하세요"
            communicate = edge_tts.Communicate(test_text, self.default_voice)
            
            # Just create the communicate object - don't actually generate audio
            # If this succeeds, Edge TTS is likely available
            return True
            
        except Exception as e:
            logger.debug(f"Edge TTS availability check failed: {e}")
            return False
    
    def get_supported_voices(self, language: str) -> list:
        """Get supported voices for language"""
        if language in self.voice_mappings:
            voices = []
            lang_voices = self.voice_mappings[language]
            for voice_type, voice_list in lang_voices.items():
                if voice_type != "default":
                    if isinstance(voice_list, list):
                        voices.extend(voice_list)
                    else:
                        voices.append(voice_list)
            return voices
        
        return self.config.get_voices_for_language(language)
    
    async def _provider_health_check(self) -> bool:
        """Edge TTS specific health check"""
        return await self.check_availability()
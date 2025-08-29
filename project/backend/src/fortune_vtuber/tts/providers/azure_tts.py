"""
Azure Cognitive Services TTS Provider Implementation

Microsoft Azure TTS provider implementation.
Premium quality TTS with extensive language support.
Requires Azure Cognitive Services subscription.
"""

import asyncio
import time
from typing import Optional
import logging

from ..tts_interface import TTSInterface, TTSRequest, TTSResult, TTSProviderConfig
from ..tts_interface import TTSProviderError, TTSProviderUnavailableError

try:
    from ...config.logging_config import get_logger, log_tts_performance
    logger = get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    # Fallback performance logging
    def log_tts_performance(provider: str, duration: float, text_length: int) -> None:
        if duration >= 5.0:
            logger.warning(f"TTS_SLOW_RESPONSE - Provider: {provider}, Duration: {duration:.2f}s, Text Length: {text_length}")
        elif duration >= 3.0:
            logger.info(f"TTS_MODERATE_RESPONSE - Provider: {provider}, Duration: {duration:.2f}s, Text Length: {text_length}")

# Optional dependency
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_TTS_AVAILABLE = True
except ImportError:
    AZURE_TTS_AVAILABLE = False
    logger.warning("azure-cognitiveservices-speech not available. Install with: pip install azure-cognitiveservices-speech")


class AzureTTSProvider(TTSInterface):
    """
    Azure Cognitive Services TTS Provider
    
    Premium quality TTS service with extensive voice support.
    Requires Azure subscription and API key.
    """
    
    def __init__(self, config: TTSProviderConfig):
        super().__init__(config)
        
        if not AZURE_TTS_AVAILABLE:
            raise TTSProviderUnavailableError("azure-cognitiveservices-speech package not installed")
        
        if not config.api_key:
            raise TTSProviderUnavailableError("Azure API key required")
        
        # Azure TTS specific settings
        self.api_key = config.api_key
        self.region = config.additional_config.get("region", "eastus")
        self.default_voice = config.default_voice or "ko-KR-SunHiNeural"
        self.file_extension = "wav"
        
        # Initialize Azure Speech Config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.api_key,
            region=self.region
        )
        
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
                "default": "en-US-AriaNeural"
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
        """Generate audio using Azure TTS"""
        start_time = time.time()
        
        try:
            # Validate request
            await self._validate_request(request)
            
            # Get optimal voice
            voice = self._get_optimal_voice_for_request(request)
            
            # Generate cache filename
            cache_file = self.generate_cache_filename(request, self.file_extension)
            
            # Configure speech synthesizer
            audio_config = speechsdk.audio.AudioOutputConfig(filename=cache_file)
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Build SSML
            ssml = self._build_ssml(request, voice)
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
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
                    audio_format="wav",
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
                
                # Log performance metrics
                generation_time = time.time() - start_time
                log_tts_performance("Azure", generation_time, len(request.text))
                
                logger.info(f"Azure TTS generated audio: {len(audio_data)} bytes, {duration:.2f}s, generation_time: {generation_time:.2f}s")
                return tts_result
                
            else:
                error_message = f"Azure TTS synthesis failed: {result.reason}"
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation = result.cancellation_details
                    error_message += f" - {cancellation.reason}: {cancellation.error_details}"
                raise TTSProviderError(error_message)
                
        except Exception as e:
            logger.error(f"Azure TTS generation failed: {e}")
            raise TTSProviderError(f"Azure TTS generation failed: {e}")
    
    async def _validate_request(self, request: TTSRequest):
        """Validate TTS request for Azure TTS"""
        if len(request.text) > self.config.max_text_length:
            raise TTSProviderError(f"Text too long: {len(request.text)} > {self.config.max_text_length}")
        
        if request.language not in self.config.supported_languages:
            raise TTSProviderError(f"Language {request.language} not supported by Azure TTS")
    
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
    
    def _build_ssml(self, request: TTSRequest, voice: str) -> str:
        """Build SSML for Azure TTS"""
        # Convert parameters to SSML format
        rate = self._convert_speed_to_rate(request.speed)
        pitch = self._convert_pitch_to_ssml(request.pitch)
        volume = self._convert_volume_to_ssml(request.volume)
        
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{request.language}">
            <voice name="{voice}">
                <prosody rate="{rate}" pitch="{pitch}" volume="{volume}">
                    {request.text}
                </prosody>
            </voice>
        </speak>"""
        
        return ssml
    
    def _convert_speed_to_rate(self, speed: float) -> str:
        """Convert speed multiplier to SSML rate format"""
        if speed == 1.0:
            return "medium"
        elif speed < 0.8:
            return "slow"
        elif speed < 1.2:
            return "medium"
        else:
            return "fast"
    
    def _convert_pitch_to_ssml(self, pitch: float) -> str:
        """Convert pitch multiplier to SSML pitch format"""
        if pitch == 1.0:
            return "medium"
        elif pitch < 0.8:
            return "low"
        elif pitch < 1.2:
            return "medium"
        else:
            return "high"
    
    def _convert_volume_to_ssml(self, volume: float) -> str:
        """Convert volume multiplier to SSML volume format"""
        if volume <= 0.3:
            return "silent"
        elif volume <= 0.6:
            return "soft"
        elif volume <= 1.2:
            return "medium"
        else:
            return "loud"
    
    def _estimate_duration(self, text: str, speed: float) -> float:
        """Estimate audio duration based on text length and speed"""
        # Rough estimation: ~150 words per minute for average speech
        chars_per_second = 200 / 60 / speed  # Adjust for speed
        duration = len(text) / chars_per_second
        return max(0.5, duration)  # Minimum 0.5 seconds
    
    async def _generate_lipsync_data(self, request: TTSRequest, duration: float):
        """Generate lip sync data for Live2D integration"""
        # Import here to avoid circular imports
        from ..tts_interface import LipSyncData
        
        # Simple phoneme analysis
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
        
        for vowel, sound in korean_vowels.items():
            if vowel in char:
                return sound
        
        return 'neutral'  # Default
    
    def _get_mouth_parameters_for_phoneme(self, phoneme: str) -> dict:
        """Get Live2D mouth parameters for phoneme"""
        mouth_shapes = {
            'a': {'mouth_open': 0.8, 'mouth_form': 0.0},
            'i': {'mouth_open': 0.2, 'mouth_form': 0.8}, 
            'u': {'mouth_open': 0.3, 'mouth_form': -0.6},
            'e': {'mouth_open': 0.5, 'mouth_form': 0.4},
            'o': {'mouth_open': 0.6, 'mouth_form': -0.3},
            'neutral': {'mouth_open': 0.0, 'mouth_form': 0.0}
        }
        
        return mouth_shapes.get(phoneme, mouth_shapes['neutral'])
    
    async def _provider_health_check(self) -> bool:
        """Azure TTS specific health check"""
        try:
            # Simple test synthesis
            test_config = speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=self.region
            )
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=test_config)
            
            # Test with minimal text
            result = synthesizer.speak_text_async("test").get()
            return result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted
            
        except Exception as e:
            logger.debug(f"Azure TTS health check failed: {e}")
            return False
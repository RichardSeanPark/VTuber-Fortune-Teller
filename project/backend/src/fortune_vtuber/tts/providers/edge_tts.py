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
            
            # Calculate accurate duration using librosa (with fallback)
            accurate_duration = self._get_accurate_audio_duration(cache_file)
            if accurate_duration is not None:
                duration = accurate_duration
                logger.info(f"📏 EdgeTTS: librosa 정확한 duration: {duration:.6f}초")
            else:
                duration = self._estimate_duration(request.text, request.speed)
                logger.info(f"📏 EdgeTTS: 폴백 추정 duration: {duration:.2f}초")
                
            # TTS vs 실제 duration 비교 로그
            estimated = self._estimate_duration(request.text, request.speed)
            if accurate_duration is not None:
                diff_percent = abs(duration - estimated) / estimated * 100
                logger.info(f"📊 Duration 비교: TTS추정={estimated:.3f}초, librosa실제={duration:.6f}초, 차이={diff_percent:.1f}%")
            
            # Generate lip sync data if requested
            lip_sync_data = None
            if request.enable_lipsync:
                logger.info(f"🔍 EdgeTTS: Generating lip sync data...")
                lip_sync_data = await self._generate_lipsync_data(request, duration)
                logger.info(f"🎭 EdgeTTS: Lip sync 생성 완료 - 타입: {type(lip_sync_data)}")
                if lip_sync_data:
                    logger.info(f"🎭 EdgeTTS: Lip sync 데이터 상세 - phonemes: {len(lip_sync_data.phonemes)}, mouth_shapes: {len(lip_sync_data.mouth_shapes)}")
                else:
                    logger.warning("⚠️ EdgeTTS: Lip sync 데이터가 None임")
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
        """Estimate audio duration - 폴백용 추정치"""
        # 기본 추정 (librosa 실패 시 사용)
        chars_per_second = 200 / 60 / speed
        duration = len(text) / chars_per_second
        return max(0.5, duration)
    
    def _get_accurate_audio_duration(self, cache_file: str) -> float:
        """librosa를 사용한 정확한 오디오 길이 측정"""
        try:
            import librosa
            
            logger.info(f"📏 librosa로 정확한 duration 측정 시작: {cache_file}")
            
            # librosa로 오디오 파일 읽기 및 길이 측정
            y, sr = librosa.load(cache_file, sr=None)
            accurate_duration = librosa.get_duration(y=y, sr=sr)
            
            logger.info(f"✅ librosa 측정 완료: {accurate_duration:.6f}초")
            return accurate_duration
            
        except ImportError:
            logger.warning("⚠️ librosa가 설치되지 않음, 추정치 사용")
            return None
        except Exception as e:
            logger.warning(f"⚠️ librosa 측정 실패: {e}, 추정치 사용")
            return None
    
    async def _generate_lipsync_data(self, request: TTSRequest, duration: float):
        """3.5Hz 단순 패턴 기반 립싱크 데이터 생성 (개선된 버전)"""
        # Import here to avoid circular imports
        from ..tts_interface import LipSyncData
        import math
        
        logger.info(f"🎭 EdgeTTS 개선된 립싱크 데이터 생성 시작: text='{request.text}', duration={duration}초")
        
        phonemes = []
        mouth_shapes = []
        
        if duration <= 0:
            logger.warning("⚠️ Duration이 0 이하, 빈 립싱크 데이터 반환")
            return LipSyncData.empty(0.0)
        
        # 3.5Hz 기본 주파수로 자연스러운 말하기 패턴 생성
        frame_rate = 30.0  # 30fps
        total_frames = int(duration * frame_rate)
        base_frequency = 3.5  # 초당 3.5회 열림/닫힘 (자연스러운 말하기 속도)
        
        logger.info(f"📊 립싱크 파라미터: duration={duration}초, frames={total_frames}개, frequency={base_frequency}Hz")
        
        for frame_idx in range(total_frames):
            timestamp = frame_idx / frame_rate
            
            # 약간의 주파수 변화로 자연스러움 추가
            frequency_variation = 0.5 * math.sin(timestamp * 0.7)
            actual_frequency = base_frequency + frequency_variation
            
            # 사인파 기반 입 열림 강도 계산
            mouth_open_intensity = abs(math.sin(timestamp * actual_frequency * math.pi))
            
            # 기본 열림 정도 + 강도 조절
            base_open = 0.3 + (mouth_open_intensity * 0.5)  # 0.3~0.8 범위
            
            # 립싱크 파라미터 (Live2D 입 모양 제어용)
            mouth_params = {
                "ParamMouthOpenY": min(1.0, base_open),  # 입 세로 열림 (0~1)
                "ParamMouthForm": 0.0,  # 입 모양 (중성)
                "ParamMouthSizeX": 0.2 + (mouth_open_intensity * 0.3)  # 입 가로 크기
            }
            
            # Phoneme 데이터 (간단한 패턴)
            if mouth_open_intensity > 0.6:
                phoneme = "a"  # 크게 벌림
            elif mouth_open_intensity > 0.3:
                phoneme = "o"  # 중간 벌림
            else:
                phoneme = "silence"  # 닫힘
                
            phonemes.append((timestamp, phoneme, 1.0/frame_rate))
            mouth_shapes.append((timestamp, mouth_params))
            
            # 처음 5프레임과 마지막 5프레임 상세 로그
            if frame_idx < 5 or frame_idx >= total_frames - 5:
                logger.info(f"  📊 프레임[{frame_idx}] t={timestamp:.3f}초: intensity={mouth_open_intensity:.3f}, phoneme='{phoneme}', mouth_open={base_open:.3f}")
        
        logger.info(f"✅ EdgeTTS 개선된 립싱크 데이터 생성 완료:")
        logger.info(f"   - phonemes: {len(phonemes)}개 (3.5Hz 기반)")
        logger.info(f"   - mouth_shapes: {len(mouth_shapes)}개 (사인파 패턴)")
        logger.info(f"   - duration: {duration}초")
        logger.info(f"   - frame_rate: {frame_rate}fps")
        
        return LipSyncData(
            phonemes=phonemes,
            mouth_shapes=mouth_shapes,
            duration=duration,
            frame_rate=frame_rate
        )
    
    def _extract_vowel_sound(self, char: str) -> str:
        """Extract vowel sound from character - 향상된 한국어 음성학적 분석"""
        logger.debug(f"🔍 음성 추출 대상 문자: '{char}'")
        
        # 한국어 기본 모음과 복합 모음 매핑
        korean_vowels = {
            'ㅏ': 'a', 'ㅓ': 'eo', 'ㅗ': 'o', 'ㅜ': 'u', 'ㅡ': 'eu', 'ㅣ': 'i',
            'ㅐ': 'ae', 'ㅔ': 'e', 'ㅑ': 'ya', 'ㅕ': 'yeo', 'ㅛ': 'yo', 'ㅠ': 'yu',
            'ㅒ': 'yae', 'ㅖ': 'ye', 'ㅘ': 'wa', 'ㅙ': 'wae', 'ㅚ': 'oe',
            'ㅝ': 'wo', 'ㅞ': 'we', 'ㅟ': 'wi', 'ㅢ': 'ui'
        }
        
        # 단순 문자열 검색 (기본적인 방법)
        for vowel, sound in korean_vowels.items():
            if vowel in char:
                logger.debug(f"  → 발견된 모음: '{vowel}' -> 음성: '{sound}'")
                return sound
        
        # 한국어 완성형 문자 분해 시도 (유니코드 범위: 가-힣)
        if '가' <= char <= '힣':
            # 한글 유니코드 분해 공식
            char_code = ord(char) - ord('가')
            vowel_index = (char_code % 588) // 28  # 중성(모음) 인덱스
            
            # 현대 한국어 모음 순서 (ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ)
            vowel_sounds = [
                'a', 'ae', 'ya', 'yae', 'eo', 'e', 'yeo', 'ye',
                'o', 'wa', 'wae', 'oe', 'yo', 'u', 'wo', 'we', 'wi', 'yu', 'eu', 'ui', 'i'
            ]
            
            if 0 <= vowel_index < len(vowel_sounds):
                sound = vowel_sounds[vowel_index]
                logger.debug(f"  → 유니코드 분해: 모음인덱스={vowel_index} -> 음성='{sound}'")
                return sound
        
        # 영어나 기타 언어의 모음
        english_vowels = {
            'a': 'a', 'e': 'e', 'i': 'i', 'o': 'o', 'u': 'u',
            'A': 'a', 'E': 'e', 'I': 'i', 'O': 'o', 'U': 'u'
        }
        
        if char in english_vowels:
            sound = english_vowels[char]
            logger.debug(f"  → 영어 모음: '{char}' -> 음성: '{sound}'")
            return sound
        
        # 숫자나 특수문자는 중성 상태
        if char.isdigit() or not char.isalpha():
            logger.debug(f"  → 숫자/특수문자: '{char}' -> 중성")
            return 'neutral'
        
        # 자음이나 알 수 없는 문자는 중성 상태
        logger.debug(f"  → 자음/미식별: '{char}' -> 중성")
        return 'neutral'
    
    def _get_mouth_parameters_for_phoneme(self, phoneme: str) -> dict:
        """Get Live2D mouth parameters for phoneme - 정확한 Live2D 파라미터명 사용"""
        logger.info(f"🎭 파라미터 생성 - phoneme: {phoneme}")
        
        # 실제 Live2D Mao 모델에서 사용되는 정확한 파라미터명과 의미있는 값 사용
        mouth_mappings = {
            # 'ㅏ' 소리 - 입을 크게 벌리고 세로로 열기 (아)
            'a': {
                'ParamMouthOpenY': 0.8,      # 세로로 크게 입 벌림
                'ParamMouthForm': 0.0,       # 중립적인 입 모양
                'ParamMouthOpenX': 0.3,      # 약간 가로로도 벌림
                'ParamMouthUp': 0.2,         # 윗입 약간 올림
                'ParamMouthDown': 0.6        # 아랫입 많이 내림
            },
            # 'ㅣ' 소리 - 입을 가로로 벌리기 (이)
            'i': {
                'ParamMouthOpenY': 0.2,      # 세로로는 조금만
                'ParamMouthForm': 0.5,       # 입 모양 변화
                'ParamMouthOpenX': 0.7,      # 가로로 크게 벌림
                'ParamMouthUp': 0.4,         # 윗입 올림
                'ParamMouthDown': 0.1        # 아랫입은 조금만
            },
            # 'ㅜ' 소리 - 입을 둥글게 작게 (우)
            'u': {
                'ParamMouthOpenY': 0.3,      # 적당히 세로 벌림
                'ParamMouthForm': -0.7,      # 둥근 모양으로
                'ParamMouthOpenX': 0.1,      # 가로는 거의 안 벌림
                'ParamMouthUp': 0.3,         # 윗입 모아서
                'ParamMouthDown': 0.3        # 아랫입도 모아서
            },
            # 'ㅔ' 소리 - 중간 정도 벌림 (에)
            'e': {
                'ParamMouthOpenY': 0.5,      # 중간 정도 세로 벌림
                'ParamMouthForm': 0.3,       # 약간의 입 모양 변화
                'ParamMouthOpenX': 0.4,      # 중간 정도 가로 벌림
                'ParamMouthUp': 0.3,         # 윗입 적당히
                'ParamMouthDown': 0.4        # 아랫입 적당히
            },
            # 'ㅗ' 소리 - 둥글게 중간 크기 (오)
            'o': {
                'ParamMouthOpenY': 0.6,      # 크게 세로 벌림
                'ParamMouthForm': -0.5,      # 둥근 모양
                'ParamMouthOpenX': 0.2,      # 가로는 적게
                'ParamMouthUp': 0.5,         # 윗입 둥글게
                'ParamMouthDown': 0.5        # 아랫입 둥글게
            },
            # 'ㅓ' 소리 - 'ㅏ'와 'ㅔ'의 중간 (어)
            'eo': {
                'ParamMouthOpenY': 0.6,      # 적당히 크게 세로 벌림
                'ParamMouthForm': 0.1,       # 약간의 변화
                'ParamMouthOpenX': 0.3,      # 적당한 가로 벌림
                'ParamMouthUp': 0.3,         # 윗입 적당히
                'ParamMouthDown': 0.5        # 아랫입 좀 더
            },
            # 다른 한국어 모음들
            'ae': {  # ㅐ
                'ParamMouthOpenY': 0.7,
                'ParamMouthForm': 0.4,
                'ParamMouthOpenX': 0.5,
                'ParamMouthUp': 0.4,
                'ParamMouthDown': 0.5
            },
            'ya': {  # ㅑ
                'ParamMouthOpenY': 0.8,
                'ParamMouthForm': 0.2,
                'ParamMouthOpenX': 0.4,
                'ParamMouthUp': 0.3,
                'ParamMouthDown': 0.6
            },
            'yeo': {  # ㅕ
                'ParamMouthOpenY': 0.6,
                'ParamMouthForm': 0.3,
                'ParamMouthOpenX': 0.4,
                'ParamMouthUp': 0.3,
                'ParamMouthDown': 0.5
            },
            'yo': {  # ㅛ
                'ParamMouthOpenY': 0.7,
                'ParamMouthForm': -0.4,
                'ParamMouthOpenX': 0.2,
                'ParamMouthUp': 0.5,
                'ParamMouthDown': 0.5
            },
            'yu': {  # ㅠ
                'ParamMouthOpenY': 0.4,
                'ParamMouthForm': -0.6,
                'ParamMouthOpenX': 0.1,
                'ParamMouthUp': 0.4,
                'ParamMouthDown': 0.4
            },
            # 중성 상태 (조용한 순간이나 자음)
            'neutral': {
                'ParamMouthOpenY': 0.0,
                'ParamMouthForm': 0.0,
                'ParamMouthOpenX': 0.0,
                'ParamMouthUp': 0.0,
                'ParamMouthDown': 0.0
            }
        }
        
        result = mouth_mappings.get(phoneme, mouth_mappings['neutral'])
        logger.info(f"🎭 파라미터 결과: {result}")
        return result
    
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
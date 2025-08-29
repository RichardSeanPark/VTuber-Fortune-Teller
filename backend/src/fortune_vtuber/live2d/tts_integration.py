"""
TTS(Text-to-Speech) 연동 시스템

Live2D와 음성 합성의 실시간 동기화
감정별 음성 톤 조절 및 립싱크 기능
다국어 지원 및 음성 캐싱

UPDATED: Now uses the new multi-provider TTS system (Phase 8.1)
with Edge TTS, SiliconFlow TTS, and fallback chain support.
"""

import asyncio
import json
import base64
import re
import time
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import logging

# Import new TTS system
from ..tts import (
    Live2DTTSManager, Live2DTTSRequest, Live2DTTSResult,
    TTSConfigManager, EmotionType, live2d_tts_manager
)

logger = logging.getLogger(__name__)


# Legacy enums - maintained for backward compatibility
class TTSEngine(str, Enum):
    """TTS 엔진 타입 (Legacy - use TTSProviderType from new system)"""
    EDGE_TTS = "edge_tts"
    GOOGLE_TTS = "google_tts"
    AZURE_TTS = "azure_tts"
    OPENAI_TTS = "openai_tts"
    LOCAL_TTS = "local_tts"


class VoiceGender(str, Enum):
    """음성 성별"""
    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


class EmotionalTone(str, Enum):
    """감정적 톤 (Legacy - use EmotionType from new system)"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    MYSTERIOUS = "mysterious"
    WORRIED = "worried"
    PLAYFUL = "playful"


@dataclass
class VoiceProfile:
    """음성 프로파일"""
    engine: TTSEngine
    voice_name: str
    language: str
    gender: VoiceGender
    pitch: float = 1.0
    speed: float = 1.0
    volume: float = 1.0


@dataclass
class TTSRequest:
    """TTS 요청"""
    text: str
    voice_profile: VoiceProfile
    emotion_tone: Optional[EmotionalTone] = None
    session_id: str = ""
    enable_lipsync: bool = True
    cache_key: Optional[str] = None


@dataclass
class LipSyncData:
    """립싱크 데이터"""
    phonemes: List[Tuple[float, str, float]]  # (timestamp, phoneme, duration)
    mouth_shapes: List[Tuple[float, Dict[str, float]]]  # (timestamp, mouth_parameters)
    total_duration: float


@dataclass
class TTSResult:
    """TTS 결과"""
    audio_data: bytes
    audio_format: str
    duration: float
    lip_sync: Optional[LipSyncData] = None
    cached: bool = False
    generation_time: float = 0.0


class TTSIntegrationService:
    """
    TTS 통합 서비스 (Updated for Phase 8.1)
    
    This class now acts as a wrapper around the new multi-provider TTS system
    while maintaining backward compatibility with existing API.
    """
    
    def __init__(self):
        # Use new TTS system
        self.live2d_tts_manager = live2d_tts_manager
        
        # Legacy compatibility - maintain old interface
        self.audio_cache: Dict[str, TTSResult] = {}
        self.voice_profiles: Dict[str, VoiceProfile] = self._initialize_voice_profiles()
        self.emotional_adjustments: Dict[EmotionalTone, Dict[str, float]] = self._initialize_emotional_adjustments()
        self.phoneme_mapping = self._initialize_phoneme_mapping()
        
        # 캐시 설정
        self.cache_max_size = 100
        self.cache_max_age_hours = 24
        
        logger.info("TTS Integration Service initialized with new multi-provider system")
        
    def _initialize_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """음성 프로파일 초기화"""
        return {
            # 한국어 여성 음성 (기본)
            "ko_female_default": VoiceProfile(
                engine=TTSEngine.EDGE_TTS,
                voice_name="ko-KR-SunHiNeural",
                language="ko-KR",
                gender=VoiceGender.FEMALE,
                pitch=1.1,
                speed=1.0,
                volume=0.9
            ),
            
            # 한국어 여성 음성 (부드러운)
            "ko_female_soft": VoiceProfile(
                engine=TTSEngine.EDGE_TTS,
                voice_name="ko-KR-JiMinNeural",
                language="ko-KR",
                gender=VoiceGender.FEMALE,
                pitch=1.0,
                speed=0.95,
                volume=0.85
            ),
            
            # 영어 여성 음성
            "en_female_default": VoiceProfile(
                engine=TTSEngine.EDGE_TTS,
                voice_name="en-US-AriaNeural",
                language="en-US",
                gender=VoiceGender.FEMALE,
                pitch=1.05,
                speed=1.0,
                volume=0.9
            ),
            
            # 일본어 여성 음성
            "ja_female_default": VoiceProfile(
                engine=TTSEngine.EDGE_TTS,
                voice_name="ja-JP-NanamiNeural",
                language="ja-JP",
                gender=VoiceGender.FEMALE,
                pitch=1.1,
                speed=0.95,
                volume=0.9
            )
        }
    
    def _initialize_emotional_adjustments(self) -> Dict[EmotionalTone, Dict[str, float]]:
        """감정별 음성 조절 초기화"""
        return {
            EmotionalTone.HAPPY: {
                "pitch_modifier": 1.15,
                "speed_modifier": 1.1,
                "volume_modifier": 1.0,
                "expression_strength": 0.8
            },
            EmotionalTone.SAD: {
                "pitch_modifier": 0.9,
                "speed_modifier": 0.85,
                "volume_modifier": 0.8,
                "expression_strength": 0.6
            },
            EmotionalTone.ANGRY: {
                "pitch_modifier": 1.2,
                "speed_modifier": 1.15,
                "volume_modifier": 1.1,
                "expression_strength": 1.0
            },
            EmotionalTone.EXCITED: {
                "pitch_modifier": 1.25,
                "speed_modifier": 1.2,
                "volume_modifier": 1.0,
                "expression_strength": 0.9
            },
            EmotionalTone.CALM: {
                "pitch_modifier": 0.95,
                "speed_modifier": 0.9,
                "volume_modifier": 0.85,
                "expression_strength": 0.5
            },
            EmotionalTone.MYSTERIOUS: {
                "pitch_modifier": 0.85,
                "speed_modifier": 0.8,
                "volume_modifier": 0.9,
                "expression_strength": 0.7
            },
            EmotionalTone.WORRIED: {
                "pitch_modifier": 1.05,
                "speed_modifier": 0.9,
                "volume_modifier": 0.8,
                "expression_strength": 0.6
            },
            EmotionalTone.PLAYFUL: {
                "pitch_modifier": 1.15,
                "speed_modifier": 1.05,
                "volume_modifier": 0.95,
                "expression_strength": 0.8
            }
        }
    
    def _initialize_phoneme_mapping(self) -> Dict[str, Dict[str, float]]:
        """음성학적 립싱크 매핑 초기화"""
        return {
            # 한국어 모음
            'ㅏ': {'ParamA': 1.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'ㅓ': {'ParamA': 0.7, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.5, 'ParamO': 0.0},
            'ㅗ': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 1.0},
            'ㅜ': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 1.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'ㅡ': {'ParamA': 0.0, 'ParamI': 0.3, 'ParamU': 0.5, 'ParamE': 0.0, 'ParamO': 0.0},
            'ㅣ': {'ParamA': 0.0, 'ParamI': 1.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'ㅐ': {'ParamA': 0.8, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.6, 'ParamO': 0.0},
            'ㅔ': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 1.0, 'ParamO': 0.0},
            
            # 영어 음소
            'a': {'ParamA': 1.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'e': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 1.0, 'ParamO': 0.0},
            'i': {'ParamA': 0.0, 'ParamI': 1.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0},
            'o': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 1.0},
            'u': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 1.0, 'ParamE': 0.0, 'ParamO': 0.0},
            
            # 자음 (입 모양 변화)
            'p': {'ParamMouthForm': 0.0},  # 입 닫기
            'b': {'ParamMouthForm': 0.0},  # 입 닫기
            'm': {'ParamMouthForm': 0.0},  # 입 닫기
            'f': {'ParamMouthDown': 0.3},  # 아래입술 물기
            'v': {'ParamMouthDown': 0.3},  # 아래입술 물기
            
            # 무음 (입 닫기)
            'silence': {'ParamA': 0.0, 'ParamI': 0.0, 'ParamU': 0.0, 'ParamE': 0.0, 'ParamO': 0.0}
        }
    
    async def synthesize_speech(self, request: TTSRequest) -> TTSResult:
        """
        음성 합성 실행 (Updated for Phase 8.1)
        Now uses the new multi-provider TTS system with fallback chains.
        """
        start_time = time.time()
        
        try:
            # Convert legacy request to new format
            live2d_request = self._convert_to_live2d_request(request)
            
            # Use new TTS system
            live2d_result = await self.live2d_tts_manager.generate_speech_with_animation(live2d_request)
            
            # Convert back to legacy format for compatibility
            legacy_result = self._convert_to_legacy_result(live2d_result, request.session_id)
            
            # Cache the result (legacy behavior)
            cache_key = self._generate_cache_key(request)
            self.audio_cache[cache_key] = legacy_result
            self._cleanup_cache()
            
            logger.info(f"TTS synthesized (new system) for session {request.session_id} in {legacy_result.generation_time:.2f}s")
            return legacy_result
            
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            # Fall back to old behavior if needed
            try:
                return await self._legacy_synthesize_speech(request)
            except Exception as fallback_error:
                logger.error(f"Legacy fallback also failed: {fallback_error}")
                raise e
    
    def _convert_to_live2d_request(self, request: TTSRequest) -> Live2DTTSRequest:
        """Convert legacy TTSRequest to new Live2DTTSRequest"""
        # Map legacy emotion to new emotion type
        emotion_mapping = {
            EmotionalTone.HAPPY: EmotionType.HAPPY,
            EmotionalTone.SAD: EmotionType.SAD,
            EmotionalTone.EXCITED: EmotionType.EXCITED,
            EmotionalTone.CALM: EmotionType.CALM,
            EmotionalTone.MYSTERIOUS: EmotionType.MYSTICAL,
            EmotionalTone.WORRIED: EmotionType.WORRIED,
            EmotionalTone.PLAYFUL: EmotionType.PLAYFUL,
        }
        
        emotion = None
        if hasattr(request, 'emotion_tone') and request.emotion_tone:
            emotion = emotion_mapping.get(request.emotion_tone, EmotionType.NEUTRAL)
        
        return Live2DTTSRequest(
            text=request.text,
            user_id="default",  # Legacy requests don't have user_id
            session_id=request.session_id,
            language="ko-KR",  # Default language
            voice=getattr(request.voice_profile, 'voice_name', None) if hasattr(request, 'voice_profile') else None,
            emotion=emotion,
            speed=getattr(request.voice_profile, 'speed', 1.0) if hasattr(request, 'voice_profile') else 1.0,
            pitch=getattr(request.voice_profile, 'pitch', 1.0) if hasattr(request, 'voice_profile') else 1.0,
            volume=getattr(request.voice_profile, 'volume', 1.0) if hasattr(request, 'voice_profile') else 1.0,
            enable_lipsync=request.enable_lipsync
        )
    
    def _convert_to_legacy_result(self, live2d_result: Live2DTTSResult, session_id: str) -> TTSResult:
        """Convert new Live2DTTSResult to legacy TTSResult"""
        tts_result = live2d_result.tts_result
        
        return TTSResult(
            audio_data=tts_result.audio_data,
            audio_format=tts_result.audio_format,
            duration=tts_result.duration,
            lip_sync=tts_result.lip_sync_data,
            cached=tts_result.cached,
            generation_time=tts_result.generation_time
        )
    
    async def _legacy_synthesize_speech(self, request: TTSRequest) -> TTSResult:
        """Legacy TTS synthesis as fallback"""
        # Simple fallback implementation
        await asyncio.sleep(0.5)  # Simulate synthesis time
        duration = len(request.text) * 0.1
        dummy_audio = b"dummy_audio_data"
        
        return TTSResult(
            audio_data=dummy_audio,
            audio_format="wav",
            duration=duration,
            lip_sync=None,
            cached=False,
            generation_time=0.5
        )
    
    async def synthesize_with_live2d_sync(self, request: TTSRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Live2D와 동기화된 TTS 스트리밍 (Updated for Phase 8.1)
        Now uses the new streaming system with enhanced Live2D synchronization.
        """
        try:
            # Convert to new request format
            live2d_request = self._convert_to_live2d_request(request)
            
            # Use new streaming system
            async for event in self.live2d_tts_manager.stream_live2d_tts(live2d_request):
                # Convert events to legacy format for backward compatibility
                if event["type"] == "tts_stream_start":
                    yield {
                        "type": "tts_start",
                        "data": {
                            "session_id": request.session_id,
                            "duration": event["data"]["total_duration"],
                            "audio_data": base64.b64encode(event["data"]["audio_data"]).decode(),
                            "audio_format": event["data"]["audio_format"],
                            "provider": event["data"]["provider"]
                        }
                    }
                elif event["type"] == "live2d_sync":
                    # Forward Live2D sync events
                    yield event
                elif event["type"] == "tts_stream_complete":
                    yield {
                        "type": "tts_complete",
                        "data": {
                            "session_id": request.session_id,
                            "duration": event["data"]["provider_info"]["generation_time"],
                            "cached": False,
                            "provider_info": event["data"]["provider_info"]
                        }
                    }
                elif event["type"] == "tts_stream_error":
                    yield {
                        "type": "tts_error",
                        "data": {
                            "session_id": request.session_id,
                            "error": event["data"]["error"]
                        }
                    }
            
        except Exception as e:
            yield {
                "type": "tts_error",
                "data": {
                    "session_id": request.session_id,
                    "error": str(e)
                }
            }
    
    def get_voice_profile_for_emotion(self, emotion: str, language: str = "ko-KR") -> VoiceProfile:
        """감정에 최적화된 음성 프로파일 선택"""
        # 언어별 기본 프로파일 매핑
        language_profiles = {
            "ko-KR": "ko_female_default",
            "en-US": "en_female_default", 
            "ja-JP": "ja_female_default"
        }
        
        # 감정별 프로파일 선택 (향후 확장 가능)
        emotion_profiles = {
            "mystical": "ko_female_soft",  # 신비로운 운세는 부드러운 음성
            "comfort": "ko_female_soft",   # 위로할 때도 부드러운 음성
        }
        
        profile_key = emotion_profiles.get(emotion, language_profiles.get(language, "ko_female_default"))
        return self.voice_profiles[profile_key]
    
    def _generate_cache_key(self, request: TTSRequest) -> str:
        """캐시 키 생성"""
        key_components = [
            request.text,
            request.voice_profile.voice_name,
            str(request.voice_profile.pitch),
            str(request.voice_profile.speed),
            str(request.voice_profile.volume),
            str(request.emotion_tone) if request.emotion_tone else "none"
        ]
        
        key_string = "|".join(key_components)
        return f"tts_{hash(key_string)}"
    
    def _is_cache_valid(self, result: TTSResult, max_age_hours: int = 24) -> bool:
        """캐시 유효성 확인 - 현재는 항상 True 반환 (개선 여지 있음)"""
        return True
    
    def _apply_emotional_adjustment(self, profile: VoiceProfile, 
                                 emotion_tone: Optional[EmotionalTone]) -> VoiceProfile:
        """감정 조절 적용"""
        if not emotion_tone:
            return profile
        
        adjustments = self.emotional_adjustments.get(emotion_tone, {})
        
        adjusted_profile = VoiceProfile(
            engine=profile.engine,
            voice_name=profile.voice_name,
            language=profile.language,
            gender=profile.gender,
            pitch=profile.pitch * adjustments.get("pitch_modifier", 1.0),
            speed=profile.speed * adjustments.get("speed_modifier", 1.0),
            volume=profile.volume * adjustments.get("volume_modifier", 1.0)
        )
        
        return adjusted_profile
    
    async def _synthesize_audio(self, text: str, profile: VoiceProfile) -> Tuple[bytes, float]:
        """실제 음성 합성 (엔진별 구현)"""
        # 현재는 시뮬레이션 - 실제 TTS 엔진 연동 필요
        await asyncio.sleep(0.5)  # 합성 시간 시뮬레이션
        
        # 텍스트 길이 기반 지속 시간 계산
        duration = len(text) * 0.1  # 대략적인 계산
        
        # 더미 오디오 데이터 (실제로는 TTS 엔진 결과)
        dummy_audio = b"dummy_audio_data"
        
        logger.debug(f"Audio synthesized: {len(text)} chars, {duration:.2f}s duration")
        return dummy_audio, duration
    
    async def _generate_lipsync_data(self, text: str, duration: float, 
                                   profile: VoiceProfile) -> LipSyncData:
        """립싱크 데이터 생성"""
        # 텍스트 음성학적 분석 (간단한 구현)
        phonemes = self._analyze_phonemes(text, duration)
        mouth_shapes = self._generate_mouth_shapes(phonemes)
        
        return LipSyncData(
            phonemes=phonemes,
            mouth_shapes=mouth_shapes,
            duration=duration
        )
    
    def _analyze_phonemes(self, text: str, duration: float) -> List[Tuple[float, str, float]]:
        """음성학적 분석 (간단한 버전)"""
        phonemes = []
        
        # 간단한 음성 분석 - 글자 단위로 처리
        chars = list(text.replace(" ", ""))
        if not chars:
            return phonemes
        
        char_duration = duration / len(chars)
        current_time = 0.0
        
        for char in chars:
            # 한국어 모음 추출
            if self._is_korean_vowel(char):
                phoneme = self._extract_korean_vowel(char)
            elif char.lower() in self.phoneme_mapping:
                phoneme = char.lower()
            else:
                phoneme = 'silence'
            
            phonemes.append((current_time, phoneme, char_duration))
            current_time += char_duration
        
        return phonemes
    
    def _generate_mouth_shapes(self, phonemes: List[Tuple[float, str, float]]) -> List[Tuple[float, Dict[str, float]]]:
        """입 모양 생성"""
        mouth_shapes = []
        
        for timestamp, phoneme, duration in phonemes:
            if phoneme in self.phoneme_mapping:
                mouth_params = self.phoneme_mapping[phoneme].copy()
            else:
                mouth_params = self.phoneme_mapping['silence'].copy()
            
            mouth_shapes.append((timestamp, mouth_params))
        
        return mouth_shapes
    
    async def _stream_lipsync_events(self, lip_sync: LipSyncData, 
                                   session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """립싱크 이벤트 스트리밍"""
        for timestamp, mouth_params in lip_sync.mouth_shapes:
            # 실제 시간에 맞춰 대기
            await asyncio.sleep(0.05)  # 50ms 간격으로 업데이트
            
            yield {
                "type": "lipsync_update",
                "data": {
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "mouth_parameters": mouth_params
                }
            }
    
    def _is_korean_vowel(self, char: str) -> bool:
        """한국어 모음 확인"""
        korean_vowels = ['ㅏ', 'ㅓ', 'ㅗ', 'ㅜ', 'ㅡ', 'ㅣ', 'ㅐ', 'ㅔ', 'ㅑ', 'ㅕ', 'ㅛ', 'ㅠ']
        # 한글 글자에서 모음 추출하는 로직 필요 (복잡하므로 간단하게 처리)
        return any(vowel in char for vowel in korean_vowels)
    
    def _extract_korean_vowel(self, char: str) -> str:
        """한국어 모음 추출 (간단한 버전)"""
        # 실제로는 유니코드 분해 필요
        vowel_map = {
            '아': 'ㅏ', '어': 'ㅓ', '오': 'ㅗ', '우': 'ㅜ', '으': 'ㅡ', '이': 'ㅣ',
            '에': 'ㅔ', '애': 'ㅐ', '야': 'ㅑ', '여': 'ㅕ', '요': 'ㅛ', '유': 'ㅠ'
        }
        
        for syllable, vowel in vowel_map.items():
            if syllable in char:
                return vowel
        
        return 'ㅏ'  # 기본값
    
    def _cleanup_cache(self):
        """캐시 정리"""
        if len(self.audio_cache) > self.cache_max_size:
            # 가장 오래된 항목 제거 (간단한 LRU)
            oldest_key = min(self.audio_cache.keys())
            del self.audio_cache[oldest_key]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 (Enhanced with new TTS system info)"""
        # Get stats from new system
        new_system_stats = self.live2d_tts_manager.get_tts_statistics()
        
        return {
            # Legacy stats
            "cache_size": len(self.audio_cache),
            "cache_max_size": self.cache_max_size,
            "cache_usage_percent": (len(self.audio_cache) / self.cache_max_size) * 100,
            "available_voices": len(self.voice_profiles),
            "supported_emotions": len(self.emotional_adjustments),
            
            # New system stats
            "new_system": {
                "providers": new_system_stats["providers"],
                "total_providers": new_system_stats["total_providers"],
                "active_sessions": new_system_stats["active_sessions"],
                "factory_info": new_system_stats["factory_info"]
            }
        }
    
    def get_available_tts_providers(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """Get available TTS providers for user"""
        return self.live2d_tts_manager.get_available_providers_for_user(user_id)
    
    def update_user_tts_preferences(self, user_id: str, **preferences) -> Dict[str, Any]:
        """Update user TTS preferences"""
        return self.live2d_tts_manager.update_user_tts_settings(user_id, **preferences)
    
    def configure_tts_provider(self, provider_id: str, api_key: str, api_url: Optional[str] = None) -> bool:
        """Configure TTS provider API credentials"""
        try:
            self.live2d_tts_manager.config_manager.configure_provider_api(
                provider_id, api_key, api_url
            )
            return True
        except Exception as e:
            logger.error(f"Failed to configure provider {provider_id}: {e}")
            return False
    
    async def preload_common_phrases(self, phrases: List[str], 
                                   voice_profile_key: str = "ko_female_default") -> Dict[str, bool]:
        """자주 사용되는 문구 사전 로딩"""
        results = {}
        voice_profile = self.voice_profiles[voice_profile_key]
        
        for phrase in phrases:
            try:
                request = TTSRequest(
                    text=phrase,
                    voice_profile=voice_profile,
                    enable_lipsync=True
                )
                
                await self.synthesize_speech(request)
                results[phrase] = True
                
            except Exception as e:
                logger.error(f"Failed to preload phrase '{phrase}': {e}")
                results[phrase] = False
        
        return results


# 싱글톤 인스턴스
tts_service = TTSIntegrationService()
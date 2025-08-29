"""
Live2D TTS Integration Manager

Unified manager for TTS generation with Live2D animation synchronization.
Implements multi-provider support, fallback chains, and real-time Live2D integration.
Enhanced with Phase 8.2-8.6 components: lip-sync, emotion processing, audio enhancement.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json

from .tts_interface import (
    TTSRequest, TTSResult, EmotionType, LipSyncData,
    TTSProviderError, TTSProviderUnavailableError
)
from .tts_factory import TTSProviderFactory, tts_factory
from .tts_config_manager import TTSConfigManager, tts_config_manager
from .emotion_voice_processor import EmotionVoiceProcessor
from ..audio.lipsync_analyzer import LipSyncAnalyzer
from ..audio.audio_enhancer import AudioEnhancer, AudioEnhancementConfig, EnhancementLevel
import librosa

logger = logging.getLogger(__name__)


@dataclass
class Live2DTTSRequest:
    """Extended TTS request with Live2D specific parameters"""
    text: str
    user_id: str
    session_id: Optional[str] = None
    language: str = "ko-KR"
    voice: Optional[str] = None
    emotion: Optional[EmotionType] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    enable_lipsync: bool = True
    provider_override: Optional[str] = None
    
    # Live2D specific
    enable_expressions: bool = True
    enable_motions: bool = True
    expression_intensity: float = 0.8
    motion_blend_duration: float = 0.5
    
    def to_tts_request(self) -> TTSRequest:
        """Convert to basic TTSRequest"""
        return TTSRequest(
            text=self.text,
            language=self.language,
            voice=self.voice,
            emotion=self.emotion,
            speed=self.speed,
            pitch=self.pitch,
            volume=self.volume,
            enable_lipsync=self.enable_lipsync,
            user_id=self.user_id,
            session_id=self.session_id,
            provider_override=self.provider_override,
            additional_params=None
        )


@dataclass
class Live2DTTSResult:
    """TTS result with Live2D integration data"""
    tts_result: TTSResult
    live2d_commands: List[Dict[str, Any]]
    expression_timeline: List[Tuple[float, str, float]]  # (timestamp, expression, intensity)
    motion_timeline: List[Tuple[float, str]]  # (timestamp, motion_name)
    synchronization_events: List[Dict[str, Any]]
    total_duration: float
    provider_info: Dict[str, Any]


class EmotionAnalyzer:
    """Emotion analysis for TTS parameter adjustment"""
    
    def __init__(self):
        self.emotion_keywords = {
            EmotionType.HAPPY: ["기쁜", "행복", "좋은", "축하", "웃음", "즐거운"],
            EmotionType.SAD: ["슬픈", "우울", "안타까운", "눈물", "아픈", "힘든"],
            EmotionType.EXCITED: ["흥미진진", "신나는", "놀라운", "와", "대박", "멋진"],
            EmotionType.CALM: ["평온한", "차분한", "고요한", "안정", "편안한"],
            EmotionType.MYSTICAL: ["신비로운", "마법", "운명", "신성한", "불가사의"],
            EmotionType.WORRIED: ["걱정", "불안", "염려", "근심", "고민"],
            EmotionType.PLAYFUL: ["장난", "재미있는", "귀여운", "활발한", "발랄"]
        }
    
    def analyze_emotion_from_text(self, text: str) -> EmotionType:
        """Analyze emotion from text content"""
        text_lower = text.lower()
        
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        return EmotionType.NEUTRAL
    
    def get_emotion_adjustments(self, emotion: EmotionType) -> Dict[str, float]:
        """Get TTS parameter adjustments for emotion"""
        adjustments = {
            EmotionType.HAPPY: {"pitch_mod": 1.1, "speed_mod": 1.05, "volume_mod": 1.0},
            EmotionType.SAD: {"pitch_mod": 0.9, "speed_mod": 0.9, "volume_mod": 0.8},
            EmotionType.EXCITED: {"pitch_mod": 1.2, "speed_mod": 1.1, "volume_mod": 1.05},
            EmotionType.CALM: {"pitch_mod": 0.95, "speed_mod": 0.9, "volume_mod": 0.85},
            EmotionType.MYSTICAL: {"pitch_mod": 0.85, "speed_mod": 0.85, "volume_mod": 0.9},
            EmotionType.WORRIED: {"pitch_mod": 1.05, "speed_mod": 0.95, "volume_mod": 0.8},
            EmotionType.PLAYFUL: {"pitch_mod": 1.15, "speed_mod": 1.05, "volume_mod": 0.95},
            EmotionType.NEUTRAL: {"pitch_mod": 1.0, "speed_mod": 1.0, "volume_mod": 1.0}
        }
        
        return adjustments.get(emotion, adjustments[EmotionType.NEUTRAL])


class Live2DAnimationPlanner:
    """Plans Live2D animations based on TTS content and emotions"""
    
    def __init__(self):
        self.expression_mappings = {
            EmotionType.HAPPY: "joy",
            EmotionType.SAD: "concern", 
            EmotionType.EXCITED: "surprise",
            EmotionType.CALM: "neutral",
            EmotionType.MYSTICAL: "mystical",
            EmotionType.WORRIED: "concern",
            EmotionType.PLAYFUL: "playful",
            EmotionType.NEUTRAL: "neutral"
        }
        
        self.motion_mappings = {
            EmotionType.HAPPY: "greeting",
            EmotionType.MYSTICAL: "crystal_gaze",
            EmotionType.EXCITED: "blessing",
            EmotionType.WORRIED: "thinking_pose",
            EmotionType.CALM: "special_reading"
        }
    
    def plan_expressions(self, emotion: EmotionType, duration: float, 
                        intensity: float = 0.8) -> List[Tuple[float, str, float]]:
        """Plan expression changes during TTS"""
        expression_timeline = []
        
        # Main expression for the emotion
        main_expression = self.expression_mappings.get(emotion, "neutral")
        
        # Start with main expression
        expression_timeline.append((0.0, main_expression, intensity))
        
        # Add micro-expressions for longer content
        if duration > 3.0:
            # Add a subtle variation in the middle
            mid_time = duration * 0.5
            variation_intensity = intensity * 0.6
            expression_timeline.append((mid_time, main_expression, variation_intensity))
        
        # Return to neutral at the end (optional)
        if duration > 2.0:
            end_time = duration - 0.5
            expression_timeline.append((end_time, "neutral", 0.3))
        
        return expression_timeline
    
    def plan_motions(self, emotion: EmotionType, text: str, 
                    duration: float) -> List[Tuple[float, str]]:
        """Plan motion triggers during TTS"""
        motion_timeline = []
        
        # Trigger motion at the beginning for certain emotions
        if emotion in self.motion_mappings:
            motion_name = self.motion_mappings[emotion]
            motion_timeline.append((0.0, motion_name))
        
        # Add context-based motions
        if "카드" in text or "타로" in text:
            motion_timeline.append((duration * 0.2, "card_draw"))
        
        if "운세" in text or "점" in text:
            motion_timeline.append((duration * 0.3, "crystal_gaze"))
        
        return motion_timeline
    
    def generate_live2d_commands(self, expressions: List[Tuple[float, str, float]], 
                                motions: List[Tuple[float, str]],
                                lipsync_data: Optional[LipSyncData]) -> List[Dict[str, Any]]:
        """Generate Live2D command sequence"""
        commands = []
        
        # Expression commands
        for timestamp, expression, intensity in expressions:
            commands.append({
                "type": "expression",
                "timestamp": timestamp,
                "data": {
                    "expression": expression,
                    "intensity": intensity,
                    "blend_duration": 0.5
                }
            })
        
        # Motion commands  
        for timestamp, motion in motions:
            commands.append({
                "type": "motion",
                "timestamp": timestamp,
                "data": {
                    "motion": motion,
                    "blend_duration": 0.3,
                    "priority": "normal"
                }
            })
        
        # Lip sync commands
        if lipsync_data:
            for timestamp, mouth_params in lipsync_data.mouth_shapes:
                commands.append({
                    "type": "lipsync",
                    "timestamp": timestamp,
                    "data": {
                        "mouth_parameters": mouth_params,
                        "duration": 0.05  # 50ms per update
                    }
                })
        
        # Sort commands by timestamp
        commands.sort(key=lambda x: x["timestamp"])
        return commands


class Live2DTTSManager:
    """
    Main Live2D TTS Integration Manager
    
    Handles multi-provider TTS generation with Live2D synchronization,
    fallback chains, and real-time streaming to frontend.
    """
    
    def __init__(self, 
                 tts_factory: TTSProviderFactory = None,
                 config_manager: TTSConfigManager = None):
        
        # Import here to avoid circular imports
        from .tts_factory import tts_factory as factory_instance
        from .tts_config_manager import tts_config_manager as config_instance
        
        self.tts_factory = tts_factory or factory_instance
        self.config_manager = config_manager or config_instance
        
        # Legacy analyzers (kept for compatibility)
        self.emotion_analyzer = EmotionAnalyzer()
        self.animation_planner = Live2DAnimationPlanner()
        
        # Enhanced Phase 8.2-8.6 components
        self.emotion_processor = EmotionVoiceProcessor()
        self.lipsync_analyzer = LipSyncAnalyzer(frame_rate=30.0)
        self.audio_enhancer = AudioEnhancer(AudioEnhancementConfig())
        
        # Request cache for optimization
        self._request_cache: Dict[str, Live2DTTSResult] = {}
        self._cache_ttl = timedelta(hours=1)
        
        # Active sessions tracking
        self._active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Live2D TTS Manager initialized with enhanced Phase 8.2-8.6 components")
    
    async def generate_speech_with_animation(self, 
                                           request: Live2DTTSRequest) -> Live2DTTSResult:
        """
        Generate TTS with Live2D animation synchronization.
        Main entry point following todo specifications.
        """
        start_time = time.time()
        
        try:
            # 1. Enhanced emotion analysis using Phase 8.3 processor
            if not request.emotion:
                emotion_analysis, emotion_params = await self.emotion_processor.process_text_for_emotion(
                    request.text
                )
                request.emotion = emotion_analysis.primary_emotion
                # Enhanced emotion detected
            else:
                # Still run emotion analysis for parameter adjustments
                emotion_analysis, emotion_params = await self.emotion_processor.process_text_for_emotion(
                    request.text
                )
            
            # 2. Apply emotion-based TTS parameter adjustments
            adjusted_request = await self._apply_enhanced_emotion_adjustments(request, emotion_analysis)
            
            # 3. Get optimal provider configuration
            provider_config = await self._get_provider_with_fallback(
                adjusted_request.user_id, 
                adjusted_request.language,
                adjusted_request.provider_override
            )
            
            if not provider_config:
                raise TTSProviderUnavailableError("No TTS providers available")
            
            # 4. Generate TTS audio with enhanced processing
            tts_result = await self._generate_enhanced_audio_with_fallback(
                adjusted_request.to_tts_request(), 
                provider_config,
                emotion_analysis
            )
            
            # 5. Enhanced Live2D animation planning using emotion processor hints
            expression_hints = self.emotion_processor.get_emotion_expression_hints(emotion_analysis)
            expressions = self._plan_enhanced_expressions(
                emotion_analysis, tts_result.duration, request.expression_intensity, expression_hints
            )
            
            motions = self.animation_planner.plan_motions(
                request.emotion, request.text, tts_result.duration
            )
            
            # 6. Generate Live2D command sequence with enhanced lip-sync
            live2d_commands = await self._generate_enhanced_live2d_commands(
                expressions, motions, tts_result.lip_sync_data, expression_hints
            )
            
            # 7. Create synchronization events for real-time streaming
            sync_events = self._generate_synchronization_events(
                tts_result, expressions, motions
            )
            
            # 8. Record usage statistics
            self.config_manager.record_provider_usage(
                tts_result.provider,
                True,  # success
                len(request.text),
                tts_result.duration,
                tts_result.generation_time
            )
            
            # 9. Build final result with numpy safety
            from ..utils import sanitize_for_json
            
            result = Live2DTTSResult(
                tts_result=tts_result,
                live2d_commands=sanitize_for_json(live2d_commands),
                expression_timeline=sanitize_for_json(expressions),
                motion_timeline=sanitize_for_json(motions),
                synchronization_events=sanitize_for_json(sync_events),
                total_duration=float(tts_result.duration),
                provider_info=sanitize_for_json({
                    "provider_id": provider_config["provider_id"],
                    "provider_name": provider_config["config"].name,
                    "voice_used": tts_result.voice_used,
                    "fallback_used": provider_config.get("fallback_used", False),
                    "generation_time": float(tts_result.generation_time),
                    "cost_info": tts_result.cost_info
                })
            )
            
            # Live2D TTS completed
            return result
            
        except Exception as e:
            # Record failure
            if hasattr(self, '_last_provider_attempt'):
                self.config_manager.record_provider_usage(
                    self._last_provider_attempt, False, len(request.text), 0.0, 0.0
                )
            
            logger.error(f"Live2D TTS generation failed: {e}")
            raise
    
    async def _get_provider_with_fallback(self, user_id: str, language: str,
                                        provider_override: Optional[str]) -> Optional[Dict[str, Any]]:
        """Get provider configuration with fallback support"""
        
        # Try user override first
        if provider_override:
            try:
                provider = await self.tts_factory.create_provider(provider_override)
                if await provider.check_availability():
                    config = self.tts_factory.get_provider_config(provider_override)
                    if config and config.supports_language(language):
                        return {
                            "provider_id": provider_override,
                            "config": config,
                            "provider_instance": provider,
                            "fallback_used": False
                        }
            except Exception as e:
                logger.warning(f"Provider override {provider_override} failed: {e}")
        
        # Use config manager to get optimal provider
        optimal_config = await self.config_manager.get_optimal_provider(user_id, language)
        if optimal_config:
            try:
                provider = await self.tts_factory.create_provider(optimal_config["provider_id"])
                optimal_config["provider_instance"] = provider
                optimal_config["fallback_used"] = bool(provider_override)
                return optimal_config
            except Exception as e:
                logger.warning(f"Optimal provider {optimal_config['provider_id']} failed: {e}")
        
        # Fallback to any available provider
        available_providers = await self.tts_factory.get_available_providers(language)
        for provider_id in available_providers:
            try:
                provider = await self.tts_factory.create_provider(provider_id)
                config = self.tts_factory.get_provider_config(provider_id)
                return {
                    "provider_id": provider_id,
                    "config": config,
                    "provider_instance": provider,
                    "fallback_used": True
                }
            except Exception as e:
                logger.warning(f"Fallback provider {provider_id} failed: {e}")
                continue
        
        return None
    
    def _apply_emotion_adjustments(self, request: Live2DTTSRequest, 
                                 adjustments: Dict[str, float]) -> Live2DTTSRequest:
        """Apply emotion-based parameter adjustments"""
        adjusted_request = Live2DTTSRequest(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id,
            language=request.language,
            voice=request.voice,
            emotion=request.emotion,
            speed=request.speed * adjustments.get("speed_mod", 1.0),
            pitch=request.pitch * adjustments.get("pitch_mod", 1.0),
            volume=request.volume * adjustments.get("volume_mod", 1.0),
            enable_lipsync=request.enable_lipsync,
            provider_override=request.provider_override,
            enable_expressions=request.enable_expressions,
            enable_motions=request.enable_motions,
            expression_intensity=request.expression_intensity,
            motion_blend_duration=request.motion_blend_duration
        )
        
        return adjusted_request
    
    async def _apply_enhanced_emotion_adjustments(self, request: Live2DTTSRequest,
                                                emotion_analysis) -> Live2DTTSRequest:
        """Apply enhanced emotion-based parameter adjustments using Phase 8.3 processor"""
        # Create emotion-aware TTS request
        base_tts_request = request.to_tts_request()
        enhanced_request, _ = self.emotion_processor.create_emotion_aware_tts_request(
            request.text, base_tts_request
        )
        
        # Update Live2D request with enhanced parameters
        adjusted_request = Live2DTTSRequest(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id,
            language=request.language,
            voice=request.voice,
            emotion=enhanced_request.emotion,
            speed=enhanced_request.speed,
            pitch=enhanced_request.pitch,
            volume=enhanced_request.volume,
            enable_lipsync=request.enable_lipsync,
            provider_override=request.provider_override,
            enable_expressions=request.enable_expressions,
            enable_motions=request.enable_motions,
            expression_intensity=request.expression_intensity * (emotion_analysis.intensity + 0.5),
            motion_blend_duration=request.motion_blend_duration
        )
        
        return adjusted_request
    
    async def _generate_enhanced_audio_with_fallback(self, request: TTSRequest, 
                                                   provider_config: Dict[str, Any],
                                                   emotion_analysis) -> TTSResult:
        """Generate audio with enhanced processing and automatic fallback"""
        provider_instance = provider_config["provider_instance"]
        self._last_provider_attempt = provider_config["provider_id"]
        
        try:
            # Generate audio using provider
            tts_result = await provider_instance.async_generate_audio(request)
            
            # Phase 8.5: Apply audio enhancement for lip-sync optimization
            if request.enable_lipsync and tts_result.audio_data:
                try:
                    enhanced_audio = self.audio_enhancer.enhance_for_lipsync(
                        tts_result.audio_data,
                        audio_format=tts_result.audio_format,
                        enhancement_level=EnhancementLevel.MODERATE
                    )
                    
                    # Update TTS result with enhanced audio
                    tts_result.audio_data = enhanced_audio
                    # Audio enhanced for lip-sync optimization
                except Exception as enhancement_error:
                    logger.warning(f"Audio enhancement failed, using original: {enhancement_error}")
            
            # Phase 8.2: Generate simple open/close lip-sync (no complex vowel analysis)
            if request.enable_lipsync and tts_result.audio_data:
                try:
                    # Use accurate audio analysis instead of unreliable TTS duration
                    tts_result.lip_sync_data = self._create_basic_lipsync_data_with_audio_analysis(
                        request.text, tts_result.audio_data, tts_result.audio_format, tts_result.duration)
                except Exception as lipsync_error:
                    logger.warning(f"Lip-sync generation failed: {lipsync_error}")
                    # Create basic lip-sync fallback with original method
                    try:
                        tts_result.lip_sync_data = self._create_basic_lipsync_data(request.text, tts_result.duration)
                    except Exception:
                        tts_result.lip_sync_data = None
            else:
                # Lip-sync disabled or no audio data
                pass
            
            return tts_result
            
        except Exception as e:
            logger.warning(f"Primary provider {provider_config['provider_id']} failed: {e}")
            
            # Try fallback providers
            fallback_chain = self.tts_factory.get_fallback_chain(request.language)
            
            for fallback_provider_id in fallback_chain:
                if fallback_provider_id == provider_config["provider_id"]:
                    continue  # Skip the one that already failed
                
                try:
                    fallback_provider = await self.tts_factory.create_provider(fallback_provider_id)
                    if await fallback_provider.check_availability():
                        self._last_provider_attempt = fallback_provider_id
                        
                        # Generate with fallback provider
                        result = await fallback_provider.async_generate_audio(request)
                        
                        # Apply same enhancements to fallback result
                        if request.enable_lipsync and result.audio_data:
                            try:
                                enhanced_audio = self.audio_enhancer.enhance_for_lipsync(
                                    result.audio_data,
                                    audio_format=result.audio_format,
                                    enhancement_level=EnhancementLevel.LIGHT  # Lighter enhancement for fallback
                                )
                                result.audio_data = enhanced_audio
                                
                                enhanced_lipsync = await self.lipsync_analyzer.analyze_audio_data(
                                    result.audio_data, result.audio_format
                                )
                                result.lip_sync_data = self._convert_lipsync_data_format(enhanced_lipsync)
                                
                            except Exception as fallback_enhancement_error:
                                logger.warning(f"Fallback enhancement failed: {fallback_enhancement_error}")
                        
                        logger.info(f"Fallback to provider {fallback_provider_id} succeeded")
                        return result
                        
                except Exception as fallback_error:
                    logger.warning(f"Fallback provider {fallback_provider_id} failed: {fallback_error}")
                    continue
            
            # All providers failed
            raise TTSProviderError("All TTS providers failed")
    
    def _generate_synchronization_events(self, tts_result: TTSResult,
                                       expressions: List[Tuple[float, str, float]],
                                       motions: List[Tuple[float, str]]) -> List[Dict[str, Any]]:
        """Generate events for real-time synchronization"""
        events = []
        
        # Audio start event
        events.append({
            "type": "audio_start",
            "timestamp": 0.0,
            "data": {
                "duration": tts_result.duration,
                "provider": tts_result.provider,
                "voice": tts_result.voice_used
            }
        })
        
        # Expression events
        for timestamp, expression, intensity in expressions:
            events.append({
                "type": "expression_change",
                "timestamp": timestamp,
                "data": {
                    "expression": expression,
                    "intensity": intensity
                }
            })
        
        # Motion events
        for timestamp, motion in motions:
            events.append({
                "type": "motion_trigger",
                "timestamp": timestamp,
                "data": {
                    "motion": motion
                }
            })
        
        # Audio end event
        events.append({
            "type": "audio_complete",
            "timestamp": tts_result.duration,
            "data": {
                "total_duration": tts_result.duration
            }
        })
        
        return sorted(events, key=lambda x: x["timestamp"])
    
    def _convert_lipsync_data_format(self, lipsync_data) -> LipSyncData:
        """Convert enhanced lip-sync data to TTSInterface format"""
        from ..utils import sanitize_for_json
        
        logger.info(f"[립싱크 변환] 시작: 입력 데이터 타입 = {type(lipsync_data)}")
        
        try:
            # Convert Phase 8.2 LipSyncData to TTSInterface LipSyncData
            mouth_shapes = []
            
            if not hasattr(lipsync_data, 'frames'):
                logger.error(f"[립싱크 변환] 프레임 속성이 없음: {dir(lipsync_data)}")
                return None
                
            logger.info(f"[립싱크 변환] 프레임 수: {len(lipsync_data.frames)}")
            
            for i, frame in enumerate(lipsync_data.frames):
                try:
                    # timestamp를 float로, mouth_params의 numpy 타입들을 안전하게 변환
                    timestamp = float(frame.timestamp)
                    params = sanitize_for_json(frame.mouth_params)
                    
                    # 파라미터 검증
                    if 'ParamMouthOpenY' not in params:
                        logger.warning(f"[립싱크 변환] 프레임 {i}: ParamMouthOpenY 없음, 기본값 설정")
                        params['ParamMouthOpenY'] = 0.5
                    
                    mouth_shapes.append((timestamp, params))
                    
                    if i < 3:  # 처음 3개 프레임 로그
                        logger.info(f"[립싱크 변환] 프레임 {i}: 시간={timestamp:.3f}s, 파라미터={params}")
                        
                except Exception as frame_error:
                    logger.error(f"[립싱크 변환] 프레임 {i} 처리 실패: {frame_error}")
                    continue
            
            # Extract phonemes if available, otherwise use empty list
            phonemes = []
            if hasattr(lipsync_data, 'phonemes') and lipsync_data.phonemes:
                phonemes = sanitize_for_json(lipsync_data.phonemes)
                logger.info(f"[립싱크 변환] 포네임 수: {len(phonemes)}")
            else:
                logger.info(f"[립싱크 변환] 포네임 없음")
            
            result = LipSyncData(
                phonemes=phonemes,
                mouth_shapes=mouth_shapes,
                duration=float(lipsync_data.duration),
                frame_rate=float(lipsync_data.frame_rate)
            )
            
            logger.info(f"[립싱크 변환] 완료: {len(mouth_shapes)} mouth_shapes, 지속시간={result.duration}s")
            return result
            
        except Exception as convert_error:
            logger.error(f"[립싱크 변환] 전체 변환 실패: {convert_error}")
            logger.exception("[립싱크 변환] 전체 스택 트레이스:")
            return None
    
    def _get_accurate_audio_duration(self, audio_data: bytes, audio_format: str = "mp3") -> float:
        """librosa를 사용하여 오디오 바이트에서 정확한 duration 추출"""
        import io
        
        try:
            logger.info(f"🔍 [정확한 Duration] 오디오 분석 시작 - 형식: {audio_format}, 데이터 크기: {len(audio_data)} bytes")
            
            # 메모리에서 오디오 로드
            audio_buffer = io.BytesIO(audio_data)
            y, sr = librosa.load(audio_buffer, sr=None)  # 원본 샘플레이트 유지
            
            # 실제 오디오 길이 계산
            actual_duration = len(y) / sr
            
            logger.info(f"📊 [정확한 Duration] librosa 분석 결과:")
            logger.info(f"  - 샘플 수: {len(y):,}")
            logger.info(f"  - 샘플레이트: {sr:,} Hz")
            logger.info(f"  - 계산된 길이: {actual_duration:.6f}초")
            logger.info(f"✅ [정확한 Duration] 오디오 분석 완료")
            
            return actual_duration
            
        except Exception as e:
            logger.error(f"❌ [정확한 Duration] 오디오 분석 실패: {e}")
            logger.exception("오디오 분석 스택 트레이스:")
            raise

    def _create_basic_lipsync_data_with_audio_analysis(self, text: str, audio_data: bytes, 
                                                     audio_format: str, tts_duration: float) -> LipSyncData:
        """정확한 오디오 분석을 통한 립싱크 데이터 생성"""
        
        logger.info(f"🎭 [립싱크 생성] 정확한 오디오 분석 기반 립싱크 데이터 생성 시작")
        logger.info(f"  - 텍스트: '{text}'")
        logger.info(f"  - TTS 제공 duration: {tts_duration:.6f}초")
        
        # 1. TTS duration 무시하고 실제 오디오에서 길이 추출
        actual_duration = self._get_accurate_audio_duration(audio_data, audio_format)
        
        # 2. Duration 비교 로그
        duration_diff = abs(actual_duration - tts_duration)
        duration_diff_percent = (duration_diff / max(actual_duration, 0.001)) * 100
        
        logger.info(f"⚖️ [Duration 비교]")
        logger.info(f"  - TTS 제공 길이: {tts_duration:.6f}초")
        logger.info(f"  - 실제 오디오 길이: {actual_duration:.6f}초")
        logger.info(f"  - 차이: {duration_diff:.6f}초 ({duration_diff_percent:.2f}%)")
        
        if duration_diff_percent > 5.0:
            logger.warning(f"⚠️ [Duration 불일치] {duration_diff_percent:.2f}% 차이로 부정확한 TTS duration 감지!")
        else:
            logger.info(f"✅ [Duration 일치] TTS duration이 비교적 정확함")
        
        # 3. 실제 길이 기반으로 프레임 생성
        frame_rate = 30.0
        frame_count = int(actual_duration * frame_rate)
        
        logger.info(f"🎬 [프레임 생성]")
        logger.info(f"  - 사용할 duration: {actual_duration:.6f}초")
        logger.info(f"  - 프레임 레이트: {frame_rate} fps")
        logger.info(f"  - 계산된 프레임 수: {frame_count}")
        logger.info(f"  - 예상 재생 시간: {frame_count / frame_rate:.6f}초")
        
        mouth_shapes = []
        
        # 단순한 입 열림/닫힘 패턴 (한글 모음 분석 없이)
        for i in range(frame_count):
            timestamp = i / frame_rate
            
            # 자연스러운 말하기 패턴 시뮬레이션
            import math
            # 자연스러운 말하기 주기로 입을 열었다 닫았다 반복
            base_frequency = 3.5  # 초당 3.5회 열림/닫힘 (자연스러운 말하기 속도)
            
            # 약간의 변화를 위한 주파수 변조 (3.0 ~ 4.0Hz 범위)
            frequency_variation = 0.5 * math.sin(timestamp * 0.7)  # 느린 변조
            actual_frequency = base_frequency + frequency_variation
            
            mouth_open_intensity = abs(math.sin(timestamp * actual_frequency * math.pi))
            
            # 기본 입 열림량 (0.3 ~ 0.8 범위)
            base_open = 0.3 + (mouth_open_intensity * 0.5)
            
            params = {
                'ParamMouthOpenY': base_open,
                'ParamMouthForm': 0.0,  # 중립 표정
                'ParamMouthOpenX': 0.2 + (mouth_open_intensity * 0.3)
            }
            
            mouth_shapes.append((timestamp, params))
            
            # 처음 5개와 마지막 5개 프레임 로그 출력
            if i < 5 or i >= frame_count - 5:
                logger.info(f"  📊 프레임 {i:3d}: 시간={timestamp:.3f}s, 입열림={base_open:.3f}")
        
        result = LipSyncData(
            phonemes=[],
            mouth_shapes=mouth_shapes,
            duration=actual_duration,  # 정확한 duration 사용
            frame_rate=frame_rate
        )
        
        logger.info(f"✅ [립싱크 생성 완료]")
        logger.info(f"  - 생성된 프레임: {len(mouth_shapes)}개")
        logger.info(f"  - 총 duration: {result.duration:.6f}초")
        logger.info(f"  - 프레임 레이트: {result.frame_rate} fps")
        logger.info(f"  - 예상 재생 시간: {len(mouth_shapes) / result.frame_rate:.6f}초")
        
        return result

    def _create_basic_lipsync_data(self, text: str, duration: float) -> LipSyncData:
        """Simple open/close mouth animation during TTS"""
        
        # 30fps로 프레임 생성
        frame_rate = 30.0
        frame_count = int(duration * frame_rate)
        
        mouth_shapes = []
        
        # 단순한 입 열림/닫힘 패턴 (한글 모음 분석 없이)
        for i in range(frame_count):
            timestamp = i / frame_rate
            
            # 자연스러운 말하기 패턴 시뮬레이션
            import math
            # 자연스러운 말하기 주기로 입을 열었다 닫았다 반복
            base_frequency = 3.5  # 초당 3.5회 열림/닫힘 (자연스러운 말하기 속도)
            
            # 약간의 변화를 위한 주파수 변조 (3.0 ~ 4.0Hz 범위)
            frequency_variation = 0.5 * math.sin(timestamp * 0.7)  # 느린 변조
            actual_frequency = base_frequency + frequency_variation
            
            mouth_open_intensity = abs(math.sin(timestamp * actual_frequency * math.pi))
            
            # 기본 입 열림량 (0.3 ~ 0.8 범위)
            base_open = 0.3 + (mouth_open_intensity * 0.5)
            
            params = {
                'ParamMouthOpenY': base_open,
                'ParamMouthForm': 0.0,  # 중립 표정
                'ParamMouthOpenX': 0.2 + (mouth_open_intensity * 0.3)
            }
            
            mouth_shapes.append((timestamp, params))
        
        return LipSyncData(
            phonemes=[],
            mouth_shapes=mouth_shapes,
            duration=duration,
            frame_rate=frame_rate
        )
    
    def _plan_enhanced_expressions(self, emotion_analysis, duration: float, 
                                 intensity: float, expression_hints: Dict[str, Any]) -> List[Tuple[float, str, float]]:
        """Plan expressions using enhanced emotion analysis"""
        expressions = []
        
        # Use emotion processor hints for more accurate expressions
        main_expression = expression_hints.get("expression", "neutral")
        suggested_motion = expression_hints.get("suggested_motion")
        
        # Start with main expression
        expressions.append((0.0, main_expression, intensity * emotion_analysis.intensity))
        
        # Add micro-expressions based on emotion confidence
        if duration > 2.0 and emotion_analysis.confidence > 0.7:
            mid_time = duration * 0.4
            variation_intensity = intensity * emotion_analysis.intensity * 0.7
            expressions.append((mid_time, main_expression, variation_intensity))
        
        # Add subtle variations for longer content
        if duration > 4.0:
            quarter_time = duration * 0.25
            three_quarter_time = duration * 0.75
            
            # Slight intensity variations
            expressions.append((quarter_time, main_expression, intensity * emotion_analysis.intensity * 0.8))
            expressions.append((three_quarter_time, main_expression, intensity * emotion_analysis.intensity * 0.6))
        
        # Return to neutral at end for long content
        if duration > 3.0:
            end_time = duration - 0.5
            expressions.append((end_time, "neutral", 0.3))
        
        return expressions
    
    async def _generate_enhanced_live2d_commands(self, expressions: List[Tuple[float, str, float]], 
                                               motions: List[Tuple[float, str]],
                                               lipsync_data: Optional[LipSyncData],
                                               expression_hints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Live2D commands with enhanced integration"""
        commands = []
        
        # Expression commands with enhanced parameters
        for timestamp, expression, intensity in expressions:
            command = {
                "type": "expression",
                "timestamp": timestamp,
                "data": {
                    "expression": expression,
                    "intensity": intensity,
                    "blend_duration": 0.5
                }
            }
            
            # Add enhanced eye and brow parameters from emotion processor
            if "eye_params" in expression_hints:
                command["data"]["eye_parameters"] = expression_hints["eye_params"]
            if "brow_params" in expression_hints:
                command["data"]["brow_parameters"] = expression_hints["brow_params"]
                
            commands.append(command)
        
        # Motion commands with context awareness
        for timestamp, motion in motions:
            commands.append({
                "type": "motion",
                "timestamp": timestamp,
                "data": {
                    "motion": motion,
                    "blend_duration": 0.3,
                    "priority": "normal",
                    "emotion_context": expression_hints.get("expression", "neutral")
                }
            })
        
        # Enhanced lip-sync commands with Phase 8.2 analysis
        if lipsync_data and hasattr(lipsync_data, 'mouth_shapes'):
            for timestamp, mouth_params in lipsync_data.mouth_shapes:
                commands.append({
                    "type": "lipsync",
                    "timestamp": timestamp,
                    "data": {
                        "mouth_parameters": mouth_params,
                        "duration": 1.0 / 30.0,  # 30 FPS
                        "interpolation": "smooth",
                        "priority": "high"  # Lip-sync has high priority
                    }
                })
        
        # Add breath animation for natural feel
        if lipsync_data and lipsync_data.duration > 2.0:
            breath_interval = 3.0  # Every 3 seconds
            current_time = breath_interval
            
            while current_time < lipsync_data.duration - 1.0:
                commands.append({
                    "type": "breath",
                    "timestamp": current_time,
                    "data": {
                        "intensity": 0.3,
                        "duration": 1.0
                    }
                })
                current_time += breath_interval
        
        # Sort commands by timestamp for proper execution order
        commands.sort(key=lambda x: x["timestamp"])
        return commands
    
    async def stream_live2d_tts(self, request: Live2DTTSRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream TTS with Live2D synchronization events"""
        try:
            # Generate complete result first
            result = await self.generate_speech_with_animation(request)
            
            # Start streaming event
            yield {
                "type": "tts_stream_start",
                "data": {
                    "session_id": request.session_id,
                    "total_duration": result.total_duration,
                    "provider": result.provider_info["provider_id"],
                    "audio_data": result.tts_result.audio_data,
                    "audio_format": result.tts_result.audio_format
                }
            }
            
            # Stream synchronization events in real-time
            start_time = asyncio.get_event_loop().time()
            
            for event in result.synchronization_events:
                # Wait until event timestamp
                event_time = start_time + event["timestamp"]
                current_time = asyncio.get_event_loop().time()
                
                if event_time > current_time:
                    await asyncio.sleep(event_time - current_time)
                
                # Send event
                yield {
                    "type": "live2d_sync",
                    "data": {
                        "session_id": request.session_id,
                        "event": event,
                        "timestamp": event["timestamp"]
                    }
                }
            
            # Stream completion
            yield {
                "type": "tts_stream_complete",
                "data": {
                    "session_id": request.session_id,
                    "provider_info": result.provider_info
                }
            }
            
        except Exception as e:
            yield {
                "type": "tts_stream_error",
                "data": {
                    "session_id": request.session_id,
                    "error": str(e)
                }
            }
    
    def get_available_providers_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get available TTS options for user"""
        return self.config_manager.get_user_tts_options(user_id)
    
    def update_user_tts_settings(self, user_id: str, **settings) -> Dict[str, Any]:
        """Update user TTS preferences"""
        prefs = self.config_manager.update_user_preferences(user_id, **settings)
        return {
            "user_id": user_id,
            "preferences": prefs.to_dict(),
            "updated": True
        }
    
    def get_tts_statistics(self) -> Dict[str, Any]:
        """Get TTS system statistics"""
        provider_stats = self.config_manager.get_provider_statistics()
        
        return {
            "providers": provider_stats,
            "cache_size": len(self._request_cache),
            "active_sessions": len(self._active_sessions),
            "total_providers": len(self.tts_factory._provider_configs),
            "factory_info": self.tts_factory.get_supported_providers()
        }


# Global Live2D TTS Manager instance
live2d_tts_manager = Live2DTTSManager()
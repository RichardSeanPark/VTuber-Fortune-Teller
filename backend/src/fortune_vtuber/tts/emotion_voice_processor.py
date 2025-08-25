"""
Emotion-based Voice Expression System

Processes text for emotion detection and applies emotion-based TTS parameter
adjustments for more expressive voice synthesis. Based on todo specifications Phase 8.3.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import asyncio

from .tts_interface import EmotionType, TTSRequest

logger = logging.getLogger(__name__)


class EmotionIntensity(Enum):
    """Emotion intensity levels"""
    SUBTLE = 0.3
    MODERATE = 0.6
    STRONG = 0.9
    EXTREME = 1.2


@dataclass
class EmotionAnalysis:
    """Result of emotion analysis"""
    primary_emotion: EmotionType
    intensity: float
    confidence: float
    emotion_scores: Dict[EmotionType, float]
    detected_keywords: List[str]
    context_indicators: List[str]


@dataclass
class VoiceModulation:
    """Voice parameter adjustments for emotions"""
    pitch_shift: float      # Pitch multiplier (0.5-2.0)
    speed_rate: float       # Speed multiplier (0.5-2.0)  
    volume_gain: float      # Volume adjustment (-1.0 to 1.0)
    tone_warmth: float      # Warmth adjustment (-1.0 to 1.0)
    breathiness: float      # Breathiness level (0.0-1.0)
    resonance: float        # Resonance adjustment (-1.0 to 1.0)


class KoreanEmotionDetector:
    """
    Korean-focused emotion detection from text content.
    Analyzes emotional indicators, context, and linguistic patterns.
    """
    
    def __init__(self):
        # Korean emotion keyword patterns
        self.emotion_patterns = {
            EmotionType.HAPPY: {
                "keywords": [
                    "기쁜", "행복", "좋은", "축하", "웃음", "즐거운", "만족", 
                    "신난", "유쾌한", "밝은", "화사한", "반가운", "기대", "설레는"
                ],
                "phrases": [
                    "너무 좋", "정말 기", "와 대박", "축하드", "기쁘게", "행복하게",
                    "만족스", "즐겁게", "신나게"
                ],
                "particles": ["네요", "예요", "군요"],
                "punctuation": ["!", "♪", "♡", "💕", "😊", "😄"]
            },
            
            EmotionType.SAD: {
                "keywords": [
                    "슬픈", "우울", "안타까운", "눈물", "아픈", "힘든", "외로운",
                    "답답한", "무거운", "걱정", "불안", "서러운", "쓸쓸한"
                ],
                "phrases": [
                    "안타깝", "슬프게", "힘들게", "어려운", "걱정이", "불안해",
                    "우울하", "외롭"
                ],
                "particles": ["ㅠㅠ", "ㅜㅜ"],
                "punctuation": ["...", "ㅠ", "ㅜ", "😢", "😭", "💧"]
            },
            
            EmotionType.EXCITED: {
                "keywords": [
                    "흥미진진", "신나는", "놀라운", "와", "대박", "멋진", "환상적",
                    "굉장한", "최고", "쩔어", "미쳤다", "레전드", "개쩐다"
                ],
                "phrases": [
                    "정말 대박", "너무 멋", "굉장히", "엄청", "완전", "진짜 좋",
                    "미친 듯", "장난 아니"
                ],
                "particles": ["!!!", "!!", "ㅋㅋ", "ㅎㅎ"],
                "punctuation": ["!!!", "!!", "🔥", "⚡", "✨", "🎉"]
            },
            
            EmotionType.CALM: {
                "keywords": [
                    "평온한", "차분한", "고요한", "안정", "편안한", "여유로운",
                    "조용한", "부드러운", "온화한", "평화로운"
                ],
                "phrases": [
                    "차분히", "조용히", "편안히", "천천히", "여유롭게", "부드럽게"
                ],
                "particles": ["습니다", "합니다", "됩니다"],
                "punctuation": [".", "~", "😌", "🕯️", "🌙"]
            },
            
            EmotionType.MYSTICAL: {
                "keywords": [
                    "신비로운", "마법", "운명", "신성한", "불가사의", "영험한",
                    "초월적", "예언", "점성", "우주", "에너지", "기운", "오라"
                ],
                "phrases": [
                    "신비한", "마법적", "운명의", "우주의", "영적인", "신성한",
                    "초자연적", "신비주의"
                ],
                "particles": ["이시여", "이로다", "하리"],
                "punctuation": ["✨", "🌟", "🔮", "🌙", "⭐", "💫"]
            },
            
            EmotionType.WORRIED: {
                "keywords": [
                    "걱정", "불안", "염려", "근심", "고민", "초조한", "조바심",
                    "두려운", "겁나는", "무서운", "불확실한"
                ],
                "phrases": [
                    "걱정이", "불안해", "염려가", "고민이", "두려워", "무서워",
                    "확실하지", "애매한"
                ],
                "particles": ["어떻게", "혹시", "만약"],
                "punctuation": ["?", "...", "😰", "😟", "😥", "❓"]
            },
            
            EmotionType.PLAYFUL: {
                "keywords": [
                    "장난", "재미있는", "귀여운", "활발한", "발랄한", "유쾌한",
                    "익살", "개구진", "경쾌한", "톡톡한"
                ],
                "phrases": [
                    "재미있", "귀엽", "장난스", "발랄하", "경쾌한", "톡톡 튀는"
                ],
                "particles": ["ㅎㅎ", "헤헤", "호호", "키키"],
                "punctuation": ["ㅋㅋ", "ㅎㅎ", "😄", "😆", "🤭", "😉"]
            }
        }
        
        # Context multipliers for fortune telling
        self.fortune_context_multipliers = {
            "타로": {"mystical": 1.3, "calm": 1.2},
            "운세": {"mystical": 1.2, "worried": 1.1},
            "사주": {"mystical": 1.4, "calm": 1.3},
            "점": {"mystical": 1.2, "worried": 0.9},
            "카드": {"mystical": 1.1, "excited": 1.1},
            "미래": {"worried": 1.1, "excited": 1.0},
            "행운": {"happy": 1.2, "excited": 1.1},
            "주의": {"worried": 1.3, "calm": 1.1}
        }
    
    def analyze_emotion(self, text: str) -> EmotionAnalysis:
        """
        Analyze emotion from Korean text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            EmotionAnalysis: Detailed emotion analysis result
        """
        # Clean and prepare text
        cleaned_text = self._preprocess_text(text)
        
        # Calculate emotion scores
        emotion_scores = {}
        detected_keywords = []
        
        for emotion, patterns in self.emotion_patterns.items():
            score = 0.0
            keywords_found = []
            
            # Keyword matching
            for keyword in patterns["keywords"]:
                if keyword in cleaned_text:
                    score += 1.0
                    keywords_found.append(keyword)
            
            # Phrase matching (weighted higher)
            for phrase in patterns["phrases"]:
                if phrase in cleaned_text:
                    score += 1.5
                    keywords_found.append(phrase)
            
            # Particle and punctuation matching
            for particle in patterns["particles"]:
                if particle in cleaned_text:
                    score += 0.5
                    keywords_found.append(particle)
            
            for punct in patterns["punctuation"]:
                if punct in cleaned_text:
                    score += 0.3
                    keywords_found.append(punct)
            
            emotion_scores[emotion] = score
            if keywords_found:
                detected_keywords.extend(keywords_found)
        
        # Apply context multipliers
        emotion_scores = self._apply_context_multipliers(emotion_scores, cleaned_text)
        
        # Find primary emotion
        if not any(score > 0 for score in emotion_scores.values()):
            # No emotion detected, default to neutral
            primary_emotion = EmotionType.NEUTRAL
            intensity = 0.0
            confidence = 1.0
        else:
            primary_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
            raw_intensity = emotion_scores[primary_emotion]
            intensity = min(1.0, raw_intensity / 3.0)  # Normalize to 0-1
            
            # Calculate confidence based on score difference
            sorted_scores = sorted(emotion_scores.values(), reverse=True)
            if len(sorted_scores) > 1:
                confidence = (sorted_scores[0] - sorted_scores[1]) / (sorted_scores[0] + 1e-6)
            else:
                confidence = intensity
        
        # Detect context indicators
        context_indicators = self._detect_context_indicators(cleaned_text)
        
        return EmotionAnalysis(
            primary_emotion=primary_emotion,
            intensity=intensity,
            confidence=confidence,
            emotion_scores=emotion_scores,
            detected_keywords=detected_keywords,
            context_indicators=context_indicators
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Convert to lowercase for consistency
        cleaned = text.lower()
        
        # Normalize repeated characters
        cleaned = re.sub(r'([ㅋㅎ])\1{2,}', r'\1\1', cleaned)  # ㅋㅋㅋ -> ㅋㅋ
        cleaned = re.sub(r'([!?])\1{2,}', r'\1\1', cleaned)     # !!! -> !!
        
        return cleaned
    
    def _apply_context_multipliers(self, scores: Dict[EmotionType, float], 
                                 text: str) -> Dict[EmotionType, float]:
        """Apply context-specific multipliers for fortune telling"""
        modified_scores = scores.copy()
        
        for context_word, multipliers in self.fortune_context_multipliers.items():
            if context_word in text:
                for emotion_name, multiplier in multipliers.items():
                    # Find matching emotion type
                    for emotion_type in EmotionType:
                        if emotion_type.name.lower() == emotion_name:
                            if emotion_type in modified_scores:
                                modified_scores[emotion_type] *= multiplier
                            break
        
        return modified_scores
    
    def _detect_context_indicators(self, text: str) -> List[str]:
        """Detect contextual indicators that influence emotion"""
        indicators = []
        
        # Time-related contexts
        time_patterns = {
            "과거": "past_reference",
            "현재": "present_focus", 
            "미래": "future_concern",
            "오늘": "immediate",
            "내일": "near_future",
            "이번": "current_period"
        }
        
        for pattern, indicator in time_patterns.items():
            if pattern in text:
                indicators.append(indicator)
        
        # Question vs statement
        if "?" in text or any(q in text for q in ["어떻", "언제", "무엇", "왜", "어디"]):
            indicators.append("question_form")
        else:
            indicators.append("statement_form")
        
        return indicators


class EmotionVoiceProcessor:
    """
    Main emotion-based voice processing system.
    
    Combines emotion detection with TTS parameter adjustment for 
    expressive voice synthesis based on emotional content.
    """
    
    def __init__(self):
        self.emotion_detector = KoreanEmotionDetector()
        
        # Base voice modulation parameters by emotion
        self.emotion_modulations = {
            EmotionType.HAPPY: VoiceModulation(
                pitch_shift=1.15,     # Higher pitch for joy
                speed_rate=1.08,      # Slightly faster 
                volume_gain=0.1,      # Bit louder
                tone_warmth=0.3,      # Warmer tone
                breathiness=0.1,      # Light breathiness
                resonance=0.2         # More resonant
            ),
            
            EmotionType.SAD: VoiceModulation(
                pitch_shift=0.88,     # Lower pitch
                speed_rate=0.85,      # Slower pace
                volume_gain=-0.15,    # Quieter
                tone_warmth=-0.2,     # Cooler tone
                breathiness=0.3,      # More breathy
                resonance=-0.3        # Less resonant
            ),
            
            EmotionType.EXCITED: VoiceModulation(
                pitch_shift=1.25,     # Much higher pitch
                speed_rate=1.15,      # Faster pace
                volume_gain=0.2,      # Louder
                tone_warmth=0.4,      # Very warm
                breathiness=0.0,      # Clear, not breathy
                resonance=0.4         # Very resonant
            ),
            
            EmotionType.CALM: VoiceModulation(
                pitch_shift=0.95,     # Slightly lower pitch
                speed_rate=0.90,      # Slower, measured pace
                volume_gain=-0.05,    # Slightly softer
                tone_warmth=0.1,      # Gentle warmth
                breathiness=0.2,      # Gentle breathiness
                resonance=0.0         # Neutral resonance
            ),
            
            EmotionType.MYSTICAL: VoiceModulation(
                pitch_shift=0.85,     # Lower, mysterious pitch
                speed_rate=0.80,      # Slow, deliberate
                volume_gain=-0.1,     # Softer for mystery
                tone_warmth=-0.1,     # Cool, ethereal tone
                breathiness=0.4,      # Breathy, otherworldly
                resonance=-0.2        # Less resonant, ethereal
            ),
            
            EmotionType.WORRIED: VoiceModulation(
                pitch_shift=1.05,     # Slight tension in pitch
                speed_rate=0.95,      # Hesitant pace
                volume_gain=-0.08,    # Uncertain volume
                tone_warmth=-0.1,     # Cooler tone
                breathiness=0.2,      # Anxious breathiness
                resonance=-0.1        # Slight tension
            ),
            
            EmotionType.PLAYFUL: VoiceModulation(
                pitch_shift=1.18,     # Higher, animated pitch
                speed_rate=1.05,      # Bouncy pace
                volume_gain=0.05,     # Cheerful volume
                tone_warmth=0.25,     # Warm, friendly tone
                breathiness=0.05,     # Clear and bright
                resonance=0.15        # Pleasant resonance
            ),
            
            EmotionType.NEUTRAL: VoiceModulation(
                pitch_shift=1.0,      # No change
                speed_rate=1.0,       # Normal pace
                volume_gain=0.0,      # Normal volume
                tone_warmth=0.0,      # Neutral tone
                breathiness=0.1,      # Natural breathiness
                resonance=0.0         # Natural resonance
            )
        }
    
    async def process_text_for_emotion(self, text: str, base_params: Dict[str, Any] = None) -> Tuple[EmotionAnalysis, Dict[str, Any]]:
        """
        Process text for emotion and generate adjusted TTS parameters.
        
        Args:
            text: Input text to process
            base_params: Base TTS parameters to adjust
            
        Returns:
            Tuple[EmotionAnalysis, Dict[str, Any]]: Emotion analysis and adjusted parameters
        """
        # Analyze emotion
        emotion_analysis = self.emotion_detector.analyze_emotion(text)
        
        logger.info(f"Detected emotion: {emotion_analysis.primary_emotion.value} "
                   f"(intensity: {emotion_analysis.intensity:.2f}, "
                   f"confidence: {emotion_analysis.confidence:.2f})")
        
        # Get base modulation for detected emotion
        base_modulation = self.emotion_modulations[emotion_analysis.primary_emotion]
        
        # Scale modulation by intensity
        scaled_modulation = self._scale_modulation_by_intensity(
            base_modulation, emotion_analysis.intensity
        )
        
        # Apply modulation to TTS parameters
        adjusted_params = self._apply_voice_modulation(
            scaled_modulation, base_params or {}
        )
        
        return emotion_analysis, adjusted_params
    
    def _scale_modulation_by_intensity(self, modulation: VoiceModulation, 
                                     intensity: float) -> VoiceModulation:
        """Scale voice modulation by emotion intensity"""
        return VoiceModulation(
            pitch_shift=1.0 + (modulation.pitch_shift - 1.0) * intensity,
            speed_rate=1.0 + (modulation.speed_rate - 1.0) * intensity,
            volume_gain=modulation.volume_gain * intensity,
            tone_warmth=modulation.tone_warmth * intensity,
            breathiness=modulation.breathiness * intensity,
            resonance=modulation.resonance * intensity
        )
    
    def _apply_voice_modulation(self, modulation: VoiceModulation, 
                              base_params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply voice modulation to TTS parameters"""
        adjusted_params = base_params.copy()
        
        # Apply modulation to common TTS parameters
        param_mappings = {
            "pitch": ("pitch_shift", lambda x, mod: x * mod),
            "pitch_scale": ("pitch_shift", lambda x, mod: x * mod),
            "speed": ("speed_rate", lambda x, mod: x * mod),
            "rate": ("speed_rate", lambda x, mod: x * mod),
            "volume": ("volume_gain", lambda x, mod: x + mod),
            "volume_scale": ("volume_gain", lambda x, mod: x + mod),
        }
        
        for param_name, (mod_attr, apply_func) in param_mappings.items():
            if param_name in adjusted_params:
                mod_value = getattr(modulation, mod_attr)
                adjusted_params[param_name] = apply_func(adjusted_params[param_name], mod_value)
        
        # Add emotion-specific parameters for advanced TTS providers
        adjusted_params["emotion_pitch_shift"] = modulation.pitch_shift
        adjusted_params["emotion_speed_rate"] = modulation.speed_rate
        adjusted_params["emotion_volume_gain"] = modulation.volume_gain
        adjusted_params["emotion_tone_warmth"] = modulation.tone_warmth
        adjusted_params["emotion_breathiness"] = modulation.breathiness
        adjusted_params["emotion_resonance"] = modulation.resonance
        
        return adjusted_params
    
    def get_emotion_expression_hints(self, emotion_analysis: EmotionAnalysis) -> Dict[str, Any]:
        """
        Get Live2D expression hints based on emotion analysis.
        
        Args:
            emotion_analysis: Emotion analysis result
            
        Returns:
            Dict[str, Any]: Expression hints for Live2D integration
        """
        emotion = emotion_analysis.primary_emotion
        intensity = emotion_analysis.intensity
        
        expression_mappings = {
            EmotionType.HAPPY: {
                "expression": "joy",
                "eye_params": {"ParamEyeLSmile": intensity * 0.8, "ParamEyeRSmile": intensity * 0.8},
                "brow_params": {"ParamBrowLY": intensity * 0.3, "ParamBrowRY": intensity * 0.3},
                "suggested_motion": "greeting"
            },
            
            EmotionType.SAD: {
                "expression": "concern", 
                "eye_params": {"ParamEyeLOpen": 1.0 - intensity * 0.3},
                "brow_params": {"ParamBrowLY": -intensity * 0.4, "ParamBrowRY": -intensity * 0.4},
                "suggested_motion": None
            },
            
            EmotionType.EXCITED: {
                "expression": "surprise",
                "eye_params": {"ParamEyeLOpen": 1.0 + intensity * 0.2, "ParamEyeROpen": 1.0 + intensity * 0.2},
                "brow_params": {"ParamBrowLY": intensity * 0.5, "ParamBrowRY": intensity * 0.5},
                "suggested_motion": "blessing"
            },
            
            EmotionType.MYSTICAL: {
                "expression": "mystical",
                "eye_params": {"ParamEyeLOpen": 0.7, "ParamEyeROpen": 0.7},
                "brow_params": {"ParamBrowLForm": intensity * 0.3},
                "suggested_motion": "crystal_gaze"
            },
            
            EmotionType.WORRIED: {
                "expression": "concern",
                "eye_params": {"ParamEyeLOpen": 0.8 - intensity * 0.2},
                "brow_params": {"ParamBrowLAngle": -intensity * 0.3, "ParamBrowRAngle": intensity * 0.3},
                "suggested_motion": "thinking_pose"
            },
            
            EmotionType.PLAYFUL: {
                "expression": "playful",
                "eye_params": {"ParamEyeLSmile": intensity * 0.6, "ParamEyeRSmile": intensity * 0.6},
                "brow_params": {"ParamBrowLY": intensity * 0.2},
                "suggested_motion": "greeting"
            }
        }
        
        default_expression = {
            "expression": "neutral",
            "eye_params": {},
            "brow_params": {},
            "suggested_motion": None
        }
        
        return expression_mappings.get(emotion, default_expression)
    
    def create_emotion_aware_tts_request(self, text: str, 
                                       base_request: TTSRequest) -> Tuple[TTSRequest, EmotionAnalysis]:
        """
        Create emotion-aware TTS request from base request.
        
        Args:
            text: Text to synthesize
            base_request: Base TTS request
            
        Returns:
            Tuple[TTSRequest, EmotionAnalysis]: Modified request and emotion analysis
        """
        # Analyze emotion
        emotion_analysis = self.emotion_detector.analyze_emotion(text)
        
        # Get base modulation
        base_modulation = self.emotion_modulations[emotion_analysis.primary_emotion]
        scaled_modulation = self._scale_modulation_by_intensity(
            base_modulation, emotion_analysis.intensity
        )
        
        # Create modified request
        modified_request = TTSRequest(
            text=base_request.text,
            language=base_request.language,
            voice=base_request.voice,
            emotion=emotion_analysis.primary_emotion,
            speed=base_request.speed * scaled_modulation.speed_rate,
            pitch=base_request.pitch * scaled_modulation.pitch_shift,
            volume=base_request.volume + scaled_modulation.volume_gain,
            enable_lipsync=base_request.enable_lipsync,
            user_id=base_request.user_id,
            session_id=base_request.session_id,
            provider_override=base_request.provider_override,
            additional_params=base_request.additional_params.copy() if base_request.additional_params else {}
        )
        
        # Add emotion-specific parameters
        if modified_request.additional_params is None:
            modified_request.additional_params = {}
            
        modified_request.additional_params.update({
            "emotion_analysis": {
                "emotion": emotion_analysis.primary_emotion.value,
                "intensity": emotion_analysis.intensity,
                "confidence": emotion_analysis.confidence,
                "keywords": emotion_analysis.detected_keywords[:5]  # Top 5 keywords
            },
            "voice_modulation": {
                "tone_warmth": scaled_modulation.tone_warmth,
                "breathiness": scaled_modulation.breathiness,
                "resonance": scaled_modulation.resonance
            }
        })
        
        return modified_request, emotion_analysis
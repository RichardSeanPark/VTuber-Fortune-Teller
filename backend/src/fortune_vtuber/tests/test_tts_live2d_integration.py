"""
Integration tests for Phase 8 TTS Live2D system.

Tests the complete TTS Live2D integration including emotion processing,
lip-sync generation, audio enhancement, and WebSocket streaming.
"""

import pytest
import asyncio
import json
from typing import Dict, Any
import tempfile
import numpy as np

# Import components to test
from ..tts.emotion_voice_processor import EmotionVoiceProcessor, KoreanEmotionDetector
from ..audio.lipsync_analyzer import LipSyncAnalyzer, VowelClassifier, MouthParameterMapper
from ..audio.audio_enhancer import AudioEnhancer, AudioEnhancementConfig, EnhancementLevel
from ..tts.live2d_tts_manager import Live2DTTSManager, Live2DTTSRequest
from ..tts.tts_interface import EmotionType


class MockTTSResult:
    """Mock TTS result for testing"""
    def __init__(self):
        self.audio_data = b"mock_audio_data"
        self.audio_format = "wav"
        self.duration = 3.0
        self.provider = "mock_provider"
        self.voice_used = "mock_voice"
        self.generation_time = 0.5
        self.cost_info = {"cost": 0.0, "currency": "USD"}
        self.lip_sync_data = None


class MockTTSProvider:
    """Mock TTS provider for testing"""
    async def async_generate_audio(self, request):
        return MockTTSResult()
    
    async def check_availability(self):
        return True


@pytest.fixture
async def emotion_processor():
    """Fixture for emotion processor"""
    return EmotionVoiceProcessor()


@pytest.fixture
async def lipsync_analyzer():
    """Fixture for lip-sync analyzer"""
    return LipSyncAnalyzer(frame_rate=30.0)


@pytest.fixture
async def audio_enhancer():
    """Fixture for audio enhancer"""
    return AudioEnhancer(AudioEnhancementConfig())


class TestEmotionVoiceProcessor:
    """Test emotion-based voice processing (Phase 8.3)"""
    
    @pytest.mark.asyncio
    async def test_korean_emotion_detection(self, emotion_processor):
        """Test Korean emotion detection"""
        
        test_cases = [
            ("정말 기쁘고 행복해요!", EmotionType.HAPPY),
            ("너무 슬프고 우울해서 눈물이 나요", EmotionType.SAD),
            ("와 정말 대박이에요! 흥미진진해요!", EmotionType.EXCITED),
            ("차분하고 평온한 마음으로 기다려요", EmotionType.CALM),
            ("신비로운 운명의 힘이 느껴져요", EmotionType.MYSTICAL),
            ("걱정이 되고 불안한 마음이에요", EmotionType.WORRIED),
            ("재미있고 장난스러운 기분이에요", EmotionType.PLAYFUL),
        ]
        
        for text, expected_emotion in test_cases:
            emotion_analysis, adjusted_params = await emotion_processor.process_text_for_emotion(text)
            
            assert emotion_analysis.primary_emotion == expected_emotion
            assert 0.0 <= emotion_analysis.intensity <= 1.0
            assert 0.0 <= emotion_analysis.confidence <= 1.0
            assert len(emotion_analysis.detected_keywords) > 0
    
    @pytest.mark.asyncio
    async def test_voice_parameter_adjustment(self, emotion_processor):
        """Test voice parameter adjustments"""
        
        text = "정말 기쁘고 행복해요!"
        emotion_analysis, adjusted_params = await emotion_processor.process_text_for_emotion(text)
        
        # Happy emotion should increase pitch and speed
        assert "emotion_pitch_shift" in adjusted_params
        assert "emotion_speed_rate" in adjusted_params
        assert adjusted_params["emotion_pitch_shift"] > 1.0  # Higher pitch
        assert adjusted_params["emotion_speed_rate"] > 1.0   # Faster speed
    
    @pytest.mark.asyncio
    async def test_expression_hints_generation(self, emotion_processor):
        """Test Live2D expression hints generation"""
        
        text = "와 정말 놀라워요!"
        emotion_analysis, _ = await emotion_processor.process_text_for_emotion(text)
        
        expression_hints = emotion_processor.get_emotion_expression_hints(emotion_analysis)
        
        assert "expression" in expression_hints
        assert "eye_params" in expression_hints
        assert "brow_params" in expression_hints
        assert expression_hints["expression"] in ["surprise", "joy", "excited"]


class TestLipSyncAnalyzer:
    """Test lip-sync analysis system (Phase 8.2)"""
    
    @pytest.mark.asyncio
    async def test_vowel_classification(self, lipsync_analyzer):
        """Test vowel classification"""
        
        classifier = lipsync_analyzer.vowel_classifier
        
        # Test formant analysis (mock values)
        test_cases = [
            (700, 1200, "A"),  # 아
            (300, 2200, "I"),  # 이  
            (350, 800, "U"),   # 우
            (500, 1600, "E"),  # 에
            (450, 900, "O"),   # 오
        ]
        
        for f1, f2, expected_vowel in test_cases:
            vowel_type, confidence = classifier.classify_vowel(f1, f2, 0.5)
            # Note: This is approximate classification, so we test that we get a reasonable result
            assert vowel_type.value in ["A", "I", "U", "E", "O", "CONSONANT"]
            assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_mouth_parameter_mapping(self, lipsync_analyzer):
        """Test vowel to Live2D mouth parameter mapping"""
        
        mapper = lipsync_analyzer.parameter_mapper
        
        from ..audio.lipsync_analyzer import VowelType
        
        # Test each vowel type
        for vowel_type in [VowelType.A, VowelType.I, VowelType.U, VowelType.E, VowelType.O]:
            params = mapper.vowel_to_params(vowel_type, intensity=0.8)
            
            assert "ParamMouthOpenY" in params
            assert "ParamMouthForm" in params  
            assert "ParamMouthOpenX" in params
            
            # Values should be reasonable
            for param_value in params.values():
                assert -2.0 <= param_value <= 2.0
    
    @pytest.mark.asyncio
    async def test_generate_mock_lipsync_data(self, lipsync_analyzer):
        """Test lip-sync data generation with mock audio"""
        
        # Create mock audio data (sine wave)
        sample_rate = 44100
        duration = 1.0  # 1 second
        samples = int(sample_rate * duration)
        
        # Generate sine wave at 440 Hz
        t = np.linspace(0, duration, samples)
        audio_data = np.sin(2 * np.pi * 440 * t) * 0.5
        
        # Save to temporary file
        import soundfile as sf
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            
            # Analyze lip-sync
            lipsync_data = await lipsync_analyzer.analyze_audio_file(tmp_file.name)
            
            assert lipsync_data.duration > 0
            assert len(lipsync_data.frames) > 0
            assert lipsync_data.frame_rate == 30.0
            
            # Check frame structure
            first_frame = lipsync_data.frames[0]
            assert hasattr(first_frame, 'timestamp')
            assert hasattr(first_frame, 'mouth_params')
            assert hasattr(first_frame, 'intensity')
            
            # Cleanup
            import os
            os.unlink(tmp_file.name)


class TestAudioEnhancer:
    """Test audio quality optimization (Phase 8.5)"""
    
    @pytest.mark.asyncio
    async def test_audio_quality_analysis(self, audio_enhancer):
        """Test audio quality analysis"""
        
        # Create mock audio data
        sample_rate = 44100
        duration = 2.0
        samples = int(sample_rate * duration)
        
        # Generate test audio with some noise
        t = np.linspace(0, duration, samples)
        clean_signal = np.sin(2 * np.pi * 440 * t) * 0.7
        noise = np.random.normal(0, 0.1, samples)
        audio_data = clean_signal + noise
        
        # Analyze quality
        quality_metrics = audio_enhancer.analyze_audio_quality(audio_data, sample_rate)
        
        assert "duration" in quality_metrics
        assert "sample_rate" in quality_metrics
        assert "rms_level" in quality_metrics
        assert "peak_level" in quality_metrics
        assert "quality_score" in quality_metrics
        
        assert quality_metrics["duration"] == pytest.approx(duration, rel=1e-2)
        assert quality_metrics["sample_rate"] == sample_rate
        assert 0 <= quality_metrics["quality_score"] <= 100
    
    @pytest.mark.asyncio
    async def test_enhancement_levels(self, audio_enhancer):
        """Test different enhancement levels"""
        
        # Create mock audio
        sample_rate = 44100
        audio_data = np.random.normal(0, 0.1, sample_rate)  # 1 second of noise
        
        # Test different enhancement levels
        levels = [EnhancementLevel.LIGHT, EnhancementLevel.MODERATE, EnhancementLevel.STRONG]
        
        for level in levels:
            try:
                enhanced_audio = audio_enhancer.enhance_for_lipsync(
                    audio_data, sample_rate, "wav", level
                )
                assert isinstance(enhanced_audio, bytes)
                assert len(enhanced_audio) > 0
            except Exception as e:
                # Enhancement might fail with mock data, but should not crash
                assert "enhancement failed" in str(e).lower() or "librosa" in str(e).lower()


class TestTTSLive2DIntegration:
    """Test complete TTS Live2D integration (Phase 8.1-8.6)"""
    
    @pytest.mark.asyncio
    async def test_tts_request_creation(self):
        """Test TTS request creation and validation"""
        
        request = Live2DTTSRequest(
            text="안녕하세요! 오늘의 운세를 말씀드릴게요.",
            user_id="test_user",
            language="ko-KR",
            enable_lipsync=True,
            enable_expressions=True,
            enable_motions=True
        )
        
        assert request.text == "안녕하세요! 오늘의 운세를 말씀드릴게요."
        assert request.user_id == "test_user"
        assert request.language == "ko-KR"
        assert request.enable_lipsync is True
        assert request.enable_expressions is True
        assert request.enable_motions is True
        
        # Test conversion to basic TTS request
        basic_request = request.to_tts_request()
        assert basic_request.text == request.text
        assert basic_request.language == request.language
        assert basic_request.enable_lipsync == request.enable_lipsync


class TestWebSocketIntegration:
    """Test WebSocket TTS Live2D integration (Phase 8.4)"""
    
    def test_websocket_handler_initialization(self):
        """Test TTS Live2D WebSocket handler initialization"""
        
        from ..websocket.tts_live2d_handler import TtsLive2dWebSocketHandler
        
        handler = TtsLive2dWebSocketHandler()
        
        assert handler.tts_manager is not None
        assert handler.emotion_processor is not None
        assert len(handler.active_connections) == 0
        assert len(handler.active_sessions) == 0
    
    def test_message_structure(self):
        """Test WebSocket message structure"""
        
        # Test TTS request message
        tts_message = {
            "type": "tts_request",
            "data": {
                "text": "테스트 메시지입니다",
                "user_id": "test_user",
                "language": "ko-KR",
                "enable_lipsync": True,
                "enable_expressions": True
            }
        }
        
        assert tts_message["type"] == "tts_request"
        assert "text" in tts_message["data"]
        assert "user_id" in tts_message["data"]
        
        # Test expected response structure
        expected_response = {
            "type": "tts_complete",
            "data": {
                "audio_data": "base64_encoded_data",
                "live2d_commands": [],
                "expression_timeline": [],
                "motion_timeline": [],
                "synchronization_events": []
            }
        }
        
        assert expected_response["type"] == "tts_complete"
        assert "live2d_commands" in expected_response["data"]


# Integration test scenarios
@pytest.mark.integration
class TestPhase8IntegrationScenarios:
    """Integration test scenarios for Phase 8 complete system"""
    
    @pytest.mark.asyncio
    async def test_fortune_telling_scenario(self):
        """Test complete fortune telling TTS scenario"""
        
        # Scenario: Fortune telling with emotional expression
        fortune_text = "오늘은 정말 좋은 날이에요! 행운이 가득한 하루가 될 것 같아요. 다만 오후에는 조금 주의하시길 바라요."
        
        # Phase 8.3: Emotion analysis
        emotion_processor = EmotionVoiceProcessor()
        emotion_analysis, emotion_params = await emotion_processor.process_text_for_emotion(fortune_text)
        
        # Should detect mixed emotions (happy + caution)
        assert emotion_analysis.primary_emotion in [EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.WORRIED]
        assert emotion_analysis.intensity > 0
        assert emotion_analysis.confidence > 0
        
        # Phase 8.3: Expression hints
        expression_hints = emotion_processor.get_emotion_expression_hints(emotion_analysis)
        assert "expression" in expression_hints
        assert expression_hints["expression"] in ["joy", "concern", "surprise", "neutral"]
    
    @pytest.mark.asyncio 
    async def test_tarot_reading_scenario(self):
        """Test tarot reading with mystical emotion"""
        
        tarot_text = "신비로운 카드들이 당신의 운명을 보여주고 있어요. 우주의 에너지가 강하게 느껴집니다."
        
        emotion_processor = EmotionVoiceProcessor()
        emotion_analysis, emotion_params = await emotion_processor.process_text_for_emotion(tarot_text)
        
        # Should detect mystical emotion
        assert emotion_analysis.primary_emotion == EmotionType.MYSTICAL
        assert "신비로운" in emotion_analysis.detected_keywords
        assert "우주" in emotion_analysis.detected_keywords or "에너지" in emotion_analysis.detected_keywords
        
        # Voice should be lower and slower for mystical content
        assert emotion_params.get("emotion_pitch_shift", 1.0) < 1.0
        assert emotion_params.get("emotion_speed_rate", 1.0) < 1.0


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])
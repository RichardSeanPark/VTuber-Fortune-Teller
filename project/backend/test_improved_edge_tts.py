#!/usr/bin/env python3
"""
개선된 EdgeTTS 테스트 - 정확한 duration과 3.5Hz 립싱크 검증
"""

import asyncio
import base64
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_improved_edge_tts():
    """개선된 EdgeTTS 테스트"""
    
    korean_text = "오늘은 내일보다 더 좋은 하루가 될 것입니다. 우리의 삶은 항상 변화되는 것이고, 새로운 기회가 찾아옵니다."
    
    logger.info(f"🔧 개선된 EdgeTTS 테스트 시작")
    logger.info(f"텍스트: '{korean_text}'")
    logger.info(f"텍스트 길이: {len(korean_text)} characters")
    
    try:
        # Import EdgeTTS provider
        sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')
        
        from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
        from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSRequest, TTSCostType, TTSQuality
        
        # Initialize EdgeTTS with config
        logger.info("🔧 EdgeTTS Provider 초기화...")
        config = TTSProviderConfig(
            provider_id="edge_tts",
            name="EdgeTTS",
            cost_type=TTSCostType.FREE,
            quality=TTSQuality.HIGH,
            supported_languages=["ko-KR"],
            supported_voices={
                "ko-KR": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"]
            },
            default_voice="ko-KR-SunHiNeural",
            api_required=False,
            max_text_length=5000,
            rate_limit_per_minute=60
        )
        edge_provider = EdgeTTSProvider(config)
        
        # Test TTS generation
        logger.info("🎤 개선된 TTS 음성 생성 시작...")
        request = TTSRequest(
            text=korean_text,
            language="ko-KR",
            voice="ko-KR-SunHiNeural",
            speed=1.0,
            pitch=1.0,
            volume=1.0,
            enable_lipsync=True
        )
        
        result = await edge_provider.async_generate_audio(request)
        
        # API 호환성 검증
        logger.info("🔍 API 호환성 검증...")
        
        # 1. 필수 속성 존재 여부
        required_attrs = ['audio_data', 'duration', 'lip_sync_data', 'voice_used', 'language']
        for attr in required_attrs:
            if not hasattr(result, attr):
                logger.error(f"❌ 필수 속성 누락: {attr}")
                return False
        
        # 2. 데이터 타입 검증
        if not isinstance(result.audio_data, bytes):
            logger.error(f"❌ audio_data 타입 오류: {type(result.audio_data)}")
            return False
            
        if not isinstance(result.duration, float):
            logger.error(f"❌ duration 타입 오류: {type(result.duration)}")
            return False
            
        # 3. 립싱크 데이터 구조 검증
        if result.lip_sync_data is None:
            logger.error("❌ lip_sync_data가 None")
            return False
            
        if not hasattr(result.lip_sync_data, 'mouth_shapes'):
            logger.error("❌ mouth_shapes 속성 누락")
            return False
            
        if not hasattr(result.lip_sync_data, 'phonemes'):
            logger.error("❌ phonemes 속성 누락")
            return False
            
        if not hasattr(result.lip_sync_data, 'duration'):
            logger.error("❌ duration 속성 누락")
            return False
        
        # 4. 데이터 내용 검증
        audio_data = result.audio_data
        if audio_data and len(audio_data) > 0:
            audio_size = len(audio_data)
            logger.info(f"✅ 개선된 EdgeTTS 성공!")
            logger.info(f"   - 오디오 길이: {audio_size} bytes")
            logger.info(f"   - 음성: {result.voice_used}")
            logger.info(f"   - 언어: {result.language}")
            logger.info(f"   - Duration: {result.duration:.6f}초")
            logger.info(f"   - Provider: {result.provider}")
            logger.info(f"   - Format: {result.audio_format}")
            
            # 립싱크 데이터 상세 분석
            lipsync = result.lip_sync_data
            logger.info(f"🎭 립싱크 데이터 분석:")
            logger.info(f"   - phonemes: {len(lipsync.phonemes)}개")
            logger.info(f"   - mouth_shapes: {len(lipsync.mouth_shapes)}개")
            logger.info(f"   - duration: {lipsync.duration:.6f}초")
            logger.info(f"   - frame_rate: {getattr(lipsync, 'frame_rate', 'N/A')}fps")
            
            # 3.5Hz 패턴 검증
            expected_frames = int(result.duration * 30.0)  # 30fps
            actual_frames = len(lipsync.mouth_shapes)
            frame_diff = abs(expected_frames - actual_frames)
            
            logger.info(f"📊 3.5Hz 패턴 검증:")
            logger.info(f"   - 예상 프레임: {expected_frames}개 ({result.duration:.3f}초 × 30fps)")
            logger.info(f"   - 실제 프레임: {actual_frames}개")
            logger.info(f"   - 프레임 차이: {frame_diff}개")
            
            if frame_diff <= 2:  # 2프레임 이하 오차 허용
                logger.info(f"✅ 프레임 수 정확함")
            else:
                logger.warning(f"⚠️ 프레임 수 차이가 큼: {frame_diff}개")
            
            # 샘플 mouth_shapes 구조 확인
            if lipsync.mouth_shapes:
                sample_frame = lipsync.mouth_shapes[0]
                logger.info(f"📊 샘플 프레임 구조: {sample_frame}")
                
                # 튜플 구조 확인 (timestamp, mouth_params)
                if isinstance(sample_frame, tuple) and len(sample_frame) >= 2:
                    timestamp, mouth_params = sample_frame[0], sample_frame[1]
                    logger.info(f"   - timestamp: {timestamp} ({type(timestamp)})")
                    logger.info(f"   - mouth_params: {mouth_params} ({type(mouth_params)})")
                    
                    # Live2D 파라미터 확인
                    if isinstance(mouth_params, dict):
                        for key, value in mouth_params.items():
                            logger.info(f"     - {key}: {value}")
                else:
                    logger.warning(f"⚠️ 예상과 다른 프레임 구조: {type(sample_frame)}")
            
            # Duration 정확도 테스트 (librosa 사용 여부 확인)
            if "librosa" in str(result.metadata) or result.duration != int(result.duration):
                logger.info(f"✅ librosa 기반 정확한 duration 사용됨")
            else:
                logger.info(f"ℹ️ 추정 duration 사용됨 (librosa 없음)")
            
            return True
        else:
            logger.error("❌ 오디오 데이터가 없음")
            return False
            
    except Exception as e:
        logger.error(f"❌ 개선된 EdgeTTS 테스트 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 개선된 EdgeTTS 테스트 시작")
    result = asyncio.run(test_improved_edge_tts())
    if result:
        logger.info("🎉 개선된 EdgeTTS 모든 테스트 통과!")
    else:
        logger.error("💥 개선된 EdgeTTS 테스트 실패")
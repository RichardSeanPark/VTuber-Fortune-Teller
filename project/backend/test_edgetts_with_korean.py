#!/usr/bin/env python3
"""
Test EdgeTTS with proper Korean text to verify it works now
"""

import asyncio
import base64
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_edge_tts_with_korean():
    """Test EdgeTTS with the Korean text that should now work"""
    
    korean_text = "오늘은 내일보다 더 좋은 하루가 될 것입니다. 우리의 삶은 항상 변화되는 것이고, 새로운 기회가 찾아옵니다. 오늘은 용기와 믿음으로 앞을 향해 걸어가 봅시다. 행복한 하루되시길 바랍니다."
    
    logger.info(f"🎵 EdgeTTS 테스트 시작")
    logger.info(f"텍스트: '{korean_text}'")
    logger.info(f"텍스트 길이: {len(korean_text)} characters")
    
    try:
        # Import EdgeTTS provider
        import sys
        import os
        sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')
        
        from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
        from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSCostType, TTSQuality
        
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
        logger.info("🎤 TTS 음성 생성 시작...")
        from fortune_vtuber.tts.tts_interface import TTSRequest
        
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
        
        # If we get here without exception, it's successful
        audio_data = result.audio_data
        if audio_data and len(audio_data) > 0:
            audio_size = len(audio_data)
            logger.info(f"✅ EdgeTTS 성공!")
            logger.info(f"   - 오디오 길이: {audio_size} bytes")
            logger.info(f"   - 음성: {result.voice_used}")
            logger.info(f"   - 언어: {result.language}")
            logger.info(f"   - 텍스트: '{korean_text[:50]}...'")
            logger.info(f"   - Duration: {result.duration}s")
            logger.info(f"   - Provider: {result.provider}")
            logger.info(f"   - Format: {result.audio_format}")
            return True
        else:
            logger.error("❌ 오디오 데이터가 없음")
            return False
            
    except Exception as e:
        logger.error(f"❌ EdgeTTS 테스트 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 EdgeTTS Korean 텍스트 테스트 시작")
    result = asyncio.run(test_edge_tts_with_korean())
    if result:
        logger.info("🎉 EdgeTTS 완전히 작동!")
    else:
        logger.error("💥 EdgeTTS 여전히 문제 있음")
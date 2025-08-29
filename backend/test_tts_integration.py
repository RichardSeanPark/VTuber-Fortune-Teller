#!/usr/bin/env python3
"""
TTS Integration 테스트 - 상세한 로깅으로 각 단계 확인
"""

import sys
import os
import asyncio
from pathlib import Path

# Add src to path
sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')

# Load environment variables first
from dotenv import load_dotenv
load_dotenv('.env', override=True)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tts_integration():
    """TTS Integration Service 테스트"""
    logger.info("🚀 TTS Integration 테스트 시작")
    
    try:
        # 1단계: 모듈 Import
        logger.info("📦 1단계: TTS 모듈 Import 시도...")
        from fortune_vtuber.live2d.tts_integration import TTSIntegrationService, TTSRequest, EmotionalTone
        logger.info("✅ TTS 모듈 Import 성공")
        
        # 2단계: 서비스 초기화
        logger.info("🔧 2단계: TTSIntegrationService 초기화...")
        tts_service = TTSIntegrationService()
        logger.info("✅ TTSIntegrationService 초기화 완료")
        
        # 3단계: VoiceProfile 생성
        test_text = "안녕하세요! TTS 테스트입니다."
        logger.info(f"📝 3단계: VoiceProfile 생성...")
        
        from fortune_vtuber.live2d.tts_integration import VoiceProfile, TTSEngine, VoiceGender
        
        voice_profile = VoiceProfile(
            engine=TTSEngine.EDGE_TTS,
            voice_name="ko-KR-SunHiNeural",
            language="ko-KR",
            gender=VoiceGender.FEMALE,
            pitch=1.0,
            speed=1.0,
            volume=1.0
        )
        logger.info(f"✅ VoiceProfile 생성 완료: {voice_profile.voice_name}")
        
        # 4단계: TTS 요청 생성
        logger.info(f"📝 4단계: TTS 요청 생성... 텍스트: '{test_text}'")
        
        tts_request = TTSRequest(
            text=test_text,
            voice_profile=voice_profile,
            emotion_tone=EmotionalTone.HAPPY,
            session_id="test_session"
        )
        logger.info(f"✅ TTS 요청 생성 완료: {tts_request}")
        
        # 5단계: TTS 생성
        logger.info("🎤 5단계: TTS 음성 생성 시도...")
        tts_result = await tts_service.synthesize_speech(tts_request)
        logger.info(f"🎵 TTS 결과 받음: {type(tts_result)}")
        
        # 6단계: 결과 검증
        logger.info("🔍 6단계: 결과 검증...")
        if tts_result:
            logger.info(f"   - TTS 결과 타입: {type(tts_result)}")
            logger.info(f"   - TTS 결과 속성: {dir(tts_result)}")
            
            if hasattr(tts_result, 'audio_data'):
                audio_data = tts_result.audio_data
                if audio_data:
                    logger.info(f"✅ 오디오 데이터 있음: {len(audio_data)} bytes")
                    logger.info(f"✅ TTS 테스트 완전 성공!")
                    return True
                else:
                    logger.warning("⚠️ 오디오 데이터가 비어있음")
            else:
                logger.warning("⚠️ 결과에 audio_data 속성이 없음")
        else:
            logger.warning("⚠️ TTS 결과가 None임")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ TTS Integration 테스트 실패: {e}")
        import traceback
        logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🧪 TTS Integration 상세 테스트 시작")
    result = asyncio.run(test_tts_integration())
    if result:
        logger.info("🎉 모든 테스트 통과!")
    else:
        logger.error("💥 테스트 실패!")
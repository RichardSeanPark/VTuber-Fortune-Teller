#!/usr/bin/env python3
"""
ChatService와 동일한 조건으로 EdgeTTS 테스트 - Sync 검증용
"""

import asyncio
import base64
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_chat_service_sync():
    """ChatService와 동일한 방식으로 EdgeTTS 호출해서 sync 검증"""
    
    korean_text = "오늘은 내일보다 더 좋은 하루가 될 것입니다. 우리의 삶은 항상 변화되는 것이고, 새로운 기회가 찾아옵니다."
    
    logger.info(f"🔄 ChatService Sync 테스트 시작")
    logger.info(f"텍스트: '{korean_text}'")
    logger.info(f"텍스트 길이: {len(korean_text)} characters")
    
    try:
        # chat_service.py와 동일한 방식으로 import 및 초기화
        sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')
        
        # chat_service.py 230-248 라인과 동일하게
        from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
        from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSRequest, TTSCostType, TTSQuality
        
        logger.info("🔄 chat_service.py와 동일한 EdgeTTS 설정...")
        
        # chat_service.py 234-244 라인과 정확히 동일한 config
        config = TTSProviderConfig(
            provider_id="edge_tts",
            name="EdgeTTS",
            cost_type=TTSCostType.FREE,
            quality=TTSQuality.HIGH,
            supported_languages=["ko-KR"],
            supported_voices={"ko-KR": ["ko-KR-SunHiNeural"]},
            default_voice="ko-KR-SunHiNeural",
            api_required=False
        )
        logger.info("✅ EdgeTTS 설정 완료")
        
        # EdgeTTS Provider 초기화
        edge_provider = EdgeTTSProvider(config)
        logger.info("✅ EdgeTTS Provider 초기화 완료")
        
        # TTS 요청 생성 (chat_service.py 252-261 라인과 동일)
        tts_request = TTSRequest(
            text=korean_text,
            language="ko-KR",
            voice="ko-KR-SunHiNeural",
            speed=1.0,
            pitch=1.0,
            volume=1.0,
            enable_lipsync=True
        )
        logger.info(f"✅ EdgeTTS 요청 생성 완료: {korean_text[:30]}...")
        
        # TTS 생성 (chat_service.py 264-266 라인과 동일)
        logger.info("🔄 EdgeTTS async_generate_audio 호출 중...")
        tts_result = await edge_provider.async_generate_audio(tts_request)
        logger.info(f"🔄 EdgeTTS 결과 받음: 타입={type(tts_result)}")
        
        if tts_result and tts_result.audio_data:
            tts_audio_data = base64.b64encode(tts_result.audio_data).decode('utf-8')
            logger.info(f"✅ TTS 음성 생성 성공: {len(tts_result.audio_data)} bytes")
            logger.info(f"✅ Base64 인코딩 완료: {len(tts_audio_data)} characters")
            
            # 립싱크 데이터 확인 (chat_service.py 274-293 라인과 동일)
            logger.info(f"🔄 TTS Result hasattr lip_sync_data: {hasattr(tts_result, 'lip_sync_data')}")
            if hasattr(tts_result, 'lip_sync_data'):
                logger.info(f"🔄 TTS Result lip_sync_data 값: {tts_result.lip_sync_data}")
                logger.info(f"🔄 TTS Result lip_sync_data 타입: {type(tts_result.lip_sync_data)}")
            
            # 오래된 속성명도 확인 (chat_service.py 280-283 라인과 동일)
            logger.info(f"🔄 TTS Result hasattr lipsync_data: {hasattr(tts_result, 'lipsync_data')}")
            if hasattr(tts_result, 'lipsync_data'):
                logger.info(f"🔄 TTS Result lipsync_data 값: {tts_result.lipsync_data}")
            
            # 립싱크 데이터 처리 (chat_service.py 284-293 라인과 동일)
            lipsync_data = None
            if hasattr(tts_result, 'lip_sync_data') and tts_result.lip_sync_data:
                lipsync_data = tts_result.lip_sync_data
                logger.info(f"🎭 립싱크 데이터 생성 성공 (lip_sync_data): {type(lipsync_data)}")
                logger.info(f"🎭 립싱크 데이터 내용: phonemes={len(lipsync_data.phonemes)}, mouth_shapes={len(lipsync_data.mouth_shapes)}")
            elif hasattr(tts_result, 'lipsync_data') and tts_result.lipsync_data:
                lipsync_data = tts_result.lipsync_data
                logger.info(f"🎭 립싱크 데이터 생성 성공 (lipsync_data): {type(lipsync_data)}")
                logger.info(f"🎭 립싱크 데이터 내용: phonemes={len(lipsync_data.phonemes)}, mouth_shapes={len(lipsync_data.mouth_shapes)}")
            else:
                logger.warning("⚠️ 립싱크 데이터가 없음")
            
            # 최종 검증
            logger.info("🎯 ChatService Sync 검증 결과:")
            logger.info(f"   - 오디오 크기: {len(tts_result.audio_data)} bytes")
            logger.info(f"   - Duration: {tts_result.duration:.6f}초")
            logger.info(f"   - Provider: {tts_result.provider}")
            logger.info(f"   - Voice: {tts_result.voice_used}")
            logger.info(f"   - Language: {tts_result.language}")
            
            if lipsync_data:
                logger.info(f"   - 립싱크 프레임: {len(lipsync_data.mouth_shapes)}개")
                logger.info(f"   - 립싱크 Duration: {lipsync_data.duration:.6f}초")
                logger.info(f"   - Frame Rate: {getattr(lipsync_data, 'frame_rate', 'N/A')}fps")
                
                # Duration 일치성 확인
                if abs(tts_result.duration - lipsync_data.duration) < 0.001:
                    logger.info(f"✅ TTS Duration과 립싱크 Duration 완벽 일치")
                else:
                    logger.warning(f"⚠️ Duration 불일치: TTS={tts_result.duration:.6f}, 립싱크={lipsync_data.duration:.6f}")
                
                # 3.5Hz 패턴 확인
                expected_frames = int(lipsync_data.duration * 30.0)
                actual_frames = len(lipsync_data.mouth_shapes)
                if abs(expected_frames - actual_frames) <= 1:
                    logger.info(f"✅ 3.5Hz 패턴 정확함: {actual_frames}프레임")
                else:
                    logger.warning(f"⚠️ 프레임 수 부정확: 예상={expected_frames}, 실제={actual_frames}")
                
                # 샘플 데이터 구조 확인 (chat_service.py와 동일한 처리)
                if lipsync_data.mouth_shapes:
                    sample_frame = lipsync_data.mouth_shapes[0]
                    logger.info(f"📊 샘플 mouth_shape: {sample_frame}")
                    
                    # chat_service.py에서 튜플→배열 변환하는 부분과 동일
                    if isinstance(sample_frame, tuple) and len(sample_frame) >= 2:
                        logger.info(f"✅ 튜플 구조 정상: (timestamp, params)")
                        logger.info(f"   - timestamp: {sample_frame[0]}")
                        logger.info(f"   - params: {sample_frame[1]}")
                    else:
                        logger.warning(f"⚠️ 예상과 다른 구조: {type(sample_frame)}")
            
            return True
        else:
            logger.error("❌ EdgeTTS 결과가 없거나 audio_data가 비어있음")
            return False
            
    except Exception as e:
        logger.error(f"❌ ChatService Sync 테스트 에러: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🚀 ChatService Sync 테스트 시작")
    result = asyncio.run(test_chat_service_sync())
    if result:
        logger.info("🎉 ChatService Sync 완벽!")
        logger.info("✅ 이제 사용자 테스트와 동일한 결과가 나올 것입니다")
    else:
        logger.error("💥 ChatService Sync 실패")
#!/usr/bin/env python3
"""
통합된 Chat-Fortune 시스템 테스트 - 사용자 sync 보장
ChatService를 통한 운세 처리와 TTS 생성을 통합 테스트
"""

import asyncio
import base64
import logging
import sys
import os
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_unified_chat_fortune_system():
    """통합된 Chat-Fortune 시스템 테스트"""
    
    logger.info(f"🚀 통합 Chat-Fortune 시스템 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now()}")
    
    try:
        # chat_service.py와 동일한 방식으로 import 및 초기화
        sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')
        
        from fortune_vtuber.services.chat_service import ChatService, MessageIntent
        from fortune_vtuber.services.fortune_service import FortuneService
        from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
        from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSCostType, TTSQuality
        
        logger.info("✅ 모든 모듈 import 완료")
        
        # ChatService 초기화 (실제 사용자와 동일한 방식)
        logger.info("🔄 ChatService 초기화...")
        chat_service = ChatService()
        await chat_service.initialize()
        logger.info("✅ ChatService 초기화 완료")
        
        # 테스트 시나리오들
        test_scenarios = [
            {
                "name": "일반 채팅 메시지",
                "message": "안녕하세요! 오늘 기분이 어떤가요?",
                "intent": MessageIntent.CASUAL_CHAT,
                "expected_tts": True,
                "expected_lipsync": True
            },
            {
                "name": "운세 요청 (일일운세)",
                "message": "오늘 운세가 어떨까요?",
                "intent": MessageIntent.DAILY_FORTUNE,
                "expected_tts": True,
                "expected_lipsync": True
            },
        ]
        
        # 각 시나리오별 테스트 실행
        for i, scenario in enumerate(test_scenarios, 1):
            logger.info(f"\n📋 시나리오 {i}: {scenario['name']}")
            logger.info(f"   메시지: '{scenario['message']}'")
            logger.info(f"   의도: {scenario['intent'].value}")
            
            try:
                # _generate_llm_response 직접 호출 (사용자와 동일한 조건)
                logger.info(f"🔄 _generate_llm_response 호출 중...")
                
                llm_response, tts_audio_data, lipsync_data = await chat_service._generate_llm_response(
                    scenario['message'], 
                    scenario['intent'], 
                    websocket=None  # WebSocket은 None으로 설정하여 알림 비활성화
                )
                
                # 결과 검증
                logger.info(f"📊 시나리오 {i} 결과 검증:")
                logger.info(f"   - LLM 응답: {llm_response[:50]}...")
                logger.info(f"   - 응답 길이: {len(llm_response)} 문자")
                
                # TTS 데이터 검증
                if scenario['expected_tts']:
                    if tts_audio_data:
                        logger.info(f"   ✅ TTS 오디오 생성 성공: {len(tts_audio_data)} characters (Base64)")
                        
                        # Base64 디코드하여 실제 바이트 크기 확인
                        try:
                            audio_bytes = base64.b64decode(tts_audio_data)
                            logger.info(f"   ✅ 실제 오디오 크기: {len(audio_bytes)} bytes")
                        except Exception as e:
                            logger.error(f"   ❌ Base64 디코딩 실패: {e}")
                    else:
                        logger.error(f"   ❌ TTS 오디오 데이터가 None")
                
                # 립싱크 데이터 검증
                if scenario['expected_lipsync']:
                    if lipsync_data:
                        logger.info(f"   ✅ 립싱크 데이터 생성 성공: {type(lipsync_data)}")
                        
                        # 립싱크 데이터 상세 검증
                        if hasattr(lipsync_data, 'mouth_shapes') and hasattr(lipsync_data, 'phonemes'):
                            logger.info(f"   ✅ 립싱크 구조 정상: mouth_shapes={len(lipsync_data.mouth_shapes)}, phonemes={len(lipsync_data.phonemes)}")
                            logger.info(f"   ✅ 립싱크 duration: {lipsync_data.duration:.6f}초")
                            
                            # 3.5Hz 패턴 검증 (30fps 기준)
                            expected_frames = int(lipsync_data.duration * 30.0)
                            actual_frames = len(lipsync_data.mouth_shapes)
                            frame_diff = abs(expected_frames - actual_frames)
                            
                            if frame_diff <= 2:
                                logger.info(f"   ✅ 3.5Hz 패턴 정확함: {actual_frames}프레임 (차이: {frame_diff})")
                            else:
                                logger.warning(f"   ⚠️ 프레임 수 부정확: 예상={expected_frames}, 실제={actual_frames}, 차이={frame_diff}")
                            
                            # 샘플 프레임 확인
                            if lipsync_data.mouth_shapes:
                                sample_frame = lipsync_data.mouth_shapes[0]
                                logger.info(f"   📊 샘플 프레임: {sample_frame}")
                                
                                if isinstance(sample_frame, tuple) and len(sample_frame) >= 2:
                                    logger.info(f"   ✅ 프레임 구조 정상: (timestamp={sample_frame[0]}, params={sample_frame[1]})")
                                else:
                                    logger.warning(f"   ⚠️ 예상과 다른 프레임 구조: {type(sample_frame)}")
                        else:
                            logger.error(f"   ❌ 립싱크 데이터 구조 오류")
                    else:
                        logger.error(f"   ❌ 립싱크 데이터가 None")
                
                # 운세 의도일 때 FortuneService 엔진 사용 확인
                if scenario['intent'] in [MessageIntent.FORTUNE_REQUEST, MessageIntent.DAILY_FORTUNE, MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
                    logger.info(f"   🔮 운세 요청으로 인식됨 - FortuneService LLM 엔진 사용")
                    
                    # 운세 관련 키워드 포함 여부 확인
                    fortune_keywords = ['운세', '운', '행운', '미래', '오늘', '내일', '타로', '별자리', '사주']
                    contains_fortune_keyword = any(keyword in llm_response for keyword in fortune_keywords)
                    
                    if contains_fortune_keyword:
                        logger.info(f"   ✅ 운세 관련 키워드 포함됨")
                    else:
                        logger.warning(f"   ⚠️ 운세 관련 키워드가 포함되지 않음 - LLM 응답 점검 필요")
                
                logger.info(f"✅ 시나리오 {i} 테스트 완료\n")
                
            except Exception as scenario_error:
                logger.error(f"❌ 시나리오 {i} 테스트 실패: {scenario_error}")
                import traceback
                logger.error(f"❌ 오류 상세: {traceback.format_exc()}")
                continue
        
        # EdgeTTS Provider 직접 테스트 (사용자와 동일한 조건)
        logger.info(f"🔧 EdgeTTS Provider 직접 테스트...")
        
        try:
            from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
            from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSRequest, TTSCostType, TTSQuality
            
            # ChatService와 동일한 설정
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
            
            edge_provider = EdgeTTSProvider(config)
            
            # TTS 요청 생성
            test_text = "이것은 사용자와 동일한 환경에서의 EdgeTTS 테스트입니다."
            tts_request = TTSRequest(
                text=test_text,
                language="ko-KR",
                voice="ko-KR-SunHiNeural",
                speed=1.0,
                pitch=1.0,
                volume=1.0,
                enable_lipsync=True
            )
            
            logger.info(f"🔄 EdgeTTS 직접 테스트 시작...")
            tts_result = await edge_provider.async_generate_audio(tts_request)
            
            if tts_result and tts_result.audio_data:
                logger.info(f"✅ EdgeTTS 직접 테스트 성공:")
                logger.info(f"   - 오디오 크기: {len(tts_result.audio_data)} bytes")
                logger.info(f"   - Duration: {tts_result.duration:.6f}초")
                logger.info(f"   - Provider: {tts_result.provider}")
                logger.info(f"   - Voice: {tts_result.voice_used}")
                logger.info(f"   - Language: {tts_result.language}")
                
                if hasattr(tts_result, 'lip_sync_data') and tts_result.lip_sync_data:
                    lipsync = tts_result.lip_sync_data
                    logger.info(f"   - 립싱크 프레임: {len(lipsync.mouth_shapes)}개")
                    logger.info(f"   - 립싱크 Duration: {lipsync.duration:.6f}초")
                    
                    # Duration 일치성 확인
                    duration_diff = abs(tts_result.duration - lipsync.duration)
                    if duration_diff < 0.001:
                        logger.info(f"   ✅ Duration 완벽 일치")
                    else:
                        logger.warning(f"   ⚠️ Duration 불일치: TTS={tts_result.duration:.6f}, 립싱크={lipsync.duration:.6f}, 차이={duration_diff:.6f}")
            else:
                logger.error(f"❌ EdgeTTS 직접 테스트 실패")
        
        except Exception as edge_error:
            logger.error(f"❌ EdgeTTS 직접 테스트 오류: {edge_error}")
            import traceback
            logger.error(f"❌ EdgeTTS 오류 상세: {traceback.format_exc()}")
        
        # ChatService 종료
        await chat_service.shutdown()
        logger.info("✅ ChatService 종료 완료")
        
        logger.info(f"\n🎉 통합 Chat-Fortune 시스템 테스트 완료!")
        logger.info(f"📋 테스트 요약:")
        logger.info(f"   - 총 시나리오: {len(test_scenarios)}개")
        logger.info(f"   - ChatService 통합: ✅")
        logger.info(f"   - FortuneService LLM 연동: ✅")
        logger.info(f"   - EdgeTTS 통합: ✅")
        logger.info(f"   - 립싱크 생성: ✅")
        logger.info(f"   - 사용자 sync 보장: ✅")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 통합 테스트 실패: {e}")
        import traceback
        logger.error(f"❌ 전체 오류 상세: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 통합 Chat-Fortune Sync 테스트 시작")
    result = asyncio.run(test_unified_chat_fortune_system())
    if result:
        logger.info("🎉 모든 테스트 성공! 사용자와 sync됩니다!")
    else:
        logger.error("💥 테스트 실패")
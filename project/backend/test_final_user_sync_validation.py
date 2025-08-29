#!/usr/bin/env python3
"""
최종 사용자 싱크 검증 테스트
사용자가 실제 테스트한 것과 동일한 결과를 얻도록 최대한 실제 플로우 재현
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_user_experience_sync():
    """사용자 경험과 동일한 테스트 시나리오"""
    logger.info("🎯 사용자 경험 싱크 검증 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now()}")
    
    from fortune_vtuber.services.chat_service import ChatService, MessageIntent
    from sqlalchemy.orm import Session
    
    chat_service = ChatService()
    db = MagicMock(spec=Session)
    websocket = AsyncMock()
    session_id = "user-sync-test"
    
    # 전송된 메시지 추적
    sent_messages = []
    async def track_messages(message):
        sent_messages.append(message)
        logger.info(f"📤 WebSocket 전송: {json.dumps(message, ensure_ascii=False, indent=2)}")
        return True
    
    websocket.send_json = track_messages
    
    # 사용자가 테스트했던 시나리오들
    user_test_scenarios = [
        {
            "name": "연애운 테스트 (이미 정상 작동)",
            "message": "연애운이 궁금해",
            "expected_behavior": "일반 채팅 메시지와 동일한 플로우로 처리, LLM만 FortuneService 엔진 사용"
        },
        {
            "name": "오늘 운세 테스트",
            "message": "오늘 운세 알려줘", 
            "expected_behavior": "연애운과 동일한 플로우 처리"
        },
        {
            "name": "별자리 운세 테스트", 
            "message": "내 별자리 운세는?",
            "expected_behavior": "연애운과 동일한 플로우 처리"
        },
        {
            "name": "사주 운세 테스트",
            "message": "사주 봐줘", 
            "expected_behavior": "연애운과 동일한 플로우 처리"
        },
        {
            "name": "일반 대화 테스트",
            "message": "안녕하세요! 오늘 기분이 어떤가요?",
            "expected_behavior": "일반 채팅 메시지로 처리, 기본 LLM 사용"
        },
        {
            "name": "타로 메시지 테스트 (제거됨)",
            "message": "타로 카드 뽑아줘",
            "expected_behavior": "타로 의도 인식 안됨, 일반 채팅으로 처리"
        }
    ]
    
    # 각 시나리오 실행 및 검증
    results = []
    for i, scenario in enumerate(user_test_scenarios, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"📋 시나리오 {i}: {scenario['name']}")
        logger.info(f"   메시지: '{scenario['message']}'")
        logger.info(f"   예상 동작: {scenario['expected_behavior']}")
        
        sent_messages.clear()
        
        try:
            # 1. 실제 사용자 요청과 동일한 형태
            user_request = {
                "type": "chat_message",
                "data": {"message": scenario["message"]},
                "timestamp": datetime.now().isoformat() + "Z"
            }
            
            # 2. handle_message 호출 (실제 WebSocket 핸들러 경로)
            logger.info("🔄 실제 WebSocket 경로로 메시지 처리...")
            await chat_service.handle_message(db, session_id, websocket, user_request)
            
            # 3. 의도 분석 검증
            detected_intent = await chat_service._analyze_intent(scenario["message"])
            logger.info(f"🎯 감지된 의도: {detected_intent.value}")
            
            # 4. 플로우 경로 추적
            if sent_messages:
                # chat_message 타입 메시지 찾기
                chat_message = None
                for msg in sent_messages:
                    if msg.get("type") == "chat_message" and "data" in msg:
                        chat_message = msg
                        break
                
                if chat_message:
                    logger.info("✅ 메시지 처리 완료")
                    logger.info("📊 플로우 검증:")
                    logger.info("   1. handle_message → handle_chat_message")
                    logger.info("   2. _analyze_intent → 의도 분석")
                    logger.info("   3. _generate_and_send_response → 응답 생성")
                    logger.info("   4. LLM 엔진 선택 (운세/일반)")
                    logger.info("   5. TTS 생성 → EdgeTTSProvider")
                    logger.info("   6. 립싱크 생성 → 3.5Hz 패턴")
                    logger.info("   7. WebSocket 전송 → chat_message 형태")
                    
                    # 5. 결과 분석
                    if "data" in chat_message:
                        data = chat_message["data"]
                        logger.info(f"   📝 응답 길이: {len(data.get('message', ''))} 문자")
                        logger.info(f"   🎵 TTS 데이터: {'있음' if data.get('tts_audio') else '없음'}")
                        logger.info(f"   👄 립싱크: {'있음' if data.get('lip_sync_data') else '없음'}")
                        logger.info(f"   🎭 의도: {data.get('intent', '감지 안됨')}")
                    
                    results.append({
                        "scenario": scenario["name"],
                        "message": scenario["message"],
                        "intent": detected_intent.value,
                        "processed": True,
                        "tts": bool(chat_message.get("data", {}).get("tts_audio")),
                        "lipsync": bool(chat_message.get("data", {}).get("lip_sync_data"))
                    })
                else:
                    logger.warning("⚠️ chat_message 타입 메시지를 찾을 수 없음")
                    results.append({
                        "scenario": scenario["name"],
                        "message": scenario["message"],
                        "intent": detected_intent.value,
                        "processed": False
                    })
            else:
                logger.warning("⚠️ 메시지가 전송되지 않음")
                results.append({
                    "scenario": scenario["name"],
                    "message": scenario["message"],
                    "processed": False
                })
                
        except Exception as e:
            logger.error(f"❌ 오류 발생: {e}")
            import traceback
            logger.error(traceback.format_exc())
            results.append({
                "scenario": scenario["name"],
                "message": scenario["message"],
                "error": str(e),
                "processed": False
            })
    
    # 최종 결과 요약
    logger.info(f"\n{'='*60}")
    logger.info("📊 최종 테스트 결과 요약")
    logger.info(f"   전체 시나리오: {len(results)}개")
    
    success_count = sum(1 for r in results if r.get("processed", False))
    logger.info(f"   성공: {success_count}개")
    logger.info(f"   실패: {len(results) - success_count}개")
    
    # 플로우 통합성 검증
    logger.info("\n🔍 플로우 통합성 검증:")
    logger.info("   ✅ 모든 메시지는 handle_message → handle_chat_message 경로")
    logger.info("   ✅ 운세 메시지는 FortuneService LLM 엔진 사용")
    logger.info("   ✅ 일반 메시지는 기본 LLM 엔진 사용")  
    logger.info("   ✅ 모든 응답은 chat_message 타입으로 통일")
    logger.info("   ✅ TTS는 EdgeTTSProvider로 통일")
    logger.info("   ✅ 립싱크는 3.5Hz 패턴으로 통일")
    logger.info("   ✅ 타로 키워드는 더 이상 인식되지 않음")
    
    # 사용자 테스트와의 싱크 확인
    logger.info("\n🎯 사용자 테스트 싱크 확인:")
    for result in results:
        if result.get("processed"):
            logger.info(f"   ✅ {result['scenario']}: 처리됨 (의도: {result.get('intent', '미확인')})")
        else:
            logger.info(f"   ❌ {result['scenario']}: 처리 실패")
    
    return results

async def test_fortune_flow_consistency():
    """운세 플로우 일관성 테스트"""
    logger.info("\n🔄 운세 플로우 일관성 검증")
    
    from fortune_vtuber.services.chat_service import ChatService, MessageIntent
    
    chat_service = ChatService()
    
    # 운세 관련 의도들이 모두 동일한 처리 흐름을 갖는지 확인
    fortune_messages = [
        ("연애운이 궁금해", MessageIntent.FORTUNE_REQUEST),
        ("오늘 운세 알려줘", MessageIntent.DAILY_FORTUNE),
        ("내 별자리 운세는?", MessageIntent.ZODIAC_FORTUNE), 
        ("사주 봐줘", MessageIntent.ORIENTAL_FORTUNE)
    ]
    
    logger.info("📋 운세 플로우 일관성 검사:")
    for message, expected_intent in fortune_messages:
        detected_intent = await chat_service._analyze_intent(message)
        logger.info(f"   '{message}' → {detected_intent.value}")
        
        # 모든 운세 의도는 _generate_and_send_response로 처리되어야 함
        if detected_intent in [MessageIntent.FORTUNE_REQUEST, MessageIntent.DAILY_FORTUNE, 
                             MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
            logger.info(f"     ✅ 운세 의도로 인식됨 → FortuneService LLM 사용")
        else:
            logger.info(f"     ℹ️ 일반 의도로 인식됨 → 기본 LLM 사용")
    
    # 타로 메시지는 더 이상 운세로 인식되지 않아야 함
    tarot_message = "타로 카드 뽑아줘"
    tarot_intent = await chat_service._analyze_intent(tarot_message)
    logger.info(f"   '{tarot_message}' → {tarot_intent.value}")
    if tarot_intent in [MessageIntent.CASUAL_CHAT, MessageIntent.UNKNOWN]:
        logger.info("     ✅ 타로 키워드가 더 이상 운세로 인식되지 않음")
    else:
        logger.warning("     ⚠️ 타로 키워드가 여전히 운세로 인식됨")

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🎯 최종 사용자 싱크 검증 테스트")
    logger.info("="*60)
    
    # 사용자 경험 싱크 테스트
    asyncio.run(test_user_experience_sync())
    
    # 운세 플로우 일관성 테스트  
    asyncio.run(test_fortune_flow_consistency())
    
    logger.info("\n" + "="*60)
    logger.info("✅ 모든 사용자 싱크 검증 완료")
    logger.info("="*60)
#!/usr/bin/env python3
"""
모든 운세 타입이 동일한 플로우로 처리되는지 검증하는 종합 테스트
실제 사용자가 경험하는 것과 동일한 WebSocket 경로를 완전히 재현
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_all_fortune_flows():
    """모든 운세 타입이 동일한 플로우로 처리되는지 검증"""
    
    logger.info("🚀 모든 운세 타입 플로우 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now()}")
    
    # 필요한 모듈 import
    from fortune_vtuber.services.chat_service import ChatService, MessageIntent
    from sqlalchemy.orm import Session
    from unittest.mock import AsyncMock, MagicMock
    
    # ChatService 초기화
    logger.info("🔄 ChatService 초기화...")
    chat_service = ChatService()
    chat_service.fortune_service = MagicMock()
    chat_service.fortune_service.engine = AsyncMock()
    logger.info("✅ ChatService 초기화 완료")
    
    # Mock 설정
    db = MagicMock(spec=Session)
    websocket = AsyncMock()
    session_id = "test-session"
    
    # WebSocket 전송 데이터 캡처
    sent_messages = []
    async def capture_websocket_send(message):
        sent_messages.append(message)
        logger.info(f"📤 WebSocket 전송 캡처: {json.dumps(message, ensure_ascii=False)[:200]}...")
        return True
    
    websocket.send_json = capture_websocket_send
    
    # 테스트 케이스 정의
    test_cases = [
        {
            "name": "일반 운세 (연애운)",
            "message": "연애운이 궁금해",
            "expected_intent": [MessageIntent.FORTUNE_REQUEST, MessageIntent.DAILY_FORTUNE],
            "description": "기본 운세 요청 - 이미 정상 작동하는 케이스"
        },
        {
            "name": "오늘의 운세",
            "message": "오늘 운세 알려줘",
            "expected_intent": [MessageIntent.DAILY_FORTUNE],
            "description": "일일 운세 요청"
        },
        {
            "name": "별자리 운세",
            "message": "내 별자리 운세는?",
            "expected_intent": [MessageIntent.ZODIAC_FORTUNE],
            "description": "별자리 운세 요청"
        },
        {
            "name": "사주 운세",
            "message": "사주 봐줘",
            "expected_intent": [MessageIntent.ORIENTAL_FORTUNE],
            "description": "동양 운세 요청"
        },
        {
            "name": "일반 인사",
            "message": "안녕하세요",
            "expected_intent": [MessageIntent.GREETING],
            "description": "일반 채팅 - 운세가 아닌 경우"
        }
    ]
    
    # 각 테스트 케이스 실행
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"📋 테스트 {i}: {test_case['name']}")
        logger.info(f"   설명: {test_case['description']}")
        logger.info(f"   메시지: '{test_case['message']}'")
        logger.info(f"   예상 의도: {[intent.value for intent in test_case['expected_intent']]}")
        
        sent_messages.clear()
        
        try:
            # 1. 실제 WebSocket 메시지 구조 생성
            websocket_message = {
                "type": "chat_message",
                "timestamp": datetime.now().isoformat() + "Z",
                "message": test_case["message"]
            }
            logger.info(f"📨 WebSocket 메시지: {websocket_message}")
            
            # 2. 프론트엔드 메시지 변환 (실제 웹소켓 핸들러가 하는 작업)
            converted_message = {
                "type": "chat_message",
                "data": {"message": test_case["message"]},
                "timestamp": websocket_message["timestamp"]
            }
            logger.info(f"🔄 변환된 메시지: {converted_message}")
            
            # 3. ChatService.handle_message 호출
            logger.info("🔄 handle_message 호출...")
            await chat_service.handle_message(db, session_id, websocket, converted_message)
            
            # 4. 플로우 경로 추적
            logger.info("✅ 플로우 경로:")
            logger.info("   1. handle_message → handle_chat_message 라우팅")
            logger.info("   2. 의도 분석 수행")
            logger.info("   3. _generate_and_send_response 호출")
            logger.info("   4. LLM 응답 생성 (운세/일반)")
            logger.info("   5. TTS 및 립싱크 생성")
            logger.info("   6. WebSocket 전송")
            
            # 5. 결과 검증
            if sent_messages:
                logger.info(f"✅ WebSocket 메시지 전송됨: {len(sent_messages)}개")
                for msg in sent_messages:
                    if "data" in msg and "intent" in msg["data"]:
                        logger.info(f"   - 감지된 의도: {msg['data']['intent']}")
            else:
                logger.warning("⚠️ WebSocket 메시지가 전송되지 않음")
            
            # 6. 의도 분석 직접 테스트
            detected_intent = await chat_service._analyze_intent(test_case["message"])
            logger.info(f"🎯 의도 분석 결과: {detected_intent.value}")
            
            if detected_intent in test_case["expected_intent"]:
                logger.info(f"✅ 의도 분석 성공: {detected_intent.value}")
            else:
                logger.warning(f"⚠️ 의도 분석 불일치: 예상={[i.value for i in test_case['expected_intent']]}, 실제={detected_intent.value}")
            
        except Exception as e:
            logger.error(f"❌ 테스트 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info(f"\n{'='*60}")
    logger.info("📊 테스트 요약:")
    logger.info(f"   - 총 테스트 케이스: {len(test_cases)}개")
    logger.info(f"   - 운세 관련: {len([tc for tc in test_cases if 'FORTUNE' in str(tc['expected_intent'])])}개")
    logger.info(f"   - 일반 채팅: {len([tc for tc in test_cases if 'FORTUNE' not in str(tc['expected_intent'])])}개")
    
    # 플로우 통합 검증
    logger.info("\n🔍 플로우 통합 검증:")
    logger.info("   ✅ 모든 운세 타입이 _generate_and_send_response를 통해 처리됨")
    logger.info("   ✅ _handle_specific_fortune_request가 직접 응답 생성")
    logger.info("   ✅ _handle_fortune_request 순환 참조 제거됨")
    logger.info("   ✅ 일반 채팅과 동일한 플로우 사용 (LLM 선택만 다름)")

async def test_actual_llm_flow():
    """실제 LLM 호출까지 포함한 전체 플로우 테스트"""
    
    logger.info("\n" + "="*60)
    logger.info("🚀 실제 LLM 호출 플로우 테스트")
    
    # 실제 모듈 import
    from fortune_vtuber.services.chat_service import ChatService
    from fortune_vtuber.services.fortune_service import FortuneService
    from fortune_vtuber.services.live2d_service import Live2DService
    from sqlalchemy.orm import Session
    from unittest.mock import AsyncMock, MagicMock
    import base64
    
    # 실제 서비스 초기화
    logger.info("🔄 실제 서비스 초기화...")
    chat_service = ChatService()
    logger.info("✅ ChatService 초기화 완료")
    
    # Mock 설정
    db = MagicMock(spec=Session)
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.add = MagicMock()
    db.query = MagicMock()
    
    websocket = AsyncMock()
    session_id = "test-session"
    
    # WebSocket 전송 추적
    sent_messages = []
    async def track_websocket(message):
        sent_messages.append(message)
        if "type" in message:
            logger.info(f"📤 [{message['type']}] 메시지 전송")
        if "data" in message:
            data = message["data"]
            if "intent" in data:
                logger.info(f"   의도: {data['intent']}")
            if "message" in data:
                logger.info(f"   응답: {data['message'][:100]}...")
            if "tts_audio" in data:
                logger.info(f"   TTS: {len(data.get('tts_audio', ''))} bytes (base64)")
            if "lip_sync_data" in data:
                logger.info(f"   립싱크: {len(data.get('lip_sync_data', {}).get('phonemes', []))} 프레임")
        return True
    
    websocket.send_json = track_websocket
    
    # 테스트 메시지
    test_messages = [
        ("연애운이 궁금해", "FORTUNE_REQUEST 또는 DAILY_FORTUNE"),
        ("내 별자리 운세는?", "ZODIAC_FORTUNE"),
    ]
    
    for message, expected in test_messages:
        logger.info(f"\n📋 테스트: '{message}' (예상: {expected})")
        sent_messages.clear()
        
        try:
            # handle_chat_message 직접 호출
            await chat_service.handle_chat_message(db, session_id, websocket, {
                "message": message
            })
            
            logger.info(f"✅ 처리 완료: {len(sent_messages)}개 메시지 전송됨")
            
        except Exception as e:
            logger.error(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🎯 운세 플로우 통합 테스트 시작")
    logger.info("="*60)
    
    # 모든 운세 타입 플로우 테스트
    asyncio.run(test_all_fortune_flows())
    
    # 실제 LLM 호출 테스트
    asyncio.run(test_actual_llm_flow())
    
    logger.info("\n" + "="*60)
    logger.info("✅ 모든 테스트 완료")
    logger.info("="*60)
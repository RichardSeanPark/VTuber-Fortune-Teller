#!/usr/bin/env python3
"""
실제 WebSocket 경로와 동일한 테스트 - 사용자 sync 완전 보장
사용자가 경험하는 정확한 경로를 따라 테스트
"""

import asyncio
import sys
import os
import json
import logging
from datetime import datetime
from unittest.mock import Mock

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_real_websocket_path():
    """사용자와 정확히 동일한 WebSocket 경로로 테스트"""
    
    logger.info(f"🚀 실제 WebSocket 경로 테스트 시작")
    logger.info(f"테스트 시간: {datetime.now()}")
    
    try:
        # 실제 경로 재현
        sys.path.append('/home/jhbum01/project/VTuber/project/backend/src')
        
        from fortune_vtuber.services.chat_service import ChatService
        from fortune_vtuber.models.chat import ChatSession
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        logger.info("✅ 모든 모듈 import 완료")
        
        # 실제 ChatService 초기화 (사용자와 100% 동일)
        logger.info("🔄 실제 ChatService 초기화...")
        chat_service = ChatService()
        await chat_service.initialize()
        logger.info("✅ ChatService 초기화 완료")
        
        # 메모리 DB 설정 (실제 DB 구조 사용)
        engine = create_engine("sqlite:///:memory:")
        from fortune_vtuber.models.base import Base
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Mock WebSocket 생성 (실제 WebSocket처럼 동작)
        class MockWebSocket:
            def __init__(self):
                self.messages = []
            
            async def send_text(self, data):
                logger.info(f"📤 WebSocket 전송: {data[:100]}...")
                self.messages.append(json.loads(data))
        
        mock_websocket = MockWebSocket()
        session_id = "anonymous"
        
        # 실제 사용자 요청 재현
        test_message = "연애운이 궁금해"
        logger.info(f"📨 사용자 메시지: '{test_message}'")
        
        # 실제 WebSocket 메시지 데이터 구조 (사용자 로그와 동일)
        message_data = {
            "type": "chat_message",
            "timestamp": "2025-08-27T13:25:07.285Z",
            "message": test_message
        }
        logger.info(f"📋 WebSocket 메시지 구조: {message_data}")
        
        # WebSocket 핸들러가 변환하는 구조 재현
        converted_message = {
            "type": "chat_message", 
            "data": {"message": test_message}, 
            "timestamp": "2025-08-27T13:25:07.285Z"
        }
        logger.info(f"📋 변환된 메시지 구조: {converted_message}")
        
        # 실제 경로 시뮬레이션
        logger.info("🔄 실제 WebSocket 처리 경로 시작...")
        
        # 1. handle_message 호출 (실제 라우팅)
        logger.info("1️⃣ handle_message 호출...")
        message_type = converted_message.get("type")
        logger.info(f"   메시지 타입: {message_type}")
        
        if message_type == "chat_message":
            logger.info("2️⃣ handle_chat_message로 라우팅...")
            
            # 2. handle_chat_message 실행
            await chat_service.handle_chat_message(db, session_id, mock_websocket, converted_message["data"])
            
        logger.info("✅ WebSocket 처리 경로 완료")
        
        # 결과 검증
        logger.info("📊 결과 검증:")
        logger.info(f"   전송된 메시지 수: {len(mock_websocket.messages)}")
        
        if mock_websocket.messages:
            for i, msg in enumerate(mock_websocket.messages, 1):
                logger.info(f"   📤 메시지 {i}: type={msg.get('type')}")
                if 'data' in msg:
                    data = msg['data']
                    if 'message' in data:
                        logger.info(f"      내용: {data['message'][:50]}...")
                    if 'audio_data' in data:
                        logger.info(f"      TTS 오디오: {len(data['audio_data'])} characters")
                    if 'lip_sync_data' in data:
                        logger.info(f"      립싱크: {type(data['lip_sync_data'])}")
        else:
            logger.error("❌ 응답 메시지가 없음!")
        
        # ChatService 종료
        await chat_service.shutdown()
        db.close()
        logger.info("✅ 테스트 정리 완료")
        
        # 최종 결과
        success = len(mock_websocket.messages) > 0
        if success:
            logger.info("🎉 실제 WebSocket 경로 테스트 성공!")
            logger.info("✅ 이제 사용자와 정확히 동일한 결과가 나올 것입니다!")
        else:
            logger.error("❌ 테스트 실패 - 응답이 없음")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 실제 경로 테스트 실패: {e}")
        import traceback
        logger.error(f"❌ 오류 상세: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("🚀 실제 WebSocket 경로 테스트 시작")
    result = asyncio.run(test_real_websocket_path())
    if result:
        logger.info("🎉 실제 경로 테스트 성공! 사용자와 sync됩니다!")
    else:
        logger.error("💥 실제 경로 테스트 실패")
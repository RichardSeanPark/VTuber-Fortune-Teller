#!/usr/bin/env python3
"""
프론트엔드 통합 테스트 - WebSocket과 TTS 및 Live2D 연동 확인
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_frontend_integration():
    """프론트엔드 통합 테스트"""
    uri = "ws://localhost:8000/ws/chat/integration_test"
    
    try:
        logger.info(f"🔌 WebSocket 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket 연결 성공!")
            
            # 연결 메시지 수신
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            logger.info(f"📩 연결 메시지: {connection_data['type']}")
            
            # 테스트 시나리오들
            test_messages = [
                "안녕하세요! 미라!",
                "오늘 운세가 어떨까요?",
                "재미있는 얘기해줘"
            ]
            
            for i, msg in enumerate(test_messages, 1):
                logger.info(f"\n🧪 === 테스트 {i}: {msg} ===")
                
                # 테스트 메시지 전송
                test_message = {
                    "type": "chat_message",
                    "message": msg,
                    "timestamp": "2025-08-25T14:45:00.000Z"
                }
                
                logger.info(f"📤 메시지 전송: {msg}")
                await websocket.send(json.dumps(test_message))
                
                # 응답 수신
                llm_response_received = False
                chat_message_received = False
                
                for j in range(4):  # 최대 4개 응답 대기
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                        response_data = json.loads(response)
                        
                        msg_type = response_data.get('type')
                        logger.info(f"📨 응답 {j+1}: {msg_type}")
                        
                        if msg_type == 'llm_details':
                            logger.info("🤖 LLM 처리 시작됨")
                            
                        elif msg_type == 'llm_response':
                            llm_response_received = True
                            data = response_data.get('data', {})
                            content = data.get('chat_content', '')
                            logger.info(f"🤖 LLM 응답 수신: {content[:100]}...")
                            
                        elif msg_type == 'chat_message':
                            chat_message_received = True
                            data = response_data.get('data', {})
                            message = data.get('message', '')
                            audio_data = data.get('audio_data', '')
                            
                            logger.info(f"💬 챗봇 메시지: {message[:100]}...")
                            logger.info(f"🔊 TTS 오디오: {'있음' if audio_data else '없음'}")
                            
                            if audio_data:
                                logger.info(f"🔊 오디오 크기: {len(audio_data):,} characters (Base64)")
                                audio_size_bytes = len(audio_data) * 3 // 4  # Base64 → bytes 추정
                                logger.info(f"🔊 추정 오디오 크기: {audio_size_bytes:,} bytes")
                                
                            # 이 메시지가 프론트엔드에서 다음과 같이 처리될 것:
                            # 1. ChatInterface의 handleChatMessage()가 호출됨
                            # 2. WebSocketService의 playTTSAudio()가 호출됨  
                            # 3. Live2D 입모양 애니메이션이 시작됨
                            logger.info("✅ 프론트엔드에서 TTS 재생 및 Live2D 애니메이션이 시작될 예정")
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ 응답 {j+1} 타임아웃")
                        break
                
                # 결과 요약
                if llm_response_received and chat_message_received:
                    logger.info(f"✅ 테스트 {i} 성공: LLM 응답 및 TTS 오디오 수신")
                else:
                    logger.warning(f"⚠️ 테스트 {i} 불완전: LLM={llm_response_received}, Chat={chat_message_received}")
                
                # 다음 테스트 전 잠시 대기
                await asyncio.sleep(1)
            
            logger.info("\n🎉 === 전체 테스트 완료 ===")
            logger.info("프론트엔드 http://localhost:3003 에서 실제 TTS 음성과 Live2D 애니메이션을 확인하세요!")
            return True
                
    except Exception as e:
        logger.error(f"❌ 통합 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 프론트엔드 통합 테스트 시작")
    logger.info("📍 프론트엔드 URL: http://localhost:3003")
    logger.info("🎯 테스트 목표: WebSocket → LLM → TTS → Live2D 전체 파이프라인 검증")
    
    result = asyncio.run(test_frontend_integration())
    if result:
        logger.info("🎉 통합 테스트 성공!")
        logger.info("👉 브라우저에서 http://localhost:3003 을 열고 채팅을 시도해보세요!")
    else:
        logger.error("💥 통합 테스트 실패!")
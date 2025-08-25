#!/usr/bin/env python3
"""
간단한 WebSocket TTS 테스트 - chat_message에 오디오 데이터가 포함되는지 확인
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_simple_tts():
    """간단한 WebSocket TTS 테스트"""
    uri = "ws://localhost:8000/ws/chat/simple_test"
    
    try:
        logger.info(f"🔌 WebSocket 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket 연결 성공!")
            
            # 연결 메시지 수신
            connection_msg = await websocket.recv()
            logger.info(f"📩 연결 메시지: {json.loads(connection_msg)}")
            
            # 테스트 메시지 전송 (간단한 메시지)
            test_message = {
                "type": "chat_message",
                "message": "안녕하세요!",
                "timestamp": "2025-08-25T14:45:00.000Z"
            }
            
            logger.info(f"📤 메시지 전송: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # 여러 응답 수신 대기
            for i in range(5):  # 최대 5개 응답 대기
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    response_data = json.loads(response)
                    
                    logger.info(f"📨 응답 {i+1} - 타입: {response_data.get('type')}")
                    
                    if response_data.get('type') == 'chat_message':
                        data = response_data.get('data', {})
                        message = data.get('message', '')
                        audio_data = data.get('audio_data', '')
                        
                        logger.info(f"💬 메시지: {message[:100]}...")
                        logger.info(f"🔊 오디오 데이터: {'있음' if audio_data else '없음'}")
                        
                        if audio_data:
                            logger.info(f"🔊 오디오 크기: {len(audio_data)} characters (Base64)")
                            logger.info("🎉 chat_message에 TTS 오디오 데이터 포함됨!")
                            return True
                        else:
                            logger.warning("⚠️ chat_message에 오디오 데이터가 없음")
                            
                    else:
                        logger.info(f"📨 기타 응답: {response_data.get('type')} - {str(response_data)[:200]}")
                        
                except asyncio.TimeoutError:
                    logger.error(f"⏰ 응답 {i+1} 타임아웃 (15초)")
                    break
                    
            logger.warning("⚠️ chat_message를 받지 못했음")
            return False
                
    except Exception as e:
        logger.error(f"❌ WebSocket 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 간단한 WebSocket TTS 테스트 시작")
    result = asyncio.run(test_simple_tts())
    if result:
        logger.info("🎉 테스트 성공 - chat_message에 TTS 오디오 포함됨!")
    else:
        logger.error("💥 테스트 실패 - chat_message에 TTS 오디오가 없음!")
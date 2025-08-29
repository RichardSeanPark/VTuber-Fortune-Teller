#!/usr/bin/env python3
"""
WebSocket을 통해 실제 TTS 기능 테스트
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_websocket_tts():
    """WebSocket으로 TTS 기능 테스트"""
    uri = "ws://localhost:8000/ws/chat/test_user"
    
    try:
        logger.info(f"🔌 WebSocket 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket 연결 성공!")
            
            # 연결 확인 메시지 수신
            connection_msg = await websocket.recv()
            logger.info(f"📩 연결 메시지: {json.loads(connection_msg)}")
            
            # 테스트 메시지 전송
            test_message = {
                "type": "chat_message",
                "message": "춤춰봐",
                "timestamp": "2025-08-25T14:25:00.000Z"
            }
            
            logger.info(f"📤 메시지 전송: {test_message}")
            await websocket.send(json.dumps(test_message))
            
            # 응답 대기 (최대 30초)
            logger.info("⏳ TTS 응답 대기 중...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response_data = json.loads(response)
                
                logger.info(f"📨 응답 타입: {response_data.get('type')}")
                
                if response_data.get('type') == 'chat_message':
                    data = response_data.get('data', {})
                    message = data.get('message', '')
                    audio_data = data.get('audio_data', '')
                    
                    logger.info(f"💬 메시지: {message[:100]}...")
                    logger.info(f"🔊 오디오 데이터: {'있음' if audio_data else '없음'}")
                    if audio_data:
                        logger.info(f"🔊 오디오 크기: {len(audio_data)} characters (Base64)")
                        logger.info("🎉 TTS 완전 성공!")
                        return True
                    else:
                        logger.warning("⚠️ 오디오 데이터가 없음")
                        return False
                else:
                    logger.info(f"📨 기타 응답: {response_data}")
                    # 추가 응답 대기
                    response2 = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    response_data2 = json.loads(response2)
                    logger.info(f"📨 두 번째 응답: {response_data2}")
                    
            except asyncio.TimeoutError:
                logger.error("⏰ 응답 타임아웃 (30초)")
                return False
                
    except Exception as e:
        logger.error(f"❌ WebSocket 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 WebSocket TTS 테스트 시작")
    result = asyncio.run(test_websocket_tts())
    if result:
        logger.info("🎉 WebSocket TTS 테스트 완전 성공!")
    else:
        logger.error("💥 WebSocket TTS 테스트 실패!")
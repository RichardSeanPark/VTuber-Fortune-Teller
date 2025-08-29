#!/usr/bin/env python3
"""
Complete flow test for fortune request and TTS debugging
Tests the complete message flow from WebSocket to TTS to find the actual root cause
"""

import asyncio
import json
import websockets
import logging
import time
import requests
import uuid

# Setup logging to see our test output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fortune_request():
    """Test complete fortune request flow with detailed logging"""
    
    # 1. Use a simple test session_id (ChatService will auto-create if needed)
    session_id = "test-session-debug-flow"
    
    logger.info(f"🆔 사용할 세션 ID: {session_id}")
    
    try:
        # 2. Connect directly to WebSocket 
        uri = f"ws://localhost:8000/ws/chat/{session_id}"
        logger.info(f"🔗 WebSocket 연결을 시도합니다: {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket 연결 성공!")
            
            # 3. Send fortune request - this should trigger our debugging logs
            fortune_message = {
                "type": "text_message",
                "data": {
                    "type": "text", 
                    "message": "오늘 운세 봐주세요"  # This should trigger fortune request
                }
            }
            
            logger.info(f"📤 운세 요청 메시지 전송: {fortune_message}")
            await websocket.send(json.dumps(fortune_message))
            
            # 4. Listen for all responses for 30 seconds to catch all debugging info
            timeout = 30
            start_time = time.time()
            response_count = 0
            
            logger.info(f"⏰ {timeout}초 동안 응답을 기다립니다...")
            
            while time.time() - start_time < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_count += 1
                    response_data = json.loads(response)
                    logger.info(f"📨 응답 #{response_count}: {response_data}")
                    
                    # Check if this is a TTS response
                    if response_data.get("type") == "tts_audio":
                        logger.info("🎵 TTS 오디오 응답을 받았습니다!")
                        audio_data = response_data.get("data", {})
                        logger.info(f"   - 오디오 길이: {len(audio_data.get('audio_data', ''))}")
                        logger.info(f"   - 음성 텍스트: {audio_data.get('text', 'N/A')}")
                        logger.info(f"   - TTS 제공자: {audio_data.get('provider', 'N/A')}")
                        
                    # Check for error responses
                    elif response_data.get("type") == "error":
                        logger.error(f"❌ 에러 응답: {response_data}")
                        
                except asyncio.TimeoutError:
                    # Continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.error("❌ WebSocket 연결이 닫혔습니다")
                    break
                except Exception as e:
                    logger.error(f"❌ 응답 처리 중 에러: {e}")
                    continue
            
            logger.info(f"✅ 테스트 완료. 총 {response_count}개의 응답을 받았습니다.")
            
    except Exception as e:
        logger.error(f"❌ 전체 테스트 에러: {e}")

if __name__ == "__main__":
    logger.info("🚀 Fortune VTuber 완전 플로우 테스트 시작")
    asyncio.run(test_fortune_request())
    logger.info("🏁 테스트 완료")
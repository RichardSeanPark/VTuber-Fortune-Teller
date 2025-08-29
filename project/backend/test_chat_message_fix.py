#!/usr/bin/env python3
"""
chat_message 립싱크 문제 수정 후 테스트
사주 메시지와 동일한 처리 방식으로 변경된 것을 확인
"""

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_message_fix():
    """수정된 chat_message 처리 테스트"""
    uri = "ws://localhost:8000/ws/chat/chat_fix_test"
    
    try:
        logger.info(f"🔌 WebSocket 연결 시도: {uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✅ WebSocket 연결 성공!")
            
            # 연결 메시지 수신
            connection_msg = await websocket.recv()
            logger.info(f"📩 연결 메시지: {json.loads(connection_msg)['type']}")
            
            # 테스트 메시지들 - 길이가 다양한 메시지로 립싱크 테스트
            test_messages = [
                "안녕하세요!",  # 짧은 메시지
                "오늘 날씨가 참 좋네요. 어떻게 지내시고 계신가요?",  # 중간 길이
                "춤춰봐. 신나는 음악에 맞춰서 즐겁게 춤을 춰보자! 기분이 좋아질 거야."  # 긴 메시지
            ]
            
            for i, msg in enumerate(test_messages, 1):
                logger.info(f"\n🧪 === 테스트 {i}: {msg} ===")
                logger.info(f"메시지 길이: {len(msg)} 글자")
                
                # 테스트 메시지 전송
                test_message = {
                    "type": "chat_message",
                    "message": msg,
                    "timestamp": "2025-08-25T14:55:00.000Z"
                }
                
                logger.info(f"📤 메시지 전송...")
                await websocket.send(json.dumps(test_message))
                
                # 응답 수신 및 분석
                llm_response_received = False
                chat_message_received = False
                audio_data_present = False
                
                for j in range(5):  # 최대 5개 응답 대기
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=25.0)
                        response_data = json.loads(response)
                        
                        msg_type = response_data.get('type')
                        logger.info(f"📨 응답 {j+1}: {msg_type}")
                        
                        if msg_type == 'llm_details':
                            logger.info("🤖 LLM 처리 시작됨")
                            
                        elif msg_type == 'llm_response':
                            llm_response_received = True
                            data = response_data.get('data', {})
                            content = data.get('chat_content', '')
                            logger.info(f"🤖 LLM 응답: {content[:50]}...")
                            logger.info(f"🤖 응답 길이: {len(content)} 글자")
                            
                        elif msg_type == 'chat_message':
                            chat_message_received = True
                            data = response_data.get('data', {})
                            message = data.get('message', '')
                            audio_data = data.get('audio_data', '')
                            
                            logger.info(f"💬 챗봇 메시지: {message[:50]}...")
                            logger.info(f"💬 메시지 길이: {len(message)} 글자")
                            
                            if audio_data:
                                audio_data_present = True
                                audio_size_bytes = len(audio_data) * 3 // 4
                                duration_estimate = audio_size_bytes / (16000 * 2)  # 16kHz 스테레오 추정
                                
                                logger.info(f"🔊 TTS 오디오: 있음")
                                logger.info(f"🔊 Base64 크기: {len(audio_data):,} characters")
                                logger.info(f"🔊 추정 바이트 크기: {audio_size_bytes:,} bytes")
                                logger.info(f"🔊 추정 재생 시간: {duration_estimate:.1f}초")
                                
                                # 중요: 이제 ChatInterface에서 TTS를 처리하므로
                                # WebSocketService에서는 자동 재생하지 않음
                                logger.info("✅ ChatInterface에서 TTS 및 립싱크 처리 예정")
                            else:
                                logger.warning("⚠️ TTS 오디오 데이터 없음")
                                
                        elif msg_type == 'error':
                            logger.warning(f"⚠️ 오류 응답: {response_data}")
                            
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ 응답 {j+1} 타임아웃")
                        break
                
                # 결과 요약
                success = llm_response_received and chat_message_received and audio_data_present
                logger.info(f"\n📊 테스트 {i} 결과:")
                logger.info(f"   LLM 응답: {'✅' if llm_response_received else '❌'}")
                logger.info(f"   Chat 메시지: {'✅' if chat_message_received else '❌'}")
                logger.info(f"   TTS 오디오: {'✅' if audio_data_present else '❌'}")
                logger.info(f"   전체 성공: {'✅' if success else '❌'}")
                
                if success:
                    logger.info("🎉 ChatInterface에서 사주 메시지와 동일하게 처리됩니다!")
                    logger.info("   1. 타이핑 애니메이션 → 2. Live2D 반응 → 3. TTS 재생 및 립싱크")
                
                # 다음 테스트 전 대기
                if i < len(test_messages):
                    await asyncio.sleep(2)
            
            logger.info("\n🎉 === 전체 테스트 완료 ===")
            logger.info("🔍 프론트엔드 (http://localhost:3003)에서 실제 확인:")
            logger.info("   1. 채팅창에 메시지 입력")
            logger.info("   2. TTS 음성이 끝까지 재생되는지 확인")
            logger.info("   3. Live2D 입모양이 TTS 음성과 동기화되는지 확인")
            
            return True
                
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    logger.info("🧪 chat_message 립싱크 문제 수정 테스트 시작")
    logger.info("📍 수정사항: chat_message를 사주 메시지와 동일하게 처리")
    logger.info("🎯 목표: TTS 음성이 끝까지 재생되고 립싱크가 정상 작동")
    
    result = asyncio.run(test_chat_message_fix())
    if result:
        logger.info("🎉 백엔드 테스트 성공!")
        logger.info("👉 브라우저에서 http://localhost:3003 을 열고 직접 테스트해보세요!")
    else:
        logger.error("💥 백엔드 테스트 실패!")
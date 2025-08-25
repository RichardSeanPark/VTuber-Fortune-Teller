#!/usr/bin/env python3
"""
WebSocket 채팅 테스트 스크립트

채팅 메시지를 보내서 LLM 호출이 되는지 확인합니다.
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_websocket_chat():
    """WebSocket 채팅 테스트"""
    session_id = "test_session_chat_llm"
    ws_url = f"ws://localhost:8000/ws/chat/{session_id}"
    
    print("WebSocket 채팅 LLM 호출 테스트")
    print("=" * 50)
    print(f"연결 URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 테스트 메시지들
            test_messages = [
                {
                    "type": "chat_message",
                    "message": "안녕하세요! 오늘의 운세가 궁금해요.",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "chat_message", 
                    "message": "일일운세 봐주세요",
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "type": "fortune_request",
                    "data": {
                        "fortune_type": "daily",
                        "question": "",
                        "additional_info": {
                            "birth_date": "1990-05-15",
                            "gender": "male",
                            "name": "테스트"
                        }
                    }
                }
            ]
            
            for i, test_message in enumerate(test_messages):
                print(f"\n📤 테스트 메시지 {i+1} 전송:")
                print(f"   {json.dumps(test_message, ensure_ascii=False, indent=2)}")
                
                # 메시지 전송
                await websocket.send(json.dumps(test_message, ensure_ascii=False))
                
                # 응답을 여러 번 받을 수 있으므로 루프로 처리
                responses_received = 0
                max_responses = 3  # 최대 3개의 응답 대기
                
                while responses_received < max_responses:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        response_data = json.loads(response)
                        responses_received += 1
                        
                        print(f"📥 응답 {responses_received} 받음:")
                        print(f"   타입: {response_data.get('type', 'unknown')}")
                        
                        if response_data.get('type') == 'fortune_result':
                            fortune_data = response_data.get('data', {})
                            print(f"   운세 결과: {fortune_data.get('fortune_result', {}).get('message', 'N/A')}")
                            print(f"   캐릭터 메시지: {fortune_data.get('character_message', 'N/A')}")
                            print(f"   TTS 활성화: {fortune_data.get('enable_tts', False)}")
                            print(f"   Live2D 감정: {fortune_data.get('live2d_emotion', 'N/A')}")
                            print("   ✅ LLM 호출 및 응답 생성 성공!")
                            break  # 운세 결과를 받으면 루프 종료
                        elif response_data.get('type') == 'assistant_message':
                            message = response_data.get('data', {}).get('message', 'N/A')
                            print(f"   어시스턴트 메시지: {message}")
                            print("   ✅ 채팅 응답 생성 성공!")
                        elif response_data.get('type') == 'fortune_processing':
                            print("   🔄 운세 처리 중...")
                        else:
                            print(f"   전체 응답: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    except asyncio.TimeoutError:
                        print("   ⏰ 응답 타임아웃 (10초)")
                        break
                
                # 각 메시지 간 잠시 대기
                await asyncio.sleep(2)
            
            print(f"\n🎉 테스트 완료!")
            
    except Exception as e:
        print(f"❌ WebSocket 연결 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_websocket_chat())
    sys.exit(0 if success else 1)
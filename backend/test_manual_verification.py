#!/usr/bin/env python3
"""
수동 검증 도구 - 사용자가 브라우저에서 직접 테스트할 수 있도록 가이드 제공
백엔드 WebSocket 로그를 실시간으로 모니터링하여 TTS 처리 상황 확인
"""

import asyncio
import websockets
import json
import logging
import sys
import threading
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class WebSocketMonitor:
    def __init__(self):
        self.connected = False
        self.message_count = 0
        self.tts_audio_count = 0
        
    async def monitor_websocket(self):
        """WebSocket 모니터링"""
        uri = "ws://localhost:8000/ws/chat/monitor_test"
        
        try:
            async with websockets.connect(uri) as websocket:
                self.connected = True
                logger.info("🔌 WebSocket 모니터링 연결 성공")
                
                # 연결 메시지 수신
                connection_msg = await websocket.recv()
                logger.info("📩 모니터링 연결 설정됨")
                
                # 실시간 메시지 모니터링
                while self.connected:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        await self.process_monitor_message(json.loads(message))
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("📡 WebSocket 모니터링 연결 종료")
                        break
                        
        except Exception as e:
            logger.error(f"❌ WebSocket 모니터링 실패: {e}")
            self.connected = False
    
    async def process_monitor_message(self, data):
        """모니터링 메시지 처리"""
        msg_type = data.get('type')
        
        if msg_type == 'llm_details':
            logger.info("🤖 [모니터] LLM 처리 시작됨")
            
        elif msg_type == 'llm_response':
            response_data = data.get('data', {})
            content = response_data.get('chat_content', '')
            logger.info(f"🤖 [모니터] LLM 응답 생성: {len(content)}글자")
            
        elif msg_type == 'chat_message':
            self.message_count += 1
            message_data = data.get('data', {})
            message = message_data.get('message', '')
            audio_data = message_data.get('audio_data', '')
            
            if audio_data:
                self.tts_audio_count += 1
                audio_size = len(audio_data) * 3 // 4
                logger.info(f"🔊 [모니터] TTS 오디오 생성됨 #{self.tts_audio_count}")
                logger.info(f"   메시지: {message[:50]}...")
                logger.info(f"   오디오 크기: {audio_size:,} bytes")
                logger.info("   ✅ 프론트엔드에서 재생 및 립싱크 처리됩니다!")
            else:
                logger.warning(f"⚠️ [모니터] TTS 오디오 없음 - 메시지: {message[:50]}...")
        
        elif msg_type == 'error':
            error_data = data.get('data', {})
            logger.warning(f"⚠️ [모니터] 오류: {error_data.get('message', 'Unknown error')}")
    
    def stop(self):
        """모니터링 중지"""
        self.connected = False

def print_test_guide():
    """테스트 가이드 출력"""
    print("\n" + "="*80)
    print("🧪 chat_message TTS 및 Live2D 립싱크 수동 테스트 가이드")
    print("="*80)
    print()
    print("📋 테스트 단계:")
    print("  1. 브라우저에서 http://localhost:3003 을 엽니다")
    print("  2. 개발자 도구(F12)를 열고 Console 탭으로 이동합니다")
    print("  3. 스피커 볼륨을 적절히 조정합니다")
    print("  4. 아래 테스트 메시지들을 채팅창에 입력합니다")
    print()
    print("🎯 테스트 메시지 예시:")
    print("  • 안녕하세요!")
    print("  • 춤춰봐")
    print("  • 오늘 기분이 어때?")
    print("  • 재미있는 얘기 해줘")
    print("  • 길고 복잡한 메시지: 점술에 대해 자세히 설명해주시고 어떤 종류들이 있는지도 알려주세요")
    print()
    print("✅ 확인할 사항:")
    print("  1. 타이핑 애니메이션이 표시되는지")
    print("  2. AI가 응답 메시지를 생성하는지")
    print("  3. TTS 음성이 재생되는지 (스피커에서 들림)")
    print("  4. Live2D 캐릭터의 입이 음성에 맞춰 움직이는지")
    print("  5. 음성이 끝까지 재생되는지 (중간에 멈추지 않음)")
    print()
    print("🔍 브라우저 콘솔에서 확인할 로그:")
    print("  • 💬 [ChatInterface] chat_message 수신")
    print("  • 🎵 [ChatInterface] TTS 재생 시작")
    print("  • 🎵 [ChatInterface] Live2D 입모양 애니메이션 시작")
    print("  • 🎵 [ChatInterface] TTS 재생 종료")
    print("  • 🎵 [ChatInterface] Live2D 입 닫기 완료")
    print()
    print("❌ 문제 발생 시 확인사항:")
    print("  • 브라우저 자동재생 정책으로 인한 차단 (페이지를 클릭해보세요)")
    print("  • 스피커/헤드폰 연결 및 볼륨 확인")
    print("  • WebSocket 연결 상태 확인 (연결 표시등이 녹색인지)")
    print()
    print("📊 이 스크립트에서 실시간 모니터링:")
    print("  • 백엔드에서 TTS 오디오 생성 현황")
    print("  • chat_message 전송 현황")
    print("  • 오류 발생 현황")
    print()
    print("="*80)

def run_monitoring():
    """모니터링 실행"""
    monitor = WebSocketMonitor()
    
    # 비동기 모니터링 실행
    def run_async_monitor():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(monitor.monitor_websocket())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    
    monitor_thread = threading.Thread(target=run_async_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    print_test_guide()
    
    try:
        print("🔄 WebSocket 모니터링이 시작되었습니다...")
        print("💡 브라우저에서 채팅을 시작해보세요! (Ctrl+C로 종료)")
        print()
        
        # 실시간 상태 표시
        start_time = time.time()
        while True:
            time.sleep(5)
            runtime = int(time.time() - start_time)
            print(f"\r📊 모니터링 상태: {runtime}초 경과 | 메시지: {monitor.message_count}개 | TTS: {monitor.tts_audio_count}개", end="")
            sys.stdout.flush()
            
    except KeyboardInterrupt:
        print("\n\n🔄 모니터링을 종료합니다...")
        monitor.stop()
        
    finally:
        # 최종 결과 출력
        print(f"\n📊 최종 결과:")
        print(f"  • 처리된 메시지: {monitor.message_count}개")
        print(f"  • 생성된 TTS 오디오: {monitor.tts_audio_count}개")
        print(f"  • TTS 성공률: {(monitor.tts_audio_count/monitor.message_count*100):.1f}%" if monitor.message_count > 0 else "  • 처리된 메시지 없음")
        print()
        if monitor.tts_audio_count > 0:
            print("🎉 chat_message가 사주 메시지와 동일하게 TTS 및 립싱크 처리되고 있습니다!")
        else:
            print("⚠️ TTS 오디오가 생성되지 않았습니다. 백엔드 로그를 확인해보세요.")

if __name__ == "__main__":
    logger.info("🧪 chat_message TTS 및 Live2D 립싱크 수동 검증 시작")
    logger.info("📍 프론트엔드: http://localhost:3003")
    logger.info("🎯 목표: 사용자가 직접 브라우저에서 TTS 음성과 립싱크 확인")
    
    run_monitoring()
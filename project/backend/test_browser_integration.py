#!/usr/bin/env python3
"""
브라우저 통합 테스트 - 실제 프론트엔드에서 TTS와 Live2D 동작 확인
Selenium을 사용하여 자동화 테스트 수행
"""

import asyncio
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    chrome_options.add_argument('--autoplay-policy=no-user-gesture-required')  # 자동재생 허용
    chrome_options.add_argument('--use-fake-ui-for-media-stream')
    chrome_options.add_argument('--use-fake-device-for-media-stream')
    
    # 헤드리스 모드 비활성화 (실제 브라우저에서 확인하기 위해)
    # chrome_options.add_argument('--headless')
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.warning(f"Chrome 드라이버 설정 실패: {e}")
        logger.info("Chrome이 설치되어 있고 chromedriver가 PATH에 있는지 확인하세요")
        return None

def test_frontend_tts_lipsync():
    """프론트엔드 TTS 및 립싱크 통합 테스트"""
    driver = setup_chrome_driver()
    if not driver:
        logger.error("❌ 브라우저 드라이버 초기화 실패")
        return False
    
    try:
        logger.info("🌐 프론트엔드 접속 중...")
        driver.get("http://localhost:3003")
        
        # 페이지 로딩 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chat-interface"))
        )
        logger.info("✅ 페이지 로딩 완료")
        
        # 콘솔 로그 모니터링 시작
        driver.execute_script("""
            window.testLogs = [];
            const originalLog = console.log;
            console.log = function(...args) {
                window.testLogs.push({
                    time: new Date().toISOString(),
                    message: args.join(' ')
                });
                originalLog.apply(console, args);
            };
        """)
        
        # 채팅 입력창 찾기
        message_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "message-input"))
        )
        logger.info("✅ 채팅 입력창 발견")
        
        # 테스트 메시지들
        test_messages = [
            "안녕하세요!",
            "춤춰봐",
            "오늘 기분이 어때?"
        ]
        
        for i, msg in enumerate(test_messages, 1):
            logger.info(f"\n🧪 === 브라우저 테스트 {i}: {msg} ===")
            
            # 메시지 입력
            message_input.clear()
            message_input.send_keys(msg)
            logger.info(f"✅ 메시지 입력됨: {msg}")
            
            # 전송 버튼 클릭 또는 Enter
            message_input.send_keys(Keys.RETURN)
            logger.info("✅ 메시지 전송됨")
            
            # 응답 대기 (타이핑 애니메이션 확인)
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "typing"))
                )
                logger.info("✅ 타이핑 애니메이션 시작됨")
            except:
                logger.warning("⚠️ 타이핑 애니메이션을 찾을 수 없음")
            
            # AI 응답 메시지 대기
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".message.ai"))
                )
                logger.info("✅ AI 응답 메시지 표시됨")
                
                # 최신 AI 메시지 가져오기
                ai_messages = driver.find_elements(By.CSS_SELECTOR, ".message.ai")
                if ai_messages:
                    latest_message = ai_messages[-1]
                    message_text = latest_message.find_element(By.TAG_NAME, "p").text
                    logger.info(f"📝 AI 응답: {message_text[:50]}...")
                
            except Exception as e:
                logger.error(f"❌ AI 응답 메시지 대기 실패: {e}")
                continue
            
            # 콘솔 로그에서 TTS 관련 로그 확인
            time.sleep(3)  # TTS 처리 대기
            logs = driver.execute_script("return window.testLogs;")
            
            # TTS 관련 로그 분석
            tts_logs = [log for log in logs if 'TTS' in log['message'] or 'Live2D' in log['message'] or '🔊' in log['message'] or '🎵' in log['message']]
            
            logger.info(f"📊 TTS 관련 로그 {len(tts_logs)}개 발견:")
            for log in tts_logs[-10:]:  # 최근 10개만 표시
                logger.info(f"   {log['message']}")
            
            # 중요 로그 확인
            chat_message_received = any('chat_message' in log['message'] for log in logs)
            tts_play_start = any('TTS 재생 시작' in log['message'] or 'ttsPlayStart' in log['message'] for log in logs)
            tts_play_end = any('TTS 재생 종료' in log['message'] or 'ttsPlayEnd' in log['message'] for log in logs)
            lipsync_start = any('립싱크' in log['message'] or 'playLipSync' in log['message'] for log in logs)
            
            logger.info(f"\n📊 테스트 {i} 결과:")
            logger.info(f"   chat_message 수신: {'✅' if chat_message_received else '❌'}")
            logger.info(f"   TTS 재생 시작: {'✅' if tts_play_start else '❌'}")
            logger.info(f"   TTS 재생 종료: {'✅' if tts_play_end else '❌'}")
            logger.info(f"   립싱크 동작: {'✅' if lipsync_start else '❌'}")
            
            success = chat_message_received and (tts_play_start or lipsync_start)
            logger.info(f"   전체 성공: {'✅' if success else '❌'}")
            
            if success:
                logger.info("🎉 TTS와 Live2D 립싱크가 정상 작동 중입니다!")
            else:
                logger.warning("⚠️ TTS 또는 립싱크에 문제가 있을 수 있습니다")
            
            # 다음 테스트 전 대기 (오디오 재생 완료 대기)
            if i < len(test_messages):
                logger.info("⏳ 다음 테스트 전 대기 중...")
                time.sleep(5)
        
        logger.info("\n🎉 === 브라우저 통합 테스트 완료 ===")
        logger.info("🔍 브라우저가 열려있습니다. 직접 테스트해보세요!")
        logger.info("   1. 채팅창에 메시지 입력")
        logger.info("   2. 스피커에서 음성이 나오는지 확인")
        logger.info("   3. Live2D 캐릭터의 입이 움직이는지 확인")
        logger.info("   4. 개발자 도구(F12) → Console에서 로그 확인")
        
        # 사용자가 직접 테스트할 수 있도록 잠시 대기
        input("\n👉 브라우저에서 직접 테스트 후 Enter를 눌러 종료하세요...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 브라우저 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        logger.info("🔄 브라우저 종료 중...")
        driver.quit()

if __name__ == "__main__":
    logger.info("🧪 브라우저 통합 테스트 시작")
    logger.info("📍 프론트엔드: http://localhost:3003")
    logger.info("🎯 목표: 실제 브라우저에서 TTS 및 Live2D 립싱크 확인")
    logger.info("⚠️ Chrome 브라우저와 chromedriver가 필요합니다")
    
    try:
        result = test_frontend_tts_lipsync()
        if result:
            logger.info("🎉 브라우저 통합 테스트 완료!")
        else:
            logger.error("💥 브라우저 통합 테스트 실패!")
    except KeyboardInterrupt:
        logger.info("🔄 사용자가 테스트를 중단했습니다")
    except Exception as e:
        logger.error(f"💥 테스트 실행 중 오류: {e}")
        logger.info("💡 Chrome이 설치되어 있지 않거나 chromedriver를 찾을 수 없습니다")
        logger.info("   sudo apt-get install chromium-browser")
        logger.info("   또는 pip install chromedriver-binary")
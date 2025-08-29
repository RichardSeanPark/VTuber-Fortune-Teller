#!/usr/bin/env python3
"""
타로 제거 검증 테스트
백엔드에서 타로 관련 코드가 제대로 제거되었는지 확인
"""

import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_tarot_removal():
    """타로 제거 확인 테스트"""
    logger.info("🔍 타로 제거 검증 테스트")
    
    from fortune_vtuber.services.chat_service import ChatService, MessageIntent
    
    # MessageIntent에 TAROT_FORTUNE이 없는지 확인
    logger.info("📋 MessageIntent enum 확인:")
    intent_values = [intent.value for intent in MessageIntent]
    logger.info(f"   사용 가능한 의도들: {intent_values}")
    
    if "tarot_fortune" in intent_values:
        logger.error("   ❌ TAROT_FORTUNE이 여전히 존재함")
    else:
        logger.info("   ✅ TAROT_FORTUNE이 성공적으로 제거됨")
    
    # 타로 관련 메시지 의도 분석 테스트
    chat_service = ChatService()
    
    tarot_messages = [
        "타로 카드 뽑아줘",
        "타로로 운세 봐주세요", 
        "타로 점 부탁해",
        "카드로 미래를 알려줘"
    ]
    
    logger.info("\n🎯 타로 메시지 의도 분석 테스트:")
    for message in tarot_messages:
        try:
            intent = await chat_service._analyze_intent(message)
            logger.info(f"   '{message}' → {intent.value}")
            
            # 타로 관련 의도가 아니어야 함
            if intent.value == "tarot_fortune":
                logger.error(f"     ❌ 여전히 타로 의도로 인식됨")
            else:
                logger.info(f"     ✅ 타로 의도가 아닌 '{intent.value}'로 인식됨")
        except Exception as e:
            logger.error(f"     ❌ 오류: {e}")
    
    # 다른 운세 메시지들이 제대로 인식되는지 확인
    logger.info("\n🔮 다른 운세 메시지 의도 분석 테스트:")
    fortune_messages = [
        ("연애운이 궁금해", "fortune_request"),
        ("오늘 운세 알려줘", "fortune_request"), 
        ("내 별자리 운세는?", "zodiac_fortune"),
        ("사주 봐줘", "oriental_fortune")
    ]
    
    for message, expected_category in fortune_messages:
        try:
            intent = await chat_service._analyze_intent(message)
            logger.info(f"   '{message}' → {intent.value}")
            
            # 운세 관련 의도로 인식되어야 함
            if intent.value in ["fortune_request", "daily_fortune", "zodiac_fortune", "oriental_fortune"]:
                logger.info(f"     ✅ 운세 의도로 정상 인식됨")
            else:
                logger.warning(f"     ⚠️ 운세 의도가 아닌 '{intent.value}'로 인식됨")
        except Exception as e:
            logger.error(f"     ❌ 오류: {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("🎯 타로 제거 검증 테스트")
    logger.info("=" * 60)
    
    asyncio.run(test_tarot_removal())
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 타로 제거 검증 완료")
    logger.info("=" * 60)
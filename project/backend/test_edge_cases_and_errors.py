#!/usr/bin/env python3
"""
엣지 케이스와 에러 처리 테스트
실제 운영 환경에서 발생 가능한 예외 상황 검증
"""

import asyncio
import json
import logging
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_edge_cases():
    """엣지 케이스 테스트"""
    logger.info("🔍 엣지 케이스 테스트 시작")
    
    from fortune_vtuber.services.chat_service import ChatService, MessageIntent
    from sqlalchemy.orm import Session
    
    chat_service = ChatService()
    db = MagicMock(spec=Session)
    websocket = AsyncMock()
    session_id = "edge-test"
    
    # 테스트 케이스
    edge_cases = [
        {
            "name": "빈 메시지",
            "message": "",
            "should_process": False
        },
        {
            "name": "공백만 있는 메시지",
            "message": "   ",
            "should_process": False
        },
        {
            "name": "매우 짧은 메시지",
            "message": "ㅎ",
            "should_process": True
        },
        {
            "name": "특수문자만",
            "message": "!@#$%",
            "should_process": True
        },
        {
            "name": "이모지 포함",
            "message": "오늘 운세 알려줘 🔮✨",
            "should_process": True
        },
        {
            "name": "초장문 메시지",
            "message": "안녕하세요 " * 100,  # 500자
            "should_process": True
        },
        {
            "name": "혼합 운세 요청",
            "message": "타로도 보고 별자리도 봐줘",
            "should_process": True
        },
        {
            "name": "오타가 있는 운세",
            "message": "오늘운세알려죠",
            "should_process": True
        }
    ]
    
    results = []
    for test_case in edge_cases:
        try:
            logger.info(f"테스트: {test_case['name']}")
            
            # handle_chat_message 호출
            await chat_service.handle_chat_message(db, session_id, websocket, {
                "message": test_case["message"]
            })
            
            # 처리 여부 확인
            if websocket.send_json.called:
                logger.info(f"  ✅ 처리됨")
                results.append({"test": test_case["name"], "result": "processed"})
            else:
                logger.info(f"  ⏭️ 건너뜀")
                results.append({"test": test_case["name"], "result": "skipped"})
                
            # 호출 초기화
            websocket.send_json.reset_mock()
            
        except Exception as e:
            logger.error(f"  ❌ 오류: {e}")
            results.append({"test": test_case["name"], "result": "error", "error": str(e)})
    
    # 결과 요약
    logger.info("\n📊 엣지 케이스 테스트 결과:")
    for result in results:
        status = "✅" if result["result"] == "processed" else "❌" if result["result"] == "error" else "⏭️"
        logger.info(f"  {status} {result['test']}: {result['result']}")

async def test_error_recovery():
    """에러 복구 테스트"""
    logger.info("\n🚨 에러 복구 테스트 시작")
    
    from fortune_vtuber.services.chat_service import ChatService
    from sqlalchemy.orm import Session
    
    chat_service = ChatService()
    db = MagicMock(spec=Session)
    websocket = AsyncMock()
    session_id = "error-test"
    
    # 에러 시나리오
    error_scenarios = [
        {
            "name": "DB 커밋 실패",
            "setup": lambda: setattr(db, 'commit', MagicMock(side_effect=Exception("DB Error"))),
            "message": "안녕하세요"
        },
        {
            "name": "WebSocket 전송 실패",
            "setup": lambda: setattr(websocket, 'send_json', AsyncMock(side_effect=Exception("WebSocket Error"))),
            "message": "오늘 운세는?"
        },
        {
            "name": "세션 조회 실패",
            "setup": lambda: setattr(db.query.return_value.filter.return_value, 'first', MagicMock(side_effect=Exception("Query Error"))),
            "message": "타로 카드 뽑아줘"
        }
    ]
    
    for scenario in error_scenarios:
        try:
            logger.info(f"시나리오: {scenario['name']}")
            
            # 에러 상황 설정
            scenario["setup"]()
            
            # 메시지 처리 시도
            await chat_service.handle_chat_message(db, session_id, websocket, {
                "message": scenario["message"]
            })
            
            logger.info(f"  ✅ 에러 처리됨 (graceful degradation)")
            
        except Exception as e:
            logger.info(f"  ⚠️ 예외 발생: {type(e).__name__}: {e}")
        
        # 원상 복구
        db = MagicMock(spec=Session)
        websocket = AsyncMock()

async def test_concurrent_requests():
    """동시 요청 처리 테스트"""
    logger.info("\n🔄 동시 요청 처리 테스트")
    
    from fortune_vtuber.services.chat_service import ChatService
    from sqlalchemy.orm import Session
    
    chat_service = ChatService()
    
    # 동시에 5개 요청 생성
    async def process_message(user_id: int, message: str):
        db = MagicMock(spec=Session)
        websocket = AsyncMock()
        session_id = f"user-{user_id}"
        
        try:
            start = datetime.now()
            await chat_service.handle_chat_message(db, session_id, websocket, {
                "message": message
            })
            elapsed = (datetime.now() - start).total_seconds()
            logger.info(f"  User {user_id}: {elapsed:.2f}초")
            return {"user": user_id, "time": elapsed, "status": "success"}
        except Exception as e:
            logger.error(f"  User {user_id}: 실패 - {e}")
            return {"user": user_id, "status": "error", "error": str(e)}
    
    # 동시 실행
    messages = [
        "오늘 운세 알려줘",
        "타로 카드 뽑아줘",
        "내 별자리 운세는?",
        "사주 봐줘",
        "안녕하세요"
    ]
    
    tasks = [
        process_message(i, msg) 
        for i, msg in enumerate(messages, 1)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # 결과 분석
    success_count = sum(1 for r in results if r["status"] == "success")
    avg_time = sum(r.get("time", 0) for r in results if "time" in r) / max(success_count, 1)
    
    logger.info(f"\n📊 동시 처리 결과:")
    logger.info(f"  성공: {success_count}/{len(results)}")
    logger.info(f"  평균 처리 시간: {avg_time:.2f}초")
    
    if success_count == len(results):
        logger.info("  ✅ 모든 동시 요청 처리 성공")
    else:
        logger.warning(f"  ⚠️ {len(results) - success_count}개 요청 실패")

async def test_memory_cleanup():
    """메모리 정리 테스트"""
    logger.info("\n🧹 메모리 정리 테스트")
    
    from fortune_vtuber.services.chat_service import ChatService
    import gc
    import tracemalloc
    
    # 메모리 추적 시작
    tracemalloc.start()
    
    chat_service = ChatService()
    db = MagicMock()
    
    # 초기 메모리
    snapshot1 = tracemalloc.take_snapshot()
    
    # 100개 메시지 처리
    for i in range(100):
        websocket = AsyncMock()
        await chat_service.handle_chat_message(db, f"session-{i}", websocket, {
            "message": f"테스트 메시지 {i}"
        })
    
    # 가비지 컬렉션
    gc.collect()
    
    # 최종 메모리
    snapshot2 = tracemalloc.take_snapshot()
    
    # 메모리 증가량 분석
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    total_diff = sum(stat.size_diff for stat in top_stats)
    logger.info(f"  메모리 증가: {total_diff / 1024 / 1024:.2f} MB")
    
    if total_diff < 10 * 1024 * 1024:  # 10MB 미만
        logger.info("  ✅ 메모리 누수 없음")
    else:
        logger.warning("  ⚠️ 메모리 누수 가능성")
    
    tracemalloc.stop()

if __name__ == "__main__":
    logger.info("="*60)
    logger.info("🔬 엣지 케이스 및 에러 처리 테스트")
    logger.info("="*60)
    
    # 각 테스트 실행
    asyncio.run(test_edge_cases())
    asyncio.run(test_error_recovery())
    asyncio.run(test_concurrent_requests())
    asyncio.run(test_memory_cleanup())
    
    logger.info("\n" + "="*60)
    logger.info("✅ 모든 추가 테스트 완료")
    logger.info("="*60)
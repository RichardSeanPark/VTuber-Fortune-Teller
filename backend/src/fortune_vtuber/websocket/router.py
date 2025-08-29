"""
WebSocket Router Module - WebSocket 엔드포인트 통합

실시간 채팅, Live2D 상태 동기화, 시스템 모니터링, TTS 연동
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session

from .chat_websocket import router as chat_ws_router
from .live2d_websocket import get_websocket_manager
from .tts_live2d_handler import tts_live2d_handler

logger = logging.getLogger(__name__)

# WebSocket 라우터 생성
ws_router = APIRouter(prefix="/ws")

# 기존 채팅 WebSocket 엔드포인트 등록
ws_router.include_router(chat_ws_router)


@ws_router.websocket("/tts/{client_id}")
async def tts_live2d_websocket_endpoint(
    websocket: WebSocket,
    client_id: str
):
    """
    TTS Live2D 실시간 WebSocket 엔드포인트 (Phase 8.4)
    
    실시간 TTS 음성 생성, Live2D 애니메이션 동기화, 감정 기반 표현,
    립싱크 데이터 스트리밍을 위한 WebSocket 연결
    """
    try:
        # TTS Live2D handler로 연결 위임
        await tts_live2d_handler.connect(websocket, client_id)
        
        # 메시지 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                raw_message = await websocket.receive_text()
                message = json.loads(raw_message)
                
                # TTS Live2D handler로 메시지 처리 위임
                await tts_live2d_handler.handle_message(websocket, client_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"TTS Live2D WebSocket client disconnected: {client_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from TTS client {client_id}: {e}")
                await tts_live2d_handler._send_error(websocket, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in TTS Live2D WebSocket message loop: {e}")
                await tts_live2d_handler._send_error(websocket, f"Message processing error: {str(e)}")
                
    except Exception as e:
        logger.error(f"TTS Live2D WebSocket connection error: {e}")
        
    finally:
        # 연결 정리
        await tts_live2d_handler.disconnect(client_id)


@ws_router.websocket("/live2d/{session_id}")
async def live2d_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    user_uuid: Optional[str] = Query(None)
):
    """
    Live2D 실시간 동기화 WebSocket 엔드포인트
    
    실시간 감정 제어, TTS 음성 합성, 립싱크, 리소스 최적화 등
    Live2D 캐릭터와 관련된 모든 실시간 기능을 담당
    """
    websocket_manager = get_websocket_manager()
    connection_id = None
    
    try:
        # WebSocket 연결
        connection_id = await websocket_manager.connect(websocket, session_id, user_uuid)
        logger.info(f"Live2D WebSocket connected: {connection_id} for session {session_id}")
        
        # 메시지 루프
        while True:
            try:
                # 클라이언트로부터 메시지 수신
                raw_message = await websocket.receive_text()
                message = json.loads(raw_message)
                
                # 메시지 처리
                await websocket_manager.handle_message(connection_id, message)
                
            except WebSocketDisconnect:
                logger.info(f"Live2D WebSocket client disconnected: {connection_id}")
                break
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON received from {connection_id}: {e}")
                await websocket_manager._send_error(connection_id, "Invalid JSON format")
            except Exception as e:
                logger.error(f"Error in Live2D WebSocket message loop: {e}")
                await websocket_manager._send_error(connection_id, f"Message processing error: {str(e)}")
                
    except Exception as e:
        logger.error(f"Live2D WebSocket connection error: {e}")
        
    finally:
        # 연결 정리
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@ws_router.websocket("/live2d/monitor")
async def live2d_monitor_websocket(websocket: WebSocket):
    """
    Live2D 시스템 모니터링 WebSocket 엔드포인트
    
    실시간 성능 메트릭, 연결 통계, 리소스 사용량 등을 모니터링
    관리자 전용 엔드포인트
    """
    try:
        await websocket.accept()
        websocket_manager = get_websocket_manager()
        
        logger.info("Live2D monitoring WebSocket connected")
        
        # 모니터링 데이터 주기적 전송
        import asyncio
        while True:
            try:
                # 연결 통계 수집
                connection_stats = websocket_manager.get_connection_stats()
                
                # 리소스 최적화 메트릭
                from ..live2d.resource_optimizer import resource_optimizer
                performance_metrics = resource_optimizer.get_performance_metrics()
                
                # TTS 캐시 통계
                from ..live2d.tts_integration import tts_service
                tts_stats = tts_service.get_cache_stats()
                
                # 종합 모니터링 데이터
                monitoring_data = {
                    "type": "monitoring_update",
                    "data": {
                        "websocket_stats": connection_stats,
                        "performance_metrics": performance_metrics,
                        "tts_stats": tts_stats,
                        "timestamp": "utcnow().isoformat()"
                    },
                    "timestamp": "utcnow().isoformat()"
                }
                
                await websocket.send_text(json.dumps(monitoring_data, ensure_ascii=False))
                
                # 10초마다 업데이트
                await asyncio.sleep(10)
                
            except WebSocketDisconnect:
                logger.info("Live2D monitoring WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error in Live2D monitoring: {e}")
                break
                
    except Exception as e:
        logger.error(f"Live2D monitoring WebSocket error: {e}")


# WebSocket 엔드포인트 상태 확인용
@ws_router.get("/live2d/status")
async def live2d_websocket_status():
    """Live2D WebSocket 시스템 상태 조회"""
    try:
        websocket_manager = get_websocket_manager()
        connection_stats = websocket_manager.get_connection_stats()
        
        from ..live2d.resource_optimizer import resource_optimizer
        performance_metrics = resource_optimizer.get_performance_metrics()
        
        from ..live2d.tts_integration import tts_service
        tts_stats = tts_service.get_cache_stats()
        
        return {
            "success": True,
            "data": {
                "websocket_system": {
                    "status": "healthy",
                    "connection_stats": connection_stats
                },
                "live2d_system": {
                    "status": "healthy",
                    "performance_metrics": performance_metrics
                },
                "tts_system": {
                    "status": "healthy",
                    "cache_stats": tts_stats
                }
            },
            "timestamp": "utcnow().isoformat()"
        }
        
    except Exception as e:
        logger.error(f"Error checking Live2D WebSocket status: {e}")
        return {
            "success": False,
            "error": {
                "code": "STATUS_CHECK_FAILED",
                "message": str(e)
            },
            "timestamp": "utcnow().isoformat()"
        }
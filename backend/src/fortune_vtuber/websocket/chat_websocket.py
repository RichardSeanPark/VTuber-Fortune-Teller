"""
WebSocket Chat Router - 실시간 채팅 WebSocket 엔드포인트

실시간 메시지 송수신, Live2D 캐릭터 상호작용
콘텐츠 필터링 및 운세 서비스 통합
"""

import asyncio
import json
import logging
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..services.chat_service import ChatService
from ..services.live2d_service import Live2DService

logger = logging.getLogger(__name__)

# Initialize services - 지연 초기화로 변경
chat_service = None

router = APIRouter()


@router.websocket("/chat/{session_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket 채팅 엔드포인트"""
    global chat_service
    try:
        # ChatService 초기화 (지연 초기화)
        if chat_service is None:
            chat_service = ChatService(database_service=db)
            await chat_service.initialize()
            logger.info("ChatService initialized in WebSocket endpoint")
        
        # WebSocket 연결 처리
        await chat_service.connect_websocket(session_id, websocket, db)
        
        logger.info(f"WebSocket chat connected: {session_id}")
        
        # 메시지 수신 루프
        while True:
            try:
                # 메시지 수신
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "error_code": "INVALID_JSON",
                            "message": "잘못된 JSON 형식입니다"
                        }
                    }, ensure_ascii=False))
                    continue
                
                # 메시지 처리
                await chat_service.handle_message(db, session_id, websocket, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket chat disconnected: {session_id}")
                break
                
            except Exception as e:
                logger.error(f"Error processing websocket message: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "error_code": "PROCESSING_ERROR",
                            "message": "메시지 처리 중 오류가 발생했습니다"
                        }
                    }, ensure_ascii=False))
                except:
                    # WebSocket이 이미 닫힌 경우
                    break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    
    finally:
        # 연결 해제 처리
        if chat_service is not None:
            await chat_service.disconnect_websocket(session_id, websocket)


@router.websocket("/live2d/{session_id}")
async def websocket_live2d_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Live2D 전용 WebSocket 엔드포인트"""
    try:
        await websocket.accept()
        
        # Live2D 서비스에 WebSocket 등록
        live2d_service = Live2DService()
        await live2d_service.register_websocket(session_id, websocket)
        
        logger.info(f"WebSocket Live2D connected: {session_id}")
        
        # 연결 확인 메시지
        await websocket.send_text(json.dumps({
            "type": "live2d_connected",
            "data": {
                "session_id": session_id,
                "character_name": "미라",
                "status": "ready"
            }
        }, ensure_ascii=False))
        
        # 연결 유지 루프
        while True:
            try:
                # Ping 메시지나 클라이언트 메시지 수신
                data = await websocket.receive_text()
                
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type", "")
                    
                    if message_type == "ping":
                        # Ping 응답
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "data": {
                                "timestamp": message_data.get("data", {}).get("timestamp")
                            }
                        }, ensure_ascii=False))
                    
                    elif message_type == "get_status":
                        # 현재 상태 요청
                        try:
                            status = await live2d_service.get_session_status(db, session_id)
                            await websocket.send_text(json.dumps({
                                "type": "status_response",
                                "data": status
                            }, ensure_ascii=False))
                        except Exception as e:
                            logger.warning(f"Failed to get Live2D status: {e}")
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received on Live2D WebSocket: {data}")
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket Live2D disconnected: {session_id}")
                break
                
            except Exception as e:
                logger.error(f"Error in Live2D WebSocket: {e}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "error_code": "WEBSOCKET_ERROR",
                            "message": "WebSocket 오류가 발생했습니다"
                        }
                    }, ensure_ascii=False))
                except:
                    break
    
    except Exception as e:
        logger.error(f"Live2D WebSocket connection error: {e}")
    
    finally:
        # 연결 해제 처리
        await live2d_service.unregister_websocket(session_id, websocket)


# WebSocket 통합 상태 확인 엔드포인트
@router.websocket("/status/{session_id}")
async def websocket_status_endpoint(
    websocket: WebSocket,
    session_id: str,
    db: Session = Depends(get_db)
):
    """WebSocket 상태 확인 전용 엔드포인트"""
    try:
        await websocket.accept()
        
        logger.info(f"WebSocket status connected: {session_id}")
        
        # 초기 상태 전송
        try:
            # Chat 서비스 상태
            chat_history = await chat_service.get_chat_history(db, session_id, 5)
            
            # Live2D 서비스 상태
            live2d_service = Live2DService()
            live2d_status = await live2d_service.get_session_status(db, session_id)
            
            # 통합 상태 전송
            status_data = {
                "session_id": session_id,
                "chat_status": {
                    "active": session_id in chat_service.active_connections,
                    "recent_messages": len(chat_history),
                    "connections": len(chat_service.active_connections.get(session_id, set()))
                },
                "live2d_status": live2d_status,
                "timestamp": chat_history[0]["created_at"] if chat_history else None
            }
            
            await websocket.send_text(json.dumps({
                "type": "status_update",
                "data": status_data
            }, ensure_ascii=False))
            
        except Exception as e:
            logger.warning(f"Failed to get initial status: {e}")
        
        # 상태 모니터링 루프
        while True:
            try:
                # 주기적 상태 업데이트 또는 클라이언트 요청 처리
                try:
                    # 30초 타임아웃으로 메시지 대기
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    
                    try:
                        message_data = json.loads(data)
                        message_type = message_data.get("type", "")
                        
                        if message_type == "request_status":
                            # 상태 업데이트 요청 처리
                            chat_history = await chat_service.get_chat_history(db, session_id, 5)
                            live2d_status = await live2d_service.get_session_status(db, session_id)
                            
                            status_data = {
                                "session_id": session_id,
                                "chat_status": {
                                    "active": session_id in chat_service.active_connections,
                                    "recent_messages": len(chat_history),
                                    "connections": len(chat_service.active_connections.get(session_id, set()))
                                },
                                "live2d_status": live2d_status,
                                "timestamp": chat_history[0]["created_at"] if chat_history else None
                            }
                            
                            await websocket.send_text(json.dumps({
                                "type": "status_response",
                                "data": status_data
                            }, ensure_ascii=False))
                    
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON on status WebSocket: {data}")
                
                except asyncio.TimeoutError:
                    # 타임아웃 시 Ping 전송
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "data": {
                            "timestamp": asyncio.get_event_loop().time()
                        }
                    }, ensure_ascii=False))
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket status disconnected: {session_id}")
                break
                
            except Exception as e:
                logger.error(f"Error in status WebSocket: {e}")
                break
    
    except Exception as e:
        logger.error(f"Status WebSocket connection error: {e}")


# Health check WebSocket
@router.websocket("/health")
async def websocket_health_endpoint(websocket: WebSocket):
    """WebSocket 서비스 헬스 체크"""
    try:
        await websocket.accept()
        
        # 헬스 체크 정보 전송
        health_data = {
            "service": "websocket",
            "status": "healthy",
            "active_chat_sessions": len(chat_service.active_connections),
            "total_connections": sum(len(connections) for connections in chat_service.active_connections.values()),
            "timestamp": asyncio.get_event_loop().time()
        }
        
        await websocket.send_text(json.dumps({
            "type": "health_check",
            "data": health_data
        }, ensure_ascii=False))
        
        # 간단한 Echo 테스트
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                
                try:
                    message_data = json.loads(data)
                    if message_data.get("type") == "echo":
                        await websocket.send_text(json.dumps({
                            "type": "echo_response",
                            "data": message_data.get("data", {})
                        }, ensure_ascii=False))
                    
                except json.JSONDecodeError:
                    pass
                
            except asyncio.TimeoutError:
                # 헬스 체크 업데이트
                health_data["timestamp"] = asyncio.get_event_loop().time()
                health_data["active_chat_sessions"] = len(chat_service.active_connections)
                health_data["total_connections"] = sum(len(connections) for connections in chat_service.active_connections.values())
                
                await websocket.send_text(json.dumps({
                    "type": "health_update",
                    "data": health_data
                }, ensure_ascii=False))
            
            except WebSocketDisconnect:
                break
                
    except Exception as e:
        logger.error(f"Health WebSocket error: {e}")


# Message broadcasting utility (for future use)
async def broadcast_to_session(session_id: str, message: Dict[str, Any]):
    """특정 세션의 모든 연결에 메시지 브로드캐스트"""
    if session_id not in chat_service.active_connections:
        return
    
    message_text = json.dumps(message, ensure_ascii=False)
    disconnected_websockets = set()
    
    for websocket in chat_service.active_connections[session_id]:
        try:
            await websocket.send_text(message_text)
        except Exception as e:
            logger.warning(f"Failed to broadcast to websocket: {e}")
            disconnected_websockets.add(websocket)
    
    # 끊어진 연결 정리
    for websocket in disconnected_websockets:
        await chat_service.disconnect_websocket(session_id, websocket)


async def broadcast_to_all(message: Dict[str, Any]):
    """모든 활성 연결에 메시지 브로드캐스트"""
    message_text = json.dumps(message, ensure_ascii=False)
    
    for session_id in list(chat_service.active_connections.keys()):
        await broadcast_to_session(session_id, message)
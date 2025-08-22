"""
Chat API Router - 채팅 관리 REST API 엔드포인트

채팅 세션 관리, 히스토리 조회, 콘텐츠 필터링 설정
WebSocket 채팅과 연동되는 REST API
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..config.database import get_db
from ..services.chat_service import ChatService
from ..models.chat import ChatSession, ChatMessage, MessageType

logger = logging.getLogger(__name__)

# Initialize service
chat_service = ChatService()

router = APIRouter(prefix="/chat", tags=["Chat"])


# Request/Response Models
class ChatSessionCreateRequest(BaseModel):
    """채팅 세션 생성 요청 모델"""
    session_id: str = Field(..., min_length=1, max_length=36, description="세션 ID")
    user_uuid: Optional[str] = Field(None, description="사용자 UUID")
    character_name: str = Field("미라", description="캐릭터 이름")


class MessageFilterRequest(BaseModel):
    """메시지 필터링 요청 모델"""
    message: str = Field(..., min_length=1, max_length=1000, description="필터링할 메시지")
    check_only: bool = Field(False, description="검사만 수행할지 여부")


class ChatHistoryRequest(BaseModel):
    """채팅 히스토리 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    limit: int = Field(50, ge=1, le=200, description="가져올 메시지 수")
    before_id: Optional[int] = Field(None, description="이 ID 이전의 메시지들")
    message_types: Optional[List[str]] = Field(None, description="필터링할 메시지 타입들")


class SessionStatsRequest(BaseModel):
    """세션 통계 요청 모델"""
    session_ids: List[str] = Field(..., max_items=50, description="통계를 조회할 세션 ID들")


# API Endpoints
@router.post("/session",
            summary="채팅 세션 생성",
            description="새로운 채팅 세션을 생성합니다.")
async def create_chat_session(
    request: ChatSessionCreateRequest,
    db: Session = Depends(get_db)
):
    """채팅 세션 생성"""
    try:
        session_info = await chat_service.create_chat_session(
            db, request.session_id, request.user_uuid
        )
        
        return {
            "success": True,
            "data": session_info,
            "metadata": {
                "request_id": f"session_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "websocket_url": f"/ws/chat/{request.session_id}"
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in create_chat_session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_chat_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/session/{session_id}",
           summary="채팅 세션 정보 조회",
           description="특정 채팅 세션의 정보를 조회합니다.")
async def get_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """채팅 세션 정보 조회"""
    try:
        # 데이터베이스에서 세션 조회
        chat_session = ChatSession.find_by_session_id(db, session_id)
        
        if not chat_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 세션 통계 정보
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).count()
        
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).first()
        
        # 현재 연결 상태
        is_connected = session_id in chat_service.active_connections
        connection_count = len(chat_service.active_connections.get(session_id, set()))
        
        session_data = {
            "session_id": chat_session.session_id,
            "user_uuid": chat_session.user_uuid,
            "character_name": chat_session.character_name,
            "is_active": chat_session.is_active,
            "created_at": chat_session.created_at.isoformat(),
            "updated_at": chat_session.updated_at.isoformat(),
            "ended_at": chat_session.ended_at.isoformat() if chat_session.ended_at else None,
            "statistics": {
                "message_count": message_count,
                "last_message_at": last_message.created_at.isoformat() if last_message else None,
                "is_connected": is_connected,
                "connection_count": connection_count
            }
        }
        
        return {
            "success": True,
            "data": session_data,
            "metadata": {
                "request_id": f"session_info_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/history/{session_id}",
           summary="채팅 히스토리 조회",
           description="특정 세션의 채팅 히스토리를 조회합니다.")
async def get_chat_history(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="가져올 메시지 수"),
    before_id: Optional[int] = Query(None, description="이 ID 이전의 메시지들"),
    message_type: Optional[str] = Query(None, description="필터링할 메시지 타입"),
    db: Session = Depends(get_db)
):
    """채팅 히스토리 조회"""
    try:
        # 세션 존재 확인
        chat_session = ChatSession.find_by_session_id(db, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 메시지 조회 쿼리 구성
        query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        
        if before_id:
            query = query.filter(ChatMessage.id < before_id)
        
        if message_type:
            query = query.filter(ChatMessage.message_type == message_type)
        
        messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        # 메시지 포맷팅
        formatted_messages = []
        for msg in reversed(messages):  # 시간순 정렬
            formatted_msg = {
                "id": msg.id,
                "message_type": msg.message_type,
                "content": msg.content,
                "metadata": msg.metadata_dict,
                "created_at": msg.created_at.isoformat()
            }
            
            # 운세 결과인 경우 파싱
            if msg.message_type == MessageType.FORTUNE_RESULT.value:
                try:
                    import json
                    fortune_data = json.loads(msg.content)
                    formatted_msg["fortune_data"] = fortune_data
                except Exception:
                    pass
            
            formatted_messages.append(formatted_msg)
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "messages": formatted_messages,
                "count": len(formatted_messages),
                "has_more": len(messages) == limit
            },
            "metadata": {
                "request_id": f"history_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/history",
            summary="채팅 히스토리 조회 (POST)",
            description="POST 방식으로 채팅 히스토리를 조회합니다.")
async def get_chat_history_post(
    request: ChatHistoryRequest,
    db: Session = Depends(get_db)
):
    """채팅 히스토리 조회 (POST)"""
    try:
        # 세션 존재 확인
        chat_session = ChatSession.find_by_session_id(db, request.session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
        # 메시지 조회 쿼리 구성
        query = db.query(ChatMessage).filter(ChatMessage.session_id == request.session_id)
        
        if request.before_id:
            query = query.filter(ChatMessage.id < request.before_id)
        
        if request.message_types:
            query = query.filter(ChatMessage.message_type.in_(request.message_types))
        
        messages = query.order_by(ChatMessage.created_at.desc()).limit(request.limit).all()
        
        # 메시지 포맷팅
        formatted_messages = []
        for msg in reversed(messages):
            formatted_msg = {
                "id": msg.id,
                "message_type": msg.message_type,
                "content": msg.content,
                "metadata": msg.metadata_dict,
                "created_at": msg.created_at.isoformat()
            }
            formatted_messages.append(formatted_msg)
        
        return {
            "success": True,
            "data": {
                "session_id": request.session_id,
                "messages": formatted_messages,
                "count": len(formatted_messages),
                "has_more": len(messages) == request.limit,
                "filters": {
                    "message_types": request.message_types,
                    "before_id": request.before_id
                }
            },
            "metadata": {
                "request_id": f"history_post_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "POST"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_chat_history_post: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/filter",
            summary="메시지 콘텐츠 필터링",
            description="메시지의 적절성을 검사하고 필터링합니다.")
async def filter_message_content(
    request: MessageFilterRequest
):
    """메시지 콘텐츠 필터링"""
    try:
        # 콘텐츠 필터링 수행
        is_appropriate, filter_category, matched_keywords = chat_service.content_filter.filter_content(
            request.message
        )
        
        # 의도 분류
        intent = chat_service.content_filter.classify_intent(request.message)
        
        filter_result = {
            "message": request.message,
            "is_appropriate": is_appropriate,
            "filter_category": filter_category,
            "matched_keywords": matched_keywords,
            "intent": intent.value,
            "check_only": request.check_only
        }
        
        # 부적절한 내용인 경우 대안 제안
        if not is_appropriate:
            filter_result["suggestions"] = [
                "운세나 긍정적인 이야기를 해볼까요?",
                "어떤 운세가 궁금하신지 물어보세요!",
                "오늘의 운세를 확인해보시는 건 어떨까요?"
            ]
        
        return {
            "success": True,
            "data": filter_result,
            "metadata": {
                "request_id": f"filter_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in filter_message_content: {e}")
        raise HTTPException(status_code=500, detail=f"필터링 중 오류가 발생했습니다: {str(e)}")


@router.get("/sessions",
           summary="활성 채팅 세션 목록",
           description="현재 활성화된 채팅 세션들의 목록을 조회합니다.")
async def get_active_sessions(
    include_stats: bool = Query(False, description="통계 정보 포함 여부"),
    db: Session = Depends(get_db)
):
    """활성 채팅 세션 목록 조회"""
    try:
        # 메모리의 활성 세션 정보
        active_sessions = []
        
        for session_id, session_data in chat_service.session_data.items():
            session_info = {
                "session_id": session_id,
                "user_uuid": session_data.get("user_uuid"),
                "last_activity": session_data["last_activity"].isoformat(),
                "message_count": session_data.get("message_count", 0),
                "connection_count": len(chat_service.active_connections.get(session_id, set())),
                "last_intent": session_data.get("context", {}).get("last_intent", "unknown")
            }
            
            if include_stats:
                # 데이터베이스에서 추가 통계 조회
                chat_session = ChatSession.find_by_session_id(db, session_id)
                if chat_session:
                    session_info["created_at"] = chat_session.created_at.isoformat()
                    session_info["character_name"] = chat_session.character_name
            
            active_sessions.append(session_info)
        
        # 최근 활동 순으로 정렬
        active_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return {
            "success": True,
            "data": {
                "sessions": active_sessions,
                "total_active": len(active_sessions),
                "total_connections": sum(len(connections) for connections in chat_service.active_connections.values())
            },
            "metadata": {
                "request_id": f"sessions_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "include_stats": include_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_active_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/sessions/stats",
            summary="채팅 세션 통계",
            description="여러 세션의 통계 정보를 일괄 조회합니다.")
async def get_sessions_stats(
    request: SessionStatsRequest,
    db: Session = Depends(get_db)
):
    """채팅 세션 통계"""
    try:
        session_stats = []
        
        for session_id in request.session_ids:
            try:
                # 데이터베이스에서 세션 정보 조회
                chat_session = ChatSession.find_by_session_id(db, session_id)
                
                if not chat_session:
                    session_stats.append({
                        "session_id": session_id,
                        "exists": False,
                        "error": "Session not found"
                    })
                    continue
                
                # 메시지 통계
                total_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).count()
                
                user_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.message_type == MessageType.USER_TEXT.value
                ).count()
                
                fortune_results = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.message_type == MessageType.FORTUNE_RESULT.value
                ).count()
                
                filtered_messages = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.message_type == MessageType.FILTERED.value
                ).count()
                
                # 최근 활동
                last_message = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.created_at.desc()).first()
                
                # 현재 연결 상태
                is_connected = session_id in chat_service.active_connections
                
                stats = {
                    "session_id": session_id,
                    "exists": True,
                    "user_uuid": chat_session.user_uuid,
                    "character_name": chat_session.character_name,
                    "is_active": chat_session.is_active,
                    "created_at": chat_session.created_at.isoformat(),
                    "last_message_at": last_message.created_at.isoformat() if last_message else None,
                    "is_connected": is_connected,
                    "connection_count": len(chat_service.active_connections.get(session_id, set())),
                    "message_stats": {
                        "total_messages": total_messages,
                        "user_messages": user_messages,
                        "fortune_results": fortune_results,
                        "filtered_messages": filtered_messages
                    }
                }
                
                session_stats.append(stats)
                
            except Exception as e:
                logger.warning(f"Error getting stats for session {session_id}: {e}")
                session_stats.append({
                    "session_id": session_id,
                    "exists": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "data": {
                "session_stats": session_stats,
                "requested_count": len(request.session_ids),
                "successful_count": len([s for s in session_stats if s.get("exists", False)])
            },
            "metadata": {
                "request_id": f"stats_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_sessions_stats: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.delete("/session/{session_id}",
              summary="채팅 세션 종료",
              description="채팅 세션을 종료하고 리소스를 정리합니다.")
async def end_chat_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """채팅 세션 종료"""
    try:
        # 데이터베이스에서 세션 비활성화
        chat_session = ChatSession.find_by_session_id(db, session_id)
        if chat_session:
            chat_session.is_active = False
            chat_session.ended_at = datetime.now()
            db.commit()
        
        # 메모리에서 세션 데이터 제거
        if session_id in chat_service.session_data:
            del chat_service.session_data[session_id]
        
        # WebSocket 연결 정리
        if session_id in chat_service.active_connections:
            # 연결된 클라이언트들에게 세션 종료 알림
            for websocket in chat_service.active_connections[session_id].copy():
                try:
                    await websocket.send_text(json.dumps({
                        "type": "session_ended",
                        "data": {
                            "session_id": session_id,
                            "reason": "session_terminated",
                            "message": "세션이 종료되었습니다."
                        }
                    }, ensure_ascii=False))
                    await websocket.close()
                except Exception:
                    pass
            
            del chat_service.active_connections[session_id]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "ended": True,
                "ended_at": datetime.now().isoformat()
            },
            "metadata": {
                "request_id": f"end_session_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in end_chat_session: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"세션 종료 중 오류가 발생했습니다: {str(e)}")


@router.post("/cleanup/inactive",
            summary="비활성 세션 정리",
            description="오래된 비활성 채팅 세션들을 정리합니다.")
async def cleanup_inactive_sessions(
    hours: int = Query(24, ge=1, le=168, description="비활성 기준 시간 (시간)"),
    db: Session = Depends(get_db)
):
    """비활성 세션 정리"""
    try:
        cleaned_count = await chat_service.cleanup_inactive_sessions(db, hours)
        
        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "cutoff_hours": hours,
                "cutoff_time": (datetime.now() - timedelta(hours=hours)).isoformat()
            },
            "metadata": {
                "request_id": f"cleanup_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 정리 중 오류가 발생했습니다: {str(e)}")


# Health check endpoint
@router.get("/health",
           summary="채팅 서비스 상태 확인",
           description="채팅 서비스의 상태를 확인합니다.")
async def chat_health_check():
    """채팅 서비스 헬스 체크"""
    try:
        # 기본 서비스 상태 확인
        active_sessions = len(chat_service.session_data)
        total_connections = sum(len(connections) for connections in chat_service.active_connections.values())
        
        # 필터 서비스 테스트
        test_message = "안녕하세요"
        is_appropriate, _, _ = chat_service.content_filter.filter_content(test_message)
        intent = chat_service.content_filter.classify_intent(test_message)
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "chat_service",
                "active_sessions": active_sessions,
                "total_connections": total_connections,
                "content_filter": {
                    "status": "operational",
                    "test_passed": is_appropriate,
                    "intent_classification": intent.value
                },
                "websocket_support": True,
                "live2d_integration": True
            },
            "metadata": {
                "request_id": f"health_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Chat service health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNHEALTHY",
                    "message": "채팅 서비스가 정상적으로 작동하지 않습니다",
                    "details": str(e)
                }
            }
        )
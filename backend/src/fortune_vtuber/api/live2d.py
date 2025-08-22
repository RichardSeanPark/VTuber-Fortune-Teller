"""
Live2D API Router - Live2D 캐릭터 제어 엔드포인트

실시간 감정/모션 제어, 운세 연동 반응, 캐릭터 상태 관리
WebSocket을 통한 실시간 동기화 지원
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..config.database import get_db
from ..services.live2d_service import Live2DService
from ..services.live2d_service import EmotionType, MotionType

logger = logging.getLogger(__name__)

# Initialize service
live2d_service = Live2DService()

router = APIRouter(prefix="/live2d", tags=["Live2D"])


# Request/Response Models
class EmotionChangeRequest(BaseModel):
    """감정 변경 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    emotion: EmotionType = Field(..., description="변경할 감정 타입")
    duration: Optional[int] = Field(None, ge=0, le=30000, description="감정 지속 시간 (ms)")


class MotionExecuteRequest(BaseModel):
    """모션 실행 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    motion: MotionType = Field(..., description="실행할 모션 타입")
    loop: Optional[bool] = Field(None, description="반복 재생 여부")
    duration: Optional[int] = Field(None, ge=0, le=60000, description="모션 지속 시간 (ms)")


class CombinedStateRequest(BaseModel):
    """감정+모션 동시 설정 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    emotion: EmotionType = Field(..., description="감정 타입")
    motion: MotionType = Field(..., description="모션 타입")
    message: Optional[str] = Field(None, max_length=500, description="함께 표시할 메시지")


class FortuneReactionRequest(BaseModel):
    """운세 반응 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    fortune_result: Dict[str, Any] = Field(..., description="운세 결과 데이터")


class SessionCreateRequest(BaseModel):
    """세션 생성 요청 모델"""
    session_id: str = Field(..., min_length=1, max_length=36, description="세션 ID")
    user_uuid: Optional[str] = Field(None, description="사용자 UUID")


# API Endpoints
@router.post("/session",
            summary="Live2D 세션 생성",
            description="새로운 Live2D 캐릭터 세션을 생성합니다.")
async def create_live2d_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """Live2D 세션 생성"""
    try:
        session_info = await live2d_service.create_live2d_session(
            db, request.session_id, request.user_uuid
        )
        
        return {
            "success": True,
            "data": session_info,
            "metadata": {
                "request_id": f"session_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "action": "session_created"
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in create_live2d_session: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_live2d_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/character/info",
           summary="캐릭터 정보 조회",
           description="Live2D 캐릭터의 기본 정보와 사용 가능한 감정/모션을 조회합니다.")
async def get_character_info():
    """캐릭터 정보 조회"""
    try:
        character_info = await live2d_service.get_character_info()
        
        return {
            "success": True,
            "data": character_info,
            "metadata": {
                "request_id": f"info_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_character_info: {e}")
        raise HTTPException(status_code=500, detail=f"캐릭터 정보 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/session/{session_id}/status",
           summary="세션 상태 조회",
           description="특정 세션의 Live2D 캐릭터 상태를 조회합니다.")
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """세션 상태 조회"""
    try:
        session_status = await live2d_service.get_session_status(db, session_id)
        
        return {
            "success": True,
            "data": session_status,
            "metadata": {
                "request_id": f"status_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id
            }
        }
        
    except ValueError as e:
        logger.warning(f"Session not found: {e}")
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"Error in get_session_status: {e}")
        raise HTTPException(status_code=500, detail=f"세션 상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/emotion",
            summary="감정 변경",
            description="Live2D 캐릭터의 감정을 변경합니다.")
async def change_emotion(
    request: EmotionChangeRequest,
    db: Session = Depends(get_db)
):
    """감정 변경"""
    try:
        result = await live2d_service.change_emotion(
            db, request.session_id, request.emotion, request.duration
        )
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"emotion_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "action": "emotion_changed",
                "emotion": request.emotion.value
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in change_emotion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in change_emotion: {e}")
        raise HTTPException(status_code=500, detail=f"감정 변경 중 오류가 발생했습니다: {str(e)}")


@router.post("/motion",
            summary="모션 실행",
            description="Live2D 캐릭터의 모션을 실행합니다.")
async def execute_motion(
    request: MotionExecuteRequest,
    db: Session = Depends(get_db)
):
    """모션 실행"""
    try:
        result = await live2d_service.execute_motion(
            db, request.session_id, request.motion, request.loop, request.duration
        )
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"motion_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "action": "motion_executed",
                "motion": request.motion.value
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in execute_motion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in execute_motion: {e}")
        raise HTTPException(status_code=500, detail=f"모션 실행 중 오류가 발생했습니다: {str(e)}")


@router.post("/state",
            summary="감정+모션 동시 설정",
            description="Live2D 캐릭터의 감정과 모션을 동시에 설정합니다.")
async def set_combined_state(
    request: CombinedStateRequest,
    db: Session = Depends(get_db)
):
    """감정+모션 동시 설정"""
    try:
        result = await live2d_service.set_combined_state(
            db, request.session_id, request.emotion, request.motion, request.message
        )
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"combined_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "action": "combined_state_set",
                "emotion": request.emotion.value,
                "motion": request.motion.value
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in set_combined_state: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in set_combined_state: {e}")
        raise HTTPException(status_code=500, detail=f"상태 설정 중 오류가 발생했습니다: {str(e)}")


@router.post("/react/fortune",
            summary="운세 반응",
            description="운세 결과에 따라 자동으로 적절한 감정과 모션을 설정합니다.")
async def react_to_fortune(
    request: FortuneReactionRequest,
    db: Session = Depends(get_db)
):
    """운세 결과에 따른 자동 반응"""
    try:
        result = await live2d_service.react_to_fortune(
            db, request.session_id, request.fortune_result
        )
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"fortune_reaction_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "action": "fortune_reaction",
                "fortune_type": request.fortune_result.get("fortune_type", "unknown")
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in react_to_fortune: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in react_to_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"운세 반응 설정 중 오류가 발생했습니다: {str(e)}")


# Quick action endpoints (GET methods for simple controls)
@router.get("/emotion/{emotion_type}",
           summary="감정 빠른 변경",
           description="GET 방식으로 감정을 빠르게 변경합니다.")
async def quick_change_emotion(
    emotion_type: EmotionType,
    session_id: str = Query(..., description="세션 ID"),
    duration: Optional[int] = Query(None, ge=0, le=30000, description="지속 시간 (ms)"),
    db: Session = Depends(get_db)
):
    """감정 빠른 변경"""
    try:
        result = await live2d_service.change_emotion(db, session_id, emotion_type, duration)
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"quick_emotion_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "GET"
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in quick_change_emotion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in quick_change_emotion: {e}")
        raise HTTPException(status_code=500, detail=f"감정 변경 중 오류가 발생했습니다: {str(e)}")


@router.get("/motion/{motion_type}",
           summary="모션 빠른 실행",
           description="GET 방식으로 모션을 빠르게 실행합니다.")
async def quick_execute_motion(
    motion_type: MotionType,
    session_id: str = Query(..., description="세션 ID"),
    loop: Optional[bool] = Query(None, description="반복 재생 여부"),
    duration: Optional[int] = Query(None, ge=0, le=60000, description="지속 시간 (ms)"),
    db: Session = Depends(get_db)
):
    """모션 빠른 실행"""
    try:
        result = await live2d_service.execute_motion(db, session_id, motion_type, loop, duration)
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"quick_motion_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "GET"
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in quick_execute_motion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in quick_execute_motion: {e}")
        raise HTTPException(status_code=500, detail=f"모션 실행 중 오류가 발생했습니다: {str(e)}")


# Administrative endpoints
@router.post("/session/{session_id}/cleanup",
            summary="세션 정리",
            description="특정 세션의 리소스를 정리합니다.")
async def cleanup_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """세션 리소스 정리"""
    try:
        # 세션 비활성화
        if session_id in live2d_service.active_sessions:
            # WebSocket 연결 정리
            if session_id in live2d_service.websocket_connections:
                del live2d_service.websocket_connections[session_id]
            
            del live2d_service.active_sessions[session_id]
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "cleaned_up": True
            },
            "metadata": {
                "request_id": f"cleanup_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 정리 중 오류가 발생했습니다: {str(e)}")


@router.post("/cleanup/inactive",
            summary="비활성 세션 일괄 정리",
            description="오래된 비활성 세션들을 일괄 정리합니다.")
async def cleanup_inactive_sessions(
    hours: int = Query(24, ge=1, le=168, description="비활성 기준 시간 (시간)"),
    db: Session = Depends(get_db)
):
    """비활성 세션 일괄 정리"""
    try:
        cleaned_count = await live2d_service.cleanup_inactive_sessions(db, hours)
        
        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "cutoff_hours": hours
            },
            "metadata": {
                "request_id": f"bulk_cleanup_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_inactive_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 정리 중 오류가 발생했습니다: {str(e)}")


@router.get("/stats",
           summary="Live2D 시스템 통계",
           description="Live2D 시스템의 현재 상태와 통계를 조회합니다.")
async def get_live2d_stats():
    """Live2D 시스템 통계"""
    try:
        active_sessions_count = len(live2d_service.active_sessions)
        websocket_connections_count = sum(
            len(connections) for connections in live2d_service.websocket_connections.values()
        )
        
        # 세션별 정보
        session_info = {}
        for session_id, session_data in live2d_service.active_sessions.items():
            live2d_session = session_data["live2d_session"]
            session_info[session_id] = {
                "emotion": live2d_session.current_emotion,
                "motion": live2d_session.current_motion,
                "websocket_count": len(session_data["websockets"]),
                "last_updated": session_data["last_updated"].isoformat(),
                "user_uuid": live2d_session.user_uuid
            }
        
        return {
            "success": True,
            "data": {
                "active_sessions": active_sessions_count,
                "websocket_connections": websocket_connections_count,
                "character_name": live2d_service.config.CHARACTER_NAME,
                "available_emotions": len(live2d_service.config.EMOTIONS),
                "available_motions": len(live2d_service.config.MOTIONS),
                "session_details": session_info
            },
            "metadata": {
                "request_id": f"stats_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_live2d_stats: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


# Frontend compatibility endpoints
@router.get("/status",
           summary="Live2D 시스템 상태",
           description="Live2D 시스템의 전체 상태를 조회합니다.")
async def get_live2d_status():
    """Live2D 시스템 상태 조회 (Frontend compatibility endpoint)"""
    try:
        # 기본 서비스 상태 확인
        character_info = await live2d_service.get_character_info()
        active_sessions = len(live2d_service.active_sessions)
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "live2d_service",
                "character_name": live2d_service.config.CHARACTER_NAME,
                "character_loaded": bool(character_info),
                "active_sessions": active_sessions,
                "websocket_ready": True,
                "emotions_available": list(live2d_service.config.EMOTIONS.keys()),
                "motions_available": list(live2d_service.config.MOTIONS.keys()),
                "models_available": ["mira"]  # Currently only one model available
            },
            "metadata": {
                "request_id": f"status_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Live2D status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Live2D 상태 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/models",
           summary="사용 가능한 Live2D 모델 목록",
           description="사용 가능한 Live2D 모델들의 정보를 조회합니다.")
async def get_available_models():
    """사용 가능한 Live2D 모델 목록 조회"""
    try:
        # Currently only one model available - "mira"
        models = {
            "mira": {
                "name": live2d_service.config.CHARACTER_NAME,
                "model_path": live2d_service.config.MODEL_PATH,
                "emotions": list(live2d_service.config.EMOTIONS.keys()),
                "motions": list(live2d_service.config.MOTIONS.keys()),
                "is_default": True
            }
        }
        
        return {
            "success": True,
            "data": {
                "models": models,
                "default_model": "mira",
                "total_count": len(models)
            },
            "metadata": {
                "request_id": f"models_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_available_models: {e}")
        raise HTTPException(status_code=500, detail=f"모델 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/config",
           summary="Live2D 시스템 설정 정보",
           description="현재 Live2D 시스템의 설정 정보를 조회합니다.")
async def get_live2d_config():
    """Live2D 시스템 설정 조회"""
    try:
        config_info = {
            "default_model": "mira",
            "default_emotion": "neutral",
            "emotion_duration": 3000,
            "motion_duration": 5000,
            "models_directory": "static/live2d",
            "character_name": live2d_service.config.CHARACTER_NAME,
            "available_emotions": list(live2d_service.config.EMOTIONS.keys()),
            "available_motions": list(live2d_service.config.MOTIONS.keys()),
            "model_config": {
                "mira": {
                    "name": live2d_service.config.CHARACTER_NAME,
                    "model_path": live2d_service.config.MODEL_PATH,
                    "emotions": live2d_service.config.EMOTIONS,
                    "motions": live2d_service.config.MOTIONS
                }
            }
        }
        
        return {
            "success": True,
            "data": config_info,
            "metadata": {
                "request_id": f"config_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_live2d_config: {e}")
        raise HTTPException(status_code=500, detail=f"설정 정보 조회 중 오류가 발생했습니다: {str(e)}")


# Health check endpoint
@router.get("/health",
           summary="Live2D 서비스 상태 확인",
           description="Live2D 서비스의 상태를 확인합니다.")
async def live2d_health_check():
    """Live2D 서비스 헬스 체크"""
    try:
        # 기본 서비스 상태 확인
        character_info = await live2d_service.get_character_info()
        active_sessions = len(live2d_service.active_sessions)
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "live2d_service", 
                "character_loaded": bool(character_info),
                "active_sessions": active_sessions,
                "websocket_ready": True,
                "emotions_available": len(live2d_service.config.EMOTIONS),
                "motions_available": len(live2d_service.config.MOTIONS)
            },
            "metadata": {
                "request_id": f"health_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Live2D service health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNHEALTHY",
                    "message": "Live2D 서비스가 정상적으로 작동하지 않습니다",
                    "details": str(e)
                }
            }
        )
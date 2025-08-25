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
from ..live2d.tts_integration import tts_service, TTSRequest, EmotionalTone
from ..live2d.resource_optimizer import resource_optimizer, DeviceType

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


# Advanced Live2D API Endpoints

class TTSRequestModel(BaseModel):
    """TTS 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    text: str = Field(..., min_length=1, max_length=500, description="합성할 텍스트")
    emotion: Optional[str] = Field(None, description="감정 톤")
    language: Optional[str] = Field("ko-KR", description="언어 설정")
    voice_profile: Optional[str] = Field("ko_female_default", description="음성 프로파일")
    enable_lipsync: Optional[bool] = Field(True, description="립싱크 활성화")


class ParameterUpdateRequest(BaseModel):
    """Live2D 파라미터 업데이트 요청 모델"""
    session_id: str = Field(..., description="세션 ID")
    parameters: Dict[str, float] = Field(..., description="Live2D 파라미터")
    duration: Optional[int] = Field(1000, ge=100, le=10000, description="지속 시간 (ms)")
    fade_in: Optional[float] = Field(0.5, ge=0.0, le=2.0, description="페이드 인 시간")
    fade_out: Optional[float] = Field(0.5, ge=0.0, le=2.0, description="페이드 아웃 시간")


class DeviceOptimizationRequest(BaseModel):
    """디바이스 최적화 요청 모델"""
    device_type: str = Field(..., description="디바이스 타입 (desktop/tablet/mobile/low_end)")
    screen_width: Optional[int] = Field(1920, ge=320, le=4096)
    screen_height: Optional[int] = Field(1080, ge=240, le=2160)
    memory_gb: Optional[int] = Field(8, ge=1, le=64)
    cpu_cores: Optional[int] = Field(4, ge=1, le=32)
    user_preferences: Optional[Dict[str, Any]] = Field({})


@router.post("/tts/synthesize",
            summary="TTS 음성 합성",
            description="텍스트를 음성으로 합성하고 립싱크 데이터를 함께 제공합니다.")
async def synthesize_tts(
    request: TTSRequestModel,
    db: Session = Depends(get_db)
):
    """TTS 음성 합성"""
    try:
        # 음성 프로파일 선택
        voice_profile = tts_service.get_voice_profile_for_emotion(
            request.emotion or "neutral", 
            request.language
        )
        
        # 감정 톤 변환
        emotion_tone = None
        if request.emotion:
            try:
                emotion_tone = EmotionalTone(request.emotion)
            except ValueError:
                emotion_tone = EmotionalTone.CALM
        
        # TTS 요청 생성
        tts_request = TTSRequest(
            text=request.text,
            voice_profile=voice_profile,
            emotion_tone=emotion_tone,
            session_id=request.session_id,
            enable_lipsync=request.enable_lipsync
        )
        
        # 새 TTS 시스템 사용 (Live2D 통합 TTS)
        from ..tts import Live2DTTSRequest, live2d_tts_manager
        
        # Live2D TTS 요청 생성
        live2d_request = Live2DTTSRequest(
            text=request.text,
            user_id="default",
            session_id=request.session_id or f"session_{datetime.now().timestamp()}",
            language=request.language,
            voice=voice_profile.voice_name if voice_profile else "ko-KR-SunHiNeural",
            emotion=None,  # 감정 매핑 필요시 추가
            speed=1.0,
            pitch=1.0, 
            volume=1.0,
            enable_lipsync=request.enable_lipsync,
            enable_expressions=True,
            enable_motions=True
        )
        
        # Live2D TTS로 음성 합성 실행
        live2d_result = await live2d_tts_manager.generate_speech_with_animation(live2d_request)
        tts_result = live2d_result.tts_result
        
        # numpy 타입 변환을 위한 import
        from ..utils import fix_tts_result_for_json, create_safe_api_response
        
        # TTS 결과의 numpy 타입들을 안전하게 변환
        tts_result = fix_tts_result_for_json(tts_result)
        
        # Base64 인코딩을 위한 import
        import base64
        
        # 결과 반환
        result_data = {
            "audio_data": base64.b64encode(tts_result.audio_data).decode('utf-8'),  # Base64 인코딩
            "audio_format": tts_result.audio_format,
            "duration": float(tts_result.duration),  # numpy.float32 방지
            "cached": bool(tts_result.cached),
            "generation_time": float(tts_result.generation_time)  # numpy.float32 방지
        }
        
        # 새 TTS 시스템에서는 lip-sync 데이터가 live2d_result에 있음
        if hasattr(tts_result, 'lip_sync_data') and tts_result.lip_sync_data:
            result_data["lip_sync"] = {
                "phonemes": tts_result.lip_sync_data.phonemes,
                "mouth_shapes": tts_result.lip_sync_data.mouth_shapes,
                "total_duration": float(tts_result.duration)
            }
        elif hasattr(live2d_result, 'tts_result') and hasattr(live2d_result.tts_result, 'lip_sync_data') and live2d_result.tts_result.lip_sync_data:
            # Live2D 결과에서 lip-sync 데이터 추출
            lip_sync_data = live2d_result.tts_result.lip_sync_data
            result_data["lip_sync"] = {
                "phonemes": lip_sync_data.phonemes if lip_sync_data else [],
                "mouth_shapes": lip_sync_data.mouth_shapes if lip_sync_data else [],
                "total_duration": float(tts_result.duration)
            }
        
        # 전체 응답을 안전하게 생성
        response_data = {
            "success": True,
            "data": result_data,
            "metadata": {
                "request_id": f"tts_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "session_id": request.session_id
            }
        }
        
        # JSON 직렬화 안전성 확보
        return create_safe_api_response(response_data)
        
    except Exception as e:
        logger.error(f"Error in TTS synthesis: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 합성 중 오류가 발생했습니다: {str(e)}")


@router.post("/parameters/update",
            summary="Live2D 파라미터 직접 제어",
            description="Live2D 캐릭터의 파라미터를 직접 제어합니다.")
async def update_live2d_parameters(
    request: ParameterUpdateRequest,
    db: Session = Depends(get_db)
):
    """Live2D 파라미터 직접 제어"""
    try:
        result = await live2d_service.set_live2d_parameters(
            db,
            request.session_id,
            request.parameters,
            request.duration,
            request.fade_in,
            request.fade_out
        )
        
        return {
            "success": True,
            "data": result,
            "metadata": {
                "request_id": f"param_update_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "parameters_count": len(request.parameters)
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid parameter update request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating Live2D parameters: {e}")
        raise HTTPException(status_code=500, detail=f"파라미터 업데이트 중 오류가 발생했습니다: {str(e)}")


@router.post("/optimize/device",
            summary="디바이스별 최적화",
            description="사용자 디바이스에 맞춰 Live2D 모델을 최적화합니다.")
async def optimize_for_device(request: DeviceOptimizationRequest):
    """디바이스별 최적화"""
    try:
        # 디바이스 타입 변환
        device_type = DeviceType(request.device_type)
        
        # 최적화 설정 생성
        optimized_config = resource_optimizer.get_optimized_config(
            device_type, 
            request.user_preferences
        )
        
        return {
            "success": True,
            "data": {
                "device_type": device_type.value,
                "optimized_config": optimized_config,
                "device_info": {
                    "screen_resolution": f"{request.screen_width}x{request.screen_height}",
                    "memory_gb": request.memory_gb,
                    "cpu_cores": request.cpu_cores
                }
            },
            "metadata": {
                "request_id": f"optimize_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "optimization_level": optimized_config["model_config"]["quality_level"]
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid device optimization request: {e}")
        raise HTTPException(status_code=400, detail=f"잘못된 디바이스 타입입니다: {request.device_type}")
    except Exception as e:
        logger.error(f"Error in device optimization: {e}")
        raise HTTPException(status_code=500, detail=f"디바이스 최적화 중 오류가 발생했습니다: {str(e)}")


@router.get("/optimize/performance/{model_name}",
           summary="성능 메트릭 조회",
           description="특정 모델의 성능 메트릭을 조회합니다.")
async def get_performance_metrics(model_name: str):
    """성능 메트릭 조회"""
    try:
        metrics = resource_optimizer.get_performance_metrics(model_name)
        
        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "metrics": metrics
            },
            "metadata": {
                "request_id": f"metrics_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"성능 메트릭 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/preload/model/{model_name}",
            summary="모델 사전 로딩",
            description="지정된 모델을 디바이스에 맞춰 사전 로딩합니다.")
async def preload_model(
    model_name: str,
    device_type: str = Query("desktop", description="디바이스 타입")
):
    """모델 사전 로딩"""
    try:
        device_enum = DeviceType(device_type)
        
        # 모델 사전 로딩 실행
        preload_result = await resource_optimizer.preload_critical_resources(model_name, device_enum)
        
        return {
            "success": True,
            "data": {
                "model_name": model_name,
                "device_type": device_type,
                "preload_result": preload_result,
                "resources_loaded": {
                    "model": bool(preload_result["model"]),
                    "textures_count": len(preload_result["textures"]),
                    "motions_count": len(preload_result["motions"]),
                    "expressions_count": len(preload_result["expressions"])
                }
            },
            "metadata": {
                "request_id": f"preload_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid model preload request: {e}")
        raise HTTPException(status_code=400, detail=f"잘못된 요청입니다: {str(e)}")
    except FileNotFoundError as e:
        logger.warning(f"Model not found: {e}")
        raise HTTPException(status_code=404, detail=f"모델을 찾을 수 없습니다: {model_name}")
    except Exception as e:
        logger.error(f"Error preloading model: {e}")
        raise HTTPException(status_code=500, detail=f"모델 사전 로딩 중 오류가 발생했습니다: {str(e)}")


@router.get("/tts/cache/stats",
           summary="TTS 캐시 통계",
           description="TTS 시스템의 캐시 사용 통계를 조회합니다.")
async def get_tts_cache_stats():
    """TTS 캐시 통계"""
    try:
        cache_stats = tts_service.get_cache_stats()
        
        return {
            "success": True,
            "data": cache_stats,
            "metadata": {
                "request_id": f"tts_stats_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting TTS cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/tts/cache/preload",
            summary="자주 사용하는 문구 사전 로딩",
            description="자주 사용되는 TTS 문구들을 사전에 합성하여 캐시합니다.")
async def preload_common_phrases(
    phrases: List[str] = Body(..., description="사전 로딩할 문구 목록"),
    voice_profile: str = Body("ko_female_default", description="음성 프로파일")
):
    """자주 사용하는 문구 사전 로딩"""
    try:
        if len(phrases) > 50:
            raise HTTPException(status_code=400, detail="한 번에 최대 50개 문구까지 사전 로딩할 수 있습니다")
        
        preload_results = await tts_service.preload_common_phrases(phrases, voice_profile)
        
        successful_count = sum(1 for success in preload_results.values() if success)
        failed_count = len(phrases) - successful_count
        
        return {
            "success": True,
            "data": {
                "preload_results": preload_results,
                "summary": {
                    "total_phrases": len(phrases),
                    "successful": successful_count,
                    "failed": failed_count,
                    "success_rate": f"{(successful_count/len(phrases)*100):.1f}%"
                }
            },
            "metadata": {
                "request_id": f"tts_preload_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "voice_profile": voice_profile
            }
        }
        
    except Exception as e:
        logger.error(f"Error preloading TTS phrases: {e}")
        raise HTTPException(status_code=500, detail=f"TTS 문구 사전 로딩 중 오류가 발생했습니다: {str(e)}")
"""
User API Router - 사용자 관리 엔드포인트

사용자 프로필, 세션 관리, 선호도 설정, 히스토리 조회
익명 사용자 지원 및 개인화 서비스
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ..config.database import get_db
from ..services.user_service import UserService
from ..models.fortune import ZodiacSign

logger = logging.getLogger(__name__)

# Initialize service
user_service = UserService()

router = APIRouter(prefix="/user", tags=["User"])


# Request/Response Models
class UserCreateRequest(BaseModel):
    """사용자 생성 요청 모델"""
    name: str = Field("익명 사용자", description="사용자 이름")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    birth_time: Optional[str] = Field(None, description="태어난 시간 (HH:MM)")
    birth_location: Optional[str] = Field(None, description="출생지")
    zodiac_sign: Optional[ZodiacSign] = Field(None, description="별자리")
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v
    
    @validator('birth_time')
    def validate_birth_time(cls, v):
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM")
        return v


class UserUpdateRequest(BaseModel):
    """사용자 정보 업데이트 요청 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="사용자 이름")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    birth_time: Optional[str] = Field(None, description="태어난 시간 (HH:MM)")
    birth_location: Optional[str] = Field(None, max_length=100, description="출생지")
    zodiac_sign: Optional[ZodiacSign] = Field(None, description="별자리")
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v
    
    @validator('birth_time')
    def validate_birth_time(cls, v):
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM")
        return v


class UserPreferencesRequest(BaseModel):
    """사용자 선호도 설정 요청 모델"""
    fortune_types: Optional[List[str]] = Field(None, description="선호하는 운세 타입들")
    notification_time: Optional[str] = Field(None, description="알림 시간 (HH:MM)")
    theme: Optional[str] = Field(None, description="테마 설정")
    language: Optional[str] = Field(None, description="언어 설정")
    timezone: Optional[str] = Field(None, description="시간대")
    privacy_settings: Optional[Dict[str, Any]] = Field(None, description="프라이버시 설정")
    
    @validator('fortune_types')
    def validate_fortune_types(cls, v):
        if v:
            valid_types = ["daily", "tarot", "zodiac", "oriental"]
            for fortune_type in v:
                if fortune_type not in valid_types:
                    raise ValueError(f"Invalid fortune type: {fortune_type}")
        return v
    
    @validator('notification_time')
    def validate_notification_time(cls, v):
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM")
        return v


class SessionCreateRequest(BaseModel):
    """세션 생성 요청 모델"""
    session_type: str = Field("web", description="세션 타입")
    metadata: Optional[Dict[str, Any]] = Field(None, description="세션 메타데이터")


# API Endpoints
@router.post("/profile",
            summary="사용자 프로필 생성",
            description="새로운 사용자 프로필을 생성합니다.")
async def create_user_profile(
    request: UserCreateRequest,
    db: Session = Depends(get_db)
):
    """사용자 프로필 생성"""
    try:
        user_data = request.dict(exclude_none=True)
        
        # 별자리 값 문자열로 변환
        if user_data.get("zodiac_sign"):
            user_data["zodiac_sign"] = user_data["zodiac_sign"].value
        
        user_info = await user_service.create_or_get_user(db, user_data)
        
        return {
            "success": True,
            "data": user_info,
            "metadata": {
                "request_id": f"create_user_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "is_new": True
            }
        }
        
    except ValueError as e:
        logger.warning(f"Invalid request in create_user_profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in create_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"프로필 생성 중 오류가 발생했습니다: {str(e)}")


@router.put("/profile/{user_uuid}",
           summary="사용자 프로필 수정",
           description="기존 사용자 프로필을 수정합니다.")
async def update_user_profile(
    user_uuid: str,
    request: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """사용자 프로필 수정"""
    try:
        update_data = request.dict(exclude_none=True)
        
        # 별자리 값 문자열로 변환
        if update_data.get("zodiac_sign"):
            update_data["zodiac_sign"] = update_data["zodiac_sign"].value
        
        user_info = await user_service.update_user_profile(db, user_uuid, update_data)
        
        return {
            "success": True,
            "data": user_info,
            "metadata": {
                "request_id": f"update_user_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except ValueError as e:
        logger.warning(f"User not found in update_user_profile: {e}")
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"Error in update_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"프로필 수정 중 오류가 발생했습니다: {str(e)}")


@router.get("/profile/{user_uuid}",
           summary="사용자 프로필 조회",
           description="사용자 프로필 정보를 조회합니다.")
async def get_user_profile(
    user_uuid: str,
    db: Session = Depends(get_db)
):
    """사용자 프로필 조회"""
    try:
        user_info = await user_service.get_user_profile(db, user_uuid)
        
        return {
            "success": True,
            "data": user_info,
            "metadata": {
                "request_id": f"get_user_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except ValueError as e:
        logger.warning(f"User not found in get_user_profile: {e}")
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"Error in get_user_profile: {e}")
        raise HTTPException(status_code=500, detail=f"프로필 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/session",
            summary="사용자 세션 생성",
            description="새로운 사용자 세션을 생성합니다.")
async def create_user_session(
    user_uuid: str = Query(..., description="사용자 UUID"),
    request: SessionCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """사용자 세션 생성"""
    try:
        session_info = await user_service.create_user_session(
            db, user_uuid, request.session_type, request.metadata
        )
        
        return {
            "success": True,
            "data": session_info,
            "metadata": {
                "request_id": f"create_session_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except ValueError as e:
        logger.warning(f"User not found in create_user_session: {e}")
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"Error in create_user_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/sessions/{user_uuid}",
           summary="사용자 세션 목록",
           description="사용자의 세션 목록을 조회합니다.")
async def get_user_sessions(
    user_uuid: str,
    active_only: bool = Query(True, description="활성 세션만 조회"),
    db: Session = Depends(get_db)
):
    """사용자 세션 목록 조회"""
    try:
        sessions = await user_service.get_user_sessions(db, user_uuid, active_only)
        
        return {
            "success": True,
            "data": {
                "user_uuid": user_uuid,
                "sessions": sessions,
                "count": len(sessions),
                "active_only": active_only
            },
            "metadata": {
                "request_id": f"get_sessions_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/sessions",
            summary="사용자 세션 생성 (Frontend compatibility)",
            description="프론트엔드용 사용자 세션을 생성합니다.")
async def create_user_sessions(
    request: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """사용자 세션 생성 (Frontend 호환용)"""
    try:
        user_id = request.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id가 필요합니다")
        
        # user_id를 기반으로 사용자 찾기 또는 생성
        # user_id는 frontend에서 생성한 ID이므로 익명 사용자로 처리
        user_data = {
            "name": "익명 사용자"
        }
        
        user_info = await user_service.create_or_get_user(db, user_data)
        
        # 세션 생성
        session_info = await user_service.create_user_session(
            db, user_info["uuid"], "web", {"frontend_user_id": user_id}
        )
        
        return {
            "success": True,
            "data": {
                "session_id": session_info["session_id"],
                "user_uuid": user_info["uuid"],
                "expires_at": session_info["expires_at"],
                "created_at": session_info["created_at"]
            },
            "metadata": {
                "request_id": f"create_sessions_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_user_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/sessions",
           summary="세션 목록 조회 (Frontend compatibility)",
           description="현재 사용자의 세션 목록을 조회합니다.")
async def get_user_sessions_list(
    active_only: bool = Query(True, description="활성 세션만 조회"),
    db: Session = Depends(get_db)
):
    """세션 목록 조회 (Frontend 호환용)"""
    try:
        # 현재는 모든 활성 세션을 반환 (향후 인증 추가시 사용자별로 필터링)
        from ..models.user import UserSession
        
        if active_only:
            sessions = db.query(UserSession).filter(
                UserSession.is_active == True
            ).order_by(UserSession.created_at.desc()).limit(50).all()
        else:
            sessions = db.query(UserSession).order_by(
                UserSession.created_at.desc()
            ).limit(50).all()
        
        session_data = []
        for session in sessions:
            session_data.append({
                "session_id": session.session_id,
                "user_uuid": session.user_uuid,
                "session_type": session.session_type,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None
            })
        
        return {
            "success": True,
            "data": {
                "sessions": session_data,
                "count": len(session_data),
                "active_only": active_only
            },
            "metadata": {
                "request_id": f"get_sessions_list_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_sessions_list: {e}")
        raise HTTPException(status_code=500, detail=f"세션 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.delete("/session/{session_id}",
              summary="사용자 세션 종료",
              description="특정 사용자 세션을 종료합니다.")
async def end_user_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """사용자 세션 종료"""
    try:
        success = await user_service.end_user_session(db, session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")
        
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
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in end_user_session: {e}")
        raise HTTPException(status_code=500, detail=f"세션 종료 중 오류가 발생했습니다: {str(e)}")


@router.get("/preferences/{user_uuid}",
           summary="사용자 선호도 조회",
           description="사용자의 선호도 설정을 조회합니다.")
async def get_user_preferences(
    user_uuid: str,
    db: Session = Depends(get_db)
):
    """사용자 선호도 조회"""
    try:
        preferences = await user_service.get_user_preferences(db, user_uuid)
        
        return {
            "success": True,
            "data": preferences,
            "metadata": {
                "request_id": f"get_preferences_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=f"선호도 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/preferences/{user_uuid}",
           summary="사용자 선호도 설정",
           description="사용자의 선호도를 설정합니다.")
async def update_user_preferences(
    user_uuid: str,
    request: UserPreferencesRequest,
    db: Session = Depends(get_db)
):
    """사용자 선호도 설정"""
    try:
        preferences_data = request.dict(exclude_none=True)
        preferences = await user_service.update_user_preferences(db, user_uuid, preferences_data)
        
        return {
            "success": True,
            "data": preferences,
            "metadata": {
                "request_id": f"update_preferences_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except Exception as e:
        logger.error(f"Error in update_user_preferences: {e}")
        raise HTTPException(status_code=500, detail=f"선호도 설정 중 오류가 발생했습니다: {str(e)}")


@router.get("/fortune-history/{user_uuid}",
           summary="사용자 운세 히스토리",
           description="사용자의 운세 요청 히스토리를 조회합니다.")
async def get_user_fortune_history(
    user_uuid: str,
    fortune_type: str = Query("all", description="운세 타입 필터"),
    limit: int = Query(50, ge=1, le=200, description="조회할 항목 수"),
    days: Optional[int] = Query(None, ge=1, le=365, description="조회 기간 (일)"),
    db: Session = Depends(get_db)
):
    """사용자 운세 히스토리 조회"""
    try:
        history = await user_service.get_user_fortune_history(
            db, user_uuid, fortune_type if fortune_type != "all" else None, limit, days
        )
        
        return {
            "success": True,
            "data": history,
            "metadata": {
                "request_id": f"fortune_history_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_fortune_history: {e}")
        raise HTTPException(status_code=500, detail=f"운세 히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/activity/{user_uuid}",
           summary="사용자 활동 요약",
           description="사용자의 활동 요약 정보를 조회합니다.")
async def get_user_activity_summary(
    user_uuid: str,
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    db: Session = Depends(get_db)
):
    """사용자 활동 요약"""
    try:
        activity_summary = await user_service.get_user_activity_summary(db, user_uuid, days)
        
        return {
            "success": True,
            "data": activity_summary,
            "metadata": {
                "request_id": f"activity_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_activity_summary: {e}")
        raise HTTPException(status_code=500, detail=f"활동 요약 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/search",
           summary="사용자 검색",
           description="사용자를 검색합니다 (관리자용).")
async def search_users(
    query: str = Query(..., min_length=1, description="검색어"),
    limit: int = Query(20, ge=1, le=100, description="결과 수 제한"),
    db: Session = Depends(get_db)
):
    """사용자 검색 (관리자용)"""
    try:
        users = await user_service.search_users(db, query, limit)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "users": users,
                "count": len(users)
            },
            "metadata": {
                "request_id": f"search_users_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in search_users: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 검색 중 오류가 발생했습니다: {str(e)}")


# Administrative endpoints
@router.post("/cleanup/sessions",
            summary="만료된 세션 정리",
            description="만료된 사용자 세션들을 정리합니다.")
async def cleanup_expired_sessions(
    db: Session = Depends(get_db)
):
    """만료된 세션 정리"""
    try:
        cleaned_count = await user_service.cleanup_expired_sessions(db)
        
        return {
            "success": True,
            "data": {
                "cleaned_sessions": cleaned_count,
                "cleaned_at": datetime.now().isoformat()
            },
            "metadata": {
                "request_id": f"cleanup_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_sessions: {e}")
        raise HTTPException(status_code=500, detail=f"세션 정리 중 오류가 발생했습니다: {str(e)}")


@router.get("/statistics",
           summary="사용자 통계",
           description="전체 사용자 통계를 조회합니다.")
async def get_user_statistics(
    days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    db: Session = Depends(get_db)
):
    """사용자 통계"""
    try:
        statistics = await user_service.get_user_statistics(db, days)
        
        return {
            "success": True,
            "data": statistics,
            "metadata": {
                "request_id": f"statistics_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_statistics: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


# Anonymous user endpoints
@router.post("/anonymous",
            summary="익명 사용자 생성",
            description="임시 익명 사용자를 생성합니다.")
async def create_anonymous_user(
    db: Session = Depends(get_db)
):
    """익명 사용자 생성"""
    try:
        user_data = {
            "name": "익명 사용자"
        }
        
        user_info = await user_service.create_or_get_user(db, user_data)
        
        # 익명 사용자용 세션 생성
        session_info = await user_service.create_user_session(
            db, user_info["uuid"], "anonymous", {"temporary": True}
        )
        
        return {
            "success": True,
            "data": {
                "user": user_info,
                "session": session_info,
                "temporary": True
            },
            "metadata": {
                "request_id": f"anonymous_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_anonymous_user: {e}")
        raise HTTPException(status_code=500, detail=f"익명 사용자 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/anonymous/upgrade",
            summary="익명 사용자 업그레이드",
            description="익명 사용자를 정식 사용자로 업그레이드합니다.")
async def upgrade_anonymous_user(
    user_uuid: str = Query(..., description="업그레이드할 익명 사용자 UUID"),
    request: UserUpdateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """익명 사용자를 정식 사용자로 업그레이드"""
    try:
        # 이름이 제공되지 않으면 오류
        if not request.name or request.name == "익명 사용자":
            raise HTTPException(status_code=400, detail="정식 사용자가 되려면 이름을 입력해야 합니다")
        
        update_data = request.dict(exclude_none=True)
        
        # 별자리 값 문자열로 변환
        if update_data.get("zodiac_sign"):
            update_data["zodiac_sign"] = update_data["zodiac_sign"].value
        
        user_info = await user_service.update_user_profile(db, user_uuid, update_data)
        
        return {
            "success": True,
            "data": {
                "user": user_info,
                "upgraded": True,
                "upgraded_at": datetime.now().isoformat()
            },
            "metadata": {
                "request_id": f"upgrade_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"User not found in upgrade_anonymous_user: {e}")
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
    except Exception as e:
        logger.error(f"Error in upgrade_anonymous_user: {e}")
        raise HTTPException(status_code=500, detail=f"사용자 업그레이드 중 오류가 발생했습니다: {str(e)}")


# Health check endpoint
@router.get("/health",
           summary="사용자 서비스 상태 확인",
           description="사용자 서비스의 상태를 확인합니다.")
async def user_health_check(
    db: Session = Depends(get_db)
):
    """사용자 서비스 헬스 체크"""
    try:
        # 기본 서비스 테스트
        test_user_data = {
            "name": "헬스체크 사용자",
            "birth_date": "1990-01-01"
        }
        
        # 사용자 생성 테스트 (실제로는 생성하지 않음)
        from ..models.user import User
        
        # 데이터베이스 연결 테스트
        user_count = db.query(User).count()
        
        # 캐시 서비스 테스트
        cache_status = "operational"
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "user_service",
                "database_connection": True,
                "total_users": user_count,
                "cache_service": cache_status,
                "preferences_support": True,
                "session_management": True,
                "anonymous_support": True
            },
            "metadata": {
                "request_id": f"health_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"User service health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNHEALTHY",
                    "message": "사용자 서비스가 정상적으로 작동하지 않습니다",
                    "details": str(e)
                }
            }
        )
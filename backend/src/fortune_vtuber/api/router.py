"""
API Router Module - 모든 API 라우터를 통합

Fortune VTuber Backend API 엔드포인트들을 통합 관리
"""

from fastapi import APIRouter
from .test_simple import router as test_router
from .fortune import router as fortune_router
from .live2d import router as live2d_router
from .live2d_motion import router as live2d_motion_router
from .chat import router as chat_router
from .user import router as user_router
from .performance import router as performance_router
from .tts import router as tts_router
from .tts_settings import router as tts_settings_router

# 메인 API 라우터 생성 (v1 prefix)
api_router = APIRouter(prefix="/api/v1")

# 각 모듈의 라우터 등록
api_router.include_router(test_router, tags=["Test"])
api_router.include_router(fortune_router, tags=["Fortune"])
api_router.include_router(live2d_router, tags=["Live2D"])
api_router.include_router(live2d_motion_router, tags=["Live2D Motion"])  # Live2D Character Motion System
api_router.include_router(chat_router, tags=["Chat"])
api_router.include_router(user_router, tags=["User"])
api_router.include_router(performance_router, tags=["Performance"])
api_router.include_router(tts_router, tags=["TTS"])  # Multi-Provider TTS System (Phase 8.1)
api_router.include_router(tts_settings_router, tags=["TTS Settings"])  # TTS Settings and Voice Testing (Phase 8.6)

# 직접 API 라우터 생성 (frontend compatibility)
direct_api_router = APIRouter(prefix="/api")
direct_api_router.include_router(live2d_router, tags=["Live2D Direct"])
direct_api_router.include_router(live2d_motion_router, tags=["Live2D Motion Direct"])
direct_api_router.include_router(tts_settings_router, tags=["TTS Settings Direct"])  # Direct access for frontend

# v2 API 라우터 생성 (호환성)
v2_api_router = APIRouter(prefix="/api/v2")

@v2_api_router.get("/heartbeat", tags=["Health"])
async def v2_heartbeat():
    """API v2 호환 heartbeat 엔드포인트"""
    return {
        "success": True,
        "data": {
            "status": "alive",
            "version": "2.0.0",
            "timestamp": "2024-01-01T00:00:00Z",
            "uptime": "running"
        }
    }

# API 상태 확인 엔드포인트
@api_router.get("/health", tags=["Health"])
async def api_health_check():
    """API 전체 상태 확인"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": "1.0.0",
            "services": {
                "fortune": "operational",
                "live2d": "operational", 
                "chat": "operational",
                "user": "operational",
                "tts": "operational"
            },
            "endpoints": {
                "fortune": ["/fortune/daily", "/fortune/tarot", "/fortune/zodiac", "/fortune/oriental"],
                "live2d": ["/live2d/status", "/live2d/models", "/live2d/config", "/live2d/session", "/live2d/emotion", "/live2d/motion"],
                "chat": ["/chat/session", "/chat/history"],
                "user": ["/user/profile", "/user/preferences", "/user/sessions"],
                "tts": ["/tts/generate", "/tts/providers", "/tts/user/{user_id}/preferences", "/tts/statistics", "/tts/settings", "/tts/test", "/tts/health"]
            }
        }
    }
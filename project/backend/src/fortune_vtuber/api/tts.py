"""
TTS API Endpoints

API endpoints for the new multi-provider TTS system.
Provides user-configurable TTS settings, provider management, and Live2D integration.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..config.settings import get_settings
from ..tts import (
    Live2DTTSManager, Live2DTTSRequest, EmotionType,
    TTSConfigManager, live2d_tts_manager
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])


class TTSGenerateRequest(BaseModel):
    """TTS generation request model"""
    text: str = Field(..., description="Text to synthesize", max_length=5000)
    user_id: str = Field(default="default", description="User identifier")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    language: str = Field(default="ko-KR", description="Target language")
    voice: Optional[str] = Field(default=None, description="Specific voice (optional)")
    emotion: Optional[EmotionType] = Field(default=None, description="Emotion type")
    speed: float = Field(default=1.0, description="Speech speed", ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, description="Speech pitch", ge=0.5, le=2.0)
    volume: float = Field(default=1.0, description="Speech volume", ge=0.1, le=2.0)
    enable_lipsync: bool = Field(default=True, description="Enable lip sync data")
    enable_expressions: bool = Field(default=True, description="Enable Live2D expressions")
    enable_motions: bool = Field(default=True, description="Enable Live2D motions")
    provider_override: Optional[str] = Field(default=None, description="Override provider selection")


class TTSUserPreferencesRequest(BaseModel):
    """User TTS preferences update request"""
    preferred_provider: Optional[str] = None
    preferred_voice: Optional[str] = None
    preferred_language: str = Field(default="ko-KR")
    speech_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    speech_pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    speech_volume: float = Field(default=1.0, ge=0.1, le=2.0)
    enable_fallback: bool = Field(default=True)
    custom_fallback_chain: Optional[List[str]] = None


class TTSProviderConfigRequest(BaseModel):
    """TTS provider configuration request"""
    provider_id: str = Field(..., description="Provider identifier")
    api_key: str = Field(..., description="API key")
    api_url: Optional[str] = Field(default=None, description="API URL (optional)")


@router.post("/generate")
async def generate_tts(
    request: TTSGenerateRequest,
    background_tasks: BackgroundTasks,
    settings=Depends(get_settings)
) -> Dict[str, Any]:
    """
    Generate TTS with Live2D integration using the multi-provider system.
    
    Supports fallback chains and user preferences.
    """
    try:
        if not settings.tts.tts_enabled:
            raise HTTPException(status_code=503, detail="TTS service is disabled")
        
        # Create Live2D TTS request
        live2d_request = Live2DTTSRequest(
            text=request.text,
            user_id=request.user_id,
            session_id=request.session_id or f"session_{datetime.now().isoformat()}",
            language=request.language,
            voice=request.voice,
            emotion=request.emotion,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            enable_lipsync=request.enable_lipsync,
            enable_expressions=request.enable_expressions,
            enable_motions=request.enable_motions,
            provider_override=request.provider_override
        )
        
        # Generate TTS with Live2D integration
        result = await live2d_tts_manager.generate_speech_with_animation(live2d_request)
        
        # numpy 타입 변환을 위한 import
        from ..utils import fix_tts_result_for_json, create_safe_api_response, sanitize_for_json
        
        # TTS 결과의 numpy 타입들을 안전하게 변환
        result.tts_result = fix_tts_result_for_json(result.tts_result)
        
        response_data = {
            "success": True,
            "data": {
                "session_id": live2d_request.session_id,
                "audio_format": result.tts_result.audio_format,
                "duration": float(result.total_duration),
                "provider_used": result.provider_info["provider_id"],
                "voice_used": result.tts_result.voice_used,
                "generation_time": float(result.tts_result.generation_time),
                "cached": bool(result.tts_result.cached),
                "live2d_commands": sanitize_for_json(result.live2d_commands),
                "expressions": sanitize_for_json(result.expression_timeline),
                "motions": sanitize_for_json(result.motion_timeline),
                # 프론트엔드 호환 립싱크 데이터 추가
                "lip_sync": _extract_lipsync_from_live2d_commands(result.live2d_commands),
                "lipsync_data": {
                    "enabled": result.tts_result.lip_sync_data is not None,
                    "phoneme_count": len(result.tts_result.lip_sync_data.phonemes) if result.tts_result.lip_sync_data else 0,
                    "mouth_shape_count": len(result.tts_result.lip_sync_data.mouth_shapes) if result.tts_result.lip_sync_data else 0
                },
                "provider_info": sanitize_for_json(result.provider_info),
                "cost_info": sanitize_for_json(result.tts_result.cost_info) if result.tts_result.cost_info else {}
            },
            "metadata": {
                "request_time": datetime.now().isoformat(),
                "text_length": len(request.text),
                "language": request.language,
                "emotion": request.emotion.value if request.emotion else None
            }
        }
        
        # JSON 직렬화 안전성 확보
        return create_safe_api_response(response_data)
        
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.get("/providers")
async def get_available_providers(
    user_id: str = "default",
    language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get available TTS providers for user.
    
    Returns provider information including cost, quality, and availability.
    """
    try:
        # Get user-specific options
        providers = live2d_tts_manager.get_available_providers_for_user(user_id)
        
        # Filter by language if specified
        if language:
            providers = [p for p in providers if language in p.get("languages", [])]
        
        return {
            "success": True,
            "data": {
                "providers": providers,
                "total_count": len(providers),
                "filter": {
                    "user_id": user_id,
                    "language": language
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get providers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {str(e)}")


@router.get("/providers/{provider_id}/voices")
async def get_provider_voices(
    provider_id: str,
    language: str = "ko-KR"
) -> Dict[str, Any]:
    """Get available voices for a specific provider and language"""
    try:
        factory = live2d_tts_manager.tts_factory
        config = factory.get_provider_config(provider_id)
        
        if not config:
            raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")
        
        voices = config.get_voices_for_language(language)
        
        return {
            "success": True,
            "data": {
                "provider_id": provider_id,
                "language": language,
                "voices": voices,
                "voice_count": len(voices),
                "supports_language": config.supports_language(language)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get voices for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/preferences")
async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """Get user TTS preferences"""
    try:
        config_manager = live2d_tts_manager.config_manager
        preferences = config_manager.get_user_preferences(user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": user_id,
                "preferences": preferences.to_dict()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    request: TTSUserPreferencesRequest
) -> Dict[str, Any]:
    """Update user TTS preferences"""
    try:
        # Convert request to dict, excluding None values
        preferences_dict = {k: v for k, v in request.dict().items() if v is not None}
        
        result = live2d_tts_manager.update_user_tts_settings(user_id, **preferences_dict)
        
        return {
            "success": True,
            "data": result,
            "message": f"Updated preferences for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/configure")
async def configure_provider(
    request: TTSProviderConfigRequest,
    settings=Depends(get_settings)
) -> Dict[str, Any]:
    """Configure TTS provider API credentials"""
    try:
        config_manager = live2d_tts_manager.config_manager
        success = config_manager.configure_provider_api(
            request.provider_id,
            request.api_key,
            request.api_url
        )
        
        if success:
            return {
                "success": True,
                "message": f"Provider {request.provider_id} configured successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to configure provider")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to configure provider: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_tts_statistics() -> Dict[str, Any]:
    """Get TTS system statistics and performance metrics"""
    try:
        stats = live2d_tts_manager.get_tts_statistics()
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/health-check")
async def health_check_providers() -> Dict[str, Any]:
    """Perform health check on all TTS providers"""
    try:
        factory = live2d_tts_manager.tts_factory
        health_results = await factory.health_check_all_providers()
        
        return {
            "success": True,
            "data": {
                "health_check": health_results,
                "available_count": sum(1 for result in health_results.values() if result),
                "total_count": len(health_results),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/info")
async def get_system_info(settings=Depends(get_settings)) -> Dict[str, Any]:
    """Get TTS system configuration and status"""
    return {
        "success": True,
        "data": {
            "tts_enabled": settings.tts.tts_enabled,
            "default_language": settings.tts.default_language,
            "default_provider": settings.tts.preferred_provider,
            "fallback_enabled": settings.tts.fallback_enabled,
            "fallback_chain": settings.tts.fallback_chain,
            "lipsync_enabled": settings.tts.lipsync_enabled,
            "expressions_enabled": settings.tts.expressions_enabled,
            "motions_enabled": settings.tts.motions_enabled,
            "cache_enabled": settings.tts.cache_enabled,
            "max_text_length": settings.tts.max_text_length,
            "supported_languages": ["ko-KR", "en-US", "ja-JP", "zh-CN"],
            "supported_emotions": [e.value for e in EmotionType]
        }
    }


def _extract_lipsync_from_live2d_commands(live2d_commands):
    """
    Live2D Commands에서 프론트엔드 호환 lip_sync 형식으로 변환
    Live2D Command: {"type": "lipsync", "timestamp": 0.0, "data": {"mouth_parameters": {...}}}
    Frontend Format: [timestamp, {"ParamMouthOpenY": value, ...}]
    """
    if not live2d_commands:
        return []
        
    lipsync_data = []
    
    for command in live2d_commands:
        if command.get("type") == "lipsync" and "data" in command:
            timestamp = command.get("timestamp", 0.0)
            mouth_params = command["data"].get("mouth_parameters", {})
            
            # 실제 데이터 구조에 맞게 변환 (키 이름이 이미 올바름)
            frontend_params = {
                "ParamMouthOpenY": mouth_params.get("ParamMouthOpenY", 0.0),
                "ParamMouthForm": mouth_params.get("ParamMouthForm", 0.0),
                "ParamMouthOpenX": mouth_params.get("ParamMouthOpenX", 0.0)
            }
            
            lipsync_data.append([timestamp, frontend_params])
    
    # 시간 순으로 정렬
    lipsync_data.sort(key=lambda x: x[0])
    
    return lipsync_data
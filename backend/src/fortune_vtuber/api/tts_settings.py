"""
TTS Settings API Endpoints

Provides REST API endpoints for TTS provider selection, voice testing,
and user preference management. Based on todo specifications Phase 8.6.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
import uuid

from ..tts.live2d_tts_manager import Live2DTTSManager, Live2DTTSRequest, live2d_tts_manager
from ..tts.tts_config_manager import TTSConfigManager, tts_config_manager
from ..tts.tts_interface import TTSProviderError, TTSProviderUnavailableError

logger = logging.getLogger(__name__)

# Pydantic Models
class TtsSettingsRequest(BaseModel):
    """TTS settings update request"""
    user_id: str = Field(..., description="User identifier")
    provider_id: str = Field(..., description="TTS provider ID")
    voice: str = Field(..., description="Voice name")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech pitch")
    volume: float = Field(default=1.0, ge=0.1, le=2.0, description="Speech volume")
    language: str = Field(default="ko-KR", description="Language code")

class TtsTestRequest(BaseModel):
    """TTS voice test request"""
    user_id: str = Field(..., description="User identifier")
    provider_id: str = Field(..., description="TTS provider ID")
    voice: str = Field(..., description="Voice name")
    test_text: str = Field(default="안녕하세요! 이 목소리가 마음에 드시나요?", description="Test text")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech pitch")  
    volume: float = Field(default=1.0, ge=0.1, le=2.0, description="Speech volume")
    language: str = Field(default="ko-KR", description="Language code")

class TtsProviderInfo(BaseModel):
    """TTS provider information"""
    id: str
    name: str
    cost: str
    languages: List[str]
    voices: List[str]
    available: bool
    priority: int
    recommended: bool = False
    description: Optional[str] = None

class TtsTestResult(BaseModel):
    """TTS test result"""
    audio_url: str
    audio_data: Optional[str] = None  # Base64 encoded audio
    audio_format: str
    provider: str
    duration: float
    cost_info: Dict[str, Any]
    test_text: str

class TtsSettingsResponse(BaseModel):
    """TTS settings response"""
    status: str
    message: str
    user_id: str
    preferences: Dict[str, Any]
    updated_at: str

# API Router
router = APIRouter(prefix="/tts", tags=["TTS Settings"])

@router.get("/providers")
async def get_available_tts_providers(
    user_id: str = Query(..., description="User identifier")
) -> Dict[str, Any]:
    """
    Get available TTS providers for user.
    
    Returns list of TTS providers with availability, cost information,
    and user-specific recommendations.
    """
    try:
        logger.info(f"Getting TTS providers for user: {user_id}")
        
        # Get providers from TTS manager
        providers_data = live2d_tts_manager.get_available_providers_for_user(user_id)
        
        # Get user preferences for recommendations
        user_prefs = tts_config_manager.get_user_preferences(user_id)
        
        # Format providers for frontend
        providers = []
        for provider_data in providers_data:
            provider_info = TtsProviderInfo(
                id=provider_data["provider_id"],
                name=provider_data["name"],
                cost=provider_data["cost_type"],
                languages=provider_data["supported_languages"],
                voices=provider_data.get("available_voices", []),
                available=provider_data["available"],
                priority=provider_data.get("priority", 999),
                recommended=provider_data.get("recommended", False),
                description=provider_data.get("description")
            )
            providers.append(provider_info.dict())
        
        # Sort by priority and availability
        providers.sort(key=lambda p: (not p["available"], p["priority"]))
        
        # Mark recommended providers
        if providers and user_prefs:
            preferred_provider = user_prefs.tts_provider
            for provider in providers:
                if provider["id"] == preferred_provider:
                    provider["recommended"] = True
                    break
        
        # Mark first available free provider as recommended if no preference
        if not user_prefs or not user_prefs.tts_provider:
            for provider in providers:
                if provider["available"] and provider["cost"] == "free":
                    provider["recommended"] = True
                    break
        
        return {
            "providers": providers,
            "user_preferences": user_prefs.to_dict() if user_prefs else None,
            "default_language": "ko-KR",
            "supported_languages": ["ko-KR", "en-US", "ja-JP", "zh-CN"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get TTS providers for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get TTS providers: {str(e)}")

@router.post("/settings")
async def update_user_tts_settings(
    request: TtsSettingsRequest,
    background_tasks: BackgroundTasks
) -> TtsSettingsResponse:
    """
    Update user TTS preferences.
    
    Saves user's preferred TTS provider, voice, and voice parameters.
    """
    try:
        logger.info(f"Updating TTS settings for user: {request.user_id}")
        
        # Validate provider and voice
        provider_config = live2d_tts_manager.tts_factory.get_provider_config(request.provider_id)
        if not provider_config:
            raise HTTPException(status_code=400, detail=f"Unknown TTS provider: {request.provider_id}")
        
        if not provider_config.supports_language(request.language):
            raise HTTPException(
                status_code=400, 
                detail=f"Provider {request.provider_id} does not support language {request.language}"
            )
        
        available_voices = provider_config.supported_voices.get(request.language, [])
        if request.voice not in available_voices:
            raise HTTPException(
                status_code=400,
                detail=f"Voice {request.voice} not available for provider {request.provider_id}"
            )
        
        # Update user preferences
        updated_prefs = tts_config_manager.update_user_preferences(
            request.user_id,
            tts_provider=request.provider_id,
            voice=request.voice,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume
        )
        
        # Background: Update provider usage stats
        background_tasks.add_task(
            _update_provider_stats,
            request.provider_id,
            request.user_id,
            "settings_update"
        )
        
        return TtsSettingsResponse(
            status="success",
            message="TTS 설정이 성공적으로 저장되었습니다.",
            user_id=request.user_id,
            preferences=updated_prefs.to_dict(),
            updated_at=updated_prefs.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update TTS settings for {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update TTS settings: {str(e)}")

@router.post("/test")
async def test_tts_voice(
    request: TtsTestRequest,
    background_tasks: BackgroundTasks
) -> TtsTestResult:
    """
    Test TTS voice with provided settings.
    
    Generates a test audio sample with the specified provider and voice settings.
    """
    try:
        logger.info(f"Testing TTS voice for user: {request.user_id}, provider: {request.provider_id}")
        
        # Create TTS request for testing
        tts_request = Live2DTTSRequest(
            text=request.test_text,
            user_id=request.user_id,
            session_id=f"test_{uuid.uuid4()}",
            language=request.language,
            voice=request.voice,
            speed=request.speed,
            pitch=request.pitch,
            volume=request.volume,
            provider_override=request.provider_id,
            enable_lipsync=False,  # Skip lip-sync for test
            enable_expressions=False,  # Skip expressions for test
            enable_motions=False  # Skip motions for test
        )
        
        # Generate test TTS
        result = await live2d_tts_manager.generate_speech_with_animation(tts_request)
        
        # Calculate cost information
        cost_info = _calculate_test_cost(result.provider_info, len(request.test_text))
        
        # Background: Update provider usage stats
        background_tasks.add_task(
            _update_provider_stats,
            request.provider_id,
            request.user_id,
            "voice_test"
        )
        
        return TtsTestResult(
            audio_url=f"/api/audio/{result.tts_result.audio_path}",  # Assuming audio serving endpoint
            audio_data=result.tts_result.audio_data,  # Base64 encoded for immediate playback
            audio_format=result.tts_result.audio_format,
            provider=result.provider_info["provider_name"],
            duration=result.total_duration,
            cost_info=cost_info,
            test_text=request.test_text
        )
        
    except TTSProviderUnavailableError as e:
        logger.warning(f"TTS provider unavailable for test: {e}")
        raise HTTPException(status_code=503, detail=f"TTS provider unavailable: {str(e)}")
    except TTSProviderError as e:
        logger.warning(f"TTS provider error during test: {e}")
        raise HTTPException(status_code=400, detail=f"TTS generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"TTS voice test failed for {request.user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Voice test failed: {str(e)}")

@router.get("/user/{user_id}/settings")
async def get_user_tts_settings(user_id: str) -> Dict[str, Any]:
    """
    Get user's current TTS settings.
    
    Returns the user's saved TTS preferences and provider information.
    """
    try:
        logger.info(f"Getting TTS settings for user: {user_id}")
        
        # Get user preferences
        user_prefs = tts_config_manager.get_user_preferences(user_id)
        
        if not user_prefs:
            # Return default settings
            return {
                "user_id": user_id,
                "settings": {
                    "provider_id": "",
                    "voice": "",
                    "language": "ko-KR",
                    "speed": 1.0,
                    "pitch": 1.0,
                    "volume": 1.0
                },
                "has_settings": False
            }
        
        # Get provider information
        provider_info = None
        if user_prefs.tts_provider:
            provider_config = live2d_tts_manager.tts_factory.get_provider_config(user_prefs.tts_provider)
            if provider_config:
                provider_info = {
                    "id": provider_config.provider_id,
                    "name": provider_config.name,
                    "cost_type": provider_config.cost_type.value,
                    "available": provider_config.is_available()
                }
        
        return {
            "user_id": user_id,
            "settings": {
                "provider_id": user_prefs.tts_provider or "",
                "voice": user_prefs.voice or "",
                "language": user_prefs.language or "ko-KR", 
                "speed": user_prefs.speed or 1.0,
                "pitch": user_prefs.pitch or 1.0,
                "volume": user_prefs.volume or 1.0
            },
            "provider_info": provider_info,
            "has_settings": True,
            "last_updated": user_prefs.updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get TTS settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get TTS settings: {str(e)}")

@router.get("/providers/{provider_id}/info")
async def get_provider_info(provider_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific TTS provider.
    
    Returns provider capabilities, cost information, and availability status.
    """
    try:
        provider_config = live2d_tts_manager.tts_factory.get_provider_config(provider_id)
        
        if not provider_config:
            raise HTTPException(status_code=404, detail=f"TTS provider not found: {provider_id}")
        
        # Get provider statistics
        provider_stats = tts_config_manager.get_provider_statistics().get(provider_id, {})
        
        return {
            "provider_id": provider_config.provider_id,
            "name": provider_config.name,
            "cost_type": provider_config.cost_type.value,
            "quality": provider_config.quality.value,
            "supported_languages": provider_config.supported_languages,
            "supported_voices": provider_config.supported_voices,
            "api_required": provider_config.api_required,
            "available": provider_config.is_available(),
            "max_text_length": provider_config.max_text_length,
            "rate_limit_per_minute": provider_config.rate_limit_per_minute,
            "statistics": {
                "total_requests": provider_stats.get("total_requests", 0),
                "success_rate": provider_stats.get("success_rate", 0.0),
                "average_duration": provider_stats.get("average_duration", 0.0),
                "last_used": provider_stats.get("last_used")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get provider info for {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider info: {str(e)}")

@router.delete("/user/{user_id}/settings")
async def reset_user_tts_settings(user_id: str) -> Dict[str, Any]:
    """
    Reset user's TTS settings to defaults.
    
    Clears all user preferences and returns to system defaults.
    """
    try:
        logger.info(f"Resetting TTS settings for user: {user_id}")
        
        # Reset user preferences
        tts_config_manager.reset_user_preferences(user_id)
        
        return {
            "status": "success",
            "message": "TTS 설정이 초기화되었습니다.",
            "user_id": user_id,
            "reset_at": tts_config_manager.get_user_preferences(user_id).updated_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset TTS settings for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reset TTS settings: {str(e)}")

# Helper Functions
def _calculate_test_cost(provider_info: Dict[str, Any], text_length: int) -> Dict[str, Any]:
    """Calculate cost information for TTS test"""
    cost_info = provider_info.get("cost_info", {})
    
    # Estimate cost based on text length and provider type
    base_cost = cost_info.get("cost_per_character", 0.0)
    test_cost = base_cost * text_length
    
    # Estimate monthly cost for typical usage (assume 100 requests per month)
    estimated_monthly = test_cost * 100
    
    return {
        "cost": test_cost,
        "currency": cost_info.get("currency", "KRW"),
        "estimated_monthly": estimated_monthly,
        "cost_type": provider_info.get("cost_type", "unknown"),
        "free_tier_remaining": cost_info.get("free_tier_remaining"),
        "billing_details": cost_info.get("billing_details")
    }

async def _update_provider_stats(provider_id: str, user_id: str, operation: str):
    """Background task to update provider usage statistics"""
    try:
        tts_config_manager.record_provider_usage(
            provider_id=provider_id,
            success=True,
            text_length=len(operation),  # Use operation length as proxy
            duration=0.0,  # Not applicable for settings operations
            generation_time=0.0,
            user_id=user_id,
            operation_type=operation
        )
    except Exception as e:
        logger.warning(f"Failed to update provider stats: {e}")

# Health check endpoint
@router.get("/health")
async def tts_health_check() -> Dict[str, Any]:
    """
    Health check for TTS system.
    
    Returns system status and provider availability.
    """
    try:
        # Check TTS manager health
        health_status = await live2d_tts_manager.tts_factory.health_check_all_providers()
        
        # Count available providers
        available_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)
        
        system_healthy = available_count > 0
        
        return {
            "status": "healthy" if system_healthy else "degraded",
            "timestamp": tts_config_manager.get_current_timestamp().isoformat(),
            "providers": {
                "available": available_count,
                "total": total_count,
                "details": health_status
            },
            "system_info": {
                "tts_manager_initialized": live2d_tts_manager is not None,
                "config_manager_initialized": tts_config_manager is not None,
                "cached_providers": len(live2d_tts_manager.tts_factory._provider_instances)
            }
        }
        
    except Exception as e:
        logger.error(f"TTS health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": tts_config_manager.get_current_timestamp().isoformat(),
            "error": str(e)
        }
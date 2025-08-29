"""
Live2D Character Motion System API Endpoints

RESTful API for Live2D 모델 관리, 감정 처리, 캐릭터 상태 제어
Phase 7.1 구현: Live2D 백엔드 인프라 API
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..services.live2d_service import Live2DService
from ..websocket.live2d_websocket import get_websocket_manager
from ..live2d.emotion_bridge import emotion_bridge

logger = logging.getLogger(__name__)

# APIRouter 생성
router = APIRouter(prefix="/api/live2d", tags=["Live2D Character Motion"])

# JavaScript 스크립트 경로
LIVE2D_SCRIPTS_PATH = Path(__file__).parent.parent / "live2d"

class ModelLoadRequest(BaseModel):
    """모델 로드 요청"""
    model_name: str = Field(..., description="Live2D 모델 이름")
    session_id: str = Field(..., description="세션 ID")

class EmotionRequest(BaseModel):
    """감정 변경 요청"""
    session_id: str = Field(..., description="세션 ID")
    emotion: str = Field(..., description="감정 (joy, sadness, anger, surprise, fear, neutral, mystical, thinking)")
    intensity: float = Field(0.7, ge=0.0, le=1.0, description="감정 강도")
    duration: int = Field(3000, ge=100, le=30000, description="지속 시간 (ms)")
    auto_motion: bool = Field(True, description="자동 모션 트리거 여부")

class MotionRequest(BaseModel):
    """모션 트리거 요청"""
    session_id: str = Field(..., description="세션 ID")
    motion_group: str = Field("Idle", description="모션 그룹")
    motion_index: int = Field(0, ge=0, description="모션 인덱스")
    priority: int = Field(1, ge=1, le=3, description="우선순위")

class TextEmotionAnalysisRequest(BaseModel):
    """텍스트 감정 분석 요청"""
    text: str = Field(..., description="분석할 텍스트")
    session_id: str = Field(..., description="세션 ID")
    model_name: str = Field("mao_pro", description="Live2D 모델 이름")
    context: Dict[str, Any] = Field(default_factory=dict, description="컨텍스트 정보")
    auto_apply: bool = Field(True, description="분석 결과 자동 적용")

class FortuneEmotionSyncRequest(BaseModel):
    """운세 기반 감정 동기화 요청"""
    session_id: str = Field(..., description="세션 ID")
    fortune_result: Dict[str, Any] = Field(..., description="운세 결과")
    user_message: str = Field("", description="사용자 메시지")
    model_name: str = Field("mao_pro", description="Live2D 모델 이름")

class ParameterUpdateRequest(BaseModel):
    """Live2D 파라미터 업데이트 요청"""
    session_id: str = Field(..., description="세션 ID")
    parameters: Dict[str, float] = Field(..., description="파라미터 맵")
    duration: int = Field(1000, ge=100, le=10000, description="지속 시간 (ms)")
    fade_in: float = Field(0.5, ge=0.0, le=2.0, description="페이드 인 시간 (초)")
    fade_out: float = Field(0.5, ge=0.0, le=2.0, description="페이드 아웃 시간 (초)")

class CombinedStateRequest(BaseModel):
    """복합 상태 설정 요청"""
    session_id: str = Field(..., description="세션 ID")
    emotion: str = Field(..., description="감정")
    intensity: float = Field(0.7, ge=0.0, le=1.0, description="감정 강도")
    motion_group: str = Field("Idle", description="모션 그룹")
    motion_index: int = Field(0, ge=0, description="모션 인덱스")
    duration: int = Field(3000, ge=100, le=30000, description="지속 시간 (ms)")
    message: str = Field("", description="메시지 (선택사항)")


# Node.js 사용 가능 여부 확인
def check_node_availability() -> bool:
    """Node.js 사용 가능 여부 확인"""
    try:
        result = subprocess.run(
            ['node', '--version'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

NODE_AVAILABLE = check_node_availability()

# JavaScript 실행 헬퍼 함수
async def execute_js_script(script_content: str, timeout: int = 30) -> Dict[str, Any]:
    """JavaScript 스크립트 실행"""
    if not NODE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Node.js is not available")
    
    try:
        # 임시 스크립트 파일 생성
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        try:
            # Node.js 실행
            result = subprocess.run(
                ['node', script_path],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"JavaScript execution failed: {result.stderr}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"JavaScript execution failed: {result.stderr}"
                )
                
        finally:
            os.unlink(script_path)
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JavaScript output: {e}")
        raise HTTPException(status_code=500, detail="Invalid JavaScript output")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="JavaScript execution timeout")
    except Exception as e:
        logger.error(f"JavaScript execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models", response_model=Dict[str, Any])
async def get_available_models():
    """사용 가능한 Live2D 모델 목록 조회"""
    try:
        if NODE_AVAILABLE:
            script_content = f"""
const Live2dModelManager = require('{LIVE2D_SCRIPTS_PATH}/model_manager.js');

async function getModels() {{
    try {{
        const manager = new Live2dModelManager(
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d"}',
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d" / "model_dict.json"}'
        );
        
        await manager.initialize();
        const models = manager.getModelInfo();
        console.log(JSON.stringify({{ success: true, models, stats: manager.getStats() }}, null, 2));
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}, null, 2));
    }}
}}

getModels();
"""
            result = await execute_js_script(script_content)
            if result.get("success"):
                return {
                    "success": True,
                    "models": result["models"],
                    "stats": result["stats"],
                    "engine": "JavaScript"
                }
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        else:
            # Python fallback
            fallback_models = [
                {
                    "name": "mao_pro",
                    "description": "Default Mao Pro model",
                    "url": "/live2d-models/mao_pro/runtime/mao_pro.model3.json",
                    "availableEmotions": ["neutral", "joy", "sadness", "anger", "surprise", "fear"]
                },
                {
                    "name": "shizuku",
                    "description": "Shizuku model",
                    "url": "/live2d-models/shizuku/runtime/shizuku.model3.json",
                    "availableEmotions": ["neutral", "joy", "sadness", "anger"]
                }
            ]
            return {
                "success": True,
                "models": fallback_models,
                "stats": {"totalModels": 2, "engine": "fallback"},
                "engine": "Python fallback"
            }
    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/load", response_model=Dict[str, Any])
async def load_model(request: ModelLoadRequest, background_tasks: BackgroundTasks):
    """Live2D 모델 로드"""
    try:
        websocket_manager = get_websocket_manager()
        
        # WebSocket을 통해 모델 로드 요청
        if request.session_id in websocket_manager.session_connections:
            # WebSocket 연결이 있는 경우
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.MODEL_LOAD_REQUEST,
                {"model_name": request.model_name}
            )
            
            return {
                "success": True,
                "message": "Model load request sent via WebSocket",
                "session_id": request.session_id,
                "model_name": request.model_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # WebSocket 연결이 없는 경우 JavaScript로 직접 로드
            if NODE_AVAILABLE:
                script_content = f"""
const Live2dModelManager = require('{LIVE2D_SCRIPTS_PATH}/model_manager.js');

async function loadModel() {{
    try {{
        const manager = new Live2dModelManager(
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d"}',
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d" / "model_dict.json"}'
        );
        
        await manager.initialize();
        const metadata = await manager.loadModelMetadata('{request.model_name}');
        console.log(JSON.stringify({{ success: true, metadata }}, null, 2));
    }} catch (error) {{
        console.log(JSON.stringify({{ success: false, error: error.message }}, null, 2));
    }}
}}

loadModel();
"""
                result = await execute_js_script(script_content)
                if result.get("success"):
                    return {
                        "success": True,
                        "metadata": result["metadata"],
                        "session_id": request.session_id,
                        "model_name": request.model_name,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise HTTPException(status_code=500, detail=result.get("error", "Failed to load model"))
            else:
                # Python fallback
                return {
                    "success": True,
                    "metadata": {
                        "name": request.model_name,
                        "fallback": True,
                        "emotionMap": {"neutral": 0, "joy": 3, "sadness": 1, "anger": 2}
                    },
                    "session_id": request.session_id,
                    "model_name": request.model_name,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion/change", response_model=Dict[str, Any])
async def change_emotion(request: EmotionRequest, db: Session = Depends(get_db)):
    """감정 상태 변경"""
    try:
        live2d_service = Live2DService()
        
        # Live2D 서비스를 통한 감정 변경
        result = await live2d_service.change_emotion(
            db, 
            request.session_id, 
            request.emotion, 
            request.duration
        )
        
        # WebSocket을 통한 실시간 브로드캐스트
        websocket_manager = get_websocket_manager()
        if request.session_id in websocket_manager.session_connections:
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.EXPRESSION_UPDATE,
                {
                    "emotion": request.emotion,
                    "intensity": request.intensity,
                    "duration": request.duration,
                    "expression_index": _get_expression_index_for_emotion(request.emotion),
                    "auto_motion": request.auto_motion
                }
            )
        
        return {
            "success": True,
            "result": result,
            "session_id": request.session_id,
            "emotion": request.emotion,
            "intensity": request.intensity,
            "duration": request.duration,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error changing emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/motion/trigger", response_model=Dict[str, Any])
async def trigger_motion(request: MotionRequest):
    """모션 트리거"""
    try:
        websocket_manager = get_websocket_manager()
        
        if request.session_id in websocket_manager.session_connections:
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.MOTION_TRIGGER,
                {
                    "motion_group": request.motion_group,
                    "motion_index": request.motion_index,
                    "priority": request.priority
                }
            )
            
            return {
                "success": True,
                "message": "Motion trigger sent",
                "session_id": request.session_id,
                "motion_group": request.motion_group,
                "motion_index": request.motion_index,
                "priority": request.priority,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=404, 
                detail="Session not found or WebSocket not connected"
            )
            
    except Exception as e:
        logger.error(f"Error triggering motion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emotion/analyze", response_model=Dict[str, Any])
async def analyze_text_emotion(request: TextEmotionAnalysisRequest):
    """텍스트 감정 분석"""
    try:
        if NODE_AVAILABLE:
            # JavaScript 감정 분석 엔진 사용
            script_content = f"""
const EmotionMapper = require('{LIVE2D_SCRIPTS_PATH}/emotion_mapper.js');

const mapper = new EmotionMapper();
const text = {json.dumps(request.text)};
const context = {json.dumps(request.context)};
const modelName = {json.dumps(request.model_name)};

try {{
    const result = mapper.mapEmotionsToExpressions(text, context, modelName);
    console.log(JSON.stringify({{ success: true, result }}, null, 2));
}} catch (error) {{
    console.log(JSON.stringify({{ success: false, error: error.message }}, null, 2));
}}
"""
            result = await execute_js_script(script_content)
            if result.get("success"):
                emotion_result = result["result"]
                
                # 자동 적용 옵션이 활성화된 경우
                if request.auto_apply:
                    websocket_manager = get_websocket_manager()
                    if request.session_id in websocket_manager.session_connections:
                        await websocket_manager.broadcast_to_session(
                            request.session_id,
                            websocket_manager.MessageType.BATCH_LIVE2D_UPDATE,
                            {
                                "updates": [{
                                    "type": "emotion_update",
                                    "expression_index": emotion_result.get("expressionIndex", 0),
                                    "duration": emotion_result.get("duration", 3000),
                                    "emotion": emotion_result.get("primaryEmotion", "neutral"),
                                    "intensity": emotion_result.get("intensity", 0.5)
                                }]
                            }
                        )
                
                return {
                    "success": True,
                    "text": request.text,
                    "emotion_result": emotion_result,
                    "auto_applied": request.auto_apply,
                    "session_id": request.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
        else:
            # Python fallback
            emotion_result = _analyze_text_emotion_fallback(request.text, request.context)
            return {
                "success": True,
                "text": request.text,
                "emotion_result": emotion_result,
                "auto_applied": False,
                "session_id": request.session_id,
                "engine": "Python fallback",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error analyzing text emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fortune/sync", response_model=Dict[str, Any])
async def sync_fortune_emotion(request: FortuneEmotionSyncRequest):
    """운세 기반 감정 동기화"""
    try:
        # 운세 결과를 기반으로 감정 계산
        context = {
            "type": f"fortune_{request.fortune_result.get('fortune_type', 'daily')}",
            "fortuneResult": request.fortune_result
        }
        
        if NODE_AVAILABLE and request.user_message:
            # 사용자 메시지가 있는 경우 JavaScript 엔진으로 복합 분석
            script_content = f"""
const EmotionMapper = require('{LIVE2D_SCRIPTS_PATH}/emotion_mapper.js');

const mapper = new EmotionMapper();
const text = {json.dumps(request.user_message)};
const context = {json.dumps(context)};
const modelName = {json.dumps(request.model_name)};

try {{
    const result = mapper.mapEmotionsToExpressions(text, context, modelName);
    console.log(JSON.stringify({{ success: true, result }}, null, 2));
}} catch (error) {{
    console.log(JSON.stringify({{ success: false, error: error.message }}, null, 2));
}}
"""
            result = await execute_js_script(script_content)
            if result.get("success"):
                emotion_result = result["result"]
            else:
                emotion_result = _analyze_fortune_only_emotion(request.fortune_result)
        else:
            # 운세 결과만으로 감정 분석
            emotion_result = _analyze_fortune_only_emotion(request.fortune_result)
        
        # WebSocket을 통한 실시간 동기화
        websocket_manager = get_websocket_manager()
        if request.session_id in websocket_manager.session_connections:
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.BATCH_LIVE2D_UPDATE,
                {
                    "updates": [{
                        "type": "fortune_emotion_sync",
                        "expression_index": emotion_result.get("expressionIndex", 0),
                        "duration": emotion_result.get("duration", 3000),
                        "emotion": emotion_result.get("primaryEmotion", "neutral"),
                        "intensity": emotion_result.get("intensity", 0.5),
                        "fortune_type": request.fortune_result.get("fortune_type")
                    }]
                }
            )
        
        return {
            "success": True,
            "emotion_result": emotion_result,
            "fortune_type": request.fortune_result.get("fortune_type"),
            "session_id": request.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error syncing fortune emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parameters/update", response_model=Dict[str, Any])
async def update_parameters(request: ParameterUpdateRequest, db: Session = Depends(get_db)):
    """Live2D 파라미터 직접 업데이트"""
    try:
        live2d_service = Live2DService()
        
        # Live2D 서비스를 통한 파라미터 업데이트
        result = await live2d_service.set_live2d_parameters(
            db,
            request.session_id,
            request.parameters,
            request.duration,
            request.fade_in,
            request.fade_out
        )
        
        # WebSocket을 통한 실시간 브로드캐스트
        websocket_manager = get_websocket_manager()
        if request.session_id in websocket_manager.session_connections:
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.LIVE2D_PARAMETER_UPDATE,
                {
                    "parameters": request.parameters,
                    "duration": request.duration,
                    "fade_in": request.fade_in,
                    "fade_out": request.fade_out
                }
            )
        
        return {
            "success": True,
            "result": result,
            "session_id": request.session_id,
            "parameters": request.parameters,
            "duration": request.duration,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/state/combined", response_model=Dict[str, Any])
async def set_combined_state(request: CombinedStateRequest, db: Session = Depends(get_db)):
    """복합 상태 설정 (감정 + 모션 + 메시지)"""
    try:
        live2d_service = Live2DService()
        
        # Live2D 서비스를 통한 복합 상태 설정
        result = await live2d_service.set_combined_state(
            db,
            request.session_id,
            request.emotion,
            request.motion_group,
            request.message
        )
        
        # WebSocket을 통한 실시간 브로드캐스트
        websocket_manager = get_websocket_manager()
        if request.session_id in websocket_manager.session_connections:
            await websocket_manager.broadcast_to_session(
                request.session_id,
                websocket_manager.MessageType.BATCH_LIVE2D_UPDATE,
                {
                    "updates": [
                        {
                            "type": "combined_state",
                            "expression_index": _get_expression_index_for_emotion(request.emotion),
                            "duration": request.duration,
                            "emotion": request.emotion,
                            "intensity": request.intensity,
                            "motion": {
                                "group": request.motion_group,
                                "index": request.motion_index
                            },
                            "message": request.message
                        }
                    ]
                }
            )
        
        return {
            "success": True,
            "result": result,
            "session_id": request.session_id,
            "emotion": request.emotion,
            "motion": {"group": request.motion_group, "index": request.motion_index},
            "message": request.message,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error setting combined state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{session_id}", response_model=Dict[str, Any])
async def get_character_state(session_id: str):
    """캐릭터 상태 조회"""
    try:
        websocket_manager = get_websocket_manager()
        character_state = websocket_manager.character_states.get(session_id)
        
        if character_state:
            return {
                "success": True,
                "session_id": session_id,
                "character_state": character_state,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "session_id": session_id,
                "error": "Character state not found",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Error getting character state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=Dict[str, Any])
async def get_live2d_stats():
    """Live2D 시스템 통계"""
    try:
        websocket_manager = get_websocket_manager()
        stats = websocket_manager.get_connection_stats()
        
        # 캐릭터 상태 통계 추가
        character_stats = {
            "active_characters": len(websocket_manager.character_states),
            "total_state_changes": sum(
                state.get("metrics", {}).get("stateChanges", 0)
                for state in websocket_manager.character_states.values()
            )
        }
        
        return {
            "success": True,
            "websocket_stats": stats,
            "character_stats": character_stats,
            "node_available": NODE_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting Live2D stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 헬퍼 함수들
def _get_expression_index_for_emotion(emotion: str, model_name: str = "mao_pro") -> int:
    """감정에 따른 표정 인덱스 반환"""
    emotion_map = {
        'mao_pro': {
            'neutral': 0,
            'fear': 1,
            'sadness': 1,
            'anger': 2,
            'joy': 3,
            'surprise': 3,
            'mystical': 0,
            'thinking': 1
        },
        'shizuku': {
            'neutral': 0,
            'joy': 1,
            'sadness': 2,
            'anger': 3,
            'surprise': 1,
            'fear': 2,
            'mystical': 0,
            'thinking': 0
        }
    }
    
    model_map = emotion_map.get(model_name, emotion_map['mao_pro'])
    return model_map.get(emotion, 0)


def _analyze_text_emotion_fallback(text: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Python fallback for emotion analysis"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['기쁘', '행복', '좋아', 'happy', 'joy', 'good']):
        return {
            "primaryEmotion": 'joy',
            "intensity": 0.7,
            "expressionIndex": 3,
            "duration": 3500,
            "fadeTiming": {"fadeIn": 0.3, "fadeOut": 0.7},
            "confidence": 0.6
        }
    elif any(word in text_lower for word in ['슬퍼', '우울', 'sad', 'sorry']):
        return {
            "primaryEmotion": 'sadness',
            "intensity": 0.6,
            "expressionIndex": 1,
            "duration": 4000,
            "fadeTiming": {"fadeIn": 0.8, "fadeOut": 0.4},
            "confidence": 0.6
        }
    else:
        return {
            "primaryEmotion": 'neutral',
            "intensity": 0.5,
            "expressionIndex": 0,
            "duration": 3000,
            "fadeTiming": {"fadeIn": 0.5, "fadeOut": 0.5},
            "confidence": 0.4
        }


def _analyze_fortune_only_emotion(fortune_result: Dict[str, Any]) -> Dict[str, Any]:
    """운세 결과만으로 감정 분석"""
    score = fortune_result.get("overall_fortune", {}).get("score", 50)
    
    if score >= 85:
        return {
            "primaryEmotion": "joy",
            "intensity": 0.9,
            "expressionIndex": 3,
            "duration": 4000,
            "fadeTiming": {"fadeIn": 0.3, "fadeOut": 0.7}
        }
    elif score >= 70:
        return {
            "primaryEmotion": "joy",
            "intensity": 0.7,
            "expressionIndex": 3,
            "duration": 3500,
            "fadeTiming": {"fadeIn": 0.4, "fadeOut": 0.6}
        }
    elif score >= 40:
        return {
            "primaryEmotion": "neutral",
            "intensity": 0.5,
            "expressionIndex": 0,
            "duration": 3000,
            "fadeTiming": {"fadeIn": 0.5, "fadeOut": 0.5}
        }
    else:
        return {
            "primaryEmotion": "sadness",
            "intensity": 0.6,
            "expressionIndex": 1,
            "duration": 3500,
            "fadeTiming": {"fadeIn": 0.6, "fadeOut": 0.4}
        }
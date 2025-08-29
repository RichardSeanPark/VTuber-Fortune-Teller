"""
Live2D WebSocket 실시간 동기화 핸들러

Live2D 캐릭터 상태, TTS 음성, 립싱크의 실시간 동기화
클라이언트와의 양방향 통신 및 상태 관리
Enhanced with Node.js emotion engine integration
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, Set, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import uuid
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..services.live2d_service import Live2DService
from ..live2d.tts_integration import tts_service, TTSRequest
from ..live2d.resource_optimizer import resource_optimizer, DeviceType
from ..config.database import get_db

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket 메시지 타입"""
    # 클라이언트 → 서버
    CLIENT_CONNECT = "client_connect"
    CLIENT_DISCONNECT = "client_disconnect"
    DEVICE_INFO = "device_info"
    USER_INTERACTION = "user_interaction"
    EMOTION_REQUEST = "emotion_request"
    TTS_REQUEST = "tts_request"
    PARAMETER_UPDATE = "parameter_update"
    HEARTBEAT = "heartbeat"
    
    # New Live2D Character Motion System messages
    MODEL_LOAD_REQUEST = "model_load_request"
    EXPRESSION_CHANGE_REQUEST = "expression_change_request"
    MOTION_TRIGGER_REQUEST = "motion_trigger_request"
    TEXT_EMOTION_ANALYSIS = "text_emotion_analysis"
    FORTUNE_EMOTION_SYNC = "fortune_emotion_sync"
    CHARACTER_STATE_SYNC = "character_state_sync"
    
    # 서버 → 클라이언트
    SERVER_READY = "server_ready"
    LIVE2D_ACTION = "live2d_action"
    LIVE2D_ADVANCED_ACTION = "live2d_advanced_action"
    LIVE2D_PARAMETER_UPDATE = "live2d_parameter_update"
    TTS_START = "tts_start"
    TTS_LIPSYNC_UPDATE = "tts_lipsync_update"
    TTS_COMPLETE = "tts_complete"
    TTS_ERROR = "tts_error"
    MODEL_OPTIMIZED = "model_optimized"
    ERROR = "error"
    
    # New Live2D Character Motion System responses
    MODEL_LOADED = "model_loaded"
    MODEL_METADATA = "model_metadata"
    EXPRESSION_UPDATE = "expression_update"
    MOTION_TRIGGER = "motion_trigger"
    EMOTION_ANALYSIS_RESULT = "emotion_analysis_result"
    CHARACTER_STATE_UPDATE = "character_state_update"
    BATCH_LIVE2D_UPDATE = "batch_live2d_update"


class ConnectionState(str, Enum):
    """연결 상태"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    READY = "ready"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class Live2DWebSocketManager:
    """Live2D WebSocket 연결 관리자"""
    
    def __init__(self, live2d_service: Live2DService):
        self.live2d_service = live2d_service
        
        # 연결 관리
        self.connections: Dict[str, WebSocket] = {}  # connection_id → websocket
        self.sessions: Dict[str, Dict[str, Any]] = {}  # session_id → session_data
        self.connection_states: Dict[str, ConnectionState] = {}
        
        # 세션별 연결 매핑
        self.session_connections: Dict[str, Set[str]] = {}  # session_id → connection_ids
        
        # Live2D Character Motion System
        self.character_states: Dict[str, Dict[str, Any]] = {}  # session_id → character_state
        self.node_engine_available = self._check_node_availability()
        self.live2d_scripts_path = Path(__file__).parent.parent / "live2d"
        
        # Batched updates for performance
        self.pending_updates: Dict[str, List[Dict[str, Any]]] = {}  # session_id → update_queue
        self.batch_timers: Dict[str, asyncio.Task] = {}  # session_id → timer_task
        
        # 성능 추적
        self.message_stats: Dict[str, int] = {}
        self.error_count = 0
        self.connection_count = 0
    
    def _check_node_availability(self) -> bool:
        """Node.js 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                ['node', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Node.js available: {result.stdout.strip()}")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Node.js not available for Live2D emotion engine")
        return False
    
    async def connect(self, websocket: WebSocket, session_id: str, user_uuid: Optional[str] = None) -> str:
        """WebSocket 연결 처리"""
        connection_id = str(uuid.uuid4())
        
        try:
            await websocket.accept()
            
            # 연결 등록
            self.connections[connection_id] = websocket
            self.connection_states[connection_id] = ConnectionState.CONNECTED
            self.connection_count += 1
            
            # 세션 연결 매핑
            if session_id not in self.session_connections:
                self.session_connections[session_id] = set()
            self.session_connections[session_id].add(connection_id)
            
            # Live2D 서비스에 WebSocket 등록
            await self.live2d_service.register_websocket(session_id, websocket)
            
            # 세션 데이터 초기화
            self.sessions[connection_id] = {
                "session_id": session_id,
                "user_uuid": user_uuid,
                "device_type": DeviceType.DESKTOP,  # 기본값
                "connected_at": datetime.now(),
                "last_heartbeat": datetime.now(),
                "message_count": 0,
                "device_optimized": False
            }
            
            # 서버 준비 완료 메시지
            await self._send_message(connection_id, MessageType.SERVER_READY, {
                "connection_id": connection_id,
                "session_id": session_id,
                "server_time": datetime.now().isoformat(),
                "supported_features": [
                    "live2d_control",
                    "tts_integration",
                    "lipsync",
                    "emotion_engine",
                    "resource_optimization"
                ]
            })
            
            self.connection_states[connection_id] = ConnectionState.READY
            logger.info(f"WebSocket connected: {connection_id} for session {session_id}")
            
            return connection_id
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection: {e}")
            await self.disconnect(connection_id)
            raise
    
    async def disconnect(self, connection_id: str):
        """WebSocket 연결 해제"""
        try:
            if connection_id in self.sessions:
                session_data = self.sessions[connection_id]
                session_id = session_data["session_id"]
                
                # Live2D 서비스에서 WebSocket 해제
                if connection_id in self.connections:
                    websocket = self.connections[connection_id]
                    await self.live2d_service.unregister_websocket(session_id, websocket)
                
                # 세션 연결 매핑에서 제거
                if session_id in self.session_connections:
                    self.session_connections[session_id].discard(connection_id)
                    if not self.session_connections[session_id]:
                        del self.session_connections[session_id]
                
                del self.sessions[connection_id]
            
            # 연결 정리
            if connection_id in self.connections:
                del self.connections[connection_id]
            
            if connection_id in self.connection_states:
                del self.connection_states[connection_id]
            
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
    
    async def handle_message(self, connection_id: str, message: Dict[str, Any]):
        """메시지 처리"""
        try:
            message_type = MessageType(message.get("type"))
            data = message.get("data", {})
            
            # 메시지 통계
            self.message_stats[message_type.value] = self.message_stats.get(message_type.value, 0) + 1
            
            # 세션 업데이트
            if connection_id in self.sessions:
                self.sessions[connection_id]["message_count"] += 1
                self.sessions[connection_id]["last_heartbeat"] = datetime.now()
            
            # 메시지 타입별 처리
            if message_type == MessageType.DEVICE_INFO:
                await self._handle_device_info(connection_id, data)
            elif message_type == MessageType.USER_INTERACTION:
                await self._handle_user_interaction(connection_id, data)
            elif message_type == MessageType.EMOTION_REQUEST:
                await self._handle_emotion_request(connection_id, data)
            elif message_type == MessageType.TTS_REQUEST:
                await self._handle_tts_request(connection_id, data)
            elif message_type == MessageType.PARAMETER_UPDATE:
                await self._handle_parameter_update(connection_id, data)
            elif message_type == MessageType.HEARTBEAT:
                await self._handle_heartbeat(connection_id, data)
            
            # New Live2D Character Motion System handlers
            elif message_type == MessageType.MODEL_LOAD_REQUEST:
                await self._handle_model_load_request(connection_id, data)
            elif message_type == MessageType.EXPRESSION_CHANGE_REQUEST:
                await self._handle_expression_change_request(connection_id, data)
            elif message_type == MessageType.MOTION_TRIGGER_REQUEST:
                await self._handle_motion_trigger_request(connection_id, data)
            elif message_type == MessageType.TEXT_EMOTION_ANALYSIS:
                await self._handle_text_emotion_analysis(connection_id, data)
            elif message_type == MessageType.FORTUNE_EMOTION_SYNC:
                await self._handle_fortune_emotion_sync(connection_id, data)
            elif message_type == MessageType.CHARACTER_STATE_SYNC:
                await self._handle_character_state_sync(connection_id, data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            self.error_count += 1
            await self._send_error(connection_id, str(e))
    
    async def _handle_device_info(self, connection_id: str, data: Dict[str, Any]):
        """디바이스 정보 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            # 디바이스 타입 결정
            device_info = data.get("device_info", {})
            device_type = self._determine_device_type(device_info)
            session_data["device_type"] = device_type
            
            # 리소스 최적화
            session_id = session_data["session_id"]
            user_preferences = data.get("user_preferences", {})
            
            optimized_config = resource_optimizer.get_optimized_config(device_type, user_preferences)
            
            # 최적화된 설정 전송
            await self._send_message(connection_id, MessageType.MODEL_OPTIMIZED, {
                "device_type": device_type.value,
                "optimized_config": optimized_config,
                "timestamp": datetime.now().isoformat()
            })
            
            session_data["device_optimized"] = True
            logger.info(f"Device optimized for {connection_id}: {device_type}")
            
        except Exception as e:
            logger.error(f"Error handling device info: {e}")
    
    async def _handle_user_interaction(self, connection_id: str, data: Dict[str, Any]):
        """사용자 상호작용 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            interaction_type = data.get("interaction_type")
            session_id = session_data["session_id"]
            
            # 상호작용에 따른 반응 결정
            if interaction_type == "tap":
                # 터치 반응
                await self._trigger_interaction_response(session_id, "greeting")
            elif interaction_type == "hover":
                # 호버 반응 (미세한 움직임)
                await self._trigger_interaction_response(session_id, "attention")
            elif interaction_type == "long_press":
                # 길게 누르기 반응
                await self._trigger_interaction_response(session_id, "special")
            
            logger.debug(f"User interaction handled: {interaction_type} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling user interaction: {e}")
    
    async def _handle_emotion_request(self, connection_id: str, data: Dict[str, Any]):
        """감정 변경 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            session_id = session_data["session_id"]
            emotion = data.get("emotion", "neutral")
            duration = data.get("duration")
            
            # 데이터베이스 세션 획득
            db_session = next(get_db())
            
            try:
                # Live2D 감정 변경
                from ..services.live2d_service import EmotionType
                emotion_type = EmotionType(emotion)
                
                result = await self.live2d_service.change_emotion(
                    db_session, session_id, emotion_type, duration
                )
                
                logger.info(f"Emotion changed via WebSocket: {emotion} for session {session_id}")
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error handling emotion request: {e}")
    
    async def _handle_tts_request(self, connection_id: str, data: Dict[str, Any]):
        """TTS 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            text = data.get("text", "")
            if not text:
                return
            
            session_id = session_data["session_id"]
            emotion = data.get("emotion", "neutral")
            language = data.get("language", "ko-KR")
            
            # 감정에 맞는 음성 프로파일 선택
            voice_profile = tts_service.get_voice_profile_for_emotion(emotion, language)
            
            # TTS 요청 생성
            tts_request = TTSRequest(
                text=text,
                voice_profile=voice_profile,
                emotion_tone=emotion,
                session_id=session_id,
                enable_lipsync=True
            )
            
            # TTS 스트리밍 시작
            asyncio.create_task(self._stream_tts_to_client(connection_id, tts_request))
            
            logger.info(f"TTS request started for session {session_id}: '{text[:50]}...'")
            
        except Exception as e:
            logger.error(f"Error handling TTS request: {e}")
            await self._send_message(connection_id, MessageType.TTS_ERROR, {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    async def _handle_parameter_update(self, connection_id: str, data: Dict[str, Any]):
        """Live2D 파라미터 업데이트 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            session_id = session_data["session_id"]
            parameters = data.get("parameters", {})
            duration = data.get("duration", 1000)
            fade_in = data.get("fade_in", 0.5)
            fade_out = data.get("fade_out", 0.5)
            
            # 데이터베이스 세션 획득
            db_session = next(get_db())
            
            try:
                # Live2D 파라미터 직접 제어
                result = await self.live2d_service.set_live2d_parameters(
                    db_session, session_id, parameters, duration, fade_in, fade_out
                )
                
                logger.debug(f"Live2D parameters updated via WebSocket for session {session_id}")
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Error handling parameter update: {e}")
    
    async def _handle_heartbeat(self, connection_id: str, data: Dict[str, Any]):
        """하트비트 처리"""
        session_data = self.sessions.get(connection_id)
        if session_data:
            session_data["last_heartbeat"] = datetime.now()
        
        # 하트비트 응답
        await self._send_message(connection_id, MessageType.HEARTBEAT, {
            "server_time": datetime.now().isoformat(),
            "connection_status": "alive"
        })
    
    async def _handle_model_load_request(self, connection_id: str, data: Dict[str, Any]):
        """Live2D 모델 로드 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
            
            session_id = session_data["session_id"]
            model_name = data.get("model_name", "mao_pro")
            
            # JavaScript 모델 매니저를 사용하여 메타데이터 로드
            metadata = await self._load_model_metadata_with_js(model_name)
            
            # 캐릭터 상태 초기화
            if session_id not in self.character_states:
                self.character_states[session_id] = {}
            
            self.character_states[session_id].update({
                "current_model": model_name,
                "current_expression": 0,
                "current_emotion": "neutral",
                "current_motion": None,
                "last_update": datetime.now().isoformat(),
                "metadata": metadata
            })
            
            # 클라이언트에 모델 메타데이터 전송
            await self._send_message(connection_id, MessageType.MODEL_METADATA, {
                "model_name": model_name,
                "metadata": metadata,
                "session_id": session_id
            })
            
            # 모델 로드 완료 알림
            await self._send_message(connection_id, MessageType.MODEL_LOADED, {
                "model_name": model_name,
                "session_id": session_id,
                "success": True
            })
            
            logger.info(f"Model {model_name} loaded for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling model load request: {e}")
            await self._send_message(connection_id, MessageType.ERROR, {
                "error": f"Failed to load model: {str(e)}"
            })
    
    async def _handle_expression_change_request(self, connection_id: str, data: Dict[str, Any]):
        """표정 변경 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
                
            session_id = session_data["session_id"]
            expression_index = data.get("expression_index", 0)
            duration = data.get("duration", 3000)
            fade_in = data.get("fade_in", 0.5)
            fade_out = data.get("fade_out", 0.5)
            
            # 캐릭터 상태 업데이트
            if session_id in self.character_states:
                self.character_states[session_id]["current_expression"] = expression_index
                self.character_states[session_id]["last_update"] = datetime.now().isoformat()
            
            # 세션의 모든 연결에 표정 업데이트 브로드캐스트
            await self.broadcast_to_session(session_id, MessageType.EXPRESSION_UPDATE, {
                "expression_index": expression_index,
                "duration": duration,
                "fade_in": fade_in,
                "fade_out": fade_out,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Expression changed to {expression_index} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling expression change request: {e}")
    
    async def _handle_motion_trigger_request(self, connection_id: str, data: Dict[str, Any]):
        """모션 트리거 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
                
            session_id = session_data["session_id"]
            motion_group = data.get("motion_group", "Idle")
            motion_index = data.get("motion_index", 0)
            priority = data.get("priority", 1)
            
            # 캐릭터 상태 업데이트
            if session_id in self.character_states:
                self.character_states[session_id]["current_motion"] = {
                    "group": motion_group,
                    "index": motion_index,
                    "triggered_at": datetime.now().isoformat()
                }
                self.character_states[session_id]["last_update"] = datetime.now().isoformat()
            
            # 세션의 모든 연결에 모션 트리거 브로드캐스트
            await self.broadcast_to_session(session_id, MessageType.MOTION_TRIGGER, {
                "motion_group": motion_group,
                "motion_index": motion_index,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Motion triggered: {motion_group}[{motion_index}] for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling motion trigger request: {e}")
    
    async def _handle_text_emotion_analysis(self, connection_id: str, data: Dict[str, Any]):
        """텍스트 감정 분석 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
                
            session_id = session_data["session_id"]
            text = data.get("text", "")
            context = data.get("context", {})
            model_name = data.get("model_name", "mao_pro")
            
            if not text:
                return
                
            # JavaScript 감정 매퍼를 사용하여 감정 분석
            emotion_result = await self._analyze_text_emotion_with_js(text, context, model_name)
            
            # 결과를 클라이언트에 전송
            await self._send_message(connection_id, MessageType.EMOTION_ANALYSIS_RESULT, {
                "text": text,
                "emotion_result": emotion_result,
                "session_id": session_id
            })
            
            # 자동으로 감정을 Live2D에 적용
            if data.get("auto_apply", True):
                await self._apply_emotion_to_live2d(session_id, emotion_result)
            
            logger.debug(f"Text emotion analyzed for session {session_id}: {emotion_result.get('primaryEmotion')}")
            
        except Exception as e:
            logger.error(f"Error handling text emotion analysis: {e}")
    
    async def _handle_fortune_emotion_sync(self, connection_id: str, data: Dict[str, Any]):
        """운세 기반 감정 동기화 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
                
            session_id = session_data["session_id"]
            fortune_result = data.get("fortune_result", {})
            user_message = data.get("user_message", "")
            model_name = data.get("model_name", "mao_pro")
            
            # 운세 결과와 사용자 메시지를 결합하여 감정 계산
            context = {
                "type": f"fortune_{fortune_result.get('fortune_type', 'daily')}",
                "fortuneResult": fortune_result
            }
            
            # 복합 감정 분석 (운세 + 텍스트)
            if user_message:
                emotion_result = await self._analyze_text_emotion_with_js(user_message, context, model_name)
            else:
                # 운세 결과만으로 감정 생성
                emotion_result = await self._analyze_fortune_only_emotion(fortune_result, model_name)
            
            # Live2D에 감정 적용
            await self._apply_emotion_to_live2d(session_id, emotion_result)
            
            # 클라이언트에 동기화 완료 알림
            await self._send_message(connection_id, MessageType.CHARACTER_STATE_UPDATE, {
                "emotion_result": emotion_result,
                "fortune_type": fortune_result.get("fortune_type"),
                "session_id": session_id
            })
            
            logger.info(f"Fortune emotion synchronized for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error handling fortune emotion sync: {e}")
    
    async def _handle_character_state_sync(self, connection_id: str, data: Dict[str, Any]):
        """캐릭터 상태 동기화 요청 처리"""
        try:
            session_data = self.sessions.get(connection_id)
            if not session_data:
                return
                
            session_id = session_data["session_id"]
            
            # 현재 캐릭터 상태 반환
            current_state = self.character_states.get(session_id, {})
            
            await self._send_message(connection_id, MessageType.CHARACTER_STATE_UPDATE, {
                "character_state": current_state,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error handling character state sync: {e}")
    
    async def _load_model_metadata_with_js(self, model_name: str) -> Dict[str, Any]:
        """JavaScript 모델 매니저를 사용하여 메타데이터 로드"""
        if not self.node_engine_available:
            return self._load_model_metadata_fallback(model_name)
        
        try:
            # Node.js 스크립트 생성
            script_content = f"""
const Live2dModelManager = require('{self.live2d_scripts_path}/model_manager.js');

async function loadModel() {{
    try {{
        const manager = new Live2dModelManager(
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d"}',
            '{Path(__file__).parent.parent.parent.parent / "static" / "live2d" / "model_dict.json"}'
        );
        
        await manager.initialize();
        const metadata = await manager.loadModelMetadata('{model_name}');
        console.log(JSON.stringify(metadata, null, 2));
    }} catch (error) {{
        console.error('Error:', error.message);
        process.exit(1);
    }}
}}

loadModel();
"""
            
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
                    timeout=30
                )
                
                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    logger.error(f"Node.js metadata loading failed: {result.stderr}")
                    return self._load_model_metadata_fallback(model_name)
                    
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            logger.error(f"Error loading model metadata with JavaScript: {e}")
            return self._load_model_metadata_fallback(model_name)
    
    def _load_model_metadata_fallback(self, model_name: str) -> Dict[str, Any]:
        """Python fallback for model metadata loading"""
        return {
            "name": model_name,
            "expressions": [],
            "motions": {},
            "parameters": [],
            "hitAreas": [],
            "emotionMap": {
                "neutral": 0,
                "joy": 3,
                "sadness": 1,
                "anger": 2,
                "surprise": 3,
                "fear": 1
            },
            "fallback": True
        }
    
    async def _analyze_text_emotion_with_js(self, text: str, context: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """JavaScript 감정 매퍼를 사용하여 텍스트 감정 분석"""
        if not self.node_engine_available:
            return self._analyze_text_emotion_fallback(text, context)
        
        try:
            # Node.js 스크립트 생성
            script_content = f"""
const EmotionMapper = require('{self.live2d_scripts_path}/emotion_mapper.js');

const mapper = new EmotionMapper();
const text = {json.dumps(text)};
const context = {json.dumps(context)};
const modelName = {json.dumps(model_name)};

try {{
    const result = mapper.mapEmotionsToExpressions(text, context, modelName);
    console.log(JSON.stringify(result, null, 2));
}} catch (error) {{
    console.error('Error:', error.message);
    process.exit(1);
}}
"""
            
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
                    timeout=30
                )
                
                if result.returncode == 0:
                    return json.loads(result.stdout)
                else:
                    logger.error(f"Node.js emotion analysis failed: {result.stderr}")
                    return self._analyze_text_emotion_fallback(text, context)
                    
            finally:
                os.unlink(script_path)
                
        except Exception as e:
            logger.error(f"Error analyzing emotion with JavaScript: {e}")
            return self._analyze_text_emotion_fallback(text, context)
    
    def _analyze_text_emotion_fallback(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Python fallback for emotion analysis"""
        # Simple keyword-based emotion detection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['기쁘', '행복', '좋아', 'happy', 'joy', 'good']):
            primary_emotion = 'joy'
            intensity = 0.7
            expression_index = 3
        elif any(word in text_lower for word in ['슬퍼', '우울', 'sad', 'sorry']):
            primary_emotion = 'sadness'
            intensity = 0.6
            expression_index = 1
        elif any(word in text_lower for word in ['화나', '짜증', 'angry', 'mad']):
            primary_emotion = 'anger'
            intensity = 0.8
            expression_index = 2
        elif any(word in text_lower for word in ['놀라', '깜짝', 'surprise', 'wow']):
            primary_emotion = 'surprise'
            intensity = 0.9
            expression_index = 3
        else:
            primary_emotion = 'neutral'
            intensity = 0.5
            expression_index = 0
        
        return {
            "primaryEmotion": primary_emotion,
            "intensity": intensity,
            "expressionIndex": expression_index,
            "duration": int(3000 * (0.8 + intensity * 0.4)),
            "fadeTiming": {"fadeIn": 0.5, "fadeOut": 0.5},
            "confidence": 0.6,
            "fallback": True
        }
    
    async def _analyze_fortune_only_emotion(self, fortune_result: Dict[str, Any], model_name: str) -> Dict[str, Any]:
        """운세 결과만으로 감정 분석"""
        score = fortune_result.get("overall_fortune", {}).get("score", 50)
        fortune_type = fortune_result.get("fortune_type", "daily")
        
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
    
    async def _apply_emotion_to_live2d(self, session_id: str, emotion_result: Dict[str, Any]):
        """감정 분석 결과를 Live2D에 적용"""
        try:
            # 배치 업데이트 큐에 추가
            if session_id not in self.pending_updates:
                self.pending_updates[session_id] = []
            
            update = {
                "type": "emotion_update",
                "expression_index": emotion_result.get("expressionIndex", 0),
                "duration": emotion_result.get("duration", 3000),
                "fade_timing": emotion_result.get("fadeTiming", {"fadeIn": 0.5, "fadeOut": 0.5}),
                "emotion": emotion_result.get("primaryEmotion", "neutral"),
                "intensity": emotion_result.get("intensity", 0.5),
                "timestamp": datetime.now().isoformat()
            }
            
            # 모션이 지정된 경우 추가
            if "motion" in emotion_result:
                motion = emotion_result["motion"]
                update["motion"] = {
                    "group": motion.get("motionGroup", "Idle"),
                    "index": motion.get("motionIndex", 0)
                }
            
            self.pending_updates[session_id].append(update)
            
            # 배치 타이머 설정 (100ms 후 일괄 전송)
            if session_id in self.batch_timers:
                self.batch_timers[session_id].cancel()
            
            self.batch_timers[session_id] = asyncio.create_task(
                self._send_batched_updates(session_id)
            )
            
        except Exception as e:
            logger.error(f"Error applying emotion to Live2D: {e}")
    
    async def _send_batched_updates(self, session_id: str):
        """배치된 업데이트 전송 (성능 최적화)"""
        try:
            await asyncio.sleep(0.1)  # 100ms 대기
            
            if session_id not in self.pending_updates or not self.pending_updates[session_id]:
                return
            
            updates = self.pending_updates[session_id].copy()
            self.pending_updates[session_id].clear()
            
            # 캐릭터 상태 업데이트
            if session_id in self.character_states:
                latest_update = updates[-1]  # 가장 최근 업데이트 사용
                self.character_states[session_id].update({
                    "current_emotion": latest_update.get("emotion"),
                    "current_expression": latest_update.get("expression_index"),
                    "last_update": datetime.now().isoformat()
                })
            
            # 세션의 모든 연결에 배치 업데이트 브로드캐스트
            await self.broadcast_to_session(session_id, MessageType.BATCH_LIVE2D_UPDATE, {
                "updates": updates,
                "session_id": session_id,
                "batch_size": len(updates),
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Sent {len(updates)} batched updates to session {session_id}")
            
        except Exception as e:
            logger.error(f"Error sending batched updates: {e}")
        finally:
            # 타이머 정리
            if session_id in self.batch_timers:
                del self.batch_timers[session_id]
    
    async def _trigger_interaction_response(self, session_id: str, interaction_type: str):
        """상호작용 반응 트리거"""
        # 데이터베이스 세션 획득
        db_session = next(get_db())
        
        try:
            if interaction_type == "greeting":
                from ..services.live2d_service import EmotionType, MotionType
                await self.live2d_service.set_combined_state(
                    db_session, session_id,
                    EmotionType.JOY, MotionType.GREETING,
                    "안녕하세요! 😊"
                )
            elif interaction_type == "attention":
                # 미세한 시선 움직임 (파라미터 업데이트)
                import random
                eye_x = random.uniform(-0.3, 0.3)
                eye_y = random.uniform(-0.2, 0.2)
                
                await self.live2d_service.set_live2d_parameters(
                    db_session, session_id,
                    {"ParamEyeBallX": eye_x, "ParamEyeBallY": eye_y},
                    duration=2000
                )
            elif interaction_type == "special":
                from ..services.live2d_service import EmotionType, MotionType
                await self.live2d_service.set_combined_state(
                    db_session, session_id,
                    EmotionType.PLAYFUL, MotionType.SPECIAL_READING,
                    "뭔가 특별한 일이 일어날 것 같아요! ✨"
                )
                
        finally:
            db_session.close()
    
    async def _stream_tts_to_client(self, connection_id: str, tts_request: TTSRequest):
        """클라이언트에게 TTS 스트리밍"""
        try:
            async for event in tts_service.synthesize_with_live2d_sync(tts_request):
                event_type = event["type"]
                event_data = event["data"]
                
                # WebSocket 메시지 타입으로 변환
                if event_type == "tts_start":
                    await self._send_message(connection_id, MessageType.TTS_START, event_data)
                elif event_type == "lipsync_update":
                    await self._send_message(connection_id, MessageType.TTS_LIPSYNC_UPDATE, event_data)
                elif event_type == "tts_complete":
                    await self._send_message(connection_id, MessageType.TTS_COMPLETE, event_data)
                elif event_type == "tts_error":
                    await self._send_message(connection_id, MessageType.TTS_ERROR, event_data)
                    
        except Exception as e:
            logger.error(f"Error streaming TTS to client: {e}")
            await self._send_message(connection_id, MessageType.TTS_ERROR, {
                "error": str(e),
                "session_id": tts_request.session_id
            })
    
    async def _send_message(self, connection_id: str, message_type: MessageType, data: Dict[str, Any]):
        """메시지 전송"""
        if connection_id not in self.connections:
            return
        
        websocket = self.connections[connection_id]
        message = {
            "type": message_type.value,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            await self.disconnect(connection_id)
    
    async def _send_error(self, connection_id: str, error_message: str):
        """에러 메시지 전송"""
        await self._send_message(connection_id, MessageType.ERROR, {
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        })
    
    def _determine_device_type(self, device_info: Dict[str, Any]) -> DeviceType:
        """디바이스 타입 결정"""
        user_agent = device_info.get("user_agent", "").lower()
        screen_width = device_info.get("screen_width", 1920)
        memory_gb = device_info.get("memory_gb", 8)
        cpu_cores = device_info.get("cpu_cores", 4)
        
        # 모바일 디바이스 감지
        if any(mobile in user_agent for mobile in ["mobile", "android", "iphone", "ipad"]):
            if memory_gb < 4 or cpu_cores < 4:
                return DeviceType.LOW_END
            elif screen_width < 768:
                return DeviceType.MOBILE
            else:
                return DeviceType.TABLET
        
        # 데스크톱 디바이스
        if memory_gb < 4 or cpu_cores < 2:
            return DeviceType.LOW_END
        elif screen_width < 1200:
            return DeviceType.TABLET
        else:
            return DeviceType.DESKTOP
    
    async def broadcast_to_session(self, session_id: str, message_type: MessageType, data: Dict[str, Any]):
        """세션의 모든 연결에 브로드캐스트"""
        if session_id not in self.session_connections:
            return
        
        connection_ids = self.session_connections[session_id].copy()
        for connection_id in connection_ids:
            await self._send_message(connection_id, message_type, data)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 통계"""
        active_connections = len(self.connections)
        active_sessions = len(self.session_connections)
        
        # 디바이스 타입별 통계
        device_stats = {}
        for session_data in self.sessions.values():
            device_type = session_data.get("device_type", DeviceType.DESKTOP)
            device_stats[device_type.value] = device_stats.get(device_type.value, 0) + 1
        
        return {
            "active_connections": active_connections,
            "active_sessions": active_sessions,
            "total_connections": self.connection_count,
            "error_count": self.error_count,
            "message_stats": self.message_stats,
            "device_distribution": device_stats,
            "uptime_seconds": (datetime.now() - datetime.now()).total_seconds()  # 실제로는 시작 시간 저장 필요
        }
    
    async def cleanup_stale_connections(self, timeout_minutes: int = 10):
        """오래된 연결 정리"""
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        stale_connections = []
        
        for connection_id, session_data in self.sessions.items():
            if session_data["last_heartbeat"] < cutoff_time:
                stale_connections.append(connection_id)
        
        for connection_id in stale_connections:
            logger.info(f"Cleaning up stale connection: {connection_id}")
            await self.disconnect(connection_id)
        
        return len(stale_connections)


# 전역 WebSocket 매니저 인스턴스
websocket_manager: Optional[Live2DWebSocketManager] = None

def get_websocket_manager() -> Live2DWebSocketManager:
    """WebSocket 매니저 싱글톤 인스턴스 반환"""
    global websocket_manager
    if websocket_manager is None:
        from ..services.live2d_service import Live2DService
        live2d_service = Live2DService()
        websocket_manager = Live2DWebSocketManager(live2d_service)
    return websocket_manager
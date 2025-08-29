"""
Real-time TTS-Live2D WebSocket Handler

Handles WebSocket TTS streaming with Live2D synchronization for real-time
voice-animation coordination. Based on todo specifications Phase 8.4.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, List, AsyncGenerator
from dataclasses import asdict
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from fastapi import WebSocket, WebSocketDisconnect

from ..tts.live2d_tts_manager import Live2DTTSManager, Live2DTTSRequest, live2d_tts_manager
from ..tts.tts_interface import TTSProviderError, TTSProviderUnavailableError
from ..tts.emotion_voice_processor import EmotionVoiceProcessor

logger = logging.getLogger(__name__)


class TtsLive2dWebSocketHandler:
    """
    WebSocket handler for real-time TTS-Live2D synchronization.
    
    Manages WebSocket connections and streams TTS audio with synchronized
    Live2D animation events in real-time.
    """
    
    def __init__(self, tts_manager: Live2DTTSManager = None):
        self.tts_manager = tts_manager or live2d_tts_manager
        self.emotion_processor = EmotionVoiceProcessor()
        
        # Active connections tracking
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("TTS-Live2D WebSocket handler initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Handle new WebSocket connection"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": time.time(),
                "last_activity": time.time(),
                "messages_sent": 0,
                "messages_received": 0,
                "active_sessions": []
            }
            
            logger.info(f"TTS WebSocket connected: {client_id}")
            
            # Send connection confirmation
            await self._send_message(websocket, {
                "type": "connection_established",
                "data": {
                    "client_id": client_id,
                    "server_time": time.time(),
                    "capabilities": {
                        "tts_streaming": True,
                        "live2d_sync": True,
                        "emotion_processing": True,
                        "multi_provider": True
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to establish WebSocket connection for {client_id}: {e}")
            await self._cleanup_connection(client_id)
            raise
    
    async def disconnect(self, client_id: str):
        """Handle WebSocket disconnection"""
        await self._cleanup_connection(client_id)
        logger.info(f"TTS WebSocket disconnected: {client_id}")
    
    async def handle_message(self, websocket: WebSocket, client_id: str, message: dict):
        """
        Handle incoming WebSocket message.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
            message: Parsed message data
        """
        try:
            # Update activity tracking
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["last_activity"] = time.time()
                self.connection_metadata[client_id]["messages_received"] += 1
            
            message_type = message.get("type")
            
            if message_type == "tts_request":
                await self._handle_tts_request(websocket, client_id, message.get("data", {}))
            
            elif message_type == "tts_stream_request":
                await self._handle_tts_stream_request(websocket, client_id, message.get("data", {}))
            
            elif message_type == "get_tts_providers":
                await self._handle_get_providers(websocket, client_id)
            
            elif message_type == "test_tts_voice":
                await self._handle_test_voice(websocket, client_id, message.get("data", {}))
            
            elif message_type == "cancel_tts":
                await self._handle_cancel_tts(websocket, client_id, message.get("data", {}))
            
            elif message_type == "ping":
                await self._handle_ping(websocket, client_id)
            
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")
            await self._send_error(websocket, f"Message processing error: {str(e)}")
    
    async def _handle_tts_request(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle single TTS request (non-streaming)"""
        try:
            # Parse request data
            tts_request = Live2DTTSRequest(
                text=data.get("text", ""),
                user_id=data.get("user_id", client_id),
                session_id=data.get("session_id", str(uuid.uuid4())),
                language=data.get("language", "ko-KR"),
                voice=data.get("voice"),
                speed=data.get("speed", 1.0),
                pitch=data.get("pitch", 1.0),
                volume=data.get("volume", 1.0),
                enable_lipsync=data.get("enable_lipsync", True),
                provider_override=data.get("provider_override"),
                enable_expressions=data.get("enable_expressions", True),
                enable_motions=data.get("enable_motions", True),
                expression_intensity=data.get("expression_intensity", 0.8),
                motion_blend_duration=data.get("motion_blend_duration", 0.5)
            )
            
            # Validate request
            if not tts_request.text.strip():
                await self._send_error(websocket, "Text is required for TTS generation")
                return
            
            logger.info(f"Processing TTS request from {client_id}: '{tts_request.text[:50]}...'")
            
            # Generate TTS with Live2D animation
            result = await self.tts_manager.generate_speech_with_animation(tts_request)
            
            # Send result to client
            await self._send_message(websocket, {
                "type": "tts_complete",
                "data": {
                    "session_id": tts_request.session_id,
                    "audio_data": result.tts_result.audio_data,
                    "audio_format": result.tts_result.audio_format,
                    "duration": result.total_duration,
                    "live2d_commands": result.live2d_commands,
                    "expression_timeline": [
                        {"timestamp": t, "expression": exp, "intensity": intens}
                        for t, exp, intens in result.expression_timeline
                    ],
                    "motion_timeline": [
                        {"timestamp": t, "motion": motion}
                        for t, motion in result.motion_timeline
                    ],
                    "synchronization_events": result.synchronization_events,
                    "provider_info": result.provider_info
                }
            })
            
        except TTSProviderUnavailableError as e:
            await self._send_error(websocket, f"No TTS providers available: {str(e)}")
        except TTSProviderError as e:
            await self._send_error(websocket, f"TTS generation failed: {str(e)}")
        except Exception as e:
            logger.error(f"TTS request processing error: {e}")
            await self._send_error(websocket, f"Internal server error: {str(e)}")
    
    async def _handle_tts_stream_request(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle streaming TTS request with real-time synchronization"""
        session_id = data.get("session_id", str(uuid.uuid4()))
        
        try:
            # Parse streaming request
            tts_request = Live2DTTSRequest(
                text=data.get("text", ""),
                user_id=data.get("user_id", client_id),
                session_id=session_id,
                language=data.get("language", "ko-KR"),
                voice=data.get("voice"),
                speed=data.get("speed", 1.0),
                pitch=data.get("pitch", 1.0),
                volume=data.get("volume", 1.0),
                enable_lipsync=data.get("enable_lipsync", True),
                provider_override=data.get("provider_override"),
                enable_expressions=data.get("enable_expressions", True),
                enable_motions=data.get("enable_motions", True),
                expression_intensity=data.get("expression_intensity", 0.8)
            )
            
            # Validate request
            if not tts_request.text.strip():
                await self._send_error(websocket, "Text is required for TTS streaming")
                return
            
            # Register active session
            self.active_sessions[session_id] = {
                "client_id": client_id,
                "request": tts_request,
                "start_time": time.time(),
                "status": "streaming"
            }
            
            if client_id in self.connection_metadata:
                self.connection_metadata[client_id]["active_sessions"].append(session_id)
            
            logger.info(f"Starting TTS stream for {client_id}, session: {session_id}")
            
            # Stream TTS with real-time Live2D synchronization
            async for stream_data in self.tts_manager.stream_live2d_tts(tts_request):
                # Check if session still active
                if session_id not in self.active_sessions:
                    break
                
                # Send streaming data to client
                await self._send_message(websocket, stream_data)
                
                # Small delay to prevent overwhelming client
                await asyncio.sleep(0.01)
            
            # Clean up session
            await self._cleanup_session(session_id)
            
        except WebSocketDisconnect:
            await self._cleanup_session(session_id)
            logger.info(f"Client {client_id} disconnected during streaming")
        except Exception as e:
            await self._cleanup_session(session_id)
            logger.error(f"TTS streaming error for {client_id}: {e}")
            await self._send_error(websocket, f"Streaming failed: {str(e)}")
    
    async def _handle_get_providers(self, websocket: WebSocket, client_id: str):
        """Handle request for available TTS providers"""
        try:
            providers = self.tts_manager.get_available_providers_for_user(client_id)
            
            await self._send_message(websocket, {
                "type": "tts_providers",
                "data": {
                    "providers": providers,
                    "default_language": "ko-KR",
                    "supported_languages": ["ko-KR", "en-US", "ja-JP", "zh-CN"]
                }
            })
            
        except Exception as e:
            logger.error(f"Failed to get TTS providers for {client_id}: {e}")
            await self._send_error(websocket, f"Failed to get providers: {str(e)}")
    
    async def _handle_test_voice(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle TTS voice testing request"""
        try:
            test_text = data.get("test_text", "안녕하세요! 이 목소리가 마음에 드시나요?")
            
            test_request = Live2DTTSRequest(
                text=test_text,
                user_id=client_id,
                session_id=f"test_{uuid.uuid4()}",
                language=data.get("language", "ko-KR"),
                voice=data.get("voice"),
                speed=data.get("speed", 1.0),
                pitch=data.get("pitch", 1.0),
                volume=data.get("volume", 1.0),
                provider_override=data.get("provider_id"),
                enable_lipsync=False,  # Skip lip-sync for test
                enable_expressions=False,  # Skip expressions for test
                enable_motions=False  # Skip motions for test
            )
            
            # Generate test audio
            result = await self.tts_manager.generate_speech_with_animation(test_request)
            
            # Send test result
            await self._send_message(websocket, {
                "type": "voice_test_result",
                "data": {
                    "audio_data": result.tts_result.audio_data,
                    "audio_format": result.tts_result.audio_format,
                    "duration": result.total_duration,
                    "provider_info": result.provider_info,
                    "test_text": test_text
                }
            })
            
        except Exception as e:
            logger.error(f"Voice test failed for {client_id}: {e}")
            await self._send_error(websocket, f"Voice test failed: {str(e)}")
    
    async def _handle_cancel_tts(self, websocket: WebSocket, client_id: str, data: dict):
        """Handle TTS cancellation request"""
        session_id = data.get("session_id")
        
        if session_id and session_id in self.active_sessions:
            await self._cleanup_session(session_id)
            
            await self._send_message(websocket, {
                "type": "tts_cancelled",
                "data": {
                    "session_id": session_id
                }
            })
            
            logger.info(f"TTS session cancelled: {session_id}")
        else:
            await self._send_error(websocket, f"Session not found: {session_id}")
    
    async def _handle_ping(self, websocket: WebSocket, client_id: str):
        """Handle ping/keepalive message"""
        await self._send_message(websocket, {
            "type": "pong",
            "data": {
                "server_time": time.time(),
                "client_id": client_id
            }
        })
    
    async def _send_message(self, websocket: WebSocket, message: dict):
        """Send message to WebSocket client with error handling"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            
            # Update metrics
            client_id = self._find_client_id_by_websocket(websocket)
            if client_id and client_id in self.connection_metadata:
                self.connection_metadata[client_id]["messages_sent"] += 1
                
        except ConnectionClosed:
            logger.warning("Attempted to send message to closed WebSocket connection")
        except WebSocketException as e:
            logger.error(f"WebSocket error sending message: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending WebSocket message: {e}")
    
    async def _send_error(self, websocket: WebSocket, error_message: str):
        """Send error message to WebSocket client"""
        await self._send_message(websocket, {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": time.time()
            }
        })
    
    def _find_client_id_by_websocket(self, websocket: WebSocket) -> Optional[str]:
        """Find client ID by WebSocket connection"""
        for client_id, ws in self.active_connections.items():
            if ws is websocket:
                return client_id
        return None
    
    async def _cleanup_connection(self, client_id: str):
        """Clean up WebSocket connection and associated resources"""
        # Cancel active sessions for this client
        if client_id in self.connection_metadata:
            sessions_to_cancel = self.connection_metadata[client_id]["active_sessions"].copy()
            for session_id in sessions_to_cancel:
                await self._cleanup_session(session_id)
        
        # Remove connection tracking
        self.active_connections.pop(client_id, None)
        self.connection_metadata.pop(client_id, None)
    
    async def _cleanup_session(self, session_id: str):
        """Clean up TTS session"""
        if session_id in self.active_sessions:
            session_info = self.active_sessions.pop(session_id)
            client_id = session_info.get("client_id")
            
            # Remove from client's active sessions
            if client_id and client_id in self.connection_metadata:
                active_sessions = self.connection_metadata[client_id]["active_sessions"]
                if session_id in active_sessions:
                    active_sessions.remove(session_id)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "active_connections": len(self.active_connections),
            "active_sessions": len(self.active_sessions),
            "connection_metadata": {
                client_id: {
                    "connected_at": metadata["connected_at"],
                    "last_activity": metadata["last_activity"],
                    "messages_sent": metadata["messages_sent"],
                    "messages_received": metadata["messages_received"],
                    "active_sessions_count": len(metadata["active_sessions"])
                }
                for client_id, metadata in self.connection_metadata.items()
            },
            "tts_statistics": self.tts_manager.get_tts_statistics()
        }
    
    async def broadcast_tts_update(self, message: dict, target_clients: List[str] = None):
        """Broadcast TTS update to clients"""
        target_connections = {}
        
        if target_clients:
            for client_id in target_clients:
                if client_id in self.active_connections:
                    target_connections[client_id] = self.active_connections[client_id]
        else:
            target_connections = self.active_connections
        
        # Send to all target connections
        for client_id, websocket in target_connections.items():
            try:
                await self._send_message(websocket, message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on TTS WebSocket system"""
        try:
            # Check TTS manager health
            provider_health = await self.tts_manager.tts_factory.health_check_all_providers()
            
            # Check active connections
            stale_connections = []
            current_time = time.time()
            
            for client_id, metadata in self.connection_metadata.items():
                if current_time - metadata["last_activity"] > 300:  # 5 minutes
                    stale_connections.append(client_id)
            
            return {
                "status": "healthy",
                "active_connections": len(self.active_connections),
                "active_sessions": len(self.active_sessions),
                "stale_connections": len(stale_connections),
                "provider_health": provider_health,
                "memory_usage": {
                    "connection_metadata_size": len(self.connection_metadata),
                    "active_sessions_size": len(self.active_sessions)
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global handler instance
tts_live2d_handler = TtsLive2dWebSocketHandler()
"""
Live2D Service - Live2D 캐릭터 상태 관리 및 제어

8가지 감정 표현과 6가지 모션 애니메이션 제어
운세 결과와 연동된 실시간 캐릭터 반응 시스템
WebSocket을 통한 실시간 상태 동기화
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
import logging

from sqlalchemy.orm import Session

from ..models.live2d import Live2DModel, Live2DSessionModel
from ..models.chat import ChatSession
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class Live2DState:
    """Live2D character state representation"""
    
    def __init__(self, session_id: str, model_name: str = "mira"):
        self.session_id = session_id
        self.model_name = model_name
        self.current_emotion = "neutral"
        self.current_motion = None
        self.is_speaking = False
        self.emotion_queue = []
        self.motion_queue = []
        self.last_updated = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "session_id": self.session_id,
            "model_name": self.model_name,
            "current_emotion": self.current_emotion,
            "current_motion": self.current_motion,
            "is_speaking": self.is_speaking,
            "last_updated": self.last_updated.isoformat()
        }


class EmotionType(str, Enum):
    """Live2D 감정 타입"""
    NEUTRAL = "neutral"
    JOY = "joy"
    THINKING = "thinking"
    CONCERN = "concern"
    SURPRISE = "surprise"
    MYSTICAL = "mystical"
    COMFORT = "comfort"
    PLAYFUL = "playful"


class MotionType(str, Enum):
    """Live2D 모션 타입"""
    GREETING = "greeting"
    CARD_DRAW = "card_draw"
    CRYSTAL_GAZE = "crystal_gaze"
    BLESSING = "blessing"
    SPECIAL_READING = "special_reading"
    THINKING_POSE = "thinking_pose"


class Live2DCharacterConfig:
    """Live2D 캐릭터 설정"""
    
    CHARACTER_NAME = "미라"
    MODEL_PATH = "/static/live2d/mira/mira.model3.json"
    
    # 감정 타입별 표정 매핑
    EMOTIONS = {
        EmotionType.NEUTRAL: {
            "id": 0,
            "name": "중립",
            "description": "기본 평온한 표정",
            "parameter": "ParamEyeLOpen",
            "value": 1.0,
            "duration": 0
        },
        EmotionType.JOY: {
            "id": 1,
            "name": "기쁨",
            "description": "밝고 즐거운 표정",
            "parameter": "ParamMouthForm",
            "value": 1.0,
            "duration": 3000
        },
        EmotionType.THINKING: {
            "id": 2,
            "name": "사색",
            "description": "생각에 잠긴 표정",
            "parameter": "ParamEyeLOpen",
            "value": 0.6,
            "duration": 5000
        },
        EmotionType.CONCERN: {
            "id": 3,
            "name": "걱정",
            "description": "걱정스러운 표정",
            "parameter": "ParamBrowLY",
            "value": -0.5,
            "duration": 4000
        },
        EmotionType.SURPRISE: {
            "id": 4,
            "name": "놀람",
            "description": "깜짝 놀란 표정",
            "parameter": "ParamEyeLOpen",
            "value": 1.2,
            "duration": 2000
        },
        EmotionType.MYSTICAL: {
            "id": 5,
            "name": "신비",
            "description": "신비로운 운세 해석 중",
            "parameter": "ParamEyeLOpen",
            "value": 0.8,
            "duration": 6000
        },
        EmotionType.COMFORT: {
            "id": 6,
            "name": "위로",
            "description": "따뜻하고 위로하는 표정",
            "parameter": "ParamMouthForm",
            "value": 0.7,
            "duration": 4000
        },
        EmotionType.PLAYFUL: {
            "id": 7,
            "name": "장난",
            "description": "장난스럽고 귀여운 표정",
            "parameter": "ParamMouthForm",
            "value": 1.2,
            "duration": 3000
        }
    }
    
    # 모션 타입별 애니메이션 매핑
    MOTIONS = {
        MotionType.GREETING: {
            "id": "greeting",
            "name": "인사",
            "description": "반갑게 인사하는 모션",
            "file": "motions/greeting.motion3.json",
            "duration": 3000,
            "loop": False
        },
        MotionType.CARD_DRAW: {
            "id": "card_draw",
            "name": "카드 뽑기",
            "description": "타로 카드를 뽑는 모션",
            "file": "motions/card_draw.motion3.json",
            "duration": 4000,
            "loop": False
        },
        MotionType.CRYSTAL_GAZE: {
            "id": "crystal_gaze",
            "name": "수정구 응시",
            "description": "수정구를 들여다보는 모션",
            "file": "motions/crystal_gaze.motion3.json",
            "duration": 5000,
            "loop": True
        },
        MotionType.BLESSING: {
            "id": "blessing",
            "name": "축복",
            "description": "축복을 내리는 모션",
            "file": "motions/blessing.motion3.json",
            "duration": 4000,
            "loop": False
        },
        MotionType.SPECIAL_READING: {
            "id": "special_reading",
            "name": "특별 해석",
            "description": "사주나 특별한 운세 해석 모션",
            "file": "motions/special_reading.motion3.json",
            "duration": 6000,
            "loop": False
        },
        MotionType.THINKING_POSE: {
            "id": "thinking_pose",
            "name": "생각하는 자세",
            "description": "깊게 생각하는 자세",
            "file": "motions/thinking_pose.motion3.json",
            "duration": 5000,
            "loop": True
        }
    }
    
    # 운세별 추천 감정/모션 조합
    FORTUNE_REACTIONS = {
        "excellent": {
            "emotion": EmotionType.JOY,
            "motion": MotionType.BLESSING,
            "messages": [
                "와! 정말 좋은 운세가 나왔어요! ✨",
                "오늘은 특별한 날이 될 것 같네요! 💫",
                "이런 훌륭한 운세는 정말 드물어요!"
            ]
        },
        "good": {
            "emotion": EmotionType.COMFORT,
            "motion": MotionType.BLESSING,
            "messages": [
                "좋은 운세가 나왔어요! 😊",
                "긍정적인 에너지가 느껴져요!",
                "오늘 하루 기대해봐도 좋겠어요!"
            ]
        },
        "normal": {
            "emotion": EmotionType.NEUTRAL,
            "motion": MotionType.THINKING_POSE,
            "messages": [
                "평범하지만 안정적인 하루가 될 것 같아요.",
                "차분하게 하루를 보내시면 좋겠어요.",
                "작은 행복을 찾아보는 하루가 되길 바라요."
            ]
        },
        "caution": {
            "emotion": EmotionType.CONCERN,
            "motion": MotionType.THINKING_POSE,
            "messages": [
                "조금 주의가 필요한 하루예요.",
                "신중하게 행동하시는 것이 좋겠어요.",
                "차분하게 하루를 보내시길 바라요."
            ]
        },
        "tarot": {
            "emotion": EmotionType.MYSTICAL,
            "motion": MotionType.CARD_DRAW,
            "messages": [
                "카드가 말하는 메시지를 들어보세요...",
                "신비로운 타로의 힘이 느껴져요.",
                "카드들이 특별한 이야기를 들려주고 있어요."
            ]
        },
        "zodiac": {
            "emotion": EmotionType.MYSTICAL,
            "motion": MotionType.CRYSTAL_GAZE,
            "messages": [
                "별들이 전하는 메시지를 읽고 있어요...",
                "우주의 에너지가 당신을 둘러싸고 있어요.",
                "별자리의 신비로운 힘이 느껴져요."
            ]
        },
        "oriental": {
            "emotion": EmotionType.MYSTICAL,
            "motion": MotionType.SPECIAL_READING,
            "messages": [
                "사주에 담긴 깊은 의미를 해석하고 있어요...",
                "당신의 운명이 사주에 새겨져 있네요.",
                "오랜 지혜가 담긴 사주의 비밀을 읽고 있어요."
            ]
        }
    }


class Live2DService:
    """Live2D 캐릭터 상태 관리 서비스"""
    
    def __init__(self, database_service=None, cache_service: CacheService = None):
        self.database_service = database_service
        self.cache_service = cache_service or CacheService()
        self.config = Live2DCharacterConfig()
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, Set] = {}  # session_id -> Set[websocket]
        self._initialized = False
    
    async def initialize(self):
        """Initialize Live2D service"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("Live2DService initialized")
    
    async def shutdown(self):
        """Shutdown Live2D service"""
        # Close all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self.close_session(session_id)
        self._initialized = False
        logger.info("Live2DService shutdown")
    
    async def close_session(self, session_id: str):
        """Close Live2D session and cleanup resources"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
        logger.debug(f"Live2D session closed: {session_id}")
        
    async def create_live2d_session(self, db: Session, session_id: str,
                                  user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """Live2D 세션 생성"""
        try:
            # 기존 세션 확인
            existing_session = Live2DSessionModel.find_by_session_id(db, session_id)
            
            if existing_session and existing_session.is_active:
                # 기존 활성 세션 반환
                return await self._get_session_state(existing_session)
            
            # 새 세션 생성
            live2d_session = Live2DSessionModel(
                session_id=session_id,
                user_uuid=user_uuid,
                model_name="mira",
                current_emotion=EmotionType.NEUTRAL.value,
                current_motion=None,
                is_active=True
            )
            
            db.add(live2d_session)
            db.commit()
            
            # 초기 상태 설정
            initial_state = await self._create_initial_state(db, live2d_session)
            
            # 활성 세션 메모리에 저장
            self.active_sessions[session_id] = {
                "live2d_session": live2d_session,
                "current_state": initial_state,
                "last_updated": datetime.now(),
                "websockets": set()
            }
            
            logger.info(f"Live2D session created: {session_id}")
            return await self._get_session_state(live2d_session)
            
        except Exception as e:
            logger.error(f"Error creating Live2D session: {e}")
            db.rollback()
            raise
    
    async def _ensure_active_session(self, db: Session, session_id: str) -> Dict[str, Any]:
        """Active session 확보 - User Session과 연동하여 Live2D session 생성/조회"""
        try:
            # 1. 이미 active_sessions에 있으면 반환
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # 2. 데이터베이스에서 Live2D session 찾기
            live2d_session = Live2DSessionModel.find_by_session_id(db, session_id)
            
            if live2d_session:
                # Live2D session이 있으면 active_sessions에 추가
                session_data = {
                    "live2d_session": live2d_session,
                    "websockets": set(),
                    "last_updated": datetime.now()
                }
                self.active_sessions[session_id] = session_data
                return session_data
            
            # 3. User session을 기반으로 Live2D session 생성
            from ..models.user import UserSession
            user_session = UserSession.find_by_session_id(db, session_id)
            
            if user_session and user_session.is_active:
                # User session이 활성상태면 Live2D session 생성
                new_live2d_session = Live2DSessionModel(
                    session_id=session_id,
                    user_uuid=user_session.user_uuid,
                    model_name="mira",
                    current_emotion=EmotionType.NEUTRAL.value,
                    current_motion=None,
                    is_active=True
                )
                
                db.add(new_live2d_session)
                db.commit()
                
                # active_sessions에 추가
                session_data = {
                    "live2d_session": new_live2d_session,
                    "websockets": set(),
                    "last_updated": datetime.now()
                }
                self.active_sessions[session_id] = session_data
                
                logger.info(f"Live2D session auto-created from user session: {session_id}")
                return session_data
            
            # 4. 모든 방법으로 찾지 못하면 예외
            raise ValueError(f"No valid session found for session_id: {session_id}")
            
        except Exception as e:
            logger.error(f"Error ensuring active session {session_id}: {e}")
            raise

    async def change_emotion(self, db: Session, session_id: str, 
                           emotion_type: EmotionType,
                           duration: Optional[int] = None) -> Dict[str, Any]:
        """감정 변경"""
        try:
            # Active session 확보 (User Session과 연동)
            session_data = await self._ensure_active_session(db, session_id)
            live2d_session = session_data["live2d_session"]
            emotion_config = self.config.EMOTIONS[emotion_type]
            
            # 감정 상태 업데이트
            live2d_session.current_emotion = emotion_type.value
            live2d_session.last_emotion_change = datetime.now()
            
            # 데이터베이스 업데이트
            live2d_session.updated_at = datetime.now()
            db.commit()
            
            # 세션 상태 업데이트
            session_data["last_updated"] = datetime.now()
            
            # WebSocket 브로드캐스트
            await self._broadcast_state_change(session_id, "emotion_change", {
                "emotion": emotion_type.value,
                "emotion_config": emotion_config,
                "duration": duration or emotion_config["duration"]
            })
            
            logger.info(f"Emotion changed to {emotion_type.value} for session {session_id}")
            return await self._get_session_state(live2d_session)
            
        except Exception as e:
            logger.error(f"Error changing emotion: {e}")
            db.rollback()
            raise
    
    async def execute_motion(self, db: Session, session_id: str,
                           motion_type: MotionType,
                           loop: Optional[bool] = None,
                           duration: Optional[int] = None) -> Dict[str, Any]:
        """모션 실행"""
        try:
            # Active session 확보 (User Session과 연동)
            session_data = await self._ensure_active_session(db, session_id)
            live2d_session = session_data["live2d_session"]
            motion_config = self.config.MOTIONS[motion_type]
            
            # 모션 상태 업데이트
            live2d_session.current_motion = motion_type.value
            live2d_session.last_motion_change = datetime.now()
            
            # 데이터베이스 업데이트
            live2d_session.updated_at = datetime.now()
            db.commit()
            
            # 세션 상태 업데이트
            session_data["last_updated"] = datetime.now()
            
            # WebSocket 브로드캐스트
            await self._broadcast_state_change(session_id, "motion_change", {
                "motion": motion_type.value,
                "motion_config": motion_config,
                "loop": loop if loop is not None else motion_config["loop"],
                "duration": duration or motion_config["duration"]
            })
            
            logger.info(f"Motion {motion_type.value} executed for session {session_id}")
            return await self._get_session_state(live2d_session)
            
        except Exception as e:
            logger.error(f"Error executing motion: {e}")
            db.rollback()
            raise
    
    async def set_combined_state(self, db: Session, session_id: str,
                               emotion_type: EmotionType, motion_type: MotionType,
                               message: Optional[str] = None) -> Dict[str, Any]:
        """감정과 모션을 동시에 설정"""
        try:
            # Active session 확보 (User Session과 연동)
            session_data = await self._ensure_active_session(db, session_id)
            live2d_session = session_data["live2d_session"]
            emotion_config = self.config.EMOTIONS[emotion_type]
            motion_config = self.config.MOTIONS[motion_type]
            
            # 상태 업데이트
            live2d_session.current_emotion = emotion_type.value
            live2d_session.current_motion = motion_type.value
            live2d_session.last_emotion_change = datetime.now()
            live2d_session.last_motion_change = datetime.now()
            
            # 데이터베이스 업데이트
            live2d_session.updated_at = datetime.now()
            db.commit()
            
            # 세션 상태 업데이트
            session_data["last_updated"] = datetime.now()
            
            # WebSocket 브로드캐스트
            await self._broadcast_state_change(session_id, "combined_change", {
                "emotion": emotion_type.value,
                "motion": motion_type.value,
                "emotion_config": emotion_config,
                "motion_config": motion_config,
                "message": message
            })
            
            logger.info(f"Combined state set: {emotion_type.value} + {motion_type.value} for session {session_id}")
            return await self._get_session_state(live2d_session)
            
        except Exception as e:
            logger.error(f"Error setting combined state: {e}")
            db.rollback()
            raise
    
    async def react_to_fortune(self, db: Session, session_id: str,
                             fortune_result: Dict[str, Any]) -> Dict[str, Any]:
        """운세 결과에 따른 자동 반응"""
        try:
            fortune_type = fortune_result.get("fortune_type", "daily")
            
            # 운세별 반응 설정 가져오기
            if fortune_type in ["daily"]:
                overall_grade = fortune_result.get("overall_fortune", {}).get("grade", "normal")
                reaction_config = self.config.FORTUNE_REACTIONS.get(overall_grade, 
                                                                  self.config.FORTUNE_REACTIONS["normal"])
            else:
                reaction_config = self.config.FORTUNE_REACTIONS.get(fortune_type,
                                                                  self.config.FORTUNE_REACTIONS["normal"])
            
            # 메시지 선택
            import random
            message = random.choice(reaction_config["messages"])
            
            # 감정과 모션 설정
            result = await self.set_combined_state(
                db, session_id,
                reaction_config["emotion"],
                reaction_config["motion"],
                message
            )
            
            # 추가 정보 포함
            result["fortune_reaction"] = {
                "fortune_type": fortune_type,
                "grade": fortune_result.get("overall_fortune", {}).get("grade") if fortune_type == "daily" else None,
                "message": message,
                "auto_triggered": True
            }
            
            logger.info(f"Fortune reaction triggered for session {session_id}: {fortune_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error reacting to fortune: {e}")
            raise
    
    async def get_session_status(self, db: Session, session_id: str) -> Dict[str, Any]:
        """세션 상태 조회"""
        try:
            # Active session 확보 (User Session과 연동)
            session_data = await self._ensure_active_session(db, session_id)
            live2d_session = session_data["live2d_session"]
            
            return await self._get_session_state(live2d_session)
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            raise
    
    async def get_character_info(self) -> Dict[str, Any]:
        """캐릭터 정보 조회"""
        return {
            "character_name": self.config.CHARACTER_NAME,
            "model_path": self.config.MODEL_PATH,
            "emotions": {
                emotion_type.value: {
                    "id": config["id"],
                    "name": config["name"],
                    "description": config["description"]
                }
                for emotion_type, config in self.config.EMOTIONS.items()
            },
            "motions": {
                motion_type.value: {
                    "id": config["id"],
                    "name": config["name"],
                    "description": config["description"],
                    "file": config["file"],
                    "duration": config["duration"],
                    "loop": config["loop"]
                }
                for motion_type, config in self.config.MOTIONS.items()
            },
            "available_reactions": list(self.config.FORTUNE_REACTIONS.keys())
        }
    
    async def register_websocket(self, session_id: str, websocket):
        """WebSocket 연결 등록"""
        if session_id not in self.websocket_connections:
            self.websocket_connections[session_id] = set()
        
        self.websocket_connections[session_id].add(websocket)
        
        # 활성 세션에도 등록
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["websockets"].add(websocket)
        
        logger.info(f"WebSocket registered for session {session_id}")
    
    async def unregister_websocket(self, session_id: str, websocket):
        """WebSocket 연결 해제"""
        if session_id in self.websocket_connections:
            self.websocket_connections[session_id].discard(websocket)
            
            # 빈 연결 세트 정리
            if not self.websocket_connections[session_id]:
                del self.websocket_connections[session_id]
        
        # 활성 세션에서도 제거
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["websockets"].discard(websocket)
        
        logger.info(f"WebSocket unregistered for session {session_id}")
    
    async def cleanup_inactive_sessions(self, db: Session, hours: int = 24):
        """비활성 세션 정리"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 메모리에서 오래된 세션 제거
            expired_sessions = []
            for session_id, session_data in self.active_sessions.items():
                if session_data["last_updated"] < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                # WebSocket 연결 정리
                if session_id in self.websocket_connections:
                    del self.websocket_connections[session_id]
                
                del self.active_sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")
            
            # 데이터베이스에서 비활성화
            inactive_sessions = Live2DSessionModel.find_inactive_sessions(db, cutoff_time)
            for session in inactive_sessions:
                session.is_active = False
                session.ended_at = datetime.now()
            
            if inactive_sessions:
                db.commit()
                logger.info(f"Deactivated {len(inactive_sessions)} inactive sessions")
            
            return len(expired_sessions) + len(inactive_sessions)
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            db.rollback()
            raise
    
    # Private methods
    async def _create_initial_state(self, db: Session, live2d_session: Live2DSessionModel) -> Dict[str, Any]:
        """초기 상태 생성"""
        # Just return the current session state
        return await self._get_session_state(live2d_session)
    
    async def _get_session_state(self, live2d_session: Live2DSessionModel) -> Dict[str, Any]:
        """세션 상태 반환"""
        return {
            "session_id": live2d_session.session_id,
            "character_name": self.config.CHARACTER_NAME,
            "model_path": self.config.MODEL_PATH,
            "current_emotion": live2d_session.current_emotion,
            "current_motion": live2d_session.current_motion,
            "is_active": live2d_session.is_active,
            "created_at": live2d_session.created_at.isoformat(),
            "last_emotion_change": live2d_session.last_emotion_change.isoformat() if live2d_session.last_emotion_change else None,
            "last_motion_change": live2d_session.last_motion_change.isoformat() if live2d_session.last_motion_change else None,
            "emotion_config": self.config.EMOTIONS.get(EmotionType(live2d_session.current_emotion)),
            "motion_config": self.config.MOTIONS.get(MotionType(live2d_session.current_motion)) if live2d_session.current_motion else None
        }
    
    async def _format_state_response(self, state: Live2DState) -> Dict[str, Any]:
        """상태 응답 포맷"""
        return {
            "session_id": state.session_id,
            "state_type": state.state_type,
            "emotion": state.emotion,
            "motion": state.motion,
            "parameters": state.parameters_dict,
            "timestamp": state.created_at.isoformat()
        }
    
    async def _broadcast_state_change(self, session_id: str, change_type: str, data: Dict[str, Any]):
        """WebSocket을 통한 상태 변경 브로드캐스트"""
        if session_id not in self.websocket_connections:
            return
        
        message = {
            "type": "live2d_action",
            "data": {
                "session_id": session_id,
                "change_type": change_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
        }
        
        # 연결된 모든 WebSocket에 브로드캐스트
        disconnected_websockets = set()
        for websocket in self.websocket_connections[session_id]:
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected_websockets.add(websocket)
        
        # 끊어진 연결 정리
        for websocket in disconnected_websockets:
            await self.unregister_websocket(session_id, websocket)
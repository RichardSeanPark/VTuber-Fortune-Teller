"""
Chat Service - 실시간 채팅 서비스

WebSocket 기반 실시간 메시지 송수신
콘텐츠 필터링 및 운세 관련 대화 유도
Live2D 캐릭터와의 상호작용 관리
"""

import asyncio
import json
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import logging

from sqlalchemy.orm import Session
from fastapi import WebSocket, WebSocketDisconnect

from ..models.chat import ChatSession, ChatMessage
from ..services.fortune_service import FortuneService
from ..security.content_filter import ContentFilter, FilterResult
from .cache_service import CacheService

logger = logging.getLogger(__name__)




class MessageIntent(str, Enum):
    """메시지 의도 분류"""
    FORTUNE_REQUEST = "fortune_request"
    DAILY_FORTUNE = "daily_fortune"
    TAROT_FORTUNE = "tarot_fortune"
    ZODIAC_FORTUNE = "zodiac_fortune"
    ORIENTAL_FORTUNE = "oriental_fortune"
    GREETING = "greeting"
    CASUAL_CHAT = "casual_chat"
    QUESTION = "question"
    COMPLIMENT = "compliment"
    INAPPROPRIATE = "inappropriate"
    UNKNOWN = "unknown"




class ChatService:
    """채팅 서비스"""
    
    def __init__(self, database_service = None, cache_service: CacheService = None, 
                 live2d_service = None, fortune_service: FortuneService = None):
        self.database_service = database_service
        self.cache_service = cache_service 
        self.live2d_service = live2d_service
        self.fortune_service = fortune_service
        self.content_filter = ContentFilter()
        
        # 활성 연결 관리
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.connection_heartbeats: Dict[str, Dict[WebSocket, datetime]] = {}
        self.heartbeat_interval = 30  # 30 seconds
        self.connection_timeout = 300  # 5 minutes
        
        # 응답 템플릿
        self.response_templates = self._load_response_templates()
        self._initialized = False
    
    async def initialize(self):
        """서비스 초기화"""
        if self._initialized:
            return
        
        # FortuneService 지연 초기화
        if not self.fortune_service:
            from .fortune_service import FortuneService
            self.fortune_service = FortuneService(self.database_service, self.cache_service)
            await self.fortune_service.initialize()
        
        # Live2DService 지연 초기화
        if not self.live2d_service:
            from .live2d_service import Live2DService  
            self.live2d_service = Live2DService(self.database_service, self.cache_service)
            await self.live2d_service.initialize()
        
        self._initialized = True
    
    async def shutdown(self):
        """서비스 종료"""
        if not self._initialized:
            return
        
        # 모든 WebSocket 연결 종료
        for session_id, connections in self.active_connections.items():
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception:
                    pass
        
        self.active_connections.clear()
        self.session_data.clear()
        self._initialized = False
    
    def _load_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """응답 템플릿 로드"""
        return {
            MessageIntent.GREETING: {
                "responses": [
                    "안녕하세요! 저는 미라예요. 오늘 운세가 궁금하신가요? ✨",
                    "반가워요! 운세 상담을 도와드릴게요. 어떤 운세가 궁금하세요?",
                    "안녕하세요! 오늘 하루 어떤 운이 기다리고 있는지 알아볼까요?"
                ],
                "emotion": "joy",
                "motion": "greeting"
            },
            MessageIntent.FORTUNE_REQUEST: {
                "responses": [
                    "어떤 운세를 봐드릴까요? 일일운세, 타로, 별자리, 사주 중에서 선택해주세요!",
                    "운세가 궁금하시군요! 어떤 종류의 운세를 원하시나요?",
                    "좋아요! 일일운세, 타로카드, 별자리, 사주 중 어떤 것이 궁금하세요?"
                ],
                "emotion": "mystical",
                "motion": "thinking_pose"
            },
            MessageIntent.DAILY_FORTUNE: {
                "responses": [
                    "오늘의 운세를 봐드릴게요! 잠시만 기다려주세요... 🔮",
                    "일일운세를 확인해보고 있어요. 곧 알려드릴게요!",
                    "오늘 하루의 운을 살펴보고 있어요. 기대해주세요!"
                ],
                "emotion": "mystical",
                "motion": "crystal_gaze"
            },
            MessageIntent.TAROT_FORTUNE: {
                "responses": [
                    "타로카드를 준비하고 있어요! 어떤 질문이 있으신가요? 🔮",
                    "신비로운 타로의 힘으로 답을 찾아드릴게요. 질문을 말씀해주세요!",
                    "카드들이 메시지를 전하고 싶어해요. 무엇이 궁금하신가요?"
                ],
                "emotion": "mystical",
                "motion": "card_draw"
            },
            MessageIntent.ZODIAC_FORTUNE: {
                "responses": [
                    "별자리 운세를 봐드릴게요! 어떤 별자리세요? ⭐",
                    "별들이 전하는 메시지를 읽어드릴게요. 별자리를 알려주세요!",
                    "천체의 움직임을 살펴보고 있어요. 별자리가 무엇인가요?"
                ],
                "emotion": "mystical",
                "motion": "crystal_gaze"
            },
            MessageIntent.ORIENTAL_FORTUNE: {
                "responses": [
                    "사주를 봐드릴게요! 생년월일시를 알려주시면 더 정확해요.",
                    "동양의 깊은 지혜로 운명을 읽어드릴게요. 생년월일을 말씀해주세요!",
                    "사주팔자에 담긴 비밀을 풀어드릴게요. 언제 태어나셨나요?"
                ],
                "emotion": "mystical",
                "motion": "special_reading"
            },
            MessageIntent.COMPLIMENT: {
                "responses": [
                    "고마워요! 당신도 정말 멋지세요! 😊",
                    "칭찬해주셔서 감사해요! 기분이 좋아져요!",
                    "와! 그런 말씀 해주시니 정말 기뻐요! ✨"
                ],
                "emotion": "joy",
                "motion": "blessing"
            },
            MessageIntent.QUESTION: {
                "responses": [
                    "궁금한 게 있으시군요! 운세와 관련된 질문이라면 언제든 답해드릴게요.",
                    "질문이 있으시네요! 무엇이든 물어보세요!",
                    "답해드릴 수 있는 건 도와드릴게요. 어떤 게 궁금하세요?"
                ],
                "emotion": "thinking",
                "motion": "thinking_pose"
            },
            MessageIntent.CASUAL_CHAT: {
                "responses": [
                    "네, 말씀해주세요! 운세와 관련된 이야기라면 더욱 좋겠어요!",
                    "좋아요! 어떤 이야기를 나누고 싶으세요?",
                    "대화하는 걸 좋아해요! 운세에 대해 더 궁금한 건 없나요?"
                ],
                "emotion": "comfort",
                "motion": "thinking_pose"
            },
            "inappropriate": {
                "responses": [
                    "죄송해요, 그런 이야기는 할 수 없어요. 운세에 대해 이야기해볼까요?",
                    "음... 다른 주제로 이야기하면 좋겠어요. 오늘 운세는 어떠신지 궁금해요!",
                    "그런 내용보다는 긍정적인 운세 이야기를 해봐요! 😊"
                ],
                "emotion": "concern",
                "motion": "thinking_pose"
            },
            "error": {
                "responses": [
                    "죄송해요, 잠시 문제가 있었어요. 다시 말씀해주시겠어요?",
                    "앗, 무언가 잘못되었네요. 다시 한 번 시도해주세요!",
                    "시스템에 작은 문제가 있었어요. 다시 이야기해볼까요?"
                ],
                "emotion": "concern",
                "motion": "thinking_pose"
            }
        }
    
    async def create_chat_session(self, db: Session, session_id: str,
                                user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """채팅 세션 생성"""
        try:
            # 기존 세션 확인
            existing_session = ChatSession.find_by_session_id(db, session_id)
            
            if existing_session and existing_session.is_active:
                # 기존 활성 세션 반환
                return self._format_session_response(existing_session)
            
            
            # 채팅 세션 생성
            chat_session = ChatSession(
                session_id=session_id,
                user_uuid=user_uuid,
                character_name="미라",
                is_active=True
            )
            
            db.add(chat_session)
            db.commit()
            
            # 초기 환영 메시지 생성
            welcome_message = await self._create_welcome_message(db, session_id)
            
            # 세션 데이터 초기화
            self.session_data[session_id] = {
                "chat_session": chat_session,
                "user_uuid": user_uuid,
                "last_activity": datetime.now(),
                "message_count": 1,
                "context": {
                    "last_intent": MessageIntent.GREETING,
                    "fortune_requests": 0,
                    "user_preferences": {}
                }
            }
            
            # 연결 목록 초기화
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            
            logger.info(f"Chat session created: {session_id}")
            
            response = self._format_session_response(chat_session)
            response["initial_message"] = welcome_message
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            db.rollback()
            raise
    
    async def connect_websocket(self, session_id: str, websocket: WebSocket, db: Session):
        """WebSocket 연결 처리"""
        try:
            # 서비스 초기화 확인 (지연 초기화)
            if not self._initialized:
                # database_service 설정
                if not self.database_service:
                    self.database_service = db
                
                await self.initialize()
                logger.info("ChatService initialized for WebSocket connection")
            
            await websocket.accept()
            
            # 연결 등록
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            
            self.active_connections[session_id].add(websocket)
            
            # 하트비트 추적 시작
            if session_id not in self.connection_heartbeats:
                self.connection_heartbeats[session_id] = {}
            self.connection_heartbeats[session_id][websocket] = datetime.now()
            
            # 세션 확인/생성
            if session_id not in self.session_data:
                await self.create_chat_session(db, session_id)
            
            # 연결 확인 메시지
            await self._send_to_websocket(websocket, {
                "type": "connection_established",
                "data": {
                    "session_id": session_id,
                    "character_name": "미라",
                    "status": "connected"
                }
            })
            
            logger.info(f"WebSocket connected for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error connecting websocket: {e}")
            raise
    
    async def disconnect_websocket(self, session_id: str, websocket: WebSocket):
        """WebSocket 연결 해제 처리"""
        try:
            # 연결 제거
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(websocket)
                
                # 빈 연결 세트 정리
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
            
            # 하트비트 추적 제거
            if session_id in self.connection_heartbeats:
                self.connection_heartbeats[session_id].pop(websocket, None)
                if not self.connection_heartbeats[session_id]:
                    del self.connection_heartbeats[session_id]
            
            
            logger.info(f"WebSocket disconnected for session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting websocket: {e}")
    
    async def update_heartbeat(self, session_id: str, websocket: WebSocket):
        """Update heartbeat timestamp for connection"""
        if session_id in self.connection_heartbeats and websocket in self.connection_heartbeats[session_id]:
            self.connection_heartbeats[session_id][websocket] = datetime.now()
    
    async def cleanup_stale_connections(self):
        """Cleanup connections that haven't sent heartbeat in timeout period"""
        current_time = datetime.now()
        stale_connections = []
        
        for session_id, connections in self.connection_heartbeats.items():
            for websocket, last_heartbeat in connections.items():
                if (current_time - last_heartbeat).total_seconds() > self.connection_timeout:
                    stale_connections.append((session_id, websocket))
        
        for session_id, websocket in stale_connections:
            logger.info(f"Cleaning up stale connection for session: {session_id}")
            await self.disconnect_websocket(session_id, websocket)
    
    async def handle_message(self, db: Session, session_id: str, 
                           websocket: WebSocket, message_data: Dict[str, Any]):
        """메시지 처리"""
        try:
            # Update heartbeat for any incoming message
            await self.update_heartbeat(session_id, websocket)
            
            message_type = message_data.get("type", "text_input")
            
            if message_type == "text_input":
                await self._handle_text_message(db, session_id, websocket, message_data)
            elif message_type == "chat_message":
                # 프론트엔드에서 보내는 chat_message 타입 처리 (데이터 구조가 다름)
                await self._handle_chat_message(db, session_id, websocket, message_data)
            elif message_type == "fortune_request":
                await self._handle_fortune_request(db, session_id, websocket, message_data)
            elif message_type == "interrupt":
                await self._handle_interrupt(db, session_id, websocket, message_data)
            elif message_type == "ping":
                # Ping 메시지에 대한 Pong 응답
                await self._handle_ping(websocket, message_data)
            else:
                await self._send_error_message(websocket, f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")
    
    async def _handle_text_message(self, db: Session, session_id: str,
                                 websocket: WebSocket, message_data: Dict[str, Any]):
        """텍스트 메시지 처리"""
        try:
            user_message = message_data.get("data", {}).get("message", "")
            
            if not user_message:
                await self._send_error_message(websocket, "메시지가 비어있습니다")
                return
            
            # 콘텐츠 필터링
            filter_result = self.content_filter.check_content(user_message)
            
            if filter_result.is_blocked:
                await self._handle_inappropriate_content(db, session_id, websocket, 
                                                       filter_result)
                return
            
            # 사용자 메시지 저장
            user_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="user",
                content=user_message,
                content_type="text",
                metadata=json.dumps({"filter_passed": True})
            )
            db.add(user_chat_message)
            
            # 의도 분류
            intent = self._classify_message_intent(user_message)
            
            # 세션 데이터 업데이트
            if session_id in self.session_data:
                self.session_data[session_id]["last_activity"] = datetime.now()
                self.session_data[session_id]["message_count"] += 1
                self.session_data[session_id]["context"]["last_intent"] = intent
            
            # 의도별 응답 생성
            if intent in [MessageIntent.DAILY_FORTUNE, MessageIntent.TAROT_FORTUNE, 
                         MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
                await self._handle_specific_fortune_request(db, session_id, websocket, intent, user_message)
            else:
                await self._generate_and_send_response(db, session_id, websocket, intent, user_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            db.rollback()
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")
    
    async def _handle_chat_message(self, db: Session, session_id: str,
                                 websocket: WebSocket, message_data: Dict[str, Any]):
        """채팅 메시지 처리 (프론트엔드 chat_message 타입용)"""
        try:
            # 프론트엔드에서 보내는 구조: {type: 'chat_message', message: '텍스트', timestamp: '...'}
            user_message = message_data.get("message", "")
            
            if not user_message:
                await self._send_error_message(websocket, "메시지가 비어있습니다")
                return
            
            # 콘텐츠 필터링
            filter_result = self.content_filter.check_content(user_message)
            
            if filter_result.is_blocked:
                await self._handle_inappropriate_content(db, session_id, websocket, 
                                                       filter_result)
                return
            
            # 사용자 메시지 저장
            user_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="user",
                content=user_message,
                content_type="text",
                metadata=json.dumps({"filter_passed": True, "message_type": "chat_message"})
            )
            db.add(user_chat_message)
            
            # 의도 분류
            intent = self._classify_message_intent(user_message)
            
            # 세션 데이터 업데이트
            if session_id in self.session_data:
                self.session_data[session_id]["last_activity"] = datetime.now()
                self.session_data[session_id]["message_count"] += 1
                self.session_data[session_id]["context"]["last_intent"] = intent
            
            # 의도별 응답 생성
            if intent in [MessageIntent.DAILY_FORTUNE, MessageIntent.TAROT_FORTUNE, 
                         MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
                await self._handle_specific_fortune_request(db, session_id, websocket, intent, user_message)
            else:
                await self._generate_and_send_response(db, session_id, websocket, intent, user_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            db.rollback()
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")
    
    async def _handle_fortune_request(self, db: Session, session_id: str,
                                    websocket: WebSocket, message_data: Dict[str, Any]):
        """운세 요청 처리"""
        try:
            fortune_data = message_data.get("data", {})
            fortune_type = fortune_data.get("fortune_type", "daily")
            question = fortune_data.get("question", "")
            additional_info = fortune_data.get("additional_info", {})
            
            # 운세 요청 카운트 증가
            if session_id in self.session_data:
                self.session_data[session_id]["context"]["fortune_requests"] += 1
            
            # 운세 생성 알림
            await self._send_to_websocket(websocket, {
                "type": "fortune_processing",
                "data": {
                    "fortune_type": fortune_type,
                    "message": f"{fortune_type} 운세를 준비하고 있어요... 🔮"
                }
            })
            
            
            # 운세 생성
            user_data = self._get_user_data_for_fortune(session_id, additional_info)
            
            if fortune_type == "daily":
                fortune_result = await self.fortune_service.get_daily_fortune(db, user_data)
            elif fortune_type == "tarot":
                from ..models.fortune import QuestionType
                question_type = QuestionType.GENERAL
                if "love" in question.lower() or "연애" in question:
                    question_type = QuestionType.LOVE
                elif "money" in question.lower() or "돈" in question or "재물" in question:
                    question_type = QuestionType.MONEY
                elif "health" in question.lower() or "건강" in question:
                    question_type = QuestionType.HEALTH
                elif "work" in question.lower() or "일" in question or "직장" in question:
                    question_type = QuestionType.WORK
                
                fortune_result = await self.fortune_service.get_tarot_fortune(
                    db, question or "일반적인 운세가 궁금해요", question_type, user_data
                )
            elif fortune_type == "zodiac":
                from ..models.fortune import ZodiacSign
                zodiac = additional_info.get("zodiac", "pisces")
                try:
                    zodiac_sign = ZodiacSign(zodiac)
                except ValueError:
                    zodiac_sign = ZodiacSign.PISCES
                
                fortune_result = await self.fortune_service.get_zodiac_fortune(
                    db, zodiac_sign, "daily", user_data
                )
            elif fortune_type == "oriental":
                birth_data = {
                    "birth_date": additional_info.get("birth_date", "1990-01-01"),
                    "birth_time": additional_info.get("birth_time", "12:00")
                }
                fortune_result = await self.fortune_service.get_oriental_fortune(
                    db, birth_data, user_data
                )
            else:
                fortune_result = await self.fortune_service.get_daily_fortune(db, user_data)
            
            
            # 운세 결과 전송 (디버깅용 로깅 추가)
            logger.info(f"Generated fortune result structure: {type(fortune_result)}")
            logger.info(f"Fortune result keys: {fortune_result.keys() if isinstance(fortune_result, dict) else 'Not a dict'}")
            logger.info(f"Fortune result sample: {str(fortune_result)[:200]}...")
            
            await self._send_to_websocket(websocket, {
                "type": "fortune_result",
                "data": {
                    "fortune_result": fortune_result,
                    "character_message": "운세를 확인해보세요!"
                }
            })
            
            # 결과 메시지 저장
            fortune_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="assistant",
                content=json.dumps(fortune_result, ensure_ascii=False),
                content_type="fortune_result",
                metadata=json.dumps({
                    "fortune_type": fortune_type,
                    "fortune_id": fortune_result.get("fortune_id")
                })
            )
            db.add(fortune_message)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling fortune request: {e}")
            db.rollback()
            await self._send_error_message(websocket, "운세 생성 중 오류가 발생했습니다")
    
    async def _handle_interrupt(self, db: Session, session_id: str,
                              websocket: WebSocket, message_data: Dict[str, Any]):
        """인터럽트 처리"""
        try:
            reason = message_data.get("data", {}).get("reason", "user_stop")
            
            
            # 중단 응답
            await self._send_to_websocket(websocket, {
                "type": "interrupt_acknowledged",
                "data": {
                    "reason": reason,
                    "message": "네, 알겠어요. 다른 질문이 있으시면 언제든 말씀해주세요!"
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling interrupt: {e}")
            await self._send_error_message(websocket, "인터럽트 처리 중 오류가 발생했습니다")
    
    async def _handle_ping(self, websocket: WebSocket, message_data: Dict[str, Any]):
        """Ping 메시지 처리 - Pong 응답 전송"""
        try:
            timestamp = message_data.get("timestamp", datetime.now().isoformat())
            
            # Pong 응답 전송
            await self._send_to_websocket(websocket, {
                "type": "pong",
                "timestamp": timestamp
            })
            
            logger.debug(f"Ping-Pong handled at {timestamp}")
            
        except Exception as e:
            logger.error(f"Error handling ping: {e}")
            # Ping 처리 실패는 에러 메시지를 보내지 않음 (연결 상태 체크용이므로)
    
    async def _handle_inappropriate_content(self, db: Session, session_id: str,
                                          websocket: WebSocket, filter_result: FilterResult):
        """부적절한 콘텐츠 처리"""
        try:
            # 부적절한 메시지 저장  
            inappropriate_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="user",
                content="[부적절한 내용으로 필터링됨]",
                content_type="system",
                metadata=json.dumps({
                    "filter_category": filter_result.category.value if filter_result.category else "unknown",
                    "filter_reason": filter_result.reason,
                    "confidence": filter_result.confidence
                })
            )
            db.add(inappropriate_message)
            
            # 필터링 응답 - 새로운 ContentFilter의 제안 기능 사용
            from ..security.content_filter import get_filter_suggestion
            suggestion_message = get_filter_suggestion(filter_result)
            
            if not suggestion_message:
                # 기본 응답
                response_template = self.response_templates["inappropriate"] 
                import random
                suggestion_message = random.choice(response_template["responses"])
            
            await self._send_to_websocket(websocket, {
                "type": "content_filtered",
                "data": {
                    "message": suggestion_message,
                    "filter_category": filter_result.category.value if filter_result.category else "inappropriate",
                    "suggestion": "운세나 긍정적인 이야기를 해볼까요? 😊"
                }
            })
            
            # 응답 메시지 저장
            response_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="assistant",
                content=suggestion_message,
                content_type="text",
                metadata=json.dumps({"response_type": "content_filter"})
            )
            db.add(response_chat_message)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling inappropriate content: {e}")
            db.rollback()
    
    async def _handle_specific_fortune_request(self, db: Session, session_id: str,
                                             websocket: WebSocket, intent: MessageIntent,
                                             user_message: str):
        """특정 운세 요청 처리"""
        try:
            # 의도별 초기 응답
            response_template = self.response_templates[intent]
            import random
            response_message = random.choice(response_template["responses"])
            
            
            # 초기 응답 전송
            await self._send_to_websocket(websocket, {
                "type": "text_response",
                "data": {
                    "message": response_message,
                    "is_complete": False,
                    "next_action": "waiting_for_details"
                }
            })
            
            # 추가 정보가 필요한 경우
            if intent == MessageIntent.TAROT_FORTUNE:
                detail_message = "어떤 질문이 있으신지 구체적으로 말씀해주세요!"
            elif intent == MessageIntent.ZODIAC_FORTUNE:
                detail_message = "별자리를 알려주시면 더 정확한 운세를 봐드릴 수 있어요!"
            elif intent == MessageIntent.ORIENTAL_FORTUNE:
                detail_message = "생년월일과 태어난 시간을 알려주시면 사주를 봐드릴게요!"
            else:
                # 일일운세는 바로 생성
                await self._auto_generate_fortune(db, session_id, websocket, "daily", user_message)
                return
            
            await self._send_to_websocket(websocket, {
                "type": "text_response",
                "data": {
                    "message": detail_message,
                    "is_complete": True,
                    "requires_input": True
                }
            })
            
            # 응답 메시지 저장
            for message in [response_message, detail_message]:
                response_chat_message = ChatMessage(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    sender_type="assistant",
                    content=message,
                    content_type="text",
                    metadata=json.dumps({"intent": intent.value})
                )
                db.add(response_chat_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling specific fortune request: {e}")
            db.rollback()
    
    async def _auto_generate_fortune(self, db: Session, session_id: str,
                                   websocket: WebSocket, fortune_type: str,
                                   user_message: str):
        """자동 운세 생성"""
        try:
            # 운세 요청으로 처리
            await self._handle_fortune_request(db, session_id, websocket, {
                "type": "fortune_request",
                "data": {
                    "fortune_type": fortune_type,
                    "question": user_message,
                    "additional_info": {}
                }
            })
            
        except Exception as e:
            logger.error(f"Error auto generating fortune: {e}")
            await self._send_error_message(websocket, "운세 생성 중 오류가 발생했습니다")
    
    async def _generate_and_send_response(self, db: Session, session_id: str,
                                        websocket: WebSocket, intent: MessageIntent,
                                        user_message: str):
        """일반 응답 생성 및 전송"""
        try:
            # 응답 템플릿 선택
            if intent in self.response_templates:
                response_template = self.response_templates[intent]
            else:
                response_template = self.response_templates[MessageIntent.CASUAL_CHAT]
            
            # 응답 메시지 선택
            import random
            response_message = random.choice(response_template["responses"])
            
            
            # 응답 전송
            await self._send_to_websocket(websocket, {
                "type": "text_response",
                "data": {
                    "message": response_message,
                    "is_complete": True,
                    "intent": intent.value
                }
            })
            
            # 응답 메시지 저장
            response_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="assistant",
                content=response_message,
                content_type="text",
                metadata=json.dumps({"intent": intent.value})
            )
            db.add(response_chat_message)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self._send_error_message(websocket, "응답 생성 중 오류가 발생했습니다")
    
    async def _create_welcome_message(self, db: Session, session_id: str) -> Dict[str, Any]:
        """환영 메시지 생성"""
        welcome_text = "안녕하세요! 저는 미라예요. 오늘 운세가 궁금하신가요? ✨"
        
        welcome_message = ChatMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            sender_type="assistant",
            content=welcome_text,
            content_type="text",
            metadata=json.dumps({"message_type": "welcome"})
        )
        
        db.add(welcome_message)
        
        return {
            "message": welcome_text,
            "type": "welcome",
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_user_data_for_fortune(self, session_id: str, additional_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """운세 생성용 사용자 데이터 구성"""
        user_data = {}
        
        # 세션 데이터에서 사용자 정보 가져오기
        if session_id in self.session_data:
            session_info = self.session_data[session_id]
            if session_info.get("user_uuid"):
                user_data["user_uuid"] = session_info["user_uuid"]
            
            # 사용자 선호도 정보
            preferences = session_info.get("context", {}).get("user_preferences", {})
            user_data.update(preferences)
        
        # 추가 정보 병합
        user_data.update(additional_info)
        
        return user_data if user_data else None
    
    def _format_session_response(self, chat_session: ChatSession) -> Dict[str, Any]:
        """세션 응답 포맷"""
        return {
            "session_id": chat_session.session_id,
            "character_name": chat_session.character_name,
            "is_active": chat_session.is_active,
            "created_at": chat_session.created_at.isoformat(),
            "expires_at": (chat_session.created_at + timedelta(hours=24)).isoformat()
        }
    
    def _classify_message_intent(self, message: str) -> MessageIntent:
        """메시지 의도 분류"""
        message_lower = message.lower()
        
        # 인사 키워드
        greeting_keywords = [
            "안녕", "안녕하세요", "안녕하십니까", "반가워", "반갑습니다",
            "하이", "헬로", "처음", "만나서", "반가워요", "좋은아침",
            "좋은하루", "고마워", "감사", "고마워요", "감사해요", "감사합니다"
        ]
        
        # 운세 관련 키워드
        fortune_keywords = {
            "daily": ["오늘", "오늘운세", "일일운세", "하루", "오늘의운세"],
            "tarot": ["타로", "카드", "타로카드", "점", "점봐", "카드점", "타로점"],
            "zodiac": ["별자리", "별자리운세", "천체", "황도", "점성술", "별", "자리"],
            "oriental": ["사주", "사주팔자", "운명", "팔자", "사주봐", "명리학", "동양점성술"]
        }
        
        # 인사 체크
        if any(keyword in message_lower for keyword in greeting_keywords):
            return MessageIntent.GREETING
        
        # 운세 요청 체크
        for fortune_type, keywords in fortune_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if fortune_type == "daily":
                    return MessageIntent.DAILY_FORTUNE
                elif fortune_type == "tarot":
                    return MessageIntent.TAROT_FORTUNE
                elif fortune_type == "zodiac":
                    return MessageIntent.ZODIAC_FORTUNE
                elif fortune_type == "oriental":
                    return MessageIntent.ORIENTAL_FORTUNE
        
        # 일반적인 운세 요청
        fortune_general = ["운세", "점", "점봐", "운", "운명", "미래", "앞일"]
        if any(keyword in message_lower for keyword in fortune_general):
            return MessageIntent.FORTUNE_REQUEST
        
        # 질문
        question_markers = ["?", "？", "뭐", "무엇", "어떻", "왜", "언제", "어디"]
        if any(marker in message for marker in question_markers):
            return MessageIntent.QUESTION
        
        # 칭찬/감탄
        compliment_markers = ["예쁘", "귀여", "멋지", "좋", "최고", "짱", "대박"]
        if any(marker in message_lower for marker in compliment_markers):
            return MessageIntent.COMPLIMENT
        
        return MessageIntent.CASUAL_CHAT
    
    async def _send_to_websocket(self, websocket: WebSocket, message: Dict[str, Any]):
        """WebSocket으로 메시지 전송"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"Failed to send websocket message: {e}")
    
    async def _send_error_message(self, websocket: WebSocket, error_message: str):
        """에러 메시지 전송"""
        await self._send_to_websocket(websocket, {
            "type": "error",
            "data": {
                "error_code": "PROCESSING_ERROR",
                "message": error_message,
                "timestamp": datetime.now().isoformat()
            }
        })
    
    async def get_chat_history(self, db: Session, session_id: str,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """채팅 히스토리 조회"""
        try:
            messages = ChatMessage.find_session_messages(db, session_id, limit)
            
            return [
                {
                    "id": msg.id,
                    "message_id": msg.message_id,
                    "sender_type": msg.sender_type,
                    "content": msg.content,
                    "content_type": msg.content_type,
                    "metadata": msg.metadata_dict,
                    "created_at": msg.created_at.isoformat()
                }
                for msg in messages
            ]
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise
    
    async def cleanup_inactive_sessions(self, db: Session, hours: int = 24) -> int:
        """비활성 세션 정리"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cleaned_count = 0
            
            # 메모리에서 오래된 세션 제거
            expired_sessions = []
            for session_id, session_data in self.session_data.items():
                if session_data["last_activity"] < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                # WebSocket 연결 정리
                if session_id in self.active_connections:
                    del self.active_connections[session_id]
                
                del self.session_data[session_id]
                cleaned_count += 1
                logger.info(f"Cleaned up expired chat session: {session_id}")
            
            # 데이터베이스에서 비활성화
            inactive_sessions = db.query(ChatSession).filter(
                ChatSession.status == 'active',
                ChatSession.started_at < cutoff_time
            ).all()
            for session in inactive_sessions:
                session.status = 'expired'
                session.ended_at = datetime.now()
                cleaned_count += 1
            
            if inactive_sessions:
                db.commit()
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up chat sessions: {e}")
            db.rollback()
            raise
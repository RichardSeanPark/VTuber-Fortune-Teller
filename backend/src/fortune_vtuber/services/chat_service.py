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
from ..services.fortune_service import FortuneService, clean_text_for_tts
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
        
        # LLM 초기화 상태
        self._initialized = False
        
        # Cerebras client 초기화
        self.cerebras_client = None
        self._init_cerebras_client()
    
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
    
    def _init_cerebras_client(self):
        """Cerebras client 초기화"""
        try:
            import os
            from cerebras.cloud.sdk import Cerebras
            
            api_key = os.getenv("CEREBRAS_API_KEY")
            if api_key:
                self.cerebras_client = Cerebras(api_key=api_key)
                logger.info("Cerebras client initialized successfully for chat service")
            else:
                logger.warning("CEREBRAS_API_KEY not found, LLM features will be limited")
                
        except Exception as e:
            logger.error(f"Failed to initialize Cerebras client: {e}")
            self.cerebras_client = None
    
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
    
    async def _generate_inappropriate_response(self, websocket: WebSocket = None) -> str:
        """부적절한 콘텐츠에 대한 LLM 응답 생성"""
        try:
            if self.cerebras_client:
                system_prompt = """당신은 '미라'라는 친근한 점술사 캐릭터입니다.
부적절한 내용이 감지되었을 때, 자연스럽게 대화를 긍정적으로 전환해주세요.
- 공격적이지 않고 친근하게 대응
- 운세나 긍정적인 주제로 자연스럽게 전환
- 30자 이내로 간결하게"""
                
                response = self.cerebras_client.chat.completions.create(
                    model="llama3.1-8b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": "부적절한 메시지"}
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                
                return response.choices[0].message.content
            else:
                # 폴백 응답
                return "앗, 다른 이야기를 해볼까요? 오늘 운세가 궁금하신가요? 😊"
                
        except Exception as e:
            logger.error(f"Failed to generate inappropriate response: {e}")
            return "다른 주제로 이야기해보는 게 어떨까요? 운세를 봐드릴게요! ✨"
    
    # MessageIntent.FORTUNE_REQUEST 처리를 위한 함수 추가
    async def _handle_fortune_request_general(self, db: Session, session_id: str,
                                             websocket: WebSocket, user_message: str):
        """일반 운세 요청 처리 (구체적인 타입이 없는 경우)"""
        try:
            # 기본적으로 일일 운세로 처리
            await self._handle_fortune_request(db, session_id, websocket, {
                "type": "fortune_request",
                "data": {
                    "fortune_type": "daily",
                    "question": user_message,
                    "additional_info": {}
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling general fortune request: {e}")
            await self._send_error_message(websocket, "운세 처리 중 오류가 발생했습니다")
    
    async def _generate_llm_response(self, user_message: str, intent: MessageIntent, 
                                     websocket: WebSocket = None) -> str:
        """Cerebras LLM을 사용한 일반 응답 생성"""
        try:
            # LLM 호출 상세 정보 전송
            if websocket:
                await self._send_to_websocket(websocket, {
                    "type": "llm_details",
                    "data": {
                        "message": f"Cerebras AI에 일반 대화 요청 중...",
                        "model": "llama3.1-8b",
                        "status": "requesting"
                    }
                })
            
            # 시스템 프롬프트 구성
            system_prompt = """당신은 '미라'라는 이름의 친근하고 귀여운 점술사 캐릭터입니다.
다음 특징을 가지고 대화해주세요:
- 친근하고 활발한 성격
- 약간 신비로운 분위기
- 특수기호나 이모지 사용하지 말고 순수한 한글로만 대화
- 한국어로 자연스럽게 대화
- 50자 이내로 간결하게 응답"""
            
            # 의도별 프롬프트 조정
            if intent == MessageIntent.GREETING:
                system_prompt += "\n- 친근한 인사와 함께 간단한 안부를 물어보세요"
            elif intent == MessageIntent.QUESTION:
                system_prompt += "\n- 질문에 대해 도움이 되는 답변을 해주세요"
            elif intent == MessageIntent.CASUAL_CHAT:
                system_prompt += "\n- 일상적이고 재미있는 대화를 이어가세요"
            
            # Cerebras API 호출
            if hasattr(self, 'cerebras_client') and self.cerebras_client:
                response = self.cerebras_client.chat.completions.create(
                    model="llama3.1-8b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.8,
                    max_tokens=200
                )
                
                llm_response = response.choices[0].message.content
                logger.info(f"[LLM 응답] 일반 대화: {llm_response[:100]}...")
                
                # TTS 호환성을 위한 텍스트 정제
                cleaned_response = clean_text_for_tts(llm_response)
                
                # TTS 음성 생성 (직접 EdgeTTS 사용)
                logger.info(f"🔍 TTS 음성 생성 시작: '{cleaned_response}'")
                tts_audio_data = None
                try:
                    logger.info("🔍 EdgeTTS Provider 직접 사용...")
                    from ..tts.providers.edge_tts import EdgeTTSProvider
                    from ..tts.tts_interface import TTSProviderConfig, TTSRequest, TTSCostType, TTSQuality
                    import base64
                    
                    # EdgeTTS 설정
                    config = TTSProviderConfig(
                        provider_id="edge_tts",
                        name="EdgeTTS",
                        cost_type=TTSCostType.FREE,
                        quality=TTSQuality.HIGH,
                        supported_languages=["ko-KR"],
                        supported_voices={"ko-KR": ["ko-KR-SunHiNeural"]},
                        default_voice="ko-KR-SunHiNeural",
                        api_required=False
                    )
                    logger.info("✅ EdgeTTS 설정 완료")
                    
                    # EdgeTTS Provider 초기화
                    edge_provider = EdgeTTSProvider(config)
                    logger.info("✅ EdgeTTS Provider 초기화 완료")
                    
                    # TTS 요청 생성
                    tts_request = TTSRequest(
                        text=cleaned_response,
                        language="ko-KR",
                        voice="ko-KR-SunHiNeural",
                        speed=1.0,
                        pitch=1.0,
                        volume=1.0,
                        enable_lipsync=True
                    )
                    logger.info(f"✅ EdgeTTS 요청 생성 완료: {cleaned_response[:30]}...")
                    
                    # TTS 생성
                    logger.info("🔍 EdgeTTS async_generate_audio 호출 중...")
                    tts_result = await edge_provider.async_generate_audio(tts_request)
                    logger.info(f"🔍 EdgeTTS 결과 받음: 타입={type(tts_result)}")
                    
                    if tts_result and tts_result.audio_data:
                        tts_audio_data = base64.b64encode(tts_result.audio_data).decode('utf-8')
                        logger.info(f"✅ TTS 음성 생성 성공: {len(tts_result.audio_data)} bytes")
                        logger.info(f"✅ Base64 인코딩 완료: {len(tts_audio_data)} characters")
                    else:
                        logger.warning("⚠️ EdgeTTS 결과가 없거나 audio_data가 비어있음")
                        logger.warning(f"⚠️ tts_result: {tts_result}")
                        
                except Exception as tts_error:
                    logger.error(f"❌ EdgeTTS 생성 실패: {tts_error}")
                    import traceback
                    logger.error(f"❌ EdgeTTS 오류 상세: {traceback.format_exc()}")
                    # TTS 실패해도 텍스트는 전송
                
                # LLM 응답 성공 알림
                if websocket:
                    await self._send_to_websocket(websocket, {
                        "type": "llm_response", 
                        "data": {
                            "message": "Cerebras AI 응답 받음!",
                            "response_length": len(cleaned_response),
                            "chat_content": cleaned_response,
                            "status": "received"
                        }
                    })
                
                return cleaned_response, tts_audio_data
                
            else:
                # Cerebras 사용 불가시 기본 응답
                logger.warning("Cerebras client not available, using template response")
                template_response = await self._get_template_response(intent)
                return template_response, None
                
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            # 오류 시 템플릿 응답 반환
            template_response = await self._get_template_response(intent)
            return template_response, None
    
    async def _get_template_response(self, intent: MessageIntent) -> str:
        """LLM 폴백용 간단한 응답 생성"""
        # LLM이 실패했을 때 사용할 기본 응답
        fallback_responses = {
            MessageIntent.GREETING: "안녕하세요! 반가워요~ 오늘 하루는 어떠셨나요? ✨",
            MessageIntent.QUESTION: "흥미로운 질문이네요! 제가 도와드릴 수 있는 게 있을까요?",
            MessageIntent.CASUAL_CHAT: "재미있는 이야기네요! 더 들려주세요~ 😊",
            MessageIntent.FORTUNE_REQUEST: "운세가 궁금하신가요? 오늘의 운세를 알려드릴게요!",
            MessageIntent.DAILY_FORTUNE: "오늘의 운세를 확인해드릴게요!",
            MessageIntent.TAROT_FORTUNE: "타로 카드를 뽑아드릴게요!",
            MessageIntent.ZODIAC_FORTUNE: "별자리 운세를 확인해드릴게요!",
            MessageIntent.ORIENTAL_FORTUNE: "사주를 봐드릴게요!"
        }
        
        return fallback_responses.get(intent, "무엇을 도와드릴까요? 😊")
    
    async def _generate_and_send_response(self, db: Session, session_id: str, 
                                          websocket: WebSocket, intent: MessageIntent, 
                                          user_message: str):
        """LLM을 사용한 응답 생성 및 전송"""
        try:
            # LLM으로 응답 생성 (TTS 오디오 포함)
            llm_response, tts_audio_data = await self._generate_llm_response(user_message, intent, websocket)
            
            # 데이터베이스에 봇 메시지 저장
            bot_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="assistant",  # 모델에서는 "assistant" 사용
                content=llm_response,
                live2d_emotion="friendly",
                live2d_motion="idle"
            )
            db.add(bot_chat_message)
            
            # 응답 전송 (TTS 오디오 포함)
            message_data = {
                "type": "chat_message",
                "data": {
                    "message": llm_response,
                    "sender": "bot",
                    "emotion": "friendly",
                    "motion": "idle", 
                    "timestamp": datetime.utcnow().isoformat(),
                    "intent": intent.value,
                    "tts_text": llm_response  # TTS용 텍스트
                }
            }
            
            # TTS 오디오가 있으면 추가
            if tts_audio_data:
                message_data["data"]["audio_data"] = tts_audio_data
                logger.info("🔊 WebSocket 메시지에 TTS 오디오 추가됨")
            
            await self._send_to_websocket(websocket, message_data)
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            # 폴백: 간단한 응답 사용
            fallback_response = await self._get_template_response(intent)
            
            bot_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="assistant",
                content=fallback_response,
                live2d_emotion="neutral",
                live2d_motion="idle"
            )
            db.add(bot_chat_message)
            
            await self._send_to_websocket(websocket, {
                "type": "chat_message",
                "data": {
                    "message": fallback_response,
                    "sender": "bot", 
                    "emotion": "neutral",
                    "motion": "idle",
                    "timestamp": datetime.utcnow().isoformat(),
                    "intent": intent.value,
                    "tts_text": fallback_response
                }
            })

    async def connect(self, websocket: WebSocket, session_id: str):
        """WebSocket 연결 처리"""
        await websocket.accept()
        
        # 연결 추가
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
        
        # 하트비트 추가
        if session_id not in self.connection_heartbeats:
            self.connection_heartbeats[session_id] = {}
        self.connection_heartbeats[session_id][websocket] = datetime.now()
        
        logger.info(f"WebSocket connected: {session_id}")
        
        # 환영 메시지 전송
        await self._send_to_websocket(websocket, {
            "type": "connection_established",
            "data": {
                "session_id": session_id,
                "message": "연결이 성공적으로 설정되었습니다.",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # 세션 초기화
        await self._initialize_session(session_id)
    
    async def disconnect(self, websocket: WebSocket, session_id: str):
        """WebSocket 연결 해제 처리"""
        # 연결 제거
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
        
        # 하트비트 제거
        if session_id in self.connection_heartbeats:
            self.connection_heartbeats[session_id].pop(websocket, None)
            if not self.connection_heartbeats[session_id]:
                del self.connection_heartbeats[session_id]
        
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def _initialize_session(self, session_id: str):
        """세션 데이터 초기화"""
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 0,
                "context": {
                    "last_intent": None,
                    "conversation_history": [],
                    "user_preferences": {}
                }
            }

    async def handle_text_message(self, db: Session, session_id: str, websocket: WebSocket, message_data: dict):
        """텍스트 메시지 처리"""
        try:
            user_message = message_data.get("message", "").strip()
            if not user_message:
                return
            
            # 콘텐츠 필터링
            filter_result = self.content_filter.check_content(user_message)
            
            if filter_result.is_blocked:
                # 부적절한 내용에 대한 LLM 응답 생성
                inappropriate_response = await self._generate_inappropriate_response(websocket)
                
                await self._send_to_websocket(websocket, {
                    "type": "chat_message",
                    "data": {
                        "message": inappropriate_response,
                        "sender": "bot",
                        "emotion": "gentle",
                        "motion": "idle",
                        "timestamp": datetime.utcnow().isoformat(),
                        "intent": MessageIntent.INAPPROPRIATE.value,
                        "tts_text": inappropriate_response
                    }
                })
                return
            
            # 사용자 메시지 저장
            user_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="user",
                content=user_message
            )
            db.add(user_chat_message)
            
            # 의도 분석
            intent = await self._analyze_intent(user_message)
            
            # 세션 데이터 업데이트
            if session_id in self.session_data:
                self.session_data[session_id]["last_activity"] = datetime.now()
                self.session_data[session_id]["message_count"] += 1
                self.session_data[session_id]["context"]["last_intent"] = intent
            
            # 의도별 응답 생성
            if intent in [MessageIntent.DAILY_FORTUNE, MessageIntent.TAROT_FORTUNE, 
                         MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
                await self._handle_specific_fortune_request(db, session_id, websocket, intent, user_message)
            elif intent == MessageIntent.FORTUNE_REQUEST:
                # 일반 운세 요청은 일일 운세로 처리
                await self._handle_fortune_request_general(db, session_id, websocket, user_message)
            else:
                await self._generate_and_send_response(db, session_id, websocket, intent, user_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            db.rollback()
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")

    async def handle_chat_message(self, db: Session, session_id: str, websocket: WebSocket, message_data: dict):
        """채팅 메시지 처리 (일반 대화)"""
        try:
            user_message = message_data.get("message", "").strip()
            if not user_message:
                return
            
            # 콘텐츠 필터링
            filter_result = self.content_filter.check_content(user_message)
            
            if filter_result.is_blocked:
                # 부적절한 내용에 대한 LLM 응답 생성
                inappropriate_response = await self._generate_inappropriate_response(websocket)
                
                await self._send_to_websocket(websocket, {
                    "type": "chat_message",
                    "data": {
                        "message": inappropriate_response,
                        "sender": "bot",
                        "emotion": "gentle",
                        "motion": "idle",
                        "timestamp": datetime.utcnow().isoformat(),
                        "intent": MessageIntent.INAPPROPRIATE.value,
                        "tts_text": inappropriate_response
                    }
                })
                return
            
            # 사용자 메시지 저장
            user_chat_message = ChatMessage(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                sender_type="user",
                content=user_message
            )
            db.add(user_chat_message)
            
            # 의도 분석
            intent = await self._analyze_intent(user_message)
            
            # 세션 데이터 업데이트
            if session_id in self.session_data:
                self.session_data[session_id]["last_activity"] = datetime.now()
                self.session_data[session_id]["message_count"] += 1
                self.session_data[session_id]["context"]["last_intent"] = intent
            
            # 의도별 응답 생성
            if intent in [MessageIntent.DAILY_FORTUNE, MessageIntent.TAROT_FORTUNE, 
                         MessageIntent.ZODIAC_FORTUNE, MessageIntent.ORIENTAL_FORTUNE]:
                await self._handle_specific_fortune_request(db, session_id, websocket, intent, user_message)
            elif intent == MessageIntent.FORTUNE_REQUEST:
                # 일반 운세 요청은 일반 운세 핸들러로 처리
                await self._handle_fortune_request_general(db, session_id, websocket, user_message)
            else:
                await self._generate_and_send_response(db, session_id, websocket, intent, user_message)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            db.rollback()
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")

    async def _handle_specific_fortune_request(self, db: Session, session_id: str, 
                                             websocket: WebSocket, intent: MessageIntent, 
                                             user_message: str):
        """구체적인 운세 요청 처리"""
        try:
            # 운세 타입 매핑
            fortune_type_map = {
                MessageIntent.DAILY_FORTUNE: "daily",
                MessageIntent.TAROT_FORTUNE: "tarot", 
                MessageIntent.ZODIAC_FORTUNE: "zodiac",
                MessageIntent.ORIENTAL_FORTUNE: "oriental"
            }
            
            fortune_type = fortune_type_map.get(intent, "daily")
            
            # 운세 요청 구성
            fortune_request = {
                "type": "fortune_request",
                "data": {
                    "fortune_type": fortune_type,
                    "question": user_message,
                    "additional_info": {}
                }
            }
            
            await self._handle_fortune_request(db, session_id, websocket, fortune_request)
            
        except Exception as e:
            logger.error(f"Error handling specific fortune request: {e}")
            await self._send_error_message(websocket, "운세 처리 중 오류가 발생했습니다")

    async def handle_fortune_request(self, db: Session, session_id: str, websocket: WebSocket, message_data: dict):
        """운세 요청 처리"""
        await self._handle_fortune_request(db, session_id, websocket, message_data)

    async def _handle_fortune_request(self, db: Session, session_id: str, websocket: WebSocket, message_data: dict):
        """내부 운세 요청 처리"""
        try:
            logger.info(f"🔍 ChatService._handle_fortune_request 시작: message_data={message_data}")
            
            if not self.fortune_service:
                logger.error("❌ Fortune service가 없음!")
                await self._send_error_message(websocket, "운세 서비스를 사용할 수 없습니다")
                return
            
            logger.info(f"🔍 Fortune service 존재 확인됨: {type(self.fortune_service)}")
            
            fortune_type = message_data.get("data", {}).get("fortune_type", "daily")
            question = message_data.get("data", {}).get("question", "")
            additional_info = message_data.get("data", {}).get("additional_info", {})
            
            logger.info(f"🔍 운세 파라미터: type={fortune_type}, question='{question}', info={additional_info}")
            
            # 운세 생성 요청
            logger.info(f"🔍 FortuneService.generate_fortune 호출 시작...")
            await self.fortune_service.generate_fortune(
                db=db,
                session_id=session_id,
                websocket=websocket,
                fortune_type=fortune_type,
                question=question,
                additional_info=additional_info
            )
            logger.info(f"🔍 FortuneService.generate_fortune 호출 완료")
            
        except Exception as e:
            logger.error(f"Error handling fortune request: {e}")
            await self._send_error_message(websocket, "운세 생성 중 오류가 발생했습니다")

    async def handle_message(self, db: Session, session_id: str, websocket: WebSocket, message: dict):
        """메시지 라우팅"""
        try:
            message_type = message.get("type")
            message_data = message.get("data", {})
            
            logger.info(f"[ChatService] Handling message - Type: {message_type}, Session: {session_id}")
            logger.info(f"[ChatService] Message data: {message_data}")
            
            if message_type == "text_message":
                logger.info(f"[ChatService] Routing to handle_text_message")
                await self.handle_text_message(db, session_id, websocket, message_data)
            elif message_type == "chat_message":
                logger.info(f"[ChatService] Routing to handle_chat_message")
                await self.handle_chat_message(db, session_id, websocket, message_data)
            elif message_type == "fortune_request":
                logger.info(f"[ChatService] Routing to handle_fortune_request")
                await self.handle_fortune_request(db, session_id, websocket, message_data)
            elif message_type == "heartbeat":
                logger.info(f"[ChatService] Routing to _handle_heartbeat")
                await self._handle_heartbeat(session_id, websocket)
            else:
                logger.warning(f"[ChatService] Unknown message type: {message_type}")
                await self._send_error_message(websocket, f"알 수 없는 메시지 타입: {message_type}")
                
        except Exception as e:
            logger.error(f"[ChatService] Error handling message: {e}")
            await self._send_error_message(websocket, "메시지 처리 중 오류가 발생했습니다")

    async def _handle_heartbeat(self, session_id: str, websocket: WebSocket):
        """하트비트 처리"""
        if session_id in self.connection_heartbeats:
            if websocket in self.connection_heartbeats[session_id]:
                self.connection_heartbeats[session_id][websocket] = datetime.now()
                
                # 하트비트 응답
                await self._send_to_websocket(websocket, {
                    "type": "heartbeat_response",
                    "data": {
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "alive"
                    }
                })

    async def _analyze_intent(self, message: str) -> MessageIntent:
        """메시지 의도 분석"""
        message_lower = message.lower().strip()
        
        # 인사말 패턴
        greetings = ["안녕", "안녕하세요", "반갑", "처음", "hello", "hi"]
        if any(greeting in message_lower for greeting in greetings):
            return MessageIntent.GREETING
        
        # 운세 관련 패턴
        fortune_keywords = ["운세", "점", "운", "미래", "오늘운세", "내운세"]
        tarot_keywords = ["타로", "카드", "타로카드"]
        zodiac_keywords = ["별자리", "별운세", "조디악", "서양"]
        oriental_keywords = ["사주", "팔자", "오행", "음양", "동양"]
        
        if any(keyword in message_lower for keyword in tarot_keywords):
            return MessageIntent.TAROT_FORTUNE
        elif any(keyword in message_lower for keyword in zodiac_keywords):
            return MessageIntent.ZODIAC_FORTUNE
        elif any(keyword in message_lower for keyword in oriental_keywords):
            return MessageIntent.ORIENTAL_FORTUNE
        elif any(keyword in message_lower for keyword in fortune_keywords):
            return MessageIntent.FORTUNE_REQUEST
        
        # 질문 패턴
        question_markers = ["?", "？", "어떻게", "왜", "언제", "어디서", "뭐", "무엇", "어떤"]
        if any(marker in message_lower for marker in question_markers):
            return MessageIntent.QUESTION
        
        # 칭찬 패턴
        compliment_keywords = ["예쁘", "귀여", "좋아", "멋지", "훌륭", "대단", "감사"]
        if any(keyword in message_lower for keyword in compliment_keywords):
            return MessageIntent.COMPLIMENT
        
        # 기본값은 일상 대화
        return MessageIntent.CASUAL_CHAT

    async def _send_to_websocket(self, websocket: WebSocket, data: dict):
        """WebSocket으로 데이터 전송"""
        try:
            await websocket.send_text(json.dumps(data, ensure_ascii=False, default=str))
        except Exception as e:
            logger.error(f"Error sending to websocket: {e}")

    async def _send_error_message(self, websocket: WebSocket, error_message: str):
        """오류 메시지 전송"""
        await self._send_to_websocket(websocket, {
            "type": "error",
            "data": {
                "message": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    def get_active_sessions_count(self) -> int:
        """활성 세션 수 반환"""
        return len(self.active_connections)

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 반환"""
        return self.session_data.get(session_id)

    async def cleanup_inactive_connections(self):
        """비활성 연결 정리"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, heartbeats in self.connection_heartbeats.items():
            websockets_to_remove = []
            
            for websocket, last_heartbeat in heartbeats.items():
                if (current_time - last_heartbeat).total_seconds() > self.connection_timeout:
                    websockets_to_remove.append(websocket)
            
            # 타임아웃된 WebSocket 정리
            for websocket in websockets_to_remove:
                await self.disconnect(websocket, session_id)
                try:
                    await websocket.close()
                except Exception:
                    pass
            
            # 세션에 연결이 없으면 세션 정리
            if not heartbeats:
                sessions_to_remove.append(session_id)
        
        # 빈 세션 데이터 정리
        for session_id in sessions_to_remove:
            self.session_data.pop(session_id, None)
            self.connection_heartbeats.pop(session_id, None)


# 필요한 추가 import
try:
    from ..models.chat import SenderType
except ImportError:
    # SenderType이 정의되어 있지 않은 경우 기본 정의
    class SenderType(str, Enum):
        USER = "user"
        BOT = "bot"
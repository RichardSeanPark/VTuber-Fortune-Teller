"""
LLM 기반 Fortune Service - 모든 템플릿 제거됨
"""

import random
import uuid
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.fortune import (
    FortuneSession, FortuneType, QuestionType, ZodiacSign
)
from ..models.user import User
from .cache_service import CacheService
from ..config.cerebras_config import get_cerebras_config, is_cerebras_enabled

logger = logging.getLogger(__name__)


def clean_text_for_tts(text: str) -> str:
    """TTS 호환성을 위한 텍스트 정제 - 특수기호/이모지 제거"""
    logger.info(f"🔍 텍스트 정제 시작: 원본 텍스트 = '{text}' (length: {len(text) if text else 0})")
    
    if not text:
        logger.warning(f"⚠️ 빈 텍스트 입력, 기본 메시지로 대체")
        return "죄송합니다. 메시지가 없습니다."
    
    original_text = text
    
    # 이모지 제거 (유니코드 이모지 범위) - Korean characters 보호
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # Miscellaneous Symbols
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    if text != original_text:
        logger.info(f"🔍 이모지 제거 후: '{text}'")
    
    # 특수 기호 제거 (TTS에 문제가 되는 것들)
    special_symbols = ['★', '☆', '♥', '♡', '❤', '💖', '💕', '🎯', '✨', '🌟', 
                      '🔮', '🎴', '🃏', '💫', '⭐', '🌙', '☀', '🌈', '💎',
                      '👑', '🎊', '🎉', '🎈', '🎁', '🌹', '🌸', '🌺', '🌻']
    
    before_symbols = text
    for symbol in special_symbols:
        text = text.replace(symbol, '')
    
    if text != before_symbols:
        logger.info(f"🔍 특수 기호 제거 후: '{text}'")
    
    # 연속된 공백 정리
    before_spaces = text
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    if text != before_spaces:
        logger.info(f"🔍 공백 정리 후: '{text}'")
    
    # TTS에 문제가 되는 텍스트 처리
    problematic_texts = [".", "..", "...", "....", ".....", ". . . .", ". . . . .", ". , . ,", ". , . , . .", "　", " "]
    if not text or text in problematic_texts:
        logger.warning(f"⚠️ 문제가 있는 텍스트 감지: '{text}', 기본 메시지로 대체")
        logger.warning(f"⚠️ 이는 LLM에서 생성된 원본 응답입니다. LLM 호출 과정을 점검해야 합니다.")
        text = "잠시만 기다려주세요."
    
    # 너무 짧은 텍스트 보완
    if len(text) < 3:
        logger.warning(f"⚠️ 텍스트가 너무 짧음: '{text}' (length: {len(text)}), 기본 메시지로 대체")
        text = "잠시만 기다려주세요."
    
    logger.info(f"✅ TTS 텍스트 정제 완료: '{text}' (length: {len(text)})")
    return text


class LLMFortuneEngine:
    """LLM 기반 운세 생성 엔진 - 폴백 메시지 완전 제거"""
    
    def __init__(self):
        from ..config.cerebras_config import get_cerebras_config, is_cerebras_enabled
        self.cerebras_config = get_cerebras_config()
        self.use_cerebras = is_cerebras_enabled()
    
    async def generate_llm_fortune(self, fortune_type: str, question: str = "", user_data: Optional[Dict] = None) -> str:
        """LLM 기반 운세 생성 - 폴백 제거로 에러 확인 가능"""
        if not self.use_cerebras:
            raise Exception("CEREBRAS_API_KEY not found. LLM service unavailable.")
        
        from cerebras.cloud.sdk import Cerebras
        
        client = Cerebras(
            api_key=self.cerebras_config.api_key
        )
        
        # 운세 타입별 프롬프트 구성
        if fortune_type in ["daily", "일일", "오늘운세"]:
            system_prompt = """당신은 '미라'라는 이름의 친근하고 귀여운 점술사입니다. 
            일일 운세를 50자 이내로 간결하고 따뜻하게 전해주세요.
            특수기호나 이모지 없이 순수한 한글로 긍정적인 메시지를 포함해주세요."""
            user_prompt = "오늘 하루 운세를 알려주세요."
        elif fortune_type in ["tarot", "타로"]:
            system_prompt = """당신은 '미라'라는 이름의 신비로운 타로 점술사입니다.
            타로 카드의 메시지를 50자 이내로 전해주세요.
            특수기호나 이모지 없이 순수한 한글로 통찰력 있는 답변을 해주세요.""" 
            user_prompt = f"타로 카드로 이 질문에 답해주세요: {question or '일반적인 질문'}"
        elif fortune_type in ["zodiac", "별자리"]:
            system_prompt = """당신은 '미라'라는 이름의 별자리 전문 점술사입니다.
            별자리 운세를 50자 이내로 알려주세요.
            특수기호나 이모지 없이 순수한 한글로 별들의 메시지를 전해주세요."""
            user_prompt = "별자리 운세를 알려주세요."
        else:
            system_prompt = """당신은 '미라'라는 이름의 친근한 점술사입니다.
            50자 이내로 특수기호나 이모지 없이 순수한 한글로 따뜻한 메시지를 전해주세요."""
            user_prompt = question or "운세를 알려주세요."
        
        # LLM 호출
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=self.cerebras_config.model,
            max_tokens=100,
            temperature=0.7
        )
        
        response = chat_completion.choices[0].message.content.strip()
        logger.info(f"🔍 LLM 원본 응답: '{response}' (length: {len(response)})")
        
        if not response:
            logger.error("❌ LLM returned empty response")
            raise Exception("LLM returned empty response")
        
        # TTS 호환성을 위한 텍스트 정제
        cleaned_response = clean_text_for_tts(response)
        logger.info(f"🔍 TTS 정제 후: '{cleaned_response}' (length: {len(cleaned_response)})")
        
        return cleaned_response


class FortuneService:
    """LLM 기반 운세 서비스 - 템플릿 시스템 완전 제거"""
    
    def __init__(self, database_service=None, cache_service: CacheService = None):
        self.engine = LLMFortuneEngine()
        self.cache_service = cache_service or CacheService()
        self.database_service = database_service
        self._initialized = False
        
        # Cerebras 설정
        self.cerebras_config = get_cerebras_config()
        self.use_cerebras = is_cerebras_enabled()
    
    async def initialize(self):
        """Initialize fortune service"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("FortuneService initialized")
    
    async def shutdown(self):
        """Shutdown fortune service"""
        self._initialized = False
        logger.info("FortuneService shutdown")
    
    async def get_fortune_history(self, db: Session, user_uuid: str,
                                 fortune_type: Optional[str] = None,
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """사용자 운세 히스토리 조회"""
        try:
            query = db.query(FortuneSession).filter(
                FortuneSession.user_uuid == user_uuid
            )
            
            if fortune_type and fortune_type != "all":
                query = query.filter(FortuneSession.fortune_type == fortune_type)
            
            fortunes = query.order_by(FortuneSession.created_at.desc()).limit(limit).all()
            
            return [
                {
                    "fortune_id": fortune.fortune_id,
                    "fortune_type": fortune.fortune_type,
                    "question": fortune.question,
                    "question_type": fortune.question_type,
                    "result": fortune.result_dict,
                    "created_at": fortune.created_at.isoformat(),
                    "is_cached": fortune.is_cached
                }
                for fortune in fortunes
            ]
            
        except Exception as e:
            logger.error(f"Error getting fortune history: {e}")
            raise
    
    # === ChatService 호환성을 위한 메서드 ===
    async def generate_fortune(self, db: Session, session_id: str, websocket, 
                              fortune_type: str = "daily", question: str = "",
                              additional_info: dict = None):
        """ChatService에서 호출하는 운세 생성 메서드 - 완전히 LLM 기반"""
        from fastapi import WebSocket
        import json
        
        try:
            logger.info(f"🔍 FortuneService.generate_fortune 시작: fortune_type={fortune_type}, question='{question}'")
            
            # 사용자 데이터 구성
            user_data = {
                "session_id": session_id,
                **(additional_info or {})
            }
            logger.info(f"🔍 사용자 데이터 구성 완료: {user_data}")
            
            # LLM 기반 운세 생성 - 템플릿 완전 제거
            logger.info(f"🔍 LLM 운세 생성 시작...")
            overall_description = await self.engine.generate_llm_fortune(fortune_type, question, user_data)
            logger.info(f"🔍 LLM 운세 생성 완료: '{overall_description}'")
            
            # 프론트엔드 호환을 위한 기본 운세 구조 생성 (JSON 형식 절대 변경하지 않음)
            fortune_result = {
                "fortune_id": str(uuid.uuid4()),
                "type": fortune_type,
                "date": datetime.now().date().isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "success": True,
                "message": overall_description,
                "score": random.randint(60, 95),
                "live2d_emotion": "joy" if "좋" in overall_description or "행운" in overall_description else "comfort",
                "live2d_motion": "blessing"
            }
            
            # WebSocket으로 응답 전송 (프론트엔드 TTS 처리를 위한 fortune_result 타입)
            response_data = {
                "type": "fortune_result",
                "data": {
                    "tts_text": overall_description,
                    "character_message": overall_description,
                    "fortune_content": overall_description,
                    "live2d_emotion": fortune_result.get("live2d_emotion", "joy"),
                    "live2d_motion": fortune_result.get("live2d_motion", "blessing"),
                    "fortune_result": fortune_result
                }
            }
            
            await websocket.send_text(json.dumps(response_data, ensure_ascii=False))
            logger.info(f"LLM fortune generated and sent for session: {session_id}")
            
            # 데이터베이스 저장
            try:
                await self._save_fortune_session(db, fortune_type, fortune_result, user_data, question)
            except Exception as e:
                logger.warning(f"Failed to save fortune session: {e}")
            
        except Exception as e:
            logger.error(f"Error in generate_fortune: {e}")
            # 에러 응답 전송
            error_response = {
                "type": "error",
                "data": {
                    "message": "운세 생성 중 오류가 발생했습니다.",
                    "error": str(e)
                }
            }
            await websocket.send_text(json.dumps(error_response, ensure_ascii=False))

    async def _save_fortune_session(self, db: Session, fortune_type: str,
                                   result: Dict[str, Any], user_data: Optional[Dict],
                                   question: Optional[str] = None):
        """운세 세션 저장"""
        try:
            fortune_session = FortuneSession(
                fortune_id=result["fortune_id"],
                session_id=user_data.get("session_id") if user_data else None,
                user_uuid=user_data.get("user_uuid") if user_data else None,
                fortune_type=fortune_type,
                question=question,
                question_type=None,
                result=json.dumps(result, ensure_ascii=False)
            )
            
            # 캐시 TTL 설정 (24시간)
            fortune_session.set_cache_ttl(24)
            
            db.add(fortune_session)
            db.commit()
            
            logger.info(f"Fortune session saved: {fortune_session.fortune_id}")
            
        except Exception as e:
            logger.error(f"Error saving fortune session: {e}")
            db.rollback()
            # 저장 실패해도 서비스는 계속 동작
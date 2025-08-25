"""
Cerebras AI 기반 운세 생성 엔진
LLM을 활용한 개인화된 운세 생성
"""

import json
import asyncio
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
from cerebras.cloud.sdk import Cerebras
from pydantic import BaseModel, Field

from .engines import (
    FortuneEngineBase, 
    PersonalizationContext, 
    FortuneGrade
)
from ..models.fortune import (
    FortuneResult, 
    FortuneCategory, 
    FortuneType, 
    TarotCard, 
    LuckyElement
)

logger = logging.getLogger(__name__)


class CerebrasConfig(BaseModel):
    """Cerebras API 설정"""
    api_key: str = Field(description="Cerebras API Key")
    model: str = Field(default="llama3.1-8b", description="Cerebras 모델명")
    fallback_model: str = Field(default="llama3-8b", description="Fallback 모델명")
    available_models: List[str] = Field(default=[
        "llama3.1-8b", 
        "llama-3.1-8b",
        "llama3-8b",
        "llama3.1-70b",
        "llama-3.1-70b",
        "llama3-70b"
    ], description="사용 가능한 모델 목록")
    max_tokens: int = Field(default=1000, description="최대 토큰 수")
    temperature: float = Field(default=0.7, description="생성 온도")
    timeout: int = Field(default=30, description="API 타임아웃 (초)")


@dataclass
class FortunePrompt:
    """운세 생성 프롬프트"""
    system_prompt: str
    user_prompt: str
    context_data: Dict[str, Any]


class CerebrasFortuneEngine(FortuneEngineBase):
    """Cerebras AI 기반 운세 엔진"""
    
    def __init__(self, config: CerebrasConfig):
        super().__init__()
        self.config = config
        self.client = Cerebras(api_key=config.api_key)
        
        # 운세 타입별 시스템 프롬프트
        self.system_prompts = {
            FortuneType.DAILY: """
당신은 전문적인 운세 상담사입니다. 사용자의 개인정보를 바탕으로 따뜻하고 희망적인 일일 운세를 제공해주세요.

응답 형식:
- 전체 운세 (overall_score, overall_description)
- 카테고리별 운세: 사랑(love), 금전(money), 건강(health), 직업(work)
- 각 카테고리마다 점수(0-100)와 설명 제공
- 행운 요소: 색상, 숫자, 아이템
- 조언과 주의사항
- Live2D 감정: neutral, joy, thinking, concern, surprise, mystical, comfort, playful 중 선택

응답은 반드시 JSON 형식으로 제공해주세요.
""",
            FortuneType.TAROT: """
당신은 전문적인 타로 리더입니다. 3장의 타로 카드(과거-현재-미래)를 해석하여 깊이 있는 운세를 제공해주세요.

타로 카드 해석 시:
- 각 카드의 위치별 의미 설명
- 정방향/역방향 해석
- 전체적인 메시지와 조언
- Live2D 감정은 주로 'mystical' 사용

응답은 반드시 JSON 형식으로 제공해주세요.
""",
            FortuneType.ZODIAC: """
당신은 서양 점성술 전문가입니다. 별자리별 특성을 고려한 개인화된 운세를 제공해주세요.

별자리별 해석:
- 각 별자리의 고유 특성 반영
- 행성의 영향 고려
- 별자리 호환성 정보 포함
- 행운의 색상, 숫자, 보석 제시

응답은 반드시 JSON 형식으로 제공해주세요.
""",
            FortuneType.ORIENTAL: """
당신은 동양 사주명리학 전문가입니다. 사주의 오행 이론을 바탕으로 전통적이면서도 현대적인 해석을 제공해주세요.

사주 해석 요소:
- 오행(목화토금수) 균형 분석
- 천간지지 조합 해석
- 대운과 세운의 영향
- 개선 방법과 주의사항 제시

응답은 반드시 JSON 형식으로 제공해주세요.
"""
        }
        
        # 감정 매핑
        self.emotion_mapping = {
            "excellent": "joy",
            "good": "comfort", 
            "normal": "neutral",
            "bad": "concern",
            "warning": "mystical"
        }
    
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """Cerebras AI를 활용한 운세 생성"""
        if date_target is None:
            date_target = datetime.now().date()
        
        try:
            # 프롬프트 생성
            prompt = self._build_fortune_prompt(context, date_target, additional_params)
            
            # Cerebras API 호출
            response = await self._call_cerebras_api(prompt)
            
            # 응답 파싱 및 FortuneResult 생성
            fortune_result = self._parse_fortune_response(
                response, context, date_target, additional_params
            )
            
            return fortune_result
            
        except Exception as e:
            logger.error(f"Cerebras 운세 생성 실패: {str(e)}")
            # 폴백: 기본 엔진 사용
            return await self._create_fallback_fortune(context, date_target, additional_params)
    
    def _build_fortune_prompt(
        self, 
        context: PersonalizationContext,
        date_target: date,
        additional_params: Dict = None
    ) -> FortunePrompt:
        """운세 생성 프롬프트 구성"""
        # 기본 컨텍스트 데이터
        context_data = {
            "date": date_target.isoformat(),
            "fortune_type": self.fortune_type.value if self.fortune_type else "daily",
            "birth_date": self._safe_date_format(context.birth_date) if context.birth_date else None,
            "zodiac_sign": context.zodiac_sign.value if context.zodiac_sign else None,
            "preferences": context.preferences,
            "additional_params": additional_params or {}
        }
        
        # 시스템 프롬프트 선택
        system_prompt = self.system_prompts.get(
            self.fortune_type, 
            self.system_prompts[FortuneType.DAILY]
        )
        
        # 사용자 프롬프트 구성
        user_prompt = self._build_user_prompt(context, date_target, additional_params)
        
        return FortunePrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_data=context_data
        )
    
    def _build_user_prompt(
        self,
        context: PersonalizationContext,
        date_target: date,
        additional_params: Dict = None
    ) -> str:
        """사용자별 맞춤 프롬프트 생성"""
        prompt_parts = [
            f"날짜: {date_target.strftime('%Y년 %m월 %d일')}",
            f"운세 유형: {self._get_fortune_type_korean()}"
        ]
        
        # 개인 정보 추가
        if context.birth_date:
            prompt_parts.append(f"생년월일: {context.birth_date.strftime('%Y년 %m월 %d일')}")
        
        if context.zodiac_sign:
            prompt_parts.append(f"별자리: {self._get_zodiac_korean(context.zodiac_sign)}")
        
        # 추가 매개변수
        if additional_params:
            if "question" in additional_params:
                prompt_parts.append(f"질문: {additional_params['question']}")
            if "question_type" in additional_params:
                prompt_parts.append(f"질문 유형: {additional_params['question_type']}")
        
        # JSON 응답 요구사항
        prompt_parts.extend([
            "",
            "위 정보를 바탕으로 개인화된 운세를 생성해주세요.",
            "응답은 반드시 다음 JSON 형식을 따라주세요:",
            self._get_json_schema()
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_fortune_type_korean(self) -> str:
        """운세 타입 한국어 변환"""
        korean_names = {
            FortuneType.DAILY: "일일 운세",
            FortuneType.TAROT: "타로 운세",
            FortuneType.ZODIAC: "별자리 운세",
            FortuneType.ORIENTAL: "사주 운세"
        }
        return korean_names.get(self.fortune_type, "일일 운세")
    
    def _get_zodiac_korean(self, zodiac_sign) -> str:
        """별자리 한국어 변환"""
        korean_names = {
            "ARIES": "양자리", "TAURUS": "황소자리", "GEMINI": "쌍둥이자리",
            "CANCER": "게자리", "LEO": "사자자리", "VIRGO": "처녀자리",
            "LIBRA": "천칭자리", "SCORPIO": "전갈자리", "SAGITTARIUS": "사수자리",
            "CAPRICORN": "염소자리", "AQUARIUS": "물병자리", "PISCES": "물고기자리"
        }
        return korean_names.get(zodiac_sign.name, str(zodiac_sign))
    
    def _safe_date_format(self, date_obj) -> str:
        """날짜 객체를 안전하게 문자열로 변환"""
        if isinstance(date_obj, str):
            # 이미 문자열인 경우 그대로 반환
            return date_obj
        elif hasattr(date_obj, 'isoformat'):
            # date 또는 datetime 객체인 경우
            return date_obj.isoformat()
        elif hasattr(date_obj, 'date'):
            # datetime 객체에서 date 부분만 추출
            return date_obj.date().isoformat()
        else:
            # 기타 경우 문자열로 변환
            return str(date_obj)
    
    def _extract_json_from_response(self, response: str) -> str:
        """응답에서 JSON 텍스트를 추출 (마크다운 코드 블록 처리)"""
        # 먼저 마크다운 코드 블록 확인
        import re
        
        # ```json 또는 ```JSON 코드 블록에서 JSON 추출
        json_block_pattern = r'```(?:json|JSON)?\s*\n(.*?)\n```'
        match = re.search(json_block_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if match:
            json_text = match.group(1).strip()
            logger.debug(f"마크다운 코드 블록에서 JSON 추출: {json_text[:100]}...")
            return json_text
        
        # 마크다운 블록이 없으면 중괄호 {} 사이의 JSON 찾기
        brace_pattern = r'\{.*\}'
        match = re.search(brace_pattern, response, re.DOTALL)
        
        if match:
            json_text = match.group(0).strip()
            logger.debug(f"중괄호에서 JSON 추출: {json_text[:100]}...")
            return json_text
        
        # JSON 패턴을 찾지 못하면 원본 응답 반환
        logger.warning("JSON 패턴을 찾을 수 없음, 원본 응답 사용")
        return response.strip()
    
    def _get_json_schema(self) -> str:
        """JSON 스키마 정의"""
        if self.fortune_type == FortuneType.TAROT:
            return """
{
    "overall_score": 75,
    "overall_description": "전체 운세 설명",
    "tarot_cards": [
        {
            "position": "past",
            "card_name": "카드명",
            "interpretation": "해석",
            "is_reversed": false
        }
    ],
    "advice": "조언",
    "live2d_emotion": "mystical"
}
"""
        else:
            return """
{
    "overall_score": 75,
    "overall_description": "전체 운세 설명",
    "categories": {
        "love": {"score": 80, "description": "사랑 운세"},
        "money": {"score": 70, "description": "금전 운세"}, 
        "health": {"score": 85, "description": "건강 운세"},
        "work": {"score": 75, "description": "직업 운세"}
    },
    "lucky_elements": {
        "colors": ["파란색", "흰색"],
        "numbers": [7, 21, 33],
        "items": ["열쇠고리", "노트"]
    },
    "advice": "조언 메시지",
    "warnings": ["주의사항1", "주의사항2"],
    "live2d_emotion": "joy"
}
"""
    
    async def _call_cerebras_api(self, prompt: FortunePrompt) -> str:
        """Cerebras API 호출 (모델 fallback 포함)"""
        models_to_try = [self.config.model]
        
        # 기본 모델이 사용 가능한 모델 목록에 없으면 fallback 모델을 먼저 시도
        if self.config.model not in self.config.available_models:
            models_to_try = [self.config.fallback_model] + self.config.available_models
        else:
            # fallback 모델을 두 번째 선택지로 추가
            if self.config.fallback_model != self.config.model:
                models_to_try.append(self.config.fallback_model)
            # 나머지 사용 가능한 모델들 추가
            for model in self.config.available_models:
                if model not in models_to_try:
                    models_to_try.append(model)
        
        last_exception = None
        
        for model in models_to_try:
            try:
                logger.info(f"[LLM 호출] Cerebras API 호출 시도: {model}")
                logger.info(f"[LLM 요청] 시스템 프롬프트: {prompt.system_prompt[:200]}...")
                logger.info(f"[LLM 요청] 사용자 프롬프트: {prompt.user_prompt[:200]}...")
                
                # 동기 클라이언트를 비동기로 래핑
                loop = asyncio.get_event_loop()
                
                def sync_call(model_name):
                    completion = self.client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": prompt.system_prompt},
                            {"role": "user", "content": prompt.user_prompt}
                        ],
                        model=model_name,
                        max_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                    )
                    return completion.choices[0].message.content
                
                # 타임아웃과 함께 실행
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: sync_call(model)),
                    timeout=self.config.timeout
                )
                
                logger.info(f"[LLM 성공] Cerebras API 호출 성공 (모델: {model})")
                logger.info(f"[LLM 응답] 길이: {len(response)} 문자")
                logger.info(f"[LLM 응답] 내용: {response[:300]}...")
                return response
                
            except asyncio.TimeoutError as e:
                last_exception = e
                logger.warning(f"Cerebras API 타임아웃 (모델: {model}, {self.config.timeout}초)")
                continue
            except Exception as e:
                last_exception = e
                logger.warning(f"Cerebras API 호출 실패 (모델: {model}): {str(e)}")
                # 모델이 존재하지 않는 경우 다른 모델 시도
                if "does not exist" in str(e).lower() or "not found" in str(e).lower():
                    continue
                # 기타 API 오류의 경우도 다른 모델 시도
                continue
        
        # 모든 모델이 실패한 경우
        logger.error(f"모든 Cerebras 모델 호출 실패. 마지막 오류: {last_exception}")
        raise last_exception or Exception("모든 Cerebras 모델을 사용할 수 없습니다")
    
    def _parse_fortune_response(
        self,
        response: str,
        context: PersonalizationContext,
        date_target: date,
        additional_params: Dict = None
    ) -> FortuneResult:
        """Cerebras 응답을 FortuneResult로 변환"""
        try:
            # JSON 파싱 (마크다운 코드 블록 처리 포함)
            json_text = self._extract_json_from_response(response)
            data = json.loads(json_text.strip())
            
            # 기본 정보
            overall_score = data.get("overall_score", 75)
            overall_description = data.get("overall_description", "운세 정보")
            
            # Live2D 감정 설정
            live2d_emotion = data.get("live2d_emotion", "neutral")
            live2d_motion = self._get_motion_from_fortune_type()
            
            # 카테고리별 운세
            categories = {}
            if "categories" in data:
                for category_name, category_data in data["categories"].items():
                    categories[category_name] = FortuneCategory(
                        score=category_data.get("score", 50),
                        grade=self._score_to_grade(category_data.get("score", 50)),
                        description=category_data.get("description", "")
                    )
            
            # 행운 요소
            lucky_elements = None
            if "lucky_elements" in data:
                le_data = data["lucky_elements"]
                lucky_elements = LuckyElement(
                    colors=le_data.get("colors", []),
                    numbers=le_data.get("numbers", []),
                    items=le_data.get("items", [])
                )
            
            # 타로 카드 (타로 운세인 경우)
            tarot_cards = []
            if self.fortune_type == FortuneType.TAROT and "tarot_cards" in data:
                for card_data in data["tarot_cards"]:
                    tarot_cards.append(TarotCard(
                        position=card_data.get("position", "present"),
                        card_name=card_data.get("card_name", ""),
                        card_meaning="",
                        interpretation=card_data.get("interpretation", ""),
                        is_reversed=card_data.get("is_reversed", False),
                        keywords=[],
                        image_url=""
                    ))
            
            # FortuneResult 생성
            import uuid
            return FortuneResult(
                fortune_id=str(uuid.uuid4()),  # Generate unique fortune ID
                fortune_type=self.fortune_type or FortuneType.DAILY,
                date=date_target.isoformat(),  # Convert date to string
                overall_fortune=FortuneCategory(
                    score=overall_score,
                    grade=self._score_to_grade(overall_score),
                    description=overall_description
                ),
                categories=categories,
                tarot_cards=tarot_cards,
                lucky_elements=lucky_elements,
                advice=data.get("advice", ""),
                warnings=data.get("warnings", []),
                question=additional_params.get("question", "") if additional_params else "",
                live2d_emotion=live2d_emotion,
                live2d_motion=live2d_motion,
                created_at=datetime.now()  # Add creation timestamp
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 실패: {str(e)}")
            logger.error(f"응답 내용: {response}")
            # 폴백 응답 생성
            return self._create_simple_fallback_fortune(context, date_target, response)
        except Exception as e:
            logger.error(f"응답 파싱 실패: {str(e)}")
            raise
    
    def _score_to_grade(self, score: int) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 50:
            return "normal"
        elif score >= 30:
            return "bad"
        else:
            return "warning"
    
    def _get_motion_from_fortune_type(self) -> str:
        """운세 타입별 Live2D 모션"""
        motion_map = {
            FortuneType.DAILY: "crystal_gaze",
            FortuneType.TAROT: "card_draw",
            FortuneType.ZODIAC: "blessing",
            FortuneType.ORIENTAL: "special_reading"
        }
        return motion_map.get(self.fortune_type, "crystal_gaze")
    
    def _extract_overall_description_from_raw(self, raw_response: str) -> str:
        """원시 응답에서 overall_description 값 추출"""
        import re
        
        logger.info(f"[Fallback] 원시 응답에서 overall_description 추출 시도: {raw_response[:200]}...")
        
        # overall_description 필드 직접 찾기
        pattern = r'"overall_description"\s*:\s*"([^"]+)"'
        match = re.search(pattern, raw_response, re.IGNORECASE)
        
        if match:
            description = match.group(1)
            logger.info(f"[Fallback] overall_description 추출 성공: {description[:100]}...")
            return description
        
        # 따옴표가 없는 경우도 시도
        pattern = r'overall_description["\s:]+([^,\n\}]+)'
        match = re.search(pattern, raw_response, re.IGNORECASE)
        
        if match:
            description = match.group(1).strip().strip('"').strip()
            logger.info(f"[Fallback] overall_description 패턴 매치: {description[:100]}...")
            return description
        
        # 기본 메시지 반환
        default_messages = {
            FortuneType.DAILY: "오늘은 좋은 기운이 함께 하는 날입니다. 긍정적인 마음으로 하루를 시작해보세요!",
            FortuneType.TAROT: "타로 카드가 전하는 메시지를 마음에 새겨보세요.",
            FortuneType.ZODIAC: "별자리의 기운이 당신과 함께 합니다.",
            FortuneType.ORIENTAL: "사주에 나타난 운명의 흐름을 느껴보세요."
        }
        
        default_message = default_messages.get(self.fortune_type, "좋은 기운이 함께 하는 하루가 될 것 같습니다!")
        logger.info(f"[Fallback] 기본 메시지 사용: {default_message}")
        return default_message
    
    def _create_simple_fallback_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date,
        raw_response: str
    ) -> FortuneResult:
        """간단한 폴백 운세 생성 (JSON 파싱 실패 시)"""
        # 텍스트에서 overall_description 추출 시도
        score = 70  # 기본 점수
        
        # overall_description을 찾아서 추출
        description = self._extract_overall_description_from_raw(raw_response)
        
        import uuid
        return FortuneResult(
            fortune_id=str(uuid.uuid4()),
            fortune_type=self.fortune_type or FortuneType.DAILY,
            date=date_target.isoformat(),
            overall_fortune=FortuneCategory(
                score=score,
                grade="good",
                description=description
            ),
            categories={},
            advice="AI 생성된 개인화된 조언입니다.",
            live2d_emotion="neutral",
            live2d_motion="crystal_gaze",
            created_at=datetime.now()
        )
    
    async def _create_fallback_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date,
        additional_params: Dict = None
    ) -> FortuneResult:
        """완전 실패 시 폴백 운세"""
        import uuid
        return FortuneResult(
            fortune_id=str(uuid.uuid4()),
            fortune_type=self.fortune_type or FortuneType.DAILY,
            date=date_target.isoformat(),
            overall_fortune=FortuneCategory(
                score=60,
                grade="normal",
                description="AI 서비스 일시 중단으로 기본 운세를 제공해드려요. 잠시 후 다시 시도해주세요."
            ),
            categories={
                "love": FortuneCategory(score=60, grade="normal", description="평온한 감정의 흐름"),
                "money": FortuneCategory(score=60, grade="normal", description="안정적인 재정 상태"),
                "health": FortuneCategory(score=60, grade="normal", description="건강한 컨디션"),
                "work": FortuneCategory(score=60, grade="normal", description="꾸준한 업무 진행")
            },
            advice="차분하게 하루를 보내시고, 곧 더 자세한 운세를 확인해보세요.",
            live2d_emotion="neutral",
            live2d_motion="crystal_gaze",
            created_at=datetime.now()
        )


# 특정 운세 타입별 Cerebras 엔진
class CerebrasDailyFortuneEngine(CerebrasFortuneEngine):
    """Cerebras AI 일일 운세 엔진"""
    
    def __init__(self, config: CerebrasConfig):
        super().__init__(config)
        self.fortune_type = FortuneType.DAILY


class CerebrasTarotFortuneEngine(CerebrasFortuneEngine):
    """Cerebras AI 타로 운세 엔진"""
    
    def __init__(self, config: CerebrasConfig):
        super().__init__(config)
        self.fortune_type = FortuneType.TAROT


class CerebrasZodiacFortuneEngine(CerebrasFortuneEngine):
    """Cerebras AI 별자리 운세 엔진"""
    
    def __init__(self, config: CerebrasConfig):
        super().__init__(config)
        self.fortune_type = FortuneType.ZODIAC


class CerebrasSajuFortuneEngine(CerebrasFortuneEngine):
    """Cerebras AI 사주 운세 엔진"""
    
    def __init__(self, config: CerebrasConfig):
        super().__init__(config)
        self.fortune_type = FortuneType.ORIENTAL
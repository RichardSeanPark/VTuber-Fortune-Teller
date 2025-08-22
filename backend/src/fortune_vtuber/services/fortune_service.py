"""
Fortune Service - 운세 생성 및 관리 서비스

4가지 운세 타입 (일일, 타로, 별자리, 사주) 구현
개인화된 운세 생성 알고리즘 및 캐싱 관리
"""

import random
import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.fortune import (
    FortuneSession, TarotCardDB, ZodiacInfo,
    FortuneType, QuestionType, ZodiacSign
)
from ..models.user import User
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class FortuneEngine:
    """운세 생성 엔진 - 개인화된 운세 알고리즘"""
    
    def __init__(self):
        self.fortune_templates = self._load_fortune_templates()
        self.lucky_items = self._load_lucky_items()
    
    def _load_fortune_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """운세 템플릿 로드"""
        return {
            "excellent": {
                "overall": [
                    "오늘은 모든 일이 순조롭게 풀려나갈 것 같아요! ✨",
                    "행운의 기운이 가득한 하루가 될 것 같네요!",
                    "오늘은 특별한 날이 될 것 같아요. 기대해보세요!",
                    "우주의 에너지가 당신을 응원하고 있어요!"
                ],
                "love": [
                    "연애운이 최고조에 달했어요! 💕",
                    "로맨틱한 일들이 기다리고 있을 것 같아요!",
                    "사랑의 기운이 당신을 둘러싸고 있어요.",
                    "특별한 인연을 만날 수 있는 날이에요!"
                ],
                "money": [
                    "재정 운이 상승세에 있어요! 💰",
                    "투자나 부업에 좋은 기회가 올 것 같네요.",
                    "돈과 관련된 좋은 소식이 있을 것 같아요.",
                    "경제적 안정을 찾을 수 있는 하루에요!"
                ],
                "health": [
                    "건강 상태가 매우 좋아요! 💪",
                    "활력이 넘치는 하루가 될 것 같네요.",
                    "몸과 마음이 모두 건강한 상태예요.",
                    "운동하기에 최적의 컨디션이에요!"
                ],
                "work": [
                    "업무에서 큰 성과를 거둘 수 있어요! 🎯",
                    "창의적인 아이디어가 샘솟을 것 같네요.",
                    "동료들과의 협력이 완벽할 것 같아요.",
                    "승진이나 인정받을 기회가 올 것 같네요!"
                ]
            },
            "good": {
                "overall": [
                    "전체적으로 좋은 하루가 될 것 같아요!",
                    "긍정적인 에너지가 느껴지는 날이에요.",
                    "작은 행복들을 발견할 수 있을 것 같네요.",
                    "평온하고 안정적인 하루가 될 것 같아요."
                ],
                "love": [
                    "연애운이 상승세에 있어요!",
                    "좋은 만남이나 대화가 있을 것 같네요.",
                    "관계가 한 단계 발전할 수 있어요.",
                    "따뜻한 마음을 나눌 수 있는 날이에요."
                ],
                "money": [
                    "재정 관리에 신경 쓰면 좋은 결과가 있을 것 같아요.",
                    "작은 수입이 생길 수 있어요.",
                    "절약하기 좋은 날이에요.",
                    "경제적 계획을 세우기 좋은 시기예요."
                ],
                "health": [
                    "건강한 하루가 될 것 같아요.",
                    "가벼운 운동을 하면 좋을 것 같네요.",
                    "충분한 휴식을 취하세요.",
                    "건강 관리에 신경 쓰면 좋겠어요."
                ],
                "work": [
                    "업무가 순조롭게 진행될 것 같아요.",
                    "새로운 아이디어가 떠오를 수 있어요.",
                    "동료들과 좋은 관계를 유지할 수 있어요.",
                    "차근차근 진행하면 좋은 결과가 있을 것 같네요."
                ]
            },
            "normal": {
                "overall": [
                    "평범하지만 안정적인 하루가 될 것 같아요.",
                    "큰 변화는 없지만 무난한 날이에요.",
                    "차분하게 하루를 보내시면 좋겠어요.",
                    "작은 것에 감사하며 보내세요."
                ],
                "love": [
                    "연애운은 평온한 상태예요.",
                    "기존 관계를 유지하는데 집중하세요.",
                    "소소한 대화를 나누어보세요.",
                    "서두르지 말고 천천히 진행하세요."
                ],
                "money": [
                    "재정 상태는 안정적이에요.",
                    "큰 지출은 피하는 것이 좋겠어요.",
                    "계획적인 소비를 하세요.",
                    "저축에 신경 쓰시는 것이 좋겠어요."
                ],
                "health": [
                    "건강 상태는 평범해요.",
                    "규칙적인 생활을 유지하세요.",
                    "충분한 수면을 취하세요.",
                    "스트레스 관리에 신경 쓰세요."
                ],
                "work": [
                    "업무는 평상시와 같을 것 같아요.",
                    "루틴한 일들을 차근차근 처리하세요.",
                    "새로운 도전보다는 기본에 충실하세요.",
                    "동료들과의 소통을 늘려보세요."
                ]
            },
            "caution": {
                "overall": [
                    "조금 주의가 필요한 하루예요.",
                    "신중하게 행동하시는 것이 좋겠어요.",
                    "성급한 결정은 피하세요.",
                    "차분하게 하루를 보내시길 바라요."
                ],
                "love": [
                    "연애운에 약간의 주의가 필요해요.",
                    "상대방의 마음을 먼저 생각해보세요.",
                    "오해가 생기지 않도록 조심하세요.",
                    "감정 조절에 신경 쓰세요."
                ],
                "money": [
                    "재정 관리에 더욱 신경 쓰세요.",
                    "불필요한 지출은 줄이는 것이 좋겠어요.",
                    "투자는 신중하게 결정하세요.",
                    "계획을 다시 한번 점검해보세요."
                ],
                "health": [
                    "건강 관리에 더욱 신경 쓰세요.",
                    "과로는 피하시는 것이 좋겠어요.",
                    "충분한 휴식을 취하세요.",
                    "스트레스를 줄이려고 노력하세요."
                ],
                "work": [
                    "업무에서 실수가 없도록 주의하세요.",
                    "중요한 결정은 미루는 것이 좋겠어요.",
                    "동료들과의 갈등을 피하세요.",
                    "차분하게 일을 처리하세요."
                ]
            }
        }
    
    def _load_lucky_items(self) -> Dict[str, List[str]]:
        """행운의 아이템 데이터 로드"""
        return {
            "items": [
                "파란색 볼펜", "흰색 머그컵", "작은 화분", "향이 좋은 캔들",
                "따뜻한 차", "좋아하는 음악", "편안한 쿠션", "예쁜 노트",
                "향긋한 핸드크림", "부드러운 스카프", "달콤한 초콜릿", "신선한 과일",
                "아늑한 담요", "좋은 책", "따뜻한 커피", "예쁜 꽃",
                "편안한 신발", "좋은 향수", "맛있는 티백", "포근한 베개"
            ],
            "colors": [
                "파란색", "분홍색", "노란색", "초록색", "보라색",
                "주황색", "하늘색", "연두색", "라벤더", "민트색",
                "베이지", "아이보리", "코랄", "터코이즈", "골드"
            ],
            "numbers": list(range(1, 46))  # 1-45 로또 번호 범위
        }
    
    def calculate_base_fortune_score(self, user_data: Optional[Dict] = None, 
                                   fortune_type: str = "daily") -> int:
        """기본 운세 점수 계산 (0-100)"""
        base_score = random.randint(40, 95)
        
        # 사용자 데이터 기반 개인화
        if user_data:
            birth_date = user_data.get("birth_date")
            if birth_date:
                # 생년월일 기반 미세 조정
                if isinstance(birth_date, str):
                    try:
                        birth_date = datetime.strptime(birth_date, "%Y-%m-%d").date()
                    except ValueError:
                        birth_date = None
                
                if birth_date:
                    # 생일과 현재 날짜의 차이로 미세 조정
                    days_diff = (datetime.now().date() - birth_date).days
                    adjustment = (days_diff % 7) - 3  # -3 to +3
                    base_score = max(10, min(100, base_score + adjustment))
        
        # 운세 타입별 조정
        type_adjustments = {
            "daily": 0,
            "tarot": random.randint(-5, 5),
            "zodiac": random.randint(-3, 3),
            "oriental": random.randint(-7, 7)
        }
        
        adjustment = type_adjustments.get(fortune_type, 0)
        return max(10, min(100, base_score + adjustment))
    
    def get_fortune_grade(self, score: int) -> str:
        """점수에 따른 운세 등급 결정"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "normal"
        else:
            return "caution"
    
    def generate_category_fortune(self, category: str, base_score: int, 
                                user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """카테고리별 운세 생성"""
        # 카테고리별 점수 변동
        category_variance = {
            "love": random.randint(-10, 15),
            "money": random.randint(-8, 12),
            "health": random.randint(-5, 10),
            "work": random.randint(-7, 13)
        }
        
        score = max(10, min(100, base_score + category_variance.get(category, 0)))
        grade = self.get_fortune_grade(score)
        
        # 템플릿에서 설명 선택
        descriptions = self.fortune_templates.get(grade, {}).get(category, [])
        description = random.choice(descriptions) if descriptions else "좋은 하루가 될 것 같아요."
        
        return {
            "score": score,
            "grade": grade,
            "description": description
        }
    
    def generate_lucky_elements(self, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """행운의 요소들 생성"""
        # 사용자 데이터 기반 개인화 가능
        birth_date = None
        if user_data and user_data.get("birth_date"):
            try:
                birth_date = datetime.strptime(user_data["birth_date"], "%Y-%m-%d").date()
            except ValueError:
                pass
        
        # 생년월일 기반 시드 설정 (일관성 위해)
        if birth_date:
            seed_base = birth_date.day + birth_date.month
            random.seed(seed_base + datetime.now().day)
        
        lucky_items = random.sample(self.lucky_items["items"], 2)
        lucky_colors = random.sample(self.lucky_items["colors"], 2)
        lucky_numbers = sorted(random.sample(self.lucky_items["numbers"], 3))
        
        # 시드 초기화
        random.seed()
        
        return {
            "items": lucky_items,
            "colors": lucky_colors,
            "numbers": lucky_numbers
        }
    
    def generate_advice_and_warnings(self, overall_grade: str, 
                                   category_scores: Dict[str, int]) -> Tuple[str, List[str]]:
        """조언과 주의사항 생성"""
        advice_templates = {
            "excellent": [
                "오늘은 새로운 도전을 해보세요!",
                "긍정적인 에너지를 주변 사람들과 나누어보세요.",
                "좋은 기회를 놓치지 마세요!",
                "자신감을 가지고 행동하세요."
            ],
            "good": [
                "차근차근 계획을 세워보세요.",
                "주변 사람들과 좋은 시간을 보내세요.",
                "새로운 것을 배워보는 것도 좋겠어요.",
                "감사하는 마음을 가져보세요."
            ],
            "normal": [
                "평범한 하루도 소중하다는 것을 기억하세요.",
                "작은 행복을 찾아보세요.",
                "차분하게 하루를 보내시길 바라요.",
                "내일을 위해 준비해보세요."
            ],
            "caution": [
                "성급한 결정은 피하세요.",
                "신중하게 행동하시는 것이 좋겠어요.",
                "휴식을 충분히 취하세요.",
                "주변 사람들의 조언을 들어보세요."
            ]
        }
        
        warning_templates = {
            "love": "연인과의 갈등을 피하세요.",
            "money": "큰 지출은 신중하게 결정하세요.",
            "health": "과로는 피하시는 것이 좋겠어요.",
            "work": "중요한 업무는 재확인하세요."
        }
        
        advice = random.choice(advice_templates.get(overall_grade, advice_templates["normal"]))
        
        warnings = []
        for category, score in category_scores.items():
            if score < 60:  # 낮은 점수인 경우 경고 추가
                warning = warning_templates.get(category)
                if warning:
                    warnings.append(warning)
        
        return advice, warnings


class FortuneService:
    """운세 서비스 - 운세 생성, 조회, 캐싱 관리"""
    
    def __init__(self, database_service=None, cache_service: CacheService = None):
        self.engine = FortuneEngine()
        self.cache_service = cache_service or CacheService()
        self.database_service = database_service
        self._initialized = False
    
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
    
    async def get_daily_fortune(self, db: Session, user_data: Optional[Dict] = None,
                               force_regenerate: bool = False) -> Dict[str, Any]:
        """일일 운세 조회/생성"""
        try:
            # 캐시 확인 (사용자별 + 날짜별)
            cache_key = self._get_daily_cache_key(user_data)
            
            if not force_regenerate:
                cached_fortune = self.cache_service.get(cache_key)
                if cached_fortune:
                    logger.info(f"Daily fortune served from cache: {cache_key}")
                    return cached_fortune
            
            # 새로운 일일 운세 생성
            fortune_result = self._generate_daily_fortune(user_data)
            
            # 캐시 저장 (24시간)
            self.cache_service.set(cache_key, fortune_result, ttl_seconds=86400)
            
            # 데이터베이스 저장
            await self._save_fortune_session(
                db, FortuneType.DAILY, fortune_result, user_data
            )
            
            logger.info(f"Daily fortune generated for user: {user_data.get('user_uuid') if user_data else 'anonymous'}")
            return fortune_result
            
        except Exception as e:
            logger.error(f"Error generating daily fortune: {e}")
            raise
    
    async def get_tarot_fortune(self, db: Session, question: str, 
                               question_type: QuestionType = QuestionType.GENERAL,
                               user_data: Optional[Dict] = None,
                               card_count: int = 3) -> Dict[str, Any]:
        """타로 운세 생성"""
        try:
            # 타로 카드 선택
            cards = self._select_tarot_cards(db, card_count)
            
            if not cards:
                # 기본 카드 데이터가 없는 경우 더미 데이터 생성
                cards = self._generate_dummy_tarot_cards(card_count)
            
            # 타로 해석 생성
            fortune_result = self._generate_tarot_interpretation(
                cards, question, question_type, user_data
            )
            
            # 데이터베이스 저장
            await self._save_fortune_session(
                db, FortuneType.TAROT, fortune_result, user_data, 
                question=question, question_type=question_type
            )
            
            logger.info(f"Tarot fortune generated for question: {question[:50]}...")
            return fortune_result
            
        except Exception as e:
            logger.error(f"Error generating tarot fortune: {e}")
            raise
    
    async def get_zodiac_fortune(self, db: Session, zodiac_sign: ZodiacSign,
                                period: str = "daily", 
                                user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """별자리 운세 조회/생성"""
        try:
            # 별자리 정보 조회
            zodiac_info = ZodiacInfo.find_by_sign(db, zodiac_sign.value)
            
            if not zodiac_info:
                # 기본 별자리 정보가 없는 경우 더미 데이터 생성
                zodiac_info = self._generate_dummy_zodiac_info(zodiac_sign)
            
            # 캐시 확인
            cache_key = self._get_zodiac_cache_key(zodiac_sign, period)
            cached_fortune = self.cache_service.get(cache_key)
            
            if cached_fortune and not (user_data and user_data.get("force_regenerate", False)):
                logger.info(f"Zodiac fortune served from cache: {cache_key}")
                return cached_fortune
            
            # 별자리 운세 생성
            fortune_result = self._generate_zodiac_fortune(zodiac_info, period, user_data)
            
            # 캐시 저장 (기간별 TTL)
            ttl = self._get_zodiac_cache_ttl(period)
            self.cache_service.set(cache_key, fortune_result, ttl_seconds=ttl)
            
            # 데이터베이스 저장
            await self._save_fortune_session(
                db, FortuneType.ZODIAC, fortune_result, user_data
            )
            
            logger.info(f"Zodiac fortune generated for {zodiac_sign.value} ({period})")
            return fortune_result
            
        except Exception as e:
            logger.error(f"Error generating zodiac fortune: {e}")
            raise
    
    async def get_oriental_fortune(self, db: Session, birth_data: Dict[str, Any],
                                  user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """사주 기반 운세 생성"""
        try:
            # 사주 운세 생성 (간단한 버전)
            fortune_result = self._generate_oriental_fortune(birth_data, user_data)
            
            # 데이터베이스 저장
            await self._save_fortune_session(
                db, FortuneType.ORIENTAL, fortune_result, user_data
            )
            
            logger.info(f"Oriental fortune generated for birth data: {birth_data.get('birth_date')}")
            return fortune_result
            
        except Exception as e:
            logger.error(f"Error generating oriental fortune: {e}")
            raise
    
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
    
    # Private methods
    def _get_daily_cache_key(self, user_data: Optional[Dict]) -> str:
        """일일 운세 캐시 키 생성"""
        today = datetime.now().date().isoformat()
        user_id = user_data.get("user_uuid", "anonymous") if user_data else "anonymous"
        return f"daily_fortune:{user_id}:{today}"
    
    def _get_zodiac_cache_key(self, zodiac_sign: ZodiacSign, period: str) -> str:
        """별자리 운세 캐시 키 생성"""
        today = datetime.now().date().isoformat()
        return f"zodiac_fortune:{zodiac_sign.value}:{period}:{today}"
    
    def _get_zodiac_cache_ttl(self, period: str) -> int:
        """별자리 운세 캐시 TTL 반환"""
        ttl_map = {
            "daily": 86400,    # 24시간
            "weekly": 604800,  # 7일
            "monthly": 2592000 # 30일
        }
        return ttl_map.get(period, 86400)
    
    def _generate_daily_fortune(self, user_data: Optional[Dict]) -> Dict[str, Any]:
        """일일 운세 생성"""
        today = datetime.now().date()
        
        # 기본 운세 점수 계산
        base_score = self.engine.calculate_base_fortune_score(user_data, "daily")
        overall_grade = self.engine.get_fortune_grade(base_score)
        
        # 카테고리별 운세
        categories = {}
        category_scores = {}
        
        for category in ["love", "money", "health", "work"]:
            cat_fortune = self.engine.generate_category_fortune(category, base_score, user_data)
            categories[category] = cat_fortune
            category_scores[category] = cat_fortune["score"]
        
        # 행운의 요소들
        lucky_elements = self.engine.generate_lucky_elements(user_data)
        
        # 조언과 주의사항
        advice, warnings = self.engine.generate_advice_and_warnings(overall_grade, category_scores)
        
        # 전체 운세 설명
        overall_descriptions = self.engine.fortune_templates.get(overall_grade, {}).get("overall", [])
        overall_description = random.choice(overall_descriptions) if overall_descriptions else "좋은 하루가 될 것 같아요."
        
        return {
            "fortune_id": str(uuid.uuid4()),
            "date": today.isoformat(),
            "fortune_type": "daily",
            "overall_fortune": {
                "score": base_score,
                "grade": overall_grade,
                "description": overall_description
            },
            "categories": categories,
            "lucky_items": lucky_elements["items"],
            "lucky_numbers": lucky_elements["numbers"],
            "lucky_colors": lucky_elements["colors"],
            "advice": advice,
            "warnings": warnings,
            "live2d_emotion": self._get_emotion_for_grade(overall_grade),
            "live2d_motion": "blessing"
        }
    
    def _select_tarot_cards(self, db: Session, count: int) -> List[TarotCardDB]:
        """타로 카드 선택"""
        return TarotCardDB.get_random_cards(db, count)
    
    def _generate_dummy_tarot_cards(self, count: int) -> List[Dict[str, Any]]:
        """더미 타로 카드 데이터 생성"""
        dummy_cards = [
            {
                "card_name": "The Fool",
                "card_name_ko": "바보",
                "suit": "major",
                "upright_meaning": "새로운 시작, 순수함, 모험",
                "general_interpretation": "새로운 여행이나 모험을 시작할 때입니다."
            },
            {
                "card_name": "The Lovers", 
                "card_name_ko": "연인",
                "suit": "major",
                "upright_meaning": "사랑, 선택, 조화",
                "general_interpretation": "중요한 선택의 순간이 다가오고 있습니다."
            },
            {
                "card_name": "The Star",
                "card_name_ko": "별",
                "suit": "major", 
                "upright_meaning": "희망, 영감, 치유",
                "general_interpretation": "희망적인 미래가 기다리고 있습니다."
            },
            {
                "card_name": "Wheel of Fortune",
                "card_name_ko": "운명의 수레바퀴",
                "suit": "major",
                "upright_meaning": "행운, 변화, 순환",
                "general_interpretation": "인생의 전환점이 다가오고 있습니다."
            },
            {
                "card_name": "The Sun",
                "card_name_ko": "태양",
                "suit": "major",
                "upright_meaning": "성공, 기쁨, 활력",
                "general_interpretation": "밝고 긍정적인 에너지가 가득합니다."
            }
        ]
        
        return random.sample(dummy_cards, min(count, len(dummy_cards)))
    
    def _generate_tarot_interpretation(self, cards: List[Any], question: str,
                                     question_type: QuestionType, 
                                     user_data: Optional[Dict]) -> Dict[str, Any]:
        """타로 해석 생성"""
        positions = ["past", "present", "future"]
        if len(cards) > 3:
            positions.extend([f"advice_{i}" for i in range(len(cards) - 3)])
        
        card_interpretations = []
        for i, card in enumerate(cards):
            position = positions[i] if i < len(positions) else f"card_{i+1}"
            
            if isinstance(card, dict):  # 더미 데이터
                interpretation = {
                    "position": position,
                    "card_name": card["card_name"],
                    "card_name_ko": card["card_name_ko"],
                    "card_meaning": card["upright_meaning"],
                    "interpretation": card["general_interpretation"],
                    "image_url": f"/static/tarot/{card['card_name'].lower().replace(' ', '_')}.jpg"
                }
            else:  # 실제 TarotCardDB 모델
                interpretation = {
                    "position": position,
                    "card_name": card.card_name,
                    "card_name_ko": card.card_name_ko,
                    "card_meaning": card.upright_meaning or "카드의 의미",
                    "interpretation": card.get_interpretation(question_type.value),
                    "image_url": card.image_url or f"/static/tarot/{card.card_name.lower().replace(' ', '_')}.jpg"
                }
            
            card_interpretations.append(interpretation)
        
        # 전체 해석 생성
        overall_interpretation = self._generate_overall_tarot_interpretation(
            card_interpretations, question, question_type
        )
        
        # 조언 생성
        advice = self._generate_tarot_advice(card_interpretations, question_type)
        
        return {
            "fortune_id": str(uuid.uuid4()),
            "fortune_type": "tarot",
            "question": question,
            "question_type": question_type.value,
            "cards": card_interpretations,
            "overall_interpretation": overall_interpretation,
            "advice": advice,
            "live2d_emotion": "mystical",
            "live2d_motion": "card_draw",
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_dummy_zodiac_info(self, zodiac_sign: ZodiacSign) -> Any:
        """더미 별자리 정보 생성"""
        zodiac_data = {
            ZodiacSign.ARIES: {
                "sign_ko": "양자리",
                "element": "fire",
                "ruling_planet": "화성",
                "personality_traits": ["열정적", "용감한", "리더십", "직선적"]
            },
            ZodiacSign.TAURUS: {
                "sign_ko": "황소자리", 
                "element": "earth",
                "ruling_planet": "금성",
                "personality_traits": ["안정적", "고집스러운", "실용적", "감각적"]
            },
            ZodiacSign.GEMINI: {
                "sign_ko": "쌍둥이자리",
                "element": "air", 
                "ruling_planet": "수성",
                "personality_traits": ["호기심많은", "사교적", "변화무쌍", "재치있는"]
            },
            ZodiacSign.CANCER: {
                "sign_ko": "게자리",
                "element": "water",
                "ruling_planet": "달",
                "personality_traits": ["감성적", "보호본능", "가정적", "직관적"]
            },
            ZodiacSign.LEO: {
                "sign_ko": "사자자리",
                "element": "fire", 
                "ruling_planet": "태양",
                "personality_traits": ["자신감", "관대함", "창조적", "드라마틱"]
            },
            ZodiacSign.VIRGO: {
                "sign_ko": "처녀자리",
                "element": "earth",
                "ruling_planet": "수성", 
                "personality_traits": ["완벽주의", "분석적", "실용적", "섬세함"]
            },
            ZodiacSign.LIBRA: {
                "sign_ko": "천칭자리",
                "element": "air",
                "ruling_planet": "금성",
                "personality_traits": ["균형감", "사교적", "예술적", "평화로운"]
            },
            ZodiacSign.SCORPIO: {
                "sign_ko": "전갈자리",
                "element": "water",
                "ruling_planet": "명왕성",
                "personality_traits": ["신비로운", "열정적", "집중력", "직관적"]
            },
            ZodiacSign.SAGITTARIUS: {
                "sign_ko": "사수자리",
                "element": "fire",
                "ruling_planet": "목성",
                "personality_traits": ["모험적", "낙천적", "철학적", "자유로운"]
            },
            ZodiacSign.CAPRICORN: {
                "sign_ko": "염소자리",
                "element": "earth",
                "ruling_planet": "토성",
                "personality_traits": ["책임감", "야심적", "실용적", "인내심"]
            },
            ZodiacSign.AQUARIUS: {
                "sign_ko": "물병자리",
                "element": "air",
                "ruling_planet": "천왕성",
                "personality_traits": ["독창적", "인도주의적", "독립적", "미래지향적"]
            },
            ZodiacSign.PISCES: {
                "sign_ko": "물고기자리",
                "element": "water", 
                "ruling_planet": "해왕성",
                "personality_traits": ["감성적", "직관적", "창의적", "공감능력"]
            }
        }
        
        # 더미 클래스 생성
        class DummyZodiacInfo:
            def __init__(self, sign: ZodiacSign, data: Dict):
                self.sign = sign.value
                self.sign_ko = data["sign_ko"]
                self.element = data["element"]
                self.ruling_planet = data["ruling_planet"]
                self.personality_traits_list = data["personality_traits"]
                self.lucky_colors_list = ["파란색", "금색"]
                self.lucky_numbers_list = [7, 14, 21]
                self.compatible_signs_list = ["cancer", "scorpio"]
        
        data = zodiac_data.get(zodiac_sign, zodiac_data[ZodiacSign.ARIES])
        return DummyZodiacInfo(zodiac_sign, data)
    
    def _generate_zodiac_fortune(self, zodiac_info: Any, period: str,
                               user_data: Optional[Dict]) -> Dict[str, Any]:
        """별자리 운세 생성"""
        today = datetime.now().date()
        
        # 기간별 날짜 범위 설정
        if period == "weekly":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            date_range = f"{start_date.isoformat()} ~ {end_date.isoformat()}"
        elif period == "monthly":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year+1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = today.replace(month=today.month+1, day=1) - timedelta(days=1)
            date_range = f"{start_date.isoformat()} ~ {end_date.isoformat()}"
        else:  # daily
            date_range = today.isoformat()
        
        # 별자리별 운세 점수 계산
        base_score = self.engine.calculate_base_fortune_score(user_data, "zodiac")
        
        # 카테고리별 운세
        fortune_categories = {}
        for category in ["love", "career", "health", "finance"]:
            cat_fortune = self.engine.generate_category_fortune(category, base_score, user_data)
            fortune_categories[category] = cat_fortune
        
        # 궁합 정보
        compatibility = {
            "best_match": zodiac_info.compatible_signs_list[:2] if hasattr(zodiac_info, 'compatible_signs_list') else ["cancer", "scorpio"],
            "good_match": ["taurus", "capricorn"],
            "challenging": ["gemini", "sagittarius"]
        }
        
        # 행운의 요소
        lucky_elements = {
            "color": zodiac_info.lucky_colors_list[0] if hasattr(zodiac_info, 'lucky_colors_list') and zodiac_info.lucky_colors_list else "파란색",
            "number": zodiac_info.lucky_numbers_list[0] if hasattr(zodiac_info, 'lucky_numbers_list') and zodiac_info.lucky_numbers_list else 7,
            "stone": self._get_lucky_stone_for_sign(zodiac_info.sign),
            "direction": self._get_lucky_direction_for_element(zodiac_info.element)
        }
        
        return {
            "fortune_id": str(uuid.uuid4()),
            "fortune_type": "zodiac",
            "zodiac_sign": zodiac_info.sign,
            "zodiac_sign_ko": zodiac_info.sign_ko,
            "period": period,
            "date_range": date_range,
            "personality_traits": zodiac_info.personality_traits_list,
            "fortune": fortune_categories,
            "compatibility": compatibility,
            "lucky_elements": lucky_elements,
            "live2d_emotion": "mystical",
            "live2d_motion": "crystal_gaze",
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_oriental_fortune(self, birth_data: Dict[str, Any],
                                 user_data: Optional[Dict]) -> Dict[str, Any]:
        """사주 기반 운세 생성 (간단한 버전)"""
        # 간단한 사주 운세 구현
        birth_date = birth_data.get("birth_date")
        birth_time = birth_data.get("birth_time", "12:00")
        
        # 기본 운세 점수
        base_score = self.engine.calculate_base_fortune_score(user_data, "oriental")
        
        # 오행 계산 (간단한 버전)
        elements = self._calculate_five_elements(birth_date, birth_time)
        
        # 카테고리별 운세
        categories = {}
        for category in ["love", "money", "health", "work"]:
            cat_fortune = self.engine.generate_category_fortune(category, base_score, user_data)
            categories[category] = cat_fortune
        
        # 사주 조언
        advice = self._generate_oriental_advice(elements, categories)
        
        return {
            "fortune_id": str(uuid.uuid4()),
            "fortune_type": "oriental",
            "birth_date": birth_date,
            "birth_time": birth_time,
            "five_elements": elements,
            "categories": categories,
            "advice": advice,
            "live2d_emotion": "mystical",
            "live2d_motion": "special_reading",
            "created_at": datetime.now().isoformat()
        }
    
    def _calculate_five_elements(self, birth_date: str, birth_time: str) -> Dict[str, Any]:
        """오행 계산 (간단한 버전)"""
        try:
            date_obj = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            date_obj = datetime.now()
        
        # 간단한 오행 계산 (실제로는 복잡한 사주 알고리즘 필요)
        elements = {
            "wood": random.randint(10, 30),
            "fire": random.randint(10, 30), 
            "earth": random.randint(10, 30),
            "metal": random.randint(10, 30),
            "water": random.randint(10, 30)
        }
        
        # 가장 강한 원소 찾기
        dominant_element = max(elements, key=elements.get)
        
        return {
            "elements": elements,
            "dominant": dominant_element,
            "description": self._get_element_description(dominant_element)
        }
    
    def _get_element_description(self, element: str) -> str:
        """오행 설명"""
        descriptions = {
            "wood": "목기운이 강한 당신은 성장과 발전의 에너지를 가지고 있습니다.",
            "fire": "화기운이 강한 당신은 열정과 활력이 넘치는 성격입니다.",
            "earth": "토기운이 강한 당신은 안정감과 포용력을 지니고 있습니다.",
            "metal": "금기운이 강한 당신은 정의감과 결단력이 뛰어납니다.",
            "water": "수기운이 강한 당신은 지혜롭고 유연한 성격을 가지고 있습니다."
        }
        return descriptions.get(element, "균형잡힌 기운을 가지고 있습니다.")
    
    def _generate_oriental_advice(self, elements: Dict[str, Any], 
                                categories: Dict[str, Any]) -> str:
        """사주 기반 조언 생성"""
        dominant = elements.get("dominant", "earth")
        
        advice_templates = {
            "wood": "성장과 발전을 위해 새로운 도전을 해보세요.",
            "fire": "열정을 잃지 말고 목표를 향해 나아가세요.",
            "earth": "안정감을 바탕으로 차근차근 진행하세요.",
            "metal": "정의로운 마음으로 올바른 선택을 하세요.", 
            "water": "유연한 사고로 변화에 적응하세요."
        }
        
        return advice_templates.get(dominant, "균형잡힌 마음으로 하루를 보내세요.")
    
    def _get_lucky_stone_for_sign(self, sign: str) -> str:
        """별자리별 행운의 돌"""
        stones = {
            "aries": "다이아몬드", "taurus": "에메랄드", "gemini": "진주",
            "cancer": "루비", "leo": "페리도트", "virgo": "사파이어",
            "libra": "오팔", "scorpio": "토파즈", "sagittarius": "터키석",
            "capricorn": "가넷", "aquarius": "자수정", "pisces": "아쿠아마린"
        }
        return stones.get(sign, "수정")
    
    def _get_lucky_direction_for_element(self, element: str) -> str:
        """원소별 행운의 방향"""
        directions = {
            "fire": "남쪽", "earth": "중앙", "metal": "서쪽",
            "water": "북쪽", "air": "동쪽"
        }
        return directions.get(element, "동쪽")
    
    def _get_emotion_for_grade(self, grade: str) -> str:
        """운세 등급에 따른 Live2D 감정"""
        emotion_map = {
            "excellent": "joy",
            "good": "comfort", 
            "normal": "neutral",
            "caution": "concern"
        }
        return emotion_map.get(grade, "neutral")
    
    def _generate_overall_tarot_interpretation(self, cards: List[Dict], 
                                             question: str, 
                                             question_type: QuestionType) -> str:
        """전체 타로 해석 생성"""
        if len(cards) >= 3:
            return f"과거의 {cards[0]['card_name_ko']}가 현재의 {cards[1]['card_name_ko']}로 이어지며, 미래에는 {cards[2]['card_name_ko']}의 기운이 기다리고 있습니다. 전체적으로 긍정적인 흐름이 보이니 마음을 열고 기대해보세요."
        else:
            return "카드들이 전하는 메시지를 종합해보면, 현재 상황을 잘 이해하고 앞으로 나아가라는 조언을 주고 있습니다."
    
    def _generate_tarot_advice(self, cards: List[Dict], 
                             question_type: QuestionType) -> str:
        """타로 조언 생성"""
        advice_templates = {
            QuestionType.LOVE: "마음을 열고 진정한 감정을 표현해보세요.",
            QuestionType.MONEY: "신중한 계획과 함께 새로운 기회를 찾아보세요.",
            QuestionType.HEALTH: "몸과 마음의 균형을 맞추는데 집중하세요.",
            QuestionType.WORK: "창의적인 아이디어와 끈기로 목표를 달성하세요.",
            QuestionType.GENERAL: "직감을 믿고 긍정적인 마음으로 나아가세요."
        }
        
        return advice_templates.get(question_type, "카드가 전하는 메시지를 마음에 새기고 행동하세요.")
    
    async def _save_fortune_session(self, db: Session, fortune_type: FortuneType,
                                   result: Dict[str, Any], user_data: Optional[Dict],
                                   question: Optional[str] = None,
                                   question_type: Optional[QuestionType] = None):
        """운세 세션 저장"""
        try:
            fortune_session = FortuneSession(
                fortune_id=result["fortune_id"],
                session_id=user_data.get("session_id") if user_data else None,
                user_uuid=user_data.get("user_uuid") if user_data else None,
                fortune_type=fortune_type.value,
                question=question,
                question_type=question_type.value if question_type else None,
                result=json.dumps(result, ensure_ascii=False)
            )
            
            # 캐시 TTL 설정
            if fortune_type == FortuneType.DAILY:
                fortune_session.set_cache_ttl(24)
            elif fortune_type == FortuneType.ZODIAC:
                fortune_session.set_cache_ttl(24)
            else:
                fortune_session.set_cache_ttl(1)  # 타로, 사주는 1시간
            
            db.add(fortune_session)
            db.commit()
            
            logger.info(f"Fortune session saved: {fortune_session.fortune_id}")
            
        except Exception as e:
            logger.error(f"Error saving fortune session: {e}")
            db.rollback()
            # 저장 실패해도 서비스는 계속 동작
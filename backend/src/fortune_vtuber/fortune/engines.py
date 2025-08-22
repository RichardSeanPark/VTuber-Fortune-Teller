"""
운세 엔진 시스템 - 4가지 운세 타입을 지원하는 핵심 엔진
"""

import random
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
import calendar

from ..models.fortune import (
    FortuneResult, FortuneCategory, TarotCard, ZodiacSign,
    SajuElement, FortuneType, LuckyElement
)

# Define FortuneType for engines (compatible with models)
class EngineFortuneType(Enum):
    """Engine-specific Fortune Type Enum"""
    DAILY = "daily"
    TAROT = "tarot"
    ZODIAC = "zodiac"
    SAJU = "oriental"  # Maps to ORIENTAL in models
    ORIENTAL = "oriental"


class FortuneGrade(Enum):
    """운세 등급"""
    EXCELLENT = "excellent"  # 90-100점
    GOOD = "good"           # 70-89점
    NORMAL = "normal"       # 50-69점
    BAD = "bad"            # 30-49점
    WARNING = "warning"     # 0-29점


@dataclass
class PersonalizationContext:
    """개인화 컨텍스트"""
    birth_date: Optional[date] = None
    birth_time: Optional[str] = None
    zodiac_sign: Optional[ZodiacSign] = None
    preferences: Dict[str, Any] = field(default_factory=dict)
    recent_fortunes: List[Dict] = field(default_factory=list)


class FortuneEngineBase(ABC):
    """운세 엔진 베이스 클래스"""
    
    def __init__(self):
        self.fortune_type = None
        self.cache_duration = 86400  # 24시간
        
    @abstractmethod
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """운세 생성 추상 메서드"""
        pass
    
    def _generate_cache_key(
        self, 
        context: PersonalizationContext, 
        date_target: date,
        additional_params: Dict = None
    ) -> str:
        """캐시 키 생성"""
        key_data = {
            "type": self.fortune_type.value if self.fortune_type else "",
            "date": date_target.isoformat() if date_target else "",
            "birth_date": context.birth_date.isoformat() if context.birth_date else "",
            "zodiac": context.zodiac_sign.value if context.zodiac_sign else "",
            "params": additional_params or {}
        }
        key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _calculate_score(self, base_score: int, modifiers: List[int]) -> int:
        """점수 계산 with modifiers"""
        score = base_score + sum(modifiers)
        return max(0, min(100, score))
    
    def _get_grade_from_score(self, score: int) -> FortuneGrade:
        """점수에서 등급 변환"""
        if score >= 90:
            return FortuneGrade.EXCELLENT
        elif score >= 70:
            return FortuneGrade.GOOD
        elif score >= 50:
            return FortuneGrade.NORMAL
        elif score >= 30:
            return FortuneGrade.BAD
        else:
            return FortuneGrade.WARNING
    
    def _personalized_random(self, context: PersonalizationContext, seed_extra: str = "") -> random.Random:
        """개인화된 랜덤 생성기"""
        seed_string = ""
        if context.birth_date:
            seed_string += context.birth_date.isoformat()
        if context.zodiac_sign:
            seed_string += context.zodiac_sign.value
        seed_string += seed_extra
        
        # 오늘 날짜로 시드 변경 (일일 변화)
        today = datetime.now().date().isoformat()
        seed_string += today
        
        seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
        return random.Random(seed)


class DailyFortuneEngine(FortuneEngineBase):
    """일일 운세 엔진"""
    
    def __init__(self):
        super().__init__()
        self.fortune_type = FortuneType.DAILY
        
        # 일일 운세 메시지 템플릿
        self.daily_messages = {
            FortuneGrade.EXCELLENT: [
                "오늘은 모든 일이 순조롭게 흘러갈 거예요! ✨",
                "행운의 여신이 당신을 미소 짓고 있어요! 🍀",
                "완벽한 하루가 될 것 같아요! 💫",
                "오늘은 당신의 매력이 최고조에 달할 날이에요! 🌟"
            ],
            FortuneGrade.GOOD: [
                "전반적으로 좋은 하루가 될 것 같아요! 😊",
                "긍정적인 에너지가 느껴져요! 🌈",
                "오늘은 기분 좋은 일들이 기다리고 있어요! 🎉",
                "좋은 소식이 들려올 것 같아요! 📧"
            ],
            FortuneGrade.NORMAL: [
                "평온하고 안정적인 하루가 될 거예요! 😌",
                "차분하게 하루를 보내시는 게 좋겠어요! ☕",
                "무난한 하루, 작은 행복을 찾아보세요! 🌸",
                "오늘은 휴식이 필요한 날이에요! 🛋️"
            ],
            FortuneGrade.BAD: [
                "조금 조심스러운 하루가 될 것 같아요! ⚠️",
                "신중하게 행동하시는 게 좋겠어요! 🤔",
                "작은 어려움이 있을 수 있어요! 💪",
                "인내심이 필요한 하루예요! 🌱"
            ],
            FortuneGrade.WARNING: [
                "오늘은 특히 주의가 필요한 날이에요! 🚨",
                "중요한 결정은 미루는 게 좋겠어요! ⏰",
                "안전을 최우선으로 생각하세요! 🛡️",
                "조심스럽게 하루를 보내세요! 🙏"
            ]
        }
        
        self.category_advice = {
            "love": {
                FortuneGrade.EXCELLENT: ["새로운 만남의 기회가!", "연인과의 달콤한 시간!", "사랑이 꽃필 예감!"],
                FortuneGrade.GOOD: ["따뜻한 감정이 통해요", "소중한 사람과 시간을", "마음이 통하는 순간"],
                FortuneGrade.NORMAL: ["평온한 관계 유지", "서로를 이해하는 시간", "차분한 대화가 필요"],
                FortuneGrade.BAD: ["오해가 생길 수 있어요", "감정 조절이 필요해요", "신중한 대화를"],
                FortuneGrade.WARNING: ["갈등 조심하세요", "말실수 주의", "거리를 두는 게 나을 듯"]
            },
            "money": {
                FortuneGrade.EXCELLENT: ["재정적 기회 포착!", "투자 운이 좋아요!", "수입 증가 가능성!"],
                FortuneGrade.GOOD: ["안정적인 재정 관리", "작은 수익이 기대", "절약 효과 나타남"],
                FortuneGrade.NORMAL: ["현상 유지", "신중한 지출 관리", "계획적인 소비"],
                FortuneGrade.BAD: ["지출 줄이세요", "투자 신중히", "절약이 필요"],
                FortuneGrade.WARNING: ["큰 지출 금물", "투자 위험", "재정 점검 필요"]
            },
            "health": {
                FortuneGrade.EXCELLENT: ["컨디션 최고!", "활력 넘치는 하루!", "건강한 에너지!"],
                FortuneGrade.GOOD: ["전반적으로 양호", "가벼운 운동 추천", "규칙적인 생활"],
                FortuneGrade.NORMAL: ["적당한 휴식", "무리하지 마세요", "균형 잡힌 식단"],
                FortuneGrade.BAD: ["피로 주의", "충분한 수면을", "스트레스 관리"],
                FortuneGrade.WARNING: ["건강 체크 필요", "무리 절대 금물", "병원 상담 고려"]
            },
            "work": {
                FortuneGrade.EXCELLENT: ["업무 성과 기대!", "승진 기회!", "인정받는 날!"],
                FortuneGrade.GOOD: ["순조로운 업무", "동료와 협력", "좋은 아이디어"],
                FortuneGrade.NORMAL: ["꾸준한 노력", "차근차근 진행", "안정적인 업무"],
                FortuneGrade.BAD: ["실수 주의", "신중한 결정", "여유 갖고 진행"],
                FortuneGrade.WARNING: ["중요 업무 미루기", "신중한 검토", "도움 요청하기"]
            }
        }
    
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """일일 운세 생성"""
        if date_target is None:
            date_target = datetime.now().date()
            
        rng = self._personalized_random(context, "daily")
        
        # 기본 점수 생성 (개인화 고려)
        base_scores = {
            "overall": rng.randint(20, 95),
            "love": rng.randint(20, 95),
            "money": rng.randint(20, 95),
            "health": rng.randint(20, 95),
            "work": rng.randint(20, 95)
        }
        
        # 별자리별 보너스 적용
        if context.zodiac_sign:
            modifiers = self._get_zodiac_modifiers(context.zodiac_sign, date_target, rng)
            for category in base_scores:
                base_scores[category] = self._calculate_score(base_scores[category], [modifiers.get(category, 0)])
        
        # 카테고리별 운세 생성
        categories = {}
        for category, score in base_scores.items():
            if category == "overall":
                continue
                
            grade = self._get_grade_from_score(score)
            advice_list = self.category_advice[category][grade]
            advice = rng.choice(advice_list)
            
            categories[category] = FortuneCategory(
                score=score,
                grade=grade.value,
                description=advice
            )
        
        # 전체 운세
        overall_grade = self._get_grade_from_score(base_scores["overall"])
        overall_description = rng.choice(self.daily_messages[overall_grade])
        
        # 행운 요소 생성
        lucky_elements = self._generate_lucky_elements(context, date_target, rng)
        
        # 조언 생성
        advice = self._generate_daily_advice(overall_grade, context, rng)
        warnings = self._generate_warnings(overall_grade, categories, rng)
        
        return FortuneResult(
            fortune_type=FortuneType.DAILY,
            date=date_target,
            overall_fortune=FortuneCategory(
                score=base_scores["overall"],
                grade=overall_grade.value,
                description=overall_description
            ),
            categories=categories,
            lucky_elements=lucky_elements,
            advice=advice,
            warnings=warnings,
            live2d_emotion=self._get_emotion_from_grade(overall_grade),
            live2d_motion="crystal_gaze"
        )
    
    def _get_zodiac_modifiers(self, zodiac: ZodiacSign, date_target: date, rng: random.Random) -> Dict[str, int]:
        """별자리별 운세 보정값"""
        # 별자리별 특성 반영
        zodiac_traits = {
            ZodiacSign.ARIES: {"love": 5, "work": 10, "health": 5, "money": 0},
            ZodiacSign.TAURUS: {"money": 10, "health": 5, "love": 5, "work": 0},
            ZodiacSign.GEMINI: {"work": 5, "love": 5, "health": 0, "money": 5},
            ZodiacSign.CANCER: {"love": 10, "health": 5, "work": 0, "money": 5},
            ZodiacSign.LEO: {"love": 5, "work": 10, "health": 5, "money": 0},
            ZodiacSign.VIRGO: {"work": 10, "health": 10, "love": 0, "money": 5},
            ZodiacSign.LIBRA: {"love": 10, "work": 5, "health": 0, "money": 5},
            ZodiacSign.SCORPIO: {"love": 5, "money": 10, "work": 5, "health": 0},
            ZodiacSign.SAGITTARIUS: {"work": 5, "health": 10, "love": 5, "money": 0},
            ZodiacSign.CAPRICORN: {"money": 10, "work": 10, "love": 0, "health": 5},
            ZodiacSign.AQUARIUS: {"work": 5, "love": 5, "health": 5, "money": 5},
            ZodiacSign.PISCES: {"love": 10, "health": 5, "work": 0, "money": 5}
        }
        
        base_modifiers = zodiac_traits.get(zodiac, {})
        
        # 랜덤 변동 추가 (-5 ~ +5)
        random_modifiers = {}
        for category in ["love", "money", "health", "work"]:
            base_mod = base_modifiers.get(category, 0)
            random_mod = rng.randint(-5, 5)
            random_modifiers[category] = base_mod + random_mod
            
        return random_modifiers
    
    def _generate_lucky_elements(self, context: PersonalizationContext, date_target: date, rng: random.Random) -> LuckyElement:
        """행운 요소 생성"""
        colors = ["빨간색", "파란색", "노란색", "초록색", "보라색", "분홍색", "흰색", "검은색", "주황색", "하늘색"]
        numbers = list(range(1, 101))
        items = [
            "볼펜", "노트", "커피", "차", "꽃", "향초", "쿠키", "사탕", "열쇠고리", "목걸이",
            "팔찌", "반지", "책", "음악", "사진", "거울", "지갑", "시계", "모자", "스카프"
        ]
        
        return LuckyElement(
            colors=rng.sample(colors, 2),
            numbers=rng.sample(numbers, 3),
            items=rng.sample(items, 2)
        )
    
    def _generate_daily_advice(self, grade: FortuneGrade, context: PersonalizationContext, rng: random.Random) -> str:
        """일일 조언 생성"""
        advice_templates = {
            FortuneGrade.EXCELLENT: [
                "오늘은 새로운 도전을 해보세요!",
                "적극적으로 기회를 잡아보세요!",
                "자신감을 가지고 행동하세요!",
                "주변 사람들과 기쁨을 나누세요!"
            ],
            FortuneGrade.GOOD: [
                "긍정적인 마음가짐을 유지하세요!",
                "주변 사람들에게 관심을 가져보세요!",
                "작은 행복을 찾아보세요!",
                "꾸준한 노력이 빛을 발할 거예요!"
            ],
            FortuneGrade.NORMAL: [
                "평온한 마음으로 하루를 보내세요!",
                "무리하지 말고 자신의 페이스를 유지하세요!",
                "가족이나 친구와 시간을 보내보세요!",
                "독서나 취미 활동을 즐겨보세요!"
            ],
            FortuneGrade.BAD: [
                "신중하게 생각하고 행동하세요!",
                "무리한 일정은 피하는 게 좋겠어요!",
                "충분한 휴식을 취하세요!",
                "주변 사람들의 조언을 들어보세요!"
            ],
            FortuneGrade.WARNING: [
                "중요한 결정은 미루세요!",
                "안전을 최우선으로 생각하세요!",
                "혼자서 해결하려 하지 말고 도움을 요청하세요!",
                "충분한 수면과 휴식이 필요해요!"
            ]
        }
        
        return rng.choice(advice_templates[grade])
    
    def _generate_warnings(self, grade: FortuneGrade, categories: Dict, rng: random.Random) -> List[str]:
        """경고 메시지 생성"""
        warnings = []
        
        if grade in [FortuneGrade.BAD, FortuneGrade.WARNING]:
            general_warnings = [
                "급한 결정은 피하세요",
                "감정적인 판단을 조심하세요",
                "건강 관리에 신경 쓰세요"
            ]
            warnings.extend(rng.sample(general_warnings, min(2, len(general_warnings))))
        
        # 카테고리별 낮은 점수 경고
        for category_name, category_data in categories.items():
            if category_data.score < 40:
                category_warnings = {
                    "love": "인간관계에서 오해가 생길 수 있어요",
                    "money": "금전 관리를 신중히 하세요",
                    "health": "컨디션 관리가 필요해요",
                    "work": "업무상 실수를 조심하세요"
                }
                if category_name in category_warnings:
                    warnings.append(category_warnings[category_name])
        
        return warnings[:3]  # 최대 3개
    
    def _get_emotion_from_grade(self, grade: FortuneGrade) -> str:
        """등급에서 감정 매핑"""
        emotion_map = {
            FortuneGrade.EXCELLENT: "joy",
            FortuneGrade.GOOD: "comfort",
            FortuneGrade.NORMAL: "neutral",
            FortuneGrade.BAD: "concern",
            FortuneGrade.WARNING: "mystical"
        }
        return emotion_map.get(grade, "neutral")


class TarotFortuneEngine(FortuneEngineBase):
    """타로 운세 엔진"""
    
    def __init__(self):
        super().__init__()
        self.fortune_type = FortuneType.TAROT
        
        # 타로 카드 데이터 (22장 메이저 아르카나)
        self.tarot_cards = [
            {"name": "The Fool", "meaning": "새로운 시작", "keywords": ["순수", "모험", "자유"]},
            {"name": "The Magician", "meaning": "의지와 창조", "keywords": ["창조", "의지", "능력"]},
            {"name": "The High Priestess", "meaning": "직감과 신비", "keywords": ["직감", "신비", "내면"]},
            {"name": "The Empress", "meaning": "풍요와 모성", "keywords": ["풍요", "창조", "모성"]},
            {"name": "The Emperor", "meaning": "권위와 안정", "keywords": ["권위", "안정", "질서"]},
            {"name": "The Hierophant", "meaning": "전통과 지혜", "keywords": ["전통", "지혜", "학습"]},
            {"name": "The Lovers", "meaning": "사랑과 선택", "keywords": ["사랑", "선택", "조화"]},
            {"name": "The Chariot", "meaning": "의지와 승리", "keywords": ["의지", "승리", "방향"]},
            {"name": "Strength", "meaning": "용기와 인내", "keywords": ["용기", "인내", "자제"]},
            {"name": "The Hermit", "meaning": "성찰과 지혜", "keywords": ["성찰", "지혜", "고독"]},
            {"name": "Wheel of Fortune", "meaning": "운명과 변화", "keywords": ["운명", "변화", "순환"]},
            {"name": "Justice", "meaning": "정의와 균형", "keywords": ["정의", "균형", "진실"]},
            {"name": "The Hanged Man", "meaning": "희생과 관점", "keywords": ["희생", "관점", "기다림"]},
            {"name": "Death", "meaning": "변화와 재생", "keywords": ["변화", "재생", "끝과시작"]},
            {"name": "Temperance", "meaning": "절제와 조화", "keywords": ["절제", "조화", "균형"]},
            {"name": "The Devil", "meaning": "유혹과 속박", "keywords": ["유혹", "속박", "물질"]},
            {"name": "The Tower", "meaning": "파괴와 해방", "keywords": ["파괴", "해방", "깨달음"]},
            {"name": "The Star", "meaning": "희망과 영감", "keywords": ["희망", "영감", "치유"]},
            {"name": "The Moon", "meaning": "환상과 무의식", "keywords": ["환상", "무의식", "혼란"]},
            {"name": "The Sun", "meaning": "성공과 기쁨", "keywords": ["성공", "기쁨", "활력"]},
            {"name": "Judgement", "meaning": "심판과 부활", "keywords": ["심판", "부활", "깨달음"]},
            {"name": "The World", "meaning": "완성과 성취", "keywords": ["완성", "성취", "통합"]}
        ]
        
        # 질문 타입별 해석 스타일
        self.question_styles = {
            "love": "감정과 관계의 관점에서",
            "money": "재정과 물질적 측면에서", 
            "health": "건강과 생명력의 관점에서",
            "work": "직업과 성취의 측면에서",
            "general": "전반적인 삶의 관점에서"
        }
    
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """타로 운세 생성 (3장 스프레드)"""
        if date_target is None:
            date_target = datetime.now().date()
            
        question = additional_params.get("question", "") if additional_params else ""
        question_type = additional_params.get("question_type", "general") if additional_params else "general"
        
        rng = self._personalized_random(context, f"tarot_{question}")
        
        # 3장 타로 카드 뽑기 (과거, 현재, 미래)
        selected_cards = rng.sample(self.tarot_cards, 3)
        positions = ["past", "present", "future"]
        
        tarot_cards = []
        for i, (card_data, position) in enumerate(zip(selected_cards, positions)):
            # 정역 여부 결정
            is_reversed = rng.choice([True, False])
            
            # 해석 생성
            interpretation = self._generate_card_interpretation(
                card_data, position, question_type, is_reversed, rng
            )
            
            tarot_card = TarotCard(
                position=position,
                card_name=card_data["name"],
                card_meaning=card_data["meaning"],
                interpretation=interpretation,
                is_reversed=is_reversed,
                keywords=card_data["keywords"],
                image_url=f"/static/tarot/{card_data['name'].lower().replace(' ', '_')}.jpg"
            )
            tarot_cards.append(tarot_card)
        
        # 전체 해석 생성
        overall_interpretation = self._generate_overall_interpretation(
            tarot_cards, question, question_type, rng
        )
        
        # 조언 생성
        advice = self._generate_tarot_advice(tarot_cards, question_type, rng)
        
        # 카테고리별 점수 (타로는 단일 카테고리)
        overall_score = self._calculate_tarot_score(tarot_cards, rng)
        overall_grade = self._get_grade_from_score(overall_score)
        
        return FortuneResult(
            fortune_type=FortuneType.TAROT,
            date=date_target,
            overall_fortune=FortuneCategory(
                score=overall_score,
                grade=overall_grade.value,
                description=overall_interpretation
            ),
            categories={},  # 타로는 카테고리별 분석 없음
            tarot_cards=tarot_cards,
            advice=advice,
            question=question,
            question_type=question_type,
            live2d_emotion="mystical",
            live2d_motion="card_draw"
        )
    
    def _generate_card_interpretation(
        self, 
        card_data: Dict, 
        position: str, 
        question_type: str, 
        is_reversed: bool,
        rng: random.Random
    ) -> str:
        """개별 카드 해석 생성"""
        position_meanings = {
            "past": "과거의 영향",
            "present": "현재 상황", 
            "future": "앞으로의 전망"
        }
        
        base_meaning = card_data["meaning"]
        keywords = card_data["keywords"]
        
        # 정역 여부에 따른 해석 조정
        if is_reversed:
            reversed_interpretations = {
                "새로운 시작": "준비 부족이나 성급함",
                "의지와 창조": "능력 부족이나 방향성 혼란",
                "직감과 신비": "직감을 무시하거나 혼란",
                "풍요와 모성": "과도한 보호나 의존",
                "권위와 안정": "독단적이거나 경직됨",
                "사랑과 선택": "갈등이나 잘못된 선택",
                "희망과 영감": "실망이나 좌절감"
            }
            meaning = reversed_interpretations.get(base_meaning, f"{base_meaning}의 부정적 측면")
        else:
            meaning = base_meaning
        
        # 질문 타입별 해석 스타일 적용
        style = self.question_styles[question_type]
        
        interpretations = [
            f"{position_meanings[position]}을 나타내는 이 카드는 {style} {meaning}을 의미해요.",
            f"{position}의 {meaning}이 {style} 중요한 메시지를 전달하고 있어요.",
            f"{style} {meaning}의 에너지가 {position_meanings[position]}에 영향을 주고 있어요."
        ]
        
        return rng.choice(interpretations)
    
    def _generate_overall_interpretation(
        self, 
        cards: List[TarotCard], 
        question: str, 
        question_type: str,
        rng: random.Random
    ) -> str:
        """전체 해석 생성"""
        # 카드들의 전반적인 에너지 분석
        positive_cards = sum(1 for card in cards if not card.is_reversed)
        negative_cards = len(cards) - positive_cards
        
        if positive_cards >= 2:
            energy = "긍정적인"
            message = "희망적인 전망이 보여요"
        elif negative_cards >= 2:
            energy = "도전적인"
            message = "신중함이 필요한 시기에요"
        else:
            energy = "균형잡힌"
            message = "변화와 기회가 함께 있어요"
        
        # 스토리 연결
        story_templates = [
            f"카드들이 보여주는 {energy} 흐름을 보면, {message}. 과거의 경험이 현재에 영향을 주고 있으며, 미래에는 새로운 가능성이 열릴 것 같아요.",
            f"{energy} 에너지가 흐르고 있어요. {message}. 지금까지의 여정이 앞으로의 방향을 제시하고 있어요.",
            f"전체적으로 {energy} 메시지가 담겨있어요. {message}. 과거와 현재를 바탕으로 미래를 준비하는 시기인 것 같아요."
        ]
        
        return rng.choice(story_templates)
    
    def _generate_tarot_advice(self, cards: List[TarotCard], question_type: str, rng: random.Random) -> str:
        """타로 조언 생성"""
        # 미래 카드 기반 조언
        future_card = cards[2]  # 미래 위치 카드
        
        advice_templates = {
            "love": [
                "마음을 열고 진실한 감정을 표현해보세요",
                "상대방의 입장을 이해하려 노력해보세요", 
                "자신을 사랑하는 것부터 시작하세요",
                "인내심을 갖고 관계를 발전시켜나가세요"
            ],
            "money": [
                "계획적인 재정 관리가 필요해요",
                "새로운 수입원을 찾아보세요",
                "투자보다는 저축에 집중하세요",
                "금전적 결정을 신중히 내리세요"
            ],
            "health": [
                "몸과 마음의 균형을 맞추세요",
                "충분한 휴식과 수면이 필요해요",
                "규칙적인 생활 습관을 만들어보세요",
                "스트레스 해소법을 찾아보세요"
            ],
            "work": [
                "자신의 능력을 믿고 도전해보세요",
                "동료들과의 협력이 중요해요",
                "꾸준한 노력이 결실을 맺을 거예요",
                "새로운 기술이나 지식을 배워보세요"
            ],
            "general": [
                "변화를 두려워하지 마세요",
                "직감을 믿고 따라가보세요",
                "주변 사람들의 조언에 귀기울여보세요",
                "긍정적인 마음가짐을 유지하세요"
            ]
        }
        
        return rng.choice(advice_templates[question_type])
    
    def _calculate_tarot_score(self, cards: List[TarotCard], rng: random.Random) -> int:
        """타로 점수 계산"""
        # 정방향 카드는 긍정적, 역방향은 부정적
        positive_count = sum(1 for card in cards if not card.is_reversed)
        
        # 기본 점수
        base_scores = {
            3: 85,  # 모두 정방향
            2: 70,  # 2장 정방향
            1: 55,  # 1장 정방향
            0: 35   # 모두 역방향
        }
        
        base_score = base_scores[positive_count]
        
        # 랜덤 변동 추가
        variation = rng.randint(-10, 10)
        
        return self._calculate_score(base_score, [variation])


class ZodiacFortuneEngine(FortuneEngineBase):
    """별자리 운세 엔진"""
    
    def __init__(self):
        super().__init__()
        self.fortune_type = FortuneType.ZODIAC
        
        # 별자리별 성격 특성
        self.zodiac_traits = {
            ZodiacSign.ARIES: {
                "personality": ["열정적", "도전적", "리더십", "직진성"],
                "lucky_stone": "다이아몬드",
                "lucky_direction": "동쪽",
                "element": "불"
            },
            ZodiacSign.TAURUS: {
                "personality": ["안정적", "현실적", "끈기", "미적감각"],
                "lucky_stone": "에메랄드", 
                "lucky_direction": "북동쪽",
                "element": "흙"
            },
            ZodiacSign.GEMINI: {
                "personality": ["다재다능", "호기심", "소통능력", "변화추구"],
                "lucky_stone": "아가사",
                "lucky_direction": "서쪽",
                "element": "바람"
            },
            ZodiacSign.CANCER: {
                "personality": ["감성적", "직관적", "보호본능", "가족중심"],
                "lucky_stone": "진주",
                "lucky_direction": "남서쪽", 
                "element": "물"
            },
            ZodiacSign.LEO: {
                "personality": ["카리스마", "창조적", "관대함", "자신감"],
                "lucky_stone": "루비",
                "lucky_direction": "남쪽",
                "element": "불"
            },
            ZodiacSign.VIRGO: {
                "personality": ["완벽주의", "분석적", "실용적", "봉사정신"],
                "lucky_stone": "사파이어",
                "lucky_direction": "남동쪽",
                "element": "흙"
            },
            ZodiacSign.LIBRA: {
                "personality": ["균형감각", "사교적", "미적감각", "평화주의"],
                "lucky_stone": "오팔",
                "lucky_direction": "서쪽",
                "element": "바람"
            },
            ZodiacSign.SCORPIO: {
                "personality": ["신비로움", "집중력", "직감", "변화력"],
                "lucky_stone": "토파즈",
                "lucky_direction": "북쪽",
                "element": "물"
            },
            ZodiacSign.SAGITTARIUS: {
                "personality": ["자유로움", "모험심", "철학적", "낙천적"],
                "lucky_stone": "터키석",
                "lucky_direction": "남서쪽",
                "element": "불"
            },
            ZodiacSign.CAPRICORN: {
                "personality": ["책임감", "야심", "인내심", "현실적"],
                "lucky_stone": "가넷",
                "lucky_direction": "북동쪽",
                "element": "흙"
            },
            ZodiacSign.AQUARIUS: {
                "personality": ["독창적", "인도주의", "미래지향", "자유로움"],
                "lucky_stone": "자수정",
                "lucky_direction": "남쪽",
                "element": "바람"
            },
            ZodiacSign.PISCES: {
                "personality": ["감성적", "직관적", "창의적", "공감능력"],
                "lucky_stone": "아쿠아마린",
                "lucky_direction": "서쪽",
                "element": "물"
            }
        }
        
        # 별자리 호환성
        self.compatibility = {
            ZodiacSign.ARIES: {
                "best": [ZodiacSign.LEO, ZodiacSign.SAGITTARIUS],
                "good": [ZodiacSign.GEMINI, ZodiacSign.AQUARIUS],
                "challenging": [ZodiacSign.CANCER, ZodiacSign.CAPRICORN]
            },
            ZodiacSign.TAURUS: {
                "best": [ZodiacSign.VIRGO, ZodiacSign.CAPRICORN],
                "good": [ZodiacSign.CANCER, ZodiacSign.PISCES],
                "challenging": [ZodiacSign.LEO, ZodiacSign.AQUARIUS]
            },
            # ... (다른 별자리들도 동일하게 정의)
        }
    
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """별자리 운세 생성"""
        if date_target is None:
            date_target = datetime.now().date()
            
        if not context.zodiac_sign:
            raise ValueError("별자리 정보가 필요합니다")
            
        period = additional_params.get("period", "daily") if additional_params else "daily"
        
        rng = self._personalized_random(context, f"zodiac_{period}")
        
        # 별자리 특성 가져오기
        traits = self.zodiac_traits[context.zodiac_sign]
        
        # 운세 점수 생성 (별자리 특성 반영)
        base_scores = self._generate_zodiac_scores(context.zodiac_sign, date_target, period, rng)
        
        # 카테고리별 운세 생성
        categories = {}
        for category, score in base_scores.items():
            if category == "overall":
                continue
                
            grade = self._get_grade_from_score(score)
            description = self._generate_zodiac_category_description(
                context.zodiac_sign, category, grade, rng
            )
            
            categories[category] = FortuneCategory(
                score=score,
                grade=grade.value,
                description=description
            )
        
        # 전체 운세
        overall_grade = self._get_grade_from_score(base_scores["overall"])
        overall_description = self._generate_zodiac_overall_description(
            context.zodiac_sign, overall_grade, period, rng
        )
        
        # 호환성 정보
        compatibility = self._get_compatibility_info(context.zodiac_sign)
        
        # 행운 요소 (별자리 특성 반영)
        lucky_elements = LuckyElement(
            colors=[self._get_zodiac_color(context.zodiac_sign)],
            numbers=[self._get_zodiac_number(context.zodiac_sign, rng)],
            items=[traits["lucky_stone"]]
        )
        
        # 조언 생성
        advice = self._generate_zodiac_advice(context.zodiac_sign, overall_grade, rng)
        
        return FortuneResult(
            fortune_type=FortuneType.ZODIAC,
            date=date_target,
            overall_fortune=FortuneCategory(
                score=base_scores["overall"],
                grade=overall_grade.value,
                description=overall_description
            ),
            categories=categories,
            zodiac_info={
                "sign": context.zodiac_sign.value,
                "personality_traits": traits["personality"],
                "element": traits["element"],
                "lucky_stone": traits["lucky_stone"],
                "lucky_direction": traits["lucky_direction"],
                "compatibility": compatibility
            },
            lucky_elements=lucky_elements,
            advice=advice,
            live2d_emotion=self._get_emotion_from_grade(overall_grade),
            live2d_motion="blessing"
        )
    
    def _generate_zodiac_scores(self, zodiac: ZodiacSign, date_target: date, period: str, rng: random.Random) -> Dict[str, int]:
        """별자리별 점수 생성"""
        # 별자리별 기본 성향 반영
        trait_modifiers = {
            ZodiacSign.ARIES: {"love": 5, "work": 10, "health": 5, "money": 0},
            ZodiacSign.TAURUS: {"money": 10, "health": 5, "love": 5, "work": 0},
            ZodiacSign.GEMINI: {"work": 5, "love": 5, "health": 0, "money": 5},
            ZodiacSign.CANCER: {"love": 10, "health": 5, "work": 0, "money": 5},
            ZodiacSign.LEO: {"love": 5, "work": 10, "health": 5, "money": 0},
            ZodiacSign.VIRGO: {"work": 10, "health": 10, "love": 0, "money": 5},
            ZodiacSign.LIBRA: {"love": 10, "work": 5, "health": 0, "money": 5},
            ZodiacSign.SCORPIO: {"love": 5, "money": 10, "work": 5, "health": 0},
            ZodiacSign.SAGITTARIUS: {"work": 5, "health": 10, "love": 5, "money": 0},
            ZodiacSign.CAPRICORN: {"money": 10, "work": 10, "love": 0, "health": 5},
            ZodiacSign.AQUARIUS: {"work": 5, "love": 5, "health": 5, "money": 5},
            ZodiacSign.PISCES: {"love": 10, "health": 5, "work": 0, "money": 5}
        }
        
        base_scores = {}
        modifiers = trait_modifiers.get(zodiac, {})
        
        for category in ["love", "career", "health", "finance"]:
            base_score = rng.randint(30, 80)
            modifier = modifiers.get(category, 0)
            # 기간별 보정 (주간, 월간일 때 더 안정적)
            period_modifier = 5 if period in ["weekly", "monthly"] else 0
            
            final_score = self._calculate_score(base_score, [modifier, period_modifier])
            base_scores[category] = final_score
        
        # 전체 점수는 평균
        base_scores["overall"] = sum(base_scores.values()) // len(base_scores)
        
        return base_scores
    
    def _generate_zodiac_category_description(self, zodiac: ZodiacSign, category: str, grade: FortuneGrade, rng: random.Random) -> str:
        """별자리별 카테고리 설명 생성"""
        descriptions = {
            ("love", FortuneGrade.EXCELLENT): f"{zodiac.value}의 매력이 최고조에 달해요!",
            ("love", FortuneGrade.GOOD): f"따뜻한 감정이 {zodiac.value}를 둘러싸고 있어요",
            ("career", FortuneGrade.EXCELLENT): f"{zodiac.value}의 능력이 인정받을 때에요!",
            ("career", FortuneGrade.GOOD): f"꾸준한 노력이 {zodiac.value}에게 좋은 결과를 가져다줄 거예요",
            ("health", FortuneGrade.EXCELLENT): f"{zodiac.value}의 생명력이 넘쳐나요!",
            ("health", FortuneGrade.GOOD): f"{zodiac.value}의 컨디션이 안정적이에요",
            ("finance", FortuneGrade.EXCELLENT): f"{zodiac.value}에게 재정적 기회가 다가와요!",
            ("finance", FortuneGrade.GOOD): f"{zodiac.value}의 신중한 관리가 빛을 발해요"
        }
        
        key = (category, grade)
        if key in descriptions:
            return descriptions[key]
        else:
            return f"{zodiac.value}의 {category} 운세가 {grade.value}해요"
    
    def _generate_zodiac_overall_description(self, zodiac: ZodiacSign, grade: FortuneGrade, period: str, rng: random.Random) -> str:
        """별자리 전체 운세 설명"""
        period_text = {
            "daily": "오늘",
            "weekly": "이번 주",
            "monthly": "이번 달"
        }
        
        descriptions = {
            FortuneGrade.EXCELLENT: [
                f"{period_text[period]}은 {zodiac.value}에게 특별한 날이 될 거예요!",
                f"{zodiac.value}의 행운이 절정에 달했어요!",
                f"모든 것이 {zodiac.value}의 편에 서 있어요!"
            ],
            FortuneGrade.GOOD: [
                f"{period_text[period]}은 {zodiac.value}에게 좋은 기운이 흘러요",
                f"{zodiac.value}의 긍정적인 에너지가 느껴져요",
                f"순조로운 흐름이 {zodiac.value}를 기다려요"
            ],
            FortuneGrade.NORMAL: [
                f"{period_text[period]}은 {zodiac.value}에게 평온한 시기예요",
                f"안정적인 에너지가 {zodiac.value}를 감싸고 있어요",
                f"{zodiac.value}만의 페이스로 나아가세요"
            ]
        }
        
        return rng.choice(descriptions.get(grade, [f"{zodiac.value}의 운세가 {grade.value}해요"]))
    
    def _get_compatibility_info(self, zodiac: ZodiacSign) -> Dict:
        """별자리 호환성 정보"""
        compatibility_data = self.compatibility.get(zodiac, {})
        
        return {
            "best_match": [sign.value for sign in compatibility_data.get("best", [])],
            "good_match": [sign.value for sign in compatibility_data.get("good", [])],
            "challenging": [sign.value for sign in compatibility_data.get("challenging", [])]
        }
    
    def _get_zodiac_color(self, zodiac: ZodiacSign) -> str:
        """별자리별 행운의 색상"""
        colors = {
            ZodiacSign.ARIES: "빨간색",
            ZodiacSign.TAURUS: "초록색", 
            ZodiacSign.GEMINI: "노란색",
            ZodiacSign.CANCER: "은색",
            ZodiacSign.LEO: "금색",
            ZodiacSign.VIRGO: "네이비색",
            ZodiacSign.LIBRA: "분홍색",
            ZodiacSign.SCORPIO: "진홍색",
            ZodiacSign.SAGITTARIUS: "보라색",
            ZodiacSign.CAPRICORN: "갈색",
            ZodiacSign.AQUARIUS: "하늘색",
            ZodiacSign.PISCES: "바다색"
        }
        return colors.get(zodiac, "흰색")
    
    def _get_zodiac_number(self, zodiac: ZodiacSign, rng: random.Random) -> int:
        """별자리별 행운의 숫자"""
        # 각 별자리마다 고유한 숫자 범위
        number_ranges = {
            ZodiacSign.ARIES: (1, 9),
            ZodiacSign.TAURUS: (2, 8),
            ZodiacSign.GEMINI: (3, 7),
            ZodiacSign.CANCER: (4, 6),
            ZodiacSign.LEO: (5, 19),
            ZodiacSign.VIRGO: (6, 15),
            ZodiacSign.LIBRA: (7, 17),
            ZodiacSign.SCORPIO: (8, 13),
            ZodiacSign.SAGITTARIUS: (9, 21),
            ZodiacSign.CAPRICORN: (10, 22),
            ZodiacSign.AQUARIUS: (11, 23),
            ZodiacSign.PISCES: (12, 29)
        }
        
        start, end = number_ranges.get(zodiac, (1, 50))
        return rng.randint(start, end)
    
    def _generate_zodiac_advice(self, zodiac: ZodiacSign, grade: FortuneGrade, rng: random.Random) -> str:
        """별자리별 조언 생성"""
        # 별자리 특성에 맞는 조언
        zodiac_advice = {
            ZodiacSign.ARIES: [
                "당신의 열정을 믿고 도전하세요!",
                "리더십을 발휘할 기회를 놓치지 마세요!",
                "빠른 결정력이 도움이 될 거예요!"
            ],
            ZodiacSign.TAURUS: [
                "꾸준함이 가장 큰 무기예요!",
                "안정적인 계획을 세우세요!",
                "신중한 판단이 좋은 결과를 가져올 거예요!"
            ],
            ZodiacSign.GEMINI: [
                "다양한 관점으로 상황을 바라보세요!",
                "소통 능력을 활용해보세요!",
                "새로운 정보에 열린 마음을 가지세요!"
            ],
            ZodiacSign.CANCER: [
                "직감을 믿고 따라가보세요!",
                "가족이나 가까운 사람들과 시간을 보내세요!",
                "감성적인 면을 표현해도 좋아요!"
            ]
            # ... (다른 별자리들도 추가)
        }
        
        advice_list = zodiac_advice.get(zodiac, ["긍정적인 마음가짐을 유지하세요!"])
        return rng.choice(advice_list)


class SajuFortuneEngine(FortuneEngineBase):
    """사주 운세 엔진"""
    
    def __init__(self):
        super().__init__()
        self.fortune_type = FortuneType.ORIENTAL
        
        # 사주 오행 원소
        self.elements = ["목", "화", "토", "금", "수"]
        self.element_cycles = {
            "생성": {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"},
            "극복": {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}
        }
        
        # 천간
        self.heavenly_stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        
        # 지지
        self.earthly_branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        
        # 십이지 동물
        self.zodiac_animals = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
    
    async def generate_fortune(
        self, 
        context: PersonalizationContext,
        date_target: date = None,
        additional_params: Dict = None
    ) -> FortuneResult:
        """사주 운세 생성"""
        if date_target is None:
            date_target = datetime.now().date()
            
        if not context.birth_date:
            raise ValueError("생년월일 정보가 필요합니다")
            
        birth_time = additional_params.get("birth_time") if additional_params else context.birth_time
        
        # 사주 정보 계산
        saju_info = self._calculate_saju(context.birth_date, birth_time)
        
        rng = self._personalized_random(context, "saju")
        
        # 오행 균형 분석
        element_balance = self._analyze_element_balance(saju_info)
        
        # 운세 점수 계산 (오행 균형 반영)
        base_scores = self._generate_saju_scores(element_balance, date_target, rng)
        
        # 카테고리별 운세 생성
        categories = {}
        for category, score in base_scores.items():
            if category == "overall":
                continue
                
            grade = self._get_grade_from_score(score)
            description = self._generate_saju_category_description(
                category, grade, element_balance, rng
            )
            
            categories[category] = FortuneCategory(
                score=score,
                grade=grade.value,
                description=description
            )
        
        # 전체 운세
        overall_grade = self._get_grade_from_score(base_scores["overall"])
        overall_description = self._generate_saju_overall_description(
            overall_grade, element_balance, rng
        )
        
        # 조언 생성
        advice = self._generate_saju_advice(element_balance, overall_grade, rng)
        
        # 오행 정보
        saju_elements = []
        for pillar_name, pillar_data in saju_info.items():
            saju_elements.append(SajuElement(
                pillar=pillar_name,
                heavenly_stem=pillar_data["heavenly_stem"],
                earthly_branch=pillar_data["earthly_branch"],
                element=pillar_data["element"],
                meaning=pillar_data["meaning"]
            ))
        
        return FortuneResult(
            fortune_type=FortuneType.ORIENTAL,
            date=date_target,
            overall_fortune=FortuneCategory(
                score=base_scores["overall"],
                grade=overall_grade.value,
                description=overall_description
            ),
            categories=categories,
            saju_elements=saju_elements,
            element_balance=element_balance,
            advice=advice,
            live2d_emotion=self._get_emotion_from_grade(overall_grade),
            live2d_motion="special_reading"
        )
    
    def _calculate_saju(self, birth_date: date, birth_time: str = None) -> Dict:
        """사주 계산 (간소화된 버전)"""
        year = birth_date.year
        month = birth_date.month
        day = birth_date.day
        
        # 년주 계산 (간소화)
        year_stem_idx = (year - 4) % 10
        year_branch_idx = (year - 4) % 12
        
        # 월주 계산 (간소화)
        month_stem_idx = (year_stem_idx * 2 + month) % 10
        month_branch_idx = (month - 1) % 12
        
        # 일주 계산 (간소화)
        day_stem_idx = (year * 365 + month * 30 + day) % 10
        day_branch_idx = (year * 365 + month * 30 + day) % 12
        
        # 시주 계산 (생시가 있으면)
        time_stem_idx = 0
        time_branch_idx = 0
        if birth_time:
            hour = int(birth_time.split(":")[0])
            time_stem_idx = (day_stem_idx * 2 + hour // 2) % 10
            time_branch_idx = (hour + 1) // 2 % 12
        
        saju_info = {
            "년주": {
                "heavenly_stem": self.heavenly_stems[year_stem_idx],
                "earthly_branch": self.earthly_branches[year_branch_idx],
                "element": self._get_element_from_stem(year_stem_idx),
                "meaning": "조상, 부모의 영향"
            },
            "월주": {
                "heavenly_stem": self.heavenly_stems[month_stem_idx],
                "earthly_branch": self.earthly_branches[month_branch_idx],
                "element": self._get_element_from_stem(month_stem_idx),
                "meaning": "사회적 관계, 직업"
            },
            "일주": {
                "heavenly_stem": self.heavenly_stems[day_stem_idx],
                "earthly_branch": self.earthly_branches[day_branch_idx],
                "element": self._get_element_from_stem(day_stem_idx),
                "meaning": "본인의 성격, 기본 운세"
            },
            "시주": {
                "heavenly_stem": self.heavenly_stems[time_stem_idx],
                "earthly_branch": self.earthly_branches[time_branch_idx],
                "element": self._get_element_from_stem(time_stem_idx),
                "meaning": "자녀, 말년 운세"
            }
        }
        
        return saju_info
    
    def _get_element_from_stem(self, stem_idx: int) -> str:
        """천간에서 오행 추출"""
        element_map = {
            0: "목", 1: "목",  # 갑을
            2: "화", 3: "화",  # 병정
            4: "토", 5: "토",  # 무기
            6: "금", 7: "금",  # 경신
            8: "수", 9: "수"   # 임계
        }
        return element_map[stem_idx]
    
    def _analyze_element_balance(self, saju_info: Dict) -> Dict[str, int]:
        """오행 균형 분석"""
        element_count = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
        
        for pillar_data in saju_info.values():
            element = pillar_data["element"]
            element_count[element] += 1
        
        return element_count
    
    def _generate_saju_scores(self, element_balance: Dict[str, int], date_target: date, rng: random.Random) -> Dict[str, int]:
        """사주 기반 점수 생성"""
        # 가장 강한 오행과 약한 오행 찾기
        max_element = max(element_balance, key=element_balance.get)
        min_element = min(element_balance, key=element_balance.get)
        
        # 오행별 영향 카테고리
        element_influence = {
            "목": {"health": 10, "love": 5, "work": 0, "money": -5},
            "화": {"love": 10, "work": 5, "health": 0, "money": -5},
            "토": {"money": 10, "health": 5, "love": 0, "work": -5},
            "금": {"work": 10, "money": 5, "health": 0, "love": -5},
            "수": {"health": 5, "love": 5, "work": 5, "money": 5}
        }
        
        base_scores = {}
        for category in ["love", "work", "health", "money"]:
            base_score = rng.randint(40, 80)
            
            # 강한 오행의 긍정적 영향
            max_influence = element_influence[max_element].get(category, 0)
            # 약한 오행의 부정적 영향
            min_influence = element_influence[min_element].get(category, 0) // 2
            
            final_score = self._calculate_score(base_score, [max_influence, min_influence])
            base_scores[category] = final_score
        
        # 전체 점수
        base_scores["overall"] = sum(base_scores.values()) // len(base_scores)
        
        return base_scores
    
    def _generate_saju_category_description(self, category: str, grade: FortuneGrade, element_balance: Dict, rng: random.Random) -> str:
        """사주 카테고리별 설명"""
        # 가장 강한 오행 기반 설명
        max_element = max(element_balance, key=element_balance.get)
        
        descriptions = {
            ("love", "목"): "감정이 풍부하고 성장하는 관계",
            ("love", "화"): "열정적이고 활발한 연애운", 
            ("love", "토"): "안정적이고 신뢰할 수 있는 관계",
            ("love", "금"): "명확하고 결단력 있는 관계",
            ("love", "수"): "깊이 있고 지혜로운 감정",
            
            ("work", "목"): "창의적이고 성장 가능성이 높은 업무",
            ("work", "화"): "역동적이고 활발한 직장 생활",
            ("work", "토"): "안정적이고 꾸준한 성과",
            ("work", "금"): "체계적이고 효율적인 업무 처리",
            ("work", "수"): "지혜롭고 유연한 문제 해결"
        }
        
        key = (category, max_element)
        if key in descriptions:
            return descriptions[key]
        else:
            return f"{max_element} 기운이 {category} 영역에 영향을 주고 있어요"
    
    def _generate_saju_overall_description(self, grade: FortuneGrade, element_balance: Dict, rng: random.Random) -> str:
        """사주 전체 운세 설명"""
        max_element = max(element_balance, key=element_balance.get)
        balance_level = max(element_balance.values()) - min(element_balance.values())
        
        if balance_level <= 1:
            balance_desc = "오행이 잘 균형을 이루고 있어"
        elif balance_level <= 2:
            balance_desc = f"{max_element} 기운이 약간 강하지만 무난해"
        else:
            balance_desc = f"{max_element} 기운이 매우 강해"
        
        descriptions = {
            FortuneGrade.EXCELLENT: f"{balance_desc} 모든 면에서 좋은 운세가 흘러요!",
            FortuneGrade.GOOD: f"{balance_desc} 전반적으로 순조로운 흐름이에요!",
            FortuneGrade.NORMAL: f"{balance_desc} 안정적인 운세를 보여줘요!",
            FortuneGrade.BAD: f"{balance_desc} 조금 신중함이 필요한 시기예요!",
            FortuneGrade.WARNING: f"{balance_desc} 특별히 주의가 필요한 때에요!"
        }
        
        return descriptions[grade]
    
    def _generate_saju_advice(self, element_balance: Dict, grade: FortuneGrade, rng: random.Random) -> str:
        """사주 기반 조언"""
        max_element = max(element_balance, key=element_balance.get)
        min_element = min(element_balance, key=element_balance.get)
        
        # 약한 오행을 보강하는 조언
        element_advice = {
            "목": "자연과 가까이하고 성장에 집중하세요",
            "화": "활발한 활동과 열정을 표현하세요",
            "토": "안정감을 찾고 꾸준함을 유지하세요",
            "금": "체계적인 계획과 규칙을 만드세요",
            "수": "지혜로운 판단과 유연성을 발휘하세요"
        }
        
        return element_advice.get(min_element, "균형 잡힌 생활을 유지하세요")


class FortuneEngineFactory:
    """운세 엔진 팩토리"""
    
    @staticmethod
    def create_engine(fortune_type: FortuneType) -> FortuneEngineBase:
        """운세 타입에 따른 엔진 생성"""
        # Handle both model FortuneType and EngineFortuneType
        if hasattr(fortune_type, 'value'):
            type_value = fortune_type.value
        else:
            type_value = str(fortune_type)
            
        if type_value in ["daily", FortuneType.DAILY.value]:
            return DailyFortuneEngine()
        elif type_value in ["tarot", FortuneType.TAROT.value]:
            return TarotFortuneEngine()
        elif type_value in ["zodiac", FortuneType.ZODIAC.value]:
            return ZodiacFortuneEngine()
        elif type_value in ["oriental", "saju", FortuneType.ORIENTAL.value]:
            return SajuFortuneEngine()
        else:
            raise ValueError(f"지원되지 않는 운세 타입: {fortune_type}")
    
    @staticmethod
    def get_available_types() -> List[EngineFortuneType]:
        """사용 가능한 운세 타입 목록"""
        return [EngineFortuneType.DAILY, EngineFortuneType.TAROT, EngineFortuneType.ZODIAC, EngineFortuneType.ORIENTAL]
"""
콘텐츠 필터링 시스템 - 부적절한 내용 자동 차단
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class FilterLevel(Enum):
    """필터링 레벨"""
    STRICT = "strict"      # 엄격한 필터링
    MODERATE = "moderate"  # 보통 필터링  
    LENIENT = "lenient"    # 관대한 필터링


class FilterCategory(Enum):
    """필터링 카테고리"""
    SEXUAL = "sexual"              # 성적 내용
    VIOLENT = "violent"            # 폭력적 내용
    HATE_SPEECH = "hate_speech"    # 혐오 발언
    PERSONAL_INFO = "personal_info" # 개인정보 수집
    POLITICAL = "political"        # 정치적 내용
    RELIGIOUS = "religious"        # 종교적 내용
    SPAM = "spam"                  # 스팸
    INAPPROPRIATE = "inappropriate" # 기타 부적절한 내용


@dataclass
class FilterResult:
    """필터링 결과"""
    is_blocked: bool
    category: Optional[FilterCategory]
    confidence: float  # 0.0 ~ 1.0
    reason: str
    filtered_text: Optional[str] = None  # 필터링된 텍스트


class ContentFilter:
    """콘텐츠 필터링 메인 클래스"""
    
    def __init__(self, filter_level: FilterLevel = FilterLevel.MODERATE):
        self.filter_level = filter_level
        self.load_filter_patterns()
        
        # 운세 관련 허용 키워드
        self.fortune_keywords = {
            "운세", "타로", "별자리", "사주", "점괘", "미래", "행운", "불행",
            "연애운", "금전운", "건강운", "직업운", "운명", "길흉", "점성술",
            "오늘", "내일", "이번주", "이번달", "올해", "궁금", "알고싶어"
        }
        
        # 캐릭터 관련 허용 키워드
        self.character_keywords = {
            "미라", "안녕", "고마워", "감사", "예쁘다", "귀엽다", "좋아",
            "이야기", "대화", "친구", "도움", "상담"
        }
    
    def load_filter_patterns(self):
        """필터링 패턴 로드"""
        # 성적 내용 패턴
        self.sexual_patterns = [
            r'(?:성관계|섹스|야동|포르노|에로|야한|음란|19금)',
            r'(?:자위|딸감|야시|꼴릿|떡치|삽입|애무)',
            r'(?:가슴|엉덩이|다리|몸매)(?:\s*)?(?:보여|줘|주세요)',
            r'(?:벗어|탈의|노출|몸|나체)',
            r'(?:키스|스킨십|터치|만지|쓰다듬)'
        ]
        
        # 폭력적 내용 패턴
        self.violent_patterns = [
            r'(?:죽이|살인|자살|폭력|때리|패|구타)',
            r'(?:칼|총|무기|폭탄|테러|공격)',
            r'(?:피|살|고문|학대|괴롭|왕따)'
        ]
        
        # 혐오 발언 패턴
        self.hate_speech_patterns = [
            r'(?:개새끼|씨발|병신|지랄|꺼져|닥쳐)',
            r'(?:바보|멍청|똥|쓰레기)(?:\s*)?(?:같|년|놈)',
            r'(?:장애|정신병|미친|또라이)',
            r'(?:죽어|사라져|없어져)(?:\s*)?(?:라|버려)'
        ]
        
        # 개인정보 수집 패턴
        self.personal_info_patterns = [
            r'(?:이름|성명)(?:\s*)?(?:이|가)?(?:\s*)?(?:뭐|무엇|어떻게)(?:\s*)?(?:돼|야|이야)',
            r'(?:나이|몇살|어디살|주소|전화번호|핸드폰)',
            r'(?:학교|직장|회사)(?:\s*)?(?:다녀|어디)',
            r'(?:사진|얼굴|모습)(?:\s*)?(?:보여|줘|주세요)',
            r'(?:만나|데이트|약속|만남)'
        ]
        
        # 정치적 내용 패턴
        self.political_patterns = [
            r'(?:대통령|정치|정부|국회|선거|투표)',
            r'(?:좌파|우파|진보|보수|민주당|국민의힘)',
            r'(?:시위|집회|데모|항의|반대)'
        ]
        
        # 종교적 내용 패턴  
        self.religious_patterns = [
            r'(?:기독교|불교|이슬람|힌두교|종교|신앙)',
            r'(?:예수|부처|알라|신|하나님|교회|절)',
            r'(?:기도|예배|전도|포교|선교)'
        ]
        
        # 스팸 패턴
        self.spam_patterns = [
            r'(?:광고|홍보|판매|구매|돈|수익)',
            r'(?:클릭|링크|사이트|URL|주소)',
            r'(?:무료|할인|이벤트|혜택|쿠폰)',
            r'(?:연락|문의)(?:\s*)?(?:주세요|해주세요|바람)',
            r'(?:같은|똑같은)(?:\s*)?(?:말|내용)(?:\s*)?(?:반복|계속)'
        ]
    
    def check_content(self, text: str, context: Optional[Dict] = None) -> FilterResult:
        """콘텐츠 필터링 수행"""
        if not text or not text.strip():
            return FilterResult(
                is_blocked=False,
                category=None,
                confidence=0.0,
                reason="Empty content"
            )
        
        text = text.strip().lower()
        
        # 운세/캐릭터 관련 내용은 우선 허용
        if self._is_fortune_related(text):
            return FilterResult(
                is_blocked=False,
                category=None,
                confidence=0.0,
                reason="Fortune-related content allowed"
            )
        
        # 카테고리별 필터링 검사
        filter_checks = [
            (FilterCategory.SEXUAL, self.sexual_patterns),
            (FilterCategory.VIOLENT, self.violent_patterns),
            (FilterCategory.HATE_SPEECH, self.hate_speech_patterns),
            (FilterCategory.PERSONAL_INFO, self.personal_info_patterns),
            (FilterCategory.POLITICAL, self.political_patterns),
            (FilterCategory.RELIGIOUS, self.religious_patterns),
            (FilterCategory.SPAM, self.spam_patterns),
        ]
        
        for category, patterns in filter_checks:
            result = self._check_patterns(text, patterns, category)
            if result.is_blocked:
                return result
        
        # 부적절한 내용 일반 검사
        inappropriate_result = self._check_inappropriate_content(text)
        if inappropriate_result.is_blocked:
            return inappropriate_result
        
        return FilterResult(
            is_blocked=False,
            category=None,
            confidence=0.0,
            reason="Content passed all filters"
        )
    
    def _is_fortune_related(self, text: str) -> bool:
        """운세 관련 내용인지 확인"""
        # 운세 키워드가 포함되어 있으면 허용
        for keyword in self.fortune_keywords:
            if keyword in text:
                return True
        
        # 캐릭터 관련 대화도 허용
        for keyword in self.character_keywords:
            if keyword in text:
                return True
                
        return False
    
    def _check_patterns(self, text: str, patterns: List[str], category: FilterCategory) -> FilterResult:
        """패턴 매칭 검사"""
        matches = []
        total_confidence = 0.0
        
        for pattern in patterns:
            matches_found = re.findall(pattern, text, re.IGNORECASE)
            if matches_found:
                matches.extend(matches_found)
                # 매치된 길이에 따라 신뢰도 증가
                confidence = min(len(''.join(matches_found)) / len(text), 1.0)
                total_confidence += confidence
        
        if matches:
            # 필터 레벨에 따른 임계값 조정
            threshold = self._get_threshold_for_category(category)
            final_confidence = min(total_confidence, 1.0)
            
            if final_confidence >= threshold:
                return FilterResult(
                    is_blocked=True,
                    category=category,
                    confidence=final_confidence,
                    reason=f"{category.value} content detected: {matches[:3]}",  # 처음 3개만 표시
                    filtered_text=self._filter_text(text, patterns)
                )
        
        return FilterResult(
            is_blocked=False,
            category=None,
            confidence=total_confidence,
            reason="Pattern check passed"
        )
    
    def _check_inappropriate_content(self, text: str) -> FilterResult:
        """기타 부적절한 내용 검사"""
        # 반복 문자 검사 (예: "ㅋㅋㅋㅋㅋㅋㅋㅋㅋㅋ")
        repeated_chars = re.findall(r'(.)\1{4,}', text)
        if repeated_chars and len(''.join(repeated_chars)) > len(text) * 0.3:
            return FilterResult(
                is_blocked=True,
                category=FilterCategory.SPAM,
                confidence=0.8,
                reason="Excessive repeated characters",
                filtered_text=re.sub(r'(.)\1{4,}', r'\1\1\1', text)
            )
        
        # 의미없는 문자열 검사
        if len(text) > 10 and len(set(text.replace(' ', ''))) < 3:
            return FilterResult(
                is_blocked=True,
                category=FilterCategory.SPAM,
                confidence=0.9,
                reason="Meaningless character sequence"
            )
        
        # 과도한 특수문자 검사
        special_chars = re.findall(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?~`]', text)
        if len(special_chars) > len(text) * 0.4:
            return FilterResult(
                is_blocked=True,
                category=FilterCategory.SPAM,
                confidence=0.7,
                reason="Excessive special characters",
                filtered_text=re.sub(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?~`]{2,}', '', text)
            )
        
        return FilterResult(
            is_blocked=False,
            category=None,
            confidence=0.0,
            reason="No inappropriate content detected"
        )
    
    def _get_threshold_for_category(self, category: FilterCategory) -> float:
        """카테고리별 임계값 반환"""
        base_thresholds = {
            FilterCategory.SEXUAL: 0.3,
            FilterCategory.VIOLENT: 0.4,
            FilterCategory.HATE_SPEECH: 0.2,
            FilterCategory.PERSONAL_INFO: 0.5,
            FilterCategory.POLITICAL: 0.6,
            FilterCategory.RELIGIOUS: 0.7,
            FilterCategory.SPAM: 0.4,
            FilterCategory.INAPPROPRIATE: 0.5
        }
        
        base_threshold = base_thresholds.get(category, 0.5)
        
        # 필터 레벨에 따른 조정
        if self.filter_level == FilterLevel.STRICT:
            return base_threshold * 0.7  # 더 엄격하게
        elif self.filter_level == FilterLevel.LENIENT:
            return base_threshold * 1.3  # 더 관대하게
        else:
            return base_threshold
    
    def _filter_text(self, text: str, patterns: List[str]) -> str:
        """부적절한 부분을 마스킹한 텍스트 반환"""
        filtered_text = text
        
        for pattern in patterns:
            filtered_text = re.sub(pattern, lambda m: '*' * len(m.group()), filtered_text, flags=re.IGNORECASE)
        
        return filtered_text
    
    def suggest_alternative(self, blocked_content: str, category: FilterCategory) -> str:
        """차단된 내용에 대한 대안 제안"""
        suggestions = {
            FilterCategory.SEXUAL: "죄송해요, 그런 내용에 대해서는 답변드릴 수 없어요. 운세나 일상 이야기는 어떠세요?",
            FilterCategory.VIOLENT: "폭력적인 내용은 다루지 않아요. 대신 긍정적인 이야기를 나눠보아요!",
            FilterCategory.HATE_SPEECH: "상처주는 말보다는 따뜻한 대화를 나누고 싶어요.",
            FilterCategory.PERSONAL_INFO: "개인정보는 말씀드릴 수 없어요. 운세 상담이나 재미있는 이야기는 어떠세요?",
            FilterCategory.POLITICAL: "정치적인 주제보다는 운세나 일상 이야기가 더 좋을 것 같아요!",
            FilterCategory.RELIGIOUS: "종교적인 내용보다는 별자리 운세나 타로는 어떠세요?",
            FilterCategory.SPAM: "같은 말을 반복하지 마시고, 궁금한 것을 물어보세요!",
            FilterCategory.INAPPROPRIATE: "좀 더 적절한 주제로 대화해요. 오늘 운세가 궁금하지 않으세요?"
        }
        
        return suggestions.get(category, "다른 주제로 이야기해볼까요? 운세 상담을 도와드릴 수 있어요!")


class AdaptiveFilter:
    """적응형 필터 - 사용자 패턴 학습"""
    
    def __init__(self, content_filter: ContentFilter):
        self.content_filter = content_filter
        self.user_patterns: Dict[str, List[str]] = {}  # user_id -> blocked_patterns
        self.false_positives: Set[str] = set()  # 잘못 차단된 내용들
    
    def check_with_learning(self, text: str, user_id: str, context: Optional[Dict] = None) -> FilterResult:
        """학습 기능이 있는 필터링"""
        # 기본 필터링 수행
        result = self.content_filter.check_content(text, context)
        
        # 사용자별 패턴 기록
        if result.is_blocked:
            if user_id not in self.user_patterns:
                self.user_patterns[user_id] = []
            
            # 차단된 패턴 기록 (중복 제거)
            pattern_key = f"{result.category.value}:{text[:50]}"
            if pattern_key not in self.user_patterns[user_id]:
                self.user_patterns[user_id].append(pattern_key)
                
                # 최대 100개까지만 보관
                if len(self.user_patterns[user_id]) > 100:
                    self.user_patterns[user_id] = self.user_patterns[user_id][-100:]
        
        # 반복 차단 사용자 감지
        if user_id in self.user_patterns and len(self.user_patterns[user_id]) > 20:
            result.reason += " (repeated violations detected)"
            result.confidence = min(result.confidence * 1.2, 1.0)
        
        return result
    
    def report_false_positive(self, text: str, user_id: str):
        """잘못된 차단 신고"""
        self.false_positives.add(text.lower().strip())
        logger.info(f"False positive reported by {user_id}: {text[:100]}")
    
    def is_likely_false_positive(self, text: str) -> bool:
        """잘못된 차단 가능성 확인"""
        return text.lower().strip() in self.false_positives


# 필터 인스턴스 생성
default_filter = ContentFilter(FilterLevel.MODERATE)
adaptive_filter = AdaptiveFilter(default_filter)


def filter_message(text: str, user_id: str = None, context: Dict = None) -> FilterResult:
    """메시지 필터링 메인 함수"""
    if user_id:
        return adaptive_filter.check_with_learning(text, user_id, context)
    else:
        return default_filter.check_content(text, context)


def get_filter_suggestion(result: FilterResult) -> str:
    """필터링 결과에 따른 제안 반환"""
    if not result.is_blocked:
        return ""
    
    return default_filter.suggest_alternative(result.filtered_text or "", result.category)
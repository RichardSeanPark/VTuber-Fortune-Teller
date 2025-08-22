# Live2D 운세 앱 보안 아키텍처 설계

## 1. 보안 아키텍처 개요

### 1.1 보안 설계 원칙
- **다층 보안 (Defense in Depth)**: 여러 보안 계층으로 중복 보호
- **최소 권한 원칙**: 최소한의 필요한 권한만 부여
- **보안 기본값 (Secure by Default)**: 기본 설정이 가장 안전한 상태
- **데이터 최소화**: 필요한 최소한의 데이터만 수집 및 저장
- **투명성**: 보안 정책과 데이터 처리 방식 공개

### 1.2 위협 모델 분석
**주요 위협 요소:**
1. **콘텐츠 위험**: 부적절한 대화 내용 및 요청
2. **개인정보 유출**: 생년월일, 개인적 질문 등 민감 정보
3. **서비스 남용**: 과도한 API 호출, 스팸
4. **데이터 무결성**: 운세 결과 조작, 채팅 기록 변조
5. **시스템 침입**: SQL Injection, XSS, CSRF 공격

## 2. 콘텐츠 필터링 시스템

### 2.1 실시간 콘텐츠 필터링

```python
from typing import List, Dict, Tuple
import re
from enum import Enum

class ContentFilterLevel(Enum):
    ALLOWED = "allowed"
    WARNING = "warning"
    BLOCKED = "blocked"
    SUSPICIOUS = "suspicious"

class ContentFilter:
    def __init__(self):
        self.blocked_patterns = self._load_blocked_patterns()
        self.warning_patterns = self._load_warning_patterns()
        self.personal_info_patterns = self._load_personal_info_patterns()
        
    def _load_blocked_patterns(self) -> List[str]:
        """차단할 패턴 로드"""
        return [
            # 성적 내용
            r'(?i)(성관계|섹스|자위|야동|음란)',
            r'(?i)(가슴|엉덩이|성기|음부)',
            
            # 폭력적 내용
            r'(?i)(죽이|살인|자살|폭력|때리)',
            r'(?i)(칼|총|폭탄|테러)',
            
            # 정치적 내용
            r'(?i)(대통령|정치|선거|정부|국정)',
            r'(?i)(민주당|국민의힘|정당)',
            
            # 종교적 내용
            r'(?i)(기독교|불교|이슬람|종교|신)',
            r'(?i)(교회|절|성당|기도)',
            
            # 개인정보 수집 시도
            r'(?i)(전화번호|휴대폰|핸드폰)',
            r'(?i)(주소|집|사는 곳)',
            r'(?i)(이름이 뭐|본명|성함)',
            
            # 전문적 조언 차단
            r'(?i)(의사|병원|치료|약|수술)',
            r'(?i)(투자|주식|펀드|대출|보험)',
            r'(?i)(법률|소송|변호사|고발)'
        ]
    
    def _load_warning_patterns(self) -> List[str]:
        """경고 표시할 패턴 로드"""
        return [
            r'(?i)(우울|슬프|힘들|죽고 싶)',
            r'(?i)(스트레스|고민|걱정)',
            r'(?i)(외로|혼자|친구 없)',
            r'(?i)(이별|헤어|실연)'
        ]
    
    def _load_personal_info_patterns(self) -> List[str]:
        """개인정보 패턴 로드"""
        return [
            r'\d{2,4}[\-\.\/]\d{1,2}[\-\.\/]\d{1,2}',  # 생년월일
            r'\d{3}[\-\s]?\d{3,4}[\-\s]?\d{4}',        # 전화번호
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 이메일
        ]
    
    def filter_content(self, text: str) -> Tuple[ContentFilterLevel, str, Dict]:
        """콘텐츠 필터링 수행"""
        text = text.strip()
        
        # 빈 메시지 차단
        if not text or len(text) < 2:
            return ContentFilterLevel.BLOCKED, "메시지가 너무 짧아요.", {}
        
        # 길이 제한
        if len(text) > 500:
            return ContentFilterLevel.BLOCKED, "메시지가 너무 길어요. 500자 이내로 작성해주세요.", {}
        
        # 개인정보 검출
        personal_info_detected = self._detect_personal_info(text)
        if personal_info_detected:
            return ContentFilterLevel.BLOCKED, "개인정보는 말씀해주시지 않으셔도 돼요!", {
                "detected_patterns": personal_info_detected
            }
        
        # 차단 패턴 검사
        blocked_matches = self._check_patterns(text, self.blocked_patterns)
        if blocked_matches:
            return ContentFilterLevel.BLOCKED, "죄송해요, 그런 질문에는 답변드릴 수 없어요.", {
                "blocked_patterns": blocked_matches
            }
        
        # 경고 패턴 검사
        warning_matches = self._check_patterns(text, self.warning_patterns)
        if warning_matches:
            return ContentFilterLevel.WARNING, "", {
                "warning_patterns": warning_matches,
                "comfort_response": True
            }
        
        return ContentFilterLevel.ALLOWED, "", {}
    
    def _detect_personal_info(self, text: str) -> List[str]:
        """개인정보 패턴 검출"""
        detected = []
        for pattern in self.personal_info_patterns:
            if re.search(pattern, text):
                detected.append(pattern)
        return detected
    
    def _check_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """패턴 매칭 검사"""
        matches = []
        for pattern in patterns:
            if re.search(pattern, text):
                matches.append(pattern)
        return matches
```

### 2.2 AI 기반 콘텐츠 분석

```python
class AIContentAnalyzer:
    """AI를 활용한 고도화된 콘텐츠 분석"""
    
    def __init__(self):
        self.sentiment_threshold = 0.3
        self.toxicity_threshold = 0.7
        
    async def analyze_content(self, text: str, context: Dict = None) -> Dict:
        """AI 모델을 사용한 콘텐츠 분석"""
        analysis_result = {
            "sentiment_score": 0.0,      # -1 ~ 1 (부정 ~ 긍정)
            "toxicity_score": 0.0,       # 0 ~ 1 (안전 ~ 위험)
            "topic_classification": "",   # 주제 분류
            "emotional_state": "",        # 감정 상태
            "requires_comfort": False     # 위로 필요 여부
        }
        
        # 감정 분석
        sentiment = await self._analyze_sentiment(text)
        analysis_result["sentiment_score"] = sentiment
        
        # 독성 콘텐츠 검출
        toxicity = await self._detect_toxicity(text)
        analysis_result["toxicity_score"] = toxicity
        
        # 주제 분류
        topic = await self._classify_topic(text)
        analysis_result["topic_classification"] = topic
        
        # 감정 상태 분석
        emotional_state = await self._analyze_emotional_state(text, sentiment)
        analysis_result["emotional_state"] = emotional_state
        
        # 위로 필요 여부 판단
        if sentiment < -0.5 or "sad" in emotional_state or "stressed" in emotional_state:
            analysis_result["requires_comfort"] = True
            
        return analysis_result
    
    async def _analyze_sentiment(self, text: str) -> float:
        """감정 분석 (간단한 키워드 기반)"""
        positive_words = ["좋", "기쁘", "행복", "사랑", "희망", "감사"]
        negative_words = ["나쁘", "슬프", "우울", "힘들", "걱정", "스트레스"]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        total_count = pos_count + neg_count
        if total_count == 0:
            return 0.0
            
        return (pos_count - neg_count) / total_count
    
    async def _detect_toxicity(self, text: str) -> float:
        """독성 콘텐츠 검출"""
        toxic_indicators = ["욕설", "비하", "차별", "혐오", "위협"]
        toxic_count = sum(1 for indicator in toxic_indicators if indicator in text)
        return min(toxic_count * 0.3, 1.0)
    
    async def _classify_topic(self, text: str) -> str:
        """주제 분류"""
        topics = {
            "love": ["연애", "사랑", "좋아", "만남", "헤어", "이별"],
            "work": ["직장", "일", "업무", "직업", "취업", "회사"],
            "health": ["건강", "몸", "아프", "병", "치료"],
            "money": ["돈", "재산", "투자", "수입", "지출", "경제"],
            "family": ["가족", "부모", "형제", "자매", "친척"],
            "friendship": ["친구", "동료", "인간관계", "사람"],
            "general": []
        }
        
        for topic, keywords in topics.items():
            if any(keyword in text for keyword in keywords):
                return topic
        return "general"
    
    async def _analyze_emotional_state(self, text: str, sentiment: float) -> str:
        """감정 상태 분석"""
        if sentiment > 0.5:
            return "happy"
        elif sentiment < -0.5:
            return "sad"
        elif any(word in text for word in ["걱정", "스트레스", "불안"]):
            return "anxious"
        elif any(word in text for word in ["화", "짜증", "분노"]):
            return "angry"
        else:
            return "neutral"
```

### 2.3 동적 응답 생성

```python
class SafeResponseGenerator:
    """안전한 응답 생성기"""
    
    def __init__(self):
        self.comfort_responses = self._load_comfort_responses()
        self.redirect_responses = self._load_redirect_responses()
        self.blocked_responses = self._load_blocked_responses()
    
    def _load_comfort_responses(self) -> List[str]:
        """위로 응답 템플릿"""
        return [
            "힘드신 일이 있으셨나 봐요. 저는 운세를 통해 조금이나마 위로가 되고 싶어요.",
            "어려운 시간을 보내고 계시는군요. 오늘의 운세를 통해 희망을 찾아보시는 건 어떨까요?",
            "마음이 무거우시네요. 운세로 기분 전환을 해보실까요?",
            "스트레스가 많으신 것 같아요. 잠시 운세로 마음을 달래보세요."
        ]
    
    def _load_redirect_responses(self) -> List[str]:
        """주제 전환 응답 템플릿"""
        return [
            "그런 이야기보다는 오늘의 운세가 어떨지 궁금하지 않으세요?",
            "저는 운세 전문가라 그런 건 잘 모르겠어요. 운세 얘기를 해볼까요?",
            "음... 그것보다는 당신의 운세를 봐드리고 싶어요!",
            "제가 잘 아는 건 운세예요. 다른 이야기를 해볼까요?"
        ]
    
    def _load_blocked_responses(self) -> Dict[str, List[str]]:
        """차단 상황별 응답 템플릿"""
        return {
            "inappropriate": [
                "죄송해요, 그런 질문에는 답변드릴 수 없어요.",
                "그런 이야기는 제가 잘 모르겠어요. 다른 걸 물어보실래요?",
                "음... 다른 주제로 이야기해요!"
            ],
            "personal_info": [
                "개인정보는 말씀해주시지 않으셔도 돼요!",
                "그런 정보 없이도 운세를 봐드릴 수 있어요.",
                "개인적인 정보는 비밀로 해두세요!"
            ],
            "medical": [
                "건강과 관련된 전문적인 조언은 의사와 상담하시는 게 좋을 것 같아요.",
                "제가 드릴 수 있는 건 운세뿐이에요. 건강은 전문가와 상의하세요.",
                "운세로는 건강에 대한 전문적인 답변을 드리기 어려워요."
            ],
            "financial": [
                "투자나 재정 조언은 전문가와 상담하시는 게 좋겠어요.",
                "제가 아는 건 운세뿐이에요. 재정 상담은 전문가에게!",
                "운세와 실제 투자는 다른 문제예요. 전문가의 도움을 받으세요."
            ]
        }
    
    def generate_safe_response(self, filter_result: ContentFilterLevel, 
                             context: Dict = None) -> Dict:
        """안전한 응답 생성"""
        response_data = {
            "message": "",
            "live2d_emotion": "neutral",
            "live2d_motion": "greeting",
            "should_redirect": False,
            "comfort_mode": False
        }
        
        if filter_result == ContentFilterLevel.BLOCKED:
            category = self._determine_block_category(context)
            responses = self.blocked_responses.get(category, self.blocked_responses["inappropriate"])
            response_data["message"] = random.choice(responses)
            response_data["live2d_emotion"] = "concern"
            response_data["should_redirect"] = True
            
        elif filter_result == ContentFilterLevel.WARNING:
            if context and context.get("comfort_response"):
                response_data["message"] = random.choice(self.comfort_responses)
                response_data["live2d_emotion"] = "comfort"
                response_data["comfort_mode"] = True
            else:
                response_data["message"] = random.choice(self.redirect_responses)
                response_data["should_redirect"] = True
        
        return response_data
    
    def _determine_block_category(self, context: Dict) -> str:
        """차단 카테고리 결정"""
        if not context:
            return "inappropriate"
            
        blocked_patterns = context.get("blocked_patterns", [])
        
        # 패턴 분석하여 카테고리 결정
        for pattern in blocked_patterns:
            if any(medical in pattern for medical in ["의사", "병원", "치료"]):
                return "medical"
            elif any(financial in pattern for financial in ["투자", "주식", "대출"]):
                return "financial"
            elif any(personal in pattern for personal in ["전화번호", "주소", "이름"]):
                return "personal_info"
                
        return "inappropriate"
```

## 3. 세션 관리 및 인증

### 3.1 세션 기반 인증 시스템

```python
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets

class SessionManager:
    """세션 관리 시스템"""
    
    def __init__(self, secret_key: str, session_timeout: int = 3600):
        self.secret_key = secret_key
        self.session_timeout = session_timeout  # 초
        self.active_sessions = {}  # 메모리 기반 세션 저장소
        
    def create_session(self, user_uuid: str = None, 
                      session_type: str = "anonymous") -> Dict:
        """새 세션 생성"""
        session_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        expires_at = current_time + timedelta(seconds=self.session_timeout)
        
        session_data = {
            "session_id": session_id,
            "user_uuid": user_uuid,
            "session_type": session_type,
            "created_at": current_time.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_activity": current_time.isoformat(),
            "ip_address": None,
            "user_agent": None,
            "is_active": True,
            "message_count": 0,
            "rate_limit_reset": current_time.isoformat()
        }
        
        # 메모리에 세션 저장
        self.active_sessions[session_id] = session_data
        
        # JWT 토큰 생성
        token_payload = {
            "session_id": session_id,
            "exp": expires_at,
            "iat": current_time,
            "type": session_type
        }
        
        session_token = jwt.encode(token_payload, self.secret_key, algorithm="HS256")
        
        return {
            "session_id": session_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "character_name": "미라"
        }
    
    def validate_session(self, session_token: str) -> Tuple[bool, Dict]:
        """세션 토큰 검증"""
        try:
            # JWT 토큰 검증
            payload = jwt.decode(session_token, self.secret_key, algorithms=["HS256"])
            session_id = payload["session_id"]
            
            # 메모리에서 세션 데이터 조회
            session_data = self.active_sessions.get(session_id)
            if not session_data:
                return False, {"error": "Session not found"}
            
            # 세션 만료 확인
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                self.cleanup_session(session_id)
                return False, {"error": "Session expired"}
            
            # 마지막 활동 시간 업데이트
            self.update_last_activity(session_id)
            
            return True, session_data
            
        except jwt.ExpiredSignatureError:
            return False, {"error": "Token expired"}
        except jwt.InvalidTokenError:
            return False, {"error": "Invalid token"}
        except Exception as e:
            return False, {"error": f"Validation error: {str(e)}"}
    
    def update_last_activity(self, session_id: str):
        """세션 활동 시간 업데이트"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def increment_message_count(self, session_id: str) -> int:
        """메시지 카운트 증가"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["message_count"] += 1
            return self.active_sessions[session_id]["message_count"]
        return 0
    
    def cleanup_session(self, session_id: str):
        """세션 정리"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_expired_sessions(self):
        """만료된 세션 정리"""
        current_time = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if current_time > expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.cleanup_session(session_id)
        
        return len(expired_sessions)
```

### 3.2 요청 제한 (Rate Limiting)

```python
from collections import defaultdict
import time

class RateLimiter:
    """요청 제한 시스템"""
    
    def __init__(self):
        self.limits = {
            "api_general": {"requests": 60, "window": 60},      # 분당 60회
            "fortune_generation": {"requests": 10, "window": 3600},  # 시간당 10회
            "websocket_messages": {"requests": 300, "window": 60},   # 분당 300개
            "session_creation": {"requests": 5, "window": 300}       # 5분당 5개
        }
        
        self.counters = defaultdict(lambda: defaultdict(list))
        
    def is_allowed(self, key: str, limit_type: str, 
                   identifier: str = None) -> Tuple[bool, Dict]:
        """요청 허용 여부 확인"""
        if limit_type not in self.limits:
            return True, {}
        
        limit_config = self.limits[limit_type]
        max_requests = limit_config["requests"]
        time_window = limit_config["window"]
        
        # 식별자 생성 (IP 또는 세션 ID)
        rate_key = f"{limit_type}:{identifier or key}"
        current_time = time.time()
        
        # 시간 윈도우 외의 요청 제거
        self.counters[rate_key] = [
            timestamp for timestamp in self.counters[rate_key]
            if current_time - timestamp < time_window
        ]
        
        # 현재 요청 수 확인
        current_requests = len(self.counters[rate_key])
        
        if current_requests >= max_requests:
            # 다음 재시도 가능 시간 계산
            oldest_request = min(self.counters[rate_key])
            reset_time = oldest_request + time_window
            
            return False, {
                "error": "Rate limit exceeded",
                "limit": max_requests,
                "window": time_window,
                "current": current_requests,
                "reset_time": reset_time
            }
        
        # 요청 기록
        self.counters[rate_key].append(current_time)
        
        return True, {
            "limit": max_requests,
            "remaining": max_requests - current_requests - 1,
            "window": time_window,
            "reset_time": current_time + time_window
        }
    
    def get_rate_limit_info(self, key: str, limit_type: str) -> Dict:
        """현재 요청 제한 상태 조회"""
        if limit_type not in self.limits:
            return {}
        
        limit_config = self.limits[limit_type]
        rate_key = f"{limit_type}:{key}"
        current_time = time.time()
        
        # 유효한 요청만 계산
        valid_requests = [
            timestamp for timestamp in self.counters[rate_key]
            if current_time - timestamp < limit_config["window"]
        ]
        
        return {
            "limit": limit_config["requests"],
            "remaining": max(0, limit_config["requests"] - len(valid_requests)),
            "window": limit_config["window"],
            "current": len(valid_requests)
        }
```

## 4. 입력 검증 및 보안

### 4.1 데이터 검증

```python
from pydantic import BaseModel, validator
import re
from typing import Optional, List

class SecureUserProfile(BaseModel):
    """보안이 강화된 사용자 프로필 모델"""
    
    name: Optional[str] = None
    birth_date: Optional[str] = None
    birth_time: Optional[str] = None
    birth_location: Optional[str] = None
    zodiac_sign: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            # 길이 제한
            if len(v) < 1 or len(v) > 20:
                raise ValueError("이름은 1-20자 사이여야 합니다")
            
            # 특수문자 제한
            if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', v):
                raise ValueError("이름에는 한글, 영문, 숫자만 사용할 수 있습니다")
                
        return v
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v is not None:
            # 날짜 형식 검증
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
                raise ValueError("생년월일은 YYYY-MM-DD 형식이어야 합니다")
            
            # 날짜 범위 검증
            try:
                from datetime import datetime
                date_obj = datetime.strptime(v, '%Y-%m-%d')
                current_year = datetime.now().year
                
                if date_obj.year < 1900 or date_obj.year > current_year:
                    raise ValueError("올바른 생년월일을 입력해주세요")
                    
            except ValueError as e:
                raise ValueError("올바른 날짜 형식이 아닙니다")
                
        return v
    
    @validator('birth_time')
    def validate_birth_time(cls, v):
        if v is not None:
            if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
                raise ValueError("시간은 HH:MM 형식이어야 합니다")
        return v
    
    @validator('zodiac_sign')
    def validate_zodiac_sign(cls, v):
        if v is not None:
            valid_signs = [
                'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
            ]
            if v not in valid_signs:
                raise ValueError("올바른 별자리를 선택해주세요")
        return v

class SecureChatMessage(BaseModel):
    """보안이 강화된 채팅 메시지 모델"""
    
    message: str
    session_id: str
    
    @validator('message')
    def validate_message(cls, v):
        # 길이 제한
        if len(v.strip()) < 1:
            raise ValueError("메시지가 너무 짧습니다")
        if len(v) > 500:
            raise ValueError("메시지가 너무 깁니다 (500자 제한)")
        
        # HTML 태그 제거
        v = re.sub(r'<[^>]+>', '', v)
        
        # 연속 공백 정리
        v = re.sub(r'\s+', ' ', v).strip()
        
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        # UUID 형식 검증
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        if not re.match(uuid_pattern, v, re.IGNORECASE):
            raise ValueError("잘못된 세션 ID 형식입니다")
        return v
```

### 4.2 SQL Injection 방지

```python
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

class SecureQueryExecutor:
    """안전한 쿼리 실행기"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    def execute_safe_query(self, query: str, params: Dict = None) -> List:
        """매개변수화된 쿼리 실행"""
        try:
            # 매개변수 검증
            if params:
                self._validate_parameters(params)
            
            # 쿼리 실행 (SQLAlchemy ORM 사용 권장)
            result = self.db.execute(text(query), params or {})
            return result.fetchall()
            
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            raise
    
    def _validate_parameters(self, params: Dict):
        """매개변수 검증"""
        for key, value in params.items():
            # 키 이름 검증
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValueError(f"Invalid parameter name: {key}")
            
            # 값 타입 검증
            if isinstance(value, str):
                # 문자열 길이 제한
                if len(value) > 1000:
                    raise ValueError(f"Parameter {key} is too long")
                
                # 위험한 패턴 검사
                dangerous_patterns = [
                    r';\s*(drop|delete|truncate|update|insert)',
                    r'union\s+select',
                    r'<script',
                    r'javascript:',
                    r'exec\s*\(',
                    r'eval\s*\('
                ]
                
                for pattern in dangerous_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise ValueError(f"Suspicious content in parameter {key}")
```

### 4.3 XSS 방지

```python
import html
import bleach
from typing import Any

class XSSProtection:
    """XSS 공격 방지"""
    
    def __init__(self):
        # 허용할 HTML 태그 (최소한으로 제한)
        self.allowed_tags = []  # 운세 앱에서는 HTML 태그 불허
        self.allowed_attributes = {}
        
    def sanitize_input(self, content: Any) -> str:
        """입력 내용 정화"""
        if not isinstance(content, str):
            content = str(content)
        
        # HTML 엔티티 인코딩
        content = html.escape(content, quote=True)
        
        # 추가 정화 (bleach 사용)
        content = bleach.clean(
            content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )
        
        return content
    
    def sanitize_output(self, content: str) -> str:
        """출력 내용 정화"""
        # 운세 결과는 신뢰할 수 있는 소스이므로 기본적인 검증만
        return html.escape(content, quote=False)
    
    def validate_json_input(self, json_data: Dict) -> Dict:
        """JSON 입력 검증 및 정화"""
        if isinstance(json_data, dict):
            return {
                key: self.sanitize_input(value) if isinstance(value, str) else value
                for key, value in json_data.items()
            }
        return json_data
```

## 5. 데이터 암호화 및 개인정보 보호

### 5.1 데이터 암호화

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    """데이터 암호화 관리"""
    
    def __init__(self, encryption_key: str = None):
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    @classmethod
    def derive_key_from_password(cls, password: str, salt: bytes = None) -> bytes:
        """비밀번호로부터 키 파생"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """민감한 데이터 암호화"""
        if not data:
            return data
        
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """민감한 데이터 복호화"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            return ""  # 복호화 실패시 빈 문자열 반환
    
    def hash_data(self, data: str) -> str:
        """데이터 해싱 (단방향)"""
        return hashlib.sha256(data.encode()).hexdigest()
```

### 5.2 개인정보 최소화

```python
class PrivacyManager:
    """개인정보 관리"""
    
    def __init__(self):
        self.encryption = DataEncryption()
        
    def minimize_user_data(self, user_data: Dict) -> Dict:
        """사용자 데이터 최소화"""
        # 필수 데이터만 보관
        minimal_data = {}
        
        # 별자리만 저장하고 정확한 생년월일은 저장하지 않음
        if 'birth_date' in user_data:
            minimal_data['zodiac_sign'] = self._calculate_zodiac(user_data['birth_date'])
        
        # 이름은 해싱하여 저장
        if 'name' in user_data and user_data['name']:
            minimal_data['name_hash'] = self.encryption.hash_data(user_data['name'])
        
        # 선택적 데이터는 암호화하여 저장
        optional_fields = ['birth_time', 'birth_location']
        for field in optional_fields:
            if field in user_data and user_data[field]:
                minimal_data[f'{field}_encrypted'] = self.encryption.encrypt_sensitive_data(
                    user_data[field]
                )
        
        return minimal_data
    
    def _calculate_zodiac(self, birth_date: str) -> str:
        """생년월일로부터 별자리 계산"""
        # 날짜 파싱하여 별자리 계산 로직
        month, day = birth_date.split('-')[1:3]
        month, day = int(month), int(day)
        
        zodiac_dates = [
            (1, 20, 'capricorn'), (2, 19, 'aquarius'), (3, 21, 'pisces'),
            (4, 20, 'aries'), (5, 21, 'taurus'), (6, 21, 'gemini'),
            (7, 23, 'cancer'), (8, 23, 'leo'), (9, 23, 'virgo'),
            (10, 23, 'libra'), (11, 22, 'scorpio'), (12, 22, 'sagittarius')
        ]
        
        for i, (end_month, end_day, sign) in enumerate(zodiac_dates):
            if month < end_month or (month == end_month and day <= end_day):
                return sign
        
        return 'capricorn'  # 12월 22일 이후
    
    def anonymize_chat_history(self, chat_data: List[Dict]) -> List[Dict]:
        """채팅 기록 익명화"""
        anonymized_data = []
        
        for message in chat_data:
            anonymized_message = {
                'timestamp': message.get('timestamp'),
                'sender_type': message.get('sender_type'),
                'content_type': message.get('content_type'),
                'message_length': len(message.get('content', '')),
                'emotion': message.get('live2d_emotion'),
                'topic': self._extract_topic(message.get('content', ''))
            }
            anonymized_data.append(anonymized_message)
        
        return anonymized_data
    
    def _extract_topic(self, content: str) -> str:
        """메시지에서 주제 추출 (개인정보 제외)"""
        topics = {
            'fortune': ['운세', '타로', '별자리', '점'],
            'greeting': ['안녕', '처음', '시작'],
            'question': ['궁금', '물어', '질문'],
            'emotion': ['기쁘', '슬프', '화', '좋']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in content for keyword in keywords):
                return topic
        
        return 'general'
```

## 6. 보안 모니터링 및 로깅

### 6.1 보안 이벤트 로깅

```python
import logging
from datetime import datetime
import json

class SecurityLogger:
    """보안 이벤트 로깅"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # 파일 핸들러 설정
        handler = logging.FileHandler('logs/security.log')
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_content_filter_event(self, session_id: str, content: str, 
                                filter_result: str, client_ip: str = None):
        """콘텐츠 필터링 이벤트 로그"""
        event_data = {
            'event_type': 'content_filter',
            'session_id': session_id,
            'content_hash': hashlib.sha256(content.encode()).hexdigest(),
            'filter_result': filter_result,
            'client_ip': client_ip,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"CONTENT_FILTER | {json.dumps(event_data)}")
    
    def log_rate_limit_event(self, identifier: str, limit_type: str, 
                           client_ip: str = None):
        """요청 제한 이벤트 로그"""
        event_data = {
            'event_type': 'rate_limit_exceeded',
            'identifier': identifier,
            'limit_type': limit_type,
            'client_ip': client_ip,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.warning(f"RATE_LIMIT | {json.dumps(event_data)}")
    
    def log_security_violation(self, event_type: str, details: Dict, 
                             severity: str = 'medium'):
        """보안 위반 이벤트 로그"""
        event_data = {
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if severity == 'high':
            self.logger.critical(f"SECURITY_VIOLATION | {json.dumps(event_data)}")
        elif severity == 'medium':
            self.logger.warning(f"SECURITY_VIOLATION | {json.dumps(event_data)}")
        else:
            self.logger.info(f"SECURITY_VIOLATION | {json.dumps(event_data)}")
```

이 보안 아키텍처는 Live2D 운세 앱의 안전한 운영을 위한 포괄적인 보안 방안을 제공하며, 사용자의 개인정보를 보호하면서도 안전하고 건전한 서비스 환경을 보장합니다.
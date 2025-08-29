# Live2D 운세 앱 API 설계 문서

## 1. API 아키텍처 개요

### 1.1 API 설계 원칙
- **RESTful 설계**: HTTP 메서드와 상태 코드를 명확히 사용
- **WebSocket 실시간 통신**: Live2D 캐릭터와의 실시간 상호작용
- **버전 관리**: `/api/v1` 접두사로 API 버전 관리
- **보안 우선**: 모든 요청에 대한 검증 및 필터링
- **응답 일관성**: 통일된 응답 형식 사용

### 1.2 기술 스택
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **WebSocket**: 실시간 양방향 통신
- **Pydantic**: 데이터 검증 및 직렬화
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **uvicorn**: ASGI 서버

## 2. RESTful API 엔드포인트

### 2.1 운세 관련 API

#### 2.1.1 일일 운세 조회
```http
GET /api/v1/fortune/daily
```

**요청 파라미터:**
```python
# Query Parameters
birth_date: str (YYYY-MM-DD, optional)
zodiac: str (optional, enum: aries, taurus, gemini, ...)
```

**응답 스키마:**
```json
{
  "success": true,
  "data": {
    "date": "2025-08-22",
    "overall_fortune": {
      "score": 85,
      "grade": "excellent",
      "description": "오늘은 모든 일이 순조롭게 진행될 것 같아요!"
    },
    "categories": {
      "love": {"score": 80, "description": "연애운이 상승세에..."},
      "money": {"score": 90, "description": "재정 관리에 신경 쓰면..."},
      "health": {"score": 85, "description": "건강한 하루가 될 것..."},
      "work": {"score": 75, "description": "업무에서 좋은 성과..."}
    },
    "lucky_items": ["파란색 볼펜", "커피"],
    "lucky_numbers": [7, 15, 23],
    "lucky_colors": ["파란색", "노란색"],
    "advice": "오늘은 새로운 도전을 해보세요!",
    "warnings": ["급한 결정은 피하세요"]
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2025-08-22T10:30:00Z"
  }
}
```

#### 2.1.2 타로 운세 요청
```http
POST /api/v1/fortune/tarot
```

**요청 스키마:**
```json
{
  "question": "이번 달 연애운은 어떨까요?",
  "question_type": "love", // love, money, health, work, general
  "user_info": {
    "birth_date": "1995-03-15",
    "zodiac": "pisces"
  }
}
```

**응답 스키마:**
```json
{
  "success": true,
  "data": {
    "reading_id": "uuid",
    "question": "이번 달 연애운은 어떨까요?",
    "cards": [
      {
        "position": "past",
        "card_name": "The Lovers",
        "card_meaning": "사랑과 선택",
        "interpretation": "과거에 있었던 감정적 결정들이...",
        "image_url": "/static/tarot/lovers.jpg"
      },
      {
        "position": "present", 
        "card_name": "Three of Cups",
        "card_meaning": "우정과 축하",
        "interpretation": "현재 주변 사람들과의 관계가...",
        "image_url": "/static/tarot/three_cups.jpg"
      },
      {
        "position": "future",
        "card_name": "The Star",
        "card_meaning": "희망과 영감",
        "interpretation": "앞으로 밝은 희망이...",
        "image_url": "/static/tarot/star.jpg"
      }
    ],
    "overall_interpretation": "전체적으로 긍정적인 연애운이 기다리고 있어요...",
    "advice": "마음을 열고 새로운 만남에 기대해보세요",
    "live2d_emotion": "mystical",
    "live2d_motion": "card_draw"
  }
}
```

#### 2.1.3 별자리 운세 조회
```http
GET /api/v1/fortune/zodiac/{zodiac_sign}
```

**URL 파라미터:**
- `zodiac_sign`: aries, taurus, gemini, cancer, leo, virgo, libra, scorpio, sagittarius, capricorn, aquarius, pisces

**Query 파라미터:**
```python
period: str = "daily"  # daily, weekly, monthly
```

**응답 스키마:**
```json
{
  "success": true,
  "data": {
    "zodiac_sign": "pisces",
    "period": "daily",
    "date_range": "2025-08-22",
    "personality_traits": [
      "감성적", "직관적", "창의적", "공감 능력이 뛰어남"
    ],
    "fortune": {
      "love": {"score": 88, "description": "물고기자리의 로맨틱한 성향이..."},
      "career": {"score": 75, "description": "창의적인 아이디어가..."},
      "health": {"score": 80, "description": "정신적 휴식이 필요한..."},
      "finance": {"score": 70, "description": "신중한 투자가..."}
    },
    "compatibility": {
      "best_match": ["cancer", "scorpio"],
      "good_match": ["taurus", "capricorn"],
      "challenging": ["gemini", "sagittarius"]
    },
    "lucky_elements": {
      "color": "바다색",
      "number": 12,
      "stone": "아쿠아마린",
      "direction": "서쪽"
    }
  }
}
```

### 2.2 사용자 관련 API

#### 2.2.1 사용자 프로필 생성/수정
```http
POST /api/v1/user/profile
PUT /api/v1/user/profile
```

**요청 스키마:**
```json
{
  "name": "사용자 이름",
  "birth_date": "1995-03-15",
  "birth_time": "14:30", // optional
  "birth_location": "서울", // optional
  "zodiac_sign": "pisces",
  "preferences": {
    "fortune_types": ["daily", "tarot"],
    "notification_time": "09:00",
    "theme": "light"
  }
}
```

#### 2.2.2 운세 히스토리 조회
```http
GET /api/v1/user/fortune-history
```

**Query 파라미터:**
```python
page: int = 1
limit: int = 20
fortune_type: str = "all"  # all, daily, tarot, zodiac
date_from: str = ""  # YYYY-MM-DD
date_to: str = ""    # YYYY-MM-DD
```

### 2.3 채팅 관련 API

#### 2.3.1 채팅 세션 생성
```http
POST /api/v1/chat/session
```

**응답 스키마:**
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "character_name": "미라",
    "session_expires_at": "2025-08-22T12:30:00Z",
    "initial_message": "안녕하세요! 오늘 운세가 궁금하신가요?"
  }
}
```

#### 2.3.2 채팅 히스토리 조회
```http
GET /api/v1/chat/history/{session_id}
```

### 2.4 Live2D 관련 API

#### 2.4.1 캐릭터 정보 조회
```http
GET /api/v1/live2d/character/info
```

**응답 스키마:**
```json
{
  "success": true,
  "data": {
    "character_name": "미라",
    "model_path": "/static/live2d/mira/mira.model3.json",
    "emotions": {
      "neutral": 0,
      "joy": 1,
      "thinking": 2,
      "concern": 3,
      "surprise": 4,
      "mystical": 5,
      "comfort": 6,
      "playful": 7
    },
    "motions": {
      "greeting": "motions/greeting.motion3.json",
      "card_draw": "motions/card_draw.motion3.json",
      "crystal_gaze": "motions/crystal_gaze.motion3.json",
      "blessing": "motions/blessing.motion3.json",
      "special_reading": "motions/special_reading.motion3.json",
      "thinking_pose": "motions/thinking_pose.motion3.json"
    }
  }
}
```

## 3. WebSocket 실시간 통신

### 3.1 WebSocket 연결 엔드포인트
```
ws://localhost:8000/ws/chat/{session_id}
```

### 3.2 WebSocket 메시지 타입

#### 3.2.1 클라이언트 → 서버 메시지

**텍스트 입력:**
```json
{
  "type": "text_input",
  "data": {
    "message": "오늘 운세 봐주세요",
    "timestamp": "2025-08-22T10:30:00Z"
  }
}
```

**음성 데이터:**
```json
{
  "type": "audio_input",
  "data": {
    "audio_data": "base64_encoded_audio",
    "format": "wav",
    "sample_rate": 16000
  }
}
```

**운세 요청:**
```json
{
  "type": "fortune_request", 
  "data": {
    "fortune_type": "daily", // daily, tarot, zodiac
    "question": "오늘 연애운은?", // tarot인 경우
    "additional_info": {}
  }
}
```

**인터럽트 신호:**
```json
{
  "type": "interrupt",
  "data": {
    "reason": "user_stop"
  }
}
```

#### 3.2.2 서버 → 클라이언트 메시지

**텍스트 응답 (스트리밍):**
```json
{
  "type": "text_response",
  "data": {
    "message": "오늘 운세를 봐드릴게요!",
    "is_complete": false,
    "live2d_emotion": "mystical",
    "live2d_motion": "crystal_gaze"
  }
}
```

**운세 결과:**
```json
{
  "type": "fortune_result",
  "data": {
    "fortune_type": "daily",
    "result": {
      // fortune API 응답과 동일한 구조
    },
    "live2d_emotion": "joy",
    "live2d_motion": "blessing"
  }
}
```

**Live2D 액션:**
```json
{
  "type": "live2d_action",
  "data": {
    "emotion": "thinking",
    "motion": "thinking_pose",
    "duration": 3000
  }
}
```

**음성 응답:**
```json
{
  "type": "audio_response",
  "data": {
    "audio_url": "/static/audio/response_123.mp3",
    "text": "응답 텍스트",
    "duration": 5.2
  }
}
```

**에러 메시지:**
```json
{
  "type": "error",
  "data": {
    "error_code": "CONTENT_FILTERED",
    "message": "죄송해요, 그런 질문에는 답변드릴 수 없어요.",
    "live2d_emotion": "concern"
  }
}
```

### 3.3 연결 상태 관리

**연결 상태:**
- `connecting`: 연결 중
- `connected`: 연결됨
- `disconnected`: 연결 해제됨
- `error`: 연결 오류

**재연결 로직:**
- 최대 5회 재시도
- 지수 백오프 (1s, 2s, 4s, 8s, 16s)
- 사용자 명시적 연결 해제시 재연결 안함

## 4. 응답 형식 표준화

### 4.1 성공 응답 형식
```json
{
  "success": true,
  "data": {
    // 실제 응답 데이터
  },
  "metadata": {
    "request_id": "uuid",
    "timestamp": "2025-08-22T10:30:00Z",
    "version": "1.0.0"
  }
}
```

### 4.2 에러 응답 형식
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다",
    "details": {
      "field": "birth_date",
      "reason": "Invalid date format"
    }
  },
  "metadata": {
    "request_id": "uuid", 
    "timestamp": "2025-08-22T10:30:00Z"
  }
}
```

### 4.3 HTTP 상태 코드 매핑

| 상태 코드 | 사용 상황 |
|-----------|-----------|
| 200 | 성공적인 요청 처리 |
| 201 | 리소스 생성 성공 |
| 400 | 잘못된 요청 (validation error) |
| 401 | 인증 실패 |
| 403 | 권한 없음 (content filtered) |
| 404 | 리소스 없음 |
| 429 | 요청 제한 초과 |
| 500 | 서버 내부 오류 |

## 5. API 보안 정책

### 5.1 요청 제한 (Rate Limiting)
- **일반 API**: 분당 60회
- **운세 생성**: 시간당 10회
- **WebSocket 메시지**: 초당 5개

### 5.2 콘텐츠 필터링
- 성적, 폭력적 내용 차단
- 개인정보 수집 시도 차단
- 정치적, 종교적 민감 내용 차단
- 운세 영역 외 전문적 조언 차단

### 5.3 입력 검증
- SQL Injection 방지
- XSS 공격 방지
- 파일 업로드 제한
- 요청 크기 제한 (10MB)

## 6. API 버전 관리

### 6.1 버전 전략
- URL 경로 버전: `/api/v1/`
- 하위 호환성 보장 기간: 6개월
- 주요 변경시 새 버전 릴리스

### 6.2 변경 사항 알림
- API 문서 업데이트
- 클라이언트 알림 시스템
- Deprecation 경고

## 7. 성능 최적화

### 7.1 캐싱 전략
- **일일 운세**: 24시간 캐시
- **별자리 운세**: 주간/월간 캐시
- **사용자 프로필**: 메모리 캐시
- **Live2D 리소스**: 브라우저 캐시

### 7.2 응답 최적화
- 불필요한 데이터 제거
- 압축 전송 (gzip)
- 이미지 최적화
- 지연 로딩

## 8. 모니터링 및 로깅

### 8.1 API 메트릭
- 응답 시간 추적
- 에러율 모니터링
- 사용량 통계
- 성능 병목 지점

### 8.2 로깅 정책
- 모든 요청/응답 로깅
- 에러 상세 로깅
- 보안 이벤트 로깅
- 개인정보 마스킹
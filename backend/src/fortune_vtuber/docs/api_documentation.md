# Fortune VTuber Backend API Documentation

## 개요

Fortune VTuber Backend는 Live2D 기반 운세 상담 VTuber 서비스를 위한 완전 기능형 백엔드 API입니다.

### 주요 특징

- **4가지 운세 타입**: 일일운세, 타로, 별자리, 사주
- **Live2D 통합**: 실시간 감정/모션 제어
- **WebSocket 실시간 통신**: 채팅 및 상태 동기화
- **콘텐츠 필터링**: 부적절한 내용 자동 차단
- **사용자 관리**: 익명 및 등록 사용자 지원

## API 엔드포인트

### 1. 운세 API (`/fortune`)

#### 1.1 일일 운세 (v2)

**POST** `/fortune/v2/daily`

사용자 개인화된 일일 운세를 생성합니다.

```json
// Request
{
  "birth_date": "1995-03-15",
  "zodiac": "pisces",
  "user_uuid": "user-uuid-here",
  "force_regenerate": false
}

// Response
{
  "success": true,
  "data": {
    "fortune_type": "daily",
    "date": "2025-08-22",
    "overall_fortune": {
      "score": 85,
      "grade": "good",
      "description": "오늘은 좋은 하루가 될 것 같아요!"
    },
    "categories": {
      "love": {"score": 80, "grade": "good", "description": "연애운이 상승세..."},
      "money": {"score": 90, "grade": "excellent", "description": "재정 관리에..."},
      "health": {"score": 85, "grade": "good", "description": "건강한 하루..."},
      "work": {"score": 75, "grade": "good", "description": "업무에서 좋은..."}
    },
    "lucky_elements": {
      "colors": ["파란색", "노란색"],
      "numbers": [7, 15, 23],
      "items": ["커피", "볼펜"]
    },
    "advice": "오늘은 새로운 도전을 해보세요!",
    "warnings": ["급한 결정은 피하세요"],
    "live2d_emotion": "joy",
    "live2d_motion": "blessing"
  }
}
```

#### 1.2 타로 운세 (v2)

**POST** `/fortune/v2/tarot?user_uuid={uuid}`

질문 기반 타로 카드 운세를 생성합니다.

```json
// Request
{
  "question": "이번 달 연애운은 어떨까요?",
  "question_type": "love",
  "card_count": 3
}

// Response
{
  "success": true,
  "data": {
    "fortune_type": "tarot",
    "question": "이번 달 연애운은 어떨까요?",
    "question_type": "love",
    "tarot_cards": [
      {
        "position": "past",
        "card_name": "The Lovers",
        "card_meaning": "사랑과 선택",
        "interpretation": "과거에 있었던 감정적 결정들이...",
        "is_reversed": false,
        "keywords": ["사랑", "선택", "조화"],
        "image_url": "/static/tarot/lovers.jpg"
      }
    ],
    "advice": "마음을 열고 새로운 만남에 기대해보세요",
    "live2d_emotion": "mystical",
    "live2d_motion": "card_draw"
  }
}
```

#### 1.3 별자리 운세 (v2)

**POST** `/fortune/v2/zodiac`

별자리별 운세를 생성합니다.

```json
// Request
{
  "period": "daily",
  "user_uuid": "user-uuid-here"
}

// Response
{
  "success": true,
  "data": {
    "fortune_type": "zodiac",
    "zodiac_sign": "pisces",
    "period": "daily",
    "zodiac_info": {
      "personality_traits": ["감성적", "직관적", "창의적"],
      "element": "물",
      "lucky_stone": "아쿠아마린",
      "lucky_direction": "서쪽",
      "compatibility": {
        "best_match": ["cancer", "scorpio"],
        "good_match": ["taurus", "capricorn"]
      }
    }
  }
}
```

#### 1.4 사주 운세 (v2)

**POST** `/fortune/v2/saju`

생년월일시 기반 사주 운세를 생성합니다.

```json
// Request
{
  "birth_date": "1995-03-15",
  "birth_time": "14:30",
  "birth_location": "서울",
  "user_uuid": "user-uuid-here"
}

// Response
{
  "success": true,
  "data": {
    "fortune_type": "saju",
    "saju_elements": [
      {
        "pillar": "년주",
        "heavenly_stem": "을",
        "earthly_branch": "해",
        "element": "목",
        "meaning": "조상, 부모의 영향"
      }
    ],
    "element_balance": {
      "목": 2, "화": 1, "토": 0, "금": 1, "수": 0
    }
  }
}
```

### 2. Live2D API (`/live2d`)

#### 2.1 세션 생성

**POST** `/live2d/session`

```json
// Request
{
  "session_id": "session-uuid",
  "user_uuid": "user-uuid"
}
```

#### 2.2 감정 변경

**POST** `/live2d/emotion`

```json
// Request
{
  "session_id": "session-uuid",
  "emotion": "joy",
  "duration": 5000
}
```

사용 가능한 감정: `neutral`, `joy`, `thinking`, `concern`, `surprise`, `mystical`, `comfort`, `playful`

#### 2.3 모션 실행

**POST** `/live2d/motion`

```json
// Request
{
  "session_id": "session-uuid",
  "motion": "card_draw",
  "duration": 4000
}
```

사용 가능한 모션: `greeting`, `card_draw`, `crystal_gaze`, `blessing`, `special_reading`, `thinking_pose`

#### 2.4 운세 반응

**POST** `/live2d/react/fortune`

운세 결과에 따라 자동으로 적절한 감정과 모션을 설정합니다.

```json
// Request
{
  "session_id": "session-uuid",
  "fortune_result": {
    "fortune_type": "daily",
    "overall_fortune": {"score": 85, "grade": "good"}
  }
}
```

### 3. 사용자 API (`/user`)

#### 3.1 익명 사용자 생성

**POST** `/user/anonymous`

```json
// Response
{
  "success": true,
  "data": {
    "user": {
      "uuid": "user-uuid",
      "name": "익명 사용자",
      "created_at": "2025-08-22T10:30:00Z"
    },
    "session": {
      "session_id": "session-uuid",
      "session_type": "anonymous"
    }
  }
}
```

#### 3.2 사용자 프로필 생성/수정

**POST** `/user/profile`
**PUT** `/user/profile/{user_uuid}`

```json
// Request
{
  "name": "사용자 이름",
  "birth_date": "1995-03-15",
  "birth_time": "14:30",
  "zodiac_sign": "pisces"
}
```

#### 3.3 선호도 설정

**PUT** `/user/preferences/{user_uuid}`

```json
// Request
{
  "fortune_types": ["daily", "tarot"],
  "notification_time": "09:00",
  "theme": "light",
  "language": "ko"
}
```

### 4. WebSocket API

#### 4.1 채팅 WebSocket

**WebSocket** `/ws/chat/{session_id}`

실시간 채팅 통신을 위한 WebSocket 연결입니다.

```json
// Client → Server
{
  "type": "text_input",
  "data": {
    "message": "오늘 운세 봐주세요",
    "timestamp": "2025-08-22T10:30:00Z"
  }
}

// Server → Client
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

#### 4.2 Live2D WebSocket

**WebSocket** `/ws/live2d/{session_id}`

Live2D 캐릭터 상태 동기화를 위한 WebSocket 연결입니다.

```json
// Server → Client (Live2D 액션)
{
  "type": "live2d_action",
  "data": {
    "emotion": "thinking",
    "motion": "thinking_pose",
    "duration": 3000
  }
}
```

## 콘텐츠 필터링

모든 사용자 입력은 다층 필터링 시스템을 통과합니다:

- **성적 내용**: 자동 차단
- **폭력적 내용**: 자동 차단  
- **혐오 발언**: 자동 차단
- **개인정보 수집**: 자동 차단
- **운세 관련 내용**: 우선 허용

### 필터링 응답

```json
{
  "type": "error",
  "data": {
    "error_code": "CONTENT_FILTERED",
    "message": "죄송해요, 그런 질문에는 답변드릴 수 없어요.",
    "suggestion": "운세 상담이나 재미있는 이야기는 어떠세요?",
    "live2d_emotion": "concern"
  }
}
```

## 헬스 체크

### 기본 헬스 체크

**GET** `/health`

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "fortune-vtuber-backend",
    "version": "1.0.0"
  }
}
```

### 상세 헬스 체크

**GET** `/health/detailed`

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "components": {
      "database": {"status": "healthy", "connection_count": 5},
      "api": {"status": "healthy"},
      "websocket": {"status": "healthy"}
    }
  }
}
```

### 통합 테스트

**POST** `/health/integration-test`

전체 시스템의 통합 테스트를 실행합니다.

```json
{
  "success": true,
  "data": {
    "summary": {
      "total": 6,
      "passed": 6,
      "failed": 0,
      "success_rate": "100.0%"
    },
    "tests": {
      "fortune_engines": {"status": "passed"},
      "api_endpoints": {"status": "passed"},
      "live2d_integration": {"status": "passed"}
    }
  }
}
```

## 에러 코드

| 코드 | 설명 |
|------|------|
| `VALIDATION_ERROR` | 요청 데이터 검증 실패 |
| `CONTENT_FILTERED` | 콘텐츠 필터링으로 차단됨 |
| `SESSION_NOT_FOUND` | 세션을 찾을 수 없음 |
| `USER_NOT_FOUND` | 사용자를 찾을 수 없음 |
| `SERVICE_UNHEALTHY` | 서비스가 비정상 상태 |
| `RATE_LIMITED` | 요청 제한 초과 |

## 사용 예시

### 기본 운세 상담 플로우

1. **익명 사용자 생성**
```bash
curl -X POST http://localhost:8000/user/anonymous
```

2. **Live2D 세션 생성**
```bash
curl -X POST http://localhost:8000/live2d/session \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session-123","user_uuid":"user-456"}'
```

3. **일일 운세 요청**
```bash
curl -X POST http://localhost:8000/fortune/v2/daily \
  -H "Content-Type: application/json" \
  -d '{"birth_date":"1995-03-15","zodiac":"pisces","user_uuid":"user-456"}'
```

4. **운세 결과로 Live2D 반응**
```bash
curl -X POST http://localhost:8000/live2d/react/fortune \
  -H "Content-Type: application/json" \
  -d '{"session_id":"session-123","fortune_result":{...}}'
```

### WebSocket 연결

```javascript
// 채팅 WebSocket 연결
const chatWs = new WebSocket('ws://localhost:8000/ws/chat/session-123');

chatWs.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'text_response') {
    console.log('미라:', data.data.message);
    // Live2D 감정/모션 업데이트
    updateLive2D(data.data.live2d_emotion, data.data.live2d_motion);
  }
};

// 메시지 전송
chatWs.send(JSON.stringify({
  type: 'text_input',
  data: {
    message: '오늘 운세 궁금해요',
    timestamp: new Date().toISOString()
  }
}));
```

## 개발 및 테스트

### 개발 서버 실행

```bash
cd /mnt/d/study/VTuber/project/backend
python -m uvicorn fortune_vtuber.main:app --reload --host 0.0.0.0 --port 8000
```

### API 문서 확인

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 통합 테스트 실행

```bash
# API를 통한 테스트
curl -X POST http://localhost:8000/health/integration-test

# 또는 직접 실행
python -m fortune_vtuber.core.integration_test
```

## 배포

### Docker 배포

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "fortune_vtuber.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 환경 변수

```bash
export ENVIRONMENT=production
export DATABASE_URL=postgresql://user:pass@localhost/fortune_vtuber
export SECRET_KEY=your-secret-key
export CORS_ORIGINS=https://yourdomain.com
```

이 API 문서는 Fortune VTuber Backend의 모든 주요 기능을 다루며, 완전히 동작하는 운세 상담 VTuber 서비스를 구축할 수 있도록 설계되었습니다.
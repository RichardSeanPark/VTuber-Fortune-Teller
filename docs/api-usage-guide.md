# 📚 Live2D 운세 앱 API 사용법 가이드

> **최종 업데이트**: 2025년 8월 22일  
> **API 버전**: v1.0.0  
> **대상**: 프론트엔드 개발자, 클라이언트 개발자, API 통합 담당자

## 📋 목차

1. [시작하기](#시작하기)
2. [인증 및 세션 관리](#인증-및-세션-관리)
3. [운세 API](#운세-api)
4. [채팅 및 WebSocket](#채팅-및-websocket)
5. [Live2D 통합](#live2d-통합)
6. [에러 처리](#에러-처리)
7. [Rate Limiting](#rate-limiting)
8. [SDK 및 라이브러리](#sdk-및-라이브러리)
9. [예제 코드](#예제-코드)
10. [FAQ](#faq)

## 🚀 시작하기

### 기본 정보

```yaml
Base URL: https://api.fortune-vtuber.com
API Version: v1
Content-Type: application/json
```

### 환경별 엔드포인트

| 환경 | Base URL | 용도 |
|------|----------|------|
| **Development** | `http://localhost:8080` | 로컬 개발 |
| **Staging** | `https://staging-api.fortune-vtuber.com` | 테스트 및 검증 |
| **Production** | `https://api.fortune-vtuber.com` | 프로덕션 서비스 |

### 빠른 시작

```javascript
// 1. 사용자 세션 생성
const sessionResponse = await fetch('https://api.fortune-vtuber.com/api/v1/user/session', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
});
const { session_id } = await sessionResponse.json();

// 2. 운세 조회
const fortuneResponse = await fetch('https://api.fortune-vtuber.com/api/v1/fortune/daily?birth_date=1995-03-15&zodiac=pisces', {
  headers: {
    'X-Session-ID': session_id
  }
});
const fortuneData = await fortuneResponse.json();
console.log(fortuneData);
```

## 🔑 인증 및 세션 관리

### 세션 기반 인증

Fortune VTuber API는 세션 기반 인증을 사용합니다. 모든 API 요청에는 세션 ID가 필요합니다.

#### 1. 세션 생성

```http
POST /api/v1/user/session
Content-Type: application/json
```

**요청 예시:**
```javascript
const response = await fetch('/api/v1/user/session', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'FortuneVTuber-Web/1.0'
  },
  body: JSON.stringify({
    user_agent: navigator.userAgent,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    language: navigator.language
  })
});
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "expires_at": "2025-08-22T14:30:00Z",
    "character_name": "미라",
    "initial_message": "안녕하세요! 오늘 운세가 궁금하신가요?"
  },
  "metadata": {
    "request_id": "req_123456789",
    "timestamp": "2025-08-22T12:30:00Z"
  }
}
```

#### 2. 세션 헤더 사용

모든 후속 요청에 세션 ID를 포함해야 합니다:

```javascript
const headers = {
  'Content-Type': 'application/json',
  'X-Session-ID': 'your-session-id-here'
};
```

#### 3. 세션 유효성 확인

```http
GET /api/v1/user/session/status
X-Session-ID: your-session-id
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "is_valid": true,
    "expires_at": "2025-08-22T14:30:00Z",
    "time_remaining": 7200
  }
}
```

#### 4. 세션 갱신

```http
PUT /api/v1/user/session/renew
X-Session-ID: your-session-id
```

### 사용자 프로필 관리

#### 프로필 정보 설정

```http
PUT /api/v1/user/profile
X-Session-ID: your-session-id
Content-Type: application/json
```

**요청 예시:**
```json
{
  "name": "사용자",
  "birth_date": "1995-03-15",
  "birth_time": "14:30",
  "birth_location": "서울",
  "zodiac_sign": "pisces",
  "preferences": {
    "fortune_types": ["daily", "tarot"],
    "notification_enabled": false,
    "theme": "light"
  }
}
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "profile_id": "profile_123456",
    "name": "사용자",
    "birth_date": "1995-03-15",
    "zodiac_sign": "pisces",
    "preferences": {
      "fortune_types": ["daily", "tarot"],
      "notification_enabled": false,
      "theme": "light"
    },
    "created_at": "2025-08-22T12:30:00Z",
    "updated_at": "2025-08-22T12:30:00Z"
  }
}
```

## 🔮 운세 API

### 1. 일일 운세

가장 기본적인 운세 서비스로, 생년월일과 별자리 기반의 개인화된 일일 운세를 제공합니다.

#### 엔드포인트

```http
GET /api/v1/fortune/daily
X-Session-ID: your-session-id
```

#### 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|----------|------|------|------|------|
| `birth_date` | string | 선택 | 생년월일 (YYYY-MM-DD) | `1995-03-15` |
| `zodiac` | string | 선택 | 별자리 | `pisces` |

#### 사용 예시

```javascript
// 기본 일일 운세 (익명)
const basicFortune = await fetch('/api/v1/fortune/daily', {
  headers: { 'X-Session-ID': sessionId }
});

// 개인화된 일일 운세
const personalizedFortune = await fetch('/api/v1/fortune/daily?birth_date=1995-03-15&zodiac=pisces', {
  headers: { 'X-Session-ID': sessionId }
});

const fortuneData = await personalizedFortune.json();
```

#### 응답 구조

```json
{
  "success": true,
  "data": {
    "date": "2025-08-22",
    "overall_fortune": {
      "score": 85,
      "grade": "excellent",
      "description": "오늘은 모든 일이 순조롭게 진행될 것 같아요! 특히 새로운 시작에 좋은 에너지가 흐르고 있습니다."
    },
    "categories": {
      "love": {
        "score": 80,
        "description": "연애운이 상승세에 있어요. 솔직한 마음을 표현하기 좋은 날입니다."
      },
      "money": {
        "score": 90,
        "description": "재정 관리에 신경 쓰면 좋은 결과가 있을 거예요."
      },
      "health": {
        "score": 85,
        "description": "건강한 하루가 될 것 같아요. 적당한 운동을 추천드려요."
      },
      "work": {
        "score": 75,
        "description": "업무에서 좋은 성과를 거둘 수 있는 날입니다."
      }
    },
    "lucky_items": ["파란색 볼펜", "커피", "작은 화분"],
    "lucky_numbers": [7, 15, 23],
    "lucky_colors": ["파란색", "노란색"],
    "advice": "오늘은 새로운 도전을 해보세요! 당신의 직감을 믿고 행동하면 좋은 결과가 있을 거예요.",
    "warnings": ["급한 결정은 피하세요", "감정적인 대화는 자제해주세요"],
    "live2d_emotion": "joy",
    "live2d_motion": "blessing"
  },
  "metadata": {
    "request_id": "req_daily_123456",
    "timestamp": "2025-08-22T12:30:00Z",
    "cache_hit": false,
    "generation_time": 1.24
  }
}
```

### 2. 타로 카드 운세

3장의 타로 카드를 통한 과거-현재-미래 리딩을 제공합니다.

#### 엔드포인트

```http
POST /api/v1/fortune/tarot
X-Session-ID: your-session-id
Content-Type: application/json
```

#### 요청 구조

```json
{
  "question": "이번 달 연애운은 어떨까요?",
  "question_type": "love",
  "user_info": {
    "birth_date": "1995-03-15",
    "zodiac": "pisces"
  }
}
```

#### 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 가능한 값 |
|----------|------|------|------|-----------|
| `question` | string | 필수 | 타로 질문 | 자유 텍스트 |
| `question_type` | string | 필수 | 질문 유형 | `love`, `money`, `health`, `work`, `general` |
| `user_info.birth_date` | string | 선택 | 생년월일 | YYYY-MM-DD |
| `user_info.zodiac` | string | 선택 | 별자리 | 12성좌 영문명 |

#### 사용 예시

```javascript
const tarotReading = await fetch('/api/v1/fortune/tarot', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': sessionId
  },
  body: JSON.stringify({
    question: "새로운 직장으로 이직하는 것이 좋을까요?",
    question_type: "work",
    user_info: {
      birth_date: "1995-03-15",
      zodiac: "pisces"
    }
  })
});

const tarotData = await tarotReading.json();
```

#### 응답 구조

```json
{
  "success": true,
  "data": {
    "reading_id": "tarot_550e8400-e29b",
    "question": "새로운 직장으로 이직하는 것이 좋을까요?",
    "question_type": "work",
    "cards": [
      {
        "position": "past",
        "card_name": "The Hermit",
        "card_number": 9,
        "suit": "major_arcana",
        "card_meaning": "내면의 지혜와 성찰",
        "interpretation": "과거에 많은 고민과 성찰의 시간을 거쳐오셨군요. 혼자만의 시간을 통해 진정한 자신을 찾아가는 과정이었습니다.",
        "image_url": "/static/tarot/hermit.jpg",
        "reversed": false
      },
      {
        "position": "present",
        "card_name": "Two of Pentacles",
        "card_number": 2,
        "suit": "pentacles",
        "card_meaning": "균형과 변화 관리",
        "interpretation": "현재 여러 가지 선택지 사이에서 균형을 맞추려 노력하고 계시는군요. 변화에 유연하게 대응하는 것이 중요합니다.",
        "image_url": "/static/tarot/two_pentacles.jpg",
        "reversed": false
      },
      {
        "position": "future",
        "card_name": "The Star",
        "card_number": 17,
        "suit": "major_arcana",
        "card_meaning": "희망과 영감",
        "interpretation": "미래에는 밝은 희망과 새로운 기회가 기다리고 있어요. 당신의 꿈을 향해 나아가세요.",
        "image_url": "/static/tarot/star.jpg",
        "reversed": false
      }
    ],
    "overall_interpretation": "과거의 깊은 성찰을 통해 현재의 선택에 직면해 있으며, 미래에는 희망적인 변화가 기다리고 있습니다. 이직에 대한 고민이 결국 더 나은 기회로 이어질 것 같아요.",
    "advice": "내면의 목소리에 귀 기울이고, 변화를 두려워하지 마세요. 당신의 직감을 믿고 새로운 길을 개척해 나가세요.",
    "confidence_level": "high",
    "live2d_emotion": "mystical",
    "live2d_motion": "card_draw"
  },
  "metadata": {
    "request_id": "req_tarot_123456",
    "timestamp": "2025-08-22T12:30:00Z",
    "generation_time": 2.15
  }
}
```

### 3. 별자리 운세

12성좌별 특성을 반영한 맞춤형 운세를 제공합니다.

#### 엔드포인트

```http
GET /api/v1/fortune/zodiac/{zodiac_sign}
X-Session-ID: your-session-id
```

#### 경로 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 가능한 값 |
|----------|------|------|------|-----------|
| `zodiac_sign` | string | 필수 | 별자리 | `aries`, `taurus`, `gemini`, `cancer`, `leo`, `virgo`, `libra`, `scorpio`, `sagittarius`, `capricorn`, `aquarius`, `pisces` |

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|----------|------|------|------|--------|
| `period` | string | 선택 | 운세 기간 | `daily` |

#### 사용 예시

```javascript
// 물고기자리 일일 운세
const piscesDaily = await fetch('/api/v1/fortune/zodiac/pisces', {
  headers: { 'X-Session-ID': sessionId }
});

// 물고기자리 주간 운세
const piscesWeekly = await fetch('/api/v1/fortune/zodiac/pisces?period=weekly', {
  headers: { 'X-Session-ID': sessionId }
});

const zodiacData = await piscesDaily.json();
```

#### 응답 구조

```json
{
  "success": true,
  "data": {
    "zodiac_sign": "pisces",
    "zodiac_name": "물고기자리",
    "period": "daily",
    "date_range": "2025-08-22",
    "symbol": "♓",
    "element": "water",
    "ruling_planet": "neptune",
    "personality_traits": [
      "감성적", "직관적", "창의적", "공감 능력이 뛰어남", "상상력이 풍부함"
    ],
    "fortune": {
      "love": {
        "score": 88,
        "description": "물고기자리의 로맨틱한 성향이 빛을 발하는 날입니다. 감정 표현을 솔직하게 해보세요."
      },
      "career": {
        "score": 75,
        "description": "창의적인 아이디어가 떠오르는 날이에요. 예술적 감각을 업무에 활용해보세요."
      },
      "health": {
        "score": 80,
        "description": "정신적 휴식이 필요한 시기입니다. 명상이나 요가를 추천드려요."
      },
      "finance": {
        "score": 70,
        "description": "충동구매를 조심하세요. 신중한 투자를 고려해보세요."
      }
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
      "direction": "서쪽",
      "flower": "수련"
    },
    "daily_advice": "오늘은 당신의 직감을 믿고 행동하세요. 물고기자리의 감수성이 올바른 길을 안내할 것입니다.",
    "live2d_emotion": "thoughtful",
    "live2d_motion": "thinking_pose"
  },
  "metadata": {
    "request_id": "req_zodiac_123456",
    "timestamp": "2025-08-22T12:30:00Z",
    "cache_hit": true,
    "cache_expires_at": "2025-08-23T00:00:00Z"
  }
}
```

### 4. 운세 히스토리

사용자의 과거 운세 조회 기록을 확인할 수 있습니다.

#### 엔드포인트

```http
GET /api/v1/user/fortune-history
X-Session-ID: your-session-id
```

#### 쿼리 파라미터

| 파라미터 | 타입 | 필수 | 설명 | 기본값 |
|----------|------|------|------|--------|
| `page` | integer | 선택 | 페이지 번호 | 1 |
| `limit` | integer | 선택 | 페이지당 항목 수 | 20 |
| `fortune_type` | string | 선택 | 운세 유형 필터 | `all` |
| `date_from` | string | 선택 | 시작 날짜 | - |
| `date_to` | string | 선택 | 종료 날짜 | - |

#### 사용 예시

```javascript
// 최근 운세 기록
const recentHistory = await fetch('/api/v1/user/fortune-history?limit=10', {
  headers: { 'X-Session-ID': sessionId }
});

// 타로 운세만 필터링
const tarotHistory = await fetch('/api/v1/user/fortune-history?fortune_type=tarot', {
  headers: { 'X-Session-ID': sessionId }
});

const historyData = await recentHistory.json();
```

## 💬 채팅 및 WebSocket

### WebSocket 연결

실시간 채팅과 Live2D 캐릭터 상호작용을 위한 WebSocket 연결을 지원합니다.

#### 연결 엔드포인트

```
wss://api.fortune-vtuber.com/ws/chat/{session_id}
```

#### 연결 예시

```javascript
class FortuneVTuberWebSocket {
  constructor(sessionId) {
    this.sessionId = sessionId;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    const wsUrl = `wss://api.fortune-vtuber.com/ws/chat/${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = (event) => {
      console.log('WebSocket 연결됨');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket 연결 종료:', event.code, event.reason);
      this.handleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket 에러:', error);
    };
  }

  handleMessage(message) {
    switch (message.type) {
      case 'connection_established':
        this.onConnectionEstablished(message.data);
        break;
      case 'text_response':
        this.onTextResponse(message.data);
        break;
      case 'fortune_result':
        this.onFortuneResult(message.data);
        break;
      case 'live2d_action':
        this.onLive2DAction(message.data);
        break;
      case 'error':
        this.onError(message.data);
        break;
    }
  }

  sendMessage(text) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'text_input',
        data: {
          message: text,
          timestamp: new Date().toISOString()
        }
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  requestFortune(fortuneType, options = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'fortune_request',
        data: {
          fortune_type: fortuneType,
          ...options
        }
      };
      this.ws.send(JSON.stringify(message));
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.pow(2, this.reconnectAttempts) * 1000; // 지수 백오프
      
      setTimeout(() => {
        console.log(`재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        this.connect();
      }, delay);
    }
  }

  // 이벤트 핸들러들 (사용자 정의)
  onConnectionEstablished(data) {
    console.log('연결 성공:', data);
  }

  onTextResponse(data) {
    console.log('텍스트 응답:', data.message);
    // UI 업데이트 로직
  }

  onFortuneResult(data) {
    console.log('운세 결과:', data);
    // 운세 결과 표시 로직
  }

  onLive2DAction(data) {
    console.log('Live2D 액션:', data);
    // Live2D 캐릭터 제어 로직
  }

  onError(data) {
    console.error('서버 에러:', data);
    // 에러 처리 로직
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// 사용 예시
const chatWS = new FortuneVTuberWebSocket(sessionId);
chatWS.connect();

// 메시지 전송
chatWS.sendMessage("오늘 운세 봐주세요!");

// 타로 운세 요청
chatWS.requestFortune('tarot', {
  question: "연애운이 궁금해요",
  question_type: "love"
});
```

### 메시지 타입

#### 클라이언트 → 서버

1. **텍스트 입력**
```json
{
  "type": "text_input",
  "data": {
    "message": "오늘 운세 봐주세요",
    "timestamp": "2025-08-22T12:30:00Z"
  }
}
```

2. **운세 요청**
```json
{
  "type": "fortune_request",
  "data": {
    "fortune_type": "daily",
    "birth_date": "1995-03-15",
    "zodiac": "pisces"
  }
}
```

3. **음성 입력** (향후 지원 예정)
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

#### 서버 → 클라이언트

1. **연결 확립**
```json
{
  "type": "connection_established",
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "character_name": "미라",
    "welcome_message": "안녕하세요! 운세가 궁금하신가요?"
  }
}
```

2. **텍스트 응답**
```json
{
  "type": "text_response",
  "data": {
    "message": "오늘 운세를 봐드릴게요!",
    "is_complete": false,
    "live2d_emotion": "joy",
    "live2d_motion": "greeting"
  }
}
```

3. **운세 결과**
```json
{
  "type": "fortune_result",
  "data": {
    "fortune_type": "daily",
    "result": {
      // 운세 API 응답과 동일한 구조
    }
  }
}
```

4. **Live2D 액션**
```json
{
  "type": "live2d_action",
  "data": {
    "emotion": "mystical",
    "motion": "card_draw",
    "duration": 3000,
    "parameters": {
      "ParamEyeLOpen": 0.8,
      "ParamEyeROpen": 0.8
    }
  }
}
```

### 채팅 히스토리 API

#### 채팅 기록 조회

```http
GET /api/v1/chat/history/{session_id}
X-Session-ID: your-session-id
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "messages": [
      {
        "message_id": "msg_123",
        "type": "user",
        "content": "오늘 운세 봐주세요",
        "timestamp": "2025-08-22T12:30:00Z"
      },
      {
        "message_id": "msg_124",
        "type": "assistant",
        "content": "네, 오늘 운세를 봐드릴게요!",
        "timestamp": "2025-08-22T12:30:15Z",
        "live2d_action": {
          "emotion": "joy",
          "motion": "greeting"
        }
      }
    ],
    "total_messages": 2,
    "created_at": "2025-08-22T12:29:00Z"
  }
}
```

## 🎭 Live2D 통합

### Live2D 캐릭터 정보

#### 캐릭터 정보 조회

```http
GET /api/v1/live2d/character/info
X-Session-ID: your-session-id
```

**응답 예시:**
```json
{
  "success": true,
  "data": {
    "character_name": "미라",
    "character_description": "친근하고 따뜻한 운세 도우미",
    "model_path": "/static/live2d/mira/mira.model3.json",
    "version": "1.0.0",
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
      "thinking_pose": "motions/thinking_pose.motion3.json",
      "idle": "motions/idle.motion3.json"
    },
    "expressions": {
      "normal": "expressions/normal.exp3.json",
      "smile": "expressions/smile.exp3.json",
      "wink": "expressions/wink.exp3.json",
      "surprise": "expressions/surprise.exp3.json",
      "concern": "expressions/concern.exp3.json"
    }
  }
}
```

### 감정 및 모션 매핑

#### 상황별 Live2D 액션

| 상황 | 감정 | 모션 | 사용 시점 |
|------|------|------|-----------|
| **첫 만남** | `joy` | `greeting` | 세션 시작 |
| **일일 운세** | `neutral` | `blessing` | 일반 운세 제공 |
| **타로 리딩** | `mystical` | `card_draw` | 타로 카드 뽑기 |
| **좋은 운세** | `joy` | `celebration` | 높은 점수 운세 |
| **나쁜 운세** | `concern` | `comfort` | 낮은 점수 운세 |
| **깊은 사고** | `thinking` | `thinking_pose` | 복잡한 질문 |
| **놀람** | `surprise` | `surprise` | 예상치 못한 질문 |

#### Live2D 파라미터 제어

```javascript
// Live2D 파라미터 직접 제어 (고급 기능)
const live2dParams = {
  "ParamEyeLOpen": 1.0,      // 왼쪽 눈 열림
  "ParamEyeROpen": 1.0,      // 오른쪽 눈 열림
  "ParamEyeBallX": 0.0,      // 눈동자 좌우
  "ParamEyeBallY": 0.0,      // 눈동자 상하
  "ParamAngleX": 0.0,        // 얼굴 좌우 회전
  "ParamAngleY": 0.0,        // 얼굴 상하 회전
  "ParamAngleZ": 0.0,        // 얼굴 기울기
  "ParamMouthOpenY": 0.0,    // 입 열림
  "ParamMouthForm": 0.0,     // 입 모양
  "ParamBrowLY": 0.0,        // 왼쪽 눈썹
  "ParamBrowRY": 0.0         // 오른쪽 눈썹
};

// WebSocket을 통한 Live2D 제어
chatWS.sendLive2DAction({
  emotion: "mystical",
  motion: "card_draw",
  parameters: live2dParams,
  duration: 3000
});
```

## ❌ 에러 처리

### 에러 응답 형식

모든 에러는 일관된 형식으로 반환됩니다:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력 데이터가 올바르지 않습니다",
    "details": {
      "field": "birth_date",
      "reason": "Invalid date format",
      "expected_format": "YYYY-MM-DD"
    }
  },
  "metadata": {
    "request_id": "req_123456789",
    "timestamp": "2025-08-22T12:30:00Z"
  }
}
```

### 주요 에러 코드

| HTTP 상태 | 에러 코드 | 설명 | 해결 방법 |
|-----------|-----------|------|-----------|
| **400** | `VALIDATION_ERROR` | 요청 데이터 검증 실패 | 요청 형식 확인 |
| **400** | `INVALID_ZODIAC` | 잘못된 별자리 | 올바른 별자리 입력 |
| **400** | `INVALID_DATE_FORMAT` | 날짜 형식 오류 | YYYY-MM-DD 형식 사용 |
| **401** | `SESSION_EXPIRED` | 세션 만료 | 새 세션 생성 |
| **401** | `INVALID_SESSION` | 잘못된 세션 | 세션 ID 확인 |
| **403** | `CONTENT_FILTERED` | 부적절한 내용 | 질문 내용 수정 |
| **403** | `RATE_LIMIT_EXCEEDED` | 요청 제한 초과 | 잠시 후 재시도 |
| **404** | `ENDPOINT_NOT_FOUND` | 존재하지 않는 엔드포인트 | URL 확인 |
| **404** | `SESSION_NOT_FOUND` | 세션을 찾을 수 없음 | 새 세션 생성 |
| **422** | `QUESTION_TOO_LONG` | 질문이 너무 길음 | 질문 길이 줄이기 |
| **429** | `TOO_MANY_REQUESTS` | 너무 많은 요청 | Rate limiting 확인 |
| **500** | `INTERNAL_SERVER_ERROR` | 서버 내부 오류 | 잠시 후 재시도 |
| **503** | `SERVICE_UNAVAILABLE` | 서비스 일시 중단 | 잠시 후 재시도 |

### 에러 처리 예시

```javascript
class FortuneAPIClient {
  async makeRequest(url, options = {}) {
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-Session-ID': this.sessionId,
          ...options.headers
        }
      });

      const data = await response.json();

      if (!response.ok) {
        throw new APIError(data.error, response.status);
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      // 네트워크 에러 등
      throw new APIError({
        code: 'NETWORK_ERROR',
        message: '네트워크 연결을 확인해주세요'
      }, 0);
    }
  }

  async getDailyFortune(birthDate, zodiac) {
    try {
      return await this.makeRequest(`/api/v1/fortune/daily?birth_date=${birthDate}&zodiac=${zodiac}`);
    } catch (error) {
      return this.handleFortuneError(error);
    }
  }

  handleFortuneError(error) {
    switch (error.code) {
      case 'SESSION_EXPIRED':
        // 세션 재생성
        return this.refreshSession().then(() => this.getDailyFortune());
        
      case 'RATE_LIMIT_EXCEEDED':
        // 잠시 후 재시도
        return new Promise(resolve => {
          setTimeout(() => resolve(this.getDailyFortune()), 60000);
        });
        
      case 'CONTENT_FILTERED':
        // 사용자에게 적절한 안내
        return {
          success: false,
          message: '죄송해요, 그런 질문에는 답변드릴 수 없어요.'
        };
        
      default:
        throw error;
    }
  }
}

class APIError extends Error {
  constructor(errorData, statusCode) {
    super(errorData.message || '알 수 없는 오류가 발생했습니다');
    this.code = errorData.code;
    this.details = errorData.details;
    this.statusCode = statusCode;
  }
}
```

## ⚡ Rate Limiting

### 제한 규칙

| 엔드포인트 | 제한 | 기간 | 초과시 동작 |
|------------|------|------|-------------|
| **모든 API** | 60회 | 1분 | 429 에러 |
| **운세 생성** | 10회 | 1시간 | 429 에러 |
| **세션 생성** | 5회 | 1분 | 429 에러 |
| **WebSocket 메시지** | 30회 | 1분 | 연결 일시 중단 |

### Rate Limit 헤더

응답에 포함되는 Rate Limiting 정보:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1692705600
X-RateLimit-Retry-After: 60
```

### Rate Limit 처리

```javascript
class RateLimitHandler {
  constructor() {
    this.requestQueue = [];
    this.isProcessing = false;
  }

  async makeRateLimitedRequest(requestFn) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({ requestFn, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.isProcessing || this.requestQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.requestQueue.length > 0) {
      const { requestFn, resolve, reject } = this.requestQueue.shift();

      try {
        const result = await requestFn();
        resolve(result);
      } catch (error) {
        if (error.statusCode === 429) {
          // Rate limit 초과시 재시도 대기
          const retryAfter = error.headers?.['X-RateLimit-Retry-After'] || 60;
          
          console.warn(`Rate limit 초과, ${retryAfter}초 후 재시도`);
          
          setTimeout(() => {
            this.requestQueue.unshift({ requestFn, resolve, reject });
            this.processQueue();
          }, retryAfter * 1000);
          
          break;
        } else {
          reject(error);
        }
      }

      // 요청 간 최소 간격 (1초)
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    this.isProcessing = false;
  }
}

// 사용 예시
const rateLimitHandler = new RateLimitHandler();

async function getDailyFortuneWithRateLimit(birthDate, zodiac) {
  return await rateLimitHandler.makeRateLimitedRequest(async () => {
    return await apiClient.getDailyFortune(birthDate, zodiac);
  });
}
```

## 📚 SDK 및 라이브러리

### JavaScript/TypeScript SDK

```bash
npm install @fortune-vtuber/api-client
```

```javascript
import { FortuneVTuberClient } from '@fortune-vtuber/api-client';

const client = new FortuneVTuberClient({
  baseURL: 'https://api.fortune-vtuber.com',
  apiKey: 'your-api-key', // 향후 지원 예정
  timeout: 10000
});

// 사용 예시
async function main() {
  // 세션 생성
  const session = await client.createSession();
  
  // 일일 운세
  const dailyFortune = await client.getDailyFortune({
    birthDate: '1995-03-15',
    zodiac: 'pisces'
  });
  
  // 타로 리딩
  const tarotReading = await client.getTarotReading({
    question: '오늘 연애운은?',
    questionType: 'love'
  });
  
  // WebSocket 채팅
  const chat = await client.connectChat(session.sessionId);
  chat.on('message', (message) => {
    console.log('새 메시지:', message);
  });
  
  chat.sendMessage('안녕하세요!');
}
```

### Python SDK

```bash
pip install fortune-vtuber-client
```

```python
from fortune_vtuber import FortuneVTuberClient

client = FortuneVTuberClient(
    base_url='https://api.fortune-vtuber.com',
    timeout=10
)

# 세션 생성
session = client.create_session()

# 일일 운세
daily_fortune = client.get_daily_fortune(
    birth_date='1995-03-15',
    zodiac='pisces'
)

# 타로 리딩
tarot_reading = client.get_tarot_reading(
    question='오늘 연애운은?',
    question_type='love'
)

print(daily_fortune)
```

### React Hooks

```bash
npm install @fortune-vtuber/react-hooks
```

```jsx
import { useFortuneAPI, useWebSocketChat } from '@fortune-vtuber/react-hooks';

function FortuneApp() {
  const { session, isLoading } = useFortuneAPI();
  const { messages, sendMessage, connectionStatus } = useWebSocketChat(session?.sessionId);

  const handleGetFortune = async () => {
    const fortune = await session.getDailyFortune({
      birthDate: '1995-03-15',
      zodiac: 'pisces'
    });
    console.log(fortune);
  };

  return (
    <div>
      <h1>Fortune VTuber</h1>
      <button onClick={handleGetFortune} disabled={isLoading}>
        운세 보기
      </button>
      
      <div>
        {messages.map(msg => (
          <div key={msg.id}>{msg.content}</div>
        ))}
      </div>
      
      <input 
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendMessage(e.target.value);
            e.target.value = '';
          }
        }}
        placeholder="메시지를 입력하세요"
      />
    </div>
  );
}
```

## 🎯 예제 코드

### 완전한 프론트엔드 통합 예시

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fortune VTuber Demo</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin: 16px 0; }
        .error { color: red; background: #ffebee; padding: 10px; border-radius: 4px; }
        .success { color: green; background: #e8f5e8; padding: 10px; border-radius: 4px; }
        .loading { opacity: 0.6; pointer-events: none; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
        input, select { padding: 8px; margin: 5px; width: 200px; }
        #live2d-container { width: 300px; height: 400px; border: 1px solid #ddd; margin: 20px 0; }
        #chat-messages { height: 200px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
        .message { margin: 5px 0; padding: 5px; border-radius: 4px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .bot-message { background: #f3e5f5; }
    </style>
</head>
<body>
    <h1>🔮 Fortune VTuber Demo</h1>

    <!-- 세션 정보 -->
    <div class="card">
        <h3>세션 정보</h3>
        <div id="session-info">연결 중...</div>
        <button onclick="createNewSession()">새 세션 생성</button>
    </div>

    <!-- 사용자 프로필 -->
    <div class="card">
        <h3>사용자 프로필</h3>
        <input type="date" id="birthDate" placeholder="생년월일">
        <select id="zodiacSelect">
            <option value="">별자리 선택</option>
            <option value="aries">양자리</option>
            <option value="taurus">황소자리</option>
            <option value="gemini">쌍둥이자리</option>
            <option value="cancer">게자리</option>
            <option value="leo">사자자리</option>
            <option value="virgo">처녀자리</option>
            <option value="libra">천칭자리</option>
            <option value="scorpio">전갈자리</option>
            <option value="sagittarius">궁수자리</option>
            <option value="capricorn">염소자리</option>
            <option value="aquarius">물병자리</option>
            <option value="pisces">물고기자리</option>
        </select>
        <button onclick="updateProfile()">프로필 업데이트</button>
    </div>

    <!-- 운세 요청 -->
    <div class="card">
        <h3>운세 요청</h3>
        <button onclick="getDailyFortune()">일일 운세</button>
        <button onclick="getTarotReading()">타로 리딩</button>
        <button onclick="getZodiacFortune()">별자리 운세</button>
        
        <div id="tarot-question-section" style="display: none;">
            <input type="text" id="tarotQuestion" placeholder="타로 질문을 입력하세요">
            <select id="questionType">
                <option value="general">일반</option>
                <option value="love">연애</option>
                <option value="money">금전</option>
                <option value="health">건강</option>
                <option value="work">업무</option>
            </select>
        </div>
    </div>

    <!-- Live2D 캐릭터 -->
    <div class="card">
        <h3>Live2D 캐릭터</h3>
        <div id="live2d-container">
            <div style="text-align: center; line-height: 400px; color: #999;">
                Live2D 캐릭터가 여기에 표시됩니다
            </div>
        </div>
        <div id="character-status">감정: neutral, 모션: idle</div>
    </div>

    <!-- 채팅 -->
    <div class="card">
        <h3>실시간 채팅</h3>
        <div id="chat-messages"></div>
        <input type="text" id="chatInput" placeholder="메시지를 입력하세요" onkeypress="handleChatKeyPress(event)">
        <button onclick="sendChatMessage()">전송</button>
        <div id="websocket-status">WebSocket: 연결 중...</div>
    </div>

    <!-- 결과 표시 -->
    <div class="card">
        <h3>운세 결과</h3>
        <div id="fortune-result">운세 결과가 여기에 표시됩니다</div>
    </div>

    <!-- 메시지 표시 -->
    <div id="message-container"></div>

    <script>
        // 전역 변수
        let sessionId = null;
        let websocket = null;
        let currentProfile = {};

        // API 베이스 URL
        const API_BASE_URL = 'https://api.fortune-vtuber.com';
        const WS_BASE_URL = 'wss://api.fortune-vtuber.com';

        // 유틸리티 함수
        function showMessage(message, type = 'info') {
            const container = document.getElementById('message-container');
            const div = document.createElement('div');
            div.className = type === 'error' ? 'error' : 'success';
            div.textContent = message;
            container.appendChild(div);
            
            setTimeout(() => {
                container.removeChild(div);
            }, 5000);
        }

        function setLoading(element, isLoading) {
            if (isLoading) {
                element.classList.add('loading');
            } else {
                element.classList.remove('loading');
            }
        }

        // API 요청 함수
        async function apiRequest(endpoint, options = {}) {
            const url = `${API_BASE_URL}${endpoint}`;
            const defaultHeaders = {
                'Content-Type': 'application/json'
            };

            if (sessionId) {
                defaultHeaders['X-Session-ID'] = sessionId;
            }

            const response = await fetch(url, {
                ...options,
                headers: {
                    ...defaultHeaders,
                    ...options.headers
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error?.message || '요청 실패');
            }

            return data;
        }

        // 세션 관리
        async function createSession() {
            try {
                const response = await apiRequest('/api/v1/user/session', {
                    method: 'POST',
                    body: JSON.stringify({
                        user_agent: navigator.userAgent,
                        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                        language: navigator.language
                    })
                });

                sessionId = response.data.session_id;
                document.getElementById('session-info').innerHTML = `
                    <strong>세션 ID:</strong> ${sessionId}<br>
                    <strong>만료 시간:</strong> ${response.data.expires_at}<br>
                    <strong>캐릭터:</strong> ${response.data.character_name}
                `;

                showMessage('세션이 성공적으로 생성되었습니다', 'success');
                
                // WebSocket 연결
                connectWebSocket();
                
                return response;
            } catch (error) {
                showMessage('세션 생성 실패: ' + error.message, 'error');
                throw error;
            }
        }

        async function createNewSession() {
            if (websocket) {
                websocket.close();
            }
            await createSession();
        }

        // 프로필 관리
        async function updateProfile() {
            const birthDate = document.getElementById('birthDate').value;
            const zodiac = document.getElementById('zodiacSelect').value;

            if (!birthDate || !zodiac) {
                showMessage('생년월일과 별자리를 선택해주세요', 'error');
                return;
            }

            try {
                const profileData = {
                    birth_date: birthDate,
                    zodiac_sign: zodiac,
                    preferences: {
                        fortune_types: ['daily', 'tarot', 'zodiac'],
                        theme: 'light'
                    }
                };

                await apiRequest('/api/v1/user/profile', {
                    method: 'PUT',
                    body: JSON.stringify(profileData)
                });

                currentProfile = profileData;
                showMessage('프로필이 업데이트되었습니다', 'success');
            } catch (error) {
                showMessage('프로필 업데이트 실패: ' + error.message, 'error');
            }
        }

        // 운세 API
        async function getDailyFortune() {
            const resultDiv = document.getElementById('fortune-result');
            setLoading(resultDiv, true);

            try {
                const birthDate = document.getElementById('birthDate').value;
                const zodiac = document.getElementById('zodiacSelect').value;
                
                let url = '/api/v1/fortune/daily';
                const params = new URLSearchParams();
                
                if (birthDate) params.append('birth_date', birthDate);
                if (zodiac) params.append('zodiac', zodiac);
                
                if (params.toString()) {
                    url += '?' + params.toString();
                }

                const response = await apiRequest(url);
                displayFortuneResult(response.data, 'daily');
                
                // Live2D 액션 트리거
                if (response.data.live2d_emotion && response.data.live2d_motion) {
                    updateLive2DCharacter(response.data.live2d_emotion, response.data.live2d_motion);
                }
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">운세 조회 실패: ${error.message}</div>`;
            } finally {
                setLoading(resultDiv, false);
            }
        }

        async function getTarotReading() {
            const questionSection = document.getElementById('tarot-question-section');
            questionSection.style.display = 'block';
            
            const question = document.getElementById('tarotQuestion').value;
            const questionType = document.getElementById('questionType').value;

            if (!question.trim()) {
                showMessage('타로 질문을 입력해주세요', 'error');
                return;
            }

            const resultDiv = document.getElementById('fortune-result');
            setLoading(resultDiv, true);

            try {
                const requestData = {
                    question: question,
                    question_type: questionType,
                    user_info: {}
                };

                if (currentProfile.birth_date) {
                    requestData.user_info.birth_date = currentProfile.birth_date;
                }
                if (currentProfile.zodiac_sign) {
                    requestData.user_info.zodiac = currentProfile.zodiac_sign;
                }

                const response = await apiRequest('/api/v1/fortune/tarot', {
                    method: 'POST',
                    body: JSON.stringify(requestData)
                });

                displayTarotResult(response.data);
                
                // Live2D 액션 트리거
                updateLive2DCharacter('mystical', 'card_draw');
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">타로 리딩 실패: ${error.message}</div>`;
            } finally {
                setLoading(resultDiv, false);
            }
        }

        async function getZodiacFortune() {
            const zodiac = document.getElementById('zodiacSelect').value;
            
            if (!zodiac) {
                showMessage('별자리를 선택해주세요', 'error');
                return;
            }

            const resultDiv = document.getElementById('fortune-result');
            setLoading(resultDiv, true);

            try {
                const response = await apiRequest(`/api/v1/fortune/zodiac/${zodiac}`);
                displayZodiacResult(response.data);
                
                // Live2D 액션 트리거
                updateLive2DCharacter('thoughtful', 'thinking_pose');
                
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">별자리 운세 조회 실패: ${error.message}</div>`;
            } finally {
                setLoading(resultDiv, false);
            }
        }

        // 결과 표시 함수
        function displayFortuneResult(data, type) {
            const resultDiv = document.getElementById('fortune-result');
            
            let html = `
                <h4>${data.date} 일일 운세</h4>
                <div class="card">
                    <h5>전체 운세 (${data.overall_fortune.score}점)</h5>
                    <p><strong>${data.overall_fortune.grade}</strong></p>
                    <p>${data.overall_fortune.description}</p>
                </div>
            `;

            if (data.categories) {
                html += '<div class="card"><h5>분야별 운세</h5>';
                for (const [category, info] of Object.entries(data.categories)) {
                    const categoryNames = {
                        love: '연애운',
                        money: '금전운', 
                        health: '건강운',
                        work: '업무운'
                    };
                    
                    html += `
                        <div style="margin: 10px 0; padding: 10px; border-left: 3px solid #2196F3;">
                            <strong>${categoryNames[category]} (${info.score}점)</strong><br>
                            ${info.description}
                        </div>
                    `;
                }
                html += '</div>';
            }

            if (data.lucky_items && data.lucky_items.length > 0) {
                html += `
                    <div class="card">
                        <h5>행운의 아이템</h5>
                        <p>${data.lucky_items.join(', ')}</p>
                    </div>
                `;
            }

            if (data.advice) {
                html += `
                    <div class="card">
                        <h5>조언</h5>
                        <p>${data.advice}</p>
                    </div>
                `;
            }

            resultDiv.innerHTML = html;
        }

        function displayTarotResult(data) {
            const resultDiv = document.getElementById('fortune-result');
            
            let html = `
                <h4>타로 리딩 결과</h4>
                <div class="card">
                    <h5>질문: ${data.question}</h5>
                    <p><strong>리딩 ID:</strong> ${data.reading_id}</p>
                </div>
            `;

            html += '<div class="card"><h5>카드 해석</h5>';
            data.cards.forEach((card, index) => {
                const positions = { past: '과거', present: '현재', future: '미래' };
                html += `
                    <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px;">
                        <h6>${positions[card.position]} - ${card.card_name}</h6>
                        <p><strong>의미:</strong> ${card.card_meaning}</p>
                        <p><strong>해석:</strong> ${card.interpretation}</p>
                    </div>
                `;
            });
            html += '</div>';

            if (data.overall_interpretation) {
                html += `
                    <div class="card">
                        <h5>전체 해석</h5>
                        <p>${data.overall_interpretation}</p>
                    </div>
                `;
            }

            if (data.advice) {
                html += `
                    <div class="card">
                        <h5>조언</h5>
                        <p>${data.advice}</p>
                    </div>
                `;
            }

            resultDiv.innerHTML = html;
        }

        function displayZodiacResult(data) {
            const resultDiv = document.getElementById('fortune-result');
            
            let html = `
                <h4>${data.zodiac_name} (${data.symbol}) 운세</h4>
                <div class="card">
                    <h5>성격 특성</h5>
                    <p>${data.personality_traits.join(', ')}</p>
                </div>
            `;

            if (data.fortune) {
                html += '<div class="card"><h5>분야별 운세</h5>';
                for (const [category, info] of Object.entries(data.fortune)) {
                    const categoryNames = {
                        love: '연애운',
                        career: '직업운',
                        health: '건강운',
                        finance: '재정운'
                    };
                    
                    html += `
                        <div style="margin: 10px 0; padding: 10px; border-left: 3px solid #4CAF50;">
                            <strong>${categoryNames[category]} (${info.score}점)</strong><br>
                            ${info.description}
                        </div>
                    `;
                }
                html += '</div>';
            }

            if (data.lucky_elements) {
                html += `
                    <div class="card">
                        <h5>행운의 요소</h5>
                        <p><strong>색깔:</strong> ${data.lucky_elements.color}</p>
                        <p><strong>숫자:</strong> ${data.lucky_elements.number}</p>
                        <p><strong>보석:</strong> ${data.lucky_elements.stone}</p>
                        <p><strong>방향:</strong> ${data.lucky_elements.direction}</p>
                    </div>
                `;
            }

            if (data.daily_advice) {
                html += `
                    <div class="card">
                        <h5>오늘의 조언</h5>
                        <p>${data.daily_advice}</p>
                    </div>
                `;
            }

            resultDiv.innerHTML = html;
        }

        // Live2D 캐릭터 제어
        function updateLive2DCharacter(emotion, motion) {
            const statusDiv = document.getElementById('character-status');
            statusDiv.textContent = `감정: ${emotion}, 모션: ${motion}`;
            
            // 실제 Live2D 모델이 있다면 여기서 제어
            // live2dModel.setExpression(emotion);
            // live2dModel.startMotion(motion);
        }

        // WebSocket 채팅
        function connectWebSocket() {
            if (!sessionId) {
                showMessage('세션이 필요합니다', 'error');
                return;
            }

            const wsUrl = `${WS_BASE_URL}/ws/chat/${sessionId}`;
            websocket = new WebSocket(wsUrl);

            websocket.onopen = function(event) {
                document.getElementById('websocket-status').textContent = 'WebSocket: 연결됨';
                showMessage('채팅이 연결되었습니다', 'success');
            };

            websocket.onmessage = function(event) {
                const message = JSON.parse(event.data);
                handleWebSocketMessage(message);
            };

            websocket.onclose = function(event) {
                document.getElementById('websocket-status').textContent = 'WebSocket: 연결 종료';
                showMessage('채팅 연결이 종료되었습니다', 'error');
            };

            websocket.onerror = function(error) {
                document.getElementById('websocket-status').textContent = 'WebSocket: 오류';
                showMessage('채팅 연결 오류: ' + error, 'error');
            };
        }

        function handleWebSocketMessage(message) {
            const messagesDiv = document.getElementById('chat-messages');
            
            switch (message.type) {
                case 'connection_established':
                    addChatMessage('시스템', message.data.welcome_message || '연결되었습니다', 'system');
                    break;
                    
                case 'text_response':
                    addChatMessage('미라', message.data.message, 'bot');
                    if (message.data.live2d_emotion && message.data.live2d_motion) {
                        updateLive2DCharacter(message.data.live2d_emotion, message.data.live2d_motion);
                    }
                    break;
                    
                case 'fortune_result':
                    addChatMessage('미라', '운세 결과를 확인해보세요!', 'bot');
                    displayFortuneResult(message.data.result, message.data.fortune_type);
                    break;
                    
                case 'live2d_action':
                    updateLive2DCharacter(message.data.emotion, message.data.motion);
                    break;
                    
                case 'error':
                    addChatMessage('시스템', '오류: ' + message.data.message, 'error');
                    break;
            }
        }

        function addChatMessage(sender, content, type = 'bot') {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            const timestamp = new Date().toLocaleTimeString();
            messageDiv.innerHTML = `
                <div style="font-size: 0.8em; color: #666;">${sender} - ${timestamp}</div>
                <div>${content}</div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function sendChatMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            if (!message) return;
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                showMessage('채팅이 연결되지 않았습니다', 'error');
                return;
            }

            // 사용자 메시지 표시
            addChatMessage('사용자', message, 'user');
            
            // 서버로 메시지 전송
            const wsMessage = {
                type: 'text_input',
                data: {
                    message: message,
                    timestamp: new Date().toISOString()
                }
            };
            
            websocket.send(JSON.stringify(wsMessage));
            input.value = '';
        }

        function handleChatKeyPress(event) {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        }

        // 초기화
        document.addEventListener('DOMContentLoaded', function() {
            createSession();
        });
    </script>
</body>
</html>
```

## ❓ FAQ

### Q1: API 키가 필요한가요?
A: 현재는 세션 기반 인증만 지원합니다. API 키 인증은 향후 추가될 예정입니다.

### Q2: WebSocket 연결이 자주 끊어져요
A: 네트워크 상태나 방화벽 설정을 확인해보세요. 자동 재연결 로직을 구현하는 것을 권장합니다.

### Q3: 운세 결과가 항상 다른가요?
A: 일일 운세는 24시간 캐시되므로 같은 날에는 동일한 결과가 반환됩니다. 타로 리딩은 매번 새로운 결과를 제공합니다.

### Q4: 어떤 언어를 지원하나요?
A: 현재는 한국어만 지원합니다. 다국어 지원은 향후 계획에 있습니다.

### Q5: Rate Limit을 늘릴 수 있나요?
A: 프로덕션 환경에서는 별도 상담을 통해 조정 가능합니다.

### Q6: Live2D 모델을 커스터마이징할 수 있나요?
A: 현재는 기본 캐릭터만 제공됩니다. 커스터마이징은 엔터프라이즈 플랜에서 지원 예정입니다.

### Q7: 오프라인에서도 작동하나요?
A: 네트워크 연결이 필요한 서비스입니다. PWA 캐싱을 통한 부분적 오프라인 지원을 고려 중입니다.

### Q8: CORS 문제가 발생해요
A: 허용된 도메인에서만 API를 호출할 수 있습니다. 개발 환경에서는 프록시를 사용하세요.

---

## 📞 지원

- **API 문서**: [https://docs.fortune-vtuber.com](https://docs.fortune-vtuber.com)
- **GitHub**: [https://github.com/fortune-vtuber/api-examples](https://github.com/fortune-vtuber/api-examples)
- **Discord**: [Fortune VTuber 개발자 커뮤니티](https://discord.gg/fortune-vtuber)
- **이메일**: api-support@fortune-vtuber.com

**API와 함께 멋진 운세 애플리케이션을 만들어보세요! ✨**
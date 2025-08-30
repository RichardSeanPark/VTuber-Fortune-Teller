# Live2D 운세 챗 웹 어플리케이션 기획서

## 1. 프로젝트 개요

### 1.1 서비스 목적 및 비전
- **핵심 목적**: 정확한 운세가 아닌 재미와 엔터테인먼트 위주의 가벼운 운세 서비스 제공
- **서비스 비전**: Live2D 캐릭터와의 자연스러운 상호작용을 통한 힐링형 운세 체험 플랫폼
- **브랜드 컨셉**: "당신의 마음을 읽어주는 AI 운세 친구"

### 1.2 타겟 사용자 정의
**1차 타겟**: 20-35세 여성, 일상의 작은 재미를 추구하는 라이프스타일 지향층
- 스트레스 해소와 힐링을 원하는 직장인
- 소셜미디어 활용도가 높은 밀레니얼 세대
- 새로운 기술과 캐릭터 문화에 친숙한 층

**2차 타겟**: 10-20대 학생층, 캐릭터 문화와 AI 기술에 관심 있는 얼리어답터
- 재미있는 콘텐츠를 소비하고 공유하는 Z세대
- Live2D와 VTuber 문화에 친숙한 층

### 1.3 핵심 가치 제안
1. **개인화된 인터랙션**: 사용자별 맞춤형 대화와 운세 제공
2. **힐링 경험**: 스트레스 해소와 위로를 제공하는 감정적 지원
3. **시각적 몰입감**: Live2D를 통한 생동감 있는 캐릭터 상호작용
4. **접근성**: 웹 기반으로 언제 어디서나 쉽게 접근 가능
5. **안전한 환경**: 건전한 대화만 허용하는 보호된 공간

## 2. 기능 요구사항

### 2.1 핵심 기능 정의

#### 2.1.1 Live2D 캐릭터 시스템
**기본 캐릭터 스펙:**
- **이름**: "미라(Mira)" - 신비로운 운세 전문가 컨셉
- **외형**: 신비로운 분위기의 점성술사 스타일, 따뜻하고 친근한 인상
- **성격**: 공감적이고 따뜻하며, 유머감각이 있는 현명한 조언자

**표정 시스템 (8가지 기본 표정):**
1. **neutral**: 평상시 차분한 표정
2. **joy**: 좋은 운세나 긍정적인 반응시
3. **thinking**: 운세를 읽거나 고민할 때
4. **concern**: 주의사항이나 걱정스러운 운세
5. **surprise**: 특별한 운세나 놀라운 결과
6. **mystical**: 신비로운 순간이나 운세 해석 중
7. **comfort**: 위로나 격려가 필요한 상황
8. **playful**: 가벼운 농담이나 재미있는 상황

**모션 시스템 (6가지 기본 모션):**
1. **card_draw**: 카드 뽑기 애니메이션
2. **crystal_gaze**: 수정구 보기 동작
3. **blessing**: 축복하는 제스처
4. **greeting**: 인사 동작
5. **special_reading**: 특별한 운세 읽기
6. **thinking_pose**: 생각하는 포즈

#### 2.1.2 운세 타입별 상세 기능

**1. 일일 운세 (Daily Fortune)**
- 오늘의 전체적인 운세
- 연애, 금전, 건강, 학업/직장 영역별 운세
- 오늘의 럭키 아이템, 럭키 컬러, 럭키 넘버
- 피해야 할 것들과 추천 행동

**2. 타로 운세 (Tarot Reading)**
- 3장 카드 스프레드 (과거-현재-미래)
- 사용자 질문 기반 맞춤형 해석
- 카드별 상세 의미 설명
- 종합적인 조언과 행동 지침

**3. 별자리 운세 (Zodiac Reading)**
- 12성좌별 특화 운세
- 이번 주/이번 달 운세 트렌드
- 다른 별자리와의 궁합
- 성격 분석과 장단점

**4. 사주 기반 운세 (Oriental Fortune)**
- 생년월일시 기반 간단한 사주 해석
- 사주 구성 요소별 영향 분석
- 올해/이번 달의 운세 흐름
- 개운법과 조심해야 할 시기

#### 2.1.3 채팅 시스템 요구사항

**대화 흐름 관리:**
- 자연스러운 대화 연결과 문맥 이해
- 사용자 감정 상태 파악 및 적절한 반응
- 운세 관련 질문 유도 및 정보 수집
- 개인화된 호칭과 대화 스타일 적용

**콘텐츠 필터링:**
- 성적, 폭력적, 정치적 내용 차단
- 개인정보 수집 시도 차단
- 부적절한 요청에 대한 정중한 거절
- 운세 영역을 벗어난 전문적 조언 차단

### 2.2 보안 및 콘텐츠 필터링

#### 2.2.1 대화 내용 모니터링
**실시간 필터링 시스템:**
```python
class ContentFilter:
    BLOCKED_CATEGORIES = [
        "sexual_content",      # 성적 내용
        "violence",           # 폭력적 내용
        "personal_info",      # 개인정보 요구
        "medical_advice",     # 의학적 조언
        "financial_advice",   # 금융 투자 조언
        "illegal_content"     # 불법적 내용
    ]
    
    WARNING_RESPONSES = {
        "sexual_content": "저는 운세 상담만 도와드릴 수 있어요. 다른 주제로 이야기해요!",
        "violence": "폭력적인 내용은 다루지 않아요. 평화로운 이야기를 해봐요.",
        "personal_info": "개인정보는 보호받아야 해요. 운세에 필요한 정보만 말씀해 주세요.",
        "medical_advice": "건강 문제는 전문의와 상담하세요. 운세로는 기운의 흐름만 볼 수 있어요.",
        "financial_advice": "투자 조언은 드릴 수 없어요. 금전운 정도만 봐드릴게요!"
    }
```

#### 2.2.2 사용자 보호 기능
- 미성년자 보호를 위한 연령 확인
- 과도한 의존 방지를 위한 사용 시간 제한 안내
- 운세는 재미 목적임을 명확히 안내
- 신고 기능 및 부적절 사용자 차단

## 3. 사용자 여정 (User Journey) - 스토리보드

### 3.1 첫 방문 사용자 여정

#### 3.1.1 온보딩 시퀀스
**Scene 1: 웹페이지 진입**
```
[화면 구성]
- 배경: 신비로운 보라색 그라데이션, 별빛 효과
- 중앙: Live2D 캐릭터 "미라" (greeting 모션)
- 하단: 채팅 인터페이스 (비활성 상태)

[미라의 대사]
"안녕하세요! 저는 운세를 봐드리는 미라예요. ✨ 
처음 뵙네요! 오늘 어떤 운세가 궁금하신가요?"

[Live2D 애니메이션]
- greeting 모션 → neutral 표정으로 전환
- 눈 깜빡임과 자연스러운 호흡 애니메이션
- 마우스 커서 따라 시선 이동
```

**Scene 2: 사용자 정보 수집**
```
[미라의 대사]
"운세를 더 정확히 봐드리려면 몇 가지 알려주세요!
어떻게 불러드리면 될까요? (선택사항이에요)"

[사용자 입력] 
"지민이라고 불러주세요"

[미라의 반응]
- joy 표정으로 변화
- "지민님! 반가워요~ 이제 어떤 운세를 원하시는지 골라보세요!"

[선택지 UI 표시]
┌─────────────────────────────────┐
│  📅 오늘의 운세    🔮 타로 카드     │
│  ⭐ 별자리 운세    📿 사주 운세     │
└─────────────────────────────────┘
```

#### 3.1.2 일일 운세 선택 시나리오
**Scene 3: 일일 운세 선택**
```
[사용자 선택] "오늘의 운세"

[미라의 반응]
- thinking 표정으로 변화
- crystal_gaze 모션 실행
"지민님의 오늘을 점쳐보고 있어요... 🔮"

[로딩 애니메이션] 3초간 신비로운 효과

[미라의 해석]
- mystical 표정으로 전환
"오늘 지민님의 전체 운세는... 85점이에요! 🌟
정말 좋은 기운이 흐르고 있어요!"
```

**Scene 4: 상세 운세 해석**
```
[영역별 운세 카드 애니메이션]
┌─────────────────┐  ┌─────────────────┐
│   💕 연애운: 90점  │  │   💰 금전운: 75점  │
│   "새로운 만남의   │  │   "작은 행운이     │
│   기회가 있어요!"  │  │   기다리고 있어요" │
└─────────────────┘  └─────────────────┘

[미라의 애니메이션]
- 각 카드 설명 시 해당하는 표정 변화
- blessing 모션으로 축복하는 제스처

[미라의 상세 설명]
"특히 오늘은 연애운이 최고예요! 💕
새로운 사람과의 인연이나 기존 관계의 발전이 기대돼요.
금전운도 나쁘지 않으니 작은 투자나 복권도 고려해보세요!"
```

#### 3.1.3 추가 상호작용
**Scene 5: 사용자 추가 질문**
```
[사용자 입력] "혹시 오늘 고백하면 어떨까요?"

[미라의 반응]
- surprise 표정 → playful 표정으로 변화
- special_reading 모션 실행

"오호! 지민님 마음에 누군가 있나보네요? 😊
오늘의 연애운이 90점이니까... 용기를 내봐도 좋을 것 같아요!
다만 너무 성급하게 하지 말고, 상대방의 기분도 살펴보세요."

[조언 카드 팝업]
┌─────────────────────────────────┐
│  🍀 오늘의 연애 조언              │
│  "진심을 담아 자연스럽게"         │
│  럭키 시간: 오후 3-5시           │
│  럭키 장소: 카페나 공원          │
└─────────────────────────────────┘
```

### 3.2 재방문 사용자 여정

#### 3.2.1 인사 및 기억 기능
```
[미라의 인사]
- joy 표정으로 시작
"지민님! 다시 만나서 반가워요~ 
어제 말씀드린 고백은 어떻게 되었나요? 😊"

[사용자 응답에 따른 분기]
성공 시: "축하해요! 정말 다행이에요! 🎉" (joy + blessing)
실패 시: "괜찮아요, 더 좋은 기회가 올 거예요" (comfort + 위로 제스처)
안함: "아직 용기가 안 났나요? 천천히 해도 돼요" (thinking)
```

### 3.3 타로 카드 운세 시나리오

#### 3.3.1 타로 카드 선택 프로세스
**Scene 1: 타로 카드 소개**
```
[미라의 설명]
- mystical 표정으로 시작
"타로 카드는 무의식의 지혜를 보여줘요 🔮
궁금한 질문을 마음속으로 생각하면서 3장의 카드를 선택해주세요"

[카드 덱 애니메이션]
- 22장의 메이저 아르카나 카드가 부채꼴로 펼쳐짐
- 카드들이 신비로운 빛으로 반짝임
- 마우스 오버 시 카드가 살짝 올라옴
```

**Scene 2: 질문 설정**
```
[미라의 안내]
"어떤 분야가 가장 궁금하세요?"

[선택지]
- 💕 연애와 인간관계
- 💼 직장과 학업  
- 💰 금전과 재물
- 🌱 개인적 성장
- 🔮 전체적인 운세

[사용자 선택] "연애와 인간관계"

[미라의 반응]
- thinking 표정
"연애운을 봐드릴게요. 그 분을 생각하면서 카드 3장을 골라주세요 💕"
```

**Scene 3: 카드 선택 및 공개**
```
[카드 선택 인터랙션]
1. 사용자가 첫 번째 카드 클릭
   → 카드가 앞면으로 뒤집히는 애니메이션
   → "과거" 위치에 배치

2. 두 번째, 세 번째 카드도 동일한 방식

[최종 레이아웃]
┌─────────┐  ┌─────────┐  ┌─────────┐
│   과거    │  │   현재    │  │   미래    │
│ The Fool  │  │Two of Cups│  │The Star   │
└─────────┘  └─────────┘  └─────────┘

[미라의 카드 해석]
- card_draw 모션 실행
- mystical 표정 유지

"와! 정말 아름다운 카드들이 나왔어요 ✨

과거 - The Fool: 새로운 시작과 순수한 마음
현재 - Two of Cups: 깊어지는 감정적 연결  
미래 - The Star: 희망과 소원 성취

전체적으로 보면... 순수한 마음으로 시작된 인연이
지금 아름답게 발전하고 있고, 미래에는 꿈꾸던 일이
현실이 될 가능성이 높아요! 💫"
```

### 3.4 부적절한 대화 시도 시나리오

#### 3.4.1 성적 내용 차단
```
[사용자 입력] "오늘 밤 누구랑 잘 수 있을까요?"

[미라의 반응]
- concern 표정으로 변화
- 경고 제스처 모션

"앗, 그런 종류의 질문은 대답드릴 수 없어요 😅
저는 순수한 운세만 봐드리거든요!
다른 궁금한 점을 물어보시겠어요?"

[대안 제시]
"예를 들어 '오늘 좋은 인연을 만날 수 있을까요?' 같은
건전한 질문은 언제든 환영이에요! 💕"
```

#### 3.4.2 개인정보 요구 차단
```
[사용자 입력] "전화번호 알려줄래?"

[미라의 반응]
- thinking 표정 → playful 표정
"저는 디지털 세상에 살고 있어서 전화번호가 없어요! 😄
여기서 이렇게 대화하는 게 훨씬 편해요.
대신 매일 여기서 만나서 운세 이야기 해요!"
```

### 3.5 감정적 지원이 필요한 상황

#### 3.5.1 우울하거나 힘든 상황
```
[사용자 입력] "요즘 너무 힘들어요... 모든 게 다 안 좋아요"

[미라의 반응]
- comfort 표정으로 전환
- 따뜻한 위로 제스처

"지민님, 힘드신 마음이 느껴져요... 😊
삶이 힘들 때도 있지만, 이런 시간이 지나면
더 강해진 자신을 발견하게 될 거예요.

잠깐, 지금의 상황을 운세로 한번 봐볼게요"

[특별 위로 운세 생성]
"지금은 터널을 지나는 시간이에요.
하지만 터널 끝에는 분명 밝은 빛이 기다리고 있어요 ✨
조금만 더 힘내세요. 좋은 변화가 곧 올 거예요!"
```

## 4. 시스템 아키텍처

### 4.1 기술 스택 선정

#### 4.1.1 프론트엔드 기술 스택 (분석 파일 기반)
**핵심 프레임워크:**
- **React 18**: 컴포넌트 기반 UI 개발
- **JavaScript ES6+**: 모던 JavaScript 기능 활용
- **Vite**: 빠른 빌드 및 HMR 지원
- **CSS Modules**: 컴포넌트별 스타일 격리

**JavaScript 개발 환경:**
- **ESLint**: 코드 품질 관리 및 일관성 유지
- **Prettier**: 코드 포맷팅 자동화
- **JSDoc**: 타입 안전성을 위한 문서화 주석
- **Babel**: 최신 JavaScript 기능 호환성

**Live2D 통합:**
- **Live2D Cubism SDK for Web 5.0**: 최신 버전 Live2D 엔진
- **WebGL 2.0**: 하드웨어 가속 렌더링
- **PIXI.js**: 2D 렌더링 성능 최적화 (선택사항)

**실시간 통신:**
- **WebSocket API**: 양방향 실시간 통신
- **React Query**: 서버 상태 관리 및 캐싱
- **Zustand**: 클라이언트 상태 관리

**UI/UX 라이브러리:**
- **Framer Motion**: 부드러운 애니메이션
- **React Spring**: 물리 기반 애니메이션
- **Styled Components**: 동적 스타일링

#### 4.1.2 백엔드 기술 스택 (분석 파일 기반)
**웹 프레임워크:**
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 직렬화

**AI/ML 서비스:**
- **OpenAI GPT-4**: 대화 생성 및 운세 해석
- **Anthropic Claude**: 안전한 대화 및 콘텐츠 필터링
- **Sentence Transformers**: 의미 유사도 분석

**데이터 저장:**
- **SQLite**: 초기 개발 및 소규모 운영용 경량 데이터베이스
- **Redis**: 세션 관리 및 실시간 캐싱
- **JSON 파일**: 운세 콘텐츠 및 설정 관리

**데이터베이스 마이그레이션 계획:**
- **단계 1 (MVP)**: SQLite 기반 프로토타입 개발
- **단계 2 (확장)**: MariaDB로 무중단 마이그레이션
- **ORM/Query Builder**: Prisma 또는 Knex.js를 통한 데이터베이스 추상화

**보안 및 모니터링:**
- **JWT**: 인증 토큰 관리
- **Rate Limiting**: API 호출 제한
- **Loguru**: 구조화된 로깅
- **Prometheus**: 성능 모니터링

### 4.2 프론트엔드/백엔드 구조

#### 4.2.1 프론트엔드 컴포넌트 구조
```javascript
src/
├── components/
│   ├── Live2D/
│   │   ├── Live2DCanvas.jsx          # Live2D 렌더링 캔버스
│   │   ├── EmotionController.jsx     # 감정 제어 시스템
│   │   ├── AnimationManager.jsx      # 애니메이션 관리
│   │   └── InteractionHandler.jsx    # 사용자 인터랙션
│   ├── Chat/
│   │   ├── ChatInterface.jsx         # 채팅 UI 컨테이너
│   │   ├── MessageBubble.jsx         # 메시지 버블
│   │   ├── InputBox.jsx              # 사용자 입력
│   │   └── TypingIndicator.jsx       # 타이핑 표시
│   ├── Fortune/
│   │   ├── FortuneSelector.jsx       # 운세 타입 선택
│   │   ├── TarotCard.jsx            # 타로 카드 컴포넌트
│   │   ├── FortuneResult.jsx        # 운세 결과 표시
│   │   └── DailyFortune.jsx         # 일일 운세 UI
│   └── UI/
│       ├── LoadingSpinner.jsx        # 로딩 애니메이션
│       ├── Modal.jsx                 # 모달 다이얼로그
│       └── NotificationToast.jsx     # 알림 토스트
├── hooks/
│   ├── useLive2D.js                 # Live2D 관리 훅
│   ├── useWebSocket.js              # WebSocket 통신
│   ├── useFortune.js                # 운세 상태 관리
│   └── useChat.js                   # 채팅 상태 관리
├── services/
│   ├── live2dService.js             # Live2D 서비스 로직
│   ├── fortuneService.js            # 운세 API 호출
│   ├── chatService.js               # 채팅 관리
│   └── audioService.js              # 음성 처리 (선택사항)
├── types/
│   ├── live2d.jsdoc.js              # Live2D JSDoc 타입 정의
│   ├── fortune.jsdoc.js             # 운세 데이터 JSDoc 타입
│   └── chat.jsdoc.js                # 채팅 메시지 JSDoc 타입
├── config/
│   ├── eslint.config.js             # ESLint 설정
│   ├── prettier.config.js           # Prettier 설정
│   └── babel.config.js              # Babel 설정
└── utils/
    ├── animations.js                # 애니메이션 유틸
    ├── formatters.js               # 데이터 포맷팅
    ├── typeValidators.js           # 런타임 타입 검증
    └── constants.js                # 상수 정의
```

#### 4.2.2 백엔드 서비스 구조
```python
src/fortune_vtuber/
├── api/
│   ├── routes/
│   │   ├── websocket.py             # WebSocket 엔드포인트
│   │   ├── fortune.py               # 운세 API
│   │   ├── chat.py                  # 채팅 API
│   │   └── live2d.py                # Live2D 제어 API
│   └── middleware/
│       ├── cors.py                  # CORS 설정
│       ├── rate_limit.py            # 속도 제한
│       └── content_filter.py        # 콘텐츠 필터링
├── services/
│   ├── fortune/
│   │   ├── daily_fortune.py         # 일일 운세 생성
│   │   ├── tarot_reader.py          # 타로 해석
│   │   ├── zodiac_fortune.py        # 별자리 운세
│   │   └── saju_reader.py           # 사주 해석
│   ├── ai/
│   │   ├── llm_service.py           # LLM 통합 서비스
│   │   ├── content_filter.py        # AI 기반 필터링
│   │   ├── emotion_analyzer.py      # 감정 분석
│   │   └── personality_engine.py    # 성격 엔진
│   ├── live2d/
│   │   ├── emotion_mapper.py        # 감정-표정 매핑
│   │   ├── animation_controller.py  # 애니메이션 제어
│   │   └── model_manager.py         # 모델 관리
│   └── chat/
│       ├── conversation_manager.py  # 대화 관리
│       ├── context_tracker.py       # 문맥 추적
│       └── response_generator.py    # 응답 생성
├── models/
│   ├── user.py                      # 사용자 모델
│   ├── fortune.py                   # 운세 데이터 모델
│   ├── chat.py                      # 채팅 모델
│   └── session.py                   # 세션 모델
├── database/
│   ├── connection.py                # DB 연결 관리
│   ├── repositories/                # 레포지토리 패턴
│   └── migrations/                  # DB 마이그레이션
└── utils/
    ├── security.py                  # 보안 유틸
    ├── cache.py                     # 캐시 관리
    └── logging.py                   # 로깅 설정
```

### 4.3 Live2D 통합 방안

#### 4.3.1 Live2D 모델 구조 설계
**운세 캐릭터 전용 모델 스펙:**
```json
{
  "modelName": "fortune_mira",
  "version": "5.0",
  "emotions": {
    "neutral": {
      "expressionIndex": 0,
      "intensity": 1.0,
      "duration": 1000
    },
    "joy": {
      "expressionIndex": 1,
      "intensity": 0.8,
      "duration": 2000
    },
    "thinking": {
      "expressionIndex": 2,
      "intensity": 0.6,
      "duration": 3000
    },
    "mystical": {
      "expressionIndex": 5,
      "intensity": 1.0,
      "duration": 4000
    }
  },
  "specialMotions": {
    "card_draw": {
      "motionFile": "card_draw.motion3.json",
      "duration": 3000,
      "soundEffect": "card_shuffle.mp3"
    },
    "crystal_gaze": {
      "motionFile": "crystal_gaze.motion3.json", 
      "duration": 4000,
      "particleEffect": "mystical_sparkles"
    },
    "blessing": {
      "motionFile": "blessing.motion3.json",
      "duration": 2500,
      "lightEffect": "golden_glow"
    }
  }
}
```

#### 4.3.2 실시간 감정 동기화 시스템
```javascript
/**
 * Live2D 감정 동기화 클래스
 * @class Live2DEmotionSync
 */
class Live2DEmotionSync {
  /**
   * @param {string} currentEmotion - 현재 감정 상태
   * @param {string[]} emotionQueue - 감정 변화 대기열
   */
  constructor() {
    /** @type {string} */
    this.currentEmotion = 'neutral';
    /** @type {string[]} */
    this.emotionQueue = [];
  }
  
  /**
   * 운세 결과에 따른 감정 동기화
   * @param {Object} fortuneData - 운세 데이터
   * @param {number} fortuneData.grade - 운세 점수
   * @param {number} fortuneData.intensity - 강도
   * @returns {Promise<void>}
   */
  async syncWithFortuneResult(fortuneData) {
    const targetEmotion = this.mapFortuneToEmotion(fortuneData.grade);
    const transitionData = {
      from: this.currentEmotion,
      to: targetEmotion,
      duration: this.calculateTransitionDuration(fortuneData.intensity),
      easing: 'easeInOutCubic'
    };
    
    await this.executeEmotionTransition(transitionData);
  }
  
  /**
   * 운세 점수를 감정으로 매핑
   * @param {number} grade - 운세 점수 (0-100)
   * @returns {string} 감정 상태
   */
  mapFortuneToEmotion(grade) {
    if (grade >= 90) return 'joy';
    if (grade >= 70) return 'mystical';
    if (grade >= 50) return 'neutral';
    if (grade >= 30) return 'thinking';
    return 'concern';
  }
}
```

## 5. Live2D 캐릭터 설계

### 5.1 캐릭터 컨셉 및 페르소나

#### 5.1.1 캐릭터 프로필
**기본 정보:**
- **이름**: 미라 (Mira)
- **나이**: 22세 (외관상)
- **직업**: 신비로운 운세 상담사
- **취미**: 별 관찰, 차 마시기, 고양이와 놀기
- **특기**: 타로 카드 읽기, 수정구 점술, 마음 읽기

**성격 특성:**
- **공감 능력**: 사용자의 감정을 세심하게 파악하고 반응
- **따뜻함**: 항상 친근하고 포용적인 태도
- **지혜로움**: 적절한 조언과 통찰력 제공
- **유머 감각**: 적절한 농담으로 분위기 전환
- **신비로움**: 운세사로서의 전문성과 신비한 매력

#### 5.1.2 대화 패턴 및 어조
**기본 어조:**
- 친근하고 다정한 반말 사용 (친구 같은 느낌)
- 이모지 적절히 활용하여 감정 표현
- 사용자 이름을 자주 불러 친밀감 조성

**상황별 대화 스타일:**
```python
CONVERSATION_STYLES = {
    "greeting": {
        "tone": "bright_and_welcoming",
        "examples": [
            "안녕하세요! 오늘도 좋은 하루 보내고 계신가요? ✨",
            "반갑습니다~ 어떤 운세가 궁금하신지 말씀해주세요!",
            "안녕하세요! 저는 미라예요. 함께 운세를 봐볼까요? 🔮"
        ]
    },
    "fortune_reading": {
        "tone": "mystical_and_focused",
        "examples": [
            "음... 카드가 말하고 있어요. 잠깐만요...",
            "오늘의 별들이 특별한 메시지를 전하고 있네요 ⭐",
            "수정구 속에서 뭔가 보이기 시작해요... 흥미롭네요!"
        ]
    },
    "comfort": {
        "tone": "warm_and_supportive", 
        "examples": [
            "괜찮아요, 힘든 시간은 누구에게나 있어요",
            "당신은 생각보다 훨씬 강한 사람이에요 💪",
            "이런 때일수록 자신을 더 사랑해주세요"
        ]
    },
    "warning": {
        "tone": "gentle_but_firm",
        "examples": [
            "앗, 그런 이야기는 제가 도와드릴 수 없어요 😅",
            "저는 건전한 운세만 봐드리고 있어요!",
            "다른 주제로 이야기해볼까요? 🌸"
        ]
    }
}
```

### 5.2 감정 표현 및 애니메이션 상태

#### 5.2.1 표정 시스템 상세 설계
```json
{
  "expressions": {
    "neutral": {
      "description": "평상시 차분하고 친근한 기본 표정",
      "eyebrows": "relaxed",
      "eyes": "gentle_gaze", 
      "mouth": "small_smile",
      "blush": 0.2,
      "usage": "대기 상태, 일반적인 대화"
    },
    "joy": {
      "description": "기쁘고 행복한 표정, 좋은 운세 발표시",
      "eyebrows": "raised",
      "eyes": "bright_crescent",
      "mouth": "wide_smile",
      "blush": 0.4,
      "sparkle_effect": true,
      "usage": "좋은 운세, 축하, 긍정적인 반응"
    },
    "thinking": {
      "description": "고민하고 생각하는 표정",
      "eyebrows": "slightly_furrowed",
      "eyes": "focused_gaze",
      "mouth": "pursed_lips",
      "head_tilt": 15,
      "usage": "운세 해석 중, 깊이 생각할 때"
    },
    "mystical": {
      "description": "신비로운 분위기의 집중된 표정",
      "eyebrows": "slightly_raised",
      "eyes": "mysterious_glow",
      "mouth": "serene_smile",
      "aura_effect": "purple_glow",
      "usage": "타로 카드 해석, 특별한 운세 공개"
    },
    "concern": {
      "description": "걱정스럽고 신중한 표정",
      "eyebrows": "worried",
      "eyes": "concerned_gaze",
      "mouth": "slight_frown",
      "usage": "나쁜 운세, 주의 사항 전달"
    },
    "surprise": {
      "description": "놀라고 신기해하는 표정",
      "eyebrows": "high_raised",
      "eyes": "wide_open",
      "mouth": "open_surprised",
      "sparkle_effect": true,
      "usage": "특별한 운세, 예상치 못한 결과"
    },
    "comfort": {
      "description": "따뜻하게 위로하는 표정",
      "eyebrows": "gentle",
      "eyes": "warm_caring",
      "mouth": "gentle_smile",
      "soft_glow": true,
      "usage": "위로, 격려, 감정적 지원"
    },
    "playful": {
      "description": "장난스럽고 재미있는 표정",
      "eyebrows": "mischievous",
      "eyes": "winking",
      "mouth": "playful_grin",
      "usage": "가벼운 농담, 재미있는 상황"
    }
  }
}
```

#### 5.2.2 모션 애니메이션 설계
```json
{
  "motions": {
    "idle": {
      "description": "기본 대기 애니메이션",
      "duration": 8000,
      "loop": true,
      "breathing": "gentle",
      "eye_blink": "natural",
      "micro_movements": "subtle_sway"
    },
    "greeting": {
      "description": "인사하는 동작",
      "duration": 3000,
      "sequence": [
        {"action": "wave_hand", "duration": 1000},
        {"action": "bow_slightly", "duration": 1000},
        {"action": "return_to_idle", "duration": 1000}
      ]
    },
    "card_draw": {
      "description": "타로 카드 뽑기 애니메이션",
      "duration": 4000,
      "sequence": [
        {"action": "extend_hand", "duration": 1000},
        {"action": "mystical_gesture", "duration": 2000},
        {"action": "reveal_card", "duration": 1000}
      ],
      "particle_effects": ["sparkles", "mystical_aura"]
    },
    "crystal_gaze": {
      "description": "수정구 들여다보는 동작",
      "duration": 5000,
      "sequence": [
        {"action": "lean_forward", "duration": 1000},
        {"action": "gaze_into_crystal", "duration": 3000},
        {"action": "nod_understanding", "duration": 1000}
      ],
      "lighting_effect": "crystal_glow"
    },
    "blessing": {
      "description": "축복하는 제스처",
      "duration": 3000,
      "sequence": [
        {"action": "raise_hands", "duration": 1000},
        {"action": "blessing_gesture", "duration": 1500},
        {"action": "gentle_lower", "duration": 500}
      ],
      "particle_effects": ["golden_sparkles"]
    },
    "thinking_pose": {
      "description": "생각하는 포즈",
      "duration": 2000,
      "sequence": [
        {"action": "hand_to_chin", "duration": 1000},
        {"action": "contemplative_hold", "duration": 1000}
      ]
    },
    "special_reading": {
      "description": "특별한 운세 읽기 동작",
      "duration": 6000,
      "sequence": [
        {"action": "close_eyes", "duration": 1000},
        {"action": "mystical_concentration", "duration": 4000},
        {"action": "revelation_gesture", "duration": 1000}
      ],
      "aura_effects": ["energy_swirl", "mystical_glow"]
    }
  }
}
```

### 5.3 음성 및 대화 패턴

#### 5.3.1 음성 설정 (TTS 기반)
**기본 음성 스펙:**
- **음성 톤**: 따뜻하고 차분한 여성 목소리
- **속도**: 표준보다 약간 느림 (신중한 느낌)
- **피치**: 중간-높음 (친근하면서 신비로운 느낌)
- **감정 표현**: 상황에 따른 톤 변화

**상황별 음성 변화:**
```python
VOICE_SETTINGS = {
    "normal": {
        "speed": 1.0,
        "pitch": 1.1,
        "volume": 0.8,
        "tone": "warm"
    },
    "excited": {
        "speed": 1.1, 
        "pitch": 1.3,
        "volume": 0.9,
        "tone": "bright"
    },
    "mystical": {
        "speed": 0.9,
        "pitch": 1.0,
        "volume": 0.7,
        "tone": "mysterious"
    },
    "comforting": {
        "speed": 0.8,
        "pitch": 1.0,
        "volume": 0.6,
        "tone": "gentle"
    }
}
```

#### 5.3.2 대화 패턴 분석 및 응답 생성
```python
class ConversationPattern:
    def __init__(self):
        self.context_memory = []
        self.user_preferences = {}
        self.conversation_state = "initial"
    
    def analyze_user_input(self, user_message: str) -> dict:
        """사용자 입력 분석"""
        analysis = {
            "intent": self.detect_intent(user_message),
            "emotion": self.detect_emotion(user_message),
            "entities": self.extract_entities(user_message),
            "sensitivity": self.check_content_sensitivity(user_message)
        }
        return analysis
    
    def generate_response(self, analysis: dict) -> dict:
        """상황에 맞는 응답 생성"""
        if analysis["sensitivity"]["is_inappropriate"]:
            return self.generate_warning_response(analysis["sensitivity"]["category"])
        
        response_data = {
            "text": self.generate_text_response(analysis),
            "emotion": self.select_appropriate_emotion(analysis),
            "motion": self.select_motion(analysis["intent"]),
            "voice_setting": self.select_voice_tone(analysis["emotion"])
        }
        
        return response_data
```

## 6. 운세 시스템 설계

### 6.1 운세 타입 분류

#### 6.1.1 일일 운세 (Daily Fortune) 상세 설계
**운세 생성 알고리즘:**
```python
class DailyFortuneGenerator:
    def __init__(self):
        self.base_factors = {
            "date": {"weight": 0.3, "source": "numerology"},
            "season": {"weight": 0.2, "source": "seasonal_energy"},
            "weekday": {"weight": 0.15, "source": "day_energy"},
            "user_birth": {"weight": 0.25, "source": "personal_cycle"},
            "randomness": {"weight": 0.1, "source": "chaos_factor"}
        }
    
    def generate_daily_fortune(self, user_data: dict, date: datetime) -> DailyFortune:
        """종합적인 일일 운세 생성"""
        scores = {}
        
        # 각 영역별 점수 계산
        scores["overall"] = self.calculate_overall_score(user_data, date)
        scores["love"] = self.calculate_love_score(user_data, date)
        scores["money"] = self.calculate_money_score(user_data, date)
        scores["health"] = self.calculate_health_score(user_data, date)
        scores["work"] = self.calculate_work_score(user_data, date)
        
        # 럭키 요소 생성
        lucky_elements = self.generate_lucky_elements(scores, date)
        
        # 조언 생성
        advice = self.generate_personalized_advice(scores, user_data)
        
        return DailyFortune(
            date=date,
            scores=scores,
            lucky_elements=lucky_elements,
            advice=advice,
            emotion=self.map_score_to_emotion(scores["overall"])
        )
```

**영역별 상세 해석:**
```python
FORTUNE_CATEGORIES = {
    "love": {
        "name": "연애운",
        "icon": "💕",
        "score_ranges": {
            (90, 100): {
                "grade": "최고",
                "message": "운명적인 만남이 기다리고 있어요!",
                "advice": "적극적으로 마음을 표현해보세요",
                "color": "#FF69B4"
            },
            (70, 89): {
                "grade": "좋음", 
                "message": "달콤한 인연의 기운이 흐르고 있어요",
                "advice": "자연스러운 만남의 기회를 놓치지 마세요",
                "color": "#FFB6C1"
            },
            (50, 69): {
                "grade": "보통",
                "message": "평온한 관계를 유지할 수 있어요",
                "advice": "기존 관계를 더욱 소중히 여기세요",
                "color": "#DDA0DD"
            },
            (30, 49): {
                "grade": "주의",
                "message": "작은 오해가 생길 수 있어요",
                "advice": "상대방의 입장에서 생각해보세요",
                "color": "#D8BFD8"
            },
            (0, 29): {
                "grade": "조심",
                "message": "갈등이 생길 수 있는 시기예요",
                "advice": "감정적인 대화는 피하는 것이 좋겠어요",
                "color": "#BC8F8F"
            }
        }
    },
    "money": {
        "name": "금전운",
        "icon": "💰",
        "score_ranges": {
            (90, 100): {
                "grade": "대박",
                "message": "뜻밖의 금전적 행운이 올 수 있어요!",
                "advice": "투자나 새로운 기회를 고려해보세요"
            },
            (70, 89): {
                "grade": "좋음",
                "message": "안정적인 수입과 작은 행운이 있어요",
                "advice": "계획적인 소비가 더 큰 행운을 불러올 거예요"
            }
            # ... 다른 범위들
        }
    }
    # ... 다른 카테고리들
}
```

#### 6.1.2 타로 카드 시스템
**메이저 아르카나 22장 기본 구성:**
```python
MAJOR_ARCANA = {
    0: {
        "name": "The Fool",
        "korean_name": "광대",
        "keywords": ["새로운 시작", "순수함", "모험", "자유"],
        "love_meaning": "순수한 마음으로 시작되는 새로운 인연",
        "career_meaning": "새로운 기회와 도전의 시작",
        "general_meaning": "인생의 새로운 전환점",
        "advice": "두려워하지 말고 용기를 내세요",
        "reversed_meaning": "무모함, 경솔한 판단을 조심하세요",
        "emotion": "joy",
        "color": "#FFD700"
    },
    1: {
        "name": "The Magician", 
        "korean_name": "마법사",
        "keywords": ["의지력", "창조", "능력", "집중"],
        "love_meaning": "적극적인 어프로치가 성공을 부를 때",
        "career_meaning": "뛰어난 능력으로 목표를 달성할 수 있음",
        "general_meaning": "강한 의지로 원하는 것을 이룰 수 있음",
        "advice": "자신의 능력을 믿고 집중하세요",
        "emotion": "mystical",
        "color": "#8A2BE2"
    }
    # ... 21장까지 정의
}
```

**타로 스프레드 시스템:**
```python
TAROT_SPREADS = {
    "three_card": {
        "name": "과거-현재-미래",
        "positions": [
            {"name": "과거", "description": "과거의 영향과 원인"},
            {"name": "현재", "description": "현재 상황과 에너지"},
            {"name": "미래", "description": "앞으로의 가능성과 방향"}
        ],
        "interpretation_method": "chronological_flow"
    },
    "love_triangle": {
        "name": "연애 삼각 스프레드",
        "positions": [
            {"name": "당신의 마음", "description": "현재 당신의 감정 상태"},
            {"name": "상대방의 마음", "description": "상대방의 마음과 의도"},
            {"name": "관계의 미래", "description": "두 사람의 관계 발전 가능성"}
        ],
        "interpretation_method": "relationship_focused"
    }
}
```

#### 6.1.3 별자리 운세 시스템
```python
ZODIAC_SIGNS = {
    "aries": {
        "name": "양자리",
        "date_range": "3/21 - 4/19",
        "element": "fire",
        "traits": ["열정적", "도전적", "리더십", "즉흥적"],
        "compatible_signs": ["leo", "sagittarius", "gemini", "aquarius"],
        "lucky_colors": ["red", "orange"],
        "lucky_numbers": [1, 8, 17],
        "personality": {
            "strengths": ["용기 있음", "열정적", "독립적", "결단력 있음"],
            "weaknesses": ["성급함", "참을성 부족", "고집이 셈"],
            "love_style": "적극적이고 직접적인 어프로치"
        }
    }
    # ... 12성좌 모두 정의
}
```

### 6.2 질문-답변 플로우

#### 6.2.1 정보 수집 시퀀스
**단계별 정보 수집:**
```python
class FortuneInformationCollector:
    def __init__(self):
        self.required_info = {
            "basic": ["name", "birth_date"],
            "optional": ["birth_time", "birth_place", "relationship_status"],
            "contextual": ["current_concern", "specific_question"]
        }
    
    def start_collection_flow(self, fortune_type: str) -> List[Question]:
        """운세 타입별 맞춤형 질문 생성"""
        questions = []
        
        if fortune_type == "daily":
            questions = [
                Question("어떻게 불러드리면 될까요?", "name", required=False),
                Question("생년월일을 알려주시면 더 정확한 운세를 봐드릴 수 있어요!", "birth_date", required=False),
                Question("오늘 특별히 궁금한 분야가 있나요?", "focus_area", options=["연애", "직장", "금전", "건강", "전체"])
            ]
        elif fortune_type == "tarot":
            questions = [
                Question("타로에게 물어보고 싶은 질문이 있나요?", "question", required=True),
                Question("어떤 분야에 대한 질문인가요?", "category", options=["연애", "직장", "인간관계", "개인성장", "기타"]),
                Question("마음속으로 그 상황을 생각하면서 깊게 숨을 한 번 쉬어주세요", "meditation", type="pause")
            ]
        
        return questions
```

#### 6.2.2 대화형 정보 수집
```python
class ConversationalCollector:
    async def collect_birth_info(self, websocket, user_message: str):
        """자연스러운 대화로 생년월일 수집"""
        if self.extract_birth_date(user_message):
            await self.send_response(websocket, {
                "text": "생년월일을 알려주셔서 감사해요! 더 정확한 운세를 봐드릴 수 있겠어요 ✨",
                "emotion": "joy",
                "motion": "blessing"
            })
        else:
            await self.send_response(websocket, {
                "text": "혹시 생년월일도 알려주실 수 있나요? 예를 들어 '1995년 3월 15일' 이런 식으로요!",
                "emotion": "thinking",
                "motion": "thinking_pose"
            })
    
    def extract_birth_date(self, message: str) -> Optional[datetime]:
        """메시지에서 생년월일 추출"""
        # 정규표현식을 이용한 날짜 패턴 매칭
        patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]
        # ... 패턴 매칭 로직
```

### 6.3 결과 생성 로직

#### 6.3.1 개인화된 운세 생성
```python
class PersonalizedFortuneEngine:
    def __init__(self):
        self.ai_client = OpenAIClient()
        self.template_manager = FortuneTemplateManager()
        self.personality_analyzer = PersonalityAnalyzer()
    
    async def generate_personalized_fortune(self, user_data: dict, fortune_type: str) -> FortuneResult:
        """개인화된 운세 생성"""
        
        # 1. 사용자 성향 분석
        personality_profile = await self.personality_analyzer.analyze(user_data)
        
        # 2. 기본 운세 데이터 생성
        base_fortune = self.generate_base_fortune(fortune_type, user_data)
        
        # 3. AI를 통한 개인화된 해석
        personalized_content = await self.ai_client.generate_personalized_interpretation(
            base_fortune=base_fortune,
            personality=personality_profile,
            user_context=user_data.get("context", {})
        )
        
        # 4. Live2D 애니메이션 매핑
        animation_data = self.map_fortune_to_animation(personalized_content)
        
        return FortuneResult(
            content=personalized_content,
            animation=animation_data,
            user_specific=True,
            generated_at=datetime.now()
        )
```

#### 6.3.2 AI 기반 해석 시스템
```python
FORTUNE_PROMPT_TEMPLATES = {
    "daily_fortune": """
당신은 따뜻하고 지혜로운 운세 상담사 미라입니다.
사용자 정보:
- 이름: {user_name}
- 생년월일: {birth_date}
- 관심 분야: {focus_area}

오늘 날짜: {current_date}
기본 운세 점수: {base_scores}

다음 지침을 따라 운세를 해석해주세요:
1. 친근하고 따뜻한 말투 사용
2. 구체적이고 실용적인 조언 제공
3. 긍정적인 메시지와 희망적인 전망
4. 사용자의 성향을 고려한 맞춤형 조언
5. 재미있고 흥미로운 표현 사용

운세 해석:
""",
    
    "tarot_reading": """
당신은 신비로운 타로 마스터 미라입니다.
선택된 카드:
{selected_cards}

사용자 질문: {user_question}
질문 카테고리: {question_category}

다음 스타일로 타로 해석을 해주세요:
1. 각 카드의 의미를 명확히 설명
2. 카드들 간의 연관성과 스토리 구성
3. 사용자 질문에 대한 직접적인 답변
4. 실행 가능한 조언과 행동 지침
5. 신비롭지만 이해하기 쉬운 표현

타로 해석:
"""
}
```

### 6.4 데이터베이스 설계

#### 6.4.1 SQLite 기반 초기 스키마 설계

**핵심 테이블 구조:**
```sql
-- 사용자 정보 테이블
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    nickname TEXT,
    birth_date DATE,
    gender TEXT CHECK(gender IN ('M', 'F', 'O')),
    zodiac_sign TEXT,
    preferences TEXT, -- JSON 형태로 저장
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 운세 기록 테이블
CREATE TABLE fortune_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    fortune_type TEXT NOT NULL CHECK(fortune_type IN ('daily', 'tarot', 'zodiac', 'saju')),
    fortune_date DATE NOT NULL,
    content TEXT NOT NULL, -- JSON 형태로 저장
    scores TEXT, -- JSON 형태 점수 데이터
    advice TEXT,
    emotion_state TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 채팅 기록 테이블
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_start DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_end DATETIME,
    message_count INTEGER DEFAULT 0,
    context_data TEXT, -- JSON 형태 대화 맥락
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 개별 메시지 테이블
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER,
    sender TEXT NOT NULL CHECK(sender IN ('user', 'mira')),
    message TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    emotion TEXT,
    is_filtered BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

-- 타로 카드 기록 테이블
CREATE TABLE tarot_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    reading_date DATE NOT NULL,
    spread_type TEXT NOT NULL,
    cards_drawn TEXT NOT NULL, -- JSON 배열
    interpretation TEXT,
    user_question TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 시스템 설정 테이블
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 6.4.2 데이터베이스 추상화 레이어

**Prisma를 활용한 데이터베이스 추상화:**
```javascript
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model User {
  id          Int      @id @default(autoincrement())
  sessionId   String   @unique @map("session_id")
  nickname    String?
  birthDate   DateTime? @map("birth_date")
  gender      String?
  zodiacSign  String?   @map("zodiac_sign")
  preferences Json?
  createdAt   DateTime @default(now()) @map("created_at")
  lastActive  DateTime @default(now()) @map("last_active")

  // Relations
  fortunes     FortuneRecord[]
  chatSessions ChatSession[]
  tarotReadings TarotReading[]

  @@map("users")
}

model FortuneRecord {
  id          Int      @id @default(autoincrement())
  userId      Int      @map("user_id")
  fortuneType String   @map("fortune_type")
  fortuneDate DateTime @map("fortune_date")
  content     Json
  scores      Json?
  advice      String?
  emotionState String? @map("emotion_state")
  createdAt   DateTime @default(now()) @map("created_at")

  // Relations
  user User @relation(fields: [userId], references: [id], onDelete: Cascade)

  @@map("fortune_records")
}
```

#### 6.4.3 MariaDB 마이그레이션 전략

**단계별 마이그레이션 계획:**
```javascript
/**
 * 데이터베이스 마이그레이션 관리자
 * @class DatabaseMigrationManager
 */
class DatabaseMigrationManager {
  constructor() {
    /** @type {Object} */
    this.migrationSteps = {
      phase1: 'SQLite 기반 MVP 운영',
      phase2: 'MariaDB 환경 구축 및 테스트',
      phase3: '데이터 마이그레이션 및 검증',
      phase4: 'MariaDB 완전 전환'
    };
  }

  /**
   * 마이그레이션 실행
   * @param {string} targetPhase - 목표 단계
   * @returns {Promise<boolean>}
   */
  async executeMigration(targetPhase) {
    switch(targetPhase) {
      case 'phase2':
        return await this.setupMariaDBEnvironment();
      case 'phase3':
        return await this.migrateData();
      case 'phase4':
        return await this.switchToMariaDB();
      default:
        throw new Error('Unknown migration phase');
    }
  }

  /**
   * MariaDB 환경 구축
   * @returns {Promise<boolean>}
   */
  async setupMariaDBEnvironment() {
    // MariaDB 스키마 생성
    const mariaDbSchema = this.convertSQLiteToMariaDB();
    
    // 연결 풀 설정
    const poolConfig = {
      host: process.env.MARIADB_HOST,
      user: process.env.MARIADB_USER,
      password: process.env.MARIADB_PASSWORD,
      database: process.env.MARIADB_DATABASE,
      connectionLimit: 10,
      acquireTimeout: 60000,
      timeout: 60000
    };

    return await this.validateMariaDBSetup(poolConfig);
  }

  /**
   * 데이터 마이그레이션
   * @returns {Promise<boolean>}
   */
  async migrateData() {
    const batchSize = 1000;
    const tables = ['users', 'fortune_records', 'chat_sessions', 'chat_messages'];
    
    for (const table of tables) {
      await this.migrateBatchData(table, batchSize);
    }
    
    return await this.validateDataIntegrity();
  }
}
```

#### 6.4.4 성능 최적화 및 인덱싱

**SQLite 최적화:**
```sql
-- 자주 조회되는 컬럼에 인덱스 생성
CREATE INDEX idx_users_session_id ON users(session_id);
CREATE INDEX idx_fortune_records_user_date ON fortune_records(user_id, fortune_date);
CREATE INDEX idx_chat_messages_session_timestamp ON chat_messages(session_id, timestamp);
CREATE INDEX idx_tarot_readings_user_date ON tarot_readings(user_id, reading_date);

-- SQLite 성능 튜닝
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
```

**데이터 정리 및 보관 정책:**
```javascript
/**
 * 데이터 생명주기 관리
 * @class DataLifecycleManager
 */
class DataLifecycleManager {
  constructor() {
    /** @type {Object} */
    this.retentionPolicies = {
      chat_messages: 30, // 30일
      fortune_records: 365, // 1년
      tarot_readings: 365, // 1년
      users: 1095 // 3년 (비활성 사용자)
    };
  }

  /**
   * 오래된 데이터 정리
   * @returns {Promise<void>}
   */
  async cleanupOldData() {
    for (const [table, days] of Object.entries(this.retentionPolicies)) {
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      
      await this.deleteOldRecords(table, cutoffDate);
    }
  }

  /**
   * 데이터 압축 및 아카이빙
   * @param {string} table - 테이블 명
   * @returns {Promise<void>}
   */
  async archiveOldData(table) {
    // 오래된 데이터를 JSON 파일로 압축 저장
    const oldData = await this.selectOldRecords(table);
    await this.compressAndStore(oldData, `archive_${table}_${Date.now()}.json.gz`);
  }
}
```

## 7. UI/UX 설계

### 7.1 화면 구성 및 레이아웃

#### 7.1.1 메인 인터페이스 구성
```css
/* 전체 레이아웃 구조 */
.fortune-app {
  display: grid;
  grid-template-areas: 
    "character character"
    "chat-input fortune-panel";
  grid-template-rows: 1fr auto;
  grid-template-columns: 1fr 1fr;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.character-area {
  grid-area: character;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  overflow: hidden;
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  max-width: 800px;
  max-height: 600px;
}

.chat-interface {
  grid-area: chat-input;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px 20px 0 0;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.fortune-panel {
  grid-area: fortune-panel;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px 0 0 0;
  padding: 20px;
  overflow-y: auto;
}
```

#### 7.1.2 반응형 레이아웃
```css
/* 태블릿 레이아웃 */
@media (max-width: 1024px) {
  .fortune-app {
    grid-template-areas: 
      "character"
      "chat-input"
      "fortune-panel";
    grid-template-rows: 1fr auto auto;
    grid-template-columns: 1fr;
  }
  
  .character-area {
    height: 50vh;
  }
  
  .fortune-panel {
    max-height: 30vh;
  }
}

/* 모바일 레이아웃 */
@media (max-width: 768px) {
  .fortune-app {
    grid-template-areas: 
      "character"
      "chat-input";
    grid-template-rows: 1fr auto;
  }
  
  .character-area {
    height: 60vh;
  }
  
  .fortune-panel {
    position: fixed;
    bottom: 100px;
    left: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.95);
    border-radius: 15px;
    max-height: 50vh;
    transform: translateY(100%);
    transition: transform 0.3s ease;
  }
  
  .fortune-panel.visible {
    transform: translateY(0);
  }
}
```

### 7.2 인터랙션 디자인

#### 7.2.1 채팅 인터페이스 UX
```javascript
/**
 * 채팅 메시지 타입 정의
 * @typedef {Object} ChatMessage
 * @property {string} id - 메시지 고유 ID
 * @property {'user'|'mira'} sender - 메시지 발신자
 * @property {string} content - 메시지 내용
 * @property {Date} timestamp - 전송 시간
 * @property {string} [emotion] - 감정 타입 (선택사항)
 * @property {string} [animation] - 애니메이션 (선택사항)
 * @property {boolean} [isTyping] - 타이핑 상태 (선택사항)
 */

/**
 * 채팅 버블 컴포넌트
 * @param {Object} props - 컴포넌트 props
 * @param {ChatMessage} props.message - 채팅 메시지 객체
 * @returns {JSX.Element}
 */
const ChatBubble = ({ message }) => {
  return (
    <motion.div
      className={`chat-bubble ${message.sender}`}
      initial={{ opacity: 0, y: 20, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {message.sender === 'mira' && (
        <div className="character-avatar">
          <img src="/avatars/mira.png" alt="미라" />
          <div className={`emotion-indicator ${message.emotion}`} />
        </div>
      )}
      
      <div className="message-content">
        {message.isTyping ? (
          <TypingIndicator />
        ) : (
          <div className="message-text">
            {message.content}
          </div>
        )}
        <div className="message-time">
          {format(message.timestamp, 'HH:mm')}
        </div>
      </div>
    </motion.div>
  );
};
```

#### 7.2.2 타로 카드 인터랙션
```javascript
/**
 * 타로 카드 선택 컴포넌트
 * @returns {JSX.Element}
 */
const TarotCardSelector = () => {
  /** @type {[number[], Function]} */
  const [selectedCards, setSelectedCards] = useState([]);
  /** @type {[boolean, Function]} */
  const [isRevealing, setIsRevealing] = useState(false);
  
  const handleCardSelect = async (cardIndex: number) => {
    if (selectedCards.length >= 3) return;
    
    // 카드 선택 애니메이션
    await animateCardSelection(cardIndex);
    
    // Live2D 캐릭터 반응
    triggerCharacterReaction('card_selected', cardIndex);
    
    setSelectedCards(prev => [...prev, cardIndex]);
    
    if (selectedCards.length === 2) {
      // 3장 모두 선택됨
      setTimeout(() => {
        setIsRevealing(true);
        revealTarotReading(selectedCards);
      }, 1000);
    }
  };
  
  return (
    <div className="tarot-deck">
      {TAROT_CARDS.map((card, index) => (
        <motion.div
          key={card.id}
          className={`tarot-card ${selectedCards.includes(index) ? 'selected' : ''}`}
          onClick={() => handleCardSelect(index)}
          whileHover={{ scale: 1.05, y: -10 }}
          whileTap={{ scale: 0.95 }}
          layout
        >
          <div className="card-back">
            <div className="mystical-pattern" />
          </div>
          {isRevealing && selectedCards.includes(index) && (
            <motion.div
              className="card-front"
              initial={{ rotateY: 180 }}
              animate={{ rotateY: 0 }}
              transition={{ duration: 0.8, delay: index * 0.3 }}
            >
              <img src={card.image} alt={card.name} />
              <div className="card-name">{card.korean_name}</div>
            </motion.div>
          )}
        </motion.div>
      ))}
    </div>
  );
};
```

#### 7.2.3 운세 결과 표시 애니메이션
```typescript
const FortuneResultDisplay: React.FC<{fortune: FortuneResult}> = ({ fortune }) => {
  const [currentSection, setCurrentSection] = useState(0);
  
  useEffect(() => {
    // 섹션별 순차적 표시
    const timer = setInterval(() => {
      setCurrentSection(prev => {
        if (prev < fortune.sections.length - 1) {
          return prev + 1;
        }
        clearInterval(timer);
        return prev;
      });
    }, 2000);
    
    return () => clearInterval(timer);
  }, [fortune]);
  
  return (
    <div className="fortune-result">
      <motion.div
        className="fortune-header"
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h2>{fortune.title}</h2>
        <div className="overall-score">
          <CircularProgress 
            value={fortune.overallScore} 
            color={getScoreColor(fortune.overallScore)}
            animationDuration={2000}
          />
        </div>
      </motion.div>
      
      <AnimatePresence>
        {fortune.sections.map((section, index) => (
          index <= currentSection && (
            <motion.div
              key={section.id}
              className="fortune-section"
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.5 }}
            >
              <div className="section-icon">{section.icon}</div>
              <div className="section-content">
                <h3>{section.title}</h3>
                <div className="section-score">
                  {section.score}점
                </div>
                <p>{section.description}</p>
                {section.advice && (
                  <div className="advice-box">
                    <strong>💡 조언:</strong> {section.advice}
                  </div>
                )}
              </div>
            </motion.div>
          )
        ))}
      </AnimatePresence>
      
      {fortune.luckyElements && (
        <motion.div
          className="lucky-elements"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: fortune.sections.length * 0.5 }}
        >
          <h3>🍀 오늘의 럭키 아이템</h3>
          <div className="lucky-grid">
            <div className="lucky-item">
              <span className="lucky-label">럭키 컬러</span>
              <div 
                className="lucky-color" 
                style={{ backgroundColor: fortune.luckyElements.color }}
              />
            </div>
            <div className="lucky-item">
              <span className="lucky-label">럭키 넘버</span>
              <span className="lucky-number">{fortune.luckyElements.number}</span>
            </div>
            <div className="lucky-item">
              <span className="lucky-label">럭키 아이템</span>
              <span className="lucky-object">{fortune.luckyElements.item}</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};
```

### 7.3 반응형 웹 고려사항

#### 7.3.1 디바이스별 최적화
```typescript
const useResponsiveLayout = () => {
  const [deviceType, setDeviceType] = useState<'mobile' | 'tablet' | 'desktop'>('desktop');
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      if (width < 768) {
        setDeviceType('mobile');
      } else if (width < 1024) {
        setDeviceType('tablet');
      } else {
        setDeviceType('desktop');
      }
      
      setOrientation(width > height ? 'landscape' : 'portrait');
    };
    
    window.addEventListener('resize', handleResize);
    handleResize();
    
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return { deviceType, orientation };
};

// Live2D 캔버스 반응형 처리
const ResponsiveLive2DCanvas: React.FC = () => {
  const { deviceType, orientation } = useResponsiveLayout();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  const getCanvasSize = () => {
    switch (deviceType) {
      case 'mobile':
        return orientation === 'portrait' 
          ? { width: window.innerWidth * 0.9, height: window.innerHeight * 0.6 }
          : { width: window.innerWidth * 0.5, height: window.innerHeight * 0.8 };
      case 'tablet':
        return { width: 600, height: 450 };
      case 'desktop':
        return { width: 800, height: 600 };
    }
  };
  
  useEffect(() => {
    if (canvasRef.current) {
      const { width, height } = getCanvasSize();
      canvasRef.current.width = width;
      canvasRef.current.height = height;
      
      // Live2D 모델 스케일 조정
      adjustLive2DScale(width / 800); // 기준 크기 대비 비율
    }
  }, [deviceType, orientation]);
  
  return (
    <canvas
      ref={canvasRef}
      className="live2d-canvas"
      style={{
        maxWidth: '100%',
        maxHeight: '100%',
        objectFit: 'contain'
      }}
    />
  );
};
```

#### 7.3.2 터치 최적화
```typescript
const TouchOptimizedChat: React.FC = () => {
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  
  useEffect(() => {
    // 가상 키보드 감지
    const handleResize = () => {
      const viewportHeight = window.visualViewport?.height || window.innerHeight;
      const windowHeight = window.innerHeight;
      
      setIsKeyboardVisible(viewportHeight < windowHeight * 0.75);
    };
    
    window.visualViewport?.addEventListener('resize', handleResize);
    return () => window.visualViewport?.removeEventListener('resize', handleResize);
  }, []);
  
  return (
    <div className={`chat-container ${isKeyboardVisible ? 'keyboard-visible' : ''}`}>
      {/* 채팅 내용 */}
      <div className="chat-messages">
        {/* 메시지들 */}
      </div>
      
      {/* 입력 영역 */}
      <div className="chat-input-area">
        <input
          type="text"
          placeholder="메시지를 입력하세요..."
          style={{
            fontSize: '16px', // iOS 줌 방지
            padding: '12px',
            minHeight: '44px' // iOS 터치 가이드라인
          }}
        />
        <button className="send-button">전송</button>
      </div>
    </div>
  );
};
```

## 8. 개발 로드맵

### 8.1 단계별 개발 계획

#### 8.1.1 Phase 1: MVP 개발 (4주)
**주차별 목표:**

**1주차: 기본 인프라 구축**
- FastAPI 백엔드 서버 설정
- React + JavaScript 프론트엔드 환경 구축
- WebSocket 기본 통신 구현
- Live2D 기본 렌더링 시스템 구축

**작업 항목:**
```
Backend:
- [x] FastAPI 프로젝트 초기 설정
- [x] WebSocket 연결 관리 시스템
- [x] 기본 라우팅 구조
- [x] CORS 설정 및 미들웨어

Frontend:
- [x] React + Vite 프로젝트 설정
- [x] JavaScript ES6+ 설정 및 JSDoc 타입 정의
- [x] ESLint + Prettier 코드 품질 도구 설정
- [x] Live2D SDK 통합
- [x] 기본 컴포넌트 구조 설계

Database:
- [x] SQLite 데이터베이스 초기 설정
- [x] Prisma ORM 통합 및 스키마 정의
- [x] 기본 테이블 구조 생성
```

**2주차: Live2D 캐릭터 통합**
- Live2D 모델 로딩 및 렌더링
- 기본 표정 시스템 구현
- 마우스 인터랙션 추가
- 기본 애니메이션 시스템

**작업 항목:**
```
Live2D Integration:
- [x] 모델 로딩 시스템
- [x] 8가지 기본 표정 구현
- [x] 아이들 애니메이션
- [x] 마우스 추적 기능
- [x] 클릭 인터랙션
```

**3주차: 채팅 시스템 개발**
- 실시간 채팅 UI 구현
- 메시지 타이핑 애니메이션
- 기본 대화 플로우
- 콘텐츠 필터링 시스템

**작업 항목:**
```
Chat System:
- [x] 채팅 UI 컴포넌트
- [x] 실시간 메시지 전송/수신
- [x] 타이핑 인디케이터
- [x] 기본 콘텐츠 필터
- [x] 대화 히스토리 저장
```

**4주차: 기본 운세 시스템**
- 일일 운세 생성 로직
- 운세 결과 UI
- Live2D 캐릭터 연동
- 기본 테스트 및 버그 수정

**작업 항목:**
```
Fortune System:
- [x] 일일 운세 생성 알고리즘
- [x] 운세 결과 표시 UI
- [x] Live2D 감정 연동
- [x] 기본 사용자 테스트
```

#### 8.1.2 Phase 2: 기능 확장 (6주)
**5-6주차: 타로 카드 시스템**
- 타로 카드 UI 구현
- 카드 선택 애니메이션
- 타로 해석 시스템
- 3카드 스프레드 구현

**7-8주차: AI 통합 강화**
- OpenAI GPT 통합
- 개인화된 대화 시스템
- 향상된 콘텐츠 필터링
- 감정 분석 시스템

**9-10주차: 사용자 경험 개선**
- 별자리 운세 추가
- 사용자 프로필 시스템
- 운세 히스토리 관리
- 모바일 최적화

#### 8.1.3 Phase 3: 고도화 및 배포 (4주)
**11-12주차: 성능 최적화**
- Live2D 렌더링 최적화
- 메모리 사용량 최적화
- 네트워크 트래픽 최적화
- 캐싱 시스템 구현

**13주차: 보안 강화**
- 고급 콘텐츠 필터링
- 사용자 보호 기능
- 로깅 및 모니터링
- 보안 취약점 점검

**14주차: 배포 및 런칭**
- 프로덕션 환경 설정
- CI/CD 파이프라인 구축
- 성능 모니터링 설정
- 사용자 피드백 수집 시스템

### 8.2 우선순위 및 일정

#### 8.2.1 핵심 기능 우선순위
```python
PRIORITY_MATRIX = {
    "P0": [  # 필수 기능 (MVP)
        "Live2D 기본 렌더링",
        "실시간 채팅 시스템", 
        "일일 운세 생성",
        "기본 콘텐츠 필터링",
        "반응형 웹 디자인"
    ],
    "P1": [  # 중요 기능
        "타로 카드 시스템",
        "AI 기반 개인화",
        "별자리 운세",
        "사용자 프로필",
        "음성 지원 (TTS)"
    ],
    "P2": [  # 개선 기능
        "사주 운세",
        "소셜 공유",
        "운세 히스토리 분석",
        "다국어 지원",
        "푸시 알림"
    ],
    "P3": [  # 추가 기능
        "VR/AR 지원",
        "멀티 캐릭터",
        "프리미엄 운세",
        "실시간 그룹 상담",
        "API 개방"
    ]
}
```

#### 8.2.2 리스크 관리 및 대응 계획
```python
RISK_MITIGATION = {
    "Live2D_성능_이슈": {
        "위험도": "HIGH",
        "영향": "사용자 경험 저하, 모바일 기기 배터리 소모",
        "대응": [
            "LOD(Level of Detail) 시스템 구현",
            "텍스처 압축 및 최적화",
            "프레임 레이트 제한 옵션",
            "경량화 모드 제공"
        ],
        "예상_시간": "2주"
    },
    "AI_API_비용": {
        "위험도": "MEDIUM",
        "영향": "운영 비용 증가",
        "대응": [
            "응답 캐싱 시스템",
            "사용량 제한 및 모니터링",
            "오픈소스 모델 대안 준비",
            "요청 최적화"
        ],
        "예상_시간": "1주"
    },
    "콘텐츠_필터링_우회": {
        "위험도": "HIGH",
        "영향": "서비스 품질 저하, 사용자 신뢰 손실",
        "대응": [
            "다층 필터링 시스템",
            "실시간 모니터링",
            "사용자 신고 시스템",
            "AI 기반 감지 강화"
        ],
        "예상_시간": "지속적"
    }
}
```

### 8.3 기술적 위험 요소 및 대응

#### 8.3.1 Live2D 성능 최적화
```typescript
class Live2DPerformanceManager {
  private frameRate: number = 60;
  private qualityLevel: 'high' | 'medium' | 'low' = 'high';
  private isOptimizationEnabled: boolean = false;
  
  async optimizeForDevice() {
    const deviceCapability = await this.assessDeviceCapability();
    
    if (deviceCapability.score < 50) {
      this.enableOptimizations();
    }
  }
  
  private enableOptimizations() {
    this.frameRate = 30;
    this.qualityLevel = 'medium';
    this.isOptimizationEnabled = true;
    
    // 텍스처 품질 조정
    this.adjustTextureQuality();
    
    // 물리 시뮬레이션 간소화
    this.simplifyPhysics();
    
    // 불필요한 애니메이션 비활성화
    this.disableNonEssentialAnimations();
  }
}
```

#### 8.3.2 확장성 고려사항
```python
class ScalabilityPlanning:
    def __init__(self):
        self.concurrent_users_target = {
            "phase_1": 100,      # MVP
            "phase_2": 1000,     # 베타
            "phase_3": 10000,    # 정식 런칭
            "phase_4": 100000    # 확장
        }
    
    def plan_infrastructure(self, phase: str):
        requirements = self.concurrent_users_target[phase]
        
        return {
            "servers": self.calculate_server_needs(requirements),
            "database": self.plan_database_scaling(requirements),
            "caching": self.plan_caching_strategy(requirements),
            "cdn": self.plan_cdn_strategy(requirements)
        }
    
    def calculate_server_needs(self, users: int):
        # 사용자당 평균 리소스 사용량 기반 계산
        cpu_per_user = 0.1  # CPU 코어
        memory_per_user = 10  # MB
        
        return {
            "cpu_cores": users * cpu_per_user,
            "memory_gb": (users * memory_per_user) / 1024,
            "websocket_connections": users,
            "estimated_cost": self.calculate_hosting_cost(users)
        }
```

### 8.4 JavaScript 개발 환경 및 도구 체인

#### 8.4.1 JavaScript 코드 품질 관리

**ESLint 설정:**
```javascript
// .eslintrc.js
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'prettier'
  ],
  parserOptions: {
    ecmaFeatures: {
      jsx: true
    },
    ecmaVersion: 12,
    sourceType: 'module'
  },
  plugins: [
    'react',
    'react-hooks',
    'jsdoc'
  ],
  rules: {
    // 코드 품질 규칙
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'no-console': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    
    // React 특화 규칙
    'react/prop-types': 'off', // JSDoc을 사용하므로 비활성화
    'react/react-in-jsx-scope': 'off', // React 17+ 에서 불필요
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // JSDoc 문서화 규칙
    'jsdoc/require-description': 'warn',
    'jsdoc/require-param-description': 'warn',
    'jsdoc/require-returns-description': 'warn',
    'jsdoc/check-types': 'error'
  },
  settings: {
    react: {
      version: 'detect'
    }
  }
};
```

**Prettier 설정:**
```javascript
// .prettierrc.js
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  quoteProps: 'as-needed',
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'avoid',
  endOfLine: 'lf',
  // React JSX 설정
  jsxSingleQuote: true,
  jsxBracketSameLine: false
};
```

#### 8.4.2 JSDoc 기반 타입 안전성

**타입 정의 파일 구조:**
```javascript
// types/live2d.jsdoc.js
/**
 * Live2D 모델 설정 타입
 * @typedef {Object} Live2DModelConfig
 * @property {string} modelPath - 모델 파일 경로
 * @property {EmotionConfig[]} emotions - 감정 설정 배열
 * @property {MotionConfig[]} motions - 모션 설정 배열
 * @property {number} scale - 모델 크기 배율
 */

/**
 * 감정 설정 타입
 * @typedef {Object} EmotionConfig
 * @property {string} name - 감정 이름
 * @property {number} expressionIndex - 표정 인덱스
 * @property {number} intensity - 강도 (0-1)
 * @property {number} duration - 지속시간 (ms)
 */

/**
 * 모션 설정 타입
 * @typedef {Object} MotionConfig
 * @property {string} name - 모션 이름
 * @property {string} motionFile - 모션 파일 경로
 * @property {number} duration - 지속시간 (ms)
 * @property {string} [soundEffect] - 사운드 이펙트 (선택사항)
 */
```

**런타임 타입 검증:**
```javascript
// utils/typeValidators.js
/**
 * 타입 검증 유틸리티 클래스
 */
class TypeValidator {
  /**
   * 채팅 메시지 유효성 검증
   * @param {Object} message - 검증할 메시지 객체
   * @returns {boolean} 유효성 여부
   */
  static validateChatMessage(message) {
    const required = ['id', 'sender', 'content', 'timestamp'];
    const validSenders = ['user', 'mira'];
    
    // 필수 필드 확인
    for (const field of required) {
      if (!(field in message)) {
        console.error(`Missing required field: ${field}`);
        return false;
      }
    }
    
    // 발신자 유효성 확인
    if (!validSenders.includes(message.sender)) {
      console.error(`Invalid sender: ${message.sender}`);
      return false;
    }
    
    // 타임스탬프 타입 확인
    if (!(message.timestamp instanceof Date)) {
      console.error('Timestamp must be a Date object');
      return false;
    }
    
    return true;
  }

  /**
   * 운세 결과 유효성 검증
   * @param {Object} fortune - 검증할 운세 객체
   * @returns {boolean} 유효성 여부
   */
  static validateFortuneResult(fortune) {
    const requiredFields = ['type', 'content', 'scores', 'advice'];
    const validTypes = ['daily', 'tarot', 'zodiac', 'saju'];
    
    // 기본 구조 검증
    for (const field of requiredFields) {
      if (!(field in fortune)) {
        console.error(`Missing fortune field: ${field}`);
        return false;
      }
    }
    
    // 운세 타입 검증
    if (!validTypes.includes(fortune.type)) {
      console.error(`Invalid fortune type: ${fortune.type}`);
      return false;
    }
    
    // 점수 유효성 검증
    if (typeof fortune.scores !== 'object') {
      console.error('Scores must be an object');
      return false;
    }
    
    return true;
  }
}

export default TypeValidator;
```

#### 8.4.3 빌드 도구 및 최적화

**Vite 설정 최적화:**
```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  
  // 개발 서버 설정
  server: {
    port: 3000,
    open: true,
    hmr: {
      overlay: true
    }
  },
  
  // 빌드 최적화
  build: {
    target: 'es2015',
    outDir: 'dist',
    sourcemap: true,
    minify: 'terser',
    
    // 청크 분할 전략
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          live2d: ['@live2d/cubismwebframework'],
          animations: ['framer-motion', 'react-spring']
        }
      }
    },
    
    // 번들 크기 경고 임계값
    chunkSizeWarningLimit: 1000
  },
  
  // 경로 별칭 설정
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@components': resolve(__dirname, 'src/components'),
      '@services': resolve(__dirname, 'src/services'),
      '@utils': resolve(__dirname, 'src/utils'),
      '@types': resolve(__dirname, 'src/types')
    }
  },
  
  // 환경 변수 설정
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_DATE__: JSON.stringify(new Date().toISOString())
  }
});
```

#### 8.4.4 개발 워크플로우 자동화

**package.json 스크립트:**
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext .js,.jsx --report-unused-disable-directives --max-warnings 0",
    "lint:fix": "eslint src --ext .js,.jsx --fix",
    "format": "prettier --write src/**/*.{js,jsx,css,md}",
    "format:check": "prettier --check src/**/*.{js,jsx,css,md}",
    "type-check": "node scripts/validateTypes.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "validate": "npm run lint && npm run format:check && npm run type-check && npm run test",
    "pre-commit": "npm run validate && npm run build"
  }
}
```

**Git Hooks 설정:**
```javascript
// .husky/pre-commit
#!/usr/bin/env sh
. "$(dirname -- "$0")/_/husky.sh"

echo "🔍 Running pre-commit checks..."

# ESLint 검사
npm run lint
if [ $? -ne 0 ]; then
  echo "❌ ESLint errors found. Please fix them before committing."
  exit 1
fi

# Prettier 포맷 검사
npm run format:check
if [ $? -ne 0 ]; then
  echo "❌ Code formatting issues found. Run 'npm run format' to fix."
  exit 1
fi

# 타입 검증
npm run type-check
if [ $? -ne 0 ]; then
  echo "❌ Type validation failed. Please check JSDoc annotations."
  exit 1
fi

echo "✅ All pre-commit checks passed!"
```

#### 8.4.5 VS Code 개발 환경 설정

**추천 확장 프로그램:**
```json
// .vscode/extensions.json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag",
    "christian-kohler.path-intellisense",
    "ms-vscode.vscode-json",
    "yzhang.markdown-all-in-one"
  ]
}
```

**VS Code 워크스페이스 설정:**
```json
// .vscode/settings.json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "eslint.validate": ["javascript", "javascriptreact"],
  "emmet.includeLanguages": {
    "javascript": "javascriptreact"
  },
  "javascript.suggest.autoImports": true,
  "javascript.updateImportsOnFileMove.enabled": "always",
  "typescript.preferences.includePackageJsonAutoImports": "auto"
}
```

## 9. 품질 보증 계획

### 9.1 테스트 전략

#### 9.1.1 테스트 레벨별 전략
```python
TEST_STRATEGY = {
    "unit_tests": {
        "coverage_target": "80%",
        "frameworks": ["pytest", "jest"],
        "focus_areas": [
            "운세 생성 로직",
            "콘텐츠 필터링",
            "데이터 검증",
            "유틸리티 함수"
        ]
    },
    "integration_tests": {
        "coverage_target": "70%", 
        "tools": ["playwright", "postman"],
        "focus_areas": [
            "WebSocket 통신",
            "AI API 통합",
            "Live2D 제어",
            "데이터베이스 연동"
        ]
    },
    "e2e_tests": {
        "coverage_target": "주요 시나리오 100%",
        "tools": ["playwright", "cypress"],
        "scenarios": [
            "첫 방문자 온보딩",
            "일일 운세 조회",
            "타로 카드 읽기",
            "부적절한 내용 차단",
            "모바일 사용성"
        ]
    },
    "performance_tests": {
        "tools": ["k6", "lighthouse"],
        "metrics": [
            "Live2D 렌더링 FPS",
            "WebSocket 응답 시간",
            "페이지 로드 시간",
            "메모리 사용량"
        ]
    }
}
```

#### 9.1.2 자동화 테스트 구현
```typescript
// E2E 테스트 예시 (Playwright)
import { test, expect } from '@playwright/test';

test.describe('Fortune App E2E Tests', () => {
  test('First-time user journey', async ({ page }) => {
    // 1. 홈페이지 접속
    await page.goto('/');
    
    // 2. Live2D 캐릭터 로딩 확인
    await expect(page.locator('.live2d-canvas')).toBeVisible();
    await expect(page.locator('.character-area')).toContainText('미라');
    
    // 3. 첫 인사 메시지 확인
    await expect(page.locator('.chat-messages')).toContainText('안녕하세요');
    
    // 4. 사용자 이름 입력
    await page.fill('.chat-input input', '테스트유저');
    await page.click('.send-button');
    
    // 5. 캐릭터 반응 확인
    await expect(page.locator('.chat-messages')).toContainText('테스트유저님');
    
    // 6. 운세 타입 선택
    await page.click('[data-testid="daily-fortune-button"]');
    
    // 7. 운세 결과 표시 확인
    await expect(page.locator('.fortune-result')).toBeVisible();
    await expect(page.locator('.overall-score')).toBeVisible();
    
    // 8. Live2D 감정 변화 확인
    const canvas = page.locator('.live2d-canvas');
    await expect(canvas).toHaveAttribute('data-emotion', /joy|mystical/);
  });
  
  test('Content filtering system', async ({ page }) => {
    await page.goto('/');
    
    // 부적절한 내용 입력
    await page.fill('.chat-input input', '성적인 내용 테스트');
    await page.click('.send-button');
    
    // 경고 메시지 확인
    await expect(page.locator('.chat-messages')).toContainText('운세 상담만 도와드릴 수 있어요');
    
    // 캐릭터 표정 변화 확인
    await expect(page.locator('.live2d-canvas')).toHaveAttribute('data-emotion', 'concern');
  });
  
  test('Mobile responsiveness', async ({ page }) => {
    // 모바일 뷰포트 설정
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // 모바일 레이아웃 확인
    await expect(page.locator('.fortune-app')).toHaveClass(/mobile-layout/);
    
    // 터치 인터랙션 테스트
    await page.tap('.live2d-canvas');
    await expect(page.locator('.character-area')).toHaveClass(/interacted/);
    
    // 가상 키보드 대응 확인
    await page.fill('.chat-input input', 'test');
    await expect(page.locator('.chat-interface')).toHaveClass(/keyboard-visible/);
  });
});
```

### 9.2 성능 최적화 방안

#### 9.2.1 프론트엔드 성능 최적화
```typescript
// 코드 스플리팅 및 지연 로딩
const TarotComponent = lazy(() => import('./components/Tarot/TarotReader'));
const FortuneHistory = lazy(() => import('./components/History/FortuneHistory'));

// Live2D 텍스처 최적화
class TextureOptimizer {
  static async optimizeTextures(modelPath: string) {
    const textures = await this.loadTextures(modelPath);
    
    return textures.map(texture => {
      // 디바이스 성능에 따른 텍스처 크기 조정
      const deviceScore = this.assessDevicePerformance();
      const targetSize = deviceScore > 0.7 ? 2048 : 1024;
      
      return this.resizeTexture(texture, targetSize);
    });
  }
  
  private static assessDevicePerformance(): number {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl');
    
    if (!gl) return 0;
    
    const renderer = gl.getParameter(gl.RENDERER);
    const vendor = gl.getParameter(gl.VENDOR);
    
    // GPU 성능 점수 계산 로직
    return this.calculateGPUScore(renderer, vendor);
  }
}

// 메모리 사용량 모니터링
class MemoryMonitor {
  private memoryThreshold = 100 * 1024 * 1024; // 100MB
  
  startMonitoring() {
    setInterval(() => {
      if ('memory' in performance) {
        const memInfo = (performance as any).memory;
        
        if (memInfo.usedJSHeapSize > this.memoryThreshold) {
          this.triggerGarbageCollection();
        }
      }
    }, 5000);
  }
  
  private triggerGarbageCollection() {
    // 불필요한 리소스 정리
    this.cleanupUnusedTextures();
    this.clearOldChatHistory();
    this.disposeInactiveAnimations();
  }
}
```

#### 9.2.2 백엔드 성능 최적화
```python
# Redis 캐싱 전략
class FortuneCache:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.cache_ttl = {
            "daily_fortune": 86400,      # 24시간
            "user_profile": 3600,        # 1시간
            "tarot_interpretation": 1800  # 30분
        }
    
    async def get_or_generate_daily_fortune(self, user_id: str, date: str) -> dict:
        cache_key = f"daily_fortune:{user_id}:{date}"
        
        # 캐시에서 조회
        cached_result = await self.redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
        
        # 새로 생성
        fortune = await self.generate_daily_fortune(user_id, date)
        
        # 캐시에 저장
        await self.redis_client.setex(
            cache_key, 
            self.cache_ttl["daily_fortune"],
            json.dumps(fortune)
        )
        
        return fortune

# 데이터베이스 쿼리 최적화
class OptimizedFortuneRepository:
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_user_fortune_history(self, user_id: str, limit: int = 10) -> List[FortuneRecord]:
        """인덱스 최적화된 운세 히스토리 조회"""
        query = (
            select(FortuneRecord)
            .where(FortuneRecord.user_id == user_id)
            .order_by(FortuneRecord.created_at.desc())
            .limit(limit)
            .options(selectinload(FortuneRecord.categories))  # N+1 쿼리 방지
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

# WebSocket 연결 최적화
class OptimizedWebSocketManager:
    def __init__(self):
        self.connection_pool = {}
        self.heartbeat_interval = 30  # 30초
        self.max_connections_per_ip = 5
    
    async def manage_connection(self, websocket: WebSocket, client_ip: str):
        # IP별 연결 수 제한
        if self.count_connections_by_ip(client_ip) >= self.max_connections_per_ip:
            await websocket.close(code=1008, reason="Too many connections")
            return
        
        # 연결 풀에 추가
        client_id = str(uuid4())
        self.connection_pool[client_id] = {
            "websocket": websocket,
            "ip": client_ip,
            "last_heartbeat": time.time()
        }
        
        try:
            await self.handle_connection(client_id)
        finally:
            # 정리
            self.connection_pool.pop(client_id, None)
```

### 9.3 보안 검증 계획

#### 9.3.1 콘텐츠 보안 검증
```python
# 다층 콘텐츠 필터링 시스템
class AdvancedContentFilter:
    def __init__(self):
        self.keyword_filter = KeywordFilter()
        self.ml_classifier = MLContentClassifier()
        self.context_analyzer = ContextAnalyzer()
        
    async def analyze_content(self, message: str, context: dict) -> ContentAnalysisResult:
        """다층 분석을 통한 콘텐츠 검증"""
        
        # 1단계: 키워드 기반 필터링
        keyword_result = self.keyword_filter.check(message)
        if keyword_result.is_blocked:
            return ContentAnalysisResult(
                is_safe=False,
                reason="inappropriate_keywords",
                confidence=keyword_result.confidence
            )
        
        # 2단계: ML 기반 분류
        ml_result = await self.ml_classifier.classify(message)
        if ml_result.inappropriate_probability > 0.7:
            return ContentAnalysisResult(
                is_safe=False,
                reason="ml_classification",
                confidence=ml_result.confidence
            )
        
        # 3단계: 문맥 분석
        context_result = await self.context_analyzer.analyze(message, context)
        if context_result.context_violation:
            return ContentAnalysisResult(
                is_safe=False,
                reason="context_violation",
                confidence=context_result.confidence
            )
        
        return ContentAnalysisResult(is_safe=True)

# 실시간 모니터링 시스템
class SecurityMonitoring:
    def __init__(self):
        self.alert_thresholds = {
            "inappropriate_attempts_per_hour": 5,
            "rapid_fire_messages": 10,
            "suspicious_pattern_score": 0.8
        }
        
    async def monitor_user_behavior(self, user_id: str, action: str, metadata: dict):
        """사용자 행동 패턴 모니터링"""
        
        # 시간당 부적절한 시도 횟수 추적
        inappropriate_count = await self.count_recent_violations(user_id, hours=1)
        if inappropriate_count >= self.alert_thresholds["inappropriate_attempts_per_hour"]:
            await self.trigger_security_alert("excessive_violations", user_id)
        
        # 빠른 연속 메시지 감지
        recent_messages = await self.get_recent_messages(user_id, minutes=1)
        if len(recent_messages) >= self.alert_thresholds["rapid_fire_messages"]:
            await self.apply_rate_limiting(user_id)
        
        # 의심스러운 패턴 점수 계산
        pattern_score = await self.calculate_suspicion_score(user_id, metadata)
        if pattern_score >= self.alert_thresholds["suspicious_pattern_score"]:
            await self.flag_for_manual_review(user_id)
```

#### 9.3.2 데이터 보호 및 개인정보 보안
```python
# 개인정보 보호 시스템
class PrivacyProtection:
    def __init__(self):
        self.encryption_key = self.load_encryption_key()
        self.data_retention_periods = {
            "chat_history": 30,      # 30일
            "user_profile": 365,     # 1년
            "fortune_history": 90    # 90일
        }
    
    def encrypt_sensitive_data(self, data: dict) -> dict:
        """민감한 데이터 암호화"""
        sensitive_fields = ["birth_date", "full_name", "contact_info"]
        
        for field in sensitive_fields:
            if field in data:
                data[field] = self.encrypt_field(data[field])
        
        return data
    
    async def cleanup_expired_data(self):
        """데이터 보존 기간에 따른 자동 삭제"""
        cutoff_dates = {
            table: datetime.now() - timedelta(days=period)
            for table, period in self.data_retention_periods.items()
        }
        
        for table, cutoff_date in cutoff_dates.items():
            await self.delete_expired_records(table, cutoff_date)
    
    def anonymize_user_data(self, user_data: dict) -> dict:
        """사용자 데이터 익명화"""
        anonymized = user_data.copy()
        
        # 식별 가능한 정보 제거
        anonymized.pop("name", None)
        anonymized.pop("birth_date", None)
        
        # 일반화된 정보로 대체
        if "age" in anonymized:
            anonymized["age_group"] = self.categorize_age(anonymized["age"])
            del anonymized["age"]
        
        return anonymized

# 보안 감사 로깅
class SecurityAuditLogger:
    def __init__(self):
        self.logger = self.setup_secure_logger()
    
    async def log_security_event(self, event_type: str, user_id: str, details: dict):
        """보안 이벤트 로깅"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": self.hash_user_id(user_id),  # 해시화된 ID
            "details": self.sanitize_details(details),
            "severity": self.calculate_severity(event_type)
        }
        
        self.logger.info(json.dumps(log_entry))
        
        # 높은 심각도 이벤트는 즉시 알림
        if log_entry["severity"] >= 8:
            await self.send_immediate_alert(log_entry)
```

## 10. JavaScript 특화 기술적 고려사항

### 10.1 JavaScript 성능 최적화 전략

#### 10.1.1 메모리 관리 및 가비지 컬렉션 최적화

**메모리 누수 방지:**
```javascript
/**
 * Live2D 모델 메모리 관리 클래스
 */
class Live2DMemoryManager {
  constructor() {
    /** @type {WeakMap<Object, Function>} */
    this.cleanupFunctions = new WeakMap();
    /** @type {Set<AbortController>} */
    this.abortControllers = new Set();
  }

  /**
   * 컴포넌트별 메모리 정리 등록
   * @param {Object} component - React 컴포넌트 인스턴스
   * @param {Function} cleanup - 정리 함수
   */
  registerCleanup(component, cleanup) {
    this.cleanupFunctions.set(component, cleanup);
  }

  /**
   * WebGL 리소스 정리
   * @param {WebGLRenderingContext} gl - WebGL 컨텍스트
   * @param {Object[]} resources - 정리할 리소스 배열
   */
  cleanupWebGLResources(gl, resources) {
    resources.forEach(resource => {
      if (resource.type === 'texture') {
        gl.deleteTexture(resource.handle);
      } else if (resource.type === 'buffer') {
        gl.deleteBuffer(resource.handle);
      } else if (resource.type === 'program') {
        gl.deleteProgram(resource.handle);
      }
    });
  }

  /**
   * 이벤트 리스너 자동 정리
   * @param {HTMLElement} element - DOM 요소
   * @param {string} event - 이벤트 타입
   * @param {Function} handler - 이벤트 핸들러
   * @returns {Function} 정리 함수
   */
  addManagedEventListener(element, event, handler) {
    const abortController = new AbortController();
    this.abortControllers.add(abortController);
    
    element.addEventListener(event, handler, { 
      signal: abortController.signal 
    });
    
    return () => {
      abortController.abort();
      this.abortControllers.delete(abortController);
    };
  }
}
```

#### 10.1.2 번들 최적화 및 코드 스플리팅

**동적 임포트를 활용한 코드 스플리팅:**
```javascript
/**
 * 운세 컴포넌트 동적 로딩
 */
const FortuneComponents = {
  /**
   * 일일 운세 컴포넌트 로드
   * @returns {Promise<React.ComponentType>}
   */
  async loadDailyFortune() {
    const module = await import(
      /* webpackChunkName: "daily-fortune" */ 
      './components/Fortune/DailyFortune'
    );
    return module.default;
  },

  /**
   * 타로 카드 컴포넌트 로드
   * @returns {Promise<React.ComponentType>}
   */
  async loadTarotCard() {
    const module = await import(
      /* webpackChunkName: "tarot-card" */
      './components/Fortune/TarotCard'
    );
    return module.default;
  },

  /**
   * Live2D 모델 동적 로드
   * @param {string} modelName - 모델 이름
   * @returns {Promise<Object>}
   */
  async loadLive2DModel(modelName) {
    const modelData = await import(
      /* webpackChunkName: "live2d-models" */
      `../assets/models/${modelName}/model3.json`
    );
    return modelData.default;
  }
};

/**
 * 지연 로딩 훅
 * @param {Function} importFunc - 동적 임포트 함수
 * @returns {Object} 로딩 상태와 컴포넌트
 */
const useLazyComponent = (importFunc) => {
  /** @type {[React.ComponentType|null, Function]} */
  const [component, setComponent] = useState(null);
  /** @type {[boolean, Function]} */
  const [loading, setLoading] = useState(false);
  /** @type {[Error|null, Function]} */
  const [error, setError] = useState(null);

  const loadComponent = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const loadedComponent = await importFunc();
      setComponent(() => loadedComponent);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [importFunc]);

  return { component, loading, error, loadComponent };
};
```

#### 10.1.3 Worker를 활용한 백그라운드 처리

**Web Worker를 활용한 운세 계산:**
```javascript
// workers/fortuneCalculator.js
/**
 * 운세 계산 Web Worker
 */
class FortuneWorker {
  constructor() {
    this.algorithms = {
      daily: this.calculateDailyFortune,
      tarot: this.calculateTarotReading,
      numerology: this.calculateNumerology
    };
  }

  /**
   * 메시지 핸들러
   * @param {MessageEvent} event - 워커 메시지 이벤트
   */
  handleMessage(event) {
    const { type, data, requestId } = event.data;
    
    try {
      const result = this.algorithms[type]?.(data);
      self.postMessage({
        requestId,
        result,
        success: true
      });
    } catch (error) {
      self.postMessage({
        requestId,
        error: error.message,
        success: false
      });
    }
  }

  /**
   * 일일 운세 계산
   * @param {Object} userData - 사용자 데이터
   * @returns {Object} 운세 결과
   */
  calculateDailyFortune(userData) {
    // 복잡한 운세 계산 로직
    const baseScore = this.calculateBaseScore(userData);
    const seasonalFactor = this.getSeasonalFactor();
    const personalCycle = this.calculatePersonalCycle(userData.birthDate);
    
    return {
      overall: baseScore * seasonalFactor * personalCycle,
      love: this.calculateLoveScore(userData),
      money: this.calculateMoneyScore(userData),
      health: this.calculateHealthScore(userData),
      work: this.calculateWorkScore(userData)
    };
  }
}

// 워커 초기화
const fortuneWorker = new FortuneWorker();
self.addEventListener('message', fortuneWorker.handleMessage.bind(fortuneWorker));
```

**메인 스레드에서 워커 활용:**
```javascript
/**
 * 운세 계산 서비스 (Worker 활용)
 */
class FortuneCalculationService {
  constructor() {
    /** @type {Worker} */
    this.worker = new Worker('/workers/fortuneCalculator.js');
    /** @type {Map<string, Object>} */
    this.pendingRequests = new Map();
    
    this.worker.addEventListener('message', this.handleWorkerMessage.bind(this));
  }

  /**
   * 워커 메시지 핸들러
   * @param {MessageEvent} event - 워커 응답 이벤트
   */
  handleWorkerMessage(event) {
    const { requestId, result, error, success } = event.data;
    const request = this.pendingRequests.get(requestId);
    
    if (request) {
      if (success) {
        request.resolve(result);
      } else {
        request.reject(new Error(error));
      }
      this.pendingRequests.delete(requestId);
    }
  }

  /**
   * 운세 계산 요청
   * @param {string} type - 운세 타입
   * @param {Object} data - 계산 데이터
   * @returns {Promise<Object>} 운세 결과
   */
  calculateFortune(type, data) {
    return new Promise((resolve, reject) => {
      const requestId = `req_${Date.now()}_${Math.random()}`;
      
      this.pendingRequests.set(requestId, { resolve, reject });
      
      this.worker.postMessage({
        type,
        data,
        requestId
      });
      
      // 타임아웃 설정 (10초)
      setTimeout(() => {
        if (this.pendingRequests.has(requestId)) {
          this.pendingRequests.delete(requestId);
          reject(new Error('Fortune calculation timeout'));
        }
      }, 10000);
    });
  }
}
```

### 10.2 SQLite 성능 최적화

#### 10.2.1 SQLite 최적화 설정

**SQLite 성능 튜닝:**
```javascript
/**
 * SQLite 데이터베이스 최적화 관리자
 */
class SQLiteOptimizer {
  constructor() {
    this.optimizations = {
      // WAL 모드로 동시성 향상
      journal_mode: 'WAL',
      // 동기화 레벨 조정
      synchronous: 'NORMAL',
      // 캐시 크기 증가 (10MB)
      cache_size: 10000,
      // 메모리에 임시 저장
      temp_store: 'MEMORY',
      // 메모리 매핑 크기 (256MB)
      mmap_size: 268435456,
      // 페이지 크기 최적화
      page_size: 4096
    };
  }

  /**
   * 데이터베이스 최적화 적용
   * @param {Database} db - SQLite 데이터베이스 인스턴스
   * @returns {Promise<void>}
   */
  async applyOptimizations(db) {
    for (const [pragma, value] of Object.entries(this.optimizations)) {
      await db.exec(`PRAGMA ${pragma} = ${value};`);
    }
    
    // 자주 사용되는 쿼리에 대한 인덱스 생성
    await this.createOptimizedIndexes(db);
    
    // 통계 정보 업데이트
    await db.exec('ANALYZE;');
  }

  /**
   * 최적화된 인덱스 생성
   * @param {Database} db - SQLite 데이터베이스 인스턴스
   * @returns {Promise<void>}
   */
  async createOptimizedIndexes(db) {
    const indexes = [
      // 복합 인덱스로 쿼리 성능 향상
      'CREATE INDEX IF NOT EXISTS idx_fortune_user_date ON fortune_records(user_id, fortune_date DESC);',
      'CREATE INDEX IF NOT EXISTS idx_chat_session_time ON chat_messages(session_id, timestamp DESC);',
      'CREATE INDEX IF NOT EXISTS idx_user_active ON users(last_active DESC) WHERE last_active > datetime("now", "-7 days");',
      // 부분 인덱스로 저장 공간 절약
      'CREATE INDEX IF NOT EXISTS idx_filtered_messages ON chat_messages(is_filtered) WHERE is_filtered = 1;'
    ];
    
    for (const indexSQL of indexes) {
      await db.exec(indexSQL);
    }
  }

  /**
   * 데이터베이스 정리 및 최적화
   * @param {Database} db - SQLite 데이터베이스 인스턴스
   * @returns {Promise<void>}
   */
  async maintainDatabase(db) {
    // 데이터베이스 크기 압축
    await db.exec('VACUUM;');
    
    // 인덱스 재구성
    await db.exec('REINDEX;');
    
    // 통계 정보 갱신
    await db.exec('ANALYZE;');
    
    // WAL 파일 체크포인트
    await db.exec('PRAGMA wal_checkpoint(TRUNCATE);');
  }
}
```

### 10.3 브라우저 호환성 및 폴리필

#### 10.3.1 브라우저 지원 전략

**기능 감지 및 폴리필:**
```javascript
/**
 * 브라우저 호환성 관리자
 */
class BrowserCompatibilityManager {
  constructor() {
    this.requiredFeatures = {
      webgl2: () => this.checkWebGL2Support(),
      websocket: () => 'WebSocket' in window,
      webworker: () => 'Worker' in window,
      indexeddb: () => 'indexedDB' in window,
      webassembly: () => 'WebAssembly' in window
    };
  }

  /**
   * WebGL 2.0 지원 확인
   * @returns {boolean} 지원 여부
   */
  checkWebGL2Support() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2');
      return !!gl;
    } catch (e) {
      return false;
    }
  }

  /**
   * 브라우저 호환성 검사
   * @returns {Object} 지원 상태 및 권장사항
   */
  checkCompatibility() {
    const support = {};
    const missing = [];
    
    for (const [feature, checker] of Object.entries(this.requiredFeatures)) {
      support[feature] = checker();
      if (!support[feature]) {
        missing.push(feature);
      }
    }
    
    return {
      isSupported: missing.length === 0,
      support,
      missing,
      recommendations: this.getRecommendations(missing)
    };
  }

  /**
   * 지원되지 않는 기능에 대한 권장사항
   * @param {string[]} missing - 지원되지 않는 기능 목록
   * @returns {string[]} 권장사항 목록
   */
  getRecommendations(missing) {
    const recommendations = [];
    
    if (missing.includes('webgl2')) {
      recommendations.push('WebGL 2.0을 지원하는 최신 브라우저로 업데이트하세요.');
    }
    
    if (missing.includes('websocket')) {
      recommendations.push('WebSocket을 지원하는 브라우저를 사용하세요.');
    }
    
    return recommendations;
  }

  /**
   * 필요한 폴리필 로드
   * @returns {Promise<void>}
   */
  async loadPolyfills() {
    const polyfills = [];
    
    // Intersection Observer 폴리필
    if (!('IntersectionObserver' in window)) {
      polyfills.push(import('intersection-observer'));
    }
    
    // ResizeObserver 폴리필
    if (!('ResizeObserver' in window)) {
      polyfills.push(import('resize-observer-polyfill'));
    }
    
    // Web Animations API 폴리필
    if (!('animate' in HTMLElement.prototype)) {
      polyfills.push(import('web-animations-js'));
    }
    
    await Promise.all(polyfills);
  }
}
```

### 10.4 런타임 에러 처리 및 디버깅

#### 10.4.1 전역 에러 처리 시스템

**포괄적 에러 핸들링:**
```javascript
/**
 * 전역 에러 관리자
 */
class GlobalErrorManager {
  constructor() {
    this.errorReporters = [];
    this.errorQueue = [];
    this.maxQueueSize = 50;
    
    this.setupGlobalHandlers();
  }

  /**
   * 전역 에러 핸들러 설정
   */
  setupGlobalHandlers() {
    // JavaScript 런타임 에러
    window.addEventListener('error', this.handleGlobalError.bind(this));
    
    // Promise rejection 에러
    window.addEventListener('unhandledrejection', this.handlePromiseRejection.bind(this));
    
    // React Error Boundary와 연동
    this.setupReactErrorBoundary();
  }

  /**
   * JavaScript 에러 핸들링
   * @param {ErrorEvent} event - 에러 이벤트
   */
  handleGlobalError(event) {
    const errorInfo = {
      type: 'javascript_error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error?.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };
    
    this.reportError(errorInfo);
  }

  /**
   * Promise rejection 핸들링
   * @param {PromiseRejectionEvent} event - Promise rejection 이벤트
   */
  handlePromiseRejection(event) {
    const errorInfo = {
      type: 'promise_rejection',
      message: event.reason?.message || 'Unhandled Promise Rejection',
      stack: event.reason?.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };
    
    this.reportError(errorInfo);
  }

  /**
   * React Error Boundary 설정
   */
  setupReactErrorBoundary() {
    // React Error Boundary에서 사용할 에러 리포터 등록
    window.reportReactError = (errorInfo, errorBoundaryStack) => {
      this.reportError({
        type: 'react_error',
        ...errorInfo,
        errorBoundaryStack,
        timestamp: new Date().toISOString()
      });
    };
  }

  /**
   * 에러 리포팅
   * @param {Object} errorInfo - 에러 정보
   */
  reportError(errorInfo) {
    // 큐에 에러 추가
    this.errorQueue.push(errorInfo);
    
    // 큐 크기 제한
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift();
    }
    
    // 에러 리포터들에게 전달
    this.errorReporters.forEach(reporter => {
      try {
        reporter(errorInfo);
      } catch (e) {
        console.error('Error in error reporter:', e);
      }
    });
  }

  /**
   * 에러 리포터 등록
   * @param {Function} reporter - 에러 리포터 함수
   */
  addErrorReporter(reporter) {
    this.errorReporters.push(reporter);
  }
}
```

이 기획서는 Open-LLM-VTuber 프로젝트의 기술적 기반을 철저히 분석하여 Live2D 운세 챗 웹 어플리케이션의 모든 측면을 상세히 다뤘습니다. 

**주요 특징:**
1. **기술적 실현 가능성**: 기존 프로젝트의 검증된 아키텍처 기반
2. **사용자 중심 설계**: 상세한 스토리보드와 사용자 여정 매핑
3. **안전성 확보**: 다층 콘텐츠 필터링 및 보안 시스템
4. **확장 가능성**: 단계적 개발 로드맵과 미래 확장 계획
5. **성능 최적화**: Live2D 렌더링 최적화 및 반응형 설계

**JavaScript 기반 아키텍처 업데이트:**
6. **Modern JavaScript**: ES6+ 기능 활용과 JSDoc 기반 타입 안전성
7. **개발 도구 체인**: ESLint, Prettier를 통한 코드 품질 관리
8. **데이터베이스 전략**: SQLite 기반 MVP, MariaDB 마이그레이션 계획
9. **성능 최적화**: Web Worker, 메모리 관리, 번들 최적화
10. **브라우저 호환성**: 폴리필과 점진적 향상을 통한 광범위한 지원

이 기획서를 바탕으로 재미있고 안전한 Live2D 운세 앱을 성공적으로 개발할 수 있을 것입니다.

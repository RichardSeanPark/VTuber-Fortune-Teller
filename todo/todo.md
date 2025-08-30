# 🔮 Live2D 운세 앱 백엔드 개발 TODO

> **백엔드 전문가 관점의 종합 개발 로드맵**  
> React JavaScript + FastAPI Python 기반 운세 앱 백엔드 시스템

---

## 📋 **Phase 1: 백엔드 아키텍처 설계 & 환경 구축**

### 🏗️ **1.1 아키텍처 설계**
- [ ] **API 설계 문서 작성**
  - RESTful API 엔드포인트 정의 (/api/fortune, /api/user, /api/chat)
  - WebSocket 이벤트 프로토콜 설계 (실시간 채팅, Live2D 동기화)
  - 요청/응답 스키마 정의 (JSON Schema 활용)
  - API 버전 관리 전략 수립

- [ ] **데이터베이스 스키마 설계**
  - SQLite 테이블 구조 설계 (users, fortune_sessions, chat_history, content_cache)
  - 인덱스 최적화 전략 (복합 인덱스, 쿼리 성능 고려)
  - 관계형 데이터 모델링 (정규화 vs 비정규화 균형)
  - MariaDB 마이그레이션 대비 호환성 확보

- [ ] **보안 아키텍처 설계**
  - 콘텐츠 필터링 시스템 설계 (다층 필터링)
  - 세션 관리 전략 (JWT vs Session Store 비교 검토)
  - 입력 검증 및 SQL 인젝션 방지
  - Rate Limiting 및 DDoS 방어 전략

### 🛠️ **1.2 개발 환경 구축**
- [ ] **Python 백엔드 프로젝트 초기화**
  - Python 가상환경 설정 (venv 활용)
  - FastAPI + Uvicorn 설정
  - Pytest 테스트 환경 구축
  - Docker 컨테이너화 준비

- [ ] **핵심 의존성 설치 및 설정**
  - FastAPI (웹 프레임워크)
  - WebSocket (실시간 통신)
  - SQLite3 + SQLAlchemy (데이터베이스 ORM)
  - Pydantic (데이터 검증)
  - Python-jose + Passlib (보안)

- [ ] **프론트엔드 개발 도구 설정**
  - React + JavaScript ES6+ (TypeScript 금지)
  - Vite (번들러 및 개발 서버)
  - ESLint + Prettier (JavaScript 코드 품질)
  - Live2D Cubism SDK for Web

---

## 📊 **Phase 2: 데이터베이스 구현 & 최적화**

### 🗄️ **2.1 SQLite 데이터베이스 구현**
- [ ] **핵심 테이블 생성**
  ```sql
  -- users: 사용자 기본 정보
  -- fortune_sessions: 운세 상담 세션
  -- chat_messages: 채팅 메시지 기록
  -- fortune_cache: 운세 결과 캐싱
  -- content_filters: 콘텐츠 필터링 룰
  ```

- [ ] **데이터 접근 계층 구현**
  - Repository 패턴 적용 (SQLAlchemy 활용)
  - Connection Pool 최적화 (SQLite WAL 모드 활용)
  - 트랜잭션 관리 (SQLAlchemy Session 관리)
  - 쿼리 최적화 (EXPLAIN QUERY PLAN 활용)

- [ ] **데이터베이스 마이그레이션 시스템**
  - Alembic 마이그레이션 스크립트 작성
  - 스키마 버전 관리 (backward compatibility)
  - 백업 및 복구 전략 수립
  - MariaDB 마이그레이션 대비 호환성 테스트

### ⚡ **2.2 SQLite 성능 최적화**
- [ ] **쿼리 성능 최적화**
  - 복합 인덱스 설계 (WHERE, ORDER BY 절 최적화)
  - 쿼리 실행 계획 분석 및 튜닝
  - N+1 문제 해결 (JOIN vs 배치 쿼리)
  - 페이징 최적화 (LIMIT/OFFSET vs Cursor-based)

- [ ] **캐싱 전략 구현**
  - Redis-like 인메모리 캐시 (Python Dict 활용)
  - 운세 결과 캐싱 (TTL 기반, 24시간 주기)
  - 쿼리 결과 캐싱 (자주 조회되는 데이터)
  - 캐시 무효화 전략 (데이터 변경시 자동 갱신)

- [ ] **SQLite 한계점 대응**
  - 동시 접속자 수 모니터링 (SQLite 제한 확인)
  - Read/Write 분리 전략 (WAL 모드 최적화)
  - 대용량 데이터 처리 방안 (배치 처리, 파티셔닝)
  - MariaDB 마이그레이션 Threshold 정의

---

## 🔧 **Phase 3: 핵심 API 구현**

### 🎯 **3.1 운세 API 개발**
- [ ] **운세 엔진 구현**
  - 일일 운세 생성 알고리즘 (랜덤 + 개인화 요소)
  - 타로 카드 시스템 (78장 카드 데이터베이스)
  - 별자리 운세 시스템 (12성좌별 특화)
  - 사주 간이 계산 로직 (생년월일시 기반)

- [ ] **개인화 시스템**
  - 사용자 프로필 기반 맞춤화
  - 과거 운세 기록 분석 (패턴 학습)
  - 선호도 기반 운세 스타일 조정
  - A/B 테스트 프레임워크 구축

- [ ] **운세 API 엔드포인트**
  ```python
  # FastAPI 라우터 구조
  # GET /api/fortune/daily/{user_id} - 일일 운세 조회
  # POST /api/fortune/tarot - 타로 카드 뽑기
  # GET /api/fortune/zodiac/{sign} - 별자리 운세
  # POST /api/fortune/saju - 사주 기반 운세
  ```

### 💬 **3.2 채팅 시스템 구현**
- [ ] **WebSocket 실시간 통신**
  - FastAPI WebSocket 기반 실시간 채팅
  - 메시지 큐 시스템 (순차 처리 보장)
  - 연결 상태 관리 (재연결, 타임아웃 처리)
  - 브로드캐스트 vs 유니캐스트 구분

- [ ] **메시지 처리 파이프라인**
  - 입력 검증 (XSS, 인젝션 방지)
  - 콘텐츠 필터링 (다층 필터링 적용)
  - 메시지 라우팅 (운세 요청 vs 일반 대화)
  - 응답 생성 (컨텍스트 기반 답변)

- [ ] **채팅 히스토리 관리**
  - 세션별 대화 기록 저장
  - 대화 컨텍스트 유지 (최근 N개 메시지)
  - 히스토리 압축 및 정리 (주기적 cleanup)
  - 개인정보 자동 마스킹

### 👤 **3.3 사용자 관리 API**
- [ ] **사용자 세션 관리**
  - 익명 사용자 지원 (UUID 기반)
  - 세션 타임아웃 관리 (30분 무활동시 정리)
  - 세션 데이터 암호화 (민감 정보 보호)
  - 동시 세션 제한 (남용 방지)

- [ ] **사용자 프로필 API**
  - 기본 정보 저장 (생년월일, 별자리 등)
  - 선호도 설정 (운세 스타일, 알림 설정)
  - 운세 기록 관리 (과거 결과 조회)
  - 데이터 내보내기/삭제 (GDPR 대응)

---

## 🛡️ **Phase 4: 보안 시스템 구현**

### 🔒 **4.1 콘텐츠 필터링 시스템**
- [ ] **다층 필터링 아키텍처**
  - 키워드 기반 1차 필터링 (블랙리스트)
  - 패턴 매칭 2차 필터링 (정규식)
  - 컨텍스트 분석 3차 필터링 (NLP 라이브러리)
  - 학습 기반 필터 개선 (사용자 신고 반영)

- [ ] **필터링 룰 관리**
  - 동적 룰 업데이트 (재시작 없이 적용)
  - 룰 우선순위 관리 (화이트리스트 > 블랙리스트)
  - 언어별 필터링 (한국어, 영어 특화)
  - 필터링 로그 및 분석

- [ ] **유해 콘텐츠 대응**
  ```python
  # Python 정규식 기반 필터링
  # 성적 콘텐츠 필터링
  # 폭력적 표현 차단
  # 개인정보 수집 시도 탐지
  # 정치적/종교적 민감 내용 필터링
  ```

### 🔐 **4.2 입력 검증 및 보안**
- [ ] **입력 데이터 검증**
  - Pydantic 모델 기반 검증
  - SQL 인젝션 방지 (SQLAlchemy 파라미터화 쿼리)
  - XSS 공격 방지 (HTML 태그 이스케이핑)
  - CSRF 토큰 검증

- [ ] **API 보안 강화**
  - Rate Limiting (IP별, 사용자별)
  - API 키 인증 (내부 서비스용)
  - CORS 정책 설정 (화이트리스트 기반)
  - HTTPS 강제 적용

- [ ] **에러 처리 및 로깅**
  - 보안 이벤트 로깅 (침입 시도, 필터링 히트)
  - 에러 정보 최소화 (내부 정보 노출 방지)
  - 모니터링 알림 시스템
  - 로그 로테이션 및 보관

---

## 🔗 **Phase 5: Live2D 백엔드 연동**

### 🎭 **5.1 Live2D 상태 관리**
- [ ] **감정 상태 동기화**
  - 운세 결과에 따른 감정 매핑
  - 실시간 감정 상태 브로드캐스트
  - 감정 전환 애니메이션 제어
  - 감정 히스토리 추적

- [ ] **모션 이벤트 처리**
  - 운세 타입별 특화 모션 트리거
  - 사용자 상호작용 기반 모션 선택
  - 모션 큐 관리 (순차 실행, 우선순위)
  - 모션 충돌 해결 로직

- [ ] **Live2D 리소스 관리**
  - 모델 파일 최적화 (로딩 시간 단축)
  - 텍스처 캐싱 전략
  - 메모리 사용량 모니터링
  - 디바이스별 품질 조정

### 🎨 **5.2 캐릭터 커스터마이징**
- [ ] **표정/의상 시스템**
  - 표정 프리셋 관리 (8가지 기본 표정)
  - 의상 변경 시스템 (시즌별, 이벤트별)
  - 사용자 선호도 기반 자동 선택
  - 커스터마이징 데이터 저장

- [ ] **음성 합성 연동**
  - TTS 엔진 통합 (운세 결과 음성 출력)
  - 감정별 음성 톤 조절
  - 음성 캐싱 (동일 텍스트 재사용)
  - 다국어 음성 지원

---

## ⚡ **Phase 6: 성능 최적화 & 모니터링**

### 📈 **6.1 성능 최적화**
- [ ] **응답 시간 최적화**
  - API 응답 시간 목표: < 200ms
  - 데이터베이스 쿼리 최적화 (< 50ms)
  - 캐시 히트율 목표: > 80%
  - WebSocket 지연시간 < 100ms

- [ ] **메모리 및 CPU 최적화**
  - 메모리 누수 방지 (Python gc 모듈 활용)
  - CPU 사용률 모니터링 (< 70%)
  - 비동기 처리 최적화 (asyncio)
  - 멀티워커 모드 준비 (Uvicorn workers)

- [ ] **네트워크 최적화**
  - Gzip 압축 적용
  - HTTP/2 지원 준비
  - CDN 연동 고려 (정적 리소스)
  - Keep-Alive 연결 최적화

### 📊 **6.2 모니터링 시스템**
- [ ] **실시간 모니터링 구축**
  - Prometheus + Grafana 메트릭 수집
  - APM 도구 연동 (New Relic 또는 DataDog)
  - 헬스체크 엔드포인트 (/health, /ready)
  - 알림 시스템 구축 (Slack, Email)

- [ ] **비즈니스 메트릭 추적**
  - 일일 활성 사용자 (DAU)
  - 운세 요청 빈도 및 타입별 분석
  - 사용자 세션 시간 및 이탈률
  - 에러율 및 성공률 추적

- [ ] **로그 분석 시스템**
  - 구조화된 로깅 (JSON 형태)
  - 로그 검색 및 필터링 (ELK 스택 고려)
  - 성능 병목 지점 분석
  - 사용자 행동 패턴 분석

---

## 🎭 **Phase 7: Live2D 캐릭터 동작 시스템 구현**

### 🏗️ **7.1 Live2D 백엔드 인프라 구축**
- [ ] **Live2D 모델 관리 시스템**
  ```python
  # src/live2d/model_manager.py
  class Live2dModelManager:
      def __init__(self, models_path: str = "live2d-models"):
          self.models_path = models_path
          self.loaded_models = {}  # 모델 캐시
          self.emotion_mappings = {}  # 감정 매핑 테이블
      
      async def load_model_metadata(self, model_name: str) -> dict:
          """Live2D 모델 메타데이터 로드 (.model3.json 파일 파싱)"""
          
      async def get_model_info(self) -> list:
          """사용 가능한 Live2D 모델 목록 반환"""
          
      def extract_emotion_keywords(self, text: str) -> list:
          """텍스트에서 감정 키워드 추출"""
          emotions = ['joy', 'sadness', 'anger', 'surprise', 'fear', 'neutral']
          # Reference의 emotion 키워드 패턴 활용
  ```

- [ ] **감정 매핑 시스템 구현**
  ```python
  # src/live2d/emotion_mapper.py
  class EmotionMapper:
      EMOTION_KEYWORDS = {
          'joy': ['기쁘', '행복', '즐거', '좋아', '웃음'],
          'sadness': ['슬퍼', '우울', '아쉬움', '눈물'],
          'anger': ['화나', '짜증', '분노', '싫어'],
          'surprise': ['놀라', '깜짝', '어?', '오?'],
          'fear': ['무서', '걱정', '두려'],
          'neutral': ['그냥', '보통', '평소']
      }
      
      def map_emotions_to_expressions(self, emotions: list, model_name: str) -> dict:
          """감정을 Live2D 표정 인덱스로 매핑 (model_dict.json 기반)"""
  ```

- [ ] **WebSocket Live2D 통신 핸들러**
  ```python
  # src/websocket/live2d_handler.py  
  class Live2dWebSocketHandler:
      async def handle_expression_change(self, websocket, data: dict):
          """표정 변경 이벤트 처리 및 브로드캐스트"""
          
      async def handle_motion_trigger(self, websocket, data: dict):
          """모션 실행 요청 처리"""
          
      async def sync_character_state(self, client_uid: str, state_data: dict):
          """클라이언트별 캐릭터 상태 동기화"""
  ```

### 🎨 **7.2 프론트엔드 Live2D 통합 시스템**
- [ ] **React Live2D 컴포넌트 구축**
  ```javascript
  // components/Live2DCharacter.jsx
  // Live2D Cubism SDK 활용 모델 로딩 및 제어
  class Live2DCharacter extends React.Component {
      async loadModel(modelPath) {
          // Reference의 live2d.min.js 활용 패턴
          const model = await this.pixi.live2d.loadModel(modelPath);
          this.setupExpressions(model);
          this.setupMotions(model);
          return model;
      }
      
      changeExpression(expressionIndex, duration = 0.5) {
          // 표정 변경 애니메이션 (Reference 분석 결과 적용)
      }
      
      playMotion(motionGroup, motionIndex, priority = 1) {
          // 모션 재생 시스템
      }
  }
  ```

- [ ] **실시간 상태 동기화 Hook**
  ```javascript
  // hooks/useLive2DSync.js
  export const useLive2DSync = (characterRef) => {
      useEffect(() => {
          // WebSocket을 통한 실시간 Live2D 상태 동기화
          ws.on('expression_change', (data) => {
              characterRef.current?.changeExpression(data.expressionIndex);
          });
          
          ws.on('motion_trigger', (data) => {
              characterRef.current?.playMotion(data.group, data.index);
          });
      }, []);
  };
  ```

### 🤖 **7.3 캐릭터 상태 관리 시스템**
- [ ] **실시간 캐릭터 상태 관리**
  ```python
  # src/live2d/character_state.py
  @dataclass
  class CharacterState:
      model_name: str
      current_expression: int = 0  # neutral
      current_motion: str = 'idle'
      emotion_queue: list = field(default_factory=list)
      last_interaction: datetime = field(default_factory=datetime.now)
  
  class CharacterStateManager:
      def __init__(self):
          self.client_states = {}  # client_uid -> CharacterState
      
      async def update_expression(self, client_uid: str, emotion: str):
          """감정 기반 표정 업데이트"""
          
      async def trigger_motion(self, client_uid: str, motion_type: str):
          """특정 모션 트리거"""
  ```

- [ ] **감정 기반 모션 시스템**
  ```python
  # src/live2d/motion_controller.py
  class MotionController:
      EMOTION_MOTIONS = {
          'joy': ['happy_dance', 'clap', 'jump'],
          'sadness': ['cry', 'sigh', 'slump'],
          'surprise': ['gasp', 'jump_back', 'look_around'],
          'greeting': ['wave', 'bow', 'peace_sign']
      }
      
      async def select_motion_by_emotion(self, emotion: str, context: str) -> str:
          """감정과 컨텍스트에 따른 적절한 모션 선택"""
  ```

### 🔗 **7.4 Live2D API 엔드포인트 구현**
- [ ] **REST API 엔드포인트**
  ```python
  # routes/live2d_routes.py (Reference 분석의 routes.py 패턴 활용)
  @router.get("/live2d/models")
  async def get_available_models():
      """사용 가능한 Live2D 모델 목록 조회"""
      return await model_manager.get_live2d_models_info()
  
  @router.post("/live2d/expression")
  async def change_expression(request: ExpressionChangeRequest):
      """표정 변경 트리거 (감정 기반)"""
      
  @router.post("/live2d/motion")
  async def trigger_motion(request: MotionTriggerRequest):
      """특정 모션 실행"""
      
  @router.get("/live2d/state/{client_uid}")
  async def get_character_state(client_uid: str):
      """클라이언트별 캐릭터 상태 조회"""
  ```

- [ ] **WebSocket 이벤트 핸들링**
  ```python
  # WebSocket 라우터에 Live2D 이벤트 통합
  async def handle_live2d_event(websocket: WebSocket, event_data: dict):
      event_type = event_data.get('type')
      
      if event_type == 'expression_change':
          await live2d_handler.handle_expression_change(websocket, event_data)
      elif event_type == 'motion_trigger':
          await live2d_handler.handle_motion_trigger(websocket, event_data)
  ```

### 🎯 **7.5 감정 인식 & 자동 애니메이션**
- [ ] **텍스트 감정 분석 엔진**
  ```python
  # src/ai/emotion_analyzer.py (Reference의 live2d_model.py 패턴 활용)
  class TextEmotionAnalyzer:
      def __init__(self):
          # Reference에서 분석한 감정 키워드 패턴 활용
          self.emotion_patterns = self.load_emotion_patterns()
      
      def analyze_text_emotion(self, text: str) -> list:
          """텍스트에서 감정 추출 (Reference 패턴 기반)"""
          emotions_found = []
          for emotion, keywords in self.emotion_patterns.items():
              if any(keyword in text for keyword in keywords):
                  emotions_found.append(emotion)
          return emotions_found if emotions_found else ['neutral']
  ```

- [ ] **자동 애니메이션 트리거 시스템**
  ```python
  # src/live2d/auto_animation.py
  class AutoAnimationSystem:
      async def process_user_message(self, message: str, client_uid: str):
          """사용자 메시지 기반 자동 애니메이션 트리거"""
          # 1. 감정 분석
          emotions = self.emotion_analyzer.analyze_text_emotion(message)
          
          # 2. 적절한 표정/모션 선택
          animation_plan = self.create_animation_plan(emotions, message)
          
          # 3. WebSocket으로 애니메이션 실행
          await self.execute_animation_plan(client_uid, animation_plan)
  ```

### 🧪 **7.6 Live2D 시스템 테스트**
- [ ] **모델 로딩 테스트**
  - Live2D 모델 파일 무결성 검증
  - 모델 메타데이터 파싱 정확성 테스트
  - 표정/모션 파일 로딩 테스트
  - 크로스 브라우저 호환성 테스트

- [ ] **실시간 동기화 테스트**
  - WebSocket 표정 동기화 테스트
  - 다중 클라이언트 상태 관리 테스트
  - 애니메이션 큐 관리 테스트
  - 네트워크 지연 시 동기화 테스트

---

## 🗣️ **Phase 8: TTS Live2D 음성 통합 시스템**

### 🎙️ **8.1 다중 TTS 제공자 시스템 구축**
- [ ] **TTS 제공자 팩토리 시스템**
  ```python
  # src/tts/tts_provider_factory.py (Reference 기반)
  class TtsProviderFactory:
      SUPPORTED_PROVIDERS = {
          # 무료 제공자들 (우선순위)
          'edge_tts': {
              'name': 'Microsoft Edge TTS',
              'cost': 'free',
              'languages': ['ko', 'en', 'ja', 'zh'],
              'voices': ['ko-KR-SunHiNeural', 'en-US-AvaMultilingualNeural'],
              'quality': 'high'
          },
          'siliconflow_tts': {
              'name': 'SiliconFlow TTS',
              'cost': 'free_tier',
              'api_required': True,
              'languages': ['ko', 'en', 'zh'],
              'quality': 'high'
          },
          # 유료 제공자들 (백업)
          'azure_tts': {
              'name': 'Azure Cognitive Services',
              'cost': 'paid',
              'api_required': True,
              'languages': ['ko', 'en', 'ja', 'zh'],
              'quality': 'premium'
          },
          'openai_tts': {
              'name': 'OpenAI TTS',
              'cost': 'paid',
              'api_required': True,
              'quality': 'premium'
          }
      }
      
      @staticmethod
      def create_tts_engine(provider_type: str, **kwargs):
          """Reference의 TTSFactory 패턴 활용"""
          if provider_type == "edge_tts":
              from .edge_tts import TTSEngine as EdgeTTSEngine
              return EdgeTTSEngine(voice=kwargs.get("voice", "ko-KR-SunHiNeural"))
          
          elif provider_type == "siliconflow_tts":
              from .siliconflow_tts import SiliconFlowTTS
              return SiliconFlowTTS(
                  api_url=kwargs.get("api_url"),
                  api_key=kwargs.get("api_key"),
                  default_model=kwargs.get("model", "tts-1"),
                  default_voice=kwargs.get("voice", "alloy"),
                  response_format=kwargs.get("format", "mp3")
              )
          # ... 기타 제공자들
  ```

- [ ] **사용자 선택 가능한 TTS 설정 시스템**
  ```python
  # src/config/tts_config.py
  class TtsConfigManager:
      def __init__(self):
          self.available_providers = {}
          self.user_preferences = {}
          self.fallback_chain = ['edge_tts', 'siliconflow_tts', 'azure_tts']
      
      async def get_optimal_provider(self, user_id: str, language: str = 'ko') -> dict:
          """사용자 설정 기반 최적 TTS 제공자 선택"""
          user_pref = self.user_preferences.get(user_id, {})
          preferred_provider = user_pref.get('tts_provider')
          
          # 사용자 선택이 있으면 우선 적용
          if preferred_provider and self.is_provider_available(preferred_provider, language):
              return self.get_provider_config(preferred_provider)
          
          # 무료 제공자 우선 선택 (기본값)
          for provider in self.fallback_chain:
              if self.is_provider_available(provider, language):
                  return self.get_provider_config(provider)
      
      def get_user_tts_options(self, user_id: str) -> list:
          """사용자가 선택 가능한 TTS 옵션 반환"""
          options = []
          for provider_id, config in TtsProviderFactory.SUPPORTED_PROVIDERS.items():
              if self.is_provider_accessible(provider_id):
                  options.append({
                      'id': provider_id,
                      'name': config['name'],
                      'cost': config['cost'],
                      'languages': config['languages'],
                      'voices': config.get('voices', [])
                  })
          return options
  ```

### 🎛️ **8.2 TTS-Live2D 통합 매니저**
- [ ] **다중 제공자 지원 TTS 매니저**
  ```python
  # src/tts/live2d_tts_manager.py
  class Live2dTtsManager:
      def __init__(self, config_manager: TtsConfigManager):
          self.config_manager = config_manager
          self.active_engines = {}  # provider_id -> engine instance
          self.audio_analyzer = LipSyncAnalyzer()
      
      async def generate_speech_with_animation(self, text: str, client_uid: str, 
                                             provider_override: str = None) -> dict:
          """다중 제공자 지원 음성 생성과 Live2D 애니메이션"""
          try:
              # 1. 최적 TTS 제공자 선택
              if provider_override:
                  provider_config = self.config_manager.get_provider_config(provider_override)
              else:
                  provider_config = await self.config_manager.get_optimal_provider(client_uid)
              
              # 2. TTS 엔진 초기화 (캐싱)
              tts_engine = await self.get_or_create_engine(provider_config['provider_id'], 
                                                         provider_config['config'])
              
              # 3. 감정 추출 및 음성 파라미터 조정
              emotions = self.extract_emotions_from_text(text)
              adjusted_params = self.adjust_tts_params_for_emotion(emotions, provider_config)
              
              # 4. TTS 음성 생성 (Fallback 지원)
              audio_result = await self.generate_audio_with_fallback(
                  tts_engine, text, adjusted_params, client_uid
              )
              
              # 5. 립싱크 데이터 생성
              lipsync_data = await self.audio_analyzer.generate_lipsync_data(
                  audio_result.audio_path
              )
              
              # 6. 표정 변경 계획
              expression_changes = self.plan_expression_changes(emotions)
              
              return {
                  'provider': provider_config['provider_id'],
                  'audio_path': audio_result.audio_path,
                  'lipsync_data': lipsync_data,
                  'expression_changes': expression_changes,
                  'duration': audio_result.duration,
                  'cost_info': self.calculate_usage_cost(provider_config, len(text))
              }
              
          except Exception as e:
              # Fallback to free provider
              return await self.fallback_to_free_provider(text, client_uid, emotions)
      
      async def generate_audio_with_fallback(self, primary_engine, text: str, 
                                           params: dict, client_uid: str):
          """Fallback 체인을 통한 안정적인 음성 생성"""
          try:
              return await primary_engine.async_generate_audio(text, **params)
          except Exception as e:
              logger.warning(f"Primary TTS failed: {e}, trying fallback")
              
              # Edge TTS로 fallback (무료이므로 항상 가능)
              fallback_engine = await self.get_or_create_engine('edge_tts', {
                  'voice': 'ko-KR-SunHiNeural'
              })
              return await fallback_engine.async_generate_audio(text)
  ```

### 👄 **8.2 립싱크 시스템 구현**
- [ ] **오디오 주파수 분석**
  ```python
  # src/audio/lipsync_analyzer.py
  class LipSyncAnalyzer:
      def __init__(self):
          self.sample_rate = 44100
          self.frame_duration = 0.1  # 100ms per frame
      
      async def generate_lipsync_data(self, audio_path: str) -> list:
          """오디오 파일에서 립싱크 데이터 생성"""
          audio_frames = self.load_and_split_audio(audio_path)
          lipsync_frames = []
          
          for i, frame in enumerate(audio_frames):
              # FFT 분석으로 주파수 특성 추출
              frequency_data = self.analyze_frequency(frame)
              
              # 입 모양 결정 (A, I, U, E, O 모음 기반)
              mouth_shape = self.determine_vowel_shape(frequency_data)
              
              lipsync_frames.append({
                  'timestamp': i * self.frame_duration,
                  'mouth_param': self.vowel_to_param(mouth_shape),
                  'intensity': frame.volume_level
              })
          
          return lipsync_frames
      
      def vowel_to_param(self, vowel: str) -> dict:
          """모음을 Live2D 입 파라미터로 변환"""
          param_map = {
              'A': {'ParamA': 1.0, 'ParamI': 0, 'ParamU': 0, 'ParamE': 0, 'ParamO': 0},
              'I': {'ParamA': 0, 'ParamI': 1.0, 'ParamU': 0, 'ParamE': 0, 'ParamO': 0},
              # ... 기타 모음 매핑
          }
          return param_map.get(vowel, param_map['A'])
  ```

- [ ] **Live2D 립싱크 매핑**
  ```javascript
  // components/Live2DLipSync.jsx
  class Live2DLipSync {
      constructor(live2dModel) {
          this.model = live2dModel;
          this.isPlaying = false;
      }
      
      playLipSyncAnimation(lipsyncData, audioElement) {
          this.isPlaying = true;
          
          const updateLipSync = () => {
              if (!this.isPlaying) return;
              
              const currentTime = audioElement.currentTime;
              const frame = this.findFrameByTime(lipsyncData, currentTime);
              
              if (frame) {
                  // 입 파라미터 업데이트
                  Object.entries(frame.mouth_param).forEach(([param, value]) => {
                      this.model.setParameterValueById(param, value * frame.intensity);
                  });
              }
              
              requestAnimationFrame(updateLipSync);
          };
          
          updateLipSync();
      }
  }
  ```

### 🎭 **8.3 감정 기반 음성 표현**
- [ ] **감정별 TTS 파라미터 조정**
  ```python
  # src/tts/emotion_voice_processor.py
  class EmotionVoiceProcessor:
      EMOTION_VOICE_PARAMS = {
          'joy': {'pitch_shift': +0.2, 'speed_rate': 1.1, 'volume_gain': 0.1},
          'sadness': {'pitch_shift': -0.15, 'speed_rate': 0.9, 'volume_gain': -0.1},
          'anger': {'pitch_shift': +0.1, 'speed_rate': 1.2, 'volume_gain': 0.15},
          'fear': {'pitch_shift': +0.3, 'speed_rate': 1.3, 'volume_gain': -0.05},
          'surprise': {'pitch_shift': +0.25, 'speed_rate': 1.15, 'volume_gain': 0.05},
          'neutral': {'pitch_shift': 0, 'speed_rate': 1.0, 'volume_gain': 0}
      }
      
      def adjust_tts_for_emotion(self, tts_params: dict, emotion: str) -> dict:
          """감정에 따른 TTS 파라미터 조정"""
          emotion_adjustment = self.EMOTION_VOICE_PARAMS.get(emotion, self.EMOTION_VOICE_PARAMS['neutral'])
          
          adjusted_params = tts_params.copy()
          for param, adjustment in emotion_adjustment.items():
              if param in adjusted_params:
                  adjusted_params[param] += adjustment
          
          return adjusted_params
  ```

### 🔄 **8.4 실시간 TTS-Live2D 동기화**
- [ ] **WebSocket TTS 스트리밍**
  ```python
  # src/websocket/tts_live2d_handler.py
  class TtsLive2dHandler:
      async def handle_tts_request(self, websocket: WebSocket, request_data: dict):
          """TTS 요청 처리 및 Live2D 동기화"""
          try:
              client_uid = request_data['client_uid']
              text = request_data['text']
              
              # 1. TTS + Live2D 데이터 생성
              tts_result = await self.tts_manager.generate_speech_with_animation(text, client_uid)
              
              # 2. 표정 변경 먼저 적용
              await websocket.send_json({
                  'type': 'expression_changes',
                  'data': tts_result['expression_changes']
              })
              
              # 3. 음성 재생 준비 완료 알림
              await websocket.send_json({
                  'type': 'tts_ready',
                  'data': {
                      'audio_path': tts_result['audio_path'],
                      'lipsync_data': tts_result['lipsync_data'],
                      'duration': tts_result['duration']
                  }
              })
              
          except Exception as e:
              await websocket.send_json({
                  'type': 'tts_error',
                  'error': str(e)
              })
  ```

### 🎵 **8.5 오디오 품질 최적화**
- [ ] **오디오 후처리 시스템**
  ```python
  # src/audio/audio_enhancer.py
  class AudioEnhancer:
      def enhance_for_lipsync(self, audio_data: bytes) -> bytes:
          """립싱크 최적화를 위한 오디오 처리"""
          # 1. 노이즈 리덕션
          cleaned_audio = self.reduce_noise(audio_data)
          
          # 2. 모음 강조 (립싱크 정확도 향상)
          vowel_enhanced = self.enhance_vowel_clarity(cleaned_audio)
          
          # 3. 볼륨 정규화
          normalized_audio = self.normalize_volume(vowel_enhanced)
          
          return normalized_audio
  ```

### 🎚️ **8.6 사용자 TTS 설정 API 시스템**
- [ ] **TTS 제공자 선택 API 엔드포인트**
  ```python
  # routes/tts_settings_routes.py
  @router.get("/api/tts/providers")
  async def get_available_tts_providers(user_id: str = Query(...)):
      """사용자가 선택 가능한 TTS 제공자 목록 조회"""
      config_manager = get_tts_config_manager()
      return config_manager.get_user_tts_options(user_id)
  
  @router.post("/api/tts/settings")
  async def update_user_tts_settings(request: TtsSettingsRequest):
      """사용자 TTS 설정 업데이트"""
      config_manager = get_tts_config_manager()
      await config_manager.update_user_preference(
          request.user_id, 
          {
              'tts_provider': request.provider_id,
              'voice': request.voice,
              'speed': request.speed,
              'pitch': request.pitch
          }
      )
      return {"status": "success", "message": "TTS 설정이 업데이트되었습니다."}
  
  @router.post("/api/tts/test")
  async def test_tts_voice(request: TtsTestRequest):
      """선택한 TTS 제공자로 테스트 음성 생성"""
      tts_manager = get_live2d_tts_manager()
      test_result = await tts_manager.generate_speech_with_animation(
          text="안녕하세요! 이 목소리가 마음에 드시나요?",
          client_uid=request.user_id,
          provider_override=request.provider_id
      )
      return {
          "audio_url": test_result['audio_path'],
          "provider": test_result['provider'],
          "cost_info": test_result['cost_info']
      }
  ```

- [ ] **프론트엔드 TTS 설정 컴포넌트**
  ```javascript
  // components/TtsSettingsPanel.jsx
  function TtsSettingsPanel({ userId, onSettingsChange }) {
      const [providers, setProviders] = useState([]);
      const [currentSettings, setCurrentSettings] = useState({});
      const [isPlaying, setIsPlaying] = useState(false);
      
      // TTS 제공자 목록 로드
      useEffect(() => {
          fetchTtsProviders();
      }, [userId]);
      
      const fetchTtsProviders = async () => {
          const response = await fetch(`/api/tts/providers?user_id=${userId}`);
          const data = await response.json();
          setProviders(data);
      };
      
      const testVoice = async (providerId, voice) => {
          setIsPlaying(true);
          try {
              const response = await fetch('/api/tts/test', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                      user_id: userId,
                      provider_id: providerId,
                      voice: voice
                  })
              });
              const result = await response.json();
              
              // 테스트 음성 재생
              const audio = new Audio(result.audio_url);
              audio.play();
              
              // 비용 정보 표시
              if (result.cost_info.cost > 0) {
                  showCostNotification(result.cost_info);
              }
              
          } catch (error) {
              console.error('TTS 테스트 실패:', error);
          } finally {
              setIsPlaying(false);
          }
      };
      
      return (
          <div className="tts-settings-panel">
              <h3>🎙️ TTS 음성 설정</h3>
              
              {providers.map(provider => (
                  <div key={provider.id} className="provider-option">
                      <div className="provider-header">
                          <h4>{provider.name}</h4>
                          <span className={`cost-badge ${provider.cost}`}>
                              {provider.cost === 'free' ? '무료' : 
                               provider.cost === 'free_tier' ? '무료 한도' : '유료'}
                          </span>
                          {provider.recommended && (
                              <span className="recommended-badge">추천</span>
                          )}
                      </div>
                      
                      <div className="voice-options">
                          {provider.voices.map(voice => (
                              <button 
                                  key={voice}
                                  onClick={() => testVoice(provider.id, voice)}
                                  disabled={isPlaying}
                                  className="voice-test-btn"
                              >
                                  {voice} {isPlaying ? '재생중...' : '테스트'}
                              </button>
                          ))}
                      </div>
                  </div>
              ))}
          </div>
      );
  }
  ```

### 🧪 **8.7 TTS-Live2D 통합 테스트**
- [ ] **음성-애니메이션 동기화 테스트**
  - 립싱크 정확도 측정 (음성-입술 동기화)
  - 감정 표현 일치도 테스트
  - 실시간 스트리밍 지연시간 측정
  - 다양한 텍스트 길이별 성능 테스트

- [ ] **다중 제공자 시스템 테스트**
  - 각 TTS 제공자별 품질 및 성능 측정
  - Fallback 체인 동작 검증
  - API 한도 및 비용 추적 정확성 테스트
  - 사용자 설정 저장/로드 테스트

---

## 💬 **Phase 9: LLM Live2D 대화형 시스템**

### 🧠 **9.1 다중 LLM 제공자 시스템 구축**
- [ ] **LLM 제공자 팩토리 및 관리 시스템**
  ```python
  # src/llm/llm_provider_factory.py (Reference LLMFactory 기반 확장)
  class LlmProviderFactory:
      SUPPORTED_PROVIDERS = {
          # 무료/저비용 제공자들 (우선순위)
          'cerebras_llm': {
              'name': 'Cerebras Inference',
              'cost': 'free_tier',
              'base_url': 'https://api.cerebras.ai/v1',
              'models': ['llama3.1-8b', 'llama3.1-70b'],
              'context_limit': 128000,
              'speed': 'very_fast'
          },
          'groq_llm': {
              'name': 'Groq',
              'cost': 'free_tier',
              'base_url': 'https://api.groq.com/openai/v1',
              'models': ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768'],
              'context_limit': 32768,
              'speed': 'very_fast'
          },
          'deepseek_llm': {
              'name': 'DeepSeek',
              'cost': 'low_cost',
              'base_url': 'https://api.deepseek.com/v1',
              'models': ['deepseek-chat', 'deepseek-coder'],
              'context_limit': 32768,
              'speed': 'fast'
          },
          'gemini_llm': {
              'name': 'Google Gemini',
              'cost': 'free_tier',
              'base_url': 'https://generativelanguage.googleapis.com/v1beta',
              'models': ['gemini-1.5-flash', 'gemini-1.5-pro'],
              'context_limit': 1048576,
              'speed': 'medium'
          },
          # 로컬 옵션
          'ollama_llm': {
              'name': 'Ollama (Local)',
              'cost': 'free',
              'base_url': 'http://localhost:11434/v1',
              'models': ['qwen2.5:7b', 'llama3.2:3b'],
              'context_limit': 32768,
              'speed': 'depends_on_hardware'
          },
          # 유료 백업 옵션들
          'openai_llm': {
              'name': 'OpenAI GPT',
              'cost': 'paid',
              'base_url': 'https://api.openai.com/v1',
              'models': ['gpt-4o-mini', 'gpt-4o'],
              'context_limit': 128000,
              'speed': 'fast'
          }
      }
      
      @staticmethod
      def create_llm_client(provider_type: str, **kwargs):
          """Reference LLMFactory 패턴 확장"""
          if provider_type in ['cerebras_llm', 'groq_llm', 'deepseek_llm', 
                              'openai_llm', 'gemini_llm']:
              from .openai_compatible_llm import AsyncLLM as OpenAICompatibleLLM
              return OpenAICompatibleLLM(
                  model=kwargs.get("model"),
                  base_url=kwargs.get("base_url"),
                  llm_api_key=kwargs.get("api_key", "not-needed"),
                  organization_id=kwargs.get("organization_id"),
                  project_id=kwargs.get("project_id"),
                  temperature=kwargs.get("temperature", 0.7)
              )
          elif provider_type == "ollama_llm":
              from .ollama_llm import OllamaLLM
              return OllamaLLM(
                  model=kwargs.get("model", "qwen2.5:7b"),
                  base_url=kwargs.get("base_url", "http://localhost:11434/v1"),
                  temperature=kwargs.get("temperature", 0.7)
              )
          else:
              raise ValueError(f"Unsupported LLM provider: {provider_type}")
  ```

- [ ] **사용자 선택 가능한 LLM 설정 시스템**
  ```python
  # src/config/llm_config.py
  class LlmConfigManager:
      def __init__(self):
          self.available_providers = {}
          self.user_preferences = {}
          # 무료 우선, 성능 고려한 Fallback 체인
          self.fallback_chain = [
              'cerebras_llm',  # 무료 + 매우 빠름
              'groq_llm',      # 무료 + 매우 빠름  
              'gemini_llm',    # 무료 + 큰 컨텍스트
              'deepseek_llm',  # 저비용 + 좋은 성능
              'ollama_llm'     # 로컬 + 완전 무료
          ]
      
      async def get_optimal_provider(self, user_id: str, 
                                   conversation_length: int = 0) -> dict:
          """사용자 설정과 컨텍스트 길이 기반 최적 LLM 제공자 선택"""
          user_pref = self.user_preferences.get(user_id, {})
          preferred_provider = user_pref.get('llm_provider')
          
          # 사용자 선택이 있으면 우선 적용
          if preferred_provider and self.is_provider_available(preferred_provider):
              provider_config = self.get_provider_config(preferred_provider)
              if conversation_length <= provider_config['context_limit']:
                  return provider_config
          
          # 컨텍스트 길이와 성능을 고려한 자동 선택
          for provider_id in self.fallback_chain:
              provider_config = self.get_provider_config(provider_id)
              if (self.is_provider_available(provider_id) and 
                  conversation_length <= provider_config['context_limit']):
                  return provider_config
          
          # 모든 제공자가 실패한 경우 기본값 (Cerebras)
          return self.get_provider_config('cerebras_llm')
      
      def get_user_llm_options(self, user_id: str) -> list:
          """사용자가 선택 가능한 LLM 옵션 반환"""
          options = []
          for provider_id, config in LlmProviderFactory.SUPPORTED_PROVIDERS.items():
              if self.is_provider_accessible(provider_id):
                  options.append({
                      'id': provider_id,
                      'name': config['name'],
                      'cost': config['cost'],
                      'models': config['models'],
                      'speed': config['speed'],
                      'context_limit': config['context_limit'],
                      'recommended': provider_id in ['cerebras_llm', 'groq_llm']
                  })
          return options
  ```

### 🤖 **9.2 Live2D 대화 에이전트 시스템**
- [ ] **다중 LLM 지원 대화 에이전트**
  ```python
  # src/agent/live2d_chat_agent.py
  class Live2dChatAgent:
      def __init__(self, llm_config_manager: LlmConfigManager, 
                   character_manager, tts_manager):
          self.llm_config_manager = llm_config_manager
          self.active_llm_clients = {}  # provider_id -> client instance
          self.character_manager = character_manager
          self.tts_manager = tts_manager
          self.conversation_memory = ConversationMemory()
          self.personality_manager = CharacterPersonality()
      
      async def process_chat_message(self, message: str, client_uid: str,
                                   llm_override: str = None) -> dict:
          """다중 LLM 지원 채팅 메시지 처리"""
          try:
              # 1. 대화 컨텍스트 및 길이 계산
              context = self.conversation_memory.get_conversation_history(client_uid)
              context_length = self.estimate_context_tokens(context + [{"role": "user", "content": message}])
              
              # 2. 최적 LLM 제공자 선택
              if llm_override:
                  provider_config = self.llm_config_manager.get_provider_config(llm_override)
              else:
                  provider_config = await self.llm_config_manager.get_optimal_provider(
                      client_uid, context_length
                  )
              
              # 3. LLM 클라이언트 초기화 (캐싱)
              llm_client = await self.get_or_create_llm_client(
                  provider_config['provider_id'], provider_config['config']
              )
              
              # 4. 캐릭터 개성 기반 시스템 프롬프트
              character_prompt = self.personality_manager.get_system_prompt()
              
              # 5. LLM 응답 생성 (Fallback 지원)
              llm_response = await self.generate_response_with_fallback(
                  llm_client, message, context, character_prompt, client_uid
              )
              
              # 6. 응답에서 감정/동작 추출
              emotions = self.extract_emotion_tags(llm_response.text)
              gestures = self.detect_gesture_cues(llm_response.text)
              
              # 7. Live2D 애니메이션 계획 수립
              animation_plan = self.create_animation_sequence(emotions, gestures)
              
              # 8. TTS + 립싱크 준비 (비동기)
              tts_task = asyncio.create_task(
                  self.tts_manager.generate_speech_with_animation(
                      llm_response.clean_text, client_uid
                  )
              )
              
              # 9. 대화 메모리 업데이트
              await self.conversation_memory.add_conversation_turn(
                  client_uid, message, llm_response.clean_text, emotions
              )
              
              return {
                  'provider': provider_config['provider_id'],
                  'model': provider_config.get('model', 'unknown'),
                  'text_response': llm_response.clean_text,
                  'emotions': emotions,
                  'animation_plan': animation_plan,
                  'tts_task': tts_task,
                  'conversation_id': llm_response.conversation_id,
                  'cost_info': self.calculate_llm_usage_cost(provider_config, context_length),
                  'performance_metrics': {
                      'response_time': llm_response.response_time,
                      'token_count': len(llm_response.clean_text.split())
                  }
              }
              
          except Exception as e:
              logger.error(f"Chat processing error: {e}")
              return await self.generate_fallback_response(client_uid)
      
      async def generate_response_with_fallback(self, primary_client, message: str,
                                              context: list, system_prompt: str,
                                              client_uid: str):
          """Fallback 체인을 통한 안정적인 응답 생성"""
          try:
              return await primary_client.chat_completion(
                  messages=context + [{"role": "user", "content": message}],
                  system=system_prompt
              )
          except Exception as e:
              logger.warning(f"Primary LLM failed: {e}, trying fallback")
              
              # Cerebras AI로 fallback (무료이고 빠름)
              fallback_client = await self.get_or_create_llm_client('cerebras_llm', {
                  'api_key': 'demo',  # Cerebras는 무료 tier에서 demo key 사용 가능
                  'model': 'llama3.1-8b',
                  'base_url': 'https://api.cerebras.ai/v1'
              })
              
              return await fallback_client.chat_completion(
                  messages=context[-10:] + [{"role": "user", "content": message}],  # 컨텍스트 축소
                  system=system_prompt
              )
  ```

### 💭 **9.2 대화형 WebSocket 핸들러**
- [ ] **실시간 채팅 처리 시스템**
  ```python
  # src/websocket/chat_live2d_handler.py
  class ChatLive2dHandler:
      async def handle_chat_message(self, websocket: WebSocket, message_data: dict):
          """실시간 채팅 메시지 처리 및 Live2D 연동"""
          client_uid = message_data.get('client_uid')
          user_message = message_data.get('message')
          
          try:
              # 1. 타이핑 애니메이션 시작
              await websocket.send_json({
                  'type': 'character_status',
                  'data': {'status': 'thinking', 'animation': 'typing'}
              })
              
              # 2. AI 응답 생성
              chat_result = await self.chat_agent.process_chat_message(user_message, client_uid)
              
              # 3. 타이핑 중지
              await websocket.send_json({
                  'type': 'character_status',
                  'data': {'status': 'ready'}
              })
              
              # 4. 텍스트 응답 즉시 전송
              await websocket.send_json({
                  'type': 'chat_response',
                  'data': {
                      'text': chat_result['text_response'],
                      'emotions': chat_result['emotions'],
                      'timestamp': datetime.now().isoformat()
                  }
              })
              
              # 5. Live2D 애니메이션 실행
              await self.execute_animation_sequence(websocket, chat_result['animation_plan'])
              
              # 6. TTS 음성 재생 (준비 완료 시)
              tts_data = await chat_result['tts_task']
              await websocket.send_json({
                  'type': 'tts_ready',
                  'data': tts_data
              })
              
          except Exception as e:
              await self.send_error_response(websocket, str(e))
  ```

### 🎭 **9.3 캐릭터 개성 시스템**
- [ ] **동적 캐릭터 개성 관리**
  ```python
  # src/character/personality_system.py
  class CharacterPersonality:
      def __init__(self, character_config: dict):
          self.personality_traits = character_config.get('personality', {})
          self.speech_patterns = character_config.get('speech_style', {})
          self.emotional_tendencies = character_config.get('emotions', {})
      
      def get_system_prompt(self) -> str:
          """캐릭터 개성이 반영된 시스템 프롬프트 생성"""
          base_prompt = f"""
          당신은 {self.personality_traits.get('name', 'AI 어시스턴트')}입니다.
          
          성격 특성:
          - 기본 성향: {self.personality_traits.get('base_trait', '친근하고 도움이 되는')}
          - 대화 스타일: {self.speech_patterns.get('style', '정중하고 자연스러운')}
          - 특별한 특징: {self.personality_traits.get('unique_trait', '없음')}
          
          감정 표현 방식:
          대화 중 감정을 다음과 같이 표현해주세요:
          - 기쁠 때: [joy] 태그 사용, 밝은 어조
          - 슬플 때: [sadness] 태그 사용, 차분한 어조  
          - 놀랄 때: [surprise] 태그 사용, 역동적인 표현
          - 화날 때: [anger] 태그 사용 (단, 부적절한 상황에서만)
          - 무서울 때: [fear] 태그 사용
          - 평상시: [neutral] 태그 사용
          
          제스처 표현:
          - 인사할 때: [gesture:wave] 또는 [gesture:bow]
          - 동의할 때: [gesture:nod]
          - 생각할 때: [gesture:thinking]
          - 강조할 때: [gesture:point]
          
          항상 Live2D 캐릭터로서 자연스럽고 생동감 있는 대화를 해주세요.
          """
          
          return base_prompt
      
      def adjust_response_style(self, response: str, context: dict) -> str:
          """캐릭터 개성에 따른 응답 스타일 조정"""
          # 성격에 따른 어조 조정 로직
          return response
  ```

### 🧠 **9.4 대화 컨텍스트 & 메모리 시스템**
- [ ] **고급 대화 메모리 관리**
  ```python
  # src/memory/conversation_memory.py
  class ConversationMemory:
      def __init__(self, max_short_term: int = 20, max_long_term: int = 100):
          self.short_term_memory = {}  # client_uid -> recent messages
          self.long_term_memory = {}   # client_uid -> summarized context
          self.emotional_memory = {}   # client_uid -> emotion patterns
          self.max_short_term = max_short_term
          self.max_long_term = max_long_term
      
      async def add_conversation_turn(self, client_uid: str, user_msg: str, ai_response: str, emotions: list):
          """대화 턴 기록 및 메모리 관리"""
          # 단기 메모리에 추가
          if client_uid not in self.short_term_memory:
              self.short_term_memory[client_uid] = []
          
          turn_data = {
              'timestamp': datetime.now(),
              'user_message': user_msg,
              'ai_response': ai_response,
              'emotions': emotions,
              'context_summary': self.generate_turn_summary(user_msg, ai_response)
          }
          
          self.short_term_memory[client_uid].append(turn_data)
          
          # 메모리 길이 제한 및 장기 메모리 압축
          if len(self.short_term_memory[client_uid]) > self.max_short_term:
              await self.compress_to_long_term_memory(client_uid)
      
      def get_conversation_context(self, client_uid: str) -> list:
          """대화 컨텍스트 조회 (단기 + 장기 메모리 결합)"""
          context = []
          
          # 장기 메모리 요약
          if client_uid in self.long_term_memory:
              context.append({
                  'role': 'system',
                  'content': f"이전 대화 요약: {self.long_term_memory[client_uid]}"
              })
          
          # 단기 메모리 상세 내용
          if client_uid in self.short_term_memory:
              for turn in self.short_term_memory[client_uid][-10:]:  # 최근 10턴
                  context.extend([
                      {'role': 'user', 'content': turn['user_message']},
                      {'role': 'assistant', 'content': turn['ai_response']}
                  ])
          
          return context
  ```

### ⚡ **9.5 고급 상호작용 & 제스처 시스템**
- [ ] **상황별 제스처 및 반응 시스템**
  ```python
  # src/interaction/advanced_gesture_system.py
  class AdvancedGestureSystem:
      GESTURE_LIBRARY = {
          # 인사 관련
          'greeting_morning': {'animation': 'wave', 'expression': 'joy', 'voice_tone': 'cheerful'},
          'greeting_evening': {'animation': 'bow', 'expression': 'neutral', 'voice_tone': 'calm'},
          
          # 감정 반응
          'empathy_sad': {'animation': 'pat', 'expression': 'sadness', 'voice_tone': 'gentle'},
          'celebration': {'animation': 'clap', 'expression': 'joy', 'voice_tone': 'excited'},
          
          # 사고 과정
          'deep_thinking': {'animation': 'thinking_pose', 'expression': 'neutral', 'voice_tone': 'contemplative'},
          'eureka_moment': {'animation': 'point_up', 'expression': 'surprise', 'voice_tone': 'excited'},
          
          # 대화 관리
          'topic_change': {'animation': 'gesture_transition', 'expression': 'neutral', 'voice_tone': 'normal'},
          'confusion': {'animation': 'head_tilt', 'expression': 'surprise', 'voice_tone': 'questioning'}
      }
      
      async def analyze_conversation_context(self, message: str, history: list) -> dict:
          """대화 맥락 분석을 통한 적절한 제스처 선택"""
          # 1. 인사 패턴 감지
          if self.is_greeting(message):
              time_of_day = datetime.now().hour
              return self.GESTURE_LIBRARY['greeting_morning' if 6 <= time_of_day < 18 else 'greeting_evening']
          
          # 2. 감정 상태 분석
          user_emotion = self.detect_user_emotion(message)
          if user_emotion == 'sad':
              return self.GESTURE_LIBRARY['empathy_sad']
          elif user_emotion == 'excited':
              return self.GESTURE_LIBRARY['celebration']
          
          # 3. 복잡한 질문 감지
          if self.is_complex_query(message):
              return self.GESTURE_LIBRARY['deep_thinking']
          
          return self.GESTURE_LIBRARY['topic_change']  # 기본 제스처
  ```

### 📈 **9.6 대화 품질 최적화 & 성능 튜닝**
- [ ] **응답 최적화 시스템**
  ```python
  # src/optimization/chat_optimizer.py
  class ChatResponseOptimizer:
      def __init__(self):
          self.response_cache = TTLCache(maxsize=500, ttl=1800)  # 30분 캐시
          self.llm_connection_pool = AsyncConnectionPool(max_size=10)
          self.performance_tracker = ResponseTimeTracker()
      
      async def get_optimized_response(self, message: str, context: list, client_uid: str) -> dict:
          """캐싱과 커넥션 풀을 활용한 최적화된 응답 생성"""
          # 1. 응답 캐시 확인
          cache_key = self.generate_cache_key(message, context)
          cached_response = self.response_cache.get(cache_key)
          if cached_response and not self.is_context_sensitive(message):
              self.performance_tracker.record_cache_hit(client_uid)
              return cached_response
          
          # 2. LLM 커넥션 풀에서 클라이언트 획득
          start_time = time.time()
          
          async with self.llm_connection_pool.acquire() as llm_client:
              response = await llm_client.generate_response(message, context)
          
          response_time = time.time() - start_time
          self.performance_tracker.record_response_time(client_uid, response_time)
          
          # 3. 응답 캐싱 (개인적이지 않은 응답만)
          if not self.is_personal_response(response):
              self.response_cache[cache_key] = response
          
          return response
  ```

### 🎛️ **9.6 사용자 LLM 설정 API 시스템**
- [ ] **LLM 제공자 선택 API 엔드포인트**
  ```python
  # routes/llm_settings_routes.py
  @router.get("/api/llm/providers")
  async def get_available_llm_providers(user_id: str = Query(...)):
      """사용자가 선택 가능한 LLM 제공자 목록 조회"""
      config_manager = get_llm_config_manager()
      return config_manager.get_user_llm_options(user_id)
  
  @router.post("/api/llm/settings")
  async def update_user_llm_settings(request: LlmSettingsRequest):
      """사용자 LLM 설정 업데이트"""
      config_manager = get_llm_config_manager()
      await config_manager.update_user_preference(
          request.user_id,
          {
              'llm_provider': request.provider_id,
              'model': request.model,
              'temperature': request.temperature,
              'max_tokens': request.max_tokens
          }
      )
      return {"status": "success", "message": "LLM 설정이 업데이트되었습니다."}
  
  @router.post("/api/llm/test")
  async def test_llm_response(request: LlmTestRequest):
      """선택한 LLM 제공자로 테스트 응답 생성"""
      chat_agent = get_live2d_chat_agent()
      test_result = await chat_agent.process_chat_message(
          message="안녕하세요! 자기소개를 해주세요.",
          client_uid=request.user_id,
          llm_override=request.provider_id
      )
      return {
          "response": test_result['text_response'],
          "provider": test_result['provider'],
          "model": test_result['model'],
          "performance_metrics": test_result['performance_metrics'],
          "cost_info": test_result['cost_info']
      }
  ```

- [ ] **프론트엔드 LLM 설정 컴포넌트**
  ```javascript
  // components/LlmSettingsPanel.jsx
  function LlmSettingsPanel({ userId, onSettingsChange }) {
      const [providers, setProviders] = useState([]);
      const [currentSettings, setCurrentSettings] = useState({});
      const [isGenerating, setIsGenerating] = useState(false);
      const [testResponse, setTestResponse] = useState('');
      
      useEffect(() => {
          fetchLlmProviders();
      }, [userId]);
      
      const fetchLlmProviders = async () => {
          const response = await fetch(`/api/llm/providers?user_id=${userId}`);
          const data = await response.json();
          setProviders(data);
      };
      
      const testModel = async (providerId, model) => {
          setIsGenerating(true);
          setTestResponse('');
          
          try {
              const response = await fetch('/api/llm/test', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({
                      user_id: userId,
                      provider_id: providerId,
                      model: model
                  })
              });
              const result = await response.json();
              
              setTestResponse(result.response);
              
              // 성능 및 비용 정보 표시
              showPerformanceMetrics(result.performance_metrics, result.cost_info);
              
          } catch (error) {
              console.error('LLM 테스트 실패:', error);
              setTestResponse('테스트 중 오류가 발생했습니다.');
          } finally {
              setIsGenerating(false);
          }
      };
      
      return (
          <div className="llm-settings-panel">
              <h3>🧠 AI 대화 설정</h3>
              
              {providers.map(provider => (
                  <div key={provider.id} className="provider-option">
                      <div className="provider-header">
                          <h4>{provider.name}</h4>
                          <div className="provider-badges">
                              <span className={`cost-badge ${provider.cost}`}>
                                  {provider.cost === 'free' ? '무료' : 
                                   provider.cost === 'free_tier' ? '무료 한도' : 
                                   provider.cost === 'low_cost' ? '저비용' : '유료'}
                              </span>
                              <span className={`speed-badge ${provider.speed}`}>
                                  {provider.speed === 'very_fast' ? '매우 빠름' : 
                                   provider.speed === 'fast' ? '빠름' : 
                                   provider.speed === 'medium' ? '보통' : '하드웨어 의존'}
                              </span>
                              {provider.recommended && (
                                  <span className="recommended-badge">추천</span>
                              )}
                          </div>
                      </div>
                      
                      <div className="provider-details">
                          <p>컨텍스트 한도: {provider.context_limit.toLocaleString()} 토큰</p>
                          <div className="model-options">
                              <label>모델 선택:</label>
                              {provider.models.map(model => (
                                  <button
                                      key={model}
                                      onClick={() => testModel(provider.id, model)}
                                      disabled={isGenerating}
                                      className="model-test-btn"
                                  >
                                      {model} {isGenerating ? '생성중...' : '테스트'}
                                  </button>
                              ))}
                          </div>
                      </div>
                  </div>
              ))}
              
              {testResponse && (
                  <div className="test-response">
                      <h4>테스트 응답:</h4>
                      <div className="response-text">{testResponse}</div>
                  </div>
              )}
          </div>
      );
  }
  ```

### 💾 **9.7 통합 설정 관리 시스템**
- [ ] **통합 사용자 설정 저장소**
  ```python
  # src/config/user_preferences.py
  class UserPreferencesManager:
      def __init__(self, db_connection):
          self.db = db_connection
          self.cache = {}  # user_id -> preferences
      
      async def get_user_preferences(self, user_id: str) -> dict:
          """사용자의 모든 설정 조회 (TTS + LLM)"""
          if user_id not in self.cache:
              self.cache[user_id] = await self.load_from_db(user_id)
          
          return self.cache[user_id]
      
      async def update_preferences(self, user_id: str, category: str, settings: dict):
          """설정 업데이트 (category: 'tts' | 'llm' | 'character')"""
          if user_id not in self.cache:
              self.cache[user_id] = await self.load_from_db(user_id)
          
          self.cache[user_id][category].update(settings)
          await self.save_to_db(user_id, self.cache[user_id])
      
      def get_default_preferences(self) -> dict:
          """기본 설정 반환"""
          return {
              'llm': {
                  'provider': 'cerebras_llm',  # 무료 우선
                  'model': 'llama3.1-8b',
                  'temperature': 0.7,
                  'max_tokens': 2048
              },
              'tts': {
                  'provider': 'edge_tts',  # 무료
                  'voice': 'ko-KR-SunHiNeural',
                  'speed': 1.0,
                  'pitch': 0
              },
              'character': {
                  'personality': 'friendly',
                  'animation_intensity': 'normal',
                  'auto_expressions': True
              }
          }
  ```

### 🧪 **9.8 LLM-Live2D 시스템 종합 테스트**
- [ ] **대화형 시스템 통합 테스트**
  - 자연스러운 대화 흐름 검증
  - 감정 표현 일관성 및 정확성 테스트
  - 캐릭터 개성 유지 검증
  - 메모리 시스템 정확성 및 성능 테스트

- [ ] **다중 제공자 시스템 테스트**
  - 각 LLM 제공자별 응답 품질 및 속도 측정
  - Fallback 체인 동작 검증 (Cerebras → Groq → Gemini)
  - API 한도 및 비용 추적 정확성 테스트
  - 사용자 설정 저장/로드 및 동기화 테스트

- [ ] **성능 벤치마크 및 최적화**
  - 응답 생성 속도 측정 (목표: 3초 이하, Cerebras/Groq는 1초 이하)
  - 동시 대화 처리 능력 테스트 (목표: 50명)
  - 메모리 사용량 모니터링 및 최적화
  - 무료 API 한도 관리 및 자동 fallback 테스트

---

## 🧪 **Phase 10: 통합 테스트 & 품질 보증**

### 🔍 **10.1 Live2D 시스템 통합 테스트**
- [ ] **Live2D 모델 시스템 테스트**
  - Live2D 모델 로딩 정확성 및 성능 테스트
  - 모델 메타데이터 파싱 무결성 검증
  - 표정/모션 파일 로딩 및 실행 테스트
  - 브라우저 간 Live2D 렌더링 호환성 테스트

- [ ] **실시간 동기화 시스템 테스트**
  - WebSocket 기반 Live2D 상태 동기화 테스트
  - 다중 클라이언트 동시 접속 시 상태 관리 검증
  - 표정/모션 변경 지연시간 측정 (목표: < 100ms)
  - 네트워크 지연 상황에서의 동기화 안정성 테스트

### 🎙️ **10.2 TTS-Live2D 통합 시스템 테스트**
- [ ] **음성-애니메이션 동기화 테스트**
  - TTS 음성과 Live2D 립싱크 정확도 측정
  - 감정별 음성 변조와 표정 변경 일치도 테스트
  - 실시간 TTS 스트리밍 지연시간 최적화
  - 다양한 텍스트 길이 및 언어에 대한 성능 테스트

- [ ] **오디오 품질 및 성능 테스트**
  - 립싱크 데이터 생성 정확도 검증
  - 오디오 후처리 품질 및 처리 시간 측정
  - 음성 캐싱 시스템 효율성 검증
  - 동시 TTS 요청 처리 능력 테스트

### 💬 **10.3 LLM-Live2D 대화 시스템 테스트**
- [ ] **대화형 AI 시스템 검증**
  - LLM 응답 품질 및 일관성 테스트
  - 감정 태그 추출 및 Live2D 애니메이션 연동 정확도
  - 대화 컨텍스트 유지 및 메모리 시스템 검증
  - 캐릭터 개성 유지 및 일관성 테스트

- [ ] **종합 성능 벤치마크**
  - 전체 대화 처리 파이프라인 지연시간 측정 (목표: < 3초)
  - 동시 대화 세션 처리 능력 (목표: 50세션)
  - 메모리 사용량 및 LLM API 사용량 최적화 검증
  - 응답 캐싱 시스템 효율성 및 적중률 측정

### 🛡️ **10.4 보안 & 품질 보증 테스트**
- [ ] **보안 검증 테스트**
  - 콘텐츠 필터링 시스템 정확도 (목표: 95% 이상)
  - WebSocket 보안 및 인증 시스템 검증
  - 입력 데이터 검증 및 SQL 인젝션 방어 테스트
  - 개인정보 보호 및 데이터 마스킹 시스템 검증

- [ ] **API 및 시스템 안정성 테스트**
  ```python
  # 통합 테스트 시나리오
  # Live2D + TTS + LLM 전체 파이프라인 테스트
  async def test_full_conversation_pipeline():
      # 1. Live2D 모델 초기화
      # 2. 사용자 메시지 입력
      # 3. LLM 응답 생성 및 감정 추출
      # 4. Live2D 애니메이션 트리거
      # 5. TTS 음성 생성 및 립싱크
      # 6. 전체 파이프라인 성능 측정
  ```

- [ ] **부하 테스트 및 확장성 검증**
  - 동시 사용자 수: 100명 (목표)
  - 초당 요청: 1000 RPS (목표)
  - Live2D 렌더링 성능: 60fps 유지
  - 메모리 사용량: < 1GB (전체 시스템)

### 🎯 **10.5 사용성 및 UX 테스트**
- [ ] **사용자 경험 검증**
  - Live2D 캐릭터 반응 자연스러움 평가
  - 대화 흐름 및 응답 품질 사용성 테스트
  - 크로스 플랫폼 호환성 (데스크톱, 모바일) 검증
  - 접근성 (Accessibility) 기준 충족 검증

- [ ] **모니터링 및 분석 시스템 검증**
  - 실시간 성능 모니터링 정확성 확인
  - 오류 추적 및 로깅 시스템 동작 검증
  - 사용자 행동 분석 데이터 수집 정확성
  - 알림 시스템 및 대시보드 동작 확인

---

## 🚀 **Phase 11: 배포 & 운영 준비**

### 📦 **11.1 배포 시스템 구축**
- [ ] **Docker 컨테이너화**
  - Dockerfile 최적화 (Multi-stage build)
  - Docker Compose 개발 환경
  - 환경별 설정 관리 (.env 파일)
  - 헬스체크 및 재시작 정책

- [ ] **CI/CD 파이프라인**
  - GitHub Actions 워크플로우
  - Python + JavaScript 자동 테스트 실행
  - 스테이징 환경 자동 배포
  - 프로덕션 배포 승인 프로세스

- [ ] **환경 설정 관리**
  - 개발/스테이징/프로덕션 환경 분리
  - 비밀키 관리 (환경변수, Vault)
  - 설정 검증 로직 (startup check)
  - 롤백 전략 수립

### 🔧 **11.2 운영 도구 및 프로세스**
- [ ] **데이터베이스 관리 도구**
  - 마이그레이션 자동화 스크립트
  - 백업 자동화 (일일 백업)
  - 데이터 정합성 검증 도구
  - 성능 모니터링 대시보드

- [ ] **장애 대응 매뉴얼**
  - 서비스 장애 분류 및 대응 절차
  - 롤백 수행 가이드
  - 긴급 연락망 및 에스컬레이션
  - 장애 후 복구 검증 절차

- [ ] **용량 계획 및 확장성**
  - 사용자 증가에 따른 리소스 요구량 예측
  - 수평 확장 전략 (로드 밸런서, 클러스터링)
  - SQLite → MariaDB 마이그레이션 계획
  - CDN 도입 및 캐시 전략 고도화

---

## ✅ **단계별 완료 기준 (Definition of Done)**

### **Phase 1 완료 기준**
- [ ] API 문서 작성 완료 (Swagger/OpenAPI)
- [ ] 데이터베이스 ERD 및 스키마 정의 완료
- [ ] 보안 요구사항 문서화 완료
- [ ] 개발 환경 셋업 가이드 작성

### **Phase 2 완료 기준**
- [ ] 모든 테이블 및 인덱스 생성 완료
- [ ] 데이터 접근 계층 구현 및 테스트 완료
- [ ] 성능 벤치마크 기준 달성 (응답시간 < 50ms)
- [ ] 마이그레이션 스크립트 검증 완료

### **Phase 3 완료 기준**
- [ ] 모든 핵심 API 엔드포인트 구현 완료
- [ ] API 응답 시간 목표 달성 (< 200ms)
- [ ] 단위 테스트 커버리지 90% 이상
- [ ] API 문서 업데이트 및 검증 완료

### **Phase 4 완료 기준**
- [ ] 콘텐츠 필터링 정확도 95% 이상
- [ ] 보안 테스트 모든 항목 통과
- [ ] 침입 탐지 및 로깅 시스템 동작 확인
- [ ] 보안 정책 문서화 완료

### **Phase 5 완료 기준**
- [ ] Live2D 감정 동기화 정확도 95% 이상
- [ ] 모션 트리거 지연시간 < 100ms
- [ ] 메모리 사용량 최적화 목표 달성
- [ ] 크로스 브라우저 호환성 확인

### **Phase 6 완료 기준**
- [ ] 성능 목표 달성 (응답시간, 메모리, CPU)
- [ ] 모니터링 대시보드 구축 완료
- [ ] 알림 시스템 동작 검증 완료
- [ ] 성능 최적화 문서화 완료

### **Phase 7 완료 기준 (Live2D 캐릭터 동작 시스템)**
- [ ] Live2D 모델 로딩 및 메타데이터 파싱 정확도 100%
- [ ] 감정 기반 표정/모션 동기화 정확도 95% 이상
- [ ] WebSocket 실시간 동기화 지연시간 < 100ms
- [ ] 크로스 브라우저 호환성 확인 (Chrome, Firefox, Safari, Edge)

### **Phase 8 완료 기준 (TTS Live2D 음성 시스템)**
- [ ] **다중 TTS 제공자 시스템**: 최소 4개 제공자 지원 (Edge TTS, SiliconFlow, Azure, OpenAI)
- [ ] **무료 우선 Fallback**: Edge TTS → SiliconFlow → 유료 제공자 순 자동 전환
- [ ] **립싱크 동기화**: 음성-립싱크 정확도 90% 이상 (무료 제공자 기준)
- [ ] **사용자 선택 시스템**: TTS 제공자/음성 선택 및 테스트 기능 완료
- [ ] **실시간 성능**: TTS 스트리밍 지연시간 < 200ms (무료 제공자 기준)

### **Phase 9 완료 기준 (LLM Live2D 대화 시스템)**
- [ ] **다중 LLM 제공자 시스템**: 최소 5개 제공자 지원 (Cerebras, Groq, Gemini, DeepSeek, Ollama)
- [ ] **무료 우선 Fallback**: Cerebras → Groq → Gemini → 저비용 제공자 순
- [ ] **응답 생성 속도**: Cerebras/Groq 1초 이하, 기타 3초 이하
- [ ] **사용자 선택 시스템**: LLM 제공자/모델 선택 및 테스트 기능 완료
- [ ] **컨텍스트 관리**: 대화 컨텍스트 유지 정확도 95% 이상
- [ ] **비용 추적**: API 사용량 및 비용 추적 시스템 완료

### **Phase 10 완료 기준 (통합 테스트 & 품질 보증)**
- [ ] 전체 Live2D 시스템 통합 테스트 통과
- [ ] TTS-Live2D-LLM 파이프라인 성능 목표 달성
- [ ] 보안 검증 테스트 모든 항목 통과
- [ ] 사용성 및 UX 테스트 기준 충족

### **Phase 11 완료 기준 (배포 & 운영 준비)**
- [ ] 프로덕션 배포 성공 및 안정성 확인
- [ ] 모니터링 시스템 정상 동작 확인
- [ ] 장애 대응 매뉴얼 검증 완료
- [ ] 운영 문서 전체 업데이트 완료

---

## 🔄 **지속적 개선 계획**

### **단기 개선 (1-3개월) - Live2D 시스템 고도화**
- Live2D 캐릭터 표정/모션 다양성 확대 (20+ 표정, 50+ 모션)
- 감정 인식 정확도 개선 (키워드 패턴 확장, ML 기반 분석 도입)
- TTS 립싱크 정확도 향상 (주파수 분석 알고리즘 최적화)
- 실시간 성능 최적화 (WebSocket 지연시간 단축, 애니메이션 최적화)

### **중기 개선 (3-6개월) - 인터랙티브 기능 확장**
- 다중 캐릭터 시스템 지원 (캐릭터 선택, 개성별 차별화)
- 고급 제스처 및 상호작용 시스템 (터치/클릭 반응, 시선 추적)
- 음성 인식 (STT) 통합 (음성으로 캐릭터와 대화)
- 감정 기반 배경/환경 변화 시스템

### **장기 개선 (6-12개월) - AI 고도화 및 확장**
- 머신러닝 기반 개인화 대화 시스템 (사용자 취향 학습)
- 실시간 감정 분석 및 반응 시스템 (카메라 기반 표정 인식)
- 3D Live2D 모델 지원 (WebGL 기반 3D 렌더링)
- 다국어 TTS 및 다문화 캐릭터 개성 지원

---

> **🎯 Live2D 시스템 핵심 성공 지표**
> - **실시간 성능**: WebSocket 지연시간 < 100ms, Live2D 렌더링 60fps
> - **동기화 정확도**: 감정-표정 매핑 95%, TTS-립싱크 90% 이상
> - **사용자 경험**: 캐릭터 반응 자연스러움 4.5/5.0, 대화 만족도 4.3/5.0
> - **기술적 안정성**: 시스템 가용률 99.5%, 동시 대화 세션 50개 지원
> - **확장성**: 다중 Live2D 모델 지원, 캐릭터별 개성 차별화 완료

---

> **📚 구현 참고 자료**
> - **Reference 코드 분석**: `/reference/markdown/Live2D_Code_Analysis.md`
> - **프론트엔드 통합 가이드**: `/reference/markdown/Live2D_Frontend_Integration.md`
> - **Live2D 모델 구조**: `/reference/live2d-models/mao_pro/runtime/mao_pro.model3.json`
> - **감정 매핑 시스템**: `/reference/model_dict.json`
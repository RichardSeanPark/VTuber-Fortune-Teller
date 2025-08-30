# Frontend Structure Analysis

## 1. 프로젝트 구조 개요

### 전체 디렉토리 구조
```
reference/Open-LLM-VTuber/
├── frontend/                    # 메인 프론트엔드 애플리케이션
│   ├── assets/                 # 빌드된 정적 자산
│   │   ├── main-Iq8WL0Kv.js   # 메인 JavaScript 번들 (Vite 빌드)
│   │   └── main-QEkl09-0.css  # 스타일시트 번들
│   ├── libs/                   # Live2D 및 외부 라이브러리
│   │   ├── live2d.min.js      # Live2D Web SDK
│   │   ├── live2dcubismcore.js # Live2D Cubism Core
│   │   └── vad.worklet.bundle.min.js # Voice Activity Detection
│   ├── favicon.ico
│   └── index.html             # 애플리케이션 진입점
├── web_tool/                   # 웹 도구 (ASR/TTS 테스트)
│   ├── index.html             # 웹 도구 UI
│   ├── main.js                # 웹 도구 로직
│   └── recorder.js            # 오디오 녹음 기능
├── live2d-models/             # Live2D 모델 리소스
│   ├── mao_pro/               # 모델 폴더
│   ├── shizuku/
│   └── tuzi_mian/
└── src/open_llm_vtuber/       # 백엔드 Python 코드
    ├── routes.py              # FastAPI 라우트
    ├── websocket_handler.py   # WebSocket 통신 처리
    └── live2d_model.py        # Live2D 모델 관리
```

### 주요 파일들의 역할과 위치

1. **프론트엔드 진입점**: `/frontend/index.html`
   - 단순한 HTML5 애플리케이션 셸
   - Vite로 빌드된 번들 파일 로드

2. **메인 애플리케이션**: `/frontend/assets/main-Iq8WL0Kv.js`
   - React 기반 SPA (Single Page Application)
   - Live2D 렌더링 및 WebSocket 통신 로직

3. **Live2D 라이브러리**: `/frontend/libs/`
   - Live2D Cubism SDK for Web
   - WebGL 기반 렌더링 엔진

4. **웹 도구**: `/web_tool/`
   - 독립적인 ASR/TTS 테스트 도구
   - Vanilla JavaScript로 구현

## 2. Live2D 통합 구조

### Live2D 모델 로딩 및 렌더링 시스템

#### 모델 구조 분석 (mao_pro.model3.json 기준)
```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "mao_pro.moc3",                    // 모델 바이너리
    "Textures": ["mao_pro.4096/texture_00.png"], // 텍스처 파일
    "Physics": "mao_pro.physics3.json",        // 물리 시뮬레이션
    "Pose": "mao_pro.pose3.json",             // 포즈 정의
    "DisplayInfo": "mao_pro.cdi3.json",       // 표시 정보
    "Expressions": [...],                      // 표정 애니메이션
    "Motions": {                              // 모션 애니메이션
      "Idle": [...],
      "": [...]  // 기본 모션들
    }
  },
  "Groups": [                                 // 파라미터 그룹
    {
      "Target": "Parameter",
      "Name": "EyeBlink",
      "Ids": ["ParamEyeLOpen", "ParamEyeROpen"]
    },
    {
      "Target": "Parameter", 
      "Name": "LipSync",
      "Ids": ["ParamA"]
    }
  ],
  "HitAreas": [                              // 클릭 가능 영역
    {"Id": "HitAreaHead", "Name": ""},
    {"Id": "HitAreaBody", "Name": ""}
  ]
}
```

#### Live2D 모델 관리 클래스 (live2d_model.py)
```python
class Live2dModel:
    """Live2D 모델 정보 관리 클래스"""
    
    def __init__(self, live2d_model_name: str, model_dict_path: str = "model_dict.json"):
        self.model_dict_path = model_dict_path
        self.live2d_model_name = live2d_model_name
        self.set_model(live2d_model_name)
    
    def set_model(self, model_name: str) -> None:
        """모델 정보 초기화 및 감정 맵핑 설정"""
        self.model_info = self._lookup_model_info(model_name)
        self.emo_map = {
            k.lower(): v for k, v in self.model_info["emotionMap"].items()
        }
        self.emo_str = " ".join([f"[{key}]," for key in self.emo_map.keys()])
    
    def extract_emotion(self, str_to_check: str) -> list:
        """텍스트에서 감정 키워드 추출"""
        expression_list = []
        str_to_check = str_to_check.lower()
        
        for key in self.emo_map.keys():
            emo_tag = f"[{key}]"
            if emo_tag in str_to_check:
                expression_list.append(self.emo_map[key])
        
        return expression_list
```

### 애니메이션 제어 구조

#### 표정 제어 시스템
- **표정 파일**: `/expressions/exp_*.exp3.json` - 8개의 기본 표정
- **감정 맵핑**: 텍스트 키워드 → 표정 인덱스 변환
- **실시간 제어**: WebSocket을 통한 표정 변경 명령

#### 모션 제어 시스템
- **Idle 모션**: 기본 대기 애니메이션
- **특수 모션**: 6개의 추가 모션 (mtn_02~04, special_01~03)
- **물리 시뮬레이션**: 자연스러운 움직임을 위한 물리 엔진

### 인터랙션 처리 방식

#### 클릭 인터랙션
```json
"HitAreas": [
  {"Id": "HitAreaHead", "Name": ""},  // 머리 클릭 영역
  {"Id": "HitAreaBody", "Name": ""}   // 몸체 클릭 영역
]
```

#### 음성 동기화 (Lip Sync)
```json
"Groups": [
  {
    "Target": "Parameter",
    "Name": "LipSync", 
    "Ids": ["ParamA"]  // 입 모양 파라미터
  }
]
```

## 3. 컴포넌트 아키텍처

### React 기반 아키텍처 (추정)
메인 번들 파일 분석을 통해 다음과 같은 구조로 추정됩니다:

#### 주요 컴포넌트
1. **Live2D Canvas Component**
   - WebGL 렌더링 컨텍스트 관리
   - Live2D 모델 렌더링 루프
   - 인터랙션 이벤트 처리

2. **Chat Interface Component**
   - 사용자 입력 처리
   - 채팅 히스토리 표시
   - WebSocket 통신 관리

3. **Audio Controller Component**
   - 마이크 입력 처리
   - 음성 재생 제어
   - VAD (Voice Activity Detection) 통합

### 상태 관리 패턴

#### WebSocket 기반 실시간 상태 동기화
```javascript
// WebSocket 연결 및 메시지 처리 (routes.py에서 확인된 패턴)
const messageTypes = {
  GROUP: ["add-client-to-group", "remove-client-from-group"],
  HISTORY: ["fetch-history-list", "fetch-and-set-history"],
  CONVERSATION: ["mic-audio-end", "text-input", "ai-speak-signal"],
  CONFIG: ["fetch-configs", "switch-config"],
  CONTROL: ["interrupt-signal", "audio-play-start"],
  DATA: ["mic-audio-data"]
};
```

#### 클라이언트 상태 관리 (websocket_handler.py 기반)
```python
class WebSocketHandler:
    def __init__(self, default_context_cache: ServiceContext):
        self.client_connections: Dict[str, WebSocket] = {}
        self.client_contexts: Dict[str, ServiceContext] = {}
        self.chat_group_manager = ChatGroupManager()
        self.current_conversation_tasks: Dict[str, Optional[asyncio.Task]] = {}
        self.received_data_buffers: Dict[str, np.ndarray] = {}
```

### 프롭스 및 이벤트 흐름

#### 이벤트 흐름도
```
User Input → WebSocket Message → Backend Processing → Live2D Animation
    ↓               ↓                    ↓                   ↓
Microphone → Audio Processing → ASR → LLM Response → TTS → Audio Output
```

## 4. UI/UX 디자인 패턴

### 레이아웃 구조

#### 메인 애플리케이션 레이아웃
- **중앙 Live2D 캔버스**: 전체 화면 또는 주요 영역
- **채팅 인터페이스**: 하단 또는 사이드바
- **컨트롤 패널**: 설정 및 상태 표시

#### 웹 도구 레이아웃 (web_tool/index.html)
```css
.section {
    margin-bottom: 30px;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 8px;
    background-color: #f9f9f9;
}

.controls {
    display: flex;
    gap: 20px;
    margin-bottom: 15px;
}
```

### 스타일링 방식

#### CSS 모듈 방식 (추정)
- Vite 번들링을 통한 CSS 최적화
- 컴포넌트별 스타일 격리
- 반응형 디자인 지원

#### 디자인 시스템
- **색상 팔레트**: 주로 파란색 계열 (#007bff, #0056b3)
- **타이포그래피**: Arial, sans-serif 기본
- **간격 체계**: 일관된 margin/padding 사용

### 반응형 디자인 구현

#### 미디어 쿼리 활용
```css
@media (max-width: 768px) {
    .controls {
        flex-direction: column;
        gap: 10px;
    }
}
```

#### 모바일 최적화
- 터치 인터랙션 지원
- 화면 크기별 레이아웃 조정
- 마이크 권한 처리

## 5. 데이터 플로우

### API 통신 구조

#### FastAPI 라우트 구조 (routes.py)
```python
# WebSocket 엔드포인트
@router.websocket("/client-ws")
async def websocket_endpoint(websocket: WebSocket)

# ASR 엔드포인트
@router.post("/asr") 
async def transcribe_audio(file: UploadFile = File(...))

# TTS WebSocket
@router.websocket("/tts-ws")
async def tts_endpoint(websocket: WebSocket)

# Live2D 모델 정보
@router.get("/live2d-models/info")
async def get_live2d_folder_info()
```

### 데이터 바인딩 패턴

#### 실시간 데이터 바인딩
```javascript
// WebSocket 메시지 처리 패턴 (main.js에서 확인)
ws.onmessage = async (event) => {
    const response = JSON.parse(event.data);
    
    switch(response.status) {
        case 'partial':
            // 부분 오디오 데이터 처리
            break;
        case 'complete':
            // 완성된 오디오 결합
            break;
        case 'error':
            // 에러 처리
            break;
    }
};
```

#### 오디오 데이터 처리
```javascript
// 오디오 버퍼 처리 (recorder.js)
class AudioRecorder {
    async createWAV(audioBuffer) {
        const numChannels = 1;      // 모노
        const sampleRate = 16000;   // 16kHz
        const format = 1;           // PCM
        const bitDepth = 16;        // 16비트
        
        // WAV 헤더 생성 및 데이터 변환
        // ...
    }
}
```

### 에러 핸들링

#### 단계별 에러 처리
```javascript
// 1. 연결 에러
ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    // 재연결 로직
};

// 2. 오디오 처리 에러
catch (error) {
    asrStatus.textContent = 'Error: ' + error.message;
    asrStatus.className = 'status error';
}

// 3. Live2D 렌더링 에러 (추정)
// WebGL 컨텍스트 복구 로직
```

## 6. 성능 최적화

### 번들링 구조

#### Vite 기반 빌드 시스템
- **코드 스플리팅**: 동적 import 활용
- **트리 셰이킹**: 미사용 코드 제거
- **CSS 최적화**: 중복 제거 및 압축

#### 에셋 최적화
- **Live2D 모델**: .moc3 바이너리 형식으로 최적화
- **텍스처**: 4096x4096 최적화된 텍스처
- **오디오**: WAV 16kHz 모노 형식

### 코드 스플리팅

#### 라이브러리 분리
```
libs/
├── live2d.min.js           # Live2D SDK (별도 로드)
├── live2dcubismcore.js     # Core 엔진 (별도 로드)
└── vad.worklet.bundle.min.js # VAD 워커 (별도 로드)
```

### 메모리 관리

#### Live2D 리소스 관리
```python
# Python 백엔드에서의 메모리 관리
async def handle_disconnect(self, client_uid: str):
    # 컨텍스트 정리
    context = self.client_contexts.get(client_uid)
    if context:
        await context.close()
    
    # 버퍼 정리
    self.received_data_buffers.pop(client_uid, None)
```

#### 오디오 버퍼 관리
```javascript
// 오디오 리소스 정리 (main.js)
window.addEventListener('beforeunload', () => {
    if (audioContext) {
        audioContext.close();
    }
    if (currentAudioPath) {
        URL.revokeObjectURL(currentAudioPath);
    }
    audioBuffers = [];
    pendingAudioPaths.clear();
});
```

## 7. 핵심 기능별 구현 분석

### 7.1 Live2D 캐릭터 렌더링

#### 구현 방식
- **WebGL 기반**: Live2D Cubism SDK for Web 사용
- **실시간 렌더링**: 60fps 타겟 렌더링 루프
- **하드웨어 가속**: GPU 기반 텍스처 렌더링

#### 코드 패턴 (추정)
```javascript
// Live2D 모델 초기화
class Live2DManager {
    async initModel(modelPath) {
        // 1. 모델 로드
        const model = await Live2DCubismUserModel.loadModel(modelPath);
        
        // 2. WebGL 컨텍스트 설정
        const gl = canvas.getContext('webgl');
        
        // 3. 렌더링 루프 시작
        this.startRenderLoop();
    }
    
    updateAnimation(deltaTime) {
        // 물리 시뮬레이션 업데이트
        model.physics.evaluate(deltaTime);
        
        // 표정 업데이트
        model.setExpression(currentExpression);
        
        // 렌더링
        model.draw();
    }
}
```

### 7.2 음성 인식 (ASR) 시스템

#### 구현 구조
```javascript
// 음성 녹음 및 처리 (recorder.js)
class AudioRecorder {
    async start() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,    // 모노
                sampleRate: 16000   // 16kHz
            }
        });
        
        this.mediaRecorder = new MediaRecorder(stream);
        this.mediaRecorder.start();
    }
    
    async stop() {
        // WAV 형식으로 변환
        const wavBlob = await this.createWAV(audioBuffer);
        return wavBlob;
    }
}
```

#### 서버 처리 (routes.py)
```python
@router.post("/asr")
async def transcribe_audio(file: UploadFile = File(...)):
    contents = await file.read()
    
    # WAV 헤더 검증
    if len(contents) < 44:
        raise ValueError("Invalid WAV file")
    
    # 오디오 데이터 추출
    audio_data = contents[44:]  # WAV 헤더 스킵
    audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
    
    # ASR 엔진으로 변환
    text = await default_context_cache.asr_engine.async_transcribe_np(audio_array)
    return {"text": text}
```

### 7.3 텍스트 음성 변환 (TTS) 시스템

#### WebSocket 기반 스트리밍 TTS
```python
@router.websocket("/tts-ws")
async def tts_endpoint(websocket: WebSocket):
    while True:
        data = await websocket.receive_json()
        text = data.get("text")
        
        # 문장 단위로 분할
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        
        for sentence in sentences:
            # 오디오 생성
            audio_path = await tts_engine.async_generate_audio(
                text=sentence, 
                file_name_no_ext=file_name
            )
            
            # 부분 결과 전송
            await websocket.send_json({
                "status": "partial",
                "audioPath": audio_path,
                "text": sentence
            })
        
        # 완료 신호
        await websocket.send_json({"status": "complete"})
```

#### 클라이언트 오디오 결합 (main.js)
```javascript
// 여러 오디오 청크를 하나로 결합
const combinedBuffer = audioContext.createBuffer(1, totalLength, 16000);
let offset = 0;

for (const buffer of audioBuffers) {
    let channelData = buffer.getChannelData(0);
    
    // 리샘플링 (필요시)
    if (buffer.sampleRate !== 16000) {
        channelData = await resampleAudio(channelData, buffer.sampleRate, 16000);
    }
    
    combinedBuffer.copyToChannel(channelData, 0, offset);
    offset += channelData.length;
}
```

### 7.4 실시간 통신 시스템

#### WebSocket 핸들러 구조 (websocket_handler.py)
```python
class WebSocketHandler:
    def __init__(self, default_context_cache: ServiceContext):
        self.client_connections: Dict[str, WebSocket] = {}
        self.client_contexts: Dict[str, ServiceContext] = {}
        self.chat_group_manager = ChatGroupManager()
        
        # 메시지 핸들러 매핑
        self._message_handlers = {
            "mic-audio-data": self._handle_audio_data,
            "text-input": self._handle_conversation_trigger,
            "interrupt-signal": self._handle_interrupt,
            "fetch-configs": self._handle_fetch_configs,
            # ...
        }
    
    async def _route_message(self, websocket: WebSocket, client_uid: str, data: dict):
        msg_type = data.get("type")
        handler = self._message_handlers.get(msg_type)
        
        if handler:
            await handler(websocket, client_uid, data)
```

### 7.5 그룹 채팅 시스템

#### 다중 사용자 지원
```python
class ChatGroupManager:
    def __init__(self):
        self.groups: Dict[str, ChatGroup] = {}
        self.client_group_map: Dict[str, str] = {}
    
    async def add_client_to_group(self, inviter_uid: str, invitee_uid: str):
        # 그룹 생성 또는 참가
        group = self._get_or_create_group(inviter_uid)
        group.add_member(invitee_uid)
        
        # 그룹 상태 브로드캐스트
        await self._broadcast_group_update(group)
```

#### 그룹 인터랙션 처리
```python
async def handle_group_interrupt(group_id: str, heard_response: str, **kwargs):
    group = chat_group_manager.get_group(group_id)
    
    # 모든 그룹 멤버의 대화 중단
    for member_uid in group.members:
        task = current_conversation_tasks.get(member_uid)
        if task and not task.done():
            task.cancel()
    
    # 중단 메시지 브로드캐스트
    await broadcast_to_group(group.members, {
        "type": "conversation-interrupted",
        "heard_response": heard_response
    })
```

### 7.6 설정 관리 시스템

#### 동적 캐릭터 전환
```python
async def _handle_config_switch(self, websocket: WebSocket, client_uid: str, data: dict):
    config_file_name = data.get("file")
    context = self.client_contexts[client_uid]
    
    # 새 설정으로 컨텍스트 업데이트
    await context.handle_config_switch(websocket, config_file_name)
    
    # 클라이언트에 새 모델 정보 전송
    await websocket.send_text(json.dumps({
        "type": "set-model-and-conf",
        "model_info": context.live2d_model.model_info,
        "conf_name": context.character_config.conf_name
    }))
```

### 7.7 음성 활동 감지 (VAD)

#### 실시간 VAD 처리
```python
async def _handle_raw_audio_data(self, websocket: WebSocket, client_uid: str, data: dict):
    context = self.client_contexts[client_uid]
    chunk = data.get("audio", [])
    
    if chunk:
        for audio_bytes in context.vad_engine.detect_speech(chunk):
            if audio_bytes == b"<|PAUSE|>":
                # 음성 중단 감지
                await websocket.send_text(json.dumps({
                    "type": "control", 
                    "text": "interrupt"
                }))
            elif len(audio_bytes) > 1024:
                # 음성 활동 감지
                self.received_data_buffers[client_uid] = np.append(
                    self.received_data_buffers[client_uid],
                    np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
                )
```

## 8. 향후 Live2D 기반 운세 앱 개발 활용 방안

### 8.1 아키텍처 적용 방안

#### 기본 구조 재사용
1. **WebSocket 통신 시스템**: 실시간 인터랙션에 활용
2. **Live2D 렌더링 엔진**: 운세 캐릭터 애니메이션
3. **음성 인식/합성**: 음성 기반 운세 상담
4. **모듈화된 컴포넌트**: 운세 기능별 컴포넌트 확장

#### 운세 앱 특화 확장
```javascript
// 운세 전용 Live2D 컨트롤러
class FortuneCharacterController extends Live2DManager {
    constructor() {
        super();
        this.fortuneExpressions = {
            'reading': 'exp_01',      // 운세 읽는 표정
            'thinking': 'exp_02',     // 고민하는 표정
            'happy': 'exp_03',        // 좋은 운세 표정
            'concerned': 'exp_04',    // 걱정되는 운세 표정
            'mysterious': 'exp_05'    // 신비로운 표정
        };
    }
    
    async performFortuneReading(fortuneType) {
        // 1. 카드 뽑기 애니메이션
        await this.playMotion('card_draw');
        
        // 2. 운세 읽기 표정
        this.setExpression(this.fortuneExpressions.reading);
        
        // 3. 결과에 따른 표정 변화
        const result = await this.getFortune(fortuneType);
        this.setExpressionByResult(result);
    }
}
```

### 8.2 핵심 기능 구현 가이드

#### 1. 운세 카드 시스템
```python
# 백엔드 운세 API
@router.post("/fortune/draw")
async def draw_fortune_card(request: FortuneRequest):
    card_type = request.type  # 'love', 'career', 'health', 'daily'
    
    # 운세 생성 로직
    fortune_data = fortune_engine.generate_fortune(card_type)
    
    # Live2D 애니메이션 커맨드 포함
    return {
        "fortune": fortune_data,
        "animation": {
            "type": "card_reveal",
            "expression": fortune_data.emotion,
            "duration": 3000
        }
    }
```

#### 2. 감정 기반 애니메이션 시스템
```python
# 운세 결과에 따른 감정 맵핑
class FortuneEmotionMapper:
    def __init__(self):
        self.emotion_map = {
            'excellent': 'exp_happy',
            'good': 'exp_smile', 
            'neutral': 'exp_normal',
            'caution': 'exp_concerned',
            'warning': 'exp_worried'
        }
    
    def get_expression_for_fortune(self, fortune_score):
        if fortune_score >= 80:
            return self.emotion_map['excellent']
        elif fortune_score >= 60:
            return self.emotion_map['good']
        # ...
```

#### 3. 인터랙티브 UI 컴포넌트
```javascript
// 운세 카드 선택 컴포넌트
class FortuneCardSelector {
    constructor(live2dController) {
        this.controller = live2dController;
        this.cards = ['love', 'career', 'health', 'daily'];
    }
    
    async selectCard(cardType) {
        // 1. 카드 선택 피드백
        await this.controller.setExpression('thinking');
        
        // 2. 카드 뽑기 애니메이션
        await this.controller.playMotion('card_select');
        
        // 3. 서버에 운세 요청
        const fortune = await this.requestFortune(cardType);
        
        // 4. 결과 표시
        await this.displayFortune(fortune);
    }
}
```

#### 4. 음성 상호작용 시스템
```javascript
// 음성 기반 운세 상담
class VoiceFortuneConsultation {
    constructor(asrEngine, ttsEngine, live2dController) {
        this.asr = asrEngine;
        this.tts = ttsEngine;
        this.controller = live2dController;
    }
    
    async startConsultation() {
        // 1. 인사 및 운세 타입 질문
        await this.speak("안녕하세요! 어떤 운세를 봐드릴까요?");
        await this.controller.setExpression('greeting');
        
        // 2. 사용자 음성 입력 대기
        const userInput = await this.listenForResponse();
        
        // 3. 운세 타입 파싱 및 처리
        const fortuneType = this.parseFortuneType(userInput);
        await this.performFortuneTelling(fortuneType);
    }
}
```

### 8.3 성능 최적화 전략

#### 1. Live2D 모델 최적화
```javascript
// 운세 앱용 경량화 전략
class OptimizedLive2DLoader {
    constructor() {
        this.modelCache = new Map();
        this.textureCache = new Map();
    }
    
    async loadFortuneCharacter(characterId) {
        // 1. 모델 사전 로딩
        if (!this.modelCache.has(characterId)) {
            const model = await this.loadOptimizedModel(characterId);
            this.modelCache.set(characterId, model);
        }
        
        // 2. 텍스처 스트리밍
        await this.streamTextures(characterId);
        
        return this.modelCache.get(characterId);
    }
    
    // 운세 타입별 필요한 애니메이션만 로드
    async preloadAnimations(fortuneType) {
        const requiredAnimations = this.getRequiredAnimations(fortuneType);
        await Promise.all(requiredAnimations.map(anim => this.loadAnimation(anim)));
    }
}
```

#### 2. 메모리 관리 최적화
```javascript
// 자원 관리 시스템
class FortuneAppResourceManager {
    constructor() {
        this.activeModels = new Set();
        this.audioBuffers = new Map();
        this.maxCacheSize = 50; // MB
    }
    
    async cleanupUnusedResources() {
        // 1. 비활성 모델 정리
        this.activeModels.forEach(model => {
            if (!model.isActive()) {
                model.dispose();
                this.activeModels.delete(model);
            }
        });
        
        // 2. 오디오 버퍼 정리
        this.cleanupAudioBuffers();
        
        // 3. 텍스처 캐시 정리
        this.cleanupTextureCache();
    }
}
```

### 8.4 확장 가능한 구조 설계

#### 1. 플러그인 시스템
```python
# 운세 플러그인 인터페이스
class FortunePlugin(ABC):
    @abstractmethod
    async def generate_fortune(self, user_data: dict) -> FortuneResult:
        pass
    
    @abstractmethod
    def get_required_animations(self) -> List[str]:
        pass

# 타로 카드 플러그인
class TarotPlugin(FortunePlugin):
    async def generate_fortune(self, user_data: dict) -> FortuneResult:
        card = self.draw_tarot_card()
        interpretation = self.interpret_card(card, user_data)
        
        return FortuneResult(
            type='tarot',
            content=interpretation,
            animations=['card_reveal', 'mystical_glow'],
            emotion=self.get_emotion_for_card(card)
        )
```

#### 2. 모듈화된 컴포넌트 구조
```javascript
// 운세 앱 메인 컨트롤러
class FortuneApp {
    constructor() {
        this.modules = {
            live2d: new Live2DModule(),
            fortune: new FortuneModule(),
            audio: new AudioModule(),
            ui: new UIModule()
        };
    }
    
    async initialize() {
        // 모듈별 초기화
        await Promise.all([
            this.modules.live2d.init(),
            this.modules.fortune.init(),
            this.modules.audio.init(),
            this.modules.ui.init()
        ]);
        
        // 모듈 간 이벤트 연결
        this.setupModuleConnections();
    }
    
    setupModuleConnections() {
        // 운세 결과 → Live2D 애니메이션
        this.modules.fortune.on('fortuneGenerated', (result) => {
            this.modules.live2d.playFortuneAnimation(result);
        });
        
        // 음성 입력 → 운세 생성
        this.modules.audio.on('speechRecognized', (text) => {
            this.modules.fortune.processUserInput(text);
        });
    }
}
```

이러한 구조를 기반으로 Live2D 기반 운세 앱을 개발하면, 기존 VTuber 시스템의 안정성과 성능을 활용하면서도 운세 앱에 특화된 기능을 효과적으로 구현할 수 있습니다.
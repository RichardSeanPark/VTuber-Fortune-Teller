# Live2D VTuber System 코드 분석 보고서

## 📋 개요

이 문서는 Open-LLM-VTuber 프로젝트의 Live2D 관련 코드를 상세히 분석하고, 캐릭터 실행 메커니즘과 동작 방식을 설명합니다. 분석된 내용은 Fortune VTuber 프로젝트 구현에 직접 참고할 수 있도록 구성되었습니다.

## 🏗️ 시스템 아키텍처

### 전체 구조도

```
Frontend (React + Live2D)
        ↓ WebSocket
Backend (FastAPI + Python)
        ↓
Service Context Manager
        ↓
├── Live2D Model Manager
├── WebSocket Handler  
├── Conversation Handler
├── TTS Integration
└── Agent System
```

## 📁 핵심 파일 구조

```
reference/
├── src/open_llm_vtuber/
│   ├── live2d_model.py          # Live2D 모델 관리 핵심 클래스
│   ├── websocket_handler.py     # WebSocket 통신 처리
│   ├── server.py               # FastAPI 서버 설정
│   ├── routes.py               # API 라우팅
│   └── service_context.py      # 서비스 컨텍스트 관리
├── live2d-models/              # Live2D 모델 파일들
│   └── mao_pro/
│       └── runtime/
│           ├── mao_pro.model3.json  # 모델 메타데이터
│           ├── mao_pro.moc3         # 모델 바이너리
│           ├── expressions/         # 표정 파일들
│           └── motions/             # 모션 파일들
├── frontend/
│   └── libs/
│       ├── live2d.min.js       # Live2D JavaScript SDK
│       └── live2dcubismcore.js # Live2D 코어 엔진
├── model_dict.json             # 모델 설정 사전
└── prompts/utils/
    └── live2d_expression_prompt.txt  # 표정 프롬프트
```

## 🎭 Live2D 모델 관리 시스템

### 1. Live2dModel 클래스 (`live2d_model.py`)

**핵심 역할**: Live2D 모델의 메타데이터 관리 및 감정 매핑 처리

```python
class Live2dModel:
    """Live2D 모델 정보를 관리하는 핵심 클래스"""
    
    def __init__(self, live2d_model_name: str, model_dict_path: str = "model_dict.json"):
        self.model_dict_path: str = model_dict_path
        self.live2d_model_name: str = live2d_model_name
        self.set_model(live2d_model_name)
```

**주요 기능**:

#### A. 모델 정보 로딩
```python
def _lookup_model_info(self, model_name: str) -> dict:
    """모델 딕셔너리에서 모델 정보를 조회"""
    # model_dict.json에서 모델 정보 로드
    # 모델명으로 검색하여 매칭되는 모델 정보 반환
```

#### B. 감정 매핑 시스템
```python
# model_dict.json의 감정 매핑 예시
"emotionMap": {
    "neutral": 0,    # 중립 → 표정 인덱스 0
    "anger": 2,      # 분노 → 표정 인덱스 2  
    "disgust": 2,    # 혐오 → 표정 인덱스 2
    "fear": 1,       # 두려움 → 표정 인덱스 1
    "joy": 3,        # 기쁨 → 표정 인덱스 3
    "smirk": 3,      # 흐뭇함 → 표정 인덱스 3
    "sadness": 1,    # 슬픔 → 표정 인덱스 1  
    "surprise": 3    # 놀람 → 표정 인덱스 3
}
```

#### C. 텍스트에서 감정 추출
```python
def extract_emotion(self, str_to_check: str) -> list:
    """텍스트에서 [joy], [anger] 같은 감정 태그를 찾아 인덱스 리스트 반환"""
    expression_list = []
    # "[joy]" → 3, "[anger]" → 2 변환
    return expression_list
```

#### D. 감정 키워드 제거
```python
def remove_emotion_keywords(self, target_str: str) -> str:
    """텍스트에서 [감정] 태그를 제거하고 순수 텍스트만 반환"""
    # "안녕하세요! [joy] 만나서 반가워요!" → "안녕하세요! 만나서 반가워요!"
```

## 🌐 WebSocket 통신 시스템

### 1. WebSocket Handler (`websocket_handler.py`)

**역할**: 실시간 클라이언트-서버 통신 관리

#### A. 연결 관리
```python
class WebSocketHandler:
    def __init__(self, default_context_cache: ServiceContext):
        self.client_connections: Dict[str, WebSocket] = {}
        self.client_contexts: Dict[str, ServiceContext] = {}
        self.chat_group_manager = ChatGroupManager()
```

#### B. 메시지 타입 분류
```python
class MessageType(Enum):
    GROUP = ["add-client-to-group", "remove-client-from-group"]
    HISTORY = ["fetch-history-list", "create-new-history"]  
    CONVERSATION = ["mic-audio-end", "text-input", "ai-speak-signal"]
    CONFIG = ["fetch-configs", "switch-config"]
    CONTROL = ["interrupt-signal", "audio-play-start"]
    DATA = ["mic-audio-data"]
```

#### C. 핵심 메시지 처리 흐름

```python
async def handle_websocket_communication(self, websocket: WebSocket, client_uid: str):
    """WebSocket 메시지 수신 및 라우팅"""
    while True:
        message = await websocket.receive_text()
        data = json.loads(message)
        
        # 메시지 타입에 따른 처리기 호출
        handler = self._message_handlers.get(data["type"])
        if handler:
            await handler(websocket, client_uid, data)
```

### 2. 실시간 Live2D 업데이트 메커니즘

#### A. 감정 상태 전송
```python
# 클라이언트로 Live2D 표정 변경 신호 전송
await websocket.send_text(json.dumps({
    "type": "live2d_expression_update",
    "expression_index": 3,  # joy 표정
    "duration": 2000       # 2초간 유지
}))
```

#### B. 모션 트리거
```python  
# Live2D 모션 실행 신호
await websocket.send_text(json.dumps({
    "type": "live2d_motion_trigger", 
    "motion_group": "Idle",
    "motion_index": 0
}))
```

## 🎨 Live2D 모델 파일 구조

### 1. 모델 메타데이터 (`mao_pro.model3.json`)

```json
{
    "Version": 3,
    "FileReferences": {
        "Moc": "mao_pro.moc3",           // 모델 바이너리 파일
        "Textures": ["mao_pro.4096/texture_00.png"],  // 텍스처 파일들
        "Physics": "mao_pro.physics3.json",     // 물리 시뮬레이션
        "Pose": "mao_pro.pose3.json",          // 포즈 설정
        "Expressions": [                        // 표정 파일들
            {"Name": "exp_01", "File": "expressions/exp_01.exp3.json"},
            {"Name": "exp_02", "File": "expressions/exp_02.exp3.json"}
        ],
        "Motions": {                           // 모션 그룹들
            "Idle": [{"File": "motions/mtn_01.motion3.json"}],
            "": [{"File": "motions/mtn_02.motion3.json"}]
        }
    },
    "Groups": [                               // 파라미터 그룹
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
    "HitAreas": [                            // 클릭 가능 영역
        {"Id": "HitAreaHead", "Name": ""},
        {"Id": "HitAreaBody", "Name": ""}
    ]
}
```

### 2. 표정 시스템

- **표정 파일**: `expressions/exp_01.exp3.json` ~ `exp_08.exp3.json`
- **매핑**: `model_dict.json`의 emotionMap으로 감정→표정인덱스 연결
- **사용법**: `[joy]` 태그 → 인덱스 3 → `exp_04.exp3.json` 실행

### 3. 모션 시스템  

- **Idle 모션**: 기본 대기 상태 모션
- **인터랙티브 모션**: 사용자 클릭 시 실행되는 특수 모션
- **HitArea**: 클릭 가능한 영역 정의 (머리, 몸)

## 🔄 캐릭터 실행 워크플로우

### 1. 시스템 초기화 단계

```python
# 1. 서버 시작 시
app = FastAPI(title="Open-LLM-VTuber Server")

# 2. 서비스 컨텍스트 생성
default_context_cache = ServiceContext()
await default_context_cache.initialize(config)

# 3. Live2D 모델 로드
live2d_model = Live2dModel("mao_pro", "model_dict.json")

# 4. WebSocket 핸들러 초기화
ws_handler = WebSocketHandler(default_context_cache)
```

### 2. 클라이언트 연결 단계

```python
@router.websocket("/client-ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_uid = str(uuid4())
    
    # 새 연결 처리
    await ws_handler.handle_new_connection(websocket, client_uid)
    
    # 통신 루프 시작
    await ws_handler.handle_websocket_communication(websocket, client_uid)
```

### 3. 대화 처리 워크플로우

#### A. 사용자 입력 → AI 응답 → Live2D 반영

```python
# 1. 사용자 텍스트 입력 수신
{
    "type": "text-input",
    "text": "안녕하세요! 오늘 기분이 좋아요."
}

# 2. AI 에이전트가 응답 생성 (감정 태그 포함)
ai_response = "안녕하세요! [joy] 저도 기분이 좋네요! [surprise]"

# 3. Live2D 모델에서 감정 추출
emotions = live2d_model.extract_emotion(ai_response)  # [3, 3]
clean_text = live2d_model.remove_emotion_keywords(ai_response)

# 4. 클라이언트에 전송
await websocket.send_text(json.dumps({
    "type": "ai-response",
    "text": clean_text,
    "expressions": emotions,
    "audio_data": tts_audio
}))
```

#### B. 음성 입력 처리

```python  
# 1. 음성 데이터 수신
{
    "type": "mic-audio-data", 
    "audio": [0.1, 0.2, -0.1, ...]  # 오디오 배열
}

# 2. ASR로 음성→텍스트 변환
text = await asr.transcribe(audio_data)

# 3. 위의 텍스트 입력 워크플로우와 동일하게 처리
```

### 4. Live2D 프론트엔드 연동

#### A. JavaScript SDK 사용

```javascript
// Live2D 모델 로드
const model = await Live2DModel.loadModel("/live2d-models/mao_pro/runtime/mao_pro.model3.json");

// WebSocket으로 표정 업데이트 수신
websocket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === "ai-response") {
        // 표정 변경
        data.expressions.forEach(expIndex => {
            model.setExpression(expIndex);
        });
        
        // TTS 재생과 립싱크
        playAudioWithLipSync(data.audio_data);
    }
};
```

## ⚙️ 설정 시스템

### 1. 모델 설정 (`model_dict.json`)

```json
[
    {
        "name": "mao_pro",                    // 모델 이름
        "description": "",                    // 설명
        "url": "/live2d-models/mao_pro/runtime/mao_pro.model3.json",  // 모델 파일 경로
        "kScale": 0.5,                       // 크기 스케일
        "initialXshift": 0,                  // 초기 X 위치
        "initialYshift": 0,                  // 초기 Y 위치  
        "kXOffset": 1150,                    // X 오프셋
        "idleMotionGroupName": "Idle",       // 기본 모션 그룹
        "emotionMap": { /* 감정 매핑 */ },   // 감정→표정인덱스 매핑
        "tapMotions": { /* 클릭 모션 */ }    // 클릭 시 실행될 모션
    }
]
```

### 2. 표정 프롬프트 시스템

```text
# prompts/utils/live2d_expression_prompt.txt

## Expressions
In your response, use the keywords provided below to express facial expressions:

- [neutral], [anger], [fear], [joy], [sadness], [surprise]

## Examples  
"Hi! [joy] Nice to meet you!"
"[surprise] That's a great question! [joy] Let me explain..."
```

**프롬프트 동작 방식**:
1. AI 에이전트가 응답 생성 시 이 프롬프트를 참조
2. `[감정]` 태그를 응답에 자연스럽게 포함
3. Live2D 시스템이 태그를 감지하고 해당 표정 실행

## 🔧 구현 시 핵심 고려사항

### 1. Fortune VTuber 프로젝트 적용 방안

#### A. 기존 시스템과 통합
```python
# Fortune VTuber의 기존 Live2D 서비스와 연동
from .services.live2d_service import Live2DService
from .live2d.emotion_bridge import emotion_bridge

# Open-LLM-VTuber의 모델 관리 기능 적용
class FortuneLive2DModel(Live2dModel):
    """Fortune VTuber용 Live2D 모델 클래스"""
    
    def __init__(self, model_name: str):
        super().__init__(model_name, "static/live2d/model_dict.json")
        
    def integrate_with_fortune_system(self):
        """기존 Fortune 시스템과 통합"""
        # 감정 매핑을 기존 emotion_bridge와 연동
        # WebSocket을 기존 live2d_websocket과 통합
```

#### B. 감정 처리 시스템 향상
```python
# Open-LLM-VTuber의 감정 추출 로직을 Fortune 시스템에 적용
def enhance_emotion_processing(fortune_result: dict, user_message: str) -> dict:
    """운세 결과와 사용자 메시지에서 감정 추출 및 Live2D 반영"""
    
    # 1. 기존 운세 기반 감정 계산
    emotion_data = emotion_bridge.calculate_emotion(fortune_result, session_id, user_uuid)
    
    # 2. Open-LLM-VTuber 방식의 텍스트 감정 태그 추출  
    live2d_model = FortuneLife2DModel("mao_pro")
    extracted_emotions = live2d_model.extract_emotion(user_message)
    
    # 3. 두 방식을 조합하여 더 정확한 감정 상태 생성
    combined_emotion = combine_emotion_sources(emotion_data, extracted_emotions)
    
    return combined_emotion
```

### 2. 성능 최적화 방안

#### A. 모델 파일 캐싱
```python
class OptimizedLive2DModel:
    _model_cache = {}  # 모델 정보 캐시
    
    @classmethod
    def get_cached_model(cls, model_name: str):
        if model_name not in cls._model_cache:
            cls._model_cache[model_name] = Live2dModel(model_name)
        return cls._model_cache[model_name]
```

#### B. WebSocket 메시지 배치 처리
```python
# 여러 Live2D 업데이트를 하나의 메시지로 배치 전송
async def send_batch_live2d_updates(websocket: WebSocket, updates: list):
    batch_message = {
        "type": "live2d_batch_update",
        "updates": updates,
        "timestamp": time.time()
    }
    await websocket.send_text(json.dumps(batch_message))
```

### 3. 확장성 고려사항

#### A. 다중 캐릭터 지원
```python
class MultiCharacterManager:
    def __init__(self):
        self.characters = {}
        
    def load_character(self, char_name: str, model_path: str):
        self.characters[char_name] = Live2dModel(char_name, model_path)
        
    def switch_character(self, websocket: WebSocket, char_name: str):
        # 캐릭터 전환 로직
```

#### B. 커스텀 표정/모션 시스템
```python
class CustomExpressionManager:
    def create_custom_emotion_map(self, base_map: dict, custom_emotions: dict):
        """사용자 정의 감정 매핑 생성"""
        return {**base_map, **custom_emotions}
        
    def register_custom_motion(self, motion_name: str, motion_file: str):
        """사용자 정의 모션 등록"""
```

## 📊 시스템 흐름도

```
[사용자 입력] 
    ↓
[WebSocket 수신]
    ↓  
[메시지 타입 분류]
    ↓
[AI 에이전트 처리]
    ↓
[응답 텍스트 생성] (감정 태그 포함)
    ↓
[Live2D 모델에서 감정 추출]
    ↓
[감정 태그 제거 + 순수 텍스트 분리]
    ↓
[TTS 음성 생성]
    ↓
[WebSocket으로 클라이언트에 전송]
    ↓
[프론트엔드에서 Live2D 표정/모션 실행]
    ↓
[음성 재생 + 립싱크]
```

## 🎯 Fortune VTuber 구현 권장사항

### 1. 단계별 구현 접근법

**Phase 1**: 기본 감정 매핑 통합
- Open-LLM-VTuber의 `Live2dModel` 클래스 적용
- 기존 `emotion_bridge.py`와 연동
- 텍스트 감정 태그 추출 기능 추가

**Phase 2**: WebSocket 메시지 확장  
- Live2D 전용 메시지 타입 추가
- 배치 업데이트 시스템 구현
- 실시간 표정 동기화 최적화

**Phase 3**: 고도화 기능
- 다중 캐릭터 지원
- 커스텀 표정/모션 시스템
- 사용자별 캐릭터 설정 저장

### 2. 코드 재사용 가이드

**직접 적용 가능한 코드**:
- `Live2dModel` 클래스의 감정 매핑 로직
- 텍스트 감정 태그 추출/제거 함수
- 모델 딕셔너리 구조 및 로딩 시스템

**수정 후 적용 권장**:  
- WebSocket 핸들러 (기존 시스템과 통합 필요)
- 서버 설정 부분 (FastAPI 설정 차이)
- 프론트엔드 연동 부분 (React 구조 차이)

이 분석 보고서를 바탕으로 Fortune VTuber 프로젝트의 Live2D 기능을 체계적으로 개선하고 확장할 수 있습니다.
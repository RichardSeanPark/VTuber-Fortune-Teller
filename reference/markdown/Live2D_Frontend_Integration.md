# Live2D 프론트엔드 통합 가이드

## 📋 개요

이 문서는 Open-LLM-VTuber의 프론트엔드 Live2D 통합 방식을 분석하고, JavaScript 기반 Live2D 시스템의 동작 원리를 상세히 설명합니다.

## 🎨 프론트엔드 Live2D 아키텍처

### 1. 기술 스택

```
React Frontend Application
├── Live2D Cubism Core (live2dcubismcore.js)
├── Live2D Framework (live2d.min.js) 
├── WebSocket Client (실시간 통신)
└── Audio System (TTS + Lip Sync)
```

### 2. 핵심 JavaScript 라이브러리

#### A. Live2D Cubism Core (`live2dcubismcore.js`)
- **역할**: Live2D 모델의 저수준 렌더링 엔진
- **기능**: .moc3 파일 로딩, 파라미터 조작, 물리 시뮬레이션
- **크기**: 압축된 바이너리 형태로 최적화

#### B. Live2D Framework (`live2d.min.js`)  
- **역할**: 고수준 Live2D 조작 인터페이스
- **기능**: 모션 재생, 표정 변경, 사용자 인터랙션 처리
- **연동**: Cubism Core와 React 컴포넌트를 연결

## 🔧 Live2D 모델 로딩 프로세스

### 1. 모델 초기화 워크플로우

```javascript
// 1. Live2D 모델 로드
async function loadLive2DModel(modelPath) {
    try {
        // 모델 JSON 파일 로드
        const modelJson = await fetch(modelPath).then(res => res.json());
        
        // 필수 리소스들 로드
        const resources = await Promise.all([
            loadModelFile(modelJson.FileReferences.Moc),      // .moc3 파일
            loadTextures(modelJson.FileReferences.Textures),  // 텍스처들
            loadPhysics(modelJson.FileReferences.Physics),    // 물리 설정
            loadPose(modelJson.FileReferences.Pose),         // 포즈 설정
            loadExpressions(modelJson.FileReferences.Expressions), // 표정들
            loadMotions(modelJson.FileReferences.Motions)    // 모션들
        ]);
        
        // Live2D 모델 객체 생성
        const model = new Live2DModel();
        await model.initialize(resources);
        
        return model;
        
    } catch (error) {
        console.error('Live2D model loading failed:', error);
        throw error;
    }
}
```

### 2. 리소스 로딩 최적화

```javascript
// 프리로딩 시스템
class Live2DResourceManager {
    constructor() {
        this.cache = new Map();
        this.loadingPromises = new Map();
    }
    
    async preloadModel(modelName) {
        if (this.loadingPromises.has(modelName)) {
            return this.loadingPromises.get(modelName);
        }
        
        const loadPromise = this.loadModelResources(modelName);
        this.loadingPromises.set(modelName, loadPromise);
        
        return loadPromise;
    }
    
    async loadModelResources(modelName) {
        const modelPath = `/live2d-models/${modelName}/runtime/${modelName}.model3.json`;
        const modelData = await this.loadWithCache(modelPath);
        
        // 병렬 리소스 로딩
        const resourcePromises = [];
        
        // 텍스처 로딩
        modelData.FileReferences.Textures.forEach(texture => {
            resourcePromises.push(this.loadTexture(texture));
        });
        
        // 표정 파일들 로딩
        modelData.FileReferences.Expressions.forEach(exp => {
            resourcePromises.push(this.loadExpression(exp.File));
        });
        
        await Promise.all(resourcePromises);
        return modelData;
    }
}
```

## 🎭 표정 시스템 구현

### 1. 표정 관리 클래스

```javascript
class Live2DExpressionManager {
    constructor(model) {
        this.model = model;
        this.expressions = new Map();
        this.currentExpression = null;
        this.transitionTime = 500; // 500ms 전환 시간
    }
    
    // 표정 파일들을 로드하고 등록
    async loadExpressions(expressionFiles) {
        for (const expFile of expressionFiles) {
            try {
                const expData = await fetch(expFile.File).then(res => res.json());
                this.expressions.set(expFile.Name, expData);
            } catch (error) {
                console.error(`Failed to load expression ${expFile.Name}:`, error);
            }
        }
    }
    
    // 표정 변경 (부드러운 전환 포함)
    setExpression(expressionName, weight = 1.0, fadeTime = null) {
        const expression = this.expressions.get(expressionName);
        if (!expression) {
            console.warn(`Expression ${expressionName} not found`);
            return;
        }
        
        const actualFadeTime = fadeTime || this.transitionTime;
        
        // 이전 표정에서 부드럽게 전환
        this.fadeExpression(this.currentExpression, 0, actualFadeTime);
        this.fadeExpression(expression, weight, actualFadeTime);
        
        this.currentExpression = expression;
    }
    
    // 표정 페이드 효과
    fadeExpression(expression, targetWeight, duration) {
        if (!expression) return;
        
        const startTime = performance.now();
        const startWeight = this.getCurrentExpressionWeight(expression);
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1.0);
            
            // 이징 함수 적용 (부드러운 전환)
            const easedProgress = this.easeInOutCubic(progress);
            const currentWeight = startWeight + (targetWeight - startWeight) * easedProgress;
            
            this.applyExpressionWeight(expression, currentWeight);
            
            if (progress < 1.0) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    // 이징 함수
    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }
}
```

### 2. WebSocket 기반 실시간 표정 업데이트

```javascript
class Live2DWebSocketClient {
    constructor(modelManager, expressionManager) {
        this.modelManager = modelManager;
        this.expressionManager = expressionManager;
        this.websocket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect(wsUrl) {
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('Live2D WebSocket connected');
            this.reconnectAttempts = 0;
            this.sendClientInfo();
        };
        
        this.websocket.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };
        
        this.websocket.onclose = () => {
            console.log('Live2D WebSocket disconnected');
            this.attemptReconnect();
        };
        
        this.websocket.onerror = (error) => {
            console.error('Live2D WebSocket error:', error);
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'live2d_expression_update':
                this.handleExpressionUpdate(message);
                break;
                
            case 'live2d_motion_trigger':
                this.handleMotionTrigger(message);
                break;
                
            case 'ai-response':
                this.handleAIResponse(message);
                break;
                
            case 'live2d_batch_update':
                this.handleBatchUpdate(message);
                break;
                
            default:
                console.log('Unknown message type:', message.type);
        }
    }
    
    handleExpressionUpdate(message) {
        const { expression_index, duration, weight } = message;
        
        // 표정 인덱스를 표정 이름으로 변환
        const expressionName = this.getExpressionNameByIndex(expression_index);
        
        if (expressionName) {
            this.expressionManager.setExpression(
                expressionName, 
                weight || 1.0, 
                duration || 500
            );
        }
    }
    
    handleAIResponse(message) {
        const { expressions, text, audio_data } = message;
        
        // 여러 표정이 있는 경우 순차 실행
        if (expressions && expressions.length > 0) {
            this.playExpressionSequence(expressions);
        }
        
        // 음성 재생과 립싱크
        if (audio_data) {
            this.playAudioWithLipSync(audio_data, text);
        }
    }
    
    playExpressionSequence(expressions) {
        expressions.forEach((expIndex, i) => {
            setTimeout(() => {
                this.handleExpressionUpdate({
                    expression_index: expIndex,
                    duration: 1000,
                    weight: 1.0
                });
            }, i * 800); // 800ms 간격으로 순차 실행
        });
    }
}
```

## 🎵 TTS와 립싱크 시스템

### 1. 오디오 재생 및 립싱크

```javascript
class Live2DAudioManager {
    constructor(model) {
        this.model = model;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.lipSyncAnalyser = null;
        this.lipSyncData = new Uint8Array(256);
    }
    
    async playAudioWithLipSync(audioData, text) {
        try {
            // Base64 오디오 데이터를 ArrayBuffer로 변환
            const audioBuffer = await this.decodeAudioData(audioData);
            
            // 오디오 소스 생성
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            
            // 립싱크를 위한 분석기 설정
            this.setupLipSyncAnalyser(source);
            
            // 재생 시작
            source.connect(this.audioContext.destination);
            source.start();
            
            // 립싱크 애니메이션 시작
            this.startLipSyncAnimation(audioBuffer.duration);
            
        } catch (error) {
            console.error('Audio playback failed:', error);
        }
    }
    
    setupLipSyncAnalyser(audioSource) {
        this.lipSyncAnalyser = this.audioContext.createAnalyser();
        this.lipSyncAnalyser.fftSize = 512;
        this.lipSyncAnalyser.smoothingTimeConstant = 0.8;
        
        audioSource.connect(this.lipSyncAnalyser);
    }
    
    startLipSyncAnimation(duration) {
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = (currentTime - startTime) / 1000;
            
            if (elapsed < duration && this.lipSyncAnalyser) {
                // 주파수 데이터 분석
                this.lipSyncAnalyser.getByteFrequencyData(this.lipSyncData);
                
                // 입 열림 정도 계산 (저주파~중주파 대역 활용)
                const mouthOpenness = this.calculateMouthOpenness(this.lipSyncData);
                
                // Live2D 모델의 입 파라미터 업데이트
                this.model.setParameterValueById('ParamA', mouthOpenness);
                
                requestAnimationFrame(animate);
            } else {
                // 애니메이션 종료 - 입 닫기
                this.model.setParameterValueById('ParamA', 0);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    calculateMouthOpenness(frequencyData) {
        // 음성의 주요 주파수 대역에서 에너지 계산
        const lowFreq = frequencyData.slice(0, 64);  // 저주파
        const midFreq = frequencyData.slice(64, 128); // 중주파
        
        const lowEnergy = lowFreq.reduce((sum, val) => sum + val, 0) / lowFreq.length;
        const midEnergy = midFreq.reduce((sum, val) => sum + val, 0) / midFreq.length;
        
        // 에너지 기반 입 열림 계산 (0~1 범위)
        const totalEnergy = (lowEnergy + midEnergy) / 2;
        const normalizedEnergy = Math.min(totalEnergy / 128, 1.0);
        
        // 자연스러운 입 움직임을 위한 보정
        return normalizedEnergy * 0.8 + 0.1; // 0.1~0.9 범위로 조정
    }
}
```

## 🖱️ 사용자 인터랙션 시스템

### 1. 클릭 상호작용 처리

```javascript
class Live2DInteractionManager {
    constructor(canvas, model, websocket) {
        this.canvas = canvas;
        this.model = model;
        this.websocket = websocket;
        this.hitAreas = new Map();
        
        this.setupEventListeners();
        this.loadHitAreas();
    }
    
    setupEventListeners() {
        this.canvas.addEventListener('click', (event) => {
            this.handleClick(event);
        });
        
        this.canvas.addEventListener('mousemove', (event) => {
            this.handleMouseMove(event);
        });
    }
    
    loadHitAreas() {
        // model3.json에서 HitArea 정보 로드
        const hitAreas = this.model.getHitAreas();
        
        hitAreas.forEach(hitArea => {
            this.hitAreas.set(hitArea.Id, {
                name: hitArea.Name,
                bounds: this.calculateHitAreaBounds(hitArea.Id)
            });
        });
    }
    
    handleClick(event) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width * 2 - 1;  // -1~1 범위로 정규화
        const y = -((event.clientY - rect.top) / rect.height * 2 - 1); // -1~1 범위로 정규화
        
        // 클릭된 HitArea 찾기
        const hitAreaId = this.getHitAreaAt(x, y);
        
        if (hitAreaId) {
            this.triggerHitAreaAction(hitAreaId, x, y);
        }
    }
    
    getHitAreaAt(x, y) {
        for (const [areaId, area] of this.hitAreas) {
            if (this.isPointInHitArea(x, y, area.bounds)) {
                return areaId;
            }
        }
        return null;
    }
    
    triggerHitAreaAction(hitAreaId, x, y) {
        console.log(`Hit area clicked: ${hitAreaId}`);
        
        // 서버에 클릭 이벤트 전송
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'live2d_interaction',
                action: 'hit_area_click',
                hit_area_id: hitAreaId,
                position: { x, y },
                timestamp: Date.now()
            }));
        }
        
        // 로컬에서 즉시 반응 (응답성 향상)
        this.playLocalReaction(hitAreaId);
    }
    
    playLocalReaction(hitAreaId) {
        switch (hitAreaId) {
            case 'HitAreaHead':
                // 머리 클릭 시 - 놀란 표정
                this.model.setExpression('surprise', 1.0, 300);
                break;
                
            case 'HitAreaBody':  
                // 몸 클릭 시 - 기쁜 표정
                this.model.setExpression('joy', 1.0, 300);
                break;
                
            default:
                // 기본 반응
                this.model.setExpression('neutral', 1.0, 200);
        }
    }
}
```

## 📱 React 컴포넌트 통합

### 1. Live2D React 컴포넌트

```jsx
import React, { useEffect, useRef, useState } from 'react';
import { Live2DModel } from './lib/live2d-model';

const Live2DCharacter = ({ 
    modelName = 'mao_pro', 
    wsUrl,
    onModelLoaded,
    onError 
}) => {
    const canvasRef = useRef(null);
    const [model, setModel] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        initializeLive2D();
        
        return () => {
            cleanup();
        };
    }, [modelName]);
    
    const initializeLive2D = async () => {
        try {
            setIsLoading(true);
            setError(null);
            
            // Canvas 설정
            const canvas = canvasRef.current;
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            
            if (!gl) {
                throw new Error('WebGL not supported');
            }
            
            // Live2D 모델 로드
            const modelPath = `/live2d-models/${modelName}/runtime/${modelName}.model3.json`;
            const live2dModel = new Live2DModel(gl);
            
            await live2dModel.loadModel(modelPath);
            
            // WebSocket 연결 설정
            const wsClient = new Live2DWebSocketClient(live2dModel);
            if (wsUrl) {
                wsClient.connect(wsUrl);
            }
            
            // 상호작용 매니저 설정
            const interactionManager = new Live2DInteractionManager(
                canvas, 
                live2dModel, 
                wsClient.websocket
            );
            
            // 렌더링 루프 시작
            startRenderLoop(live2dModel, gl);
            
            setModel(live2dModel);
            setIsLoading(false);
            
            if (onModelLoaded) {
                onModelLoaded(live2dModel);
            }
            
        } catch (err) {
            console.error('Live2D initialization failed:', err);
            setError(err.message);
            setIsLoading(false);
            
            if (onError) {
                onError(err);
            }
        }
    };
    
    const startRenderLoop = (model, gl) => {
        const render = () => {
            // 캔버스 클리어
            gl.clearColor(0.0, 0.0, 0.0, 0.0);
            gl.clear(gl.COLOR_BUFFER_BIT);
            
            // 모델 업데이트 및 렌더링
            model.update();
            model.draw(gl);
            
            requestAnimationFrame(render);
        };
        
        requestAnimationFrame(render);
    };
    
    const cleanup = () => {
        if (model) {
            model.dispose();
        }
    };
    
    if (error) {
        return (
            <div className="live2d-error">
                <p>Live2D 로딩 실패: {error}</p>
            </div>
        );
    }
    
    return (
        <div className="live2d-container">
            {isLoading && (
                <div className="live2d-loading">
                    Live2D 모델 로딩 중...
                </div>
            )}
            <canvas
                ref={canvasRef}
                width={800}
                height={600}
                style={{ 
                    width: '100%', 
                    height: '100%',
                    display: isLoading ? 'none' : 'block'
                }}
            />
        </div>
    );
};

export default Live2DCharacter;
```

### 2. 앱 레벨 통합

```jsx
// App.jsx
import React, { useState, useCallback } from 'react';
import Live2DCharacter from './components/Live2DCharacter';
import ChatInterface from './components/ChatInterface';

const App = () => {
    const [live2dModel, setLive2dModel] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    
    const handleModelLoaded = useCallback((model) => {
        console.log('Live2D model loaded successfully');
        setLive2dModel(model);
    }, []);
    
    const handleModelError = useCallback((error) => {
        console.error('Live2D model error:', error);
    }, []);
    
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/client-ws';
    
    return (
        <div className="app">
            <div className="live2d-section">
                <Live2DCharacter
                    modelName="mao_pro"
                    wsUrl={wsUrl}
                    onModelLoaded={handleModelLoaded}
                    onError={handleModelError}
                />
            </div>
            
            <div className="chat-section">
                <ChatInterface
                    wsUrl={wsUrl}
                    onConnectionChange={setIsConnected}
                />
            </div>
            
            <div className="status-bar">
                <span>모델: {live2dModel ? '로드됨' : '로딩중'}</span>
                <span>연결: {isConnected ? '연결됨' : '연결 안됨'}</span>
            </div>
        </div>
    );
};

export default App;
```

## 🔧 Fortune VTuber 프로젝트 적용 가이드

### 1. 기존 시스템과의 통합 포인트

#### A. WebSocket 메시지 확장
```javascript
// Fortune VTuber의 기존 WebSocket과 통합
const fortuneWebSocket = new WebSocket('ws://localhost:8000/ws/live2d');

fortuneWebSocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
        // 기존 Fortune VTuber 메시지들
        case 'LIVE2D_ACTION':
        case 'LIVE2D_PARAMETER_UPDATE':
        case 'TTS_LIPSYNC_UPDATE':
            handleFortuneLive2DMessage(message);
            break;
            
        // Open-LLM-VTuber 방식 추가
        case 'ai-response':
            handleAIResponseWithExpressions(message);
            break;
    }
};
```

#### B. 감정 매핑 시스템 통합
```javascript
class FortuneLive2DExpressionManager extends Live2DExpressionManager {
    constructor(model, fortuneEmotionMap) {
        super(model);
        this.fortuneEmotionMap = fortuneEmotionMap; // 기존 Fortune 감정 매핑
        this.openVTuberMap = this.loadOpenVTuberMapping(); // Open-LLM-VTuber 매핑
    }
    
    // 두 시스템의 감정 매핑을 통합
    setEmotionFromFortune(fortuneEmotion) {
        const mappedExpression = this.fortuneEmotionMap[fortuneEmotion];
        if (mappedExpression) {
            this.setExpression(mappedExpression.name, mappedExpression.intensity);
        }
    }
    
    setEmotionFromText(textWithTags) {
        // Open-LLM-VTuber 방식의 [joy], [anger] 태그 처리
        const emotions = this.extractEmotionTags(textWithTags);
        emotions.forEach(emotion => {
            const mappedExpression = this.openVTuberMap[emotion];
            if (mappedExpression) {
                this.setExpression(mappedExpression);
            }
        });
    }
}
```

### 2. 성능 최적화 권장사항

#### A. 프리로딩 및 캐싱
```javascript
class OptimizedLive2DLoader {
    static preloadedModels = new Map();
    
    static async preloadModel(modelName) {
        if (this.preloadedModels.has(modelName)) {
            return this.preloadedModels.get(modelName);
        }
        
        const modelData = await this.loadModelData(modelName);
        this.preloadedModels.set(modelName, modelData);
        
        return modelData;
    }
    
    // 사용하지 않는 모델 메모리 해제
    static unloadModel(modelName) {
        const modelData = this.preloadedModels.get(modelName);
        if (modelData) {
            modelData.dispose();
            this.preloadedModels.delete(modelName);
        }
    }
}
```

#### B. 렌더링 최적화
```javascript
class OptimizedLive2DRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.lastFrameTime = 0;
        this.targetFPS = 60;
        this.frameInterval = 1000 / this.targetFPS;
    }
    
    // 프레임 레이트 제한
    render(currentTime) {
        if (currentTime - this.lastFrameTime >= this.frameInterval) {
            this.actualRender();
            this.lastFrameTime = currentTime;
        }
        
        requestAnimationFrame((time) => this.render(time));
    }
    
    actualRender() {
        // 실제 Live2D 렌더링 로직
        if (this.model) {
            this.model.update();
            this.model.draw(this.gl);
        }
    }
}
```

이 가이드를 참고하여 Fortune VTuber 프로젝트에 고급 Live2D 기능을 체계적으로 통합할 수 있습니다.
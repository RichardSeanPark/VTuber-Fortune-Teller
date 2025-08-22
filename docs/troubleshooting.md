# 🛠️ Live2D 운세 앱 문제 해결 가이드

> **최종 업데이트**: 2025년 8월 22일  
> **버전**: 1.0.0  
> **대상**: 개발자, 시스템 관리자, 사용자

## 📋 목차

1. [일반적인 문제들](#일반적인-문제들)
2. [설치 및 설정 문제](#설치-및-설정-문제)
3. [API 관련 문제](#api-관련-문제)
4. [WebSocket 연결 문제](#websocket-연결-문제)
5. [Live2D 관련 문제](#live2d-관련-문제)
6. [데이터베이스 문제](#데이터베이스-문제)
7. [성능 문제](#성능-문제)
8. [보안 관련 문제](#보안-관련-문제)
9. [프론트엔드 문제](#프론트엔드-문제)
10. [진단 도구](#진단-도구)
11. [로그 분석](#로그-분석)
12. [지원 요청](#지원-요청)

## 🔧 일반적인 문제들

### 1. 서비스가 시작되지 않음

#### 증상
- 백엔드 서버가 시작되지 않음
- "Address already in use" 에러
- 프로세스가 즉시 종료됨

#### 해결 방법

```bash
# 1. 포트 사용 확인
sudo netstat -tlnp | grep :8080
sudo lsof -i :8080

# 2. 기존 프로세스 종료
sudo pkill -f fortune_vtuber
sudo kill -9 $(sudo lsof -t -i:8080)

# 3. 환경 변수 확인
echo $DATABASE_URL
echo $SECRET_KEY

# 4. 의존성 확인
cd project/backend
source venv/bin/activate
pip list | grep -E "(fastapi|sqlalchemy|uvicorn)"

# 5. 설정 파일 확인
python -c "from fortune_vtuber.config.settings import get_settings; print(get_settings())"

# 6. 서비스 재시작
sudo systemctl restart fortune-vtuber-backend
sudo systemctl status fortune-vtuber-backend
```

#### 로그 확인
```bash
# 시스템 로그
journalctl -u fortune-vtuber-backend -f

# 애플리케이션 로그
tail -f /var/log/fortune-vtuber/app.log

# Python 에러 확인
python -m fortune_vtuber.main
```

### 2. 403 Forbidden 에러

#### 증상
- API 요청시 403 에러 발생
- "Content filtered" 메시지
- 특정 단어/문장에서 차단

#### 해결 방법

```python
# 콘텐츠 필터 테스트
from fortune_vtuber.security.content_filter import ContentFilter

filter = ContentFilter()
result = await filter.filter_content("문제가 되는 텍스트")
print(result)
```

**해결책:**
- 부적절한 내용이 포함되지 않았는지 확인
- 콘텐츠 필터 설정 조정 (관리자만)
- 다른 표현으로 질문 변경

#### 허용되는 질문 예시
```
✅ 좋은 예시:
- "오늘 운세가 어떨까요?"
- "연애운이 궁금해요"
- "이번 주 금전운은 어떤가요?"

❌ 피해야 할 예시:
- 성적인 내용
- 폭력적인 내용
- 정치적인 내용
- 의료/법률 조언 요청
```

### 3. 세션 만료 문제

#### 증상
- "Session expired" 에러
- 401 Unauthorized 응답
- 갑작스러운 로그아웃

#### 해결 방법

```javascript
// 세션 자동 갱신 구현
class SessionManager {
  constructor() {
    this.sessionId = null;
    this.expiresAt = null;
    this.renewalTimer = null;
  }

  async createSession() {
    const response = await fetch('/api/v1/user/session', { method: 'POST' });
    const data = await response.json();
    
    this.sessionId = data.data.session_id;
    this.expiresAt = new Date(data.data.expires_at);
    
    // 만료 30분 전에 갱신
    const renewTime = this.expiresAt.getTime() - Date.now() - (30 * 60 * 1000);
    this.renewalTimer = setTimeout(() => this.renewSession(), renewTime);
    
    return this.sessionId;
  }

  async renewSession() {
    try {
      const response = await fetch('/api/v1/user/session/renew', {
        method: 'PUT',
        headers: { 'X-Session-ID': this.sessionId }
      });
      
      if (response.ok) {
        const data = await response.json();
        this.expiresAt = new Date(data.data.expires_at);
        console.log('세션 갱신 성공');
      }
    } catch (error) {
      console.error('세션 갱신 실패:', error);
      // 새 세션 생성
      await this.createSession();
    }
  }

  async makeAuthenticatedRequest(url, options = {}) {
    // 세션 만료 체크
    if (Date.now() >= this.expiresAt.getTime()) {
      await this.createSession();
    }

    return fetch(url, {
      ...options,
      headers: {
        'X-Session-ID': this.sessionId,
        ...options.headers
      }
    });
  }
}
```

## 🚀 설치 및 설정 문제

### 1. Python 의존성 설치 실패

#### 증상
- `pip install` 실패
- 컴파일 에러
- "No module named" 에러

#### 해결 방법

```bash
# 1. Python 버전 확인 (3.10+ 필요)
python --version

# 2. pip 업그레이드
python -m pip install --upgrade pip

# 3. 시스템 패키지 설치 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip build-essential

# 4. 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate

# 5. 의존성 개별 설치
pip install wheel setuptools
pip install -e .

# 6. 특정 패키지 문제 해결
# SQLAlchemy 설치 실패시
pip install --no-binary sqlalchemy sqlalchemy

# FastAPI 설치 실패시
pip install --no-cache-dir fastapi

# 7. 대안 설치 방법
pip install -r requirements.txt --no-deps
pip install --force-reinstall fortune-vtuber
```

### 2. Node.js 프론트엔드 설치 문제

#### 증상
- `npm install` 실패
- 패키지 충돌
- 빌드 에러

#### 해결 방법

```bash
# 1. Node.js 버전 확인 (18+ 권장)
node --version
npm --version

# 2. 캐시 정리
npm cache clean --force
rm -rf node_modules package-lock.json

# 3. 재설치
npm install

# 4. 특정 패키지 문제 해결
# React 버전 충돌
npm install react@^18.0.0 react-dom@^18.0.0 --save

# Live2D 라이브러리 문제
npm install --legacy-peer-deps

# 5. Yarn 사용 (npm 대신)
npm install -g yarn
yarn install

# 6. 개발 서버 시작 확인
npm start
```

### 3. 데이터베이스 초기화 문제

#### 증상
- Alembic 마이그레이션 실패
- 테이블 생성 오류
- 권한 문제

#### 해결 방법

```bash
# 1. 데이터베이스 연결 확인
python -c "from fortune_vtuber.config.database import test_connection; test_connection()"

# 2. SQLite 파일 권한 확인
ls -la fortune_vtuber.db
sudo chown $(whoami):$(whoami) fortune_vtuber.db

# 3. Alembic 초기화
cd project/backend
rm -rf alembic/versions/*
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# 4. 수동 테이블 생성
python -c "
from fortune_vtuber.config.database import init_database
import asyncio
asyncio.run(init_database())
"

# 5. PostgreSQL 설정 (프로덕션)
sudo -u postgres createdb fortune_vtuber
sudo -u postgres psql -c "CREATE USER fortune_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fortune_vtuber TO fortune_user;"
```

## 🌐 API 관련 문제

### 1. API 응답 시간 초과

#### 증상
- 요청이 매우 느림 (>5초)
- 타임아웃 에러
- 로딩이 끝나지 않음

#### 진단 방법

```bash
# 1. API 응답 시간 측정
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8080/api/v1/fortune/daily"

# curl-format.txt 파일 내용:
#     time_namelookup:  %{time_namelookup}\n
#     time_connect:     %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#     time_pretransfer: %{time_pretransfer}\n
#     time_redirect:    %{time_redirect}\n
#     time_starttransfer: %{time_starttransfer}\n
#     ----------\n
#     time_total:       %{time_total}\n

# 2. 데이터베이스 쿼리 성능 확인
tail -f /var/log/fortune-vtuber/app.log | grep "SQL"

# 3. 메모리 사용량 확인
ps aux | grep fortune_vtuber
```

#### 해결 방법

```python
# 1. 비동기 처리 최적화
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_fortune_with_timeout():
    try:
        # 10초 타임아웃 설정
        async with asyncio.timeout(10):
            yield
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Request timeout")

# 2. 캐시 구현
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_fortune(cache_key: str):
    # 캐시된 운세 반환
    pass

# 3. 데이터베이스 연결 풀 최적화
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 2. 운세 생성 실패

#### 증상
- "Fortune generation failed" 에러
- 빈 응답 반환
- 운세 내용이 이상함

#### 진단 및 해결

```python
# 1. 운세 엔진 테스트
from fortune_vtuber.fortune.engines import DailyFortuneEngine

async def test_fortune_engine():
    engine = DailyFortuneEngine()
    try:
        result = await engine.generate_fortune(
            birth_date="1995-03-15",
            zodiac="pisces"
        )
        print("운세 생성 성공:", result)
    except Exception as e:
        print("운세 생성 실패:", str(e))
        import traceback
        traceback.print_exc()

# 2. 입력 데이터 검증
def validate_fortune_input(birth_date: str, zodiac: str):
    from datetime import datetime
    
    # 날짜 형식 확인
    try:
        datetime.strptime(birth_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format")
    
    # 별자리 확인
    valid_zodiacs = [
        "aries", "taurus", "gemini", "cancer", 
        "leo", "virgo", "libra", "scorpio",
        "sagittarius", "capricorn", "aquarius", "pisces"
    ]
    
    if zodiac not in valid_zodiacs:
        raise ValueError("Invalid zodiac sign")

# 3. 로깅 강화
import logging

logger = logging.getLogger(__name__)

async def generate_fortune_with_logging(**kwargs):
    logger.info(f"운세 생성 시작: {kwargs}")
    
    try:
        result = await fortune_engine.generate(**kwargs)
        logger.info("운세 생성 성공")
        return result
    except Exception as e:
        logger.error(f"운세 생성 실패: {str(e)}")
        raise
```

### 3. Rate Limiting 문제

#### 증상
- 429 Too Many Requests 에러
- "Rate limit exceeded" 메시지
- 요청이 거부됨

#### 해결 방법

```javascript
// 1. Rate Limit 대응 클라이언트
class RateLimitedAPIClient {
  constructor() {
    this.requestQueue = [];
    this.lastRequestTime = 0;
    this.minInterval = 1000; // 1초 간격
  }

  async makeRequest(url, options) {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequestTime;
    
    if (timeSinceLastRequest < this.minInterval) {
      await new Promise(resolve => 
        setTimeout(resolve, this.minInterval - timeSinceLastRequest)
      );
    }

    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        const retryAfter = response.headers.get('X-RateLimit-Retry-After') || 60;
        console.warn(`Rate limited, retrying after ${retryAfter} seconds`);
        
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        return this.makeRequest(url, options);
      }
      
      this.lastRequestTime = Date.now();
      return response;
      
    } catch (error) {
      console.error('Request failed:', error);
      throw error;
    }
  }
}

// 2. 백오프 전략
async function makeRequestWithBackoff(requestFn, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      if (error.status === 429 && attempt < maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 지수 백오프
        console.log(`Attempt ${attempt} failed, retrying in ${delay}ms`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error;
      }
    }
  }
}
```

## 🔌 WebSocket 연결 문제

### 1. WebSocket 연결 실패

#### 증상
- "WebSocket connection failed" 메시지
- 연결이 즉시 끊어짐
- 채팅이 작동하지 않음

#### 진단 방법

```bash
# 1. WebSocket 엔드포인트 테스트
websocat ws://localhost:8080/ws/chat/test_session_id

# 2. 네트워크 연결 확인
curl -I http://localhost:8080/health

# 3. 방화벽 설정 확인
sudo ufw status
netstat -tulpn | grep :8080

# 4. SSL/TLS 문제 (HTTPS 환경)
openssl s_client -connect fortune-vtuber.com:443 -servername fortune-vtuber.com
```

#### 해결 방법

```javascript
// 1. 강력한 WebSocket 클라이언트
class RobustWebSocket {
  constructor(url, options = {}) {
    this.url = url;
    this.options = options;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
    this.messageQueue = [];
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting) return;
    
    this.isConnecting = true;
    console.log(`WebSocket 연결 시도: ${this.url}`);

    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = (event) => {
        console.log('WebSocket 연결 성공');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        
        // 대기 중인 메시지 전송
        while (this.messageQueue.length > 0) {
          const message = this.messageQueue.shift();
          this.ws.send(message);
        }
        
        if (this.options.onOpen) this.options.onOpen(event);
      };

      this.ws.onmessage = (event) => {
        if (this.options.onMessage) this.options.onMessage(event);
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket 연결 종료:', event.code, event.reason);
        this.isConnecting = false;
        
        if (this.options.onClose) this.options.onClose(event);
        
        // 자동 재연결 (정상 종료가 아닌 경우)
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket 에러:', error);
        this.isConnecting = false;
        
        if (this.options.onError) this.options.onError(error);
      };

    } catch (error) {
      console.error('WebSocket 생성 실패:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`재연결 예약: ${delay}ms 후 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      this.connect();
    }, delay);
  }

  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(message);
    } else {
      // 연결되지 않은 경우 큐에 저장
      this.messageQueue.push(message);
      
      if (!this.isConnecting && this.ws?.readyState !== WebSocket.CONNECTING) {
        this.connect();
      }
    }
  }

  close() {
    this.reconnectAttempts = this.maxReconnectAttempts; // 재연결 방지
    if (this.ws) {
      this.ws.close(1000, 'Manual close');
    }
  }
}

// 사용 예시
const ws = new RobustWebSocket('ws://localhost:8080/ws/chat/session_id', {
  onOpen: () => console.log('연결됨'),
  onMessage: (event) => console.log('메시지:', event.data),
  onClose: (event) => console.log('연결 종료'),
  onError: (error) => console.error('에러:', error)
});

ws.connect();
```

### 2. WebSocket 메시지 손실

#### 증상
- 일부 메시지가 전달되지 않음
- 응답이 누락됨
- 순서가 뒤바뀜

#### 해결 방법

```javascript
// 메시지 확인 및 재전송 시스템
class ReliableWebSocket extends RobustWebSocket {
  constructor(url, options = {}) {
    super(url, options);
    this.messageId = 0;
    this.pendingMessages = new Map();
    this.acknowledgmentTimeout = 5000;
  }

  sendReliable(data) {
    const messageId = ++this.messageId;
    const message = {
      id: messageId,
      type: 'reliable_message',
      data: data,
      timestamp: Date.now()
    };

    this.send(JSON.stringify(message));
    
    // 확인 응답 대기
    this.pendingMessages.set(messageId, message);
    
    setTimeout(() => {
      if (this.pendingMessages.has(messageId)) {
        console.warn(`메시지 ${messageId} 확인 실패, 재전송`);
        this.sendReliable(data);
      }
    }, this.acknowledgmentTimeout);
  }

  handleMessage(event) {
    try {
      const message = JSON.parse(event.data);
      
      if (message.type === 'acknowledgment') {
        this.pendingMessages.delete(message.messageId);
      } else if (message.type === 'reliable_message') {
        // 확인 응답 전송
        this.send(JSON.stringify({
          type: 'acknowledgment',
          messageId: message.id
        }));
        
        // 메시지 처리
        if (this.options.onReliableMessage) {
          this.options.onReliableMessage(message.data);
        }
      }
      
      if (this.options.onMessage) {
        this.options.onMessage(event);
      }
      
    } catch (error) {
      console.error('메시지 파싱 실패:', error);
    }
  }
}
```

## 🎭 Live2D 관련 문제

### 1. Live2D 모델 로딩 실패

#### 증상
- 캐릭터가 표시되지 않음
- "Failed to load model" 에러
- 흰 화면 또는 깨진 화면

#### 진단 방법

```javascript
// Live2D 모델 로딩 진단
async function diagnoseLive2DModel(modelPath) {
  console.log('Live2D 모델 진단 시작:', modelPath);
  
  try {
    // 1. 모델 파일 존재 확인
    const modelResponse = await fetch(modelPath);
    if (!modelResponse.ok) {
      throw new Error(`모델 파일 접근 실패: ${modelResponse.status}`);
    }
    
    const modelJson = await modelResponse.json();
    console.log('모델 정보:', modelJson);
    
    // 2. 필수 파일들 확인
    const requiredFiles = [
      modelJson.FileReferences.Moc,
      ...modelJson.FileReferences.Textures,
      modelJson.FileReferences.Physics || null,
      modelJson.FileReferences.Pose || null
    ].filter(Boolean);
    
    for (const file of requiredFiles) {
      const fileUrl = new URL(file, modelPath).href;
      const fileResponse = await fetch(fileUrl, { method: 'HEAD' });
      
      if (!fileResponse.ok) {
        console.error(`파일 누락: ${file}`);
      } else {
        console.log(`파일 확인: ${file} (${fileResponse.headers.get('content-length')} bytes)`);
      }
    }
    
    // 3. Live2D SDK 버전 확인
    if (typeof Live2DCubismCore !== 'undefined') {
      console.log('Live2D Core 버전:', Live2DCubismCore.Version);
    } else {
      console.error('Live2D Core가 로드되지 않음');
    }
    
    return true;
    
  } catch (error) {
    console.error('Live2D 모델 진단 실패:', error);
    return false;
  }
}

// 사용 예시
diagnoseLive2DModel('/static/live2d/mira/mira.model3.json');
```

#### 해결 방법

```javascript
// 강력한 Live2D 로더
class RobustLive2DLoader {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.gl = null;
    this.model = null;
    this.app = null;
  }

  async loadModel(modelPath) {
    try {
      // 1. WebGL 초기화
      await this.initializeWebGL();
      
      // 2. Live2D 앱 초기화
      await this.initializeLive2DApp();
      
      // 3. 모델 로드
      await this.loadLive2DModel(modelPath);
      
      console.log('Live2D 모델 로딩 완료');
      return true;
      
    } catch (error) {
      console.error('Live2D 모델 로딩 실패:', error);
      await this.handleLoadingError(error);
      return false;
    }
  }

  async initializeWebGL() {
    this.gl = this.canvas.getContext('webgl2') || this.canvas.getContext('webgl');
    
    if (!this.gl) {
      throw new Error('WebGL을 지원하지 않는 브라우저입니다');
    }
    
    console.log('WebGL 초기화 완료');
  }

  async initializeLive2DApp() {
    if (typeof PIXI === 'undefined') {
      throw new Error('PIXI.js가 로드되지 않았습니다');
    }
    
    if (typeof Live2DCubismCore === 'undefined') {
      throw new Error('Live2D Core가 로드되지 않았습니다');
    }
    
    this.app = new PIXI.Application({
      view: this.canvas,
      autoStart: true,
      backgroundColor: 0x00000000, // 투명
      resolution: window.devicePixelRatio,
      autoDensity: true
    });
    
    console.log('Live2D 앱 초기화 완료');
  }

  async loadLive2DModel(modelPath) {
    // 모델 파일 사전 검증
    await diagnoseLive2DModel(modelPath);
    
    // Live2D 모델 생성
    this.model = await Live2DCubismFramework.loadModel(modelPath);
    
    if (!this.model) {
      throw new Error('모델 생성 실패');
    }
    
    // 앱에 모델 추가
    this.app.stage.addChild(this.model);
    
    // 모델 크기 조정
    this.resizeModel();
    
    console.log('Live2D 모델 로드 완료');
  }

  resizeModel() {
    if (!this.model) return;
    
    // 캔버스 크기에 맞춰 모델 조정
    const canvasWidth = this.canvas.width;
    const canvasHeight = this.canvas.height;
    
    const modelWidth = this.model.width;
    const modelHeight = this.model.height;
    
    const scaleX = canvasWidth / modelWidth;
    const scaleY = canvasHeight / modelHeight;
    const scale = Math.min(scaleX, scaleY) * 0.8; // 여백 추가
    
    this.model.scale.set(scale);
    this.model.position.set(canvasWidth / 2, canvasHeight / 2);
  }

  async handleLoadingError(error) {
    console.error('Live2D 로딩 에러 처리:', error);
    
    // 1. 폴백 이미지 표시
    this.showFallbackImage();
    
    // 2. 에러 리포팅
    this.reportError(error);
    
    // 3. 사용자 알림
    this.showUserNotification('캐릭터 로딩에 실패했습니다. 새로고침 해주세요.');
  }

  showFallbackImage() {
    const ctx = this.canvas.getContext('2d');
    if (ctx) {
      ctx.fillStyle = '#f0f0f0';
      ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      ctx.fillStyle = '#666';
      ctx.font = '16px Arial';
      ctx.textAlign = 'center';
      ctx.fillText('캐릭터 로딩 중...', this.canvas.width / 2, this.canvas.height / 2);
    }
  }

  showUserNotification(message) {
    // 사용자 알림 표시
    const notification = document.createElement('div');
    notification.className = 'live2d-error-notification';
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 5000);
  }
}
```

### 2. Live2D 애니메이션 문제

#### 증상
- 모션이 재생되지 않음
- 감정 변화가 없음
- 애니메이션이 끊김

#### 해결 방법

```javascript
// Live2D 애니메이션 관리자
class Live2DAnimationManager {
  constructor(model) {
    this.model = model;
    this.currentMotion = null;
    this.currentExpression = null;
    this.motionQueue = [];
    this.isPlaying = false;
  }

  async playMotion(motionName, priority = 1) {
    try {
      if (!this.model || !this.model.motions) {
        throw new Error('모델 또는 모션 데이터가 없습니다');
      }

      const motion = this.model.motions.get(motionName);
      if (!motion) {
        console.warn(`모션을 찾을 수 없습니다: ${motionName}`);
        return false;
      }

      // 우선순위 검사
      if (this.isPlaying && this.currentMotion?.priority >= priority) {
        this.motionQueue.push({ name: motionName, priority });
        return true;
      }

      // 모션 재생
      this.currentMotion = { name: motionName, priority };
      this.isPlaying = true;

      await this.model.startMotion(motionName, false, () => {
        this.isPlaying = false;
        this.currentMotion = null;
        
        // 대기 중인 모션 재생
        if (this.motionQueue.length > 0) {
          const nextMotion = this.motionQueue.shift();
          this.playMotion(nextMotion.name, nextMotion.priority);
        }
      });

      console.log(`모션 재생 시작: ${motionName}`);
      return true;

    } catch (error) {
      console.error('모션 재생 실패:', error);
      this.isPlaying = false;
      return false;
    }
  }

  async setExpression(expressionName) {
    try {
      if (!this.model || !this.model.expressions) {
        throw new Error('모델 또는 표정 데이터가 없습니다');
      }

      const expression = this.model.expressions.get(expressionName);
      if (!expression) {
        console.warn(`표정을 찾을 수 없습니다: ${expressionName}`);
        return false;
      }

      await this.model.setExpression(expressionName);
      this.currentExpression = expressionName;
      
      console.log(`표정 변경: ${expressionName}`);
      return true;

    } catch (error) {
      console.error('표정 변경 실패:', error);
      return false;
    }
  }

  async setEmotion(emotionName) {
    // 감정에 따른 표정과 모션 매핑
    const emotionMap = {
      'joy': { expression: 'smile', motion: 'greeting' },
      'thinking': { expression: 'normal', motion: 'thinking_pose' },
      'mystical': { expression: 'serious', motion: 'crystal_gaze' },
      'concern': { expression: 'worry', motion: 'comfort' },
      'surprise': { expression: 'surprise', motion: 'surprise' },
      'neutral': { expression: 'normal', motion: 'idle' }
    };

    const emotion = emotionMap[emotionName];
    if (!emotion) {
      console.warn(`알 수 없는 감정: ${emotionName}`);
      return false;
    }

    // 표정과 모션 동시 적용
    const results = await Promise.allSettled([
      this.setExpression(emotion.expression),
      this.playMotion(emotion.motion)
    ]);

    const success = results.every(result => result.status === 'fulfilled');
    console.log(`감정 설정 ${success ? '성공' : '실패'}: ${emotionName}`);
    
    return success;
  }

  // 매개변수 직접 제어
  setParameter(parameterName, value, duration = 1000) {
    if (!this.model || !this.model.parameters) {
      console.error('모델 매개변수에 접근할 수 없습니다');
      return false;
    }

    try {
      // 부드러운 전환을 위한 애니메이션
      const currentValue = this.model.parameters.get(parameterName) || 0;
      const startTime = Date.now();

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // easeInOut 함수 적용
        const easeProgress = 0.5 * (1 - Math.cos(Math.PI * progress));
        const interpolatedValue = currentValue + (value - currentValue) * easeProgress;
        
        this.model.parameters.set(parameterName, interpolatedValue);
        
        if (progress < 1) {
          requestAnimationFrame(animate);
        }
      };

      animate();
      return true;

    } catch (error) {
      console.error(`매개변수 설정 실패: ${parameterName}`, error);
      return false;
    }
  }

  // 진단 정보
  getDiagnostics() {
    if (!this.model) {
      return { error: '모델이 로드되지 않음' };
    }

    return {
      modelLoaded: !!this.model,
      motionsAvailable: this.model.motions ? this.model.motions.size : 0,
      expressionsAvailable: this.model.expressions ? this.model.expressions.size : 0,
      currentMotion: this.currentMotion?.name || 'none',
      currentExpression: this.currentExpression || 'none',
      isPlaying: this.isPlaying,
      queueLength: this.motionQueue.length
    };
  }
}
```

## 🗄️ 데이터베이스 문제

### 1. 데이터베이스 연결 실패

#### 증상
- "Database connection failed" 에러
- 느린 쿼리 성능
- 연결 풀 고갈

#### 진단 방법

```python
# 데이터베이스 연결 진단
async def diagnose_database():
    from fortune_vtuber.config.database import get_db_session
    import time
    
    print("데이터베이스 진단 시작...")
    
    try:
        # 1. 기본 연결 테스트
        start_time = time.time()
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1"))
            connection_time = time.time() - start_time
            print(f"✅ 기본 연결 성공 ({connection_time:.3f}s)")
        
        # 2. 테이블 존재 확인
        async with get_db_session() as session:
            tables = await session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """))
            table_list = [row[0] for row in tables.fetchall()]
            print(f"📊 테이블 목록: {table_list}")
        
        # 3. 인덱스 확인
        async with get_db_session() as session:
            indexes = await session.execute(text("""
                SELECT name, tbl_name FROM sqlite_master 
                WHERE type='index' AND name NOT LIKE 'sqlite_%'
            """))
            index_list = [(row[0], row[1]) for row in indexes.fetchall()]
            print(f"🔍 인덱스 목록: {index_list}")
        
        # 4. 데이터 카운트
        async with get_db_session() as session:
            for table in table_list:
                count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = count_result.scalar()
                print(f"📈 {table}: {count}개 레코드")
        
        # 5. 연결 풀 상태
        from fortune_vtuber.config.database import engine
        pool = engine.pool
        print(f"🏊 연결 풀: {pool.checkedin()}/{pool.size()} (체크인/전체)")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 진단 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

# 실행
import asyncio
asyncio.run(diagnose_database())
```

#### 해결 방법

```python
# 데이터베이스 연결 복구
async def repair_database():
    from fortune_vtuber.config.database import engine, get_db_session
    from sqlalchemy import text
    
    print("데이터베이스 복구 시작...")
    
    try:
        # 1. 연결 풀 초기화
        await engine.dispose()
        print("✅ 연결 풀 초기화 완료")
        
        # 2. 데이터베이스 무결성 검사 (SQLite)
        async with get_db_session() as session:
            integrity_result = await session.execute(text("PRAGMA integrity_check"))
            integrity = integrity_result.scalar()
            
            if integrity == "ok":
                print("✅ 데이터베이스 무결성 정상")
            else:
                print(f"⚠️ 데이터베이스 무결성 문제: {integrity}")
        
        # 3. 인덱스 재구성
        async with get_db_session() as session:
            await session.execute(text("REINDEX"))
            await session.commit()
            print("✅ 인덱스 재구성 완료")
        
        # 4. 통계 업데이트
        async with get_db_session() as session:
            await session.execute(text("ANALYZE"))
            await session.commit()
            print("✅ 통계 업데이트 완료")
        
        # 5. 빈 공간 정리 (SQLite)
        async with get_db_session() as session:
            await session.execute(text("VACUUM"))
            await session.commit()
            print("✅ 빈 공간 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 복구 실패: {e}")
        return False

# 연결 풀 최적화
from sqlalchemy.pool import QueuePool, StaticPool

def create_optimized_engine(database_url: str):
    if "sqlite" in database_url:
        # SQLite 최적화
        return create_async_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 20,
                "isolation_level": None
            },
            echo=False
        )
    else:
        # PostgreSQL 최적화
        return create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
```

### 2. 데이터 일관성 문제

#### 증상
- 중복 데이터
- 외래 키 제약 위반
- 트랜잭션 롤백 실패

#### 해결 방법

```python
# 데이터 일관성 검사 및 복구
async def check_data_consistency():
    from fortune_vtuber.config.database import get_db_session
    from sqlalchemy import text
    
    issues = []
    
    async with get_db_session() as session:
        # 1. 중복 세션 검사
        duplicate_sessions = await session.execute(text("""
            SELECT session_id, COUNT(*) as count
            FROM user_sessions
            GROUP BY session_id
            HAVING COUNT(*) > 1
        """))
        
        for row in duplicate_sessions.fetchall():
            issues.append(f"중복 세션: {row[0]} ({row[1]}개)")
        
        # 2. 고아 레코드 검사
        orphan_fortunes = await session.execute(text("""
            SELECT f.id FROM fortune_results f
            LEFT JOIN user_sessions s ON f.session_id = s.session_id
            WHERE s.session_id IS NULL
        """))
        
        orphan_count = len(orphan_fortunes.fetchall())
        if orphan_count > 0:
            issues.append(f"고아 운세 레코드: {orphan_count}개")
        
        # 3. 만료된 세션 정리
        expired_sessions = await session.execute(text("""
            SELECT COUNT(*) FROM user_sessions
            WHERE expires_at < datetime('now')
        """))
        
        expired_count = expired_sessions.scalar()
        if expired_count > 0:
            issues.append(f"만료된 세션: {expired_count}개")
    
    return issues

async def fix_data_consistency():
    from fortune_vtuber.config.database import get_db_session
    from sqlalchemy import text
    
    async with get_db_session() as session:
        try:
            # 1. 중복 세션 제거 (최신것만 유지)
            await session.execute(text("""
                DELETE FROM user_sessions
                WHERE id NOT IN (
                    SELECT MAX(id) FROM user_sessions
                    GROUP BY session_id
                )
            """))
            
            # 2. 고아 레코드 삭제
            await session.execute(text("""
                DELETE FROM fortune_results
                WHERE session_id NOT IN (
                    SELECT session_id FROM user_sessions
                )
            """))
            
            # 3. 만료된 세션 삭제
            await session.execute(text("""
                DELETE FROM user_sessions
                WHERE expires_at < datetime('now', '-1 day')
            """))
            
            await session.commit()
            print("✅ 데이터 일관성 복구 완료")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 데이터 일관성 복구 실패: {e}")
            raise
```

## ⚡ 성능 문제

### 1. 응답 속도 저하

#### 진단 방법

```python
# 성능 프로파일링
import time
import asyncio
from functools import wraps

def performance_monitor(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            if duration > 1.0:  # 1초 이상 걸린 경우
                print(f"⚠️ 느린 함수: {func.__name__} ({duration:.3f}s)")
            
            # 메트릭 수집
            from fortune_vtuber.monitoring.metrics import REQUEST_DURATION
            REQUEST_DURATION.labels(
                function=func.__name__
            ).observe(duration)
    
    return wrapper

# 사용 예시
@performance_monitor
async def get_daily_fortune(birth_date: str, zodiac: str):
    # 운세 생성 로직
    pass

# 데이터베이스 쿼리 최적화
from sqlalchemy import explain

async def analyze_query_performance():
    from fortune_vtuber.config.database import get_db_session
    
    async with get_db_session() as session:
        # 느린 쿼리 찾기
        slow_query = """
        SELECT * FROM fortune_results 
        WHERE created_at >= date('now', '-7 days')
        ORDER BY created_at DESC
        """
        
        # 실행 계획 확인
        explain_result = await session.execute(text(f"EXPLAIN QUERY PLAN {slow_query}"))
        
        for row in explain_result.fetchall():
            print(f"실행 계획: {row}")
        
        # 실제 실행 시간 측정
        start_time = time.time()
        result = await session.execute(text(slow_query))
        results = result.fetchall()
        end_time = time.time()
        
        print(f"쿼리 실행 시간: {end_time - start_time:.3f}s")
        print(f"결과 수: {len(results)}")
```

#### 최적화 방법

```python
# 캐시 시스템 구현
import redis
import json
from functools import wraps

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
    
    def cache_result(self, key_prefix: str, ttl: int = 3600):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 캐시 키 생성
                cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
                
                # 캐시에서 확인
                cached_result = self.redis_client.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)
                
                # 함수 실행 및 캐시 저장
                result = await func(*args, **kwargs)
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    json.dumps(result, default=str)
                )
                
                return result
            return wrapper
        return decorator

# 사용 예시
cache_manager = CacheManager()

@cache_manager.cache_result("daily_fortune", ttl=86400)  # 24시간 캐시
async def get_daily_fortune_cached(birth_date: str, zodiac: str):
    # 무거운 운세 생성 로직
    return await generate_fortune(birth_date, zodiac)

# 비동기 처리 최적화
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncOptimizer:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def run_in_thread(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    async def batch_process(self, items, process_func, batch_size: int = 10):
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_tasks = [process_func(item) for item in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results

# 메모리 사용량 최적화
import gc
import psutil
import os

def monitor_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    print(f"메모리 사용량: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"가상 메모리: {memory_info.vms / 1024 / 1024:.1f} MB")
    
    # 가비지 컬렉션 통계
    gc_stats = gc.get_stats()
    for i, stat in enumerate(gc_stats):
        print(f"GC Generation {i}: {stat}")

def optimize_memory():
    # 가비지 컬렉션 강제 실행
    collected = gc.collect()
    print(f"가비지 컬렉션 완료: {collected}개 객체 정리")
    
    # 메모리 사용량 다시 확인
    monitor_memory_usage()
```

## 🔒 보안 관련 문제

### 1. 콘텐츠 필터링 우회

#### 증상
- 부적절한 내용이 통과됨
- 필터가 너무 엄격함
- 정상 질문이 차단됨

#### 해결 방법

```python
# 콘텐츠 필터 개선
import re
from typing import List, Dict, Tuple

class AdvancedContentFilter:
    def __init__(self):
        self.blocked_patterns = [
            # 성적 내용
            r'(?i)(sex|sexual|porn|nude|naked)',
            # 폭력적 내용  
            r'(?i)(kill|murder|violence|suicide)',
            # 정치적 내용
            r'(?i)(president|election|political|government)',
            # 의료 조언
            r'(?i)(medical|doctor|treatment|medicine|drug)',
        ]
        
        self.context_patterns = [
            # 운세 관련 허용 패턴
            r'(?i)(fortune|tarot|zodiac|luck|future)',
            r'(?i)(love|relationship|romance|marriage)',
            r'(?i)(money|finance|wealth|success)',
        ]
        
        self.severity_weights = {
            'sexual_content': 1.0,
            'violence': 1.0,
            'political': 0.8,
            'medical_advice': 0.7,
            'spam': 0.5
        }
    
    async def advanced_filter(self, text: str) -> Dict:
        # 1. 기본 패턴 매칭
        blocked_matches = []
        for pattern in self.blocked_patterns:
            matches = re.findall(pattern, text)
            if matches:
                blocked_matches.extend(matches)
        
        # 2. 컨텍스트 분석
        context_score = self.analyze_context(text)
        
        # 3. 의도 분석
        intent_score = await self.analyze_intent(text)
        
        # 4. 종합 판단
        total_score = len(blocked_matches) * 0.4 + context_score * 0.3 + intent_score * 0.3
        
        is_blocked = total_score > 0.6
        
        return {
            'blocked': is_blocked,
            'confidence': min(total_score, 1.0),
            'matches': blocked_matches,
            'category': self.categorize_content(text),
            'reason': self.generate_reason(blocked_matches, context_score, intent_score) if is_blocked else None
        }
    
    def analyze_context(self, text: str) -> float:
        # 운세 관련 컨텍스트인지 확인
        fortune_keywords = len(re.findall(r'(?i)(운세|타로|별자리|점술)', text))
        question_keywords = len(re.findall(r'(?i)(어떨까|궁금|알려줘|봐줘)', text))
        
        if fortune_keywords > 0 or question_keywords > 0:
            return -0.3  # 컨텍스트 점수 감점
        return 0.0
    
    async def analyze_intent(self, text: str) -> float:
        # 간단한 의도 분석 (실제로는 ML 모델 사용)
        question_patterns = [
            r'(?i).*\?$',  # 물음표로 끝남
            r'(?i)^(what|how|when|where|why)',  # 의문사로 시작
            r'(?i)(어떻게|언제|어디서|왜|무엇)',  # 한국어 의문사
        ]
        
        is_question = any(re.search(pattern, text) for pattern in question_patterns)
        return -0.2 if is_question else 0.1
    
    def categorize_content(self, text: str) -> str:
        if re.search(r'(?i)(sex|sexual|porn)', text):
            return 'sexual_content'
        elif re.search(r'(?i)(kill|violence|murder)', text):
            return 'violence'
        elif re.search(r'(?i)(president|political)', text):
            return 'political'
        elif re.search(r'(?i)(medical|doctor|treatment)', text):
            return 'medical_advice'
        else:
            return 'other'
    
    def generate_reason(self, matches: List, context_score: float, intent_score: float) -> str:
        if matches:
            return f"부적절한 키워드가 감지되었습니다: {', '.join(matches)}"
        elif context_score > 0.5:
            return "운세와 관련 없는 내용입니다"
        elif intent_score > 0.5:
            return "질문 의도가 명확하지 않습니다"
        else:
            return "안전하지 않은 내용으로 판단됩니다"

# 화이트리스트 기반 필터
class WhitelistFilter:
    def __init__(self):
        self.allowed_topics = {
            'fortune': ['운세', '점술', '미래', '예측'],
            'love': ['연애', '사랑', '결혼', '관계'],
            'money': ['돈', '재물', '투자', '사업'],
            'health': ['건강', '몸', '병', '치료'],
            'work': ['직업', '일', '취업', '승진']
        }
        
        self.allowed_questions = [
            '어떨까요', '궁금해요', '알려주세요', '봐주세요',
            '좋을까요', '나쁠까요', '언제', '어디서'
        ]
    
    def is_allowed(self, text: str) -> bool:
        text_lower = text.lower()
        
        # 허용된 주제 확인
        topic_found = any(
            any(keyword in text_lower for keyword in keywords)
            for keywords in self.allowed_topics.values()
        )
        
        # 허용된 질문 형태 확인
        question_found = any(
            question in text_lower 
            for question in self.allowed_questions
        )
        
        return topic_found and question_found
```

### 2. Rate Limiting 우회

#### 해결 방법

```python
# 강화된 Rate Limiting
from collections import defaultdict
import time
import hashlib

class AdvancedRateLimiter:
    def __init__(self):
        self.request_logs = defaultdict(list)
        self.user_fingerprints = {}
        
        # 제한 규칙
        self.limits = {
            'api_requests': {'count': 60, 'window': 60},  # 분당 60회
            'fortune_requests': {'count': 10, 'window': 3600},  # 시간당 10회
            'websocket_messages': {'count': 30, 'window': 60},  # 분당 30회
            'session_creation': {'count': 5, 'window': 60}  # 분당 5회
        }
    
    def generate_fingerprint(self, request) -> str:
        # 사용자 지문 생성 (IP + User-Agent + 기타)
        components = [
            request.client.host,
            request.headers.get('user-agent', ''),
            request.headers.get('accept-language', ''),
            str(request.headers.get('screen-resolution', '')),
        ]
        
        fingerprint = hashlib.sha256('|'.join(components).encode()).hexdigest()[:16]
        return fingerprint
    
    def check_rate_limit(self, identifier: str, action_type: str) -> Tuple[bool, Dict]:
        current_time = time.time()
        limit_config = self.limits.get(action_type)
        
        if not limit_config:
            return True, {}
        
        # 해당 식별자의 요청 기록 정리 (윈도우 밖의 기록 제거)
        window_start = current_time - limit_config['window']
        self.request_logs[identifier] = [
            timestamp for timestamp in self.request_logs[identifier]
            if timestamp > window_start
        ]
        
        # 현재 윈도우 내 요청 수 확인
        current_requests = len(self.request_logs[identifier])
        
        if current_requests >= limit_config['count']:
            # 제한 초과
            return False, {
                'limit': limit_config['count'],
                'window': limit_config['window'],
                'current': current_requests,
                'reset_time': window_start + limit_config['window']
            }
        
        # 요청 기록 추가
        self.request_logs[identifier].append(current_time)
        
        return True, {
            'limit': limit_config['count'],
            'remaining': limit_config['count'] - current_requests - 1,
            'reset_time': window_start + limit_config['window']
        }
    
    def adaptive_rate_limit(self, identifier: str, user_behavior: Dict) -> Dict:
        # 사용자 행동 패턴에 따른 동적 제한
        base_limit = self.limits['api_requests']['count']
        
        # 정상 사용자 판단 요소
        trust_score = 0.0
        
        if user_behavior.get('session_duration', 0) > 300:  # 5분 이상
            trust_score += 0.3
        
        if user_behavior.get('human_like_intervals', False):  # 인간다운 요청 간격
            trust_score += 0.3
        
        if user_behavior.get('variety_in_requests', False):  # 다양한 요청
            trust_score += 0.2
        
        if user_behavior.get('realistic_content', False):  # 현실적인 질문
            trust_score += 0.2
        
        # 신뢰 점수에 따른 제한 조정
        if trust_score >= 0.8:
            adjusted_limit = int(base_limit * 1.5)  # 50% 증가
        elif trust_score >= 0.5:
            adjusted_limit = base_limit  # 기본 제한
        else:
            adjusted_limit = int(base_limit * 0.5)  # 50% 감소
        
        return {
            'trust_score': trust_score,
            'base_limit': base_limit,
            'adjusted_limit': adjusted_limit,
            'reasoning': self.get_trust_reasoning(user_behavior)
        }
```

## 🖥️ 프론트엔드 문제

### 1. React 컴포넌트 렌더링 문제

#### 증상
- 컴포넌트가 렌더링되지 않음
- 무한 리렌더링
- 상태 업데이트 실패

#### 해결 방법

```javascript
// React 디버깅 도구
const withErrorBoundary = (Component) => {
  return class extends React.Component {
    constructor(props) {
      super(props);
      this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
      return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
      console.error('컴포넌트 에러:', error, errorInfo);
      
      // 에러 리포팅
      if (window.Sentry) {
        window.Sentry.captureException(error, { extra: errorInfo });
      }
    }

    render() {
      if (this.state.hasError) {
        return (
          <div className="error-boundary">
            <h2>문제가 발생했습니다</h2>
            <details>
              <summary>에러 상세 정보</summary>
              <pre>{this.state.error?.toString()}</pre>
            </details>
            <button onClick={() => window.location.reload()}>
              페이지 새로고침
            </button>
          </div>
        );
      }

      return <Component {...this.props} />;
    }
  };
};

// 사용 예시
const SafeFortuneComponent = withErrorBoundary(FortuneComponent);

// 성능 최적화
import { memo, useMemo, useCallback, useState, useEffect } from 'react';

const OptimizedFortuneResult = memo(({ fortuneData, onUpdate }) => {
  // 비용이 큰 계산을 메모이제이션
  const processedData = useMemo(() => {
    if (!fortuneData) return null;
    
    return {
      ...fortuneData,
      formattedDate: new Date(fortuneData.date).toLocaleDateString('ko-KR'),
      categoryScores: Object.values(fortuneData.categories || {}).map(cat => cat.score),
      averageScore: Object.values(fortuneData.categories || {})
        .reduce((sum, cat) => sum + cat.score, 0) / 
        Object.keys(fortuneData.categories || {}).length
    };
  }, [fortuneData]);

  // 이벤트 핸들러 메모이제이션
  const handleShare = useCallback(() => {
    if (navigator.share) {
      navigator.share({
        title: '오늘의 운세',
        text: `오늘 운세 점수: ${processedData?.averageScore?.toFixed(0)}점`,
        url: window.location.href
      });
    }
  }, [processedData?.averageScore]);

  if (!processedData) {
    return <div>운세 데이터를 로딩 중...</div>;
  }

  return (
    <div className="fortune-result">
      <h3>{processedData.formattedDate} 운세</h3>
      <div className="overall-score">
        전체 점수: {processedData.averageScore.toFixed(0)}점
      </div>
      <button onClick={handleShare}>공유하기</button>
    </div>
  );
});

// 상태 관리 최적화
const useFortuneState = () => {
  const [fortune, setFortune] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchFortune = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/fortune/daily', {
        method: 'GET',
        headers: {
          'X-Session-ID': params.sessionId,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setFortune(data.data);
      
    } catch (err) {
      setError(err.message);
      console.error('운세 조회 실패:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return { fortune, loading, error, fetchFortune };
};
```

### 2. CSS 스타일링 문제

#### 해결 방법

```css
/* 반응형 디자인 개선 */
.fortune-app {
  /* 기본 레이아웃 */
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  
  /* 브라우저 호환성 */
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  
  /* 폴백 (그리드 미지원 브라우저) */
  display: flex;
  flex-wrap: wrap;
}

/* Live2D 캔버스 최적화 */
.live2d-container {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.live2d-canvas {
  width: 100%;
  height: 100%;
  object-fit: contain;
  
  /* 하드웨어 가속 */
  transform: translateZ(0);
  will-change: transform;
}

/* 로딩 애니메이션 */
.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 다크 모드 지원 */
@media (prefers-color-scheme: dark) {
  .fortune-app {
    background-color: #1a1a1a;
    color: #ffffff;
  }
  
  .card {
    background-color: #2d2d2d;
    border-color: #444;
  }
}

/* 모바일 최적화 */
@media (max-width: 768px) {
  .fortune-app {
    grid-template-columns: 1fr;
    padding: 10px;
  }
  
  .live2d-container {
    height: 300px;
  }
  
  /* 터치 친화적 버튼 */
  button {
    min-height: 44px;
    min-width: 44px;
    padding: 12px 16px;
  }
}

/* 접근성 개선 */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* 포커스 표시 */
button:focus,
input:focus {
  outline: 2px solid #4A90E2;
  outline-offset: 2px;
}

/* 고대비 모드 지원 */
@media (prefers-contrast: high) {
  .card {
    border: 2px solid currentColor;
  }
  
  button {
    border: 2px solid currentColor;
  }
}
```

## 🔍 진단 도구

### 시스템 진단 스크립트

```bash
#!/bin/bash
# comprehensive-diagnosis.sh

echo "🔍 Live2D 운세 앱 종합 진단 시작"
echo "=================================="

# 1. 시스템 정보
echo "📊 시스템 정보"
echo "OS: $(uname -a)"
echo "Python: $(python3 --version)"
echo "Node.js: $(node --version)"
echo "메모리: $(free -h | grep '^Mem' | awk '{print $2}')"
echo "디스크: $(df -h / | tail -1 | awk '{print $4}') 사용 가능"
echo ""

# 2. 서비스 상태
echo "🔧 서비스 상태"
services=("fortune-vtuber-backend" "nginx" "postgresql" "redis")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        echo "✅ $service: 실행 중"
    else
        echo "❌ $service: 중지됨"
    fi
done
echo ""

# 3. 포트 확인
echo "🌐 포트 상태"
ports=(8080 80 443 5432 6379)
for port in "${ports[@]}"; do
    if netstat -tlnp | grep -q ":$port "; then
        echo "✅ 포트 $port: 열림"
    else
        echo "❌ 포트 $port: 닫힘"
    fi
done
echo ""

# 4. API 엔드포인트 테스트
echo "🌍 API 엔드포인트 테스트"
endpoints=(
    "http://localhost:8080/health"
    "http://localhost:8080/api/v1/live2d/character/info"
)

for endpoint in "${endpoints[@]}"; do
    if curl -s -f "$endpoint" > /dev/null; then
        echo "✅ $endpoint: 응답 정상"
    else
        echo "❌ $endpoint: 응답 실패"
    fi
done
echo ""

# 5. 로그 에러 확인
echo "📝 최근 에러 로그"
if [ -f "/var/log/fortune-vtuber/app.log" ]; then
    error_count=$(grep -c "ERROR" /var/log/fortune-vtuber/app.log | tail -100)
    echo "최근 100라인 중 에러: $error_count개"
    
    if [ "$error_count" -gt 0 ]; then
        echo "최근 에러들:"
        grep "ERROR" /var/log/fortune-vtuber/app.log | tail -5
    fi
else
    echo "로그 파일을 찾을 수 없습니다"
fi
echo ""

# 6. 디스크 사용량
echo "💾 디스크 사용량"
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$disk_usage" -gt 85 ]; then
    echo "⚠️ 디스크 사용량: $disk_usage% (위험)"
else
    echo "✅ 디스크 사용량: $disk_usage% (정상)"
fi
echo ""

# 7. 메모리 사용량
echo "🧠 메모리 사용량"
memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
if (( $(echo "$memory_usage > 85" | bc -l) )); then
    echo "⚠️ 메모리 사용량: $memory_usage% (위험)"
else
    echo "✅ 메모리 사용량: $memory_usage% (정상)"
fi
echo ""

# 8. 권장 사항
echo "💡 권장 사항"
if [ "$disk_usage" -gt 80 ]; then
    echo "- 디스크 정리가 필요합니다"
fi
if (( $(echo "$memory_usage > 80" | bc -l) )); then
    echo "- 메모리 사용량을 확인하세요"
fi
if ! systemctl is-active --quiet fortune-vtuber-backend; then
    echo "- 백엔드 서비스를 시작하세요: sudo systemctl start fortune-vtuber-backend"
fi

echo "진단 완료! 문제가 지속되면 로그를 확인하세요."
```

### 자동 복구 스크립트

```bash
#!/bin/bash
# auto-recovery.sh

echo "🔧 자동 복구 시작"

# 1. 서비스 재시작
restart_service() {
    local service=$1
    echo "재시작 중: $service"
    
    if sudo systemctl restart "$service"; then
        echo "✅ $service 재시작 성공"
        return 0
    else
        echo "❌ $service 재시작 실패"
        return 1
    fi
}

# 2. 포트 해제
free_port() {
    local port=$1
    echo "포트 $port 해제 중..."
    
    local pid=$(sudo lsof -ti:$port)
    if [ -n "$pid" ]; then
        sudo kill -9 $pid
        echo "✅ 포트 $port 해제 완료"
    else
        echo "포트 $port는 이미 사용 가능합니다"
    fi
}

# 3. 로그 정리
cleanup_logs() {
    echo "로그 정리 중..."
    
    # 7일 이상된 로그 압축
    find /var/log/fortune-vtuber -name "*.log" -mtime +7 -exec gzip {} \;
    
    # 30일 이상된 압축 로그 삭제
    find /var/log/fortune-vtuber -name "*.gz" -mtime +30 -delete
    
    echo "✅ 로그 정리 완료"
}

# 4. 캐시 정리
clear_cache() {
    echo "캐시 정리 중..."
    
    # Redis 캐시 정리
    if systemctl is-active --quiet redis; then
        redis-cli FLUSHDB
        echo "✅ Redis 캐시 정리 완료"
    fi
    
    # 파일 시스템 캐시 정리
    echo 3 > /proc/sys/vm/drop_caches
    echo "✅ 파일 시스템 캐시 정리 완료"
}

# 복구 실행
if ! curl -s -f http://localhost:8080/health > /dev/null; then
    echo "백엔드 서비스에 문제가 있습니다. 복구를 시작합니다..."
    
    free_port 8080
    restart_service fortune-vtuber-backend
    
    # 10초 대기 후 재확인
    sleep 10
    
    if curl -s -f http://localhost:8080/health > /dev/null; then
        echo "✅ 백엔드 서비스 복구 완료"
    else
        echo "❌ 백엔드 서비스 복구 실패"
        exit 1
    fi
fi

# 정기 유지보수
cleanup_logs
clear_cache

echo "🎉 자동 복구 완료"
```

## 📞 지원 요청

### 지원 요청 전 체크리스트

```markdown
## 🚨 지원 요청 전 확인사항

### 기본 정보 수집
- [ ] 운영체제 및 버전
- [ ] Python 버전
- [ ] Node.js 버전  
- [ ] 에러 발생 시간
- [ ] 재현 가능 여부

### 로그 수집
- [ ] 백엔드 로그 (`/var/log/fortune-vtuber/app.log`)
- [ ] 시스템 로그 (`journalctl -u fortune-vtuber-backend`)
- [ ] 브라우저 콘솔 로그
- [ ] 네트워크 탭 로그

### 환경 정보
- [ ] 환경 변수 설정 (민감한 정보 제외)
- [ ] 데이터베이스 상태
- [ ] 네트워크 구성
- [ ] 방화벽 설정

### 재현 단계
1. 정확한 재현 단계 기록
2. 예상 결과 vs 실제 결과
3. 스크린샷 또는 동영상
```

### 지원 요청 양식

```markdown
## 🆘 지원 요청

**문제 제목**: [간단하고 명확한 제목]

**환경 정보**:
- OS: 
- Python 버전: 
- Node.js 버전:
- 브라우저: 

**문제 설명**:
[문제를 상세히 설명해주세요]

**재현 단계**:
1. 
2. 
3. 

**예상 결과**:
[어떤 결과를 기대했는지]

**실제 결과**:
[실제로 어떤 일이 일어났는지]

**에러 로그**:
```
[에러 로그를 여기에 붙여넣기]
```

**시도한 해결 방법**:
- [ ] 서비스 재시작
- [ ] 브라우저 캐시 삭제
- [ ] 다른 브라우저에서 테스트
- [ ] 진단 스크립트 실행

**스크린샷**:
[가능한 경우 스크린샷 첨부]

**추가 정보**:
[기타 도움이 될 수 있는 정보]
```

### 연락처

- **GitHub Issues**: [프로젝트 이슈 페이지](https://github.com/your-org/fortune-vtuber/issues)
- **이메일 지원**: support@fortune-vtuber.com
- **실시간 채팅**: [Discord 채널](https://discord.gg/fortune-vtuber)
- **문서**: [공식 문서 사이트](https://docs.fortune-vtuber.com)

### 우선순위 지침

| 우선순위 | 설명 | 응답 시간 |
|----------|------|-----------|
| **P0 - Critical** | 전체 서비스 중단 | 1시간 이내 |
| **P1 - High** | 핵심 기능 장애 | 4시간 이내 |
| **P2 - Medium** | 일부 기능 문제 | 24시간 이내 |
| **P3 - Low** | 개선 요청, 질문 | 48시간 이내 |

---

**문제 해결이 어려우시면 언제든지 연락주세요. 최대한 빠르게 도움을 드리겠습니다! 🤝**
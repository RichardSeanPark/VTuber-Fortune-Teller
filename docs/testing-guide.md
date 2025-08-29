# 🧪 Live2D 운세 앱 종합 테스트 가이드

> **최종 업데이트**: 2025년 8월 22일  
> **버전**: 1.0.0  
> **적용 범위**: 백엔드 + 프론트엔드 통합 테스트

## 📋 목차

1. [테스트 전략 개요](#테스트-전략-개요)
2. [테스트 환경 설정](#테스트-환경-설정)
3. [단위 테스트](#단위-테스트)
4. [통합 테스트](#통합-테스트)
5. [E2E 테스트](#e2e-테스트)
6. [성능 테스트](#성능-테스트)
7. [보안 테스트](#보안-테스트)
8. [테스트 자동화](#테스트-자동화)
9. [품질 게이트](#품질-게이트)
10. [문제 해결](#문제-해결)

## 🎯 테스트 전략 개요

### 테스트 피라미드

```
    /\
   /  \    E2E Tests (10%)
  /____\   - 전체 사용자 시나리오
 /      \  Integration Tests (30%)
/        \ - API + WebSocket + Live2D
\        / Unit Tests (60%)
 \______/  - 개별 컴포넌트
```

### 품질 목표

| 메트릭 | 목표값 | 측정 방법 |
|--------|--------|-----------|
| **코드 커버리지** | ≥80% | pytest-cov |
| **API 응답 시간** | <200ms (95th) | 성능 테스트 |
| **WebSocket 지연** | <100ms | 실시간 모니터링 |
| **보안 취약점** | 0개 (Critical/High) | 보안 스캔 |
| **장애 복구** | <30초 | 장애 시뮬레이션 |

### 테스트 우선순위

1. **Critical (P0)**: 운세 생성, 채팅 기능, 보안 필터링
2. **High (P1)**: Live2D 통합, 사용자 세션, 캐싱
3. **Medium (P2)**: 에러 처리, 로깅, 모니터링
4. **Low (P3)**: 성능 최적화, UX 개선

## 🛠️ 테스트 환경 설정

### 백엔드 테스트 환경

```bash
# 1. 가상환경 설정
cd project/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 테스트 의존성 설치
pip install -e ".[test]"

# 3. 테스트 데이터베이스 설정
export TEST_DATABASE_URL="sqlite:///./test_fortune_vtuber.db"
export ENVIRONMENT="testing"

# 4. 테스트 서버 실행
python -m pytest tests/ --setup-show
```

### 프론트엔드 테스트 환경

```bash
# 1. 의존성 설치
cd project/frontend
npm install

# 2. 테스트 환경 설정
echo "REACT_APP_API_BASE_URL=http://localhost:8080" > .env.test
echo "REACT_APP_WS_BASE_URL=ws://localhost:8080" >> .env.test

# 3. 테스트 실행
npm test
```

### Docker 테스트 환경

```yaml
# docker-compose.test.yml
version: '3.8'
services:
  backend-test:
    build: 
      context: ./backend
      dockerfile: Dockerfile.test
    environment:
      - ENVIRONMENT=testing
      - DATABASE_URL=sqlite:///./test.db
    ports:
      - "8081:8080"
    
  frontend-test:
    build:
      context: ./frontend
      dockerfile: Dockerfile.test
    environment:
      - REACT_APP_API_BASE_URL=http://backend-test:8080
    depends_on:
      - backend-test
```

## 🔬 단위 테스트

### 백엔드 단위 테스트

#### 1. 운세 엔진 테스트

```python
# tests/test_fortune_engines.py
import pytest
from datetime import date, datetime
from fortune_vtuber.fortune.engines import (
    DailyFortuneEngine,
    TarotEngine,
    ZodiacEngine,
    SajuEngine
)

class TestDailyFortuneEngine:
    @pytest.fixture
    def engine(self):
        return DailyFortuneEngine()
    
    @pytest.mark.asyncio
    async def test_generate_daily_fortune_basic(self, engine):
        """기본 일일 운세 생성 테스트"""
        result = await engine.generate_fortune(
            birth_date=date(1995, 3, 15),
            zodiac="pisces"
        )
        
        assert result is not None
        assert "overall_fortune" in result
        assert "categories" in result
        assert result["overall_fortune"]["score"] >= 0
        assert result["overall_fortune"]["score"] <= 100
        
        # 카테고리별 운세 검증
        categories = ["love", "money", "health", "work"]
        for category in categories:
            assert category in result["categories"]
            assert result["categories"][category]["score"] >= 0
            assert result["categories"][category]["score"] <= 100
    
    @pytest.mark.asyncio
    async def test_generate_fortune_with_invalid_zodiac(self, engine):
        """잘못된 별자리 입력 테스트"""
        with pytest.raises(ValueError):
            await engine.generate_fortune(
                birth_date=date(1995, 3, 15),
                zodiac="invalid_sign"
            )
    
    @pytest.mark.parametrize("zodiac,expected_traits", [
        ("aries", ["용감함", "도전적"]),
        ("pisces", ["감성적", "직관적"]),
        ("leo", ["자신감", "리더십"])
    ])
    async def test_zodiac_specific_traits(self, engine, zodiac, expected_traits):
        """별자리별 특성 반영 테스트"""
        result = await engine.generate_fortune(
            birth_date=date(1995, 3, 15),
            zodiac=zodiac
        )
        
        # 별자리 특성이 반영되었는지 확인
        description = result["overall_fortune"]["description"]
        assert any(trait in description for trait in expected_traits)

class TestTarotEngine:
    @pytest.fixture
    def engine(self):
        return TarotEngine()
    
    @pytest.mark.asyncio
    async def test_three_card_spread(self, engine):
        """3장 타로 스프레드 테스트"""
        result = await engine.generate_reading(
            question="연애운이 궁금해요",
            question_type="love"
        )
        
        assert len(result["cards"]) == 3
        positions = ["past", "present", "future"]
        
        for i, card in enumerate(result["cards"]):
            assert card["position"] == positions[i]
            assert "card_name" in card
            assert "interpretation" in card
            assert len(card["interpretation"]) > 10
    
    @pytest.mark.asyncio
    async def test_card_uniqueness(self, engine):
        """카드 중복 방지 테스트"""
        result = await engine.generate_reading(
            question="오늘 운세는?",
            question_type="general"
        )
        
        card_names = [card["card_name"] for card in result["cards"]]
        assert len(card_names) == len(set(card_names))  # 중복 없음

class TestContentFilter:
    @pytest.fixture
    def filter(self):
        from fortune_vtuber.security.content_filter import ContentFilter
        return ContentFilter()
    
    @pytest.mark.parametrize("input_text,should_block", [
        ("오늘 운세가 궁금해요", False),
        ("사랑하는 사람과 결혼할 수 있을까요?", False),
        ("섹스에 대해 알려주세요", True),
        ("누군가를 죽이고 싶어요", True),
        ("정치인 XXX에 대해 어떻게 생각해요?", True),
        ("의료 조언을 해주세요", True),
        ("투자 조언을 해주세요", True),
    ])
    async def test_content_filtering(self, filter, input_text, should_block):
        """콘텐츠 필터링 테스트"""
        result = await filter.filter_content(input_text)
        
        if should_block:
            assert result["blocked"] is True
            assert "reason" in result
        else:
            assert result["blocked"] is False
```

#### 2. 서비스 레이어 테스트

```python
# tests/test_services.py
import pytest
from unittest.mock import AsyncMock, Mock
from fortune_vtuber.services.fortune_service import FortuneService
from fortune_vtuber.services.chat_service import ChatService
from fortune_vtuber.services.live2d_service import Live2DService

class TestFortuneService:
    @pytest.fixture
    def fortune_service(self):
        return FortuneService()
    
    @pytest.mark.asyncio
    async def test_get_daily_fortune_cached(self, fortune_service):
        """캐시된 일일 운세 조회 테스트"""
        # 첫 번째 호출
        result1 = await fortune_service.get_daily_fortune(
            user_id="test_user",
            birth_date="1995-03-15",
            zodiac="pisces"
        )
        
        # 두 번째 호출 (캐시 사용)
        result2 = await fortune_service.get_daily_fortune(
            user_id="test_user",
            birth_date="1995-03-15",
            zodiac="pisces"
        )
        
        assert result1["data"]["overall_fortune"]["score"] == result2["data"]["overall_fortune"]["score"]
        # 캐시 히트 확인
        assert result2["metadata"]["cache_hit"] is True

class TestChatService:
    @pytest.fixture
    def chat_service(self):
        return ChatService()
    
    @pytest.mark.asyncio
    async def test_message_processing_pipeline(self, chat_service):
        """메시지 처리 파이프라인 테스트"""
        session_id = "test_session_123"
        message = "오늘 타로 카드 봐주세요"
        
        # 메시지 처리
        result = await chat_service.process_message(
            session_id=session_id,
            message=message,
            user_id="test_user"
        )
        
        assert result["success"] is True
        assert "response" in result["data"]
        assert "live2d_action" in result["data"]
        
        # 채팅 히스토리 저장 확인
        history = await chat_service.get_chat_history(session_id)
        assert len(history) >= 2  # 사용자 메시지 + 응답
```

#### 3. Live2D 통합 테스트

```python
# tests/test_live2d_integration.py
import pytest
from fortune_vtuber.live2d.emotion_mapping import EmotionMapper
from fortune_vtuber.services.live2d_service import Live2DService

class TestEmotionMapping:
    @pytest.fixture
    def emotion_mapper(self):
        return EmotionMapper()
    
    @pytest.mark.parametrize("fortune_type,expected_emotion", [
        ("daily", "neutral"),
        ("tarot", "mystical"),
        ("zodiac", "thoughtful"),
        ("saju", "serious")
    ])
    def test_fortune_type_emotion_mapping(self, emotion_mapper, fortune_type, expected_emotion):
        """운세 타입별 감정 매핑 테스트"""
        emotion = emotion_mapper.map_fortune_emotion(fortune_type, score=75)
        assert emotion in ["neutral", "mystical", "thoughtful", "serious"]
    
    @pytest.mark.parametrize("score,expected_emotion_type", [
        (90, "positive"),
        (50, "neutral"),
        (20, "concern")
    ])
    def test_score_based_emotion(self, emotion_mapper, score, expected_emotion_type):
        """점수 기반 감정 매핑 테스트"""
        emotion = emotion_mapper.map_score_emotion(score)
        emotion_config = emotion_mapper.get_emotion_config(emotion)
        assert emotion_config["type"] == expected_emotion_type

class TestLive2DService:
    @pytest.fixture
    def live2d_service(self):
        return Live2DService()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_actions(self, live2d_service):
        """Live2D 액션 포함 응답 생성 테스트"""
        result = await live2d_service.generate_response(
            message="타로 카드를 뽑아주세요",
            context={"fortune_type": "tarot"}
        )
        
        assert "text_response" in result
        assert "live2d_action" in result
        assert result["live2d_action"]["emotion"] in ["mystical", "thinking"]
        assert result["live2d_action"]["motion"] in ["card_draw", "thinking_pose"]
```

### 프론트엔드 단위 테스트

#### 1. React 컴포넌트 테스트

```javascript
// src/components/__tests__/FortuneSelector.test.js
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import FortuneSelector from '../FortuneSelector';

describe('FortuneSelector', () => {
  const mockOnSelect = jest.fn();
  
  beforeEach(() => {
    mockOnSelect.mockClear();
  });
  
  test('renders all fortune type options', () => {
    render(<FortuneSelector onSelect={mockOnSelect} />);
    
    expect(screen.getByText('일일 운세')).toBeInTheDocument();
    expect(screen.getByText('타로 카드')).toBeInTheDocument();
    expect(screen.getByText('별자리 운세')).toBeInTheDocument();
    expect(screen.getByText('사주 운세')).toBeInTheDocument();
  });
  
  test('calls onSelect when fortune type is selected', async () => {
    render(<FortuneSelector onSelect={mockOnSelect} />);
    
    const tarotButton = screen.getByText('타로 카드');
    fireEvent.click(tarotButton);
    
    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith('tarot');
    });
  });
  
  test('shows loading state during selection', async () => {
    render(<FortuneSelector onSelect={mockOnSelect} loading={true} />);
    
    expect(screen.getByText('운세를 준비하고 있어요...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });
});
```

#### 2. 서비스 클래스 테스트

```javascript
// src/services/__tests__/FortuneService.test.js
import FortuneService from '../FortuneService';

// API 모킹
global.fetch = jest.fn();

describe('FortuneService', () => {
  beforeEach(() => {
    fetch.mockClear();
  });
  
  test('getDailyFortune returns formatted fortune data', async () => {
    const mockResponse = {
      success: true,
      data: {
        overall_fortune: { score: 85, description: 'Great day!' },
        categories: {
          love: { score: 80, description: 'Love is in the air' }
        }
      }
    };
    
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse
    });
    
    const result = await FortuneService.getDailyFortune({
      birthDate: '1995-03-15',
      zodiac: 'pisces'
    });
    
    expect(result.overall_fortune.score).toBe(85);
    expect(result.categories.love.score).toBe(80);
  });
  
  test('handles API error gracefully', async () => {
    fetch.mockRejectedValueOnce(new Error('Network error'));
    
    await expect(
      FortuneService.getDailyFortune({ birthDate: '1995-03-15' })
    ).rejects.toThrow('Network error');
  });
});
```

## 🔗 통합 테스트

### API 통합 테스트

```python
# tests/integration/test_api_integration.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from fortune_vtuber.main import app

class TestFortuneAPIIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_daily_fortune_api_flow(self, client):
        """일일 운세 API 전체 플로우 테스트"""
        # 1. 사용자 세션 생성
        session_response = client.post("/api/v1/user/session")
        assert session_response.status_code == 201
        session_data = session_response.json()
        session_id = session_data["data"]["session_id"]
        
        # 2. 일일 운세 조회
        fortune_response = client.get(
            "/api/v1/fortune/daily",
            params={"birth_date": "1995-03-15", "zodiac": "pisces"},
            headers={"X-Session-ID": session_id}
        )
        assert fortune_response.status_code == 200
        fortune_data = fortune_response.json()
        
        # 운세 데이터 검증
        assert fortune_data["success"] is True
        assert "overall_fortune" in fortune_data["data"]
        assert fortune_data["data"]["overall_fortune"]["score"] >= 0
        
    def test_tarot_reading_flow(self, client):
        """타로 리딩 전체 플로우 테스트"""
        # 세션 생성
        session_response = client.post("/api/v1/user/session")
        session_id = session_response.json()["data"]["session_id"]
        
        # 타로 리딩 요청
        tarot_request = {
            "question": "이번 달 연애운은 어떨까요?",
            "question_type": "love",
            "user_info": {
                "birth_date": "1995-03-15",
                "zodiac": "pisces"
            }
        }
        
        tarot_response = client.post(
            "/api/v1/fortune/tarot",
            json=tarot_request,
            headers={"X-Session-ID": session_id}
        )
        
        assert tarot_response.status_code == 200
        tarot_data = tarot_response.json()
        
        # 타로 데이터 검증
        assert len(tarot_data["data"]["cards"]) == 3
        assert tarot_data["data"]["overall_interpretation"]
        assert tarot_data["data"]["live2d_emotion"] in ["mystical", "thinking"]
```

### WebSocket 통합 테스트

```python
# tests/integration/test_websocket_integration.py
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fortune_vtuber.main import app

class TestWebSocketIntegration:
    @pytest.mark.asyncio
    async def test_chat_websocket_flow(self):
        """채팅 WebSocket 전체 플로우 테스트"""
        with TestClient(app) as client:
            # 1. 세션 생성
            session_response = client.post("/api/v1/chat/session")
            session_id = session_response.json()["data"]["session_id"]
            
            # 2. WebSocket 연결
            with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
                # 3. 초기 메시지 수신
                initial_msg = websocket.receive_json()
                assert initial_msg["type"] == "connection_established"
                
                # 4. 텍스트 메시지 전송
                websocket.send_json({
                    "type": "text_input",
                    "data": {
                        "message": "오늘 운세 봐주세요",
                        "timestamp": "2025-08-22T10:30:00Z"
                    }
                })
                
                # 5. 응답 메시지들 수신
                messages = []
                for _ in range(3):  # Live2D 액션, 텍스트 응답, 운세 결과
                    msg = websocket.receive_json()
                    messages.append(msg)
                
                # 응답 검증
                msg_types = [msg["type"] for msg in messages]
                expected_types = ["live2d_action", "text_response", "fortune_result"]
                assert all(t in msg_types for t in expected_types)
    
    @pytest.mark.asyncio
    async def test_content_filtering_websocket(self):
        """WebSocket 콘텐츠 필터링 테스트"""
        with TestClient(app) as client:
            session_response = client.post("/api/v1/chat/session")
            session_id = session_response.json()["data"]["session_id"]
            
            with client.websocket_connect(f"/ws/chat/{session_id}") as websocket:
                # 필터링될 메시지 전송
                websocket.send_json({
                    "type": "text_input",
                    "data": {
                        "message": "성적인 내용의 메시지",
                        "timestamp": "2025-08-22T10:30:00Z"
                    }
                })
                
                # 에러 응답 수신
                error_msg = websocket.receive_json()
                assert error_msg["type"] == "error"
                assert error_msg["data"]["error_code"] == "CONTENT_FILTERED"
                assert error_msg["data"]["live2d_emotion"] == "concern"
```

### 데이터베이스 통합 테스트

```python
# tests/integration/test_database_integration.py
import pytest
import asyncio
from fortune_vtuber.config.database import get_db_session
from fortune_vtuber.repositories.user_repository import UserRepository
from fortune_vtuber.repositories.fortune_repository import FortuneRepository
from fortune_vtuber.repositories.chat_repository import ChatRepository

class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_user_session_lifecycle(self):
        """사용자 세션 생명주기 테스트"""
        async with get_db_session() as session:
            user_repo = UserRepository(session)
            
            # 1. 사용자 세션 생성
            user_session = await user_repo.create_session(
                user_agent="test-agent",
                ip_address="127.0.0.1"
            )
            assert user_session.session_id is not None
            
            # 2. 세션 조회
            retrieved_session = await user_repo.get_session(user_session.session_id)
            assert retrieved_session.session_id == user_session.session_id
            
            # 3. 세션 업데이트
            await user_repo.update_session_activity(user_session.session_id)
            
            # 4. 세션 만료
            await user_repo.expire_session(user_session.session_id)
            expired_session = await user_repo.get_session(user_session.session_id)
            assert expired_session.is_expired is True
    
    @pytest.mark.asyncio
    async def test_fortune_cache_integration(self):
        """운세 캐시 통합 테스트"""
        async with get_db_session() as session:
            fortune_repo = FortuneRepository(session)
            
            # 1. 운세 결과 저장
            fortune_data = {
                "overall_fortune": {"score": 85, "description": "Great day!"},
                "categories": {"love": {"score": 80}}
            }
            
            cache_key = await fortune_repo.cache_fortune_result(
                user_id="test_user",
                fortune_type="daily",
                cache_key="daily_2025-08-22",
                result=fortune_data
            )
            
            # 2. 캐시된 결과 조회
            cached_result = await fortune_repo.get_cached_fortune(cache_key)
            assert cached_result["overall_fortune"]["score"] == 85
            
            # 3. 캐시 만료 확인
            await asyncio.sleep(1)  # TTL 테스트를 위한 대기
            # TTL이 적용된 경우 None 반환 확인
```

## 🎭 E2E 테스트

### Playwright E2E 테스트

```javascript
// tests/e2e/fortune-flow.spec.js
import { test, expect } from '@playwright/test';

test.describe('Fortune App E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // 앱 접속
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
  });
  
  test('complete daily fortune flow', async ({ page }) => {
    // 1. 메인 페이지 로딩 확인
    await expect(page.locator('h1')).toContainText('운세 VTuber');
    
    // 2. Live2D 캐릭터 로딩 확인
    await expect(page.locator('#live2d-canvas')).toBeVisible();
    
    // 3. 일일 운세 선택
    await page.click('[data-testid="daily-fortune-button"]');
    
    // 4. 생년월일 입력
    await page.fill('[data-testid="birth-date-input"]', '1995-03-15');
    
    // 5. 별자리 선택
    await page.selectOption('[data-testid="zodiac-select"]', 'pisces');
    
    // 6. 운세 요청
    await page.click('[data-testid="get-fortune-button"]');
    
    // 7. 로딩 상태 확인
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    
    // 8. 운세 결과 표시 확인
    await expect(page.locator('[data-testid="fortune-result"]')).toBeVisible({ timeout: 10000 });
    
    // 9. Live2D 감정 변화 확인
    await expect(page.locator('#live2d-canvas')).toHaveAttribute('data-emotion');
    
    // 10. 운세 점수 확인
    const scoreElement = page.locator('[data-testid="fortune-score"]');
    await expect(scoreElement).toBeVisible();
    const score = await scoreElement.textContent();
    expect(parseInt(score)).toBeGreaterThanOrEqual(0);
    expect(parseInt(score)).toBeLessThanOrEqual(100);
  });
  
  test('tarot reading with chat interaction', async ({ page }) => {
    // 1. 타로 카드 선택
    await page.click('[data-testid="tarot-button"]');
    
    // 2. 질문 입력
    await page.fill('[data-testid="tarot-question"]', '이번 달 연애운은 어떨까요?');
    
    // 3. 카드 뽑기
    await page.click('[data-testid="draw-cards-button"]');
    
    // 4. 카드 뽑기 애니메이션 확인
    await expect(page.locator('[data-testid="card-drawing-animation"]')).toBeVisible();
    
    // 5. 3장의 카드 표시 확인
    await expect(page.locator('[data-testid="tarot-card"]')).toHaveCount(3);
    
    // 6. 각 카드의 해석 확인
    const cards = page.locator('[data-testid="tarot-card"]');
    for (let i = 0; i < 3; i++) {
      await expect(cards.nth(i).locator('[data-testid="card-interpretation"]')).toBeVisible();
    }
    
    // 7. 채팅으로 추가 질문
    await page.fill('[data-testid="chat-input"]', '더 자세히 설명해주세요');
    await page.press('[data-testid="chat-input"]', 'Enter');
    
    // 8. 채팅 응답 확인
    await expect(page.locator('[data-testid="chat-message"]:last-child')).toBeVisible({ timeout: 5000 });
  });
  
  test('responsive design across devices', async ({ page }) => {
    // 모바일 뷰포트 테스트
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:3000');
    
    // 모바일 레이아웃 확인
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="desktop-sidebar"]')).not.toBeVisible();
    
    // 태블릿 뷰포트 테스트
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();
    
    // 태블릿 레이아웃 확인
    await expect(page.locator('[data-testid="tablet-layout"]')).toBeVisible();
    
    // 데스크톱 뷰포트 테스트
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.reload();
    
    // 데스크톱 레이아웃 확인
    await expect(page.locator('[data-testid="desktop-sidebar"]')).toBeVisible();
  });
  
  test('accessibility compliance', async ({ page }) => {
    // 접근성 검사
    await page.goto('http://localhost:3000');
    
    // 키보드 탐색 테스트
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();
    
    // 스크린 리더 지원 확인
    await expect(page.locator('[aria-label]')).toHaveCount(6); // 최소 6개의 aria-label
    
    // 색상 대비 확인 (시각적 테스트)
    await expect(page.locator('body')).toHaveCSS('color', 'rgb(51, 51, 51)');
    
    // alt 텍스트 확인
    const images = page.locator('img');
    const imageCount = await images.count();
    for (let i = 0; i < imageCount; i++) {
      await expect(images.nth(i)).toHaveAttribute('alt');
    }
  });
});
```

### 성능 E2E 테스트

```javascript
// tests/e2e/performance.spec.js
import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('page load performance', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000); // 3초 이내 로딩
    
    // Core Web Vitals 측정
    const metrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const vitals = {};
          
          entries.forEach((entry) => {
            if (entry.name === 'largest-contentful-paint') {
              vitals.LCP = entry.value;
            }
            if (entry.name === 'first-input-delay') {
              vitals.FID = entry.value;
            }
            if (entry.name === 'cumulative-layout-shift') {
              vitals.CLS = entry.value;
            }
          });
          
          resolve(vitals);
        }).observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
        
        // 타임아웃 설정
        setTimeout(() => resolve({}), 5000);
      });
    });
    
    if (metrics.LCP) expect(metrics.LCP).toBeLessThan(2500); // LCP < 2.5s
    if (metrics.FID) expect(metrics.FID).toBeLessThan(100);  // FID < 100ms
    if (metrics.CLS) expect(metrics.CLS).toBeLessThan(0.1);  // CLS < 0.1
  });
  
  test('API response time', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // API 요청 모니터링
    const apiPromise = page.waitForResponse(response => 
      response.url().includes('/api/v1/fortune/daily') && response.status() === 200
    );
    
    const startTime = Date.now();
    await page.click('[data-testid="daily-fortune-button"]');
    await page.fill('[data-testid="birth-date-input"]', '1995-03-15');
    await page.click('[data-testid="get-fortune-button"]');
    
    const response = await apiPromise;
    const responseTime = Date.now() - startTime;
    
    expect(responseTime).toBeLessThan(2000); // 2초 이내 응답
    expect(response.status()).toBe(200);
  });
});
```

## ⚡ 성능 테스트

### 부하 테스트 (Locust)

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import json
import random
from datetime import date, timedelta

class FortuneAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """사용자 세션 시작 시 실행"""
        # 세션 생성
        response = self.client.post("/api/v1/user/session")
        if response.status_code == 201:
            self.session_id = response.json()["data"]["session_id"]
        else:
            self.session_id = None
    
    @task(3)
    def get_daily_fortune(self):
        """일일 운세 조회 (가중치: 3)"""
        if not self.session_id:
            return
            
        birth_date = self._random_birth_date()
        zodiac = random.choice([
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ])
        
        with self.client.get(
            "/api/v1/fortune/daily",
            params={"birth_date": birth_date, "zodiac": zodiac},
            headers={"X-Session-ID": self.session_id},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data["success"] and "overall_fortune" in data["data"]:
                    response.success()
                else:
                    response.failure("Invalid fortune data structure")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_tarot_reading(self):
        """타로 리딩 요청 (가중치: 2)"""
        if not self.session_id:
            return
            
        questions = [
            "오늘 연애운은 어떨까요?",
            "이번 주 금전운이 궁금해요",
            "새로운 일을 시작하기 좋은 시기인가요?",
            "건강 관리에 신경 써야 할 부분이 있나요?"
        ]
        
        tarot_request = {
            "question": random.choice(questions),
            "question_type": random.choice(["love", "money", "work", "health"]),
            "user_info": {
                "birth_date": self._random_birth_date(),
                "zodiac": random.choice(["aries", "pisces", "leo"])
            }
        }
        
        with self.client.post(
            "/api/v1/fortune/tarot",
            json=tarot_request,
            headers={"X-Session-ID": self.session_id},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data["success"] and len(data["data"]["cards"]) == 3:
                    response.success()
                else:
                    response.failure("Invalid tarot data structure")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_zodiac_fortune(self):
        """별자리 운세 조회 (가중치: 1)"""
        zodiac = random.choice([
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        ])
        
        with self.client.get(
            f"/api/v1/fortune/zodiac/{zodiac}",
            params={"period": random.choice(["daily", "weekly"])},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data["success"] and data["data"]["zodiac_sign"] == zodiac:
                    response.success()
                else:
                    response.failure("Invalid zodiac data")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    def _random_birth_date(self):
        """랜덤 생년월일 생성"""
        start_date = date(1970, 1, 1)
        end_date = date(2005, 12, 31)
        random_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days)
        )
        return random_date.strftime("%Y-%m-%d")

# 실행 명령어:
# locust -f tests/performance/locustfile.py --host=http://localhost:8080
```

### WebSocket 성능 테스트

```python
# tests/performance/websocket_load_test.py
import asyncio
import websockets
import json
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

class WebSocketLoadTest:
    def __init__(self, base_url="ws://localhost:8080"):
        self.base_url = base_url
        self.results = []
    
    async def single_user_simulation(self, user_id):
        """단일 사용자 시뮬레이션"""
        try:
            # 세션 생성 (HTTP 요청 필요 - 별도 구현)
            session_id = f"test_session_{user_id}"
            
            # WebSocket 연결
            uri = f"{self.base_url}/ws/chat/{session_id}"
            
            async with websockets.connect(uri) as websocket:
                start_time = time.time()
                
                # 메시지 전송
                message = {
                    "type": "text_input",
                    "data": {
                        "message": "오늘 운세 봐주세요",
                        "timestamp": "2025-08-22T10:30:00Z"
                    }
                }
                
                await websocket.send(json.dumps(message))
                
                # 응답 대기
                responses = []
                timeout = 10  # 10초 타임아웃
                
                try:
                    while time.time() - start_time < timeout:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1)
                        responses.append(json.loads(response))
                        
                        # 운세 결과 수신시 종료
                        if json.loads(response).get("type") == "fortune_result":
                            break
                            
                except asyncio.TimeoutError:
                    pass
                
                end_time = time.time()
                response_time = end_time - start_time
                
                self.results.append({
                    "user_id": user_id,
                    "response_time": response_time,
                    "responses_count": len(responses),
                    "success": len(responses) > 0
                })
                
        except Exception as e:
            self.results.append({
                "user_id": user_id,
                "response_time": None,
                "responses_count": 0,
                "success": False,
                "error": str(e)
            })
    
    async def run_load_test(self, concurrent_users=50, duration=60):
        """부하 테스트 실행"""
        print(f"WebSocket 부하 테스트 시작: {concurrent_users}명 동시 접속, {duration}초 진행")
        
        tasks = []
        for i in range(concurrent_users):
            task = asyncio.create_task(self.single_user_simulation(i))
            tasks.append(task)
            
            # 동시 연결 수 제한을 위한 딜레이
            if i % 10 == 9:
                await asyncio.sleep(0.1)
        
        # 모든 태스크 완료 대기
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 분석
        self.analyze_results()
    
    def analyze_results(self):
        """결과 분석 및 출력"""
        successful_tests = [r for r in self.results if r["success"]]
        failed_tests = [r for r in self.results if not r["success"]]
        
        if successful_tests:
            response_times = [r["response_time"] for r in successful_tests]
            
            print(f"\n=== WebSocket 성능 테스트 결과 ===")
            print(f"총 테스트: {len(self.results)}")
            print(f"성공: {len(successful_tests)} ({len(successful_tests)/len(self.results)*100:.1f}%)")
            print(f"실패: {len(failed_tests)} ({len(failed_tests)/len(self.results)*100:.1f}%)")
            print(f"\n응답 시간 통계:")
            print(f"  평균: {statistics.mean(response_times):.2f}초")
            print(f"  중간값: {statistics.median(response_times):.2f}초")
            print(f"  최소: {min(response_times):.2f}초")
            print(f"  최대: {max(response_times):.2f}초")
            print(f"  95th percentile: {statistics.quantiles(response_times, n=20)[18]:.2f}초")
            
            # 목표 성능 검증
            avg_response_time = statistics.mean(response_times)
            success_rate = len(successful_tests) / len(self.results)
            
            print(f"\n=== 성능 목표 달성 여부 ===")
            print(f"평균 응답 시간 < 5초: {'✅' if avg_response_time < 5 else '❌'} ({avg_response_time:.2f}초)")
            print(f"성공률 > 95%: {'✅' if success_rate > 0.95 else '❌'} ({success_rate*100:.1f}%)")
            
        else:
            print("모든 테스트가 실패했습니다.")
            
        # 실패 원인 분석
        if failed_tests:
            error_types = {}
            for test in failed_tests:
                error = test.get("error", "Unknown error")
                error_types[error] = error_types.get(error, 0) + 1
            
            print(f"\n=== 실패 원인 분석 ===")
            for error, count in error_types.items():
                print(f"  {error}: {count}회")

# 테스트 실행
async def main():
    load_test = WebSocketLoadTest()
    await load_test.run_load_test(concurrent_users=50, duration=60)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🛡️ 보안 테스트

### 콘텐츠 필터링 테스트

```python
# tests/security/test_content_filtering.py
import pytest
from fortune_vtuber.security.content_filter import ContentFilter

class TestContentFiltering:
    @pytest.fixture
    def content_filter(self):
        return ContentFilter()
    
    @pytest.mark.parametrize("input_text,expected_blocked,expected_category", [
        # 허용되는 내용
        ("오늘 운세가 궁금해요", False, None),
        ("연애운이 어떨까요?", False, None),
        ("금전운을 봐주세요", False, None),
        ("건강 상태가 걱정되어요", False, None),
        
        # 성적 내용
        ("섹스에 대해 알려주세요", True, "sexual_content"),
        ("야한 이야기 해주세요", True, "sexual_content"),
        ("성관계는 언제가 좋을까요?", True, "sexual_content"),
        
        # 폭력적 내용
        ("누군가를 죽이고 싶어요", True, "violence"),
        ("자살하는 방법을 알려주세요", True, "violence"),
        ("다른 사람을 해치고 싶어요", True, "violence"),
        
        # 정치적 내용
        ("대통령에 대해 어떻게 생각해요?", True, "political"),
        ("선거 결과를 예측해주세요", True, "political"),
        ("정당 추천해주세요", True, "political"),
        
        # 의료/법률 조언
        ("우울증 치료법을 알려주세요", True, "medical_advice"),
        ("이 약을 먹어도 될까요?", True, "medical_advice"),
        ("법적 문제를 해결하는 방법은?", True, "legal_advice"),
        
        # 금융 조언
        ("주식 투자 조언해주세요", True, "financial_advice"),
        ("비트코인 사야 할까요?", True, "financial_advice"),
        ("대출받는 방법을 알려주세요", True, "financial_advice"),
        
        # 개인정보 수집 시도
        ("당신의 실명을 알려주세요", True, "privacy_violation"),
        ("집 주소를 알려주세요", True, "privacy_violation"),
        ("신용카드 번호가 뭐예요?", True, "privacy_violation"),
        
        # 경계선 케이스
        ("사랑하는 사람과 결혼할 수 있을까요?", False, None),
        ("이번 주 건강 관리법을 알려주세요", False, None),
        ("돈 관리 운세를 봐주세요", False, None),
    ])
    async def test_content_filtering_comprehensive(self, content_filter, input_text, expected_blocked, expected_category):
        """포괄적 콘텐츠 필터링 테스트"""
        result = await content_filter.filter_content(input_text)
        
        assert result["blocked"] == expected_blocked
        
        if expected_blocked:
            assert result["category"] == expected_category
            assert "reason" in result
            assert len(result["reason"]) > 0
        else:
            assert result.get("category") is None
    
    @pytest.mark.asyncio
    async def test_filter_performance(self, content_filter):
        """필터링 성능 테스트"""
        import time
        
        test_messages = [
            "오늘 운세 봐주세요",
            "연애운이 궁금해요",
            "금전운은 어떨까요?",
            "건강운을 알려주세요",
            "이번 주 전체 운세는?"
        ] * 20  # 100개 메시지
        
        start_time = time.time()
        
        tasks = []
        for message in test_messages:
            task = content_filter.filter_content(message)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(test_messages)
        
        # 성능 기준: 평균 50ms 이내
        assert avg_time < 0.05, f"필터링 속도가 너무 느림: {avg_time*1000:.1f}ms"
        
        # 모든 허용 메시지가 통과되었는지 확인
        blocked_count = sum(1 for r in results if r["blocked"])
        assert blocked_count == 0, f"{blocked_count}개 메시지가 잘못 차단됨"
    
    @pytest.mark.asyncio
    async def test_multilingual_filtering(self, content_filter):
        """다국어 콘텐츠 필터링 테스트"""
        multilingual_tests = [
            # 영어
            ("Tell me about sex", True, "sexual_content"),
            ("What is my fortune today?", False, None),
            
            # 일본어
            ("今日の運勢を教えて", False, None),
            ("セックスについて教えて", True, "sexual_content"),
            
            # 중국어 (간체)
            ("今天的运势如何?", False, None),
            ("告诉我一些性的内容", True, "sexual_content"),
        ]
        
        for text, expected_blocked, expected_category in multilingual_tests:
            result = await content_filter.filter_content(text)
            assert result["blocked"] == expected_blocked
            if expected_blocked:
                assert result["category"] == expected_category
```

### 입력 검증 보안 테스트

```python
# tests/security/test_input_validation.py
import pytest
from httpx import AsyncClient
from fortune_vtuber.main import app

class TestInputValidation:
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self):
        """SQL Injection 공격 방어 테스트"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # SQL Injection 시도들
            sql_payloads = [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "'; INSERT INTO users (name) VALUES ('hacker'); --",
                "1' UNION SELECT * FROM users --",
                "'; DELETE FROM fortune_results; --"
            ]
            
            for payload in sql_payloads:
                # birth_date 파라미터에 SQL Injection 시도
                response = await client.get(
                    "/api/v1/fortune/daily",
                    params={"birth_date": payload, "zodiac": "aries"}
                )
                
                # 400 Bad Request이거나 정상적인 validation error 응답
                assert response.status_code in [400, 422]
                
                if response.status_code == 400:
                    error_data = response.json()
                    assert error_data["success"] is False
                    assert "VALIDATION_ERROR" in error_data["error"]["code"]
    
    @pytest.mark.asyncio
    async def test_xss_protection(self):
        """XSS 공격 방어 테스트"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            xss_payloads = [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//"
            ]
            
            # 세션 생성
            session_response = await client.post("/api/v1/user/session")
            session_id = session_response.json()["data"]["session_id"]
            
            for payload in xss_payloads:
                # 타로 질문에 XSS 페이로드 삽입 시도
                tarot_request = {
                    "question": payload,
                    "question_type": "general",
                    "user_info": {
                        "birth_date": "1995-03-15",
                        "zodiac": "aries"
                    }
                }
                
                response = await client.post(
                    "/api/v1/fortune/tarot",
                    json=tarot_request,
                    headers={"X-Session-ID": session_id}
                )
                
                if response.status_code == 200:
                    # 성공 응답인 경우 XSS 코드가 이스케이프되었는지 확인
                    response_data = response.json()
                    response_text = str(response_data)
                    
                    # 위험한 태그들이 이스케이프되었는지 확인
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
                    assert "<img" not in response_text or "onerror" not in response_text
    
    @pytest.mark.asyncio
    async def test_request_size_limits(self):
        """요청 크기 제한 테스트"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 매우 큰 요청 데이터 생성 (10MB 초과)
            large_question = "A" * (10 * 1024 * 1024 + 1)  # 10MB + 1바이트
            
            tarot_request = {
                "question": large_question,
                "question_type": "general",
                "user_info": {
                    "birth_date": "1995-03-15",
                    "zodiac": "aries"
                }
            }
            
            response = await client.post("/api/v1/fortune/tarot", json=tarot_request)
            
            # 413 Payload Too Large 또는 400 Bad Request 응답 확인
            assert response.status_code in [413, 400]
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Rate Limiting 테스트"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # 세션 생성
            session_response = await client.post("/api/v1/user/session")
            session_id = session_response.json()["data"]["session_id"]
            
            # 연속으로 많은 요청 전송 (분당 60회 제한 테스트)
            responses = []
            for i in range(65):  # 제한 초과 요청
                response = await client.get(
                    "/api/v1/fortune/daily",
                    params={"birth_date": "1995-03-15", "zodiac": "aries"},
                    headers={"X-Session-ID": session_id}
                )
                responses.append(response.status_code)
            
            # 일부 요청이 429 Too Many Requests로 차단되었는지 확인
            rate_limited_count = responses.count(429)
            assert rate_limited_count > 0, "Rate limiting이 작동하지 않음"
```

### 보안 헤더 테스트

```python
# tests/security/test_security_headers.py
import pytest
from httpx import AsyncClient
from fortune_vtuber.main import app

class TestSecurityHeaders:
    @pytest.mark.asyncio
    async def test_security_headers_present(self):
        """보안 헤더 존재 확인"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")
            
            # 필수 보안 헤더 확인
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'",
                "Referrer-Policy": "strict-origin-when-cross-origin"
            }
            
            for header, expected_value in security_headers.items():
                assert header in response.headers, f"보안 헤더 {header}가 누락됨"
                # 일부 헤더는 정확한 값까지 확인
                if header in ["X-Content-Type-Options", "X-Frame-Options"]:
                    assert response.headers[header] == expected_value
    
    @pytest.mark.asyncio
    async def test_cors_configuration(self):
        """CORS 설정 확인"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Preflight 요청
            response = await client.options(
                "/api/v1/fortune/daily",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
            )
            
            # CORS 헤더 확인
            assert "Access-Control-Allow-Origin" in response.headers
            assert "Access-Control-Allow-Methods" in response.headers
            assert "Access-Control-Allow-Headers" in response.headers
            
            # 허용되지 않은 origin 테스트
            response = await client.options(
                "/api/v1/fortune/daily",
                headers={
                    "Origin": "http://malicious-site.com",
                    "Access-Control-Request-Method": "GET"
                }
            )
            
            # malicious origin 차단 확인 (환경에 따라 다를 수 있음)
            allowed_origin = response.headers.get("Access-Control-Allow-Origin")
            assert allowed_origin != "http://malicious-site.com"
```

## 🤖 테스트 자동화

### GitHub Actions CI/CD

```yaml
# .github/workflows/test.yml
name: Comprehensive Testing

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.10, 3.11]
    
    services:
      sqlite:
        image: keinos/sqlite3:latest
        options: >-
          --health-cmd "sqlite3 --version"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        cd project/backend
        python -m pip install --upgrade pip
        pip install -e ".[test]"
    
    - name: Run linting
      run: |
        cd project/backend
        flake8 src tests
        black --check src tests
        isort --check-only src tests
    
    - name: Run type checking
      run: |
        cd project/backend
        mypy src
    
    - name: Run unit tests
      run: |
        cd project/backend
        pytest tests/unit -v --cov=src --cov-report=xml --cov-report=html
    
    - name: Run integration tests
      run: |
        cd project/backend
        pytest tests/integration -v
    
    - name: Run security tests
      run: |
        cd project/backend
        pytest tests/security -v
        bandit -r src/
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./project/backend/coverage.xml
        flags: backend
        name: backend-coverage
    
    - name: Generate test report
      if: always()
      run: |
        cd project/backend
        pytest --html=test-report.html --self-contained-html

  frontend-tests:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [18, 20]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
        cache-dependency-path: project/frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd project/frontend
        npm ci
    
    - name: Run linting
      run: |
        cd project/frontend
        npm run lint
    
    - name: Run type checking
      run: |
        cd project/frontend
        npm run type-check
    
    - name: Run unit tests
      run: |
        cd project/frontend
        npm test -- --coverage --watchAll=false
    
    - name: Build application
      run: |
        cd project/frontend
        npm run build
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./project/frontend/coverage/lcov.info
        flags: frontend
        name: frontend-coverage

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    services:
      backend:
        image: node:18
        ports:
          - 8080:8080
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: 18
        cache: 'npm'
        cache-dependency-path: project/frontend/package-lock.json
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Start backend server
      run: |
        cd project/backend
        pip install -e .
        python -m fortune_vtuber.main &
        sleep 10
    
    - name: Start frontend server
      run: |
        cd project/frontend
        npm ci
        npm start &
        sleep 15
    
    - name: Install Playwright
      run: |
        cd project/frontend
        npx playwright install --with-deps chromium
    
    - name: Run E2E tests
      run: |
        cd project/frontend
        npx playwright test
    
    - name: Upload E2E test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: e2e-test-results
        path: project/frontend/test-results/

  performance-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install Locust
      run: pip install locust
    
    - name: Start backend server
      run: |
        cd project/backend
        pip install -e .
        python -m fortune_vtuber.main &
        sleep 10
    
    - name: Run performance tests
      run: |
        cd project/backend
        locust -f tests/performance/locustfile.py --host=http://localhost:8080 \
               --users 50 --spawn-rate 5 --run-time 60s --headless \
               --html performance-report.html
    
    - name: Upload performance report
      uses: actions/upload-artifact@v3
      with:
        name: performance-report
        path: project/backend/performance-report.html

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Run OWASP ZAP scan
      uses: zaproxy/action-baseline@v0.7.0
      with:
        target: 'http://localhost:8080'
        rules_file_name: '.zap/rules.tsv'
        cmd_options: '-a'
```

### 테스트 결과 리포팅

```python
# tests/utils/test_reporter.py
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any

class TestReporter:
    def __init__(self, output_dir: str = "test-reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_results = {
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "error": 0
            },
            "categories": {
                "unit": {"passed": 0, "failed": 0, "duration": 0},
                "integration": {"passed": 0, "failed": 0, "duration": 0},
                "e2e": {"passed": 0, "failed": 0, "duration": 0},
                "security": {"passed": 0, "failed": 0, "duration": 0},
                "performance": {"passed": 0, "failed": 0, "duration": 0}
            },
            "coverage": {
                "line_coverage": 0,
                "branch_coverage": 0,
                "function_coverage": 0
            },
            "performance_metrics": {
                "api_response_time_p95": 0,
                "websocket_latency_avg": 0,
                "concurrent_users_max": 0,
                "throughput_rps": 0
            },
            "security_findings": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "timestamp": datetime.datetime.now().isoformat(),
            "test_details": []
        }
    
    def add_test_result(self, category: str, name: str, status: str, 
                       duration: float, details: Dict[str, Any] = None):
        """테스트 결과 추가"""
        self.test_results["summary"]["total"] += 1
        self.test_results["summary"][status] += 1
        
        if category in self.test_results["categories"]:
            self.test_results["categories"][category][status] += 1
            self.test_results["categories"][category]["duration"] += duration
        
        test_detail = {
            "category": category,
            "name": name,
            "status": status,
            "duration": duration,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        if details:
            test_detail.update(details)
        
        self.test_results["test_details"].append(test_detail)
    
    def update_coverage(self, line_coverage: float, branch_coverage: float = None, 
                       function_coverage: float = None):
        """커버리지 정보 업데이트"""
        self.test_results["coverage"]["line_coverage"] = line_coverage
        if branch_coverage:
            self.test_results["coverage"]["branch_coverage"] = branch_coverage
        if function_coverage:
            self.test_results["coverage"]["function_coverage"] = function_coverage
    
    def update_performance_metrics(self, metrics: Dict[str, float]):
        """성능 메트릭 업데이트"""
        self.test_results["performance_metrics"].update(metrics)
    
    def update_security_findings(self, findings: Dict[str, int]):
        """보안 취약점 결과 업데이트"""
        self.test_results["security_findings"].update(findings)
    
    def generate_json_report(self) -> str:
        """JSON 형식 리포트 생성"""
        report_file = self.output_dir / f"test-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        return str(report_file)
    
    def generate_html_report(self) -> str:
        """HTML 형식 리포트 생성"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Live2D 운세 앱 테스트 리포트</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .summary { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .metric { display: inline-block; margin: 10px; padding: 10px; border-radius: 4px; }
                .passed { background: #d4edda; color: #155724; }
                .failed { background: #f8d7da; color: #721c24; }
                .warning { background: #fff3cd; color: #856404; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .status-passed { color: #28a745; }
                .status-failed { color: #dc3545; }
                .status-skipped { color: #6c757d; }
            </style>
        </head>
        <body>
            <h1>🧪 Live2D 운세 앱 테스트 리포트</h1>
            
            <div class="summary">
                <h2>📊 테스트 요약</h2>
                <div class="metric passed">✅ 성공: {passed}</div>
                <div class="metric failed">❌ 실패: {failed}</div>
                <div class="metric warning">⏭️ 건너뜀: {skipped}</div>
                <div class="metric">📊 총 테스트: {total}</div>
                <div class="metric">📈 성공률: {success_rate:.1f}%</div>
            </div>
            
            <div class="summary">
                <h2>📋 카테고리별 결과</h2>
                <table>
                    <tr><th>카테고리</th><th>성공</th><th>실패</th><th>소요시간</th><th>성공률</th></tr>
                    {category_rows}
                </table>
            </div>
            
            <div class="summary">
                <h2>📊 커버리지</h2>
                <div class="metric">📏 라인 커버리지: {line_coverage:.1f}%</div>
                <div class="metric">🌿 브랜치 커버리지: {branch_coverage:.1f}%</div>
                <div class="metric">⚙️ 함수 커버리지: {function_coverage:.1f}%</div>
            </div>
            
            <div class="summary">
                <h2>⚡ 성능 메트릭</h2>
                <div class="metric">🚀 API 응답시간 (95th): {api_response_time_p95:.0f}ms</div>
                <div class="metric">🔗 WebSocket 지연: {websocket_latency_avg:.0f}ms</div>
                <div class="metric">👥 최대 동시 사용자: {concurrent_users_max}</div>
                <div class="metric">📈 처리량: {throughput_rps:.1f} RPS</div>
            </div>
            
            <div class="summary">
                <h2>🛡️ 보안 검사</h2>
                <div class="metric failed">🚨 치명적: {critical}</div>
                <div class="metric failed">⚠️ 높음: {high}</div>
                <div class="metric warning">⚠️ 보통: {medium}</div>
                <div class="metric">ℹ️ 낮음: {low}</div>
            </div>
            
            <h2>📝 상세 테스트 결과</h2>
            <table>
                <tr><th>카테고리</th><th>테스트명</th><th>상태</th><th>소요시간</th><th>실행시간</th></tr>
                {detail_rows}
            </table>
            
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                <p>리포트 생성 시간: {timestamp}</p>
                <p>Live2D 운세 앱 테스트 시스템 v1.0</p>
            </footer>
        </body>
        </html>
        """
        
        # 성공률 계산
        total = self.test_results["summary"]["total"]
        passed = self.test_results["summary"]["passed"]
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # 카테고리별 테이블 생성
        category_rows = ""
        for category, data in self.test_results["categories"].items():
            total_cat = data["passed"] + data["failed"]
            success_rate_cat = (data["passed"] / total_cat * 100) if total_cat > 0 else 0
            category_rows += f"""
                <tr>
                    <td>{category.title()}</td>
                    <td class="status-passed">{data["passed"]}</td>
                    <td class="status-failed">{data["failed"]}</td>
                    <td>{data["duration"]:.2f}s</td>
                    <td>{success_rate_cat:.1f}%</td>
                </tr>
            """
        
        # 상세 결과 테이블 생성
        detail_rows = ""
        for detail in self.test_results["test_details"]:
            status_class = f"status-{detail['status']}"
            detail_rows += f"""
                <tr>
                    <td>{detail['category'].title()}</td>
                    <td>{detail['name']}</td>
                    <td class="{status_class}">{detail['status'].title()}</td>
                    <td>{detail['duration']:.3f}s</td>
                    <td>{detail['timestamp']}</td>
                </tr>
            """
        
        # HTML 생성
        html_content = html_template.format(
            passed=passed,
            failed=self.test_results["summary"]["failed"],
            skipped=self.test_results["summary"]["skipped"],
            total=total,
            success_rate=success_rate,
            category_rows=category_rows,
            detail_rows=detail_rows,
            line_coverage=self.test_results["coverage"]["line_coverage"],
            branch_coverage=self.test_results["coverage"]["branch_coverage"],
            function_coverage=self.test_results["coverage"]["function_coverage"],
            api_response_time_p95=self.test_results["performance_metrics"]["api_response_time_p95"],
            websocket_latency_avg=self.test_results["performance_metrics"]["websocket_latency_avg"],
            concurrent_users_max=self.test_results["performance_metrics"]["concurrent_users_max"],
            throughput_rps=self.test_results["performance_metrics"]["throughput_rps"],
            critical=self.test_results["security_findings"]["critical"],
            high=self.test_results["security_findings"]["high"],
            medium=self.test_results["security_findings"]["medium"],
            low=self.test_results["security_findings"]["low"],
            timestamp=self.test_results["timestamp"]
        )
        
        report_file = self.output_dir / f"test-report-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)
```

## 🎯 품질 게이트

### 품질 기준 체크리스트

```markdown
## ✅ 배포 전 품질 게이트 체크리스트

### 📊 코드 품질
- [ ] 코드 커버리지 ≥ 80%
- [ ] 라인 커버리지 ≥ 85%
- [ ] 브랜치 커버리지 ≥ 75%
- [ ] 린팅 에러 0개
- [ ] 타입 체크 에러 0개
- [ ] 코드 스멜 0개 (SonarQube)

### 🧪 테스트 통과
- [ ] 단위 테스트 100% 통과
- [ ] 통합 테스트 100% 통과
- [ ] E2E 테스트 95% 이상 통과
- [ ] 보안 테스트 100% 통과
- [ ] 성능 테스트 기준 달성

### ⚡ 성능 기준
- [ ] API 응답 시간 95th percentile < 200ms
- [ ] WebSocket 평균 지연 < 100ms
- [ ] 동시 접속 100명 지원
- [ ] 메모리 사용량 < 512MB
- [ ] CPU 사용률 < 80%

### 🛡️ 보안 검증
- [ ] 치명적 취약점 0개
- [ ] 높은 수준 취약점 0개
- [ ] 콘텐츠 필터링 100% 작동
- [ ] 입력 검증 모든 케이스 통과
- [ ] 보안 헤더 모두 설정

### 📱 사용자 경험
- [ ] 모든 운세 타입 정상 작동
- [ ] Live2D 캐릭터 정상 렌더링
- [ ] 채팅 기능 정상 작동
- [ ] 모바일 반응형 완벽 지원
- [ ] 접근성 기준 AA 준수

### 🔧 운영 준비
- [ ] 로깅 시스템 정상 작동
- [ ] 모니터링 대시보드 설정
- [ ] 에러 추적 시스템 연동
- [ ] 백업 시스템 구축
- [ ] 장애 복구 계획 수립
```

### 자동화된 품질 게이트

```python
# tests/quality_gate.py
import asyncio
import subprocess
import json
import sys
from pathlib import Path

class QualityGate:
    def __init__(self):
        self.criteria = {
            "code_coverage": 80.0,
            "line_coverage": 85.0,
            "branch_coverage": 75.0,
            "api_response_time_p95": 200,  # ms
            "websocket_latency_avg": 100,  # ms
            "security_critical": 0,
            "security_high": 0,
            "test_success_rate": 95.0
        }
        
        self.results = {}
        self.passed = True
    
    async def run_quality_checks(self):
        """모든 품질 검사 실행"""
        print("🎯 품질 게이트 검사 시작...")
        
        # 1. 코드 품질 검사
        await self._check_code_quality()
        
        # 2. 테스트 결과 검사
        await self._check_test_results()
        
        # 3. 성능 검사
        await self._check_performance()
        
        # 4. 보안 검사
        await self._check_security()
        
        # 결과 출력
        self._print_results()
        
        return self.passed
    
    async def _check_code_quality(self):
        """코드 품질 검사"""
        print("📊 코드 품질 검사 중...")
        
        try:
            # 커버리지 리포트 파싱
            coverage_file = Path("project/backend/coverage.json")
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                
                total_coverage = coverage_data["totals"]["percent_covered"]
                self.results["code_coverage"] = total_coverage
                
                if total_coverage < self.criteria["code_coverage"]:
                    self.passed = False
                    print(f"❌ 코드 커버리지 부족: {total_coverage:.1f}% < {self.criteria['code_coverage']}%")
                else:
                    print(f"✅ 코드 커버리지: {total_coverage:.1f}%")
            
            # 린팅 검사
            lint_result = subprocess.run(
                ["flake8", "project/backend/src"],
                capture_output=True,
                text=True
            )
            
            if lint_result.returncode != 0:
                self.passed = False
                print(f"❌ 린팅 에러 발견:\n{lint_result.stdout}")
            else:
                print("✅ 린팅 검사 통과")
            
        except Exception as e:
            print(f"❌ 코드 품질 검사 실패: {e}")
            self.passed = False
    
    async def _check_test_results(self):
        """테스트 결과 검사"""
        print("🧪 테스트 결과 검사 중...")
        
        try:
            # pytest 결과 파싱 (JUnit XML)
            test_result = subprocess.run([
                "pytest", "project/backend/tests",
                "--junit-xml=test-results.xml",
                "-q"
            ], capture_output=True, text=True)
            
            if test_result.returncode != 0:
                self.passed = False
                print(f"❌ 테스트 실패:\n{test_result.stdout}")
            else:
                print("✅ 모든 테스트 통과")
                
        except Exception as e:
            print(f"❌ 테스트 검사 실패: {e}")
            self.passed = False
    
    async def _check_performance(self):
        """성능 검사"""
        print("⚡ 성능 검사 중...")
        
        try:
            # 성능 테스트 결과 파일 읽기
            perf_file = Path("performance-results.json")
            if perf_file.exists():
                with open(perf_file) as f:
                    perf_data = json.load(f)
                
                api_response_time = perf_data.get("api_response_time_p95", 0)
                websocket_latency = perf_data.get("websocket_latency_avg", 0)
                
                self.results["api_response_time_p95"] = api_response_time
                self.results["websocket_latency_avg"] = websocket_latency
                
                if api_response_time > self.criteria["api_response_time_p95"]:
                    self.passed = False
                    print(f"❌ API 응답 시간 기준 초과: {api_response_time}ms > {self.criteria['api_response_time_p95']}ms")
                else:
                    print(f"✅ API 응답 시간: {api_response_time}ms")
                
                if websocket_latency > self.criteria["websocket_latency_avg"]:
                    self.passed = False
                    print(f"❌ WebSocket 지연 기준 초과: {websocket_latency}ms > {self.criteria['websocket_latency_avg']}ms")
                else:
                    print(f"✅ WebSocket 지연: {websocket_latency}ms")
            
        except Exception as e:
            print(f"❌ 성능 검사 실패: {e}")
            self.passed = False
    
    async def _check_security(self):
        """보안 검사"""
        print("🛡️ 보안 검사 중...")
        
        try:
            # 보안 스캔 결과 파싱
            security_file = Path("security-results.json")
            if security_file.exists():
                with open(security_file) as f:
                    security_data = json.load(f)
                
                critical = security_data.get("critical", 0)
                high = security_data.get("high", 0)
                
                self.results["security_critical"] = critical
                self.results["security_high"] = high
                
                if critical > self.criteria["security_critical"]:
                    self.passed = False
                    print(f"❌ 치명적 보안 취약점 발견: {critical}개")
                
                if high > self.criteria["security_high"]:
                    self.passed = False
                    print(f"❌ 높은 수준 보안 취약점 발견: {high}개")
                
                if critical == 0 and high == 0:
                    print("✅ 보안 검사 통과")
            
        except Exception as e:
            print(f"❌ 보안 검사 실패: {e}")
            self.passed = False
    
    def _print_results(self):
        """최종 결과 출력"""
        print("\n" + "="*60)
        print("🎯 품질 게이트 최종 결과")
        print("="*60)
        
        if self.passed:
            print("✅ 모든 품질 기준을 만족합니다. 배포 가능합니다!")
        else:
            print("❌ 품질 기준을 만족하지 못했습니다. 수정 후 재검사해주세요.")
        
        print("\n📊 상세 결과:")
        for key, value in self.results.items():
            criterion = self.criteria.get(key, "N/A")
            status = "✅" if value <= criterion else "❌"
            print(f"  {status} {key}: {value} (기준: {criterion})")
        
        print("="*60)

# 실행
async def main():
    quality_gate = QualityGate()
    success = await quality_gate.run_quality_checks()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 문제 해결

### 일반적인 테스트 문제

| 문제 | 원인 | 해결방법 |
|------|------|----------|
| **테스트 데이터베이스 연결 실패** | 환경 변수 미설정 | `export TEST_DATABASE_URL="sqlite:///./test.db"` |
| **WebSocket 연결 타임아웃** | 서버 미실행 | 백엔드 서버 먼저 실행 |
| **E2E 테스트 실패** | 프론트엔드 빌드 오류 | `npm run build` 확인 |
| **성능 테스트 불안정** | 리소스 경합 | 테스트 격리, 순차 실행 |
| **보안 스캔 False Positive** | 설정 문제 | `.trivyignore` 파일 생성 |

### 테스트 환경 디버깅

```bash
# 백엔드 테스트 디버깅
cd project/backend
python -m pytest tests/ -v -s --tb=long --pdb

# 프론트엔드 테스트 디버깅
cd project/frontend
npm test -- --verbose --no-coverage

# WebSocket 연결 테스트
websocat ws://localhost:8080/ws/chat/test_session

# 데이터베이스 상태 확인
sqlite3 test_fortune_vtuber.db ".tables"

# 로그 확인
tail -f project/backend/logs/test.log
```

### 지속적 개선

1. **테스트 메트릭 추적**: 테스트 실행 시간, 성공률, 커버리지 변화 모니터링
2. **플레이키 테스트 관리**: 불안정한 테스트 식별 및 개선
3. **테스트 병렬화**: 테스트 실행 시간 단축
4. **테스트 데이터 관리**: 테스트 데이터 생성/정리 자동화
5. **피드백 루프**: 개발자 피드백 기반 테스트 개선

---

## 📚 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [FastAPI 테스팅 가이드](https://fastapi.tiangolo.com/tutorial/testing/)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Playwright 문서](https://playwright.dev/)
- [Locust 성능 테스트](https://locust.io/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

**테스트는 품질의 첫 번째 관문입니다. 철저한 테스트를 통해 안정적이고 신뢰할 수 있는 Live2D 운세 앱을 만들어보세요! 🚀**
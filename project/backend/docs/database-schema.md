# Live2D 운세 앱 데이터베이스 스키마 설계

## 1. 데이터베이스 아키텍처 개요

### 1.1 데이터베이스 전략
- **개발/테스트**: SQLite 사용 (파일 기반, 단순한 배포)
- **프로덕션**: MariaDB 마이그레이션 대비 호환성 확보
- **ORM**: SQLAlchemy를 통한 데이터베이스 추상화
- **마이그레이션**: Alembic을 통한 스키마 버전 관리

### 1.2 설계 원칙
- **정규화**: 3NF까지 정규화하여 중복 최소화
- **성능**: 적절한 인덱스와 외래 키 설계
- **확장성**: 향후 기능 추가에 대비한 유연한 구조
- **호환성**: SQLite와 MariaDB 간 호환성 보장
- **보안**: 민감 정보 암호화 및 접근 제어

## 2. 핵심 테이블 설계

### 2.1 사용자 관리 (Users)

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    uuid CHAR(36) UNIQUE NOT NULL,          -- 외부 노출용 UUID
    name VARCHAR(50),                        -- 사용자 이름
    birth_date DATE,                         -- 생년월일
    birth_time TIME,                         -- 출생 시간 (선택적)
    birth_location VARCHAR(100),             -- 출생 지역 (선택적)
    zodiac_sign ENUM('aries', 'taurus', 'gemini', 'cancer', 
                     'leo', 'virgo', 'libra', 'scorpio', 
                     'sagittarius', 'capricorn', 'aquarius', 'pisces'),
    preferences JSON,                        -- 사용자 설정 (JSON)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_uuid (uuid),
    INDEX idx_zodiac (zodiac_sign),
    INDEX idx_birth_date (birth_date),
    INDEX idx_last_active (last_active_at)
);
```

**SQLite 호환 버전:**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid TEXT UNIQUE NOT NULL,
    name TEXT,
    birth_date TEXT,                         -- DATE 형식: YYYY-MM-DD
    birth_time TEXT,                         -- TIME 형식: HH:MM:SS
    birth_location TEXT,
    zodiac_sign TEXT CHECK(zodiac_sign IN (
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    )),
    preferences TEXT,                        -- JSON 문자열
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_active_at TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX idx_users_uuid ON users(uuid);
CREATE INDEX idx_users_zodiac ON users(zodiac_sign);
CREATE INDEX idx_users_birth_date ON users(birth_date);
```

### 2.2 채팅 세션 (Chat Sessions)

```sql
CREATE TABLE chat_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id CHAR(36) UNIQUE NOT NULL,     -- 세션 UUID
    user_uuid CHAR(36),                      -- 사용자 UUID (선택적)
    character_name VARCHAR(50) DEFAULT '미라',
    session_type ENUM('anonymous', 'registered') DEFAULT 'anonymous',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    expires_at TIMESTAMP,                    -- 세션 만료 시간
    status ENUM('active', 'expired', 'closed') DEFAULT 'active',
    metadata JSON,                           -- 세션 메타데이터
    
    INDEX idx_session_id (session_id),
    INDEX idx_user_uuid (user_uuid),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    FOREIGN KEY (user_uuid) REFERENCES users(uuid) ON DELETE SET NULL
);
```

### 2.3 채팅 메시지 (Chat Messages)

```sql
CREATE TABLE chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    message_id CHAR(36) UNIQUE NOT NULL,     -- 메시지 UUID
    session_id CHAR(36) NOT NULL,            -- 세션 ID
    sender_type ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,                   -- 메시지 내용
    content_type ENUM('text', 'fortune_result', 'system') DEFAULT 'text',
    live2d_emotion VARCHAR(20),              -- Live2D 감정
    live2d_motion VARCHAR(50),               -- Live2D 모션
    audio_url VARCHAR(255),                  -- 음성 파일 URL
    metadata JSON,                           -- 추가 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    INDEX idx_message_id (message_id),
    INDEX idx_session_id (session_id),
    INDEX idx_sender_type (sender_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
```

### 2.4 운세 세션 (Fortune Sessions)

```sql
CREATE TABLE fortune_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    fortune_id CHAR(36) UNIQUE NOT NULL,     -- 운세 UUID
    session_id CHAR(36),                     -- 채팅 세션 ID (선택적)
    user_uuid CHAR(36),                      -- 사용자 UUID (선택적)
    fortune_type ENUM('daily', 'tarot', 'zodiac', 'oriental') NOT NULL,
    question TEXT,                           -- 사용자 질문 (타로의 경우)
    question_type ENUM('love', 'money', 'health', 'work', 'general'),
    result JSON NOT NULL,                    -- 운세 결과 (JSON)
    cached_until TIMESTAMP,                  -- 캐시 만료 시간
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_fortune_id (fortune_id),
    INDEX idx_session_id (session_id),
    INDEX idx_user_uuid (user_uuid),
    INDEX idx_fortune_type (fortune_type),
    INDEX idx_created_at (created_at),
    INDEX idx_cached_until (cached_until),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    FOREIGN KEY (user_uuid) REFERENCES users(uuid) ON DELETE SET NULL
);
```

### 2.5 타로 카드 마스터 (Tarot Cards)

```sql
CREATE TABLE tarot_cards (
    id INT PRIMARY KEY AUTO_INCREMENT,
    card_name VARCHAR(50) UNIQUE NOT NULL,   -- 카드 이름 (영문)
    card_name_ko VARCHAR(50) NOT NULL,       -- 카드 이름 (한글)
    card_number INT,                         -- 카드 번호
    suit ENUM('major', 'wands', 'cups', 'swords', 'pentacles'),
    upright_meaning TEXT,                    -- 정방향 의미
    reversed_meaning TEXT,                   -- 역방향 의미
    general_interpretation TEXT,             -- 일반적 해석
    love_interpretation TEXT,                -- 연애 관련 해석
    career_interpretation TEXT,              -- 직업 관련 해석
    health_interpretation TEXT,              -- 건강 관련 해석
    image_url VARCHAR(255),                  -- 카드 이미지 URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_card_name (card_name),
    INDEX idx_suit (suit)
);
```

### 2.6 별자리 정보 (Zodiac Info)

```sql
CREATE TABLE zodiac_info (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sign ENUM('aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
              'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces') UNIQUE,
    sign_ko VARCHAR(20) NOT NULL,            -- 한글 이름
    date_range VARCHAR(50),                  -- 날짜 범위
    element ENUM('fire', 'earth', 'air', 'water'),
    ruling_planet VARCHAR(20),               -- 지배 행성
    personality_traits JSON,                 -- 성격 특성
    strengths JSON,                          -- 장점
    weaknesses JSON,                         -- 단점
    compatible_signs JSON,                   -- 호환되는 별자리
    lucky_colors JSON,                       -- 행운의 색깔
    lucky_numbers JSON,                      -- 행운의 숫자
    
    INDEX idx_sign (sign),
    INDEX idx_element (element)
);
```

### 2.7 콘텐츠 캐시 (Content Cache)

```sql
CREATE TABLE content_cache (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cache_key VARCHAR(255) UNIQUE NOT NULL,  -- 캐시 키
    cache_type ENUM('daily_fortune', 'zodiac_weekly', 'zodiac_monthly', 'system') NOT NULL,
    content JSON NOT NULL,                   -- 캐시된 콘텐츠
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,           -- 만료 시간
    access_count INT DEFAULT 0,              -- 접근 횟수
    last_accessed_at TIMESTAMP,
    
    INDEX idx_cache_key (cache_key),
    INDEX idx_cache_type (cache_type),
    INDEX idx_expires_at (expires_at)
);
```

### 2.8 Live2D 모델 정보 (Live2D Models)

```sql
CREATE TABLE live2d_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    model_name VARCHAR(50) UNIQUE NOT NULL,  -- 모델 이름
    display_name VARCHAR(50) NOT NULL,       -- 표시 이름
    model_path VARCHAR(255) NOT NULL,        -- 모델 파일 경로
    emotions JSON NOT NULL,                  -- 감정 매핑
    motions JSON NOT NULL,                   -- 모션 매핑
    default_emotion VARCHAR(20) DEFAULT 'neutral',
    description TEXT,                        -- 모델 설명
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_model_name (model_name),
    INDEX idx_is_active (is_active)
);
```

### 2.9 시스템 설정 (System Settings)

```sql
CREATE TABLE system_settings (
    id INT PRIMARY KEY AUTO_INCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type ENUM('string', 'integer', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,         -- 클라이언트에 노출 가능 여부
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_setting_key (setting_key),
    INDEX idx_is_public (is_public)
);
```

### 2.10 사용자 통계 (User Analytics)

```sql
CREATE TABLE user_analytics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_uuid CHAR(36),                      -- 사용자 UUID (선택적)
    session_id CHAR(36),                     -- 세션 ID
    event_type ENUM('session_start', 'session_end', 'fortune_request', 
                    'message_sent', 'error_occurred') NOT NULL,
    event_data JSON,                         -- 이벤트 상세 데이터
    ip_address VARCHAR(45),                  -- IP 주소 (IPv6 지원)
    user_agent TEXT,                         -- User Agent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_uuid (user_uuid),
    INDEX idx_session_id (session_id),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_uuid) REFERENCES users(uuid) ON DELETE SET NULL,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
```

## 3. SQLAlchemy 모델 정의

### 3.1 Base 모델 클래스

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 3.2 User 모델

```python
class User(BaseModel):
    __tablename__ = 'users'
    
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    name = Column(String(50))
    birth_date = Column(String(10))  # YYYY-MM-DD format
    birth_time = Column(String(8))   # HH:MM:SS format
    birth_location = Column(String(100))
    zodiac_sign = Column(String(20))
    preferences = Column(JSON)
    last_active_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user")
    fortune_sessions = relationship("FortuneSession", back_populates="user")
```

### 3.3 ChatSession 모델

```python
class ChatSession(BaseModel):
    __tablename__ = 'chat_sessions'
    
    session_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_uuid = Column(String(36), ForeignKey('users.uuid'))
    character_name = Column(String(50), default='미라')
    session_type = Column(String(20), default='anonymous')
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    expires_at = Column(DateTime)
    status = Column(String(20), default='active')
    metadata = Column(JSON)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")
    fortune_sessions = relationship("FortuneSession", back_populates="chat_session")
```

### 3.4 ChatMessage 모델

```python
class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    
    message_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey('chat_sessions.session_id'), nullable=False)
    sender_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(20), default='text')
    live2d_emotion = Column(String(20))
    live2d_motion = Column(String(50))
    audio_url = Column(String(255))
    metadata = Column(JSON)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
```

## 4. 데이터 초기화 및 시드 데이터

### 4.1 타로 카드 기본 데이터

```python
TAROT_CARDS_SEED = [
    {
        "card_name": "The Fool",
        "card_name_ko": "바보",
        "card_number": 0,
        "suit": "major",
        "upright_meaning": "새로운 시작, 순수함, 자유로운 정신",
        "reversed_meaning": "무모함, 충동적 행동, 준비 부족",
        "general_interpretation": "새로운 여행이나 모험의 시작을 의미합니다.",
        "love_interpretation": "새로운 만남이나 순수한 사랑의 시작",
        "career_interpretation": "새로운 직업이나 프로젝트의 시작",
        "health_interpretation": "새로운 건강 습관이나 치료법 도입"
    },
    # ... 78장의 카드 데이터
]
```

### 4.2 별자리 기본 데이터

```python
ZODIAC_SEED = [
    {
        "sign": "aries",
        "sign_ko": "양자리",
        "date_range": "3월 21일 ~ 4월 19일",
        "element": "fire",
        "ruling_planet": "화성",
        "personality_traits": ["열정적", "리더십", "용감함", "독립적"],
        "strengths": ["결단력", "에너지", "낙관적"],
        "weaknesses": ["성급함", "충동적", "이기적"],
        "compatible_signs": ["leo", "sagittarius", "gemini", "aquarius"],
        "lucky_colors": ["빨간색", "주황색"],
        "lucky_numbers": [1, 8, 17]
    },
    # ... 12개 별자리 데이터
]
```

### 4.3 Live2D 모델 기본 데이터

```python
LIVE2D_MODEL_SEED = {
    "model_name": "mira",
    "display_name": "미라",
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
    },
    "default_emotion": "neutral",
    "description": "신비로운 운세 전문가 미라"
}
```

## 5. 데이터베이스 마이그레이션 전략

### 5.1 Alembic 설정

```python
# alembic/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from src.fortune_vtuber.models import Base

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### 5.2 SQLite → MariaDB 마이그레이션 고려사항

**데이터 타입 매핑:**
```python
# SQLite → MariaDB 타입 변환
TYPE_MAPPING = {
    'TEXT': 'VARCHAR(255)',
    'INTEGER': 'BIGINT',
    'REAL': 'DECIMAL(10,2)',
    'BLOB': 'LONGBLOB'
}
```

**제약 조건 호환성:**
- SQLite의 CHECK 제약 조건 → MariaDB ENUM
- JSON 컬럼 타입 호환성 확인
- 인덱스 및 외래 키 제약 조건 변환

## 6. 성능 최적화 전략

### 6.1 인덱스 최적화

```sql
-- 복합 인덱스
CREATE INDEX idx_fortune_sessions_user_type_date 
ON fortune_sessions(user_uuid, fortune_type, created_at);

-- 부분 인덱스 (MariaDB 8.0+)
CREATE INDEX idx_active_users ON users(uuid) WHERE is_active = 1;

-- JSON 인덱스 (MariaDB 10.3+)
CREATE INDEX idx_user_preferences_fortune_types 
ON users((CAST(JSON_EXTRACT(preferences, '$.fortune_types') AS CHAR(100))));
```

### 6.2 파티셔닝 전략 (프로덕션용)

```sql
-- 날짜 기반 파티셔닝
CREATE TABLE chat_messages_partitioned (
    -- 컬럼 정의 동일
) PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION pmax VALUES LESS THAN MAXVALUE
);
```

### 6.3 캐싱 전략

```python
# Redis 캐시 키 패턴
CACHE_KEYS = {
    'daily_fortune': 'fortune:daily:{zodiac}:{date}',
    'user_profile': 'user:profile:{uuid}',
    'tarot_cards': 'tarot:cards:all',
    'zodiac_info': 'zodiac:info:{sign}'
}

# TTL 설정
CACHE_TTL = {
    'daily_fortune': 86400,    # 24시간
    'user_profile': 3600,      # 1시간
    'tarot_cards': 604800,     # 1주일
    'zodiac_info': 604800      # 1주일
}
```

## 7. 보안 및 개인정보 보호

### 7.1 데이터 암호화

```python
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key):
        self.cipher = Fernet(key)
    
    def encrypt(self, value):
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value):
        return self.cipher.decrypt(encrypted_value.encode()).decode()
```

### 7.2 데이터 보관 정책

- **채팅 메시지**: 90일 후 자동 삭제
- **운세 기록**: 1년 후 익명화
- **사용자 분석 데이터**: 6개월 후 집계 데이터만 보관
- **개인정보**: 사용자 요청시 즉시 삭제

### 7.3 접근 제어

```sql
-- 사용자별 데이터 접근 제어
CREATE VIEW user_chat_messages AS
SELECT * FROM chat_messages 
WHERE session_id IN (
    SELECT session_id FROM chat_sessions 
    WHERE user_uuid = @current_user_uuid
);
```

이 데이터베이스 스키마 설계는 Live2D 운세 앱의 모든 기능을 지원하면서도 확장성과 성능을 고려한 구조로 설계되었습니다.
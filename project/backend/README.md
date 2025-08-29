# Fortune VTuber Backend

Live2D 기반 운세 VTuber 웹 어플리케이션의 백엔드 서비스입니다.

## 🚀 프로젝트 개요

이 프로젝트는 Live2D 캐릭터와 실시간으로 상호작용하며 다양한 운세 서비스를 제공하는 웹 어플리케이션의 백엔드입니다.

### 주요 기능
- 🎯 **일일 운세**: 개인화된 일일 운세 제공
- 🃏 **타로 카드**: 3장 스프레드 타로 리딩
- ⭐ **별자리 운세**: 12성좌별 맞춤 운세
- 🔮 **사주 기반 운세**: 생년월일시 기반 사주 해석
- 💬 **실시간 채팅**: WebSocket 기반 Live2D 캐릭터와의 대화
- 🛡️ **콘텐츠 필터링**: 다층 필터링을 통한 안전한 대화 환경

## 🏗️ 아키텍처

### 기술 스택
- **Framework**: FastAPI 0.115.8+
- **Database**: SQLite (개발), MariaDB (프로덕션 대비)
- **ORM**: SQLAlchemy 2.0+
- **Migration**: Alembic
- **Validation**: Pydantic 2.0+
- **WebSocket**: FastAPI WebSocket
- **Logging**: Loguru

### 프로젝트 구조
```
backend/
├── src/
│   └── fortune_vtuber/
│       ├── __init__.py
│       ├── main.py                    # FastAPI 애플리케이션 엔트리포인트
│       ├── config/
│       │   ├── __init__.py
│       │   ├── settings.py            # 설정 관리
│       │   └── database.py            # 데이터베이스 설정
│       ├── api/
│       │   ├── __init__.py
│       │   ├── v1/
│       │   │   ├── __init__.py
│       │   │   ├── fortune.py         # 운세 API 라우터
│       │   │   ├── user.py            # 사용자 API 라우터
│       │   │   ├── chat.py            # 채팅 API 라우터
│       │   │   └── websocket.py       # WebSocket 라우터
│       │   └── dependencies.py        # FastAPI 의존성
│       ├── models/
│       │   ├── __init__.py
│       │   ├── database.py            # SQLAlchemy 모델들
│       │   └── schemas.py             # Pydantic 스키마들
│       ├── services/
│       │   ├── __init__.py
│       │   ├── fortune/
│       │   │   ├── __init__.py
│       │   │   ├── daily.py           # 일일 운세 서비스
│       │   │   ├── tarot.py           # 타로 운세 서비스
│       │   │   ├── zodiac.py          # 별자리 운세 서비스
│       │   │   └── saju.py            # 사주 운세 서비스
│       │   ├── chat/
│       │   │   ├── __init__.py
│       │   │   ├── manager.py         # 채팅 세션 관리
│       │   │   └── websocket.py       # WebSocket 핸들러
│       │   ├── security/
│       │   │   ├── __init__.py
│       │   │   ├── filter.py          # 콘텐츠 필터링
│       │   │   ├── session.py         # 세션 관리
│       │   │   └── rate_limit.py      # Rate Limiting
│       │   └── live2d/
│       │       ├── __init__.py
│       │       ├── emotion.py         # 감정 매핑
│       │       └── motion.py          # 모션 제어
│       ├── core/
│       │   ├── __init__.py
│       │   ├── exceptions.py          # 커스텀 예외
│       │   ├── logging.py             # 로깅 설정
│       │   └── security.py            # 보안 유틸리티
│       └── utils/
│           ├── __init__.py
│           ├── cache.py               # 캐시 유틸리티
│           ├── datetime.py            # 날짜/시간 유틸리티
│           └── validators.py          # 검증 유틸리티
├── migrations/                        # Alembic 마이그레이션
├── tests/                            # 테스트 코드
├── docs/                             # 설계 문서
│   ├── api-design.md
│   ├── database-schema.md
│   └── security-architecture.md
├── scripts/                          # 유틸리티 스크립트
├── .env.example                      # 환경변수 예시
├── .gitignore
├── pyproject.toml                    # 프로젝트 설정
└── README.md
```

## 🚀 빠른 시작

### 요구사항
- Python 3.10 이상
- Poetry 또는 pip (의존성 관리)

### 설치 및 실행

1. **저장소 클론**
```bash
git clone <repository-url>
cd project/backend
```

2. **의존성 설치**
```bash
# Poetry 사용시
poetry install

# pip 사용시  
pip install -e .
```

3. **환경변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 설정값 입력
```

4. **데이터베이스 초기화**
```bash
# 마이그레이션 실행
alembic upgrade head

# 초기 데이터 로드 (선택적)
python scripts/init_data.py
```

5. **개발 서버 실행**
```bash
# 개발 모드
uvicorn fortune_vtuber.main:app --reload --host 0.0.0.0 --port 8080

# 또는
python -m fortune_vtuber.main
```

6. **API 문서 확인**
- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🧪 테스트

### 테스트 실행
```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src

# 특정 마커만 실행
pytest -m "not slow"
```

### 테스트 종류
- **Unit Tests**: 개별 컴포넌트 테스트
- **Integration Tests**: API 엔드포인트 테스트
- **Security Tests**: 보안 기능 테스트

## 📊 API 문서

### 주요 엔드포인트

#### 운세 API
- `GET /api/v1/fortune/daily` - 일일 운세 조회
- `POST /api/v1/fortune/tarot` - 타로 카드 리딩
- `GET /api/v1/fortune/zodiac/{sign}` - 별자리 운세
- `POST /api/v1/fortune/saju` - 사주 기반 운세

#### 사용자 API
- `POST /api/v1/user/session` - 세션 생성
- `GET /api/v1/user/profile` - 프로필 조회
- `PUT /api/v1/user/profile` - 프로필 업데이트

#### 채팅 API
- `GET /api/v1/chat/history` - 채팅 히스토리
- `WebSocket /ws/fortune` - 실시간 채팅

## 🔧 설정

### 환경변수
```bash
# 서버 설정
HOST=0.0.0.0
PORT=8080
DEBUG=True

# 데이터베이스
DATABASE_URL=sqlite:///./fortune_vtuber.db

# 보안
SECRET_KEY=your-secret-key-here
SESSION_TIMEOUT_HOURS=2

# 로깅
LOG_LEVEL=INFO
LOG_FILE=logs/fortune_vtuber.log

# 외부 서비스 (선택적)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## 🛡️ 보안

### 보안 기능
- **세션 기반 인증**: 익명 사용자 지원
- **Rate Limiting**: IP별, 사용자별 요청 제한
- **콘텐츠 필터링**: 다층 필터링 시스템
- **입력 검증**: Pydantic을 통한 데이터 검증
- **SQL Injection 방지**: SQLAlchemy ORM 사용
- **XSS 방지**: HTML 태그 이스케이핑

### 보안 정책
- 개인정보 수집 최소화
- 대화 내용 암호화 저장
- 정기적인 보안 감사
- 침입 탐지 및 로깅

## 📈 성능

### 성능 목표
- API 응답 시간: < 200ms (95th percentile)
- WebSocket 지연: < 100ms
- 동시 접속: 100명 지원
- 데이터베이스 쿼리: < 50ms

### 최적화 기법
- 운세 결과 캐싱 (24시간 TTL)
- 데이터베이스 인덱스 최적화
- 비동기 처리 (asyncio)
- SQLite WAL 모드

## 🚀 배포

### Docker 배포
```bash
# 이미지 빌드
docker build -t fortune-vtuber-backend .

# 컨테이너 실행
docker run -p 8080:8080 -e DATABASE_URL=sqlite:///./data/fortune_vtuber.db fortune-vtuber-backend
```

### 프로덕션 배포
```bash
# Gunicorn을 사용한 프로덕션 배포
gunicorn fortune_vtuber.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

- 문서: [API 문서](./docs/)
- 이슈: [GitHub Issues](https://github.com/your-org/fortune-vtuber-backend/issues)
- 이메일: dev@fortune-vtuber.com

---

**Fortune VTuber Backend** - Live2D 캐릭터와 함께하는 즐거운 운세 경험 🔮✨
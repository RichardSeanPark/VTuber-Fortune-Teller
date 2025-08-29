# 🚀 Live2D 운세 앱 배포 및 운영 가이드

> **최종 업데이트**: 2025년 8월 22일  
> **버전**: 1.0.0  
> **대상**: DevOps 엔지니어, 시스템 관리자, 프로덕션 운영팀

## 📋 목차

1. [배포 전 체크리스트](#배포-전-체크리스트)
2. [개발 환경 설정](#개발-환경-설정)
3. [스테이징 환경 배포](#스테이징-환경-배포)
4. [프로덕션 환경 배포](#프로덕션-환경-배포)
5. [Docker 컨테이너 배포](#docker-컨테이너-배포)
6. [로드 밸런싱 및 고가용성](#로드-밸런싱-및-고가용성)
7. [모니터링 및 로깅](#모니터링-및-로깅)
8. [백업 및 복구](#백업-및-복구)
9. [보안 설정](#보안-설정)
10. [성능 최적화](#성능-최적화)
11. [CI/CD 파이프라인](#cicd-파이프라인)
12. [장애 대응](#장애-대응)

## ✅ 배포 전 체크리스트

### 📊 코드 품질 검증
```bash
# 백엔드 품질 검사
cd project/backend
pytest tests/ --cov=src --cov-report=term-missing
flake8 src tests
mypy src
bandit -r src/

# 프론트엔드 품질 검사
cd project/frontend
npm test -- --coverage --watchAll=false
npm run lint
npm run type-check
npm run build
```

### 🔧 환경 설정 검증
```bash
# 환경 변수 확인
checklist=(
    "DATABASE_URL"
    "SECRET_KEY"
    "CORS_ORIGINS"
    "LOG_LEVEL"
    "RATE_LIMIT_PER_MINUTE"
    "SESSION_TIMEOUT_HOURS"
)

for var in "${checklist[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ $var 환경 변수가 설정되지 않았습니다"
        exit 1
    else
        echo "✅ $var 설정됨"
    fi
done
```

### 🛡️ 보안 설정 확인
```bash
# SSL 인증서 유효성 검사
openssl x509 -in /path/to/cert.pem -text -noout

# 방화벽 설정 확인
ufw status verbose

# 포트 검사
nmap -p 80,443,8080 localhost
```

### 📊 리소스 요구사항

| 환경 | CPU | 메모리 | 디스크 | 네트워크 |
|------|-----|--------|--------|----------|
| **개발** | 2 Core | 4GB | 20GB | 100Mbps |
| **스테이징** | 4 Core | 8GB | 50GB | 1Gbps |
| **프로덕션** | 8 Core | 16GB | 100GB | 10Gbps |

## 🔧 개발 환경 설정

### 로컬 개발 환경

```bash
#!/bin/bash
# setup-dev-environment.sh

echo "🔧 Live2D 운세 앱 개발 환경 설정 시작..."

# 1. 필수 도구 설치 확인
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1이 설치되지 않았습니다"
        exit 1
    else
        echo "✅ $1 설치됨"
    fi
}

echo "📦 필수 도구 확인 중..."
check_tool "python3"
check_tool "node"
check_tool "npm"
check_tool "git"
check_tool "docker"

# 2. Python 가상환경 설정
echo "🐍 Python 환경 설정 중..."
cd project/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"

# 3. 데이터베이스 초기화
echo "🗄️ 데이터베이스 초기화 중..."
export DATABASE_URL="sqlite:///./fortune_vtuber.db"
alembic upgrade head

# 4. 프론트엔드 의존성 설치
echo "📦 프론트엔드 의존성 설치 중..."
cd ../frontend
npm install

# 5. 환경 변수 파일 생성
echo "🔑 환경 변수 설정 중..."
cat > .env << EOF
# 서버 설정
HOST=0.0.0.0
PORT=8080
DEBUG=True
ENVIRONMENT=development

# 데이터베이스
DATABASE_URL=sqlite:///./fortune_vtuber.db

# 보안
SECRET_KEY=$(openssl rand -hex 32)
SESSION_TIMEOUT_HOURS=2

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# 로깅
LOG_LEVEL=DEBUG
LOG_FILE=logs/fortune_vtuber.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
FORTUNE_RATE_LIMIT_PER_HOUR=10

# Live2D
LIVE2D_MODEL_PATH=static/live2d/
LIVE2D_MOTION_FADE_TIME=0.5

# 캐시
CACHE_TYPE=memory
CACHE_TTL_SECONDS=3600
EOF

# 6. 개발 서버 시작 스크립트 생성
cat > start-dev.sh << 'EOF'
#!/bin/bash
echo "🚀 Live2D 운세 앱 개발 서버 시작..."

# 백엔드 서버 시작 (백그라운드)
cd project/backend
source venv/bin/activate
python -m fortune_vtuber.main &
BACKEND_PID=$!
echo "✅ 백엔드 서버 시작됨 (PID: $BACKEND_PID)"

# 프론트엔드 서버 시작 (백그라운드)
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "✅ 프론트엔드 서버 시작됨 (PID: $FRONTEND_PID)"

# 서버 상태 확인
sleep 5
if curl -s http://localhost:8080/health > /dev/null; then
    echo "✅ 백엔드 서버 정상 작동"
else
    echo "❌ 백엔드 서버 시작 실패"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ 프론트엔드 서버 정상 작동"
else
    echo "❌ 프론트엔드 서버 시작 실패"
fi

echo "🎉 개발 환경 준비 완료!"
echo "📱 프론트엔드: http://localhost:3000"
echo "🔧 백엔드 API: http://localhost:8080"
echo "📚 API 문서: http://localhost:8080/docs"

# 종료 시 프로세스 정리
trap "echo '정리 중...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF

chmod +x start-dev.sh

echo "🎉 개발 환경 설정 완료!"
echo "실행: ./start-dev.sh"
```

### VSCode 개발 환경 설정

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./project/backend/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["project/backend/tests"],
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "eslint.workingDirectories": ["project/frontend"],
  "typescript.preferences.importModuleSpecifier": "relative"
}
```

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI Backend",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/project/backend/src/fortune_vtuber/main.py",
      "env": {
        "ENVIRONMENT": "development",
        "DATABASE_URL": "sqlite:///./fortune_vtuber.db"
      },
      "cwd": "${workspaceFolder}/project/backend",
      "console": "integratedTerminal"
    },
    {
      "name": "Debug Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "cwd": "${workspaceFolder}/project/backend",
      "console": "integratedTerminal"
    }
  ]
}
```

## 🧪 스테이징 환경 배포

### 스테이징 서버 설정

```bash
#!/bin/bash
# deploy-staging.sh

echo "🧪 스테이징 환경 배포 시작..."

# 서버 정보
STAGING_HOST="staging.fortune-vtuber.com"
STAGING_USER="deploy"
DEPLOY_PATH="/opt/fortune-vtuber"

# 1. 코드 배포
echo "📦 코드 배포 중..."
rsync -avz --exclude-from='.deployignore' \
    ./ ${STAGING_USER}@${STAGING_HOST}:${DEPLOY_PATH}/

# 2. 원격 서버에서 배포 스크립트 실행
ssh ${STAGING_USER}@${STAGING_HOST} << 'EOF'
cd /opt/fortune-vtuber

# Python 환경 설정
python3 -m venv venv
source venv/bin/activate
pip install -e ./project/backend/

# 환경 변수 설정
cp .env.staging .env

# 데이터베이스 마이그레이션
cd project/backend
alembic upgrade head

# 프론트엔드 빌드
cd ../frontend
npm ci --production
npm run build

# 서비스 재시작
sudo systemctl restart fortune-vtuber-backend
sudo systemctl restart nginx

# 헬스 체크
sleep 10
curl -f http://localhost:8080/health || exit 1

echo "✅ 스테이징 배포 완료"
EOF
```

### 스테이징 환경 변수

```bash
# .env.staging
ENVIRONMENT=staging
DEBUG=False
HOST=0.0.0.0
PORT=8080

# 데이터베이스 (스테이징용 PostgreSQL)
DATABASE_URL=postgresql://staging_user:password@localhost:5432/fortune_vtuber_staging

# 보안
SECRET_KEY=${STAGING_SECRET_KEY}
SESSION_TIMEOUT_HOURS=1

# CORS
CORS_ORIGINS=["https://staging.fortune-vtuber.com"]

# 로깅
LOG_LEVEL=INFO
LOG_FILE=/var/log/fortune-vtuber/app.log

# SSL
SSL_CERT_PATH=/etc/ssl/certs/staging.fortune-vtuber.com.pem
SSL_KEY_PATH=/etc/ssl/private/staging.fortune-vtuber.com.key

# 외부 서비스 (스테이징 계정)
OPENAI_API_KEY=${STAGING_OPENAI_KEY}
ANTHROPIC_API_KEY=${STAGING_ANTHROPIC_KEY}

# 모니터링
SENTRY_DSN=${STAGING_SENTRY_DSN}
```

### Nginx 설정 (스테이징)

```nginx
# /etc/nginx/sites-available/staging.fortune-vtuber.com
server {
    listen 80;
    server_name staging.fortune-vtuber.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name staging.fortune-vtuber.com;

    # SSL 설정
    ssl_certificate /etc/ssl/certs/staging.fortune-vtuber.com.pem;
    ssl_certificate_key /etc/ssl/private/staging.fortune-vtuber.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # 보안 헤더
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # 프론트엔드 (React 빌드)
    location / {
        root /opt/fortune-vtuber/project/frontend/build;
        try_files $uri $uri/ /index.html;
        
        # 캐시 설정
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API 프록시
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket 프록시
    location /ws/ {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 정적 파일 (Live2D 모델 등)
    location /static/ {
        alias /opt/fortune-vtuber/project/backend/static/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # 로그 설정
    access_log /var/log/nginx/staging-fortune-vtuber-access.log;
    error_log /var/log/nginx/staging-fortune-vtuber-error.log;
}
```

## 🌟 프로덕션 환경 배포

### 프로덕션 배포 스크립트

```bash
#!/bin/bash
# deploy-production.sh

set -e  # 에러 발생시 즉시 종료

echo "🌟 프로덕션 환경 배포 시작..."

# 배포 전 확인사항
echo "⚠️  프로덕션 배포 전 확인사항:"
echo "1. 모든 테스트가 통과했나요? (y/n)"
read -r test_passed
if [[ $test_passed != "y" ]]; then
    echo "❌ 테스트를 먼저 통과해주세요"
    exit 1
fi

echo "2. 코드 리뷰가 완료되었나요? (y/n)"
read -r review_completed
if [[ $review_completed != "y" ]]; then
    echo "❌ 코드 리뷰를 먼저 완료해주세요"
    exit 1
fi

echo "3. 데이터베이스 백업이 완료되었나요? (y/n)"
read -r backup_completed
if [[ $backup_completed != "y" ]]; then
    echo "❌ 데이터베이스 백업을 먼저 완료해주세요"
    exit 1
fi

# 서버 정보
PROD_HOSTS=("prod1.fortune-vtuber.com" "prod2.fortune-vtuber.com")
PROD_USER="deploy"
DEPLOY_PATH="/opt/fortune-vtuber"
BACKUP_PATH="/opt/backups/fortune-vtuber"

# Git 태그 생성
echo "🏷️ 배포 태그 생성 중..."
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
TAG_NAME="release-${TIMESTAMP}"
git tag -a "$TAG_NAME" -m "Production release $TIMESTAMP"
git push origin "$TAG_NAME"

echo "📦 배포 패키지 생성 중..."
# 배포 파일 압축
tar -czf "fortune-vtuber-${TAG_NAME}.tar.gz" \
    --exclude-from='.deployignore' \
    project/ \
    .env.production \
    docker-compose.prod.yml \
    nginx.prod.conf

# Blue-Green 배포 전략
for HOST in "${PROD_HOSTS[@]}"; do
    echo "🚀 $HOST 서버 배포 중..."
    
    # 1. 새로운 버전 업로드
    scp "fortune-vtuber-${TAG_NAME}.tar.gz" ${PROD_USER}@${HOST}:${BACKUP_PATH}/
    
    # 2. 원격 서버에서 배포 실행
    ssh ${PROD_USER}@${HOST} << EOF
        set -e
        
        echo "📦 배포 패키지 압축 해제..."
        cd ${BACKUP_PATH}
        tar -xzf fortune-vtuber-${TAG_NAME}.tar.gz
        
        echo "🔄 서비스 중단 (Blue-Green 전환)..."
        sudo systemctl stop fortune-vtuber-backend-green || true
        
        echo "📁 기존 Green 환경 백업..."
        sudo rm -rf ${DEPLOY_PATH}-green-old
        sudo mv ${DEPLOY_PATH}-green ${DEPLOY_PATH}-green-old || true
        
        echo "📋 새로운 Green 환경 준비..."
        sudo mkdir -p ${DEPLOY_PATH}-green
        sudo cp -r project/ ${DEPLOY_PATH}-green/
        sudo cp .env.production ${DEPLOY_PATH}-green/.env
        sudo chown -R fortune-vtuber:fortune-vtuber ${DEPLOY_PATH}-green
        
        echo "🐍 Python 환경 설정..."
        cd ${DEPLOY_PATH}-green
        sudo -u fortune-vtuber python3 -m venv venv
        sudo -u fortune-vtuber ./venv/bin/pip install -e ./project/backend/
        
        echo "🗄️ 데이터베이스 마이그레이션..."
        cd project/backend
        sudo -u fortune-vtuber ../../venv/bin/alembic upgrade head
        
        echo "📦 프론트엔드 빌드..."
        cd ../frontend
        sudo -u fortune-vtuber npm ci --production
        sudo -u fortune-vtuber npm run build
        
        echo "🔄 Green 환경 시작..."
        sudo systemctl start fortune-vtuber-backend-green
        
        echo "🏥 헬스 체크..."
        sleep 15
        curl -f http://localhost:8081/health || {
            echo "❌ Green 환경 헬스 체크 실패, 롤백 중..."
            sudo systemctl stop fortune-vtuber-backend-green
            sudo systemctl start fortune-vtuber-backend-blue
            exit 1
        }
        
        echo "🔄 로드 밸런서 전환..."
        sudo systemctl reload nginx
        
        echo "🛑 Blue 환경 중단..."
        sleep 10  # 기존 연결 처리 대기
        sudo systemctl stop fortune-vtuber-backend-blue
        
        echo "🔄 Blue-Green 환경 교체..."
        sudo rm -rf ${DEPLOY_PATH}-blue-old
        sudo mv ${DEPLOY_PATH}-blue ${DEPLOY_PATH}-blue-old || true
        sudo mv ${DEPLOY_PATH}-green ${DEPLOY_PATH}-blue
        
        echo "✅ $HOST 배포 완료"
EOF

    echo "✅ $HOST 서버 배포 완료"
done

# 배포 후 검증
echo "🔍 배포 후 검증 중..."
for HOST in "${PROD_HOSTS[@]}"; do
    echo "검증 중: $HOST"
    
    # API 헬스 체크
    if curl -f "https://$HOST/health" &> /dev/null; then
        echo "✅ $HOST API 정상"
    else
        echo "❌ $HOST API 오류"
        exit 1
    fi
    
    # WebSocket 연결 테스트
    if timeout 5 websocat --close-code-message "wss://$HOST/ws/chat/test" &> /dev/null; then
        echo "✅ $HOST WebSocket 정상"
    else
        echo "⚠️ $HOST WebSocket 확인 필요"
    fi
done

# 배포 완료 알림
echo "🎉 프로덕션 배포 완료!"
echo "📊 배포 정보:"
echo "  - 태그: $TAG_NAME"
echo "  - 시간: $(date)"
echo "  - 서버: ${PROD_HOSTS[*]}"

# Slack/Discord 알림 (선택사항)
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"✅ Fortune VTuber 프로덕션 배포 완료\\n태그: $TAG_NAME\\n시간: $(date)\"}" \
    "$SLACK_WEBHOOK_URL" || true

echo "📚 롤백 명령어 (필요시):"
echo "  git checkout $TAG_NAME^"
echo "  ./rollback-production.sh $TAG_NAME"
```

### 프로덕션 환경 변수

```bash
# .env.production
ENVIRONMENT=production
DEBUG=False
HOST=0.0.0.0
PORT=8080

# 데이터베이스 (프로덕션 PostgreSQL)
DATABASE_URL=postgresql://prod_user:${DB_PASSWORD}@prod-db.fortune-vtuber.com:5432/fortune_vtuber_prod

# 보안
SECRET_KEY=${PROD_SECRET_KEY}
SESSION_TIMEOUT_HOURS=2

# CORS
CORS_ORIGINS=["https://fortune-vtuber.com", "https://www.fortune-vtuber.com"]

# 로깅
LOG_LEVEL=WARNING
LOG_FILE=/var/log/fortune-vtuber/app.log
SENTRY_DSN=${PROD_SENTRY_DSN}

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/fortune-vtuber.com.pem
SSL_KEY_PATH=/etc/ssl/private/fortune-vtuber.com.key

# Rate Limiting (프로덕션 강화)
RATE_LIMIT_PER_MINUTE=30
FORTUNE_RATE_LIMIT_PER_HOUR=5

# 캐시 (Redis)
CACHE_TYPE=redis
REDIS_URL=redis://prod-redis.fortune-vtuber.com:6379/0
CACHE_TTL_SECONDS=7200

# 외부 서비스
OPENAI_API_KEY=${PROD_OPENAI_KEY}
ANTHROPIC_API_KEY=${PROD_ANTHROPIC_KEY}

# CDN
CDN_BASE_URL=https://cdn.fortune-vtuber.com
LIVE2D_MODEL_CDN=${CDN_BASE_URL}/live2d/

# 모니터링
METRICS_ENABLED=True
PROMETHEUS_PORT=9090

# 백업
BACKUP_ENABLED=True
BACKUP_SCHEDULE="0 2 * * *"  # 매일 새벽 2시
BACKUP_RETENTION_DAYS=30
```

## 🐳 Docker 컨테이너 배포

### Docker Compose 설정

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./project/backend
      dockerfile: Dockerfile.prod
    image: fortune-vtuber/backend:${VERSION:-latest}
    container_name: fortune-vtuber-backend
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/fortune_vtuber
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    ports:
      - "8080:8080"
    depends_on:
      - db
      - redis
    volumes:
      - static_files:/app/static
      - ./logs:/app/logs
    networks:
      - fortune-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  frontend:
    build:
      context: ./project/frontend
      dockerfile: Dockerfile.prod
    image: fortune-vtuber/frontend:${VERSION:-latest}
    container_name: fortune-vtuber-frontend
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - static_files:/usr/share/nginx/html/static
      - ./ssl:/etc/ssl/certs
      - ./nginx.prod.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend
    networks:
      - fortune-network

  db:
    image: postgres:15-alpine
    container_name: fortune-vtuber-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=fortune_vtuber
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    networks:
      - fortune-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: fortune-vtuber-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - fortune-network
    healthcheck:
      test: ["CMD", "redis-cli", "auth", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  prometheus:
    image: prom/prometheus:latest
    container_name: fortune-vtuber-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - fortune-network

  grafana:
    image: grafana/grafana:latest
    container_name: fortune-vtuber-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - fortune-network

volumes:
  postgres_data:
  redis_data:
  static_files:
  prometheus_data:
  grafana_data:

networks:
  fortune-network:
    driver: bridge
```

### Backend Dockerfile

```dockerfile
# project/backend/Dockerfile.prod
FROM python:3.11-slim as builder

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir .

# 프로덕션 이미지
FROM python:3.11-slim

# 비루트 사용자 생성
RUN useradd --create-home --shell /bin/bash app

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# 정적 파일 디렉토리 생성
RUN mkdir -p static/live2d logs && \
    chown -R app:app /app

# 비루트 사용자로 전환
USER app

# 헬스체크 스크립트
COPY --chown=app:app healthcheck.sh /app/
RUN chmod +x /app/healthcheck.sh

# 포트 노출
EXPOSE 8080

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /app/healthcheck.sh

# 애플리케이션 시작
CMD ["python", "-m", "fortune_vtuber.main"]
```

### Frontend Dockerfile

```dockerfile
# project/frontend/Dockerfile.prod
# 빌드 스테이지
FROM node:18-alpine as builder

WORKDIR /app

# 의존성 설치
COPY package*.json ./
RUN npm ci --only=production

# 소스 코드 복사 및 빌드
COPY . .
RUN npm run build

# 프로덕션 스테이지
FROM nginx:alpine

# Nginx 설정 복사
COPY nginx.prod.conf /etc/nginx/nginx.conf

# 빌드된 애플리케이션 복사
COPY --from=builder /app/build /usr/share/nginx/html

# 정적 파일 권한 설정
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# 포트 노출
EXPOSE 80 443

# 헬스체크
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Nginx 시작
CMD ["nginx", "-g", "daemon off;"]
```

### Docker 배포 스크립트

```bash
#!/bin/bash
# deploy-docker.sh

set -e

echo "🐳 Docker 컨테이너 배포 시작..."

# 환경 변수 설정
export VERSION=$(git describe --tags --always)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export REDIS_PASSWORD=$(openssl rand -base64 32)
export GRAFANA_PASSWORD=$(openssl rand -base64 16)

# 환경 변수 저장
cat > .env.docker << EOF
VERSION=${VERSION}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
EOF

echo "📦 Docker 이미지 빌드 중..."
docker-compose -f docker-compose.prod.yml build

echo "🧪 컨테이너 헬스체크..."
docker-compose -f docker-compose.prod.yml up -d

# 서비스 시작 대기
echo "⏳ 서비스 시작 대기 중..."
sleep 30

# 헬스체크
services=("backend" "frontend" "db" "redis")
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.prod.yml ps $service | grep -q "Up (healthy)"; then
        echo "✅ $service 정상"
    else
        echo "❌ $service 오류"
        docker-compose -f docker-compose.prod.yml logs $service
        exit 1
    fi
done

echo "🎉 Docker 배포 완료!"
echo "📊 컨테이너 상태:"
docker-compose -f docker-compose.prod.yml ps

echo "📚 유용한 명령어:"
echo "  로그 확인: docker-compose -f docker-compose.prod.yml logs -f [service]"
echo "  재시작: docker-compose -f docker-compose.prod.yml restart [service]"
echo "  중지: docker-compose -f docker-compose.prod.yml down"
echo "  백업: docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres fortune_vtuber > backup.sql"
```

## ⚖️ 로드 밸런싱 및 고가용성

### HAProxy 설정

```haproxy
# /etc/haproxy/haproxy.cfg
global
    log stdout local0 info
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    mode http
    log global
    option httplog
    option dontlognull
    option log-health-checks
    option forwardfor
    option httpchk GET /health
    timeout connect 5000
    timeout client 50000
    timeout server 50000
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

# 프론트엔드 (HTTPS 터미네이션)
frontend fortune_vtuber_frontend
    bind *:443 ssl crt /etc/ssl/certs/fortune-vtuber.com.pem
    bind *:80
    redirect scheme https if !{ ssl_fc }
    
    # 보안 헤더
    http-response add-header X-Frame-Options DENY
    http-response add-header X-Content-Type-Options nosniff
    http-response add-header X-XSS-Protection "1; mode=block"
    http-response add-header Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    # API 라우팅
    acl is_api path_beg /api/
    acl is_ws path_beg /ws/
    acl is_static path_beg /static/
    
    use_backend fortune_vtuber_api if is_api
    use_backend fortune_vtuber_websocket if is_ws
    use_backend fortune_vtuber_static if is_static
    default_backend fortune_vtuber_web

# 웹 서버 백엔드
backend fortune_vtuber_web
    balance roundrobin
    option httpchk GET /
    server web1 10.0.1.10:80 check
    server web2 10.0.1.11:80 check

# API 서버 백엔드
backend fortune_vtuber_api
    balance leastconn
    option httpchk GET /health
    server api1 10.0.1.20:8080 check
    server api2 10.0.1.21:8080 check

# WebSocket 백엔드 (sticky sessions)
backend fortune_vtuber_websocket
    balance source
    option httpchk GET /health
    server ws1 10.0.1.20:8080 check
    server ws2 10.0.1.21:8080 check

# 정적 파일 백엔드
backend fortune_vtuber_static
    balance roundrobin
    option httpchk GET /health
    server static1 10.0.1.30:80 check
    server static2 10.0.1.31:80 check

# 통계 페이지
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
    stats admin if TRUE
```

### Keepalived 설정 (고가용성)

```bash
# /etc/keepalived/keepalived.conf (Master)
vrrp_script chk_haproxy {
    script "/bin/kill -0 `cat /var/run/haproxy.pid`"
    interval 2
    weight 2
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 101
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass fortune_ha_pass
    }
    virtual_ipaddress {
        10.0.1.100
    }
    track_script {
        chk_haproxy
    }
}
```

### 자동 장애조치 스크립트

```bash
#!/bin/bash
# failover-monitor.sh

LOG_FILE="/var/log/fortune-vtuber/failover.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

check_service_health() {
    local service_url=$1
    local service_name=$2
    
    if curl -f --connect-timeout 5 --max-time 10 "$service_url" &>/dev/null; then
        return 0
    else
        log_message "❌ $service_name 헬스체크 실패: $service_url"
        return 1
    fi
}

restart_service() {
    local service_name=$1
    log_message "🔄 $service_name 서비스 재시작 시도"
    
    if systemctl restart "$service_name"; then
        log_message "✅ $service_name 재시작 성공"
        return 0
    else
        log_message "❌ $service_name 재시작 실패"
        return 1
    fi
}

send_alert() {
    local message=$1
    
    # Slack 알림
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 Fortune VTuber 장애 알림: $message\"}" \
        "$SLACK_WEBHOOK_URL" &

    # 이메일 알림
    echo "$message" | mail -s "Fortune VTuber 장애 알림" "$ADMIN_EMAIL" &
    
    log_message "📢 알림 전송: $message"
}

# 메인 모니터링 루프
while true; do
    # API 서버 체크
    if ! check_service_health "http://localhost:8080/health" "API 서버"; then
        if ! restart_service "fortune-vtuber-backend"; then
            send_alert "API 서버 재시작 실패 - 즉시 확인 필요"
        fi
    fi
    
    # 웹 서버 체크
    if ! check_service_health "http://localhost/health" "웹 서버"; then
        if ! restart_service "nginx"; then
            send_alert "웹 서버 재시작 실패 - 즉시 확인 필요"
        fi
    fi
    
    # 데이터베이스 체크
    if ! pg_isready -h localhost -p 5432 -U postgres &>/dev/null; then
        log_message "❌ 데이터베이스 연결 실패"
        if ! restart_service "postgresql"; then
            send_alert "데이터베이스 재시작 실패 - 즉시 확인 필요"
        fi
    fi
    
    # Redis 체크
    if ! redis-cli ping &>/dev/null; then
        log_message "❌ Redis 연결 실패"
        if ! restart_service "redis"; then
            send_alert "Redis 재시작 실패 - 즉시 확인 필요"
        fi
    fi
    
    sleep 30
done
```

## 📊 모니터링 및 로깅

### Prometheus 설정

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # Fortune VTuber Backend
  - job_name: 'fortune-vtuber-backend'
    static_configs:
      - targets: ['backend:8080']
    metrics_path: /metrics
    scrape_interval: 5s

  # System Metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # PostgreSQL
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Nginx
  - job_name: 'nginx-exporter'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Grafana 대시보드 설정

```json
# monitoring/grafana/dashboards/fortune-vtuber-dashboard.json
{
  "dashboard": {
    "id": null,
    "title": "Fortune VTuber Monitoring",
    "tags": ["fortune-vtuber"],
    "timezone": "Asia/Seoul",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ],
        "yAxes": [
          {
            "label": "Response Time (seconds)",
            "min": 0
          }
        ]
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "id": 4,
        "title": "Active WebSocket Connections",
        "type": "stat",
        "targets": [
          {
            "expr": "websocket_connections_active",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "id": 5,
        "title": "Database Connection Pool",
        "type": "graph",
        "targets": [
          {
            "expr": "db_connections_active",
            "legendFormat": "Active"
          },
          {
            "expr": "db_connections_idle",
            "legendFormat": "Idle"
          }
        ]
      },
      {
        "id": 6,
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "process_resident_memory_bytes / 1024 / 1024",
            "legendFormat": "Memory Usage (MB)"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

### 로그 관리 설정

```yaml
# logging/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "fortune-vtuber-backend" {
    grok {
      match => { 
        "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{LOGLEVEL:level} - %{DATA:logger} - %{GREEDYDATA:message}"
      }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [level] == "ERROR" {
      mutate {
        add_tag => [ "error" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "fortune-vtuber-logs-%{+YYYY.MM.dd}"
  }
  
  if "error" in [tags] {
    slack {
      url => "${SLACK_WEBHOOK_URL}"
      channel => "#alerts"
      username => "LogAlert"
      icon_emoji => ":warning:"
      format => "에러 발생: %{message}"
    }
  }
}
```

### 커스텀 메트릭 수집

```python
# src/fortune_vtuber/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from functools import wraps

# 메트릭 정의
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'websocket_connections_active',
    'Active WebSocket connections'
)

FORTUNE_GENERATION_TIME = Histogram(
    'fortune_generation_duration_seconds',
    'Time spent generating fortune',
    ['fortune_type']
)

DATABASE_CONNECTIONS = Gauge(
    'db_connections_active',
    'Active database connections'
)

def track_request_metrics(func):
    """HTTP 요청 메트릭 데코레이터"""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        try:
            response = await func(request, *args, **kwargs)
            status = response.status_code
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status
            ).inc()
            
            return response
            
        except Exception as e:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=500
            ).inc()
            raise
            
        finally:
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)
    
    return wrapper

def track_fortune_generation(fortune_type: str):
    """운세 생성 시간 추적 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                FORTUNE_GENERATION_TIME.labels(
                    fortune_type=fortune_type
                ).observe(time.time() - start_time)
        return wrapper
    return decorator

class MetricsCollector:
    def __init__(self):
        self.websocket_connections = 0
    
    def websocket_connect(self):
        self.websocket_connections += 1
        ACTIVE_CONNECTIONS.set(self.websocket_connections)
    
    def websocket_disconnect(self):
        self.websocket_connections -= 1
        ACTIVE_CONNECTIONS.set(self.websocket_connections)
    
    def update_db_connections(self, active_count: int):
        DATABASE_CONNECTIONS.set(active_count)

# 메트릭 서버 시작
def start_metrics_server(port: int = 9090):
    start_http_server(port)
```

## 💾 백업 및 복구

### 자동화된 백업 시스템

```bash
#!/bin/bash
# backup-system.sh

set -e

# 설정
BACKUP_DIR="/opt/backups/fortune-vtuber"
RETENTION_DAYS=30
S3_BUCKET="fortune-vtuber-backups"
ENCRYPTION_KEY="/etc/backup-encryption.key"

# 로깅 함수
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/backup.log
}

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"/{database,files,config}

# 데이터베이스 백업
backup_database() {
    log "🗄️ 데이터베이스 백업 시작..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/database/fortune_vtuber_${timestamp}.sql"
    
    # PostgreSQL 덤프
    PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
        -h localhost \
        -U postgres \
        -d fortune_vtuber \
        --verbose \
        --no-owner \
        --no-privileges \
        > "$backup_file"
    
    # 압축 및 암호화
    gzip "$backup_file"
    gpg --symmetric --cipher-algo AES256 --batch --yes \
        --passphrase-file "$ENCRYPTION_KEY" \
        "${backup_file}.gz"
    
    rm "${backup_file}.gz"
    
    log "✅ 데이터베이스 백업 완료: ${backup_file}.gz.gpg"
    echo "${backup_file}.gz.gpg"
}

# 파일 시스템 백업
backup_files() {
    log "📁 파일 시스템 백업 시작..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/files/fortune_vtuber_files_${timestamp}.tar.gz"
    
    # 중요 파일들 백업
    tar -czf "$backup_file" \
        --exclude='*.log' \
        --exclude='*.tmp' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        /opt/fortune-vtuber/ \
        /etc/nginx/sites-available/fortune-vtuber.com \
        /etc/systemd/system/fortune-vtuber*.service
    
    # 암호화
    gpg --symmetric --cipher-algo AES256 --batch --yes \
        --passphrase-file "$ENCRYPTION_KEY" \
        "$backup_file"
    
    rm "$backup_file"
    
    log "✅ 파일 백업 완료: ${backup_file}.gpg"
    echo "${backup_file}.gpg"
}

# 설정 백업
backup_config() {
    log "⚙️ 설정 백업 시작..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/config/fortune_vtuber_config_${timestamp}.tar.gz"
    
    # 설정 파일들 백업
    tar -czf "$backup_file" \
        /opt/fortune-vtuber/.env.production \
        /etc/nginx/nginx.conf \
        /etc/ssl/certs/fortune-vtuber.com.* \
        /etc/haproxy/haproxy.cfg \
        /etc/keepalived/keepalived.conf \
        /etc/systemd/system/fortune-vtuber*.service
    
    # 암호화
    gpg --symmetric --cipher-algo AES256 --batch --yes \
        --passphrase-file "$ENCRYPTION_KEY" \
        "$backup_file"
    
    rm "$backup_file"
    
    log "✅ 설정 백업 완료: ${backup_file}.gpg"
    echo "${backup_file}.gpg"
}

# S3 업로드
upload_to_s3() {
    local file_path=$1
    local s3_key="backups/$(basename "$file_path")"
    
    log "☁️ S3 업로드 중: $file_path"
    
    if aws s3 cp "$file_path" "s3://$S3_BUCKET/$s3_key"; then
        log "✅ S3 업로드 완료: $s3_key"
    else
        log "❌ S3 업로드 실패: $s3_key"
        return 1
    fi
}

# 오래된 백업 정리
cleanup_old_backups() {
    log "🧹 오래된 백업 정리 중..."
    
    # 로컬 백업 정리
    find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
    
    # S3 백업 정리 (30일 이상된 파일)
    aws s3 ls "s3://$S3_BUCKET/backups/" --recursive | \
    while read -r line; do
        createDate=$(echo "$line" | awk '{print $1" "$2}')
        createDate=$(date -d "$createDate" +%s)
        olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
        
        if [[ $createDate -lt $olderThan ]]; then
            fileName=$(echo "$line" | awk '{print $4}')
            aws s3 rm "s3://$S3_BUCKET/$fileName"
            log "🗑️ 오래된 백업 삭제: $fileName"
        fi
    done
    
    log "✅ 백업 정리 완료"
}

# 백업 무결성 검증
verify_backup() {
    local backup_file=$1
    
    log "🔍 백업 무결성 검증 중: $backup_file"
    
    # GPG 파일 검증
    if gpg --quiet --batch --yes --passphrase-file "$ENCRYPTION_KEY" \
           --decrypt "$backup_file" > /dev/null 2>&1; then
        log "✅ 백업 파일 무결성 확인됨"
        return 0
    else
        log "❌ 백업 파일 손상됨: $backup_file"
        return 1
    fi
}

# 메인 백업 프로세스
main_backup() {
    log "🚀 백업 프로세스 시작..."
    
    # 백업 실행
    db_backup=$(backup_database)
    files_backup=$(backup_files)
    config_backup=$(backup_config)
    
    # 백업 검증
    verify_backup "$db_backup" || exit 1
    verify_backup "$files_backup" || exit 1
    verify_backup "$config_backup" || exit 1
    
    # S3 업로드
    upload_to_s3 "$db_backup"
    upload_to_s3 "$files_backup"
    upload_to_s3 "$config_backup"
    
    # 정리
    cleanup_old_backups
    
    log "🎉 백업 프로세스 완료"
    
    # 백업 성공 알림
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Fortune VTuber 백업 완료\\n시간: $(date)\\n파일: 3개\"}" \
        "$SLACK_WEBHOOK_URL" || true
}

# 복구 함수
restore_from_backup() {
    local backup_date=$1
    
    if [[ -z "$backup_date" ]]; then
        echo "사용법: $0 restore YYYYMMDD_HHMMSS"
        exit 1
    fi
    
    log "🔄 백업 복구 시작: $backup_date"
    
    # 서비스 중지
    systemctl stop fortune-vtuber-backend
    systemctl stop nginx
    
    # 데이터베이스 복구
    local db_backup="$BACKUP_DIR/database/fortune_vtuber_${backup_date}.sql.gz.gpg"
    
    if [[ -f "$db_backup" ]]; then
        log "🗄️ 데이터베이스 복구 중..."
        
        # 기존 데이터베이스 백업
        PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
            -h localhost -U postgres -d fortune_vtuber \
            > "$BACKUP_DIR/database/pre_restore_$(date +%Y%m%d_%H%M%S).sql"
        
        # 복구 실행
        gpg --quiet --batch --yes --passphrase-file "$ENCRYPTION_KEY" \
            --decrypt "$db_backup" | gunzip | \
            PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -U postgres -d fortune_vtuber
        
        log "✅ 데이터베이스 복구 완료"
    fi
    
    # 파일 시스템 복구
    local files_backup="$BACKUP_DIR/files/fortune_vtuber_files_${backup_date}.tar.gz.gpg"
    
    if [[ -f "$files_backup" ]]; then
        log "📁 파일 시스템 복구 중..."
        
        # 기존 파일 백업
        cp -r /opt/fortune-vtuber "/opt/fortune-vtuber.backup.$(date +%Y%m%d_%H%M%S)"
        
        # 복구 실행
        gpg --quiet --batch --yes --passphrase-file "$ENCRYPTION_KEY" \
            --decrypt "$files_backup" | tar -xzf - -C /
        
        log "✅ 파일 시스템 복구 완료"
    fi
    
    # 서비스 재시작
    systemctl start fortune-vtuber-backend
    systemctl start nginx
    
    # 헬스 체크
    sleep 10
    if curl -f http://localhost:8080/health; then
        log "✅ 복구 완료 및 서비스 정상"
    else
        log "❌ 복구 후 서비스 오류"
    fi
}

# 스크립트 실행
case "${1:-backup}" in
    "backup")
        main_backup
        ;;
    "restore")
        restore_from_backup "$2"
        ;;
    *)
        echo "사용법: $0 [backup|restore] [backup_date]"
        exit 1
        ;;
esac
```

### 백업 스케줄링

```bash
# /etc/cron.d/fortune-vtuber-backup
# 매일 새벽 2시 전체 백업
0 2 * * * root /opt/scripts/backup-system.sh backup

# 매시간 데이터베이스 백업 (증분)
0 * * * * root /opt/scripts/backup-system.sh backup_database_incremental

# 매주 일요일 백업 검증
0 3 * * 0 root /opt/scripts/verify-all-backups.sh
```

## 🛡️ 보안 설정

### SSL/TLS 설정

```bash
#!/bin/bash
# setup-ssl.sh

# Let's Encrypt 인증서 설치
install_letsencrypt() {
    # Certbot 설치
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    
    # 인증서 발급
    certbot --nginx -d fortune-vtuber.com -d www.fortune-vtuber.com \
        --email admin@fortune-vtuber.com \
        --agree-tos \
        --non-interactive \
        --redirect
    
    # 자동 갱신 설정
    cat > /etc/cron.d/certbot << EOF
# Let's Encrypt 인증서 자동 갱신
0 12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF
}

# 커스텀 SSL 인증서 설정
setup_custom_ssl() {
    local cert_file="/etc/ssl/certs/fortune-vtuber.com.pem"
    local key_file="/etc/ssl/private/fortune-vtuber.com.key"
    
    # 인증서 권한 설정
    chmod 644 "$cert_file"
    chmod 600 "$key_file"
    chown root:ssl-cert "$key_file"
    
    # 인증서 유효성 검증
    openssl x509 -in "$cert_file" -text -noout
    openssl rsa -in "$key_file" -check
    
    # Nginx 설정 테스트
    nginx -t
}

# SSL 보안 강화
harden_ssl() {
    # DHE 파라미터 생성
    openssl dhparam -out /etc/ssl/certs/dhparam.pem 4096
    
    # SSL 설정 파일 생성
    cat > /etc/nginx/snippets/ssl-params.conf << EOF
# SSL 보안 설정
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;
ssl_dhparam /etc/ssl/certs/dhparam.pem;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
}

# 실행
if [[ "$1" == "letsencrypt" ]]; then
    install_letsencrypt
elif [[ "$1" == "custom" ]]; then
    setup_custom_ssl
fi

harden_ssl
systemctl reload nginx
```

### 방화벽 설정

```bash
#!/bin/bash
# setup-firewall.sh

# UFW 초기화
ufw --force reset

# 기본 정책
ufw default deny incoming
ufw default allow outgoing

# SSH (관리용)
ufw allow 22/tcp comment 'SSH'

# HTTP/HTTPS (웹 서비스)
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# Prometheus (모니터링 - 내부 네트워크만)
ufw allow from 10.0.1.0/24 to any port 9090 comment 'Prometheus'

# PostgreSQL (내부 네트워크만)
ufw allow from 10.0.1.0/24 to any port 5432 comment 'PostgreSQL'

# Redis (내부 네트워크만)
ufw allow from 10.0.1.0/24 to any port 6379 comment 'Redis'

# Rate limiting (SSH brute force 방지)
ufw limit ssh comment 'SSH rate limiting'

# 로깅 활성화
ufw logging on

# 방화벽 활성화
ufw --force enable

# 상태 확인
ufw status verbose

# Fail2ban 설정
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true

[nginx-badbots]
enabled = true

[nginx-noproxy]
enabled = true
EOF

systemctl enable fail2ban
systemctl restart fail2ban
```

### 시스템 보안 강화

```bash
#!/bin/bash
# harden-system.sh

# 커널 파라미터 보안 설정
cat > /etc/sysctl.d/99-security.conf << EOF
# IP Spoofing 방지
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# ICMP redirect 차단
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# Source routed packets 차단
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Log Martians
net.ipv4.conf.all.log_martians = 1

# ICMP ping 차단 (선택사항)
# net.ipv4.icmp_echo_ignore_all = 1

# SYN flood 공격 방어
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 5

# IP forwarding 비활성화 (라우터가 아닌 경우)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0
EOF

sysctl -p

# 불필요한 서비스 비활성화
services_to_disable=(
    "telnet"
    "ftp"
    "rsh"
    "rlogin"
    "tftp"
    "bluetooth"
    "avahi-daemon"
)

for service in "${services_to_disable[@]}"; do
    systemctl disable "$service" 2>/dev/null || true
    systemctl stop "$service" 2>/dev/null || true
done

# 파일 권한 설정
chmod 700 /root
chmod 600 /etc/ssh/sshd_config
chmod 644 /etc/passwd
chmod 640 /etc/shadow
chmod 644 /etc/group

# SSH 보안 강화
cat > /etc/ssh/sshd_config.d/99-security.conf << EOF
# SSH 보안 설정
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxStartups 10:30:60
ClientAliveInterval 300
ClientAliveCountMax 0
AllowUsers deploy
EOF

# 자동 보안 업데이트 활성화
apt-get install -y unattended-upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

systemctl enable unattended-upgrades
systemctl restart sshd
```

## ⚡ 성능 최적화

### 시스템 성능 튜닝

```bash
#!/bin/bash
# performance-tuning.sh

# 시스템 리소스 한계 설정
cat > /etc/security/limits.d/99-fortune-vtuber.conf << EOF
# Fortune VTuber 애플리케이션 한계 설정
fortune-vtuber soft nofile 65536
fortune-vtuber hard nofile 65536
fortune-vtuber soft nproc 4096
fortune-vtuber hard nproc 4096

# 모든 사용자 기본 한계
* soft nofile 32768
* hard nofile 65536
EOF

# 커널 네트워크 파라미터 최적화
cat > /etc/sysctl.d/99-performance.conf << EOF
# 네트워크 성능 최적화
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 16384 16777216
net.ipv4.tcp_wmem = 4096 16384 16777216

# TCP 연결 최적화
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0

# 소켓 백로그 증가
net.core.somaxconn = 32768
net.core.netdev_max_backlog = 5000

# 파일 시스템 최적화
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.swappiness = 10
EOF

sysctl -p

# PostgreSQL 성능 튜닝
optimize_postgresql() {
    local pg_config="/etc/postgresql/15/main/postgresql.conf"
    
    # 메모리 설정 (시스템 RAM의 25%)
    local total_ram=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    local shared_buffers=$((total_ram / 4))
    local effective_cache_size=$((total_ram * 3 / 4))
    
    cat >> "$pg_config" << EOF

# Fortune VTuber 성능 최적화
shared_buffers = ${shared_buffers}MB
effective_cache_size = ${effective_cache_size}MB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200

# 로깅 최적화
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

# 연결 설정
max_connections = 200
EOF

    systemctl restart postgresql
}

# Redis 성능 튜닝
optimize_redis() {
    local redis_config="/etc/redis/redis.conf"
    
    # Redis 설정 최적화
    sed -i 's/^# maxmemory <bytes>/maxmemory 2gb/' "$redis_config"
    sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' "$redis_config"
    
    cat >> "$redis_config" << EOF

# Fortune VTuber 성능 최적화
tcp-keepalive 300
timeout 0
tcp-backlog 511
databases 16

# AOF 최적화
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# 저장 최적화
save 900 1
save 300 10
save 60 10000
EOF

    systemctl restart redis
}

# Nginx 성능 튜닝
optimize_nginx() {
    cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
worker_rlimit_nofile 65535;
pid /run/nginx.pid;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # 기본 설정
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # 성능 최적화
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    
    # 버퍼 크기 최적화
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # Gzip 압축
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # 캐시 설정
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # 로깅
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;
    
    # 가상 호스트 설정 포함
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF

    systemctl restart nginx
}

# 실행
echo "🚀 성능 최적화 시작..."
optimize_postgresql
optimize_redis
optimize_nginx
echo "✅ 성능 최적화 완료"
```

### CDN 설정

```bash
#!/bin/bash
# setup-cdn.sh

# CloudFlare CDN 설정
setup_cloudflare() {
    echo "☁️ CloudFlare CDN 설정..."
    
    # DNS 레코드 설정 스크립트
    cat > cloudflare-dns.sh << 'EOF'
#!/bin/bash
# CloudFlare DNS API를 통한 레코드 설정

CF_API_TOKEN="your-api-token"
CF_ZONE_ID="your-zone-id"
DOMAIN="fortune-vtuber.com"

# DNS 레코드 생성
create_dns_record() {
    local type=$1
    local name=$2
    local content=$3
    
    curl -X POST "https://api.cloudflare.com/client/v4/zones/$CF_ZONE_ID/dns_records" \
         -H "Authorization: Bearer $CF_API_TOKEN" \
         -H "Content-Type: application/json" \
         --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"ttl\":1}"
}

# A 레코드 설정
create_dns_record "A" "$DOMAIN" "your-server-ip"
create_dns_record "A" "www.$DOMAIN" "your-server-ip"
create_dns_record "A" "cdn.$DOMAIN" "your-server-ip"

# CNAME 레코드 설정
create_dns_record "CNAME" "api.$DOMAIN" "$DOMAIN"
create_dns_record "CNAME" "static.$DOMAIN" "cdn.$DOMAIN"
EOF

    chmod +x cloudflare-dns.sh
}

# 정적 파일 최적화
optimize_static_files() {
    echo "📁 정적 파일 최적화..."
    
    # 이미지 최적화 스크립트
    cat > optimize-images.sh << 'EOF'
#!/bin/bash
# 이미지 최적화 스크립트

STATIC_DIR="/opt/fortune-vtuber/project/backend/static"

# ImageMagick 설치 확인
if ! command -v convert &> /dev/null; then
    apt-get install -y imagemagick
fi

# PNG 최적화
find "$STATIC_DIR" -name "*.png" -type f | while read -r file; do
    echo "최적화 중: $file"
    convert "$file" -strip -interlace Plane -quality 85 "${file%.png}_optimized.png"
    mv "${file%.png}_optimized.png" "$file"
done

# JPEG 최적화
find "$STATIC_DIR" -name "*.jpg" -type f | while read -r file; do
    echo "최적화 중: $file"
    convert "$file" -strip -interlace Plane -quality 85 "${file%.jpg}_optimized.jpg"
    mv "${file%.jpg}_optimized.jpg" "$file"
done

# WebP 버전 생성
find "$STATIC_DIR" -name "*.png" -o -name "*.jpg" | while read -r file; do
    webp_file="${file%.*}.webp"
    convert "$file" -quality 80 "$webp_file"
    echo "WebP 생성: $webp_file"
done
EOF

    chmod +x optimize-images.sh
    ./optimize-images.sh
}

# Nginx CDN 설정
configure_nginx_cdn() {
    cat > /etc/nginx/conf.d/cdn.conf << 'EOF'
# CDN 설정
server {
    listen 80;
    server_name cdn.fortune-vtuber.com;
    
    root /opt/fortune-vtuber/project/backend/static;
    
    # 캐시 헤더 설정
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary "Accept-Encoding";
    }
    
    # WebP 지원
    location ~* \.(png|jpg|jpeg)$ {
        add_header Vary "Accept";
        try_files $uri$webp_suffix $uri =404;
    }
    
    # Live2D 모델 파일
    location /live2d/ {
        expires 30d;
        add_header Cache-Control "public";
        add_header Access-Control-Allow-Origin "*";
    }
    
    # Gzip 압축
    gzip on;
    gzip_types
        text/css
        application/javascript
        application/json
        image/svg+xml;
}
EOF
}

# 실행
setup_cloudflare
optimize_static_files
configure_nginx_cdn
systemctl reload nginx
```

## 🔄 CI/CD 파이프라인

### GitHub Actions 워크플로우

```yaml
# .github/workflows/deploy.yml
name: Deploy Fortune VTuber

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.11]
        node-version: [18]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_fortune_vtuber
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
        cache-dependency-path: project/frontend/package-lock.json
    
    - name: Install Python dependencies
      run: |
        cd project/backend
        python -m pip install --upgrade pip
        pip install -e ".[test]"
    
    - name: Install Node.js dependencies
      run: |
        cd project/frontend
        npm ci
    
    - name: Run Python tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_fortune_vtuber
      run: |
        cd project/backend
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Run Node.js tests
      run: |
        cd project/frontend
        npm test -- --coverage --watchAll=false
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./project/backend/coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
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

  build-and-push:
    needs: [test, security-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    
    permissions:
      contents: read
      packages: write
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v5
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push backend image
      id: build
      uses: docker/build-push-action@v5
      with:
        context: ./project/backend
        file: ./project/backend/Dockerfile.prod
        push: true
        tags: ${{ steps.meta.outputs.tags }}-backend
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
    
    - name: Build and push frontend image
      uses: docker/build-push-action@v5
      with:
        context: ./project/frontend
        file: ./project/frontend/Dockerfile.prod
        push: true
        tags: ${{ steps.meta.outputs.tags }}-frontend
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: staging
      url: https://staging.fortune-vtuber.com
    
    steps:
    - name: Deploy to staging
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_USER }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          cd /opt/fortune-vtuber
          
          # 새 이미지 풀
          docker pull ${{ needs.build-and-push.outputs.image-tag }}-backend
          docker pull ${{ needs.build-and-push.outputs.image-tag }}-frontend
          
          # 서비스 업데이트
          docker-compose -f docker-compose.staging.yml up -d
          
          # 헬스 체크
          sleep 30
          curl -f https://staging.fortune-vtuber.com/health || exit 1
    
    - name: Run staging tests
      run: |
        # E2E 테스트 실행
        npx playwright test --config=playwright.staging.config.js

  deploy-production:
    needs: [build-and-push, deploy-staging]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    
    environment:
      name: production
      url: https://fortune-vtuber.com
    
    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/fortune-vtuber
          
          # 백업 생성
          ./backup-system.sh backup
          
          # Blue-Green 배포
          export VERSION=${{ github.ref_name }}
          docker-compose -f docker-compose.prod.yml pull
          
          # Green 환경 시작
          docker-compose -f docker-compose.prod.yml up -d --scale backend=2
          
          # 헬스 체크
          sleep 60
          curl -f https://fortune-vtuber.com/health || exit 1
          
          # 트래픽 전환 완료
          echo "배포 완료: $VERSION"
    
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
        message: |
          🚀 Fortune VTuber 프로덕션 배포 완료
          버전: ${{ github.ref_name }}
          커밋: ${{ github.sha }}
          작성자: ${{ github.actor }}
```

### 배포 자동화 스크립트

```bash
#!/bin/bash
# deploy-automation.sh

set -e

# 설정
REPO_URL="https://github.com/your-org/fortune-vtuber.git"
DEPLOY_KEY="/home/deploy/.ssh/deploy_key"
ENVIRONMENTS=("staging" "production")

# 로깅 함수
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a /var/log/deploy.log
}

# Git 배포
deploy_from_git() {
    local environment=$1
    local branch=$2
    local deploy_path="/opt/fortune-vtuber-${environment}"
    
    log "🚀 Git 배포 시작: $environment ($branch)"
    
    # 기존 배포 백업
    if [[ -d "$deploy_path" ]]; then
        sudo mv "$deploy_path" "${deploy_path}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 새 코드 클론
    git clone --depth 1 --branch "$branch" "$REPO_URL" "$deploy_path"
    cd "$deploy_path"
    
    # 환경별 설정 적용
    cp ".env.${environment}" .env
    
    # 의존성 설치
    cd project/backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    
    cd ../frontend
    npm ci --production
    npm run build
    
    # 서비스 재시작
    sudo systemctl restart "fortune-vtuber-${environment}"
    
    log "✅ 배포 완료: $environment"
}

# Docker 배포
deploy_docker() {
    local environment=$1
    local image_tag=$2
    
    log "🐳 Docker 배포 시작: $environment ($image_tag)"
    
    cd "/opt/fortune-vtuber-${environment}"
    
    # 이미지 업데이트
    export VERSION="$image_tag"
    docker-compose -f "docker-compose.${environment}.yml" pull
    
    # 서비스 업데이트 (무중단 배포)
    docker-compose -f "docker-compose.${environment}.yml" up -d --no-deps backend
    
    # 헬스 체크
    sleep 30
    if curl -f "http://localhost:8080/health"; then
        log "✅ Docker 배포 완료: $environment"
    else
        log "❌ Docker 배포 실패: $environment"
        # 롤백
        docker-compose -f "docker-compose.${environment}.yml" rollback
        exit 1
    fi
}

# 배포 후 검증
post_deploy_verification() {
    local environment=$1
    local base_url
    
    case "$environment" in
        "staging") base_url="https://staging.fortune-vtuber.com" ;;
        "production") base_url="https://fortune-vtuber.com" ;;
    esac
    
    log "🔍 배포 후 검증 시작: $environment"
    
    # API 헬스 체크
    if curl -f "$base_url/health"; then
        log "✅ API 헬스 체크 통과"
    else
        log "❌ API 헬스 체크 실패"
        return 1
    fi
    
    # 기능 테스트
    test_apis=(
        "/api/v1/fortune/daily?birth_date=1995-03-15&zodiac=pisces"
        "/api/v1/user/session"
    )
    
    for api in "${test_apis[@]}"; do
        if curl -f "${base_url}${api}"; then
            log "✅ API 테스트 통과: $api"
        else
            log "❌ API 테스트 실패: $api"
            return 1
        fi
    done
    
    log "✅ 배포 후 검증 완료: $environment"
}

# 롤백 함수
rollback_deployment() {
    local environment=$1
    local backup_path=$2
    
    log "🔄 롤백 시작: $environment"
    
    # 서비스 중지
    sudo systemctl stop "fortune-vtuber-${environment}"
    
    # 백업에서 복원
    sudo rm -rf "/opt/fortune-vtuber-${environment}"
    sudo mv "$backup_path" "/opt/fortune-vtuber-${environment}"
    
    # 서비스 재시작
    sudo systemctl start "fortune-vtuber-${environment}"
    
    log "✅ 롤백 완료: $environment"
}

# 메인 배포 함수
main_deploy() {
    local deploy_type=$1  # git 또는 docker
    local environment=$2
    local version=$3
    
    case "$deploy_type" in
        "git")
            deploy_from_git "$environment" "$version"
            ;;
        "docker")
            deploy_docker "$environment" "$version"
            ;;
        *)
            echo "사용법: $0 [git|docker] [staging|production] [branch|tag]"
            exit 1
            ;;
    esac
    
    # 배포 후 검증
    if post_deploy_verification "$environment"; then
        log "🎉 배포 성공: $environment ($version)"
        
        # 성공 알림
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"✅ Fortune VTuber $environment 배포 성공\\n버전: $version\"}" \
            "$SLACK_WEBHOOK_URL" || true
    else
        log "❌ 배포 실패: $environment ($version)"
        exit 1
    fi
}

# 스크립트 실행
if [[ $# -lt 3 ]]; then
    echo "사용법: $0 [git|docker] [staging|production] [branch|tag]"
    echo "예시: $0 git staging main"
    echo "예시: $0 docker production v1.2.3"
    exit 1
fi

main_deploy "$1" "$2" "$3"
```

## 🚨 장애 대응

### 장애 대응 플레이북

```markdown
# 🚨 Fortune VTuber 장애 대응 플레이북

## 1. 즉시 대응 (5분 이내)

### 1.1 상황 파악
- [ ] 모니터링 대시보드 확인 (Grafana)
- [ ] 알림 채널 확인 (Slack, PagerDuty)
- [ ] 서비스 상태 확인
  ```bash
  curl -f https://fortune-vtuber.com/health
  curl -f https://fortune-vtuber.com/api/v1/fortune/daily
  ```

### 1.2 장애 분류
| 심각도 | 설명 | 대응 시간 |
|--------|------|-----------|
| P0 (Critical) | 전체 서비스 중단 | 즉시 |
| P1 (High) | 핵심 기능 중단 | 15분 |
| P2 (Medium) | 일부 기능 장애 | 1시간 |
| P3 (Low) | 성능 저하 | 4시간 |

### 1.3 초기 대응
```bash
# 서비스 상태 확인
systemctl status fortune-vtuber-backend
systemctl status nginx
systemctl status postgresql
systemctl status redis

# 로그 확인
tail -f /var/log/fortune-vtuber/app.log
tail -f /var/log/nginx/error.log
```

## 2. 일반적인 장애 시나리오

### 2.1 API 서버 응답 없음

**증상**:
- HTTP 500/502/503 에러
- API 응답 시간 초과
- 헬스 체크 실패

**원인 분석**:
```bash
# 프로세스 확인
ps aux | grep python
ps aux | grep gunicorn

# 포트 확인
netstat -tlnp | grep :8080

# 메모리/CPU 사용량
top -p $(pgrep -f fortune_vtuber)
```

**해결 방법**:
```bash
# 1. 서비스 재시작
sudo systemctl restart fortune-vtuber-backend

# 2. 여전히 문제시 프로세스 강제 종료
sudo pkill -f fortune_vtuber
sudo systemctl start fortune-vtuber-backend

# 3. 여전히 문제시 서버 재부팅 고려
```

### 2.2 데이터베이스 연결 실패

**증상**:
- "Database connection failed" 에러
- 운세 데이터 조회 실패
- 세션 생성 실패

**원인 분석**:
```bash
# PostgreSQL 상태 확인
systemctl status postgresql
pg_isready -h localhost -p 5432

# 연결 수 확인
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# 로그 확인
tail -f /var/log/postgresql/postgresql-15-main.log
```

**해결 방법**:
```bash
# 1. PostgreSQL 재시작
sudo systemctl restart postgresql

# 2. 연결 수 제한 초과시
psql -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';"

# 3. 디스크 공간 확인
df -h
```

### 2.3 WebSocket 연결 실패

**증상**:
- 채팅 기능 작동 안함
- Live2D 캐릭터 반응 없음
- 실시간 업데이트 중단

**원인 분석**:
```bash
# WebSocket 연결 테스트
websocat ws://localhost:8080/ws/chat/test

# Nginx WebSocket 프록시 설정 확인
nginx -t
tail -f /var/log/nginx/error.log
```

**해결 방법**:
```bash
# 1. Nginx 설정 확인 및 재로드
sudo nginx -s reload

# 2. 백엔드 WebSocket 핸들러 재시작
sudo systemctl restart fortune-vtuber-backend
```

### 2.4 메모리 부족

**증상**:
- OOM (Out of Memory) 에러
- 서비스 성능 저하
- 프로세스 자동 종료

**원인 분석**:
```bash
# 메모리 사용량 확인
free -h
ps aux --sort=-%mem | head -10

# 메모리 누수 확인
top -o %MEM
```

**해결 방법**:
```bash
# 1. 메모리 정리
echo 3 > /proc/sys/vm/drop_caches

# 2. 서비스 재시작
sudo systemctl restart fortune-vtuber-backend

# 3. 스왑 공간 확인
swapon --show
```

## 3. 자동 복구 스크립트

### 3.1 헬스 체크 및 자동 복구
```bash
#!/bin/bash
# auto-recovery.sh

check_and_recover() {
    local service=$1
    local check_url=$2
    local max_retries=3
    local retry_count=0
    
    while [[ $retry_count -lt $max_retries ]]; do
        if curl -f --connect-timeout 5 --max-time 10 "$check_url" &>/dev/null; then
            echo "✅ $service 정상"
            return 0
        else
            echo "❌ $service 장애 감지 (시도: $((retry_count + 1))/$max_retries)"
            
            # 서비스 재시작
            sudo systemctl restart "$service"
            sleep 30
            
            retry_count=$((retry_count + 1))
        fi
    done
    
    # 최대 재시도 횟수 초과
    echo "🚨 $service 복구 실패 - 수동 개입 필요"
    send_alert "$service 자동 복구 실패"
    return 1
}

# 알림 전송
send_alert() {
    local message=$1
    
    # Slack 알림
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"🚨 Fortune VTuber 자동 복구 실패: $message\"}" \
        "$SLACK_WEBHOOK_URL" &
    
    # 이메일 알림
    echo "$message" | mail -s "Fortune VTuber 장애 알림" "$ADMIN_EMAIL" &
}

# 메인 체크
check_and_recover "fortune-vtuber-backend" "http://localhost:8080/health"
check_and_recover "nginx" "http://localhost/health"
```

### 3.2 로그 기반 장애 감지
```bash
#!/bin/bash
# log-monitor.sh

LOG_FILE="/var/log/fortune-vtuber/app.log"
ERROR_PATTERNS=(
    "Database connection failed"
    "Out of memory"
    "Internal server error"
    "Connection refused"
    "Timeout"
)

monitor_logs() {
    tail -F "$LOG_FILE" | while read -r line; do
        for pattern in "${ERROR_PATTERNS[@]}"; do
            if echo "$line" | grep -q "$pattern"; then
                echo "🚨 에러 패턴 감지: $pattern"
                echo "로그: $line"
                
                # 자동 복구 시도
                case "$pattern" in
                    "Database connection failed")
                        systemctl restart postgresql
                        ;;
                    "Out of memory")
                        systemctl restart fortune-vtuber-backend
                        ;;
                    "Connection refused")
                        systemctl restart nginx
                        ;;
                esac
                
                # 알림 전송
                send_alert "에러 패턴 감지: $pattern"
            fi
        done
    done
}

monitor_logs
```

## 4. 장애 예방

### 4.1 프로액티브 모니터링
```bash
#!/bin/bash
# proactive-monitoring.sh

# 디스크 사용량 모니터링
check_disk_usage() {
    local threshold=80
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $usage -gt $threshold ]]; then
        echo "⚠️ 디스크 사용량 경고: ${usage}%"
        
        # 로그 파일 정리
        find /var/log -name "*.log" -mtime +7 -delete
        
        # 임시 파일 정리
        find /tmp -type f -mtime +1 -delete
        
        send_alert "디스크 사용량 경고: ${usage}%"
    fi
}

# 메모리 사용량 모니터링
check_memory_usage() {
    local threshold=85
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [[ $usage -gt $threshold ]]; then
        echo "⚠️ 메모리 사용량 경고: ${usage}%"
        
        # 메모리 정리
        echo 1 > /proc/sys/vm/drop_caches
        
        send_alert "메모리 사용량 경고: ${usage}%"
    fi
}

# 실행
check_disk_usage
check_memory_usage
```

### 4.2 예방적 유지보수
```bash
#!/bin/bash
# preventive-maintenance.sh

# 데이터베이스 최적화
optimize_database() {
    echo "🗄️ 데이터베이스 최적화 시작..."
    
    # VACUUM 및 ANALYZE
    psql -U postgres -d fortune_vtuber -c "VACUUM ANALYZE;"
    
    # 인덱스 재구성
    psql -U postgres -d fortune_vtuber -c "REINDEX DATABASE fortune_vtuber;"
    
    # 통계 업데이트
    psql -U postgres -d fortune_vtuber -c "ANALYZE;"
    
    echo "✅ 데이터베이스 최적화 완료"
}

# SSL 인증서 갱신 확인
check_ssl_expiry() {
    local cert_file="/etc/ssl/certs/fortune-vtuber.com.pem"
    local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
    local expiry_timestamp=$(date -d "$expiry_date" +%s)
    local current_timestamp=$(date +%s)
    local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    if [[ $days_until_expiry -lt 30 ]]; then
        echo "⚠️ SSL 인증서 만료 임박: ${days_until_expiry}일 남음"
        send_alert "SSL 인증서 갱신 필요: ${days_until_expiry}일 남음"
    fi
}

# 로그 로테이션
rotate_logs() {
    echo "📝 로그 로테이션 시작..."
    
    # 애플리케이션 로그 압축
    find /var/log/fortune-vtuber -name "*.log" -mtime +1 -exec gzip {} \;
    
    # 오래된 압축 로그 삭제
    find /var/log/fortune-vtuber -name "*.gz" -mtime +30 -delete
    
    echo "✅ 로그 로테이션 완료"
}

# 실행
optimize_database
check_ssl_expiry
rotate_logs
```

---

**장애는 예방이 최선입니다. 정기적인 모니터링과 유지보수를 통해 안정적인 서비스를 운영하세요! 🛡️**
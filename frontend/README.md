# Live2D Fortune Telling App - Frontend

React 기반의 Live2D 캐릭터와 함께하는 실시간 운세 상담 앱입니다.

## 🌟 주요 기능

### ✨ 핵심 기능
- **4가지 운세 타입**: 일일운세, 타로카드, 별자리운세, 사주운세
- **Live2D 캐릭터**: 미라와의 실시간 상호작용
- **실시간 채팅**: WebSocket 기반 AI 대화 시스템
- **백엔드 완전 연동**: FastAPI 서버와 실시간 통신

### 🎯 Live2D 통합
- 운세 결과에 따른 캐릭터 반응
- 채팅 메시지 기반 감정 변화
- 클릭 인터랙션 지원
- 백엔드와 실시간 상태 동기화

### 💬 실시간 통신
- WebSocket 기반 채팅 시스템
- 자동 재연결 및 에러 복구
- 채팅 히스토리 로컬 저장
- 콘텐츠 필터링 결과 표시

## 🏗️ 아키텍처

### 컴포넌트 구조
```
src/
├── components/          # React 컴포넌트
│   ├── MainLayout.js    # 메인 레이아웃
│   ├── Live2DViewer.js  # Live2D 캐릭터 뷰어
│   ├── ChatInterface.js # 실시간 채팅 인터페이스
│   ├── FortuneSelector.js # 운세 선택 및 사용자 입력
│   ├── FortuneResult.js # 운세 결과 표시
│   ├── CardDrawing.js   # 타로 카드 뽑기
│   ├── ErrorBoundary.js # 에러 경계 처리
│   └── LoadingSpinner.js # 로딩 상태 표시
├── services/            # API 및 서비스 레이어
│   ├── FortuneService.js # 운세 API 통신
│   ├── UserService.js   # 사용자 관리
│   ├── Live2DService.js # Live2D 캐릭터 제어
│   └── WebSocketService.js # WebSocket 통신
├── utils/               # 유틸리티 함수
│   ├── constants.js     # 상수 정의
│   └── errorHandler.js  # 에러 처리 시스템
└── tests/               # 테스트 파일
    └── integration.test.md # 통합 테스트 가이드
```

### 서비스 레이어
- **FortuneService**: 4가지 운세 API 호출 및 데이터 처리
- **UserService**: 익명 사용자 생성, 세션 관리, 프로필 저장
- **Live2DService**: 캐릭터 제어 및 백엔드 API 연동
- **WebSocketService**: 실시간 채팅 및 Live2D 상태 동기화

## 🚀 시작하기

### 사전 요구사항
- Node.js 16+ 
- npm 또는 yarn
- 백엔드 서버 실행 중 (포트 8000)

### 설치 및 실행
```bash
# 의존성 설치
npm install

# 개발 서버 시작
npm start

# 브라우저에서 http://localhost:3000 접속
```

### 환경 설정
```bash
# .env 파일 생성 (선택사항)
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## 🔌 백엔드 연동

### API 엔드포인트
```
운세 API (v2):
POST /fortune/v2/daily      # 일일 운세
POST /fortune/v2/tarot      # 타로 운세
POST /fortune/v2/zodiac     # 별자리 운세
POST /fortune/v2/saju       # 사주 운세

Live2D API:
POST /api/live2d/emotion    # 감정 변경
POST /api/live2d/motion     # 모션 실행
GET  /api/live2d/status     # 현재 상태

사용자 API:
POST /api/user/profile      # 프로필 생성/수정
POST /api/user/sessions     # 세션 생성
GET  /api/user/sessions     # 세션 목록
```

### WebSocket 연결
```
채팅: /ws/chat/{session_id}
Live2D: /ws/live2d/{session_id}
```

## 📱 사용자 플로우

### 1. 앱 초기화
1. 익명 사용자 자동 생성
2. WebSocket 연결 설정
3. Live2D 캐릭터 초기화
4. 환영 메시지 표시

### 2. 운세 상담
1. 운세 타입 선택 (일일/타로/별자리/사주)
2. 필요한 정보 입력 (생년월일, 출생시간 등)
3. 백엔드 API 호출
4. 운세 결과 표시
5. Live2D 캐릭터 반응

### 3. 실시간 채팅
1. 채팅 메시지 입력
2. WebSocket으로 전송
3. AI 응답 수신
4. Live2D 감정 반응
5. 히스토리 저장

## 🛡️ 에러 처리

### 에러 분류 시스템
- **네트워크 에러**: 연결 실패, 타임아웃
- **API 에러**: 4xx/5xx HTTP 상태 코드
- **WebSocket 에러**: 연결 끊김, 재연결 필요
- **Live2D 에러**: 캐릭터 로딩 실패
- **검증 에러**: 사용자 입력 오류

### 복구 전략
- 자동 재연결 (WebSocket)
- 재시도 버튼 제공
- 폴백 데이터 사용
- 사용자 친화적 에러 메시지

## 🎨 UI/UX 특징

### 디자인 시스템
- **글래스모피즘**: 반투명 효과와 블러
- **그라데이션**: 신비로운 운세 테마
- **반응형 디자인**: 모바일/데스크톱 최적화
- **애니메이션**: 부드러운 전환 효과

### 접근성
- WCAG 2.1 AA 준수
- 키보드 네비게이션 지원
- 스크린 리더 호환성
- 색상 대비 최적화

## 🔧 개발 도구

### 코드 품질
```bash
# 린트 검사
npm run lint

# 타입 검사 (TypeScript 전환 시)
npm run type-check

# 테스트 실행
npm test

# 빌드
npm run build
```

### 디버깅
- Chrome DevTools 지원
- React Developer Tools
- WebSocket 연결 상태 모니터링
- API 호출 로깅

## 📈 성능 최적화

### 로딩 성능
- 코드 스플리팅 적용
- 이미지 최적화
- 캐싱 전략
- 지연 로딩

### 메모리 관리
- WebSocket 연결 정리
- Live2D 리소스 해제
- 이벤트 리스너 정리
- 메모리 누수 방지

## 🧪 테스트

### 통합 테스트
전체 사용자 플로우를 테스트하는 시나리오:
- 앱 초기화 플로우
- 운세 상담 플로우 (4가지 타입)
- 실시간 채팅 플로우
- Live2D 상호작용 플로우
- 에러 처리 및 복구 플로우

자세한 내용은 `src/tests/integration.test.md` 참조

### 브라우저 호환성
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚧 현재 제한사항

### Live2D 관련
- Live2D SDK는 플레이스홀더로 구현
- 실제 3D 모델 로딩 필요
- 모션 및 표정 데이터 통합 필요

### 향후 개선사항
- 실제 Live2D Cubism SDK 통합
- 고급 AI 대화 시스템
- 사용자 계정 시스템
- 운세 히스토리 관리
- 푸시 알림 지원

## 🤝 기여하기

### 개발 가이드라인
1. ESLint 규칙 준수
2. 컴포넌트별 단위 테스트 작성
3. 접근성 가이드라인 준수
4. 성능 최적화 고려

### 코드 스타일
- Functional Components + Hooks 사용
- 명확한 변수명과 함수명
- JSDoc 주석 작성
- 에러 경계 적절히 배치

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 지원

문제나 질문이 있으시면 GitHub Issues를 통해 문의해주세요.

---

**Live2D 운세 앱** - 미라와 함께하는 신비로운 운세 상담 🔮✨
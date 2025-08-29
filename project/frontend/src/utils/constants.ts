/**
 * 애플리케이션 상수 정의
 */

// 운세 타입
export const FORTUNE_TYPES = {
  DAILY: 'daily',
  TAROT: 'tarot',
  ZODIAC: 'zodiac',
  SAJU: 'saju'
};

// 연결 상태
export const CONNECTION_STATUS = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error'
};

// Live2D 상태
export const LIVE2D_STATUS = {
  INITIALIZING: 'initializing',
  LOADING: 'loading',
  READY: 'ready',
  ERROR: 'error'
};

// 메시지 타입
export const MESSAGE_TYPES = {
  USER: 'user',
  AI: 'ai',
  SYSTEM: 'system'
};

// WebSocket 이벤트 타입
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  ERROR: 'error',
  MESSAGE: 'message',
  FORTUNE_RESULT: 'fortuneResult',
  CHAT_RESPONSE: 'chatResponse',
  LIVE2D_COMMAND: 'live2dCommand',
  SYSTEM_STATUS: 'systemStatus'
};

// Live2D 표정
export const EXPRESSIONS = {
  NEUTRAL: 'neutral',
  JOY: 'joy',
  THINKING: 'thinking',
  CONCERN: 'concern',
  SURPRISE: 'surprise',
  MYSTICAL: 'mystical',
  COMFORT: 'comfort',
  PLAYFUL: 'playful'
};

// Live2D 모션
export const MOTIONS = {
  IDLE: 'idle',
  CARD_DRAW: 'card_draw',
  CRYSTAL_GAZE: 'crystal_gaze',
  BLESSING: 'blessing',
  GREETING: 'greeting',
  SPECIAL_READING: 'special_reading',
  THINKING_POSE: 'thinking_pose'
};

// 운세 점수 범위
export const FORTUNE_SCORES = {
  EXCELLENT: { min: 80, max: 100, label: '최고' },
  GOOD: { min: 60, max: 79, label: '좋음' },
  NEUTRAL: { min: 40, max: 59, label: '보통' },
  CAUTION: { min: 20, max: 39, label: '주의' },
  WARNING: { min: 0, max: 19, label: '경고' }
};

// 별자리 목록
export const ZODIAC_SIGNS = {
  ARIES: { id: 'aries', name: '양자리', period: '3/21 - 4/19', emoji: '♈' },
  TAURUS: { id: 'taurus', name: '황소자리', period: '4/20 - 5/20', emoji: '♉' },
  GEMINI: { id: 'gemini', name: '쌍둥이자리', period: '5/21 - 6/21', emoji: '♊' },
  CANCER: { id: 'cancer', name: '게자리', period: '6/22 - 7/22', emoji: '♋' },
  LEO: { id: 'leo', name: '사자자리', period: '7/23 - 8/22', emoji: '♌' },
  VIRGO: { id: 'virgo', name: '처녀자리', period: '8/23 - 9/22', emoji: '♍' },
  LIBRA: { id: 'libra', name: '천칭자리', period: '9/23 - 10/22', emoji: '♎' },
  SCORPIO: { id: 'scorpio', name: '전갈자리', period: '10/23 - 11/21', emoji: '♏' },
  SAGITTARIUS: { id: 'sagittarius', name: '사수자리', period: '11/22 - 12/21', emoji: '♐' },
  CAPRICORN: { id: 'capricorn', name: '염소자리', period: '12/22 - 1/19', emoji: '♑' },
  AQUARIUS: { id: 'aquarius', name: '물병자리', period: '1/20 - 2/18', emoji: '♒' },
  PISCES: { id: 'pisces', name: '물고기자리', period: '2/19 - 3/20', emoji: '♓' }
};

// 타로 카드 (메이저 아르카나)
export const TAROT_CARDS = {
  THE_FOOL: { id: 0, name: '바보', emoji: '🃏' },
  THE_MAGICIAN: { id: 1, name: '마법사', emoji: '🎩' },
  THE_HIGH_PRIESTESS: { id: 2, name: '여교황', emoji: '🔮' },
  THE_EMPRESS: { id: 3, name: '여황제', emoji: '👑' },
  THE_EMPEROR: { id: 4, name: '황제', emoji: '⚡' },
  THE_HIEROPHANT: { id: 5, name: '교황', emoji: '📿' },
  THE_LOVERS: { id: 6, name: '연인', emoji: '💕' },
  THE_CHARIOT: { id: 7, name: '전차', emoji: '🚗' },
  STRENGTH: { id: 8, name: '힘', emoji: '💪' },
  THE_HERMIT: { id: 9, name: '은둔자', emoji: '🕯️' },
  WHEEL_OF_FORTUNE: { id: 10, name: '운명의 수레바퀴', emoji: '🎡' },
  JUSTICE: { id: 11, name: '정의', emoji: '⚖️' },
  THE_HANGED_MAN: { id: 12, name: '매달린 남자', emoji: '🙃' },
  DEATH: { id: 13, name: '죽음', emoji: '💀' },
  TEMPERANCE: { id: 14, name: '절제', emoji: '🍃' },
  THE_DEVIL: { id: 15, name: '악마', emoji: '😈' },
  THE_TOWER: { id: 16, name: '탑', emoji: '🏗️' },
  THE_STAR: { id: 17, name: '별', emoji: '⭐' },
  THE_MOON: { id: 18, name: '달', emoji: '🌙' },
  THE_SUN: { id: 19, name: '태양', emoji: '☀️' },
  JUDGEMENT: { id: 20, name: '심판', emoji: '📯' },
  THE_WORLD: { id: 21, name: '세계', emoji: '🌍' }
};

// 색상 테마
export const COLORS = {
  PRIMARY: '#667eea',
  SECONDARY: '#764ba2',
  ACCENT: '#4facfe',
  SUCCESS: '#198754',
  WARNING: '#ffc107',
  ERROR: '#dc3545',
  INFO: '#0dcaf0',
  WHITE: '#ffffff',
  TRANSPARENT_WHITE: 'rgba(255, 255, 255, 0.1)',
  GLASS_EFFECT: 'rgba(255, 255, 255, 0.15)'
};

// 애니메이션 지속시간
export const ANIMATION_DURATION = {
  FAST: 200,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000
};

// 로컬 스토리지 키
export const STORAGE_KEYS = {
  USER_PREFERENCES: 'fortune_app_user_preferences',
  CHAT_HISTORY: 'fortune_app_chat_history',
  FORTUNE_HISTORY: 'fortune_app_fortune_history',
  SETTINGS: 'fortune_app_settings'
};

// API 엔드포인트 (백엔드 연동)
export const API_ENDPOINTS = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 
    (process.env.NODE_ENV === 'development' ? 'http://175.118.126.76:8000' : ''),
  WEBSOCKET: process.env.REACT_APP_WS_BASE_URL || 
    (process.env.NODE_ENV === 'development' ? 'ws://175.118.126.76:8000' : `ws://${window.location.host}`),
  FORTUNE: '/api/v1/fortune',
  CHAT: '/api/v1/chat',
  USER: '/api/v1/user',
  LIVE2D: '/api/v1/live2d'
};

// 에러 메시지
export const ERROR_MESSAGES = {
  CONNECTION_FAILED: '서버 연결에 실패했습니다.',
  LIVE2D_INIT_FAILED: 'Live2D 초기화에 실패했습니다.',
  FORTUNE_REQUEST_FAILED: '운세 요청에 실패했습니다.',
  INVALID_INPUT: '잘못된 입력입니다.',
  NETWORK_ERROR: '네트워크 오류가 발생했습니다.',
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다.'
};

// 성공 메시지
export const SUCCESS_MESSAGES = {
  CONNECTION_SUCCESS: '서버에 연결되었습니다.',
  LIVE2D_READY: 'Live2D 캐릭터가 준비되었습니다.',
  FORTUNE_SUCCESS: '운세를 성공적으로 받았습니다.',
  MESSAGE_SENT: '메시지가 전송되었습니다.'
};

// 기본 설정
export const DEFAULT_SETTINGS = {
  volume: 0.7,
  autoPlay: true,
  notifications: true,
  theme: 'default',
  language: 'ko'
};

// 환경 정보 및 디버깅을 위한 헬퍼
export const DEBUG_INFO = {
  getEnvironmentInfo() {
    return {
      NODE_ENV: process.env.NODE_ENV,
      API_BASE_URL: API_ENDPOINTS.BASE_URL,
      WS_BASE_URL: API_ENDPOINTS.WEBSOCKET,
      ENV_VARS: {
        REACT_APP_API_BASE_URL: process.env.REACT_APP_API_BASE_URL,
        REACT_APP_WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL,
        REACT_APP_LIVE2D_MODEL_PATH: process.env.REACT_APP_LIVE2D_MODEL_PATH
      },
      WINDOW_LOCATION: {
        origin: typeof window !== 'undefined' ? window.location.origin : 'undefined',
        host: typeof window !== 'undefined' ? window.location.host : 'undefined',
        hostname: typeof window !== 'undefined' ? window.location.hostname : 'undefined',
        port: typeof window !== 'undefined' ? window.location.port : 'undefined'
      }
    };
  },

  logConfiguration() {
    const info = this.getEnvironmentInfo();
    console.group('🔧 VTuber Frontend Configuration');
    console.log('Environment:', info.NODE_ENV);
    console.log('API Base URL:', info.API_BASE_URL);
    console.log('WebSocket URL:', info.WS_BASE_URL);
    console.log('Environment Variables:', info.ENV_VARS);
    console.log('Window Location:', info.WINDOW_LOCATION);
    console.groupEnd();
    return info;
  },

  async testApiConnection() {
    try {
      const apiUrl = API_ENDPOINTS.BASE_URL;
      console.log(`Testing API connection to: ${apiUrl}`);
      
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      const result = {
        success: response.ok,
        status: response.status,
        url: `${apiUrl}/health`,
        timestamp: new Date().toISOString()
      };
      
      console.log('API Connection Test Result:', result);
      return result;
    } catch (error) {
      const result = {
        success: false,
        error: error.message,
        url: `${API_ENDPOINTS.BASE_URL}/health`,
        timestamp: new Date().toISOString()
      };
      
      console.error('API Connection Test Failed:', result);
      return result;
    }
  }
};
/**
 * Live2D 캐릭터 관리 서비스
 * Live2D SDK와의 상호작용 및 백엔드 API 연동을 담당
 */

import { API_ENDPOINTS } from '../utils/constants';

class Live2DService {
  constructor() {
    this.model = null;
    this.canvas = null;
    this.animationId = null;
    this.isInitialized = false;
    this.currentExpression = 'neutral';
    this.currentMotion = null;
    this.lastTime = 0;
    this.modelPath = '/models/mira/'; // 향후 실제 모델 경로
    this.baseURL = API_ENDPOINTS.BASE_URL;
  }

  // Live2D 초기화
  async initialize(canvas) {
    try {
      console.log('[Live2D] 서비스 초기화 시작');
      
      this.canvas = canvas;
      
      // Live2D SDK 로드 확인
      if (!window.Live2D) {
        await this.loadSDK();
      }

      // SDK 초기화
      await window.Live2D.init();
      
      // 모델 로더 생성
      this.modelLoader = new window.Live2D.ModelLoader();
      
      // 기본 모델 로드
      await this.loadModel();
      
      // 렌더링 루프 시작
      this.startRenderLoop();
      
      this.isInitialized = true;
      console.log('[Live2D] 서비스 초기화 완료');
      
      return true;
    } catch (error) {
      console.error('[Live2D] 초기화 실패:', error);
      throw error;
    }
  }

  // Live2D SDK 로드
  async loadSDK() {
    return new Promise((resolve, reject) => {
      // 실제 환경에서는 Live2D SDK 스크립트 로드
      // 현재는 플레이스홀더 사용
      const script = document.createElement('script');
      script.src = '/libs/live2d-placeholder.js';
      script.onload = () => {
        console.log('[Live2D] SDK 로드 완료');
        resolve();
      };
      script.onerror = () => {
        reject(new Error('Live2D SDK 로드 실패'));
      };
      document.head.appendChild(script);
    });
  }

  // 모델 로드
  async loadModel(modelName = 'mira') {
    try {
      console.log(`[Live2D] 모델 로드 시작: ${modelName}`);
      
      const modelPath = `${this.modelPath}${modelName}.model3.json`;
      this.model = await this.modelLoader.loadModel(modelPath);
      
      // 기본 표정 설정
      this.setExpression('neutral');
      
      console.log('[Live2D] 모델 로드 완료');
      return this.model;
    } catch (error) {
      console.error('[Live2D] 모델 로드 실패:', error);
      throw error;
    }
  }

  // 렌더링 루프 시작
  startRenderLoop() {
    const render = (time) => {
      if (!this.isInitialized || !this.model || !this.canvas) {
        return;
      }

      const deltaTime = time - this.lastTime;
      this.lastTime = time;

      // 모델 업데이트
      this.modelLoader.update(deltaTime);
      
      // 렌더링
      this.modelLoader.render(this.canvas);

      this.animationId = requestAnimationFrame(render);
    };

    this.animationId = requestAnimationFrame(render);
    console.log('[Live2D] 렌더링 루프 시작');
  }

  // 렌더링 루프 중지
  stopRenderLoop() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
      console.log('[Live2D] 렌더링 루프 중지');
    }
  }

  // 표정 변경
  setExpression(expressionId) {
    if (!this.isInitialized || !this.modelLoader) {
      console.warn('[Live2D] 모델이 초기화되지 않음');
      return false;
    }

    try {
      const success = this.modelLoader.setExpression(expressionId);
      if (success) {
        this.currentExpression = expressionId;
        console.log(`[Live2D] 표정 변경 성공: ${expressionId}`);
      }
      return success;
    } catch (error) {
      console.error('[Live2D] 표정 변경 실패:', error);
      return false;
    }
  }

  // 모션 재생
  async playMotion(motionId) {
    if (!this.isInitialized || !this.modelLoader) {
      console.warn('[Live2D] 모델이 초기화되지 않음');
      return false;
    }

    try {
      this.currentMotion = motionId;
      const success = await this.modelLoader.playMotion(motionId);
      this.currentMotion = null;
      return success;
    } catch (error) {
      console.error('[Live2D] 모션 재생 실패:', error);
      this.currentMotion = null;
      return false;
    }
  }

  // 운세 결과에 따른 표정/모션 설정
  async handleFortuneResult(fortuneData, sessionId) {
    // 백엔드 API 응답 구조를 처리
    const data = fortuneData.data || fortuneData;
    const { live2d_emotion, live2d_motion, fortune_type } = data;
    
    console.log('[Live2D] 운세 결과 처리:', { 
      live2d_emotion, 
      live2d_motion, 
      fortune_type 
    });

    try {
      // 백엔드에서 직접 제공한 감정과 모션 사용
      if (live2d_motion) {
        await this.playMotion(live2d_motion);
      }

      if (live2d_emotion) {
        this.setExpression(live2d_emotion);
      }

      // 백엔드 API 호출 (선택사항)
      if (sessionId) {
        try {
          if (live2d_emotion) {
            await this.setEmotionAPI(live2d_emotion, sessionId);
          }
          if (live2d_motion) {
            await this.playMotionAPI(live2d_motion, sessionId);
          }
        } catch (apiError) {
          console.warn('[Live2D] 백엔드 API 호출 실패 (계속 진행):', apiError);
        }
      }

      return true;
    } catch (error) {
      console.error('[Live2D] 운세 결과 처리 실패:', error);
      return false;
    }
  }

  // 인터랙션 처리
  async handleInteraction(x, y) {
    if (!this.isInitialized) {
      return false;
    }

    console.log(`[Live2D] 인터랙션 처리: (${x}, ${y})`);

    // 클릭 위치에 따른 반응
    const canvasRect = this.canvas.getBoundingClientRect();
    const relativeY = y / canvasRect.height;

    if (relativeY < 0.5) {
      // 상단 클릭 (얼굴 영역) - 표정 변경
      const expressions = ['joy', 'surprise', 'playful'];
      const randomExpression = expressions[Math.floor(Math.random() * expressions.length)];
      this.setExpression(randomExpression);
      
      // 잠시 후 기본 표정으로 복귀
      setTimeout(() => {
        this.setExpression('neutral');
      }, 3000);
    } else {
      // 하단 클릭 (몸체 영역) - 인사 모션
      await this.playMotion('greeting');
    }

    return true;
  }

  // 채팅 메시지에 따른 반응
  handleChatMessage(message) {
    if (!this.isInitialized) {
      return;
    }

    // 감정 키워드 매핑
    const emotionKeywords = {
      joy: ['기쁘', '좋', '행복', '최고', '멋져', '완벽'],
      concern: ['걱정', '불안', '힘들', '어려', '문제'],
      surprise: ['놀라', '대박', '와', '헐', '정말'],
      thinking: ['궁금', '어떻게', '왜', '생각', '고민']
    };

    // 메시지에서 감정 감지
    for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
      if (keywords.some(keyword => message.includes(keyword))) {
        this.setExpression(emotion);
        setTimeout(() => {
          this.setExpression('neutral');
        }, 4000);
        break;
      }
    }
  }

  // 리소스 정리
  dispose() {
    this.stopRenderLoop();
    
    if (this.modelLoader) {
      this.modelLoader.dispose();
    }
    
    this.model = null;
    this.canvas = null;
    this.isInitialized = false;
    
    console.log('[Live2D] 리소스 정리 완료');
  }

  /**
   * API 요청 헬퍼 메서드
   */
  async apiRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    console.log(`[Live2DService] API 요청 시작: ${url}`);

    try {
      const response = await fetch(url, {
        ...defaultOptions,
        ...options,
      });

      console.log(`[Live2DService] API 응답 상태: ${response.status}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        console.error(`[Live2DService] API 오류 응답:`, { status: response.status, errorData, url });
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log(`[Live2DService] API 요청 성공: ${endpoint}`, data);
      return data;
    } catch (error) {
      console.error(`[Live2DService] API 요청 실패: ${endpoint}`, {
        url,
        error: error.message,
        baseURL: this.baseURL,
        endpoint
      });
      
      // 네트워크 연결 오류 또는 CORS 오류일 가능성 확인
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(`Live2D 서버 연결 실패: ${this.baseURL} (네트워크 오류 또는 CORS 문제)`);
      }
      
      throw error;
    }
  }

  /**
   * 백엔드 감정 변경 API 호출
   */
  async setEmotionAPI(emotion, sessionId) {
    try {
      const response = await this.apiRequest('/api/live2d/emotion', {
        method: 'POST',
        body: JSON.stringify({
          emotion: emotion,
          session_id: sessionId
        })
      });

      console.log('[Live2D] 백엔드 감정 변경 성공:', response);
      return response;
    } catch (error) {
      console.error('[Live2D] 백엔드 감정 변경 실패:', error);
      throw error;
    }
  }

  /**
   * 백엔드 모션 실행 API 호출
   */
  async playMotionAPI(motion, sessionId) {
    try {
      const response = await this.apiRequest('/api/live2d/motion', {
        method: 'POST',
        body: JSON.stringify({
          motion: motion,
          session_id: sessionId
        })
      });

      console.log('[Live2D] 백엔드 모션 실행 성공:', response);
      return response;
    } catch (error) {
      console.error('[Live2D] 백엔드 모션 실행 실패:', error);
      throw error;
    }
  }

  /**
   * 백엔드 현재 상태 조회 API 호출
   */
  async getStatusAPI(sessionId) {
    try {
      const response = await this.apiRequest(`/api/live2d/status?session_id=${sessionId}`, {
        method: 'GET'
      });

      console.log('[Live2D] 백엔드 상태 조회 성공:', response);
      return response;
    } catch (error) {
      console.error('[Live2D] 백엔드 상태 조회 실패:', error);
      throw error;
    }
  }

  // 상태 정보 조회
  getStatus() {
    return {
      initialized: this.isInitialized,
      hasModel: !!this.model,
      currentExpression: this.currentExpression,
      currentMotion: this.currentMotion,
      isRendering: !!this.animationId
    };
  }

  // 사용 가능한 표정 목록
  getAvailableExpressions() {
    return ['neutral', 'joy', 'thinking', 'concern', 'surprise', 'mystical', 'comfort', 'playful'];
  }

  // 사용 가능한 모션 목록
  getAvailableMotions() {
    return ['idle', 'card_draw', 'crystal_gaze', 'blessing', 'greeting', 'special_reading', 'thinking_pose'];
  }
}

// 싱글톤 인스턴스 생성
const live2DService = new Live2DService();

export default live2DService;
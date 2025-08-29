/**
 * Live2D Service for Live2DViewer - Simplified stub version
 * This is a stub implementation that provides the same interface as the original
 * but without complex dependencies to avoid import errors.
 */

class Live2DServiceReference2 {
  constructor() {
    this.isInitialized = false;
    this._canvas = null;
    this._currentModel = null;
    this._currentExpression = 'neutral';
    this._isRendering = false;
    this._animationId = null;
    
    console.log('[Live2DService_Reference2] Live2D 서비스 생성됨 (간소화 버전)');
    
    // 글로벌 접근을 위해 window에 등록
    if (typeof window !== 'undefined') {
      window.live2DService = this;
    }
  }

  /**
   * Live2D 초기화
   */
  async initialize(canvas) {
    try {
      console.log('[Live2DService_Reference2] Live2D 초기화 시작...');
      
      this._canvas = canvas;
      
      // 기본 Canvas 설정
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#333';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Live2D Ready', canvas.width / 2, canvas.height / 2);
      }
      
      this.isInitialized = true;
      console.log('[Live2DService_Reference2] Live2D 초기화 완료');
      
      return true;
      
    } catch (error) {
      console.error('[Live2DService_Reference2] 초기화 실패:', error);
      throw error;
    }
  }

  /**
   * 모델 로드 (로컬)
   */
  async loadModel(modelName = 'Mao') {
    try {
      console.log('[Live2DService_Reference2] 모델 로드 시작:', modelName);
      
      if (!this.isInitialized) {
        throw new Error('서비스가 초기화되지 않았습니다');
      }
      
      // 시뮬레이션된 모델 로드
      await new Promise(resolve => setTimeout(resolve, 500));
      
      this._currentModel = {
        name: modelName,
        loaded: true,
        expressions: ['neutral', 'joy', 'surprise', 'thinking', 'playful'],
        motions: ['greeting', 'blessing', 'idle']
      };
      
      // 렌더링 시작
      this.startRendering();
      
      console.log('[Live2DService_Reference2] 모델 로드 완료:', modelName);
      return true;
      
    } catch (error) {
      console.error('[Live2DService_Reference2] 모델 로드 실패:', error);
      throw error;
    }
  }

  /**
   * API를 통한 모델 로드 (백엔드)
   */
  async loadModelAPI(modelName, sessionId) {
    try {
      console.log('[Live2DService_Reference2] API 모델 로드 시작:', { modelName, sessionId });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      console.log('[Live2DService_Reference2] API 모델 로드 완료');
      return true;
      
    } catch (error) {
      console.warn('[Live2DService_Reference2] API 모델 로드 실패 (로컬 모델 사용):', error);
      throw error;
    }
  }

  /**
   * 렌더링 시작
   */
  startRendering() {
    if (this._isRendering) return;
    
    this._isRendering = true;
    
    const render = () => {
      if (!this._isRendering || !this.isInitialized) return;
      
      this.update();
      this._animationId = requestAnimationFrame(render);
    };
    
    render();
    console.log('[Live2DService_Reference2] 렌더링 시작');
  }

  /**
   * 업데이트 루프
   */
  update() {
    if (!this._canvas) return;
    
    const ctx = this._canvas.getContext('2d');
    if (!ctx) return;
    
    // 간단한 렌더링 - 투명한 배경과 상태 표시
    ctx.clearRect(0, 0, this._canvas.width, this._canvas.height);
    
    if (this._currentModel && this._currentModel.loaded) {
      // 모델이 로드된 경우
      ctx.fillStyle = 'rgba(100, 255, 100, 0.1)';
      ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);
      
      ctx.fillStyle = '#4CAF50';
      ctx.font = '14px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(`${this._currentModel.name}`, this._canvas.width / 2, this._canvas.height / 2 - 20);
      ctx.fillText(`Expression: ${this._currentExpression}`, this._canvas.width / 2, this._canvas.height / 2);
      ctx.fillText('Live2D Active', this._canvas.width / 2, this._canvas.height / 2 + 20);
    }
  }

  /**
   * 표정 변경
   */
  async setExpression(expression) {
    try {
      console.log('[Live2DService_Reference2] 표정 변경:', expression);
      
      if (!this._currentModel) {
        console.warn('[Live2DService_Reference2] 모델이 로드되지 않음');
        return;
      }
      
      this._currentExpression = expression;
      console.log('[Live2DService_Reference2] 표정 변경 완료:', expression);
      
    } catch (error) {
      console.error('[Live2DService_Reference2] 표정 변경 실패:', error);
    }
  }

  /**
   * 모션 재생
   */
  async playMotion(motion, priority = 1) {
    try {
      console.log('[Live2DService_Reference2] 모션 재생:', { motion, priority });
      
      if (!this._currentModel) {
        console.warn('[Live2DService_Reference2] 모델이 로드되지 않음');
        return;
      }
      
      console.log('[Live2DService_Reference2] 모션 재생 완료:', motion);
      
    } catch (error) {
      console.error('[Live2DService_Reference2] 모션 재생 실패:', error);
    }
  }

  /**
   * 인터랙션 처리
   */
  async handleInteraction(x, y) {
    try {
      console.log('[Live2DService_Reference2] 인터랙션 처리:', { x, y });
      
      if (!this._currentModel) {
        console.warn('[Live2DService_Reference2] 모델이 로드되지 않음');
        return;
      }
      
      // 클릭 위치에 따른 간단한 반응
      if (y < this._canvas.height / 2) {
        await this.setExpression('joy');
        setTimeout(() => this.setExpression('neutral'), 2000);
      } else {
        await this.playMotion('greeting');
      }
      
    } catch (error) {
      console.error('[Live2DService_Reference2] 인터랙션 처리 실패:', error);
    }
  }

  /**
   * 상태 정보 반환
   */
  getStatus() {
    return {
      initialized: this.isInitialized,
      rendering: this._isRendering,
      model: this._currentModel,
      expression: this._currentExpression,
      canvasSize: this._canvas ? { 
        width: this._canvas.width, 
        height: this._canvas.height 
      } : null
    };
  }

  /**
   * API 메서드들 - 백엔드와의 통신을 시뮬레이션
   */

  /**
   * 상태 조회 API
   */
  async getStatusAPI(sessionId) {
    try {
      console.log('[Live2DService_Reference2] 상태 조회 API 호출:', sessionId);
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 100));
      
      return {
        success: true,
        data: {
          emotion: this._currentExpression,
          motion: null,
          parameters: {}
        }
      };
    } catch (error) {
      console.error('[Live2DService_Reference2] 상태 조회 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 감정 설정 API
   */
  async setEmotionAPI(emotion, sessionId, intensity = 0.8) {
    try {
      console.log('[Live2DService_Reference2] 감정 설정 API 호출:', { emotion, sessionId, intensity });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 로컬 상태 업데이트
      await this.setExpression(emotion);
      
      return { success: true, data: { emotion, intensity } };
    } catch (error) {
      console.error('[Live2DService_Reference2] 감정 설정 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 모션 재생 API
   */
  async playMotionAPI(motion, sessionId, priority = 1) {
    try {
      console.log('[Live2DService_Reference2] 모션 재생 API 호출:', { motion, sessionId, priority });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 로컬 모션 재생
      await this.playMotion(motion, priority);
      
      return { success: true, data: { motion, priority } };
    } catch (error) {
      console.error('[Live2DService_Reference2] 모션 재생 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 텍스트 감정 분석 API
   */
  async analyzeTextEmotionAPI(text, sessionId) {
    try {
      console.log('[Live2DService_Reference2] 텍스트 감정 분석 API 호출:', { text, sessionId });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 간단한 감정 분석 시뮬레이션
      const emotions = ['joy', 'surprise', 'thinking', 'neutral'];
      const motions = ['greeting', 'blessing', 'idle'];
      
      const primaryEmotion = emotions[Math.floor(Math.random() * emotions.length)];
      const recommendedMotion = motions[Math.floor(Math.random() * motions.length)];
      
      return {
        success: true,
        data: {
          primary_emotion: primaryEmotion,
          intensity: 0.8,
          recommended_motion: recommendedMotion,
          analysis: `텍스트 분석 결과: ${primaryEmotion}`
        }
      };
    } catch (error) {
      console.error('[Live2DService_Reference2] 텍스트 감정 분석 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 운세 감정 동기화 API
   */
  async syncFortuneEmotionAPI(fortuneType, sessionId, fortuneResult) {
    try {
      console.log('[Live2DService_Reference2] 운세 감정 동기화 API 호출:', { fortuneType, sessionId, fortuneResult });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 150));
      
      // 운세 결과에 따른 감정 매핑
      const fortuneEmotionMap = {
        'love': 'joy',
        'career': 'thinking',
        'health': 'neutral',
        'money': 'surprise'
      };
      
      const emotion = fortuneEmotionMap[fortuneType] || 'neutral';
      const motion = 'blessing';
      
      return {
        success: true,
        data: {
          emotion,
          motion,
          parameters: {}
        }
      };
    } catch (error) {
      console.error('[Live2DService_Reference2] 운세 감정 동기화 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 통합 상태 설정 API
   */
  async setCombinedStateAPI(emotion, motion, sessionId, parameters = null) {
    try {
      console.log('[Live2DService_Reference2] 통합 상태 설정 API 호출:', { emotion, motion, sessionId, parameters });
      
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 로컬 상태 업데이트
      if (emotion) {
        await this.setExpression(emotion);
      }
      
      if (motion) {
        await this.playMotion(motion);
      }
      
      return { success: true, data: { emotion, motion, parameters } };
    } catch (error) {
      console.error('[Live2DService_Reference2] 통합 상태 설정 API 실패:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * 채팅 메시지 처리 (로컬 폴백)
   */
  async handleChatMessage(text, sessionId) {
    try {
      console.log('[Live2DService_Reference2] 채팅 메시지 처리:', { text, sessionId });
      
      // 간단한 로컬 감정 분석 및 반응
      if (text.includes('안녕') || text.includes('반가')) {
        await this.setExpression('joy');
        await this.playMotion('greeting');
      } else if (text.includes('고마')) {
        await this.setExpression('joy');
        await this.playMotion('blessing');
      } else if (text.includes('?') || text.includes('궁금')) {
        await this.setExpression('thinking');
      } else {
        await this.setExpression('neutral');
      }
      
      console.log('[Live2DService_Reference2] 채팅 메시지 처리 완료');
    } catch (error) {
      console.error('[Live2DService_Reference2] 채팅 메시지 처리 실패:', error);
    }
  }

  /**
   * 운세 결과 처리 (로컬 폴백)
   */
  async handleFortuneResult(fortuneResult, sessionId) {
    try {
      console.log('[Live2DService_Reference2] 운세 결과 처리:', { fortuneResult, sessionId });
      
      // 운세 결과에 따른 감정 반응
      if (fortuneResult && fortuneResult.fortune_type) {
        const fortuneEmotionMap = {
          'love': 'joy',
          'career': 'thinking', 
          'health': 'neutral',
          'money': 'surprise'
        };
        
        const emotion = fortuneEmotionMap[fortuneResult.fortune_type] || 'neutral';
        await this.setExpression(emotion);
        await this.playMotion('blessing');
      }
      
      console.log('[Live2DService_Reference2] 운세 결과 처리 완료');
    } catch (error) {
      console.error('[Live2DService_Reference2] 운세 결과 처리 실패:', error);
    }
  }

  /**
   * 리소스 해제
   */
  dispose() {
    console.log('[Live2DService_Reference2] 리소스 해제...');
    
    this._isRendering = false;
    
    if (this._animationId) {
      cancelAnimationFrame(this._animationId);
      this._animationId = null;
    }
    
    this.isInitialized = false;
    this._currentModel = null;
    
    console.log('[Live2DService_Reference2] 리소스 해제 완료');
  }
}

// 싱글톤 인스턴스
const live2DService = new Live2DServiceReference2();

export default live2DService;
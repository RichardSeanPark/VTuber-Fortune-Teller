/**
 * WebSocket 통신 서비스
 * 백엔드와의 실시간 통신을 담당
 */

import { API_ENDPOINTS } from '../utils/constants';

class WebSocketService {
  constructor() {
    this.ws = null;
    this.baseUrl = API_ENDPOINTS.WEBSOCKET;
    this.sessionId = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
    this.isConnecting = false;
    this.heartbeatInterval = null;
    // Error tracking for deduplication
    this.lastErrors = new Map();
    this.errorCooldownMs = 5000; // 5 seconds cooldown for same error
  }

  // WebSocket 연결 (세션 ID 포함)
  connect(sessionId = null) {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('[WebSocket] 이미 연결되어 있거나 연결 중입니다.');
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        this.isConnecting = true;
        this.sessionId = sessionId;
        
        // 세션 ID를 포함한 WebSocket URL 구성
        const url = sessionId 
          ? `${this.baseUrl}/ws/chat/${sessionId}`
          : `${this.baseUrl}/ws/chat/anonymous`;
          
        console.log(`[WebSocket] 연결 시도: ${url}`);
        
        this.ws = new WebSocket(url);
        
        this.ws.onopen = (event) => {
          console.log('[WebSocket] 연결 성공');
          this.isConnecting = false;
          this.resetReconnectionState();
          this.startHeartbeat();
          this.emit('connect', event);
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] 메시지 수신:', data);
            this.handleMessage(data);
          } catch (error) {
            const parseError = {
              type: 'message_parse_error',
              message: 'WebSocket 메시지 파싱 실패',
              originalError: error,
              rawData: event.data,
              timestamp: new Date().toISOString()
            };
            console.error('[WebSocket] 메시지 파싱 오류:', parseError);
            this.emit('error', parseError);
          }
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] 연결 종료:', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('disconnect', event);
          
          // 자동 재연결 시도
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] 연결 오류:', error);
          this.isConnecting = false;
          
          // 더 상세한 오류 정보 제공
          const enhancedError = {
            type: 'websocket_connection_error',
            source: 'connection_attempt',
            message: this.getConnectionErrorMessage(),
            timestamp: new Date().toISOString(),
            url: url,
            sessionId: this.sessionId,
            baseUrl: this.baseUrl,
            connectionAttempt: this.reconnectAttempts + 1,
            maxAttempts: this.maxReconnectAttempts,
            isRetryable: this.reconnectAttempts < this.maxReconnectAttempts,
            nextRetryIn: this.calculateNextRetryDelay(),
            originalError: error
          };
          
          // 에러 중복 체크
          if (!this.shouldLogError({
            errorType: 'connection_error',
            errorCode: this.reconnectAttempts,
            message: enhancedError.message
          })) {
            reject(enhancedError);
            return;
          }
          
          console.group('🚨 [WebSocket] 연결 오류 상세 정보');
          console.error('연결 URL:', url);
          console.error('기본 URL:', this.baseUrl);
          console.error('세션 ID:', this.sessionId);
          console.error('재시도 횟수:', `${this.reconnectAttempts + 1}/${this.maxReconnectAttempts}`);
          console.error('다음 재시도:', `${enhancedError.nextRetryIn}ms 후`);
          console.error('원본 에러:', error);
          console.groupEnd();
          
          this.emit('error', enhancedError);
          reject(enhancedError);
        };

      } catch (error) {
        this.isConnecting = false;
        console.error('[WebSocket] 연결 초기화 오류:', error);
        reject(error);
      }
    });
  }

  // 메시지 전송
  send(type, data = {}) {
    if (!this.isConnected()) {
      console.warn('[WebSocket] 연결되지 않음. 메시지 전송 실패:', { type, data });
      return false;
    }

    const message = {
      type,
      timestamp: new Date().toISOString(),
      ...data
    };

    try {
      this.ws.send(JSON.stringify(message));
      console.log('[WebSocket] 메시지 전송:', message);
      return true;
    } catch (error) {
      console.error('[WebSocket] 메시지 전송 오류:', error);
      return false;
    }
  }

  // 메시지 핸들링
  handleMessage(data) {
    const { type } = data;
    
    switch (type) {
      case 'fortune_result':
        this.emit('fortuneResult', data);
        break;
      case 'chat_response':
        this.emit('chatResponse', data);
        break;
      case 'live2d_command':
        this.emit('live2dCommand', data);
        break;
      case 'system_status':
        this.emit('systemStatus', data);
        break;
      case 'error':
        this.handleBackendError(data);
        break;
      case 'text_response':
        // 텍스트 응답 메시지 (채팅 응답)
        console.log('[WebSocket] 텍스트 응답 수신:', data);
        this.emit('chatResponse', data);
        break;
      case 'fortune_processing':
        // 운세 처리 중 메시지
        console.log('[WebSocket] 운세 처리 중:', data);
        this.emit('fortuneProcessing', data);
        break;
      case 'pong':
        // 하트비트 응답
        console.log('[WebSocket] 하트비트 응답 수신');
        break;
      default:
        console.log('[WebSocket] 알 수 없는 메시지 타입:', type, data);
        this.emit('message', data);
    }
  }

  // 백엔드 에러 메시지 처리
  handleBackendError(errorData) {
    try {
      const enhancedError = {
        type: 'backend_error',
        source: 'websocket_message',
        timestamp: new Date().toISOString(),
        sessionId: this.sessionId,
        originalData: errorData,
        // 백엔드 에러 정보 추출
        ...this.extractBackendErrorInfo(errorData)
      };

      // 에러 중복 제거 확인
      if (!this.shouldLogError(enhancedError)) {
        return;
      }

      // 상세한 에러 로깅
      console.group('🚨 [WebSocket] 백엔드 에러 수신');
      console.error('에러 타입:', enhancedError.errorType || 'unknown');
      console.error('에러 메시지:', enhancedError.message);
      console.error('에러 코드:', enhancedError.errorCode || 'none');
      console.error('세부 정보:', enhancedError.details);
      console.error('원본 데이터:', errorData);
      console.groupEnd();

      this.emit('error', enhancedError);
    } catch (error) {
      console.error('[WebSocket] 백엔드 에러 처리 중 오류:', error);
      // 원본 데이터라도 전달
      this.emit('error', {
        type: 'backend_error_parse_failed',
        message: '백엔드 에러 파싱 실패',
        originalData: errorData,
        parseError: error
      });
    }
  }

  // 백엔드 에러 정보 추출
  extractBackendErrorInfo(errorData) {
    const extracted = {
      errorType: null,
      errorCode: null,
      message: '예상치 못한 오류가 발생했습니다.',
      details: null,
      severity: 'medium',
      isRetryable: false
    };

    try {
      // data 객체에서 에러 정보 추출
      if (errorData.data) {
        const { data } = errorData;
        
        // 에러 타입
        extracted.errorType = data.error_type || data.type || 'unknown';
        
        // 에러 코드
        extracted.errorCode = data.error_code || data.code || null;
        
        // 에러 메시지
        extracted.message = data.error_message || data.message || 
                          data.detail || extracted.message;
        
        // 추가 세부 정보
        extracted.details = data.details || data.context || null;
        
        // 심각도 판단
        if (data.severity) {
          extracted.severity = data.severity;
        } else if (extracted.errorType) {
          extracted.severity = this.determineSeverity(extracted.errorType);
        }
        
        // 재시도 가능 여부
        extracted.isRetryable = data.retryable !== undefined ? 
                              data.retryable : this.isErrorRetryable(extracted.errorType);
      }
      
      // 직접 메시지가 있는 경우
      if (errorData.message && !extracted.details) {
        extracted.message = errorData.message;
      }
      
    } catch (error) {
      console.warn('[WebSocket] 에러 정보 추출 실패:', error);
    }

    return extracted;
  }

  // 에러 심각도 판단
  determineSeverity(errorType) {
    const criticalErrors = ['database_error', 'authentication_failed', 'system_error'];
    const highErrors = ['validation_error', 'permission_denied', 'rate_limit_exceeded'];
    const lowErrors = ['user_input_error', 'format_error'];
    
    if (criticalErrors.includes(errorType)) return 'critical';
    if (highErrors.includes(errorType)) return 'high';
    if (lowErrors.includes(errorType)) return 'low';
    return 'medium';
  }

  // 에러 재시도 가능 여부 판단
  isErrorRetryable(errorType) {
    const retryableErrors = [
      'network_error', 'timeout_error', 'service_unavailable', 
      'rate_limit_exceeded', 'temporary_failure'
    ];
    return retryableErrors.includes(errorType);
  }

  // 에러 중복 제거 확인
  shouldLogError(errorInfo) {
    const errorKey = `${errorInfo.errorType}_${errorInfo.errorCode}_${errorInfo.message}`;
    const now = Date.now();
    
    if (this.lastErrors.has(errorKey)) {
      const lastTime = this.lastErrors.get(errorKey);
      if (now - lastTime < this.errorCooldownMs) {
        console.log(`[WebSocket] 중복 에러 무시: ${errorKey}`);
        return false;
      }
    }
    
    this.lastErrors.set(errorKey, now);
    
    // 오래된 에러 기록 정리 (메모리 누수 방지)
    this.cleanupOldErrors(now);
    
    return true;
  }

  // 오래된 에러 기록 정리
  cleanupOldErrors(currentTime) {
    for (const [key, timestamp] of this.lastErrors.entries()) {
      if (currentTime - timestamp > this.errorCooldownMs * 2) {
        this.lastErrors.delete(key);
      }
    }
  }

  // 이벤트 리스너 등록
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  // 이벤트 리스너 제거
  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  // 이벤트 발생
  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WebSocket] 이벤트 콜백 오류 (${event}):`, error);
        }
      });
    }
  }

  // 연결 상태 확인
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // 하트비트 시작
  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send('ping');
      }
    }, 30000); // 30초마다 핑 전송
  }

  // 하트비트 중지
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // 연결 오류 메시지 생성
  getConnectionErrorMessage() {
    const messages = {
      1: 'WebSocket 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.',
      2: '서버 연결에 문제가 발생했습니다. 네트워크 연결을 확인해주세요.',
      3: '연결이 불안정합니다. 계속 재시도 중...',
      4: '서버 연결에 심각한 문제가 있습니다. 마지막 시도 중...',
      5: '서버에 연결할 수 없습니다. 페이지를 새로고침해주세요.'
    };
    return messages[this.reconnectAttempts + 1] || messages[5];
  }

  // 다음 재시도 지연 시간 계산
  calculateNextRetryDelay() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return 0;
    }
    return this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
  }

  // 재연결 스케줄링 (개선된 버전)
  scheduleReconnect() {
    this.reconnectAttempts++;
    const delay = this.calculateNextRetryDelay();
    
    if (this.reconnectAttempts > this.maxReconnectAttempts) {
      console.error('[WebSocket] 최대 재연결 시도 초과. 자동 재연결 중단.');
      this.emit('reconnectFailed', {
        attempts: this.reconnectAttempts,
        maxAttempts: this.maxReconnectAttempts,
        message: '자동 재연결에 실패했습니다. 수동으로 재시도하거나 페이지를 새로고침해주세요.'
      });
      return;
    }
    
    console.log(`[WebSocket] ${delay}ms 후 재연결 시도 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
    
    this.reconnectTimeout = setTimeout(async () => {
      if (!this.isConnected() && this.reconnectAttempts <= this.maxReconnectAttempts) {
        try {
          console.log(`[WebSocket] 재연결 시도 ${this.reconnectAttempts} 시작...`);
          await this.connect(this.sessionId);
          console.log('[WebSocket] 재연결 성공!');
        } catch (error) {
          console.error(`[WebSocket] 재연결 시도 ${this.reconnectAttempts} 실패:`, error);
          // 다음 재시도 예약
          this.scheduleReconnect();
        }
      }
    }, delay);
  }

  // 수동 재연결 시도
  async retryConnection() {
    if (this.isConnected()) {
      console.log('[WebSocket] 이미 연결되어 있습니다.');
      return true;
    }

    // 진행 중인 재연결 스케줄 취소
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    try {
      console.log('[WebSocket] 수동 재연결 시도...');
      await this.connect(this.sessionId);
      console.log('[WebSocket] 수동 재연결 성공!');
      return true;
    } catch (error) {
      console.error('[WebSocket] 수동 재연결 실패:', error);
      return false;
    }
  }

  // 재연결 리셋
  resetReconnectionState() {
    this.reconnectAttempts = 0;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.lastErrors.clear();
    console.log('[WebSocket] 재연결 상태 리셋 완료');
  }

  // 연결 종료
  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, '사용자 요청');
      this.ws = null;
    }
    console.log('[WebSocket] 연결 종료됨');
  }

  // 운세 요청 전송
  requestFortune(fortuneType, userData = {}) {
    return this.send('fortune_request', {
      fortune_type: fortuneType,
      user_data: userData
    });
  }

  // 채팅 메시지 전송
  sendChatMessage(message) {
    return this.send('chat_message', {
      message: message,
      timestamp: new Date().toISOString()
    });
  }

  // Live2D 명령 전송
  sendLive2DCommand(command, params = {}) {
    return this.send('live2d_command', {
      command,
      params
    });
  }

  // Live2D WebSocket 연결 (별도 채널)
  connectLive2D(sessionId) {
    return new Promise((resolve, reject) => {
      try {
        const live2dUrl = sessionId 
          ? `${this.baseUrl}/ws/live2d/${sessionId}`
          : `${this.baseUrl}/ws/live2d/anonymous`;
          
        console.log(`[WebSocket] Live2D 연결 시도: ${live2dUrl}`);
        
        this.live2dWs = new WebSocket(live2dUrl);
        
        this.live2dWs.onopen = (event) => {
          console.log('[WebSocket] Live2D 연결 성공');
          this.emit('live2dConnect', event);
          resolve();
        };

        this.live2dWs.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] Live2D 메시지 수신:', data);
            this.emit('live2dMessage', data);
          } catch (error) {
            console.error('[WebSocket] Live2D 메시지 파싱 오류:', error);
          }
        };

        this.live2dWs.onclose = (event) => {
          console.log('[WebSocket] Live2D 연결 종료');
          this.emit('live2dDisconnect', event);
        };

        this.live2dWs.onerror = (error) => {
          console.error('[WebSocket] Live2D 연결 오류:', error);
          this.emit('live2dError', error);
          reject(error);
        };

      } catch (error) {
        console.error('[WebSocket] Live2D 연결 초기화 오류:', error);
        reject(error);
      }
    });
  }

  // Live2D 상태 동기화 전송
  sendLive2DSync(emotion, motion) {
    if (this.live2dWs && this.live2dWs.readyState === WebSocket.OPEN) {
      const message = {
        type: 'sync',
        emotion,
        motion,
        timestamp: new Date().toISOString()
      };
      
      try {
        this.live2dWs.send(JSON.stringify(message));
        console.log('[WebSocket] Live2D 동기화 전송:', message);
        return true;
      } catch (error) {
        console.error('[WebSocket] Live2D 동기화 전송 오류:', error);
        return false;
      }
    }
    return false;
  }

  // 세션 ID 설정
  setSessionId(sessionId) {
    this.sessionId = sessionId;
  }

  // 현재 세션 ID 반환
  getSessionId() {
    return this.sessionId;
  }
}

// 싱글톤 인스턴스 생성
const webSocketService = new WebSocketService();

export default webSocketService;
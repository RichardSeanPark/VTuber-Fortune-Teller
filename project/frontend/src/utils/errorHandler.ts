/**
 * 에러 처리 유틸리티
 * 다양한 에러 타입을 처리하고 사용자 친화적인 메시지를 제공
 */

// 에러 타입 정의
export const ERROR_TYPES = {
  NETWORK: 'network',
  API: 'api',
  WEBSOCKET: 'websocket',
  LIVE2D: 'live2d',
  VALIDATION: 'validation',
  UNKNOWN: 'unknown'
};

// 에러 심각도 정의
export const ERROR_SEVERITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
};

/**
 * 에러 분류 및 처리
 */
export class ErrorHandler {
  static classify(error) {
    if (!error) {
      return {
        type: ERROR_TYPES.UNKNOWN,
        severity: ERROR_SEVERITY.LOW,
        message: '알 수 없는 오류가 발생했습니다.'
      };
    }

    // 브라우저 확장 프로그램 에러 필터링 (무시)
    if (this.isBrowserExtensionError(error)) {
      return {
        type: 'browser_extension',
        severity: ERROR_SEVERITY.LOW,
        message: 'Browser extension error (ignored)',
        shouldIgnore: true,
        originalError: error
      };
    }

    // 네트워크 에러
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return {
        type: ERROR_TYPES.NETWORK,
        severity: ERROR_SEVERITY.HIGH,
        message: '서버에 연결할 수 없습니다. 인터넷 연결을 확인해주세요.',
        originalError: error
      };
    }

    // WebSocket 에러 (개선된 분류)
    if (error.type === 'websocket_connection_error' || error.type === 'backend_error' || 
        error.source === 'websocket_message' || error.source === 'connection_attempt' ||
        (error.message && error.message.includes('WebSocket'))) {
      return this.classifyWebSocketError(error);
    }

    // API 에러
    if (error.status || error.response) {
      const status = error.status || error.response?.status;
      
      if (status >= 400 && status < 500) {
        return {
          type: ERROR_TYPES.API,
          severity: ERROR_SEVERITY.MEDIUM,
          message: this.getAPIErrorMessage(status),
          originalError: error
        };
      }
      
      if (status >= 500) {
        return {
          type: ERROR_TYPES.API,
          severity: ERROR_SEVERITY.HIGH,
          message: '서버에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
          originalError: error
        };
      }
    }

    // Live2D 에러
    if (error.message && error.message.includes('Live2D')) {
      return {
        type: ERROR_TYPES.LIVE2D,
        severity: ERROR_SEVERITY.MEDIUM,
        message: 'Live2D 캐릭터 로딩에 실패했습니다. 브라우저를 새로고침해주세요.',
        originalError: error
      };
    }

    // 검증 에러
    if (error.name === 'ValidationError' || (error.message && error.message.includes('validation'))) {
      return {
        type: ERROR_TYPES.VALIDATION,
        severity: ERROR_SEVERITY.LOW,
        message: error.message || '입력한 정보를 다시 확인해주세요.',
        originalError: error
      };
    }

    // 기본 에러
    return {
      type: ERROR_TYPES.UNKNOWN,
      severity: ERROR_SEVERITY.MEDIUM,
      message: error.message || '예상치 못한 오류가 발생했습니다.',
      originalError: error
    };
  }

  /**
   * WebSocket 에러 세부 분류
   */
  static classifyWebSocketError(error) {
    // 백엔드에서 온 에러 메시지
    if (error.type === 'backend_error') {
      return {
        type: ERROR_TYPES.WEBSOCKET,
        severity: this.mapBackendSeverity(error.severity),
        message: error.message || '백엔드에서 오류가 발생했습니다.',
        originalError: error,
        errorType: error.errorType,
        errorCode: error.errorCode,
        details: error.details,
        isRetryable: error.isRetryable || false,
        source: 'backend'
      };
    }

    // 연결 에러
    if (error.type === 'websocket_connection_error') {
      return {
        type: ERROR_TYPES.WEBSOCKET,
        severity: error.isRetryable ? ERROR_SEVERITY.MEDIUM : ERROR_SEVERITY.HIGH,
        message: error.message || 'WebSocket 연결에 실패했습니다.',
        originalError: error,
        connectionAttempt: error.connectionAttempt,
        maxAttempts: error.maxAttempts,
        nextRetryIn: error.nextRetryIn,
        isRetryable: error.isRetryable || false,
        source: 'connection'
      };
    }

    // 일반 WebSocket 에러
    return {
      type: ERROR_TYPES.WEBSOCKET,
      severity: ERROR_SEVERITY.HIGH,
      message: error.message || '실시간 연결에 문제가 발생했습니다.',
      originalError: error,
      isRetryable: true,
      source: 'websocket'
    };
  }

  /**
   * 백엔드 에러 심각도 매핑
   */
  static mapBackendSeverity(backendSeverity) {
    const severityMap = {
      'low': ERROR_SEVERITY.LOW,
      'medium': ERROR_SEVERITY.MEDIUM,
      'high': ERROR_SEVERITY.HIGH,
      'critical': ERROR_SEVERITY.CRITICAL
    };
    return severityMap[backendSeverity] || ERROR_SEVERITY.MEDIUM;
  }

  static getAPIErrorMessage(status) {
    switch (status) {
      case 400:
        return '잘못된 요청입니다. 입력한 정보를 확인해주세요.';
      case 401:
        return '인증이 필요합니다. 다시 로그인해주세요.';
      case 403:
        return '접근 권한이 없습니다.';
      case 404:
        return '요청한 자원을 찾을 수 없습니다.';
      case 429:
        return '너무 많은 요청을 보냈습니다. 잠시 후 다시 시도해주세요.';
      default:
        return '서버 오류가 발생했습니다.';
    }
  }

  /**
   * 브라우저 확장 프로그램 에러인지 확인
   */
  static isBrowserExtensionError(error) {
    if (!error) return false;
    
    // 에러 메시지 패턴 확인
    const extensionErrorPatterns = [
      'The message port closed before a response was received',
      'Extension context invalidated',
      'Could not establish connection',
      'Receiving end does not exist',
      'Script error',
      'Non-Error promise rejection captured'
    ];
    
    const errorMessage = error.message || error.toString() || '';
    const isMessagePortError = extensionErrorPatterns.some(pattern => 
      errorMessage.includes(pattern)
    );
    
    // 에러 소스 확인 (content.js, background.js 등)
    const isExtensionScript = error.stack && (
      error.stack.includes('content.js') ||
      error.stack.includes('background.js') ||
      error.stack.includes('extension://')
    );
    
    // 파일 이름 확인
    const isExtensionFile = error.filename && (
      error.filename.includes('content.js') ||
      error.filename.includes('background.js') ||
      error.filename.includes('extension://')
    );
    
    return isMessagePortError || isExtensionScript || isExtensionFile;
  }

  /**
   * 에러 로깅
   */
  static log(error, context = {}) {
    const classified = this.classify(error);
    
    // 브라우저 확장 프로그램 에러는 무시
    if (classified.shouldIgnore) {
      return classified;
    }
    
    const logData = {
      timestamp: new Date().toISOString(),
      type: classified.type,
      severity: classified.severity,
      message: classified.message,
      context: context,
      userAgent: navigator.userAgent,
      url: window.location.href,
      originalError: classified.originalError
    };

    // 개발 환경에서는 콘솔에 출력
    if (process.env.NODE_ENV === 'development') {
      console.group(`🚨 [${classified.severity.toUpperCase()}] ${classified.type} Error`);
      console.error('Message:', classified.message);
      console.error('Context:', context);
      console.error('Original Error:', classified.originalError);
      console.groupEnd();
    }

    // 프로덕션 환경에서는 에러 리포팅 서비스로 전송
    if (process.env.NODE_ENV === 'production') {
      this.reportError(logData);
    }

    return classified;
  }

  /**
   * 에러 리포팅 (프로덕션용)
   */
  static reportError(logData) {
    // 여기에 Sentry, LogRocket 등의 에러 리포팅 서비스 연동
    // 예시:
    // Sentry.captureException(logData.originalError, {
    //   tags: { type: logData.type, severity: logData.severity },
    //   extra: logData.context
    // });
    
    console.log('Error reported:', logData);
  }

  /**
   * 재시도 가능한 에러인지 확인 (개선된 버전)
   */
  static isRetryable(error) {
    const classified = this.classify(error);
    
    // 분류된 에러에 isRetryable 정보가 있으면 우선 사용
    if (classified.isRetryable !== undefined) {
      return classified.isRetryable;
    }
    
    // 네트워크 에러나 5xx 서버 에러는 재시도 가능
    if (classified.type === ERROR_TYPES.NETWORK) {
      return true;
    }
    
    if (classified.type === ERROR_TYPES.API && 
        classified.originalError.status >= 500) {
      return true;
    }
    
    // WebSocket 에러는 소스에 따라 결정
    if (classified.type === ERROR_TYPES.WEBSOCKET) {
      // 백엔드 에러 중 일부는 재시도 불가능
      if (classified.source === 'backend' && classified.errorType) {
        const nonRetryableBackendErrors = [
          'authentication_failed', 'permission_denied', 'validation_error', 'user_input_error'
        ];
        return !nonRetryableBackendErrors.includes(classified.errorType);
      }
      return true; // 연결 에러는 기본적으로 재시도 가능
    }
    
    return false;
  }

  /**
   * 에러에 따른 액션 추천 (개선된 버전)
   */
  static getRecommendedActions(error) {
    const classified = this.classify(error);
    
    switch (classified.type) {
      case ERROR_TYPES.NETWORK:
        return [
          { label: '다시 시도', action: 'retry' },
          { label: '인터넷 연결 확인', action: 'check_connection' },
          { label: '페이지 새로고침', action: 'reload' }
        ];
        
      case ERROR_TYPES.WEBSOCKET:
        return this.getWebSocketActions(classified);
        
      case ERROR_TYPES.API:
        if (classified.originalError.status >= 500) {
          return [
            { label: '다시 시도', action: 'retry' },
            { label: '잠시 후 재시도', action: 'wait_retry' }
          ];
        } else {
          return [
            { label: '입력 정보 확인', action: 'check_input' },
            { label: '다시 시도', action: 'retry' }
          ];
        }
        
      case ERROR_TYPES.LIVE2D:
        return [
          { label: '페이지 새로고침', action: 'reload' },
          { label: '브라우저 캐시 삭제', action: 'clear_cache' }
        ];
        
      case ERROR_TYPES.VALIDATION:
        return [
          { label: '입력 정보 수정', action: 'fix_input' }
        ];
        
      default:
        return [
          { label: '다시 시도', action: 'retry' },
          { label: '페이지 새로고침', action: 'reload' }
        ];
    }
  }

  /**
   * WebSocket 에러별 액션 추천
   */
  static getWebSocketActions(classified) {
    // 백엔드 에러인 경우
    if (classified.source === 'backend') {
      const actions = [];
      
      if (classified.isRetryable) {
        actions.push({ label: '다시 시도', action: 'retry' });
      }
      
      // 에러 타입별 특별한 액션
      switch (classified.errorType) {
        case 'authentication_failed':
          actions.push({ label: '다시 로그인', action: 'reauth' });
          break;
        case 'validation_error':
          actions.push({ label: '입력 정보 확인', action: 'check_input' });
          break;
        case 'rate_limit_exceeded':
          actions.push({ label: '잠시 후 재시도', action: 'wait_retry' });
          break;
      }
      
      actions.push({ label: '페이지 새로고침', action: 'reload' });
      return actions;
    }
    
    // 연결 에러인 경우
    if (classified.source === 'connection') {
      const actions = [];
      
      if (classified.isRetryable) {
        actions.push({ label: '재연결 시도', action: 'reconnect' });
        if (classified.nextRetryIn > 0) {
          actions.push({ 
            label: `${Math.ceil(classified.nextRetryIn / 1000)}초 후 자동 재시도`, 
            action: 'wait_auto_retry', 
            disabled: true 
          });
        }
      }
      
      actions.push({ label: '페이지 새로고침', action: 'reload' });
      return actions;
    }
    
    // 기본 WebSocket 에러
    return [
      { label: '재연결 시도', action: 'reconnect' },
      { label: '페이지 새로고침', action: 'reload' }
    ];
  }
}

/**
 * React Hook용 에러 핸들러
 */
export const useErrorHandler = () => {
  const handleError = (error, context = {}) => {
    return ErrorHandler.log(error, context);
  };

  const getErrorActions = (error) => {
    return ErrorHandler.getRecommendedActions(error);
  };

  const isRetryable = (error) => {
    return ErrorHandler.isRetryable(error);
  };

  return {
    handleError,
    getErrorActions,
    isRetryable
  };
};

/**
 * 구성 설정 검증기
 */
export class ConfigValidator {
  /**
   * 현재 구성 설정 정보 반환
   */
  static getCurrentConfig() {
    const config = {
      NODE_ENV: process.env.NODE_ENV,
      REACT_APP_API_BASE_URL: process.env.REACT_APP_API_BASE_URL,
      REACT_APP_WS_BASE_URL: process.env.REACT_APP_WS_BASE_URL,
      REACT_APP_LIVE2D_MODEL_PATH: process.env.REACT_APP_LIVE2D_MODEL_PATH,
      windowLocation: {
        origin: window.location.origin,
        host: window.location.host,
        hostname: window.location.hostname,
        port: window.location.port
      }
    };
    
    console.group('🔧 현재 구성 설정');
    console.log('환경변수:', config);
    console.log('브라우저 위치:', config.windowLocation);
    console.groupEnd();
    
    return config;
  }
  
  /**
   * API 및 WebSocket URL 유효성 검사
   */
  static validateUrls() {
    const config = this.getCurrentConfig();
    const issues = [];
    
    // API Base URL 검사
    const apiBaseUrl = config.REACT_APP_API_BASE_URL || 
      (config.NODE_ENV === 'development' ? 'http://175.118.126.76:8000' : '');
    
    if (!apiBaseUrl) {
      issues.push({
        type: 'missing_api_url',
        severity: 'high',
        message: 'API Base URL이 설정되지 않았습니다.'
      });
    } else if (!apiBaseUrl.startsWith('http')) {
      issues.push({
        type: 'invalid_api_protocol',
        severity: 'high',
        message: `API URL에 프로토콜이 누락되었습니다: ${apiBaseUrl}`
      });
    }
    
    // WebSocket URL 검사
    const wsBaseUrl = config.REACT_APP_WS_BASE_URL || 
      (config.NODE_ENV === 'development' ? 'ws://175.118.126.76:8000' : `ws://${config.windowLocation.host}`);
    
    if (!wsBaseUrl.startsWith('ws')) {
      issues.push({
        type: 'invalid_ws_protocol',
        severity: 'high',
        message: `WebSocket URL에 ws:// 또는 wss:// 프로토콜이 필요합니다: ${wsBaseUrl}`
      });
    }
    
    // 포트 일관성 검사
    const apiPort = this.extractPortFromUrl(apiBaseUrl);
    const wsPort = this.extractPortFromUrl(wsBaseUrl);
    
    if (apiPort && wsPort && apiPort !== wsPort) {
      issues.push({
        type: 'port_mismatch',
        severity: 'medium',
        message: `API 포트(${apiPort})와 WebSocket 포트(${wsPort})가 일치하지 않습니다.`
      });
    }
    
    const validation = {
      config,
      urls: {
        api: apiBaseUrl,
        websocket: wsBaseUrl,
        apiPort,
        wsPort
      },
      issues,
      isValid: issues.filter(issue => issue.severity === 'high').length === 0
    };
    
    if (issues.length > 0) {
      console.group('⚠️ 구성 설정 문제 발견');
      issues.forEach(issue => {
        console.warn(`[${issue.severity.toUpperCase()}] ${issue.type}: ${issue.message}`);
      });
      console.groupEnd();
    } else {
      console.log('✅ 구성 설정 검증 완료 - 문제 없음');
    }
    
    return validation;
  }
  
  /**
   * URL에서 포트 번호 추출
   */
  static extractPortFromUrl(url) {
    if (!url) return null;
    
    try {
      const urlObj = new URL(url);
      return urlObj.port || (urlObj.protocol === 'https:' ? '443' : '80');
    } catch (error) {
      console.warn('URL 파싱 실패:', url, error);
      return null;
    }
  }
  
  /**
   * 네트워크 연결 테스트
   */
  static async testConnectivity() {
    const config = this.validateUrls();
    const results = {
      api: { status: 'unknown', latency: null, error: null },
      websocket: { status: 'unknown', error: null }
    };
    
    // API 연결 테스트
    try {
      const startTime = Date.now();
      const response = await fetch(`${config.urls.api}/health`, {
        method: 'GET',
        timeout: 5000
      });
      const latency = Date.now() - startTime;
      
      results.api = {
        status: response.ok ? 'connected' : 'error',
        latency,
        httpStatus: response.status,
        error: response.ok ? null : `HTTP ${response.status}`
      };
    } catch (error) {
      results.api = {
        status: 'failed',
        latency: null,
        error: error.message
      };
    }
    
    console.group('🌐 네트워크 연결 테스트 결과');
    console.log('API 연결:', results.api);
    console.groupEnd();
    
    return { ...config, connectivity: results };
  }
  
  /**
   * 구성 설정 진단 보고서
   */
  static async generateDiagnosticReport() {
    console.log('🔍 구성 설정 진단 시작...');
    
    const validation = this.validateUrls();
    const connectivity = await this.testConnectivity();
    
    const report = {
      timestamp: new Date().toISOString(),
      validation,
      connectivity: connectivity.connectivity,
      recommendations: []
    };
    
    // 추천사항 생성
    if (validation.issues.length > 0) {
      report.recommendations.push(
        '구성 설정 문제를 해결하세요. .env 파일을 확인하고 올바른 URL과 포트를 설정하세요.'
      );
    }
    
    if (connectivity.connectivity.api.status !== 'connected') {
      report.recommendations.push(
        'API 서버가 실행 중인지 확인하세요. 백엔드 서버가 해당 포트에서 실행되고 있어야 합니다.'
      );
    }
    
    
    console.group('📋 진단 보고서');
    console.log('전체 보고서:', report);
    console.groupEnd();
    
    return report;
  }
}

export default ErrorHandler;
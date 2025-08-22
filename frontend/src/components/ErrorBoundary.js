/**
 * 에러 경계 컴포넌트
 * React 애플리케이션에서 발생하는 JavaScript 에러를 캐치하고 처리
 */

import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // 다음 렌더링에서 폴백 UI가 보이도록 상태를 업데이트 합니다.
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // 에러 로깅
    console.error('[ErrorBoundary] 에러 캐치:', error);
    console.error('[ErrorBoundary] 에러 정보:', errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // 에러 리포팅 서비스에 에러를 보낼 수 있습니다
    // 예: Sentry, LogRocket 등
    if (typeof this.props.onError === 'function') {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      // 커스텀 폴백 UI를 렌더링할 수 있습니다
      return (
        <div className="error-boundary">
          <div className="error-container">
            <div className="error-icon">⚠️</div>
            <h2>앗, 문제가 발생했어요!</h2>
            <p>예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.</p>
            
            {process.env.NODE_ENV === 'development' && (
              <details className="error-details">
                <summary>기술적 세부사항 (개발 모드)</summary>
                <div className="error-info">
                  <h4>에러:</h4>
                  <pre>{this.state.error && this.state.error.toString()}</pre>
                  
                  <h4>스택 트레이스:</h4>
                  <pre>{this.state.errorInfo.componentStack}</pre>
                </div>
              </details>
            )}
            
            <div className="error-actions">
              <button 
                onClick={this.handleRetry}
                className="btn-primary"
              >
                다시 시도
              </button>
              <button 
                onClick={() => window.location.reload()}
                className="btn-secondary"
              >
                페이지 새로고침
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
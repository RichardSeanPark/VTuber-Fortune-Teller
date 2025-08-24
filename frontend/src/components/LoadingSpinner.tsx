/**
 * 로딩 스피너 컴포넌트
 * 다양한 로딩 상태를 표시하는 재사용 가능한 컴포넌트
 */

import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ 
  size = 'medium', 
  message = '로딩 중...', 
  overlay = false,
  type = 'default'
}) => {
  const sizeClass = `spinner-${size}`;
  const typeClass = `spinner-${type}`;
  
  const spinner = (
    <div className={`loading-spinner ${sizeClass} ${typeClass}`}>
      <div className="spinner-container">
        {type === 'dots' ? (
          <div className="spinner-dots">
            <div className="dot"></div>
            <div className="dot"></div>
            <div className="dot"></div>
          </div>
        ) : type === 'pulse' ? (
          <div className="spinner-pulse">
            <div className="pulse-circle"></div>
          </div>
        ) : type === 'fortune' ? (
          <div className="spinner-fortune">
            <div className="fortune-crystal">🔮</div>
            <div className="fortune-sparkles">
              <span>✨</span>
              <span>⭐</span>
              <span>✨</span>
            </div>
          </div>
        ) : (
          <div className="spinner-ring">
            <div></div>
            <div></div>
            <div></div>
            <div></div>
          </div>
        )}
        
        {message && (
          <div className="spinner-message">
            {message}
          </div>
        )}
      </div>
    </div>
  );

  if (overlay) {
    return (
      <div className="loading-overlay">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;
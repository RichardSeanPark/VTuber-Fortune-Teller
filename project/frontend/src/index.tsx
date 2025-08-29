import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App';
import ErrorHandler from './utils/errorHandler';

// 전역 에러 핸들러 설정 (브라우저 확장 프로그램 에러 필터링)
window.addEventListener('error', (event) => {
  const classified = ErrorHandler.classify(event.error);
  if (!classified.shouldIgnore) {
    ErrorHandler.log(event.error, { 
      source: 'window.error',
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno
    });
  }
});

window.addEventListener('unhandledrejection', (event) => {
  const classified = ErrorHandler.classify(event.reason);
  if (!classified.shouldIgnore) {
    ErrorHandler.log(event.reason, { 
      source: 'unhandledrejection',
      type: 'promise'
    });
  }
});

const container = document.getElementById('root');
if (!container) {
  throw new Error('Root element not found');
}

const root = createRoot(container);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
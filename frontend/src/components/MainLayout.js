import React from 'react';
import './MainLayout.css';

const MainLayout = ({ children }) => {
  return (
    <div className="main-layout">
      <header className="app-header">
        <div className="header-content">
          <div className="title-section">
            <h1 className="app-title">
              <span className="title-emoji" role="img" aria-label="crystal ball">🔮</span>
              미라의 운세
              <span className="title-sparkle" role="img" aria-label="sparkles">✨</span>
            </h1>
            <p className="app-subtitle">Live2D 캐릭터와 함께하는 특별한 운세 체험</p>
          </div>
        </div>
      </header>
      
      <main className="app-main">
        {children}
      </main>
      
      <footer className="app-footer">
        <div className="footer-content">
          <p>&copy; 2025 미라의 운세. 재미와 엔터테인먼트를 위한 서비스입니다.</p>
          <div className="footer-links">
            <span>Live2D Technology</span>
            <span className="separator">•</span>
            <span>React Frontend</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default MainLayout;
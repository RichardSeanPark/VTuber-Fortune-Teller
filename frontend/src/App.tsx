import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import MainLayout from './components/MainLayout';
import FortuneSelector from './components/FortuneSelector';
import ChatInterface from './components/ChatInterface';
import FortuneResult from './components/FortuneResult';
import CardDrawing from './components/CardDrawing';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';
import Live2DViewer from './components/Live2DViewer';
import FortuneService from './services/FortuneService';
import UserService from './services/UserService';

export type AppView = 'normal' | 'loading' | 'cardDrawing';

interface FortuneData {
  fortune: string;
  advice: string;
  lucky_number: number;
  lucky_color: string;
}

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>('normal');
  const [fortuneResult, setFortuneResult] = useState<FortuneData | null>(null);
  const [isCardDrawing, setIsCardDrawing] = useState<boolean>(false);
  const [selectedFortune, setSelectedFortune] = useState<string | null>(null);
  
  // Live2D 뷰어 참조 (현재는 실제 Live2D 컴포넌트가 없으므로 null)
  const live2dViewerRef = useRef(null);

  useEffect(() => {
    // UserService initializes automatically in constructor
    console.log('App initialized, UserService ready');
  }, []);

  const handleFortuneSelect = async (fortuneType: any, fortuneResult: any = null) => {
    setSelectedFortune(fortuneType.id);

    if (fortuneType.id === 'tarot' && !fortuneResult) {
      // 타로 카드 선택 화면 표시
      setIsCardDrawing(true);
    } else if (fortuneResult) {
      // 결과가 있으면 바로 모달 표시
      handleFortuneResult(fortuneResult);
    } else {
      // 결과 대기 중
      console.log('운세 결과 대기 중...');
    }
  };

  const handleFortuneResult = (fortuneData: any) => {
    // 운세 결과 처리 및 모달 표시
    setFortuneResult(fortuneData);
  };

  const handleCardSelect = async (selectedCards: any[]) => {
    setCurrentView('loading');
    try {
      // 타로 카드 데이터 구성
      const userData = {
        question: '타로 카드 운세를 알려주세요'
      };
      const extraData = {
        selectedCards
      };
      
      // FortuneService의 getFortuneByType 메서드 사용
      const result = await FortuneService.getFortuneByType('tarot', userData, extraData);
      
      // 결과 데이터 추출 (FortuneSelector와 동일한 로직)
      let actualFortuneData = null;
      if (result && typeof result === 'object') {
        if (result.success === true && result.data) {
          actualFortuneData = { ...result.data };
        } else if (result.type) {
          actualFortuneData = { ...result };
        } else {
          actualFortuneData = { ...result };
        }
      }
      
      // 카드 선택 화면 숨기고 모달 표시
      setIsCardDrawing(false);
      setFortuneResult(actualFortuneData);
      setCurrentView('normal');
    } catch (err) {
      console.error('타로 카드 운세 요청 실패:', err);
      setIsCardDrawing(false);
      setCurrentView('normal');
    }
  };

  const handleBackToSelector = () => {
    setIsCardDrawing(false);
    setCurrentView('normal');
  };

  const handleFortuneClose = () => {
    setFortuneResult(null);
  };

  const handleFortuneRetry = () => {
    setFortuneResult(null);
    // 같은 운세 타입으로 다시 시작
    if (selectedFortune === 'tarot') {
      setIsCardDrawing(true);
    }
    // 다른 운세는 FortuneSelector에서 바로 처리되므로 추가 액션 불필요
  };


  return (
    <ErrorBoundary>
      <div className="App">
        {/* Hidden Live2D Viewer for lip-sync bridge */}
        <div style={{ display: 'none' }}>
          <Live2DViewer 
            ref={live2dViewerRef}
            character="Haru"
            connectionStatus="connected"
          />
        </div>
        
        <div className="app-container">
          <div className="react-container">
            {/* 카드 선택 화면 또는 메인 화면 */}
            {!isCardDrawing ? (
              <>
                {/* Fortune Selector와 Chat Interface를 함께 표시 */}
                <div className="fortune-section">
                  <FortuneSelector onFortuneSelect={handleFortuneSelect} />
                </div>
                <div className="chat-section">
                  <ChatInterface live2dViewerRef={live2dViewerRef} />
                </div>
              </>
            ) : (
              <div className="card-drawing-section">
                <CardDrawing
                  isActive={true}
                  onCardSelect={handleCardSelect}
                  onBack={handleBackToSelector}
                  maxCards={3}
                />
              </div>
            )}
            
            {/* 로딩 표시 */}
            {currentView === 'loading' && (
              <div className="loading-overlay">
                <LoadingSpinner message="운세를 분석하고 있습니다..." />
              </div>
            )}
          </div>
        </div>
        
        {/* Fortune Result Modal */}
        {fortuneResult && (
          <FortuneResult 
            fortuneData={fortuneResult}
            onClose={handleFortuneClose}
            onRetry={handleFortuneRetry}
          />
        )}
      </div>
    </ErrorBoundary>
  );
};

export default App;
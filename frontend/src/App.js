import React, { useState, useEffect } from 'react';
import './App.css';
import MainLayout from './components/MainLayout';
import Live2DViewer from './components/Live2DViewer';
import ChatInterface from './components/ChatInterface';
import FortuneSelector from './components/FortuneSelector';
import FortuneResult from './components/FortuneResult';
import CardDrawing from './components/CardDrawing';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingSpinner from './components/LoadingSpinner';
import webSocketService from './services/WebSocketService';
import live2DService from './services/Live2DService';
import userService from './services/UserService';
import fortuneService from './services/FortuneService';
import { CONNECTION_STATUS, DEBUG_INFO } from './utils/constants';
import { useErrorHandler, ConfigValidator } from './utils/errorHandler';
import { transformApiResponseToFortuneData, validateFortuneData } from './utils/fortuneDataTransform';

function App() {
  const [character] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState(CONNECTION_STATUS.DISCONNECTED);
  const [fortuneResult, setFortuneResult] = useState(null);
  const [isCardDrawing, setIsCardDrawing] = useState(false);
  const [selectedFortune, setSelectedFortune] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [appError, setAppError] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);
  
  const { handleError, getErrorActions, isRetryable } = useErrorHandler();

  useEffect(() => {
    const initializeApp = async () => {
      console.log('[App] Live2D 운세 앱이 시작되었습니다.');
      
      try {
        // 0. 구성 설정 검증 및 진단
        console.log('[App] 구성 설정 진단 시작...');
        DEBUG_INFO.logConfiguration();
        
        // 개발 환경에서 API 연결 테스트
        if (process.env.NODE_ENV === 'development') {
          await DEBUG_INFO.testApiConnection();
        }
        
        const diagnosticReport = await ConfigValidator.generateDiagnosticReport();
        
        if (diagnosticReport.validation.issues.length > 0) {
          console.warn('[App] 구성 설정 문제 발견:', diagnosticReport.validation.issues);
        }
        
        setConnectionStatus(CONNECTION_STATUS.CONNECTING);
        
        // 1. 사용자 서비스 초기화
        const user = userService.getCurrentUser();
        setCurrentUser(user);
        setSessionId(user.sessionId);
        console.log('[App] 사용자 초기화 완료:', user);
        
        // 2. WebSocket 연결 설정
        setupWebSocketEvents();
        
        // 3. WebSocket 연결 시도 (with retry logic)
        try {
          await webSocketService.connect(user.sessionId);
          console.log('[App] WebSocket 연결 성공');
        } catch (wsError) {
          console.warn('[App] WebSocket 초기 연결 실패, 재시도 예정:', wsError);
          // 초기 연결 실패는 치명적이지 않음 - 백그라운드에서 재시도됨
        }
        
        // 4. 세션 생성/갱신
        try {
          await userService.createSession();
          console.log('[App] 백엔드 세션 생성 완료');
        } catch (sessionError) {
          console.warn('[App] 백엔드 세션 생성 실패, 로컬 세션 사용:', sessionError);
        }
        
        setConnectionStatus(CONNECTION_STATUS.CONNECTED);
        console.log('[App] 앱 초기화 완료');
        
      } catch (error) {
        console.error('[App] 앱 초기화 실패:', error);
        setConnectionStatus(CONNECTION_STATUS.ERROR);
        
        const classifiedError = handleError(error, { 
          component: 'App',
          action: 'initialize' 
        });
        
        setAppError(classifiedError.message);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeApp();
    
    return () => {
      cleanup();
    };
  }, []);


  const setupWebSocketEvents = () => {
    webSocketService.on('connect', () => {
      setConnectionStatus(CONNECTION_STATUS.CONNECTED);
      console.log('WebSocket 연결 성공');
    });

    webSocketService.on('disconnect', () => {
      setConnectionStatus(CONNECTION_STATUS.DISCONNECTED);
      console.log('WebSocket 연결 해제');
    });

    webSocketService.on('error', (error) => {
      setConnectionStatus(CONNECTION_STATUS.ERROR);
      
      // 에러 분류 및 처리
      const classifiedError = handleError(error, { 
        component: 'App',
        action: 'websocket_error',
        sessionId: sessionId
      });
      
      // 상세한 에러 로깅
      logDetailedWebSocketError(error, classifiedError);
      
      // 에러 타입별 처리
      handleWebSocketErrorByType(error, classifiedError);
    });
    
    // 재연결 실패 이벤트 처리
    webSocketService.on('reconnectFailed', (failureInfo) => {
      console.error('[App] WebSocket 재연결 완전 실패:', failureInfo);
      setAppError(`서버 연결에 실패했습니다: ${failureInfo.message}`);
    });

    webSocketService.on('fortuneResult', (data) => {
      handleWebSocketFortuneResult(data);
    });

    webSocketService.on('chatResponse', (data) => {
      // 채팅 응답 처리 로직
      console.log('채팅 응답:', data);
    });

    webSocketService.on('live2dCommand', (data) => {
      // Live2D 명령 처리
      handleLive2DCommand(data);
    });
  };

  const handleFortuneSelect = async (fortuneType, fortuneResult = null) => {
    console.log('[App] 선택된 운세 타입:', fortuneType);
    setSelectedFortune(fortuneType);

    if (fortuneType.id === 'tarot' && !fortuneResult) {
      // 타로 카드인 경우 카드 뽑기 화면 표시
      setIsCardDrawing(true);
    } else if (fortuneResult) {
      // 운세 결과가 이미 있는 경우 (API에서 받은 결과)
      handleFortuneResult(fortuneResult);
    } else {
      // 다른 운세는 바로 처리 (이 경우는 FortuneSelector에서 이미 API 호출함)
      console.log('[App] 운세 결과 대기 중...');
    }
  };

  const handleCardSelect = async (selectedCards) => {
    console.log('[App] 선택된 카드들:', selectedCards);
    setIsCardDrawing(false);
    
    try {
      // 실제 타로 API 호출
      const userData = currentUser;
      const tarotResult = await fortuneService.getTarotFortune(userData, selectedCards);
      
      console.log('[App] 타로 운세 결과:', tarotResult);
      setFortuneResult(tarotResult);
      
      // Live2D 캐릭터 반응 (세션 ID 포함)
      if (live2DService.isInitialized) {
        await live2DService.handleFortuneResult(tarotResult, sessionId);
      }
      
    } catch (error) {
      console.error('[App] 타로 운세 요청 실패:', error);
      
      const classifiedError = handleError(error, {
        component: 'App',
        action: 'getTarotFortune',
        userData: { hasUser: !!currentUser, cardCount: selectedCards.length }
      });
      
      // 오류 시 로컬 결과 생성
      const fallbackResult = generateTarotResult(selectedCards);
      setFortuneResult({
        ...fallbackResult,
        error: classifiedError.message,
        isRetryable: isRetryable(error)
      });
    }
  };

  const handleFortuneResult = (fortuneData) => {
    console.log('[App] 운세 결과 처리 (원본):', fortuneData);
    
    // API 응답을 표준화된 형식으로 변환
    const transformedData = transformApiResponseToFortuneData(fortuneData);
    console.log('[App] 변환된 운세 결과:', transformedData);
    
    // 데이터 유효성 검사
    if (!validateFortuneData(transformedData)) {
      console.error('[App] 운세 데이터가 유효하지 않습니다:', transformedData);
      handleError('운세 결과를 표시할 수 없습니다.', { 
        component: 'App', 
        action: 'fortune_data_validation', 
        data: transformedData 
      });
      return;
    }
    
    setFortuneResult(transformedData);
    
    // Live2D 캐릭터 반응 (세션 ID 포함)
    if (live2DService.isInitialized) {
      live2DService.handleFortuneResult(transformedData, sessionId);
    }
  };


  const generateTarotResult = (selectedCards) => {
    const score = Math.floor(Math.random() * 40) + 60;
    
    return {
      type: 'tarot',
      score: score,
      emotion: score >= 80 ? 'excellent' : score >= 60 ? 'good' : 'neutral',
      message: '카드들이 말하는 당신의 운명은... 곧 중요한 변화의 시기가 찾아올 것 같아요. 용기를 가지고 새로운 도전을 해보세요! 🔮',
      cards: selectedCards.map(card => card.id),
      advice: '직감을 믿고 마음의 소리에 귀 기울이세요. 당신이 원하는 것을 얻기 위해서는 먼저 행동을 취해야 합니다.'
    };
  };

  const handleLive2DCommand = async (command) => {
    if (!live2DService.isInitialized) return;

    console.log('[App] Live2D 명령 처리:', command);

    switch (command.type) {
      case 'expression':
        await live2DService.setExpression(command.value, sessionId);
        break;
      case 'motion':
        await live2DService.playMotion(command.value, sessionId);
        break;
      case 'sync':
        // 백엔드에서 동기화 요청
        if (command.emotion) {
          await live2DService.setExpression(command.emotion, sessionId);
        }
        if (command.motion) {
          await live2DService.playMotion(command.motion, sessionId);
        }
        break;
      default:
        console.log('[App] 알 수 없는 Live2D 명령:', command);
    }
  };

  const handleWebSocketFortuneResult = (data) => {
    console.log('[App] WebSocket 운세 결과 수신:', data);
    // WebSocket 데이터 구조에서 실제 운세 결과 추출
    const fortuneData = data.data?.fortune_result || data.data || data;
    console.log('[App] 추출된 운세 데이터:', fortuneData);
    handleFortuneResult(fortuneData);
  };

  const handleChatMessage = (message) => {
    console.log('[App] 채팅 메시지 처리:', message);
    
    // Live2D 캐릭터 반응 (로컬)
    if (live2DService.isInitialized) {
      live2DService.handleChatMessage(message);
    }
    
    // WebSocket으로 메시지 전송은 ChatInterface에서 처리됨
  };

  const handleFortuneClose = () => {
    setFortuneResult(null);
    setSelectedFortune(null);
  };

  const handleFortuneRetry = () => {
    setFortuneResult(null);
    if (selectedFortune) {
      if (selectedFortune.id === 'tarot') {
        setIsCardDrawing(true);
      } else {
        handleFortuneSelect(selectedFortune);
      }
    }
  };

  const cleanup = async () => {
    console.log('[App] 앱 정리 시작...');
    
    try {
      // 세션 종료
      if (sessionId) {
        await userService.endSession();
      }
      
      // WebSocket 연결 해제
      if (webSocketService.isConnected()) {
        webSocketService.disconnect();
      }
      
      // Live2D 리소스 정리
      if (live2DService.isInitialized) {
        live2DService.dispose();
      }
      
      console.log('[App] 앱 정리 완료');
    } catch (error) {
      console.error('[App] 앱 정리 중 오류:', error);
    }
  };

  // WebSocket 에러 상세 로깅
  const logDetailedWebSocketError = (error, classifiedError) => {
    console.group('🚨 [App] WebSocket 에러 처리');
    
    // 기본 에러 정보
    console.error('에러 타입:', error.type || 'unknown');
    console.error('에러 메시지:', classifiedError.message);
    console.error('에러 심각도:', classifiedError.severity);
    
    // 백엔드 에러 세부 정보
    if (error.type === 'backend_error') {
      console.group('백엔드 에러 세부 정보');
      console.error('에러 타입:', error.errorType || 'unknown');
      console.error('에러 코드:', error.errorCode || 'none');
      console.error('세부 내용:', error.details);
      console.error('재시도 가능:', error.isRetryable ? '예' : '아니오');
      console.groupEnd();
    }
    
    // 연결 에러 세부 정보
    if (error.type === 'websocket_connection_error') {
      console.group('연결 에러 세부 정보');
      console.error('연결 시도:', `${error.connectionAttempt}/${error.maxAttempts}`);
      console.error('다음 재시도:', `${error.nextRetryIn}ms 후`);
      console.error('연결 URL:', error.url);
      console.error('세션 ID:', error.sessionId);
      console.groupEnd();
    }
    
    // 추천 액션
    const recommendedActions = getErrorActions(error);
    if (recommendedActions.length > 0) {
      console.log('추천 액션:', recommendedActions.map(action => action.label).join(', '));
    }
    
    console.groupEnd();
  };
  
  // WebSocket 에러 타입별 처리
  const handleWebSocketErrorByType = (error, classifiedError) => {
    // 백엔드 에러 처리
    if (error.type === 'backend_error') {
      // 인증 오류인 경우 세션 재생성 시도
      if (error.errorType === 'authentication_failed') {
        console.log('[App] 인증 오류 - 세션 재생성 시도');
        userService.createSession().then(() => {
          webSocketService.connect(sessionId);
        }).catch(sessionError => {
          console.error('[App] 세션 재생성 실패:', sessionError);
        });
        return;
      }
      
      // 재시도 가능한 백엔드 에러인 경우 단순 재연결
      if (error.isRetryable && classifiedError.severity !== 'critical') {
        setTimeout(() => {
          if (!webSocketService.isConnected()) {
            console.log('[App] 백엔드 에러 재시도...');
            webSocketService.retryConnection();
          }
        }, 2000);
        return;
      }
    }
    
    // 연결 에러 처리
    if (error.type === 'websocket_connection_error') {
      // WebSocketService에서 이미 재연결 처리 중
      console.log('[App] 연결 오류 - WebSocketService에서 재연결 처리 중');
      return;
    }
    
    // 기타 에러는 기본 재연결 시도
    if (classifiedError.severity !== 'critical' && isRetryable(error)) {
      setTimeout(() => {
        if (!webSocketService.isConnected()) {
          console.log('[App] 일반 WebSocket 에러 재시도...');
          webSocketService.connect(sessionId).catch(retryError => {
            console.error('[App] WebSocket 재연결 실패:', retryError);
          });
        }
      }, 3000);
    }
  };

  const handleAppError = (error, errorInfo) => {
    handleError(error, {
      component: 'App',
      action: 'render',
      errorInfo
    });
  };

  const handleRetryInitialization = () => {
    setAppError(null);
    setIsInitializing(true);
    window.location.reload();
  };
  
  // WebSocket 수동 재연결
  const handleManualReconnect = async () => {
    console.log('[App] 수동 WebSocket 재연결 시도...');
    setConnectionStatus(CONNECTION_STATUS.CONNECTING);
    
    try {
      const success = await webSocketService.retryConnection();
      if (success) {
        setConnectionStatus(CONNECTION_STATUS.CONNECTED);
        console.log('[App] 수동 재연결 성공!');
      } else {
        setConnectionStatus(CONNECTION_STATUS.ERROR);
        console.error('[App] 수동 재연결 실패');
      }
    } catch (error) {
      setConnectionStatus(CONNECTION_STATUS.ERROR);
      console.error('[App] 수동 재연결 오류:', error);
    }
  };
  
  // 연결 상태에 따른 표시 (최적화된 간결한 메시지)
  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case CONNECTION_STATUS.CONNECTING:
        return '연결중';
      case CONNECTION_STATUS.CONNECTED:
        return '온라인';
      case CONNECTION_STATUS.DISCONNECTED:
        return '오프라인';
      case CONNECTION_STATUS.ERROR:
        return '오류';
      default:
        return '대기중';
    }
  };

  if (isInitializing) {
    return (
      <div className="App">
        <LoadingSpinner 
          size="large" 
          message="미라 연결중" 
          type="fortune"
          overlay={true}
        />
      </div>
    );
  }

  return (
    <ErrorBoundary onError={handleAppError}>
      <div className="App">
        <MainLayout>
          {appError ? (
            <div className="app-error">
              <div className="error-container">
                <h2>🚨 앱 초기화 오류</h2>
                <p>{appError}</p>
                <div className="error-actions">
                  <button 
                    onClick={handleRetryInitialization}
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
          ) : (
            <div className="app-container">
              {/* 연결 상태 표시바 */}
              <div className={`connection-status-bar ${connectionStatus}`}>
                <div className="connection-info">
                  <span className="status-indicator"></span>
                  <span className="status-text">{getConnectionStatusText()}</span>
                </div>
                {connectionStatus === CONNECTION_STATUS.ERROR && (
                  <button 
                    onClick={handleManualReconnect}
                    className="reconnect-btn"
                    disabled={connectionStatus === CONNECTION_STATUS.CONNECTING}
                  >
                    다시 연결
                  </button>
                )}
              </div>
              
              <div className="left-panel">
                <ErrorBoundary>
                  <Live2DViewer 
                    character={character}
                    connectionStatus={connectionStatus}
                  />
                </ErrorBoundary>
              </div>
              <div className="right-panel">
                {!isCardDrawing && (
                  <>
                    <div className="fortune-section">
                      <ErrorBoundary>
                        <FortuneSelector onFortuneSelect={handleFortuneSelect} />
                      </ErrorBoundary>
                    </div>
                    <div className="chat-section">
                      <ErrorBoundary>
                        <ChatInterface 
                          onMessageSend={handleChatMessage}
                          connectionStatus={connectionStatus}
                        />
                      </ErrorBoundary>
                    </div>
                  </>
                )}
                
                {isCardDrawing && (
                  <div className="card-drawing-section">
                    <ErrorBoundary>
                      <CardDrawing
                        isActive={isCardDrawing}
                        onCardSelect={handleCardSelect}
                        maxCards={3}
                      />
                    </ErrorBoundary>
                  </div>
                )}
              </div>
            </div>
          )}
        </MainLayout>

        {fortuneResult && (
          <ErrorBoundary>
            <FortuneResult
              fortuneData={fortuneResult}
              onClose={handleFortuneClose}
              onRetry={handleFortuneRetry}
            />
          </ErrorBoundary>
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
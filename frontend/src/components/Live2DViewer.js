import React, { useRef, useEffect, useState } from 'react';
import './Live2DViewer.css';
import live2DService from '../services/Live2DService';
import webSocketService from '../services/WebSocketService';
import userService from '../services/UserService';

const Live2DViewer = ({ character, connectionStatus }) => {
  const canvasRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [live2dStatus, setLive2dStatus] = useState('initializing');
  const [currentExpression, setCurrentExpression] = useState('neutral');
  const [currentMotion, setCurrentMotion] = useState(null);
  const [backendSynced, setBackendSynced] = useState(false);
  const sessionId = userService.getSessionId();

  useEffect(() => {
    const initializeLive2D = async () => {
      try {
        setLive2dStatus('loading');
        console.log('[Live2DViewer] Live2D 초기화 시작...');
        
        // Live2D 서비스 초기화
        const canvas = canvasRef.current;
        if (canvas) {
          await live2DService.initialize(canvas);
        }
        
        // WebSocket Live2D 채널 연결
        setupLive2DWebSocket();
        
        // 백엔드 상태 동기화
        await syncWithBackend();
        
        setLive2dStatus('ready');
        setIsLoading(false);
        console.log('[Live2DViewer] Live2D 초기화 완료');
        
      } catch (err) {
        console.error('[Live2DViewer] Live2D 초기화 실패:', err);
        setError(`Live2D 로딩에 실패했습니다: ${err.message}`);
        setLive2dStatus('error');
        setIsLoading(false);
        
        // 실패 시 임시 캔버스 설정
        const canvas = canvasRef.current;
        if (canvas) {
          const ctx = canvas.getContext('2d');
          setupTemporaryCanvas(ctx, canvas.width, canvas.height);
        }
      }
    };

    initializeLive2D();

    // 클린업
    return () => {
      if (live2DService.isInitialized) {
        live2DService.dispose();
      }
      webSocketService.off('live2dMessage', handleLive2DMessage);
    };
  }, []);

  // Live2D WebSocket 설정
  const setupLive2DWebSocket = async () => {
    try {
      // Live2D 전용 WebSocket 연결
      await webSocketService.connectLive2D(sessionId);
      
      // 이벤트 리스너 설정
      webSocketService.on('live2dMessage', handleLive2DMessage);
      webSocketService.on('live2dConnect', () => {
        console.log('[Live2DViewer] Live2D WebSocket 연결 성공');
        setBackendSynced(true);
      });
      webSocketService.on('live2dDisconnect', () => {
        console.log('[Live2DViewer] Live2D WebSocket 연결 해제');
        setBackendSynced(false);
      });
      
    } catch (error) {
      console.error('[Live2DViewer] Live2D WebSocket 설정 실패:', error);
    }
  };

  // Live2D 메시지 처리
  const handleLive2DMessage = (data) => {
    console.log('[Live2DViewer] Live2D 메시지 수신:', data);
    
    switch (data.type) {
      case 'emotion_change':
        if (data.emotion !== currentExpression) {
          setCurrentExpression(data.emotion);
          live2DService.setExpression(data.emotion);
        }
        break;
      
      case 'motion_play':
        setCurrentMotion(data.motion);
        live2DService.playMotion(data.motion);
        break;
      
      case 'sync_state':
        // 백엔드 상태와 동기화
        if (data.emotion) {
          setCurrentExpression(data.emotion);
          live2DService.setExpression(data.emotion);
        }
        if (data.motion) {
          setCurrentMotion(data.motion);
          live2DService.playMotion(data.motion);
        }
        break;
      
      default:
        console.log('[Live2DViewer] 알 수 없는 Live2D 메시지:', data);
    }
  };

  // 백엔드와 상태 동기화
  const syncWithBackend = async () => {
    try {
      if (sessionId) {
        const backendStatus = await live2DService.getStatusAPI(sessionId);
        console.log('[Live2DViewer] 백엔드 상태:', backendStatus);
        
        // 백엔드 상태로 동기화
        if (backendStatus.emotion && backendStatus.emotion !== currentExpression) {
          setCurrentExpression(backendStatus.emotion);
          live2DService.setExpression(backendStatus.emotion);
        }
        
        setBackendSynced(true);
      }
    } catch (error) {
      console.error('[Live2DViewer] 백엔드 동기화 실패:', error);
      setBackendSynced(false);
    }
  };


  const setupTemporaryCanvas = (ctx, width, height) => {
    // 임시 배경 설정 (실제로는 Live2D 모델 렌더링)
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, '#4facfe');
    gradient.addColorStop(1, '#00f2fe');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);
    
    // 임시 캐릭터 플레이스홀더
    ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.fillRect(width * 0.25, height * 0.3, width * 0.5, height * 0.6);
    
    // 텍스트 추가
    ctx.fillStyle = 'white';
    ctx.font = '18px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('미라 (Live2D 캐릭터)', width / 2, height / 2);
    ctx.font = '14px Arial';
    ctx.fillText('Live2D SDK 연동 예정', width / 2, height / 2 + 30);
  };

  const handleCanvasClick = async (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    console.log('[Live2DViewer] 캐릭터 클릭:', { x, y });
    
    try {
      // Live2D 인터랙션 처리
      if (live2DService.isInitialized) {
        await live2DService.handleInteraction(x, y);
      }
      
      // 백엔드에 인터랙션 알림 (WebSocket으로 동기화)
      if (backendSynced) {
        webSocketService.sendLive2DSync(currentExpression, 'interaction');
      }
      
      // 시각적 피드백
      showInteractionFeedback(x, y);
      
    } catch (error) {
      console.error('[Live2DViewer] 인터랙션 처리 실패:', error);
    }
  };

  const showInteractionFeedback = (x, y) => {
    // 클릭 피드백 효과 (임시)
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    ctx.save();
    ctx.globalAlpha = 0.7;
    ctx.fillStyle = '#ffd700';
    ctx.beginPath();
    ctx.arc(x, y, 20, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    
    // 1초 후 다시 그리기
    setTimeout(() => {
      setupTemporaryCanvas(ctx, canvas.width, canvas.height);
    }, 1000);
  };

  return (
    <div className="live2d-viewer">
      <div className="viewer-header">
        <h3>Live2D 캐릭터</h3>
        <div className={`status-badge status-${live2dStatus}`}>
          {live2dStatus === 'loading' && '로딩 중...'}
          {live2dStatus === 'ready' && '준비 완료'}
          {live2dStatus === 'error' && '오류'}
          {live2dStatus === 'initializing' && '초기화 중...'}
        </div>
      </div>
      
      <div className="canvas-container">
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
            <p>Live2D 캐릭터를 불러오는 중...</p>
          </div>
        )}
        
        {error && (
          <div className="error-overlay">
            <div className="error-icon">⚠️</div>
            <p>{error}</p>
            <button onClick={() => {
              const retryInitialize = async () => {
                try {
                  setError(null);
                  setIsLoading(true);
                  setLive2dStatus('loading');
                  
                  // Live2D SDK 로딩 확인 (향후 실제 Live2D SDK 연동)
                  console.log('Live2D 초기화 재시도...');
                  
                  // 임시 시뮬레이션 - 실제로는 Live2D SDK 로드
                  await new Promise(resolve => setTimeout(resolve, 2000));
                  
                  // Canvas 초기화
                  const canvas = canvasRef.current;
                  if (canvas) {
                    const ctx = canvas.getContext('2d');
                    setupTemporaryCanvas(ctx, canvas.width, canvas.height);
                  }
                  
                  setLive2dStatus('ready');
                  setIsLoading(false);
                  console.log('Live2D 초기화 완료');
                  
                } catch (err) {
                  console.error('Live2D 초기화 실패:', err);
                  setError('Live2D 로딩에 실패했습니다.');
                  setLive2dStatus('error');
                  setIsLoading(false);
                }
              };
              retryInitialize();
            }} className="retry-button">
              다시 시도
            </button>
          </div>
        )}
        
        <canvas
          ref={canvasRef}
          width={400}
          height={500}
          onClick={handleCanvasClick}
          className="live2d-canvas"
        />
      </div>
      
      <div className="character-info">
        <div className="character-details">
          <p><strong>캐릭터:</strong> 미라 (Mira)</p>
          <p><strong>연결:</strong> {connectionStatus === 'connected' ? '✅ 온라인' : connectionStatus === 'connecting' ? '🔄 연결중' : '⚪ 오프라인'}</p>
          <p><strong>Live2D 상태:</strong> {live2dStatus}</p>
          <p><strong>백엔드 동기화:</strong> {backendSynced ? '✅ 연결됨' : '❌ 연결 안됨'}</p>
        </div>
        
        <div className="live2d-status">
          <p><strong>현재 표정:</strong> {currentExpression}</p>
          {currentMotion && <p><strong>실행 중인 모션:</strong> {currentMotion}</p>}
        </div>
        
        <div className="interaction-guide">
          <p>💡 캐릭터를 클릭해서 인터랙션하세요!</p>
          {live2dStatus === 'ready' && (
            <p>🎭 미라가 당신의 메시지와 운세에 반응합니다</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Live2DViewer;
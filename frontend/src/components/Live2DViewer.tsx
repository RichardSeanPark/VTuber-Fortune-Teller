import React, { useRef, useEffect, useState } from 'react';
import './Live2DViewer.css';
import live2DService from '../services/Live2DService_Reference2_Pure';
import { useLive2DSync } from '../hooks/useLive2DSync';
import userService from '../services/UserService';

const Live2DViewer = React.forwardRef(({ character, connectionStatus, onEmotionChange, onMotionPlay }, ref) => {
  const canvasRef = useRef(null);
  const characterRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [live2dStatus, setLive2dStatus] = useState('initializing');
  const sessionId = userService.getSessionId();

  // Live2D 실시간 동기화 Hook 사용
  const {
    isConnected: live2dConnected,
    currentEmotion,
    currentMotion,
    backendSynced,
    modelInfo,
    connectionStats,
    changeEmotion,
    playMotion,
    analyzeAndReact,
    syncWithFortune,
    setCombinedState,
    checkBackendSync
  } = useLive2DSync(characterRef);

  useEffect(() => {
    const initializeLive2D = async () => {
      try {
        setLive2dStatus('loading');
        console.log('[Live2DViewer] Live2D 초기화 시작...');
        
        // Live2D 서비스 초기화
        const canvas = canvasRef.current;
        if (canvas) {
          await live2DService.initialize(canvas);
          
          // Debug: Expose service on window for testing
          if (typeof window !== 'undefined') {
            window.live2DService = live2DService;
            console.log('[Live2DViewer] Live2D service exposed on window for debugging');
          }
          
          // characterRef에 Live2D 제어 메서드 연결
          characterRef.current = {
            changeExpression: (emotion, duration) => live2DService.setExpression(emotion),
            playMotion: (motion, priority) => live2DService.playMotion(motion),
            updateParameters: (parameters) => {
              console.log('[Live2DViewer] 파라미터 업데이트 (향후 구현):', parameters);
            },
            getStatus: () => live2DService.getStatus()
          };
        }
        
        // 로컬 모델 로드
        await live2DService.loadModel(character || 'Haru');
        
        // 백엔드 모델 로드
        if (sessionId) {
          try {
            await live2DService.loadModelAPI(character || 'Haru', sessionId);
          } catch (modelError) {
            console.warn('[Live2DViewer] 백엔드 모델 로드 실패, 로컬만 사용:', modelError);
          }
        }
        
        setLive2dStatus('ready');
        setIsLoading(false);
        console.log('[Live2DViewer] Live2D 초기화 완료');
        
      } catch (err) {
        console.error('[Live2DViewer] Live2D 초기화 실패:', err);
        setError(`Live2D 로딩에 실패했습니다: ${err.message}`);
        setLive2dStatus('error');
        setIsLoading(false);
      }
      
      // Live2D 서비스가 이미 Canvas를 처리하므로 여기서는 추가 설정 불필요
      console.log('[Live2DViewer] Live2D 서비스가 Canvas 렌더링을 담당합니다.');
    };

    initializeLive2D();

    // 클린업
    return () => {
      if (live2DService.isInitialized) {
        live2DService.dispose();
      }
      characterRef.current = null;
    };
  }, [character, sessionId]);

  // 감정/모션 변화 콜백 (부모 컴포넌트에 알림)
  useEffect(() => {
    if (onEmotionChange && currentEmotion) {
      onEmotionChange(currentEmotion);
    }
    
    console.log('[Live2DViewer] 감정 변경:', currentEmotion);
    // Live2D 서비스가 렌더링을 담당하므로 여기서는 로깅만
  }, [currentEmotion, onEmotionChange, live2dStatus]);

  useEffect(() => {
    if (onMotionPlay && currentMotion) {
      onMotionPlay(currentMotion);
    }
    
    console.log('[Live2DViewer] 모션 변경:', currentMotion);
    // Live2D 서비스가 렌더링을 담당하므로 여기서는 로깅만
  }, [currentMotion, onMotionPlay, live2dStatus]);

  // 외부에서 호출할 수 있는 메서드들을 ref로 노출
  React.useImperativeHandle(ref, () => ({
    // 감정 변경
    changeEmotion: (emotion, intensity = 0.8, duration = 0.5) => 
      changeEmotion(emotion, intensity, duration),
    
    // 모션 재생  
    playMotion: (motion, priority = 1) => 
      playMotion(motion, priority),
    
    // 텍스트 감정 분석 및 반응
    analyzeAndReact: (text) => 
      analyzeAndReact(text),
    
    // 운세와 동기화
    syncWithFortune: (fortuneType, fortuneResult) => 
      syncWithFortune(fortuneType, fortuneResult),
    
    // 통합 상태 설정
    setCombinedState: (emotion, motion, parameters) => 
      setCombinedState(emotion, motion, parameters),
    
    // 백엔드 동기화 확인
    checkBackendSync: () => 
      checkBackendSync(),
    
    // 현재 상태 조회
    getStatus: () => ({
      live2dStatus,
      currentEmotion,
      currentMotion,
      backendSynced,
      live2dConnected,
      modelInfo,
      connectionStats,
      isLoading,
      error
    }),
    
    // Live2D 서비스 상태
    getLive2DServiceStatus: () => 
      live2DService.getStatus()
  }), [
    changeEmotion, 
    playMotion, 
    analyzeAndReact, 
    syncWithFortune, 
    setCombinedState, 
    checkBackendSync,
    live2dStatus,
    currentEmotion,
    currentMotion,
    backendSynced,
    live2dConnected,
    modelInfo,
    connectionStats,
    isLoading,
    error
  ]);


  // Live2D 서비스가 모든 렌더링을 담당하므로 별도 함수 불필요

  const handleCanvasClick = async (event) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    console.log('[Live2DViewer] 캐릭터 클릭:', { x, y });
    
    try {
      // Live2D 인터랙션 처리 (로컬)
      if (live2DService.isInitialized) {
        await live2DService.handleInteraction(x, y);
      }
      
      // 클릭 위치에 따른 감정/모션 결정
      const canvasRect = canvas.getBoundingClientRect();
      const relativeY = y / canvasRect.height;
      
      if (relativeY < 0.5) {
        // 상단 클릭 (얼굴 영역) - 표정 변경
        const expressions = ['joy', 'surprise', 'playful'];
        const randomExpression = expressions[Math.floor(Math.random() * expressions.length)];
        await changeEmotion(randomExpression, 0.8, 0.5);
        
        // 잠시 후 기본 표정으로 복귀
        setTimeout(() => {
          changeEmotion('neutral', 0.5, 0.5);
        }, 3000);
      } else {
        // 하단 클릭 (몸체 영역) - 인사 모션
        await playMotion('greeting', 1);
      }
      
      // 시각적 피드백
      showInteractionFeedback(x, y);
      
    } catch (error) {
      console.error('[Live2DViewer] 인터랙션 처리 실패:', error);
    }
  };

  const showInteractionFeedback = (x, y) => {
    // 클릭 피드백 효과 - Live2D 서비스에 위임
    console.log('[Live2DViewer] 클릭 피드백:', { x, y });
    
    // Live2D 서비스가 초기화되어 있으면 WebGL로 처리
    if (live2DService.isInitialized) {
      console.log('[Live2DViewer] Live2D 서비스에서 클릭 피드백 처리');
      return;
    }
    
    // Live2D 서비스가 아직 초기화되지 않은 경우 간단한 로그만 출력
    console.log('[Live2DViewer] Live2D 서비스가 아직 초기화되지 않음 - 클릭 피드백 생략');
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
                  
                  // Live2D 서비스를 통한 초기화
                  const canvas = canvasRef.current;
                  if (canvas) {
                    await live2DService.initialize(canvas);
                    await live2DService.loadModel(character || 'mao_pro');
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
          <p><strong>캐릭터:</strong> {character || 'Mao Pro'}</p>
          <p><strong>채팅 연결:</strong> {connectionStatus === 'connected' ? '✅ 온라인' : connectionStatus === 'connecting' ? '🔄 연결중' : '⚪ 오프라인'}</p>
          <p><strong>Live2D 연결:</strong> {live2dConnected ? '✅ 연결됨' : '❌ 연결 안됨'}</p>
          <p><strong>Live2D 상태:</strong> {live2dStatus}</p>
          <p><strong>백엔드 동기화:</strong> {backendSynced ? '✅ 동기화됨' : '❌ 동기화 안됨'}</p>
        </div>
        
        <div className="live2d-status">
          <p><strong>현재 표정:</strong> {currentEmotion}</p>
          {currentMotion && <p><strong>실행 중인 모션:</strong> {currentMotion}</p>}
          {modelInfo && <p><strong>모델 정보:</strong> {modelInfo.name || modelInfo.model_name}</p>}
        </div>
        
        <div className="connection-stats">
          <p><strong>메시지 송신:</strong> {connectionStats.messagesSent}</p>
          <p><strong>메시지 수신:</strong> {connectionStats.messagesReceived}</p>
          <p><strong>오류 수:</strong> {connectionStats.errors}</p>
          {connectionStats.lastSync && (
            <p><strong>마지막 동기화:</strong> {new Date(connectionStats.lastSync).toLocaleTimeString()}</p>
          )}
        </div>
        
        <div className="interaction-guide">
          <p>💡 캐릭터를 클릭해서 인터랙션하세요!</p>
          {live2dStatus === 'ready' && (
            <p>🎭 {character || 'Mao'}가 당신의 메시지와 운세에 반응합니다</p>
          )}
          <div className="interaction-buttons">
            <button 
              onClick={() => changeEmotion('joy', 0.8)} 
              disabled={live2dStatus !== 'ready'}
              className="emotion-btn"
            >
              😊 기쁨
            </button>
            <button 
              onClick={() => changeEmotion('surprise', 0.8)} 
              disabled={live2dStatus !== 'ready'}
              className="emotion-btn"
            >
              😲 놀람
            </button>
            <button 
              onClick={() => changeEmotion('thinking', 0.8)} 
              disabled={live2dStatus !== 'ready'}
              className="emotion-btn"
            >
              🤔 생각
            </button>
            <button 
              onClick={() => playMotion('greeting', 1)} 
              disabled={live2dStatus !== 'ready'}
              className="motion-btn"
            >
              👋 인사
            </button>
            <button 
              onClick={() => playMotion('blessing', 1)} 
              disabled={live2dStatus !== 'ready'}
              className="motion-btn"
            >
              🙏 축복
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

Live2DViewer.displayName = 'Live2DViewer';

export default Live2DViewer;
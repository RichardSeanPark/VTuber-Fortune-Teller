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
        // Live2D initialization starting
        
        // Live2D 서비스 초기화
        const canvas = canvasRef.current;
        if (canvas) {
          await live2DService.initialize(canvas);
          
          // Debug: Expose service on window for testing
          if (typeof window !== 'undefined') {
            window.live2DService = live2DService;
            // characterRef의 디버그 함수를 window에도 노출
            window.debugLive2D = () => {
              if (characterRef.current && characterRef.current.debugLive2DStatus) {
                characterRef.current.debugLive2DStatus();
              } else {
                console.warn('debugLive2DStatus not available');
              }
            };
            // Live2D service exposed for debugging
          }
          
          // characterRef에 Live2D 제어 메서드 연결
          characterRef.current = {
            changeExpression: (emotion, duration) => live2DService.setExpression(emotion),
            playMotion: (motion, priority) => live2DService.playMotion(motion),
            updateParameters: (parameters) => {
              // updateParameters called
              
              // HTML Live2D 시스템 접근
              const lappDelegate = (window as any).lappDelegate;
              if (!lappDelegate) {
                console.warn('❌ [Live2DViewer] window.lappDelegate not found - Live2D 시스템이 준비되지 않음');
                return;
              }
              // lappDelegate found
              
              const subdelegates = lappDelegate._subdelegates;
              if (!subdelegates || subdelegates.getSize() === 0) {
                console.warn('❌ [Live2DViewer] No subdelegates found - Live2D 모델이 로드되지 않음');
                return;
              }
              // subdelegates found
              
              const subdelegate = subdelegates.at(0);
              const live2DManager = subdelegate.getLive2DManager();
              
              if (!live2DManager || !live2DManager._models) {
                console.warn('❌ [Live2DViewer] No Live2D manager or models');
                return;
              }
              // live2DManager found
              
              const lappModel = live2DManager._models.at(0);
              if (!lappModel || !lappModel._model) {
                console.warn('❌ [Live2DViewer] No model found');
                return;
              }
              // lappModel found
              
              // 각 파라미터를 Live2D 모델에 직접 적용
              Object.keys(parameters).forEach(paramName => {
                const paramValue = parameters[paramName];
                
                try {
                  // Live2D 모델의 파라미터 ID 찾기
                  const paramId = lappModel._model.getParameterIndex(paramName);
                  if (paramId >= 0) {
                    // 파라미터 값 설정 (범위: -30 ~ 30 또는 모델 정의에 따라)
                    const clampedValue = Math.max(-30, Math.min(30, paramValue));
                    lappModel._model.setParameterValueById(paramName, clampedValue);
                  }
                } catch (error) {
                  console.error(`Live2D parameter error ${paramName}:`, error);
                }
              });
              
              // 특별히 ParamMouthOpenY의 경우 WAV Handler 오버라이드도 병행
              if (lappModel._wavFileHandler && parameters.ParamMouthOpenY !== undefined) {
                const value = Math.max(0, Math.min(1, parameters.ParamMouthOpenY));
                
                // WAV Handler가 우리가 원하는 값을 반환하도록 오버라이드
                lappModel._wavFileHandler.getRms = function() {
                  return value;
                };
                
                // 또한 _lastRms도 직접 설정
                if (lappModel._wavFileHandler._lastRms !== undefined) {
                  lappModel._wavFileHandler._lastRms = value;
                }
              }
              
              // Parameters applied to Live2D model
            },
            getStatus: () => live2DService.getStatus(),
            
            // 디버깅용 Live2D 상태 확인
            debugLive2DStatus: () => {
              console.log('=== Live2D Debug Status ===');
              const lappDelegate = (window as any).lappDelegate;
              console.log('LAppDelegate:', lappDelegate);
              
              if (lappDelegate && lappDelegate._subdelegates) {
                console.log('Subdelegates size:', lappDelegate._subdelegates.getSize());
                const subdelegate = lappDelegate._subdelegates.at(0);
                console.log('First subdelegate:', subdelegate);
                
                if (subdelegate) {
                  const live2DManager = subdelegate.getLive2DManager();
                  console.log('Live2DManager:', live2DManager);
                  
                  if (live2DManager && live2DManager._models) {
                    console.log('Models size:', live2DManager._models.getSize());
                    const model = live2DManager._models.at(0);
                    console.log('First model:', model);
                    
                    if (model) {
                      console.log('Model _lipSyncIds:', model._lipSyncIds);
                      console.log('Model _model:', model._model);
                      
                      if (model._lipSyncIds) {
                        console.log('LipSync IDs count:', model._lipSyncIds.getSize());
                        for (let i = 0; i < model._lipSyncIds.getSize(); i++) {
                          const id = model._lipSyncIds.at(i);
                          console.log(`  LipSync ID[${i}]:`, id?.s || id);
                        }
                      }
                    }
                  }
                }
              }
              console.log('=== End Debug Status ===');
            }
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
        // Live2D initialization completed
        
      } catch (err) {
        console.error('[Live2DViewer] Live2D 초기화 실패:', err);
        setError(`Live2D 로딩에 실패했습니다: ${err.message}`);
        setLive2dStatus('error');
        setIsLoading(false);
      }
      
      // Live2D 서비스가 이미 Canvas를 처리하므로 여기서는 추가 설정 불필요
      // Live2D service handles Canvas rendering
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
    
    // Emotion changed, handled by Live2D service
  }, [currentEmotion, onEmotionChange, live2dStatus]);

  useEffect(() => {
    if (onMotionPlay && currentMotion) {
      onMotionPlay(currentMotion);
    }
    
    // Motion changed, handled by Live2D service
  }, [currentMotion, onMotionPlay, live2dStatus]);

  // startSimpleTalkingAnimation 제거 - 백엔드 데이터만 사용

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
    
    // 립싱크 파라미터 업데이트 (HTML Live2D와 브릿지)
    updateParameters: (parameters) => {
      if (characterRef.current && characterRef.current.updateParameters) {
        characterRef.current.updateParameters(parameters);
      }
    },

    // startTalking 제거 - 백엔드 립싱크 데이터만 사용

    // 립싱크 애니메이션 재생
    playLipSync: (lipSyncData) => {
      // Playing lip-sync animation
      
      if (!lipSyncData || !lipSyncData.mouth_shapes || !Array.isArray(lipSyncData.mouth_shapes)) {
        // Invalid lip-sync data
        return;
      }

      const mouthShapes = lipSyncData.mouth_shapes;
      // Mouth shapes validated
      let currentIndex = 0;
      const startTime = Date.now();

      const playFrame = () => {
        if (currentIndex >= mouthShapes.length) {
          console.log('🎬 [립싱크 종료] 모든 프레임 완료, 페이드아웃 시작 - 프레임:', mouthShapes.length);
          // 애니메이션 완료 - 부드럽게 입을 닫기
          if (characterRef.current && characterRef.current.updateParameters) {
            // 부드러운 페이드아웃 효과를 위해 점진적으로 입을 닫기
            let fadeStep = 0;
            const fadeInterval = setInterval(() => {
              const fadeAmount = 1.0 - (fadeStep * 0.2); // 5단계로 페이드
              console.log(`🎬 [페이드아웃] 단계 ${fadeStep + 1}/5, fadeAmount: ${fadeAmount.toFixed(2)}`);
              if (fadeAmount <= 0 || !characterRef.current) {
                clearInterval(fadeInterval);
                console.log('🎬 [립싱크 완전 종료] 페이드아웃 완료, 입 완전히 닫음');
                if (characterRef.current && characterRef.current.updateParameters) {
                  characterRef.current.updateParameters({
                    ParamMouthOpenY: 0.0,
                    ParamMouthForm: 0.0,
                    ParamMouthOpenX: 0.0
                  });
                }
                return;
              }
              
              if (characterRef.current.updateParameters) {
                characterRef.current.updateParameters({
                  ParamMouthOpenY: fadeAmount * 0.8,     // 더 큰 시작값에서 페이드
                  ParamMouthForm: fadeAmount * 0.6,      // 더 큰 시작값에서 페이드
                  ParamMouthOpenX: fadeAmount * 0.6,     // 더 큰 시작값에서 페이드
                  ParamMouthUp: fadeAmount * 0.5,
                  ParamMouthDown: fadeAmount * 0.5
                });
              }
              fadeStep++;
            }, 50); // 50ms 간격으로 페이드
          }
          // Lip-sync animation completed, closing mouth smoothly
          return;
        }

        const frame = mouthShapes[currentIndex];
        const [timestamp, parameters] = frame;
        const elapsed = (Date.now() - startTime) / 1000.0;

        // 현재 시간에 맞는 프레임인지 확인
        if (elapsed >= timestamp) {
          // Playing frame
          // Processing parameters
          
          if (characterRef.current && characterRef.current.updateParameters) {
            // 간단한 입 움직임 (복잡한 한글 모음 분석 없이)
            const simpleParameters = {
              ParamMouthOpenY: Math.max(0.3, Math.min(1.0, parameters.ParamMouthOpenY || 0.5)),
              ParamMouthForm: 0.0,  // 중립 표정
              ParamMouthOpenX: Math.max(0.2, Math.min(0.8, parameters.ParamMouthOpenX || 0.4))
            };
            
            characterRef.current.updateParameters(simpleParameters);
          } else {
            // Character ref not available
          }
          currentIndex++;
        }

        // 더 부드러운 애니메이션을 위한 타이머 설정 (60fps = 16ms)
        setTimeout(playFrame, 16);
      };

      // 애니메이션 시작
      playFrame();
    },
    
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
    
    // Character clicked
    
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
    // Click feedback
    
    // Live2D 서비스가 초기화되어 있으면 WebGL로 처리
    if (live2DService.isInitialized) {
      // Live2D service handling click feedback
      return;
    }
    
    // Live2D 서비스가 아직 초기화되지 않은 경우 간단한 로그만 출력
    // Live2D service not initialized, skipping click feedback
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
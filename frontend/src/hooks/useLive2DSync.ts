/**
 * Live2D 실시간 상태 동기화 Hook
 * WebSocket을 통한 Live2D 상태 동기화 및 백엔드 API 연동
 */

import { useEffect, useRef, useCallback, useState } from 'react';
import live2DService from '../services/Live2DService_Reference2_Pure';
import webSocketService from '../services/WebSocketService';
import userService from '../services/UserService';

export const useLive2DSync = (characterRef) => {
  const [isConnected, setIsConnected] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState('neutral');
  const [currentMotion, setCurrentMotion] = useState(null);
  const [backendSynced, setBackendSynced] = useState(false);
  const [modelInfo, setModelInfo] = useState(null);
  const [connectionStats, setConnectionStats] = useState({
    messagesSent: 0,
    messagesReceived: 0,
    lastSync: null,
    errors: 0
  });
  
  const sessionId = useRef(userService.getSessionId());
  const syncTimer = useRef(null);
  const statsTimer = useRef(null);

  // WebSocket 메시지 핸들러
  const handleLive2DMessage = useCallback((data) => {
    console.log('[useLive2DSync] Live2D 메시지 수신:', data);
    
    setConnectionStats(prev => ({
      ...prev,
      messagesReceived: prev.messagesReceived + 1,
      lastSync: new Date().toISOString()
    }));

    try {
      switch (data.type) {
        case 'emotion_change':
          if (data.emotion !== currentEmotion) {
            setCurrentEmotion(data.emotion);
            if (characterRef.current) {
              characterRef.current.changeExpression?.(data.emotion, data.duration || 0.5);
            }
          }
          break;
        
        case 'motion_trigger':
          setCurrentMotion(data.motion);
          if (characterRef.current) {
            characterRef.current.playMotion?.(data.motion, data.priority || 1);
          }
          // 모션 완료 후 상태 초기화
          setTimeout(() => setCurrentMotion(null), data.duration || 3000);
          break;
        
        case 'state_sync':
          // 백엔드 상태와 전체 동기화
          if (data.emotion) {
            setCurrentEmotion(data.emotion);
            if (characterRef.current) {
              characterRef.current.changeExpression?.(data.emotion);
            }
          }
          if (data.motion) {
            setCurrentMotion(data.motion);
            if (characterRef.current) {
              characterRef.current.playMotion?.(data.motion);
            }
          }
          if (data.parameters && characterRef.current) {
            characterRef.current.updateParameters?.(data.parameters);
          }
          break;
        
        case 'model_loaded':
          setModelInfo(data.model_info);
          console.log('[useLive2DSync] 모델 로드 완료:', data.model_info);
          break;
        
        case 'sync_error':
          console.error('[useLive2DSync] 동기화 오류:', data.error);
          setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
          break;
        
        default:
          console.log('[useLive2DSync] 알 수 없는 Live2D 메시지 타입:', data.type);
      }
    } catch (error) {
      console.error('[useLive2DSync] 메시지 처리 중 오류:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [currentEmotion, characterRef]);

  // WebSocket 연결 상태 핸들러
  const handleConnectionStatus = useCallback((status) => {
    setIsConnected(status === 'connected');
    console.log('[useLive2DSync] 연결 상태 변경:', status);
  }, []);

  // 백엔드 동기화 확인
  const checkBackendSync = useCallback(async () => {
    try {
      if (sessionId.current) {
        const status = await live2DService.getStatusAPI(sessionId.current);
        setBackendSynced(status.success);
        
        if (status.success && status.data) {
          const { emotion, motion } = status.data;
          
          // 상태 불일치 시 동기화
          if (emotion && emotion !== currentEmotion) {
            setCurrentEmotion(emotion);
            if (characterRef.current) {
              characterRef.current.changeExpression?.(emotion);
            }
          }
        }
      }
    } catch (error) {
      console.warn('[useLive2DSync] 백엔드 상태 확인 실패:', error);
      setBackendSynced(false);
    }
  }, [currentEmotion, characterRef]);

  // 감정 변경 함수
  const changeEmotion = useCallback(async (emotion, intensity = 0.8, duration = 0.5) => {
    try {
      setCurrentEmotion(emotion);
      
      // 로컬 Live2D 적용
      if (characterRef.current) {
        characterRef.current.changeExpression?.(emotion, duration);
      }
      
      // 백엔드 동기화
      if (sessionId.current && backendSynced) {
        await live2DService.setEmotionAPI(emotion, sessionId.current, intensity);
      }
      
      // WebSocket으로 다른 클라이언트에게 브로드캐스트
      if (isConnected) {
        webSocketService.sendLive2DMessage({
          type: 'emotion_change',
          emotion,
          intensity,
          duration,
          session_id: sessionId.current
        });
        
        setConnectionStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
      }
      
    } catch (error) {
      console.error('[useLive2DSync] 감정 변경 실패:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [backendSynced, isConnected, characterRef]);

  // 모션 재생 함수
  const playMotion = useCallback(async (motion, priority = 1) => {
    try {
      setCurrentMotion(motion);
      
      // 로컬 Live2D 적용
      if (characterRef.current) {
        await characterRef.current.playMotion?.(motion, priority);
      }
      
      // 백엔드 동기화
      if (sessionId.current && backendSynced) {
        await live2DService.playMotionAPI(motion, sessionId.current, priority);
      }
      
      // WebSocket으로 다른 클라이언트에게 브로드캐스트
      if (isConnected) {
        webSocketService.sendLive2DMessage({
          type: 'motion_trigger',
          motion,
          priority,
          session_id: sessionId.current
        });
        
        setConnectionStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
      }
      
      // 모션 완료 후 상태 초기화 (기본 3초)
      setTimeout(() => setCurrentMotion(null), 3000);
      
    } catch (error) {
      console.error('[useLive2DSync] 모션 재생 실패:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [backendSynced, isConnected, characterRef]);

  // 텍스트 감정 분석 및 반응
  const analyzeAndReact = useCallback(async (text) => {
    try {
      if (sessionId.current && backendSynced) {
        const result = await live2DService.analyzeTextEmotionAPI(text, sessionId.current);
        
        if (result.success && result.data) {
          const { primary_emotion, intensity, recommended_motion } = result.data;
          
          if (primary_emotion) {
            await changeEmotion(primary_emotion, intensity || 0.8);
          }
          
          if (recommended_motion) {
            await playMotion(recommended_motion);
          }
          
          return result.data;
        }
      }
      
      // 폴백: 로컬 감정 분석
      await live2DService.handleChatMessage(text, sessionId.current);
      
    } catch (error) {
      console.error('[useLive2DSync] 텍스트 분석 실패:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [backendSynced, changeEmotion, playMotion]);

  // 운세 결과와 동기화
  const syncWithFortune = useCallback(async (fortuneType, fortuneResult) => {
    try {
      if (sessionId.current && backendSynced) {
        const result = await live2DService.syncFortuneEmotionAPI(
          fortuneType, 
          sessionId.current, 
          fortuneResult
        );
        
        if (result.success && result.data) {
          const { emotion, motion, parameters } = result.data;
          
          if (emotion) {
            await changeEmotion(emotion);
          }
          
          if (motion) {
            await playMotion(motion);
          }
          
          if (parameters && characterRef.current) {
            characterRef.current.updateParameters?.(parameters);
          }
          
          return result.data;
        }
      }
      
      // 폴백: 로컬 운세 처리
      await live2DService.handleFortuneResult(fortuneResult, sessionId.current);
      
    } catch (error) {
      console.error('[useLive2DSync] 운세 동기화 실패:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [backendSynced, changeEmotion, playMotion, characterRef]);

  // 통합 상태 설정
  const setCombinedState = useCallback(async (emotion, motion, parameters = null) => {
    try {
      // 로컬 적용
      if (emotion) {
        setCurrentEmotion(emotion);
        if (characterRef.current) {
          characterRef.current.changeExpression?.(emotion);
        }
      }
      
      if (motion) {
        setCurrentMotion(motion);
        if (characterRef.current) {
          await characterRef.current.playMotion?.(motion);
        }
        setTimeout(() => setCurrentMotion(null), 3000);
      }
      
      if (parameters && characterRef.current) {
        characterRef.current.updateParameters?.(parameters);
      }
      
      // 백엔드 동기화
      if (sessionId.current && backendSynced) {
        await live2DService.setCombinedStateAPI(
          emotion, 
          motion, 
          sessionId.current, 
          parameters
        );
      }
      
    } catch (error) {
      console.error('[useLive2DSync] 통합 상태 설정 실패:', error);
      setConnectionStats(prev => ({ ...prev, errors: prev.errors + 1 }));
    }
  }, [backendSynced, characterRef]);

  // Hook 초기화
  useEffect(() => {
    console.log('[useLive2DSync] Hook 초기화 시작');
    
    // WebSocket 이벤트 리스너 설정
    webSocketService.on('live2dMessage', handleLive2DMessage);
    webSocketService.on('connectionStatus', handleConnectionStatus);
    
    // 백엔드 동기화 주기적 확인 (30초마다)
    syncTimer.current = setInterval(checkBackendSync, 30000);
    
    // 통계 업데이트 (5분마다)
    statsTimer.current = setInterval(() => {
      console.log('[useLive2DSync] 연결 통계:', connectionStats);
    }, 300000);
    
    // 초기 백엔드 동기화 확인
    checkBackendSync();
    
    return () => {
      console.log('[useLive2DSync] Hook 정리');
      
      // 이벤트 리스너 제거
      webSocketService.off('live2dMessage', handleLive2DMessage);
      webSocketService.off('connectionStatus', handleConnectionStatus);
      
      // 타이머 정리
      if (syncTimer.current) {
        clearInterval(syncTimer.current);
      }
      if (statsTimer.current) {
        clearInterval(statsTimer.current);
      }
    };
  }, [handleLive2DMessage, handleConnectionStatus, checkBackendSync]);

  // 반환되는 Hook API
  return {
    // 상태 정보
    isConnected,
    currentEmotion,
    currentMotion,
    backendSynced,
    modelInfo,
    connectionStats,
    
    // 제어 함수
    changeEmotion,
    playMotion,
    analyzeAndReact,
    syncWithFortune,
    setCombinedState,
    
    // 유틸리티 함수
    checkBackendSync,
    
    // 세션 ID
    sessionId: sessionId.current
  };
};
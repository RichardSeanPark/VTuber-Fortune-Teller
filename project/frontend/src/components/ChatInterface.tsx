import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import webSocketService from '../services/WebSocketService';
import userService from '../services/UserService';
import { STORAGE_KEYS } from '../utils/constants';

const ChatInterface = ({ onMessageSend, connectionStatus, live2dViewerRef }) => {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const sessionId = userService.getSessionId();

  // 컴포넌트 마운트 시 초기화
  useEffect(() => {
    initializeChat();
    
    return () => {
      // 클린업
      webSocketService.off('chatResponse', handleChatResponse);
      webSocketService.off('chatMessage', handleChatMessage);
      webSocketService.off('message', handleWebSocketMessage);
      webSocketService.off('connect', handleWebSocketConnect);
      webSocketService.off('disconnect', handleWebSocketDisconnect);
      webSocketService.off('error', handleWebSocketError);
      webSocketService.off('ttsPlayStart', handleTTSPlayStart);
      webSocketService.off('ttsPlayEnd', handleTTSPlayEnd);
      webSocketService.off('ttsAutoplayBlocked', handleTTSAutoplayBlocked);
    };
  }, []);

  // 메시지 변경 시 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 컴포넌트 언마운트 시 립싱크 정리

  // 채팅 초기화
  const initializeChat = async () => {
    try {
      // 저장된 채팅 히스토리 로드
      loadChatHistory();
      
      // WebSocket 이벤트 리스너 설정
      setupWebSocketListeners();
      
      // WebSocket 연결 상태 확인 및 연결 시도
      if (webSocketService.isConnected()) {
        setIsConnected(true);
        console.log('[ChatInterface] WebSocket 이미 연결됨');
      } else {
        console.log('[ChatInterface] WebSocket 연결 시도 중...');
        console.log('[ChatInterface] 사용할 세션 ID:', sessionId);
        // WebSocket 연결 시도
        const connected = await webSocketService.connect(sessionId);
        if (connected) {
          setIsConnected(true);
          console.log('[ChatInterface] WebSocket 연결 성공');
        } else {
          setIsConnected(false);
          console.log('[ChatInterface] WebSocket 연결 실패 - 재시도 중...');
          // 3초 후 재시도
          setTimeout(() => {
            webSocketService.connect(sessionId).then(success => {
              setIsConnected(success);
              console.log('[ChatInterface] WebSocket 재연결:', success ? '성공' : '실패');
            });
          }, 3000);
        }
      }
      
      // 환영 메시지 추가 (히스토리가 비어있는 경우)
      if (messages.length === 0) {
        addWelcomeMessage();
      }
      
    } catch (error) {
      console.error('[ChatInterface] 초기화 실패:', error);
      addSystemMessage('채팅 연결에 실패했습니다. 페이지를 새로고침해 주세요.');
    }
  };

  // 채팅 히스토리 로드
  const loadChatHistory = () => {
    try {
      const savedHistory = localStorage.getItem(STORAGE_KEYS.CHAT_HISTORY);
      if (savedHistory) {
        const history = JSON.parse(savedHistory);
        // 최근 20개 메시지만 로드
        const recentMessages = history.slice(-20).map(msg => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        }));
        setMessages(recentMessages);
      }
    } catch (error) {
      console.error('[ChatInterface] 히스토리 로드 실패:', error);
    }
  };

  // 채팅 히스토리 저장
  const saveChatHistory = (newMessages) => {
    try {
      localStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, JSON.stringify(newMessages));
    } catch (error) {
      console.error('[ChatInterface] 히스토리 저장 실패:', error);
    }
  };

  // 단순한 립싱크 interval 추적 (하나만 사용)
  const lipSyncIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // 컴포넌트 언마운트 시 립싱크 정리
  useEffect(() => {
    return () => {
      if (lipSyncIntervalRef.current) {
        console.log('[ChatInterface] 컴포넌트 언마운트 - 립싱크 정리');
        clearInterval(lipSyncIntervalRef.current);
        lipSyncIntervalRef.current = null;
      }
    };
  }, []);

  // Lip sync cleanup on unmount
  const cleanupLipSync = () => {
    if (lipSyncIntervalRef.current) {
      clearInterval(lipSyncIntervalRef.current);
      lipSyncIntervalRef.current = null;
    }
    
    // Close mouth
    if (live2dViewerRef?.current && typeof live2dViewerRef.current.updateParameters === 'function') {
      live2dViewerRef.current.updateParameters({ 
        ParamMouthOpenY: 0.0,
        ParamMouthForm: 0.0
      });
      console.log('[ChatInterface] 입 다물기 완료');
    }
  };

  // TTS 음성 생성 및 재생 - 비활성화됨 (Backend에서 TTS 처리)
  const generateAndPlayTTS = async (text) => {
    console.log('⚠️ [Deprecated] generateAndPlayTTS 호출됨 - Backend에서 TTS 처리하므로 사용하지 않음');
    console.log('📋 [TTS 텍스트]:', text);
    
    // Frontend TTS 생성은 더 이상 사용하지 않음
    // 모든 TTS는 Backend에서 생성하여 chat_message로 전송됨
    return;
    
    try {
      console.log('🔥 [generateAndPlayTTS] 함수 진입 - 텍스트:', text);
      
      // 🎤 TTS 입력 메시지 명확히 출력
      console.log('🎤 [TTS 입력]:', text);
      console.log('🎤 [TTS 입력 길이]:', text.length);
      
      // 기존 TTS나 립싱크가 진행 중이면 먼저 정리
      if (lipSyncIntervalRef.current) {
        cleanupLipSync();
        
        // 기존 음성도 정지
        if ('speechSynthesis' in window) {
          speechSynthesis.cancel();
        }
        
        // 정리 완료를 위한 짧은 대기
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      // 사용자 ID 가져오기 (기본값: anonymous)
      const userId = userService.getUserId() || 'anonymous';
      
      // Live2D TTS API 호출 (기존 시스템 사용)
      console.log('🚀 [TTS API] 호출 시작 - 요청 데이터:', {
        session_id: 'tts_session_' + Date.now(),
        text: text,
        language: 'ko-KR',
        enable_lipsync: true
      });
      
      const response = await fetch('/api/live2d/tts/synthesize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: 'tts_session_' + Date.now(),
          text: text,
          emotion: 'neutral',
          language: 'ko-KR',
          voice_profile: 'ko_female_default',
          enable_lipsync: true
        })
      });
      
      console.log('🚀 [TTS API] 응답 받음 - 상태:', response.status, response.statusText);
      
      if (!response.ok) {
        throw new Error(`TTS API 오류: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('✅ [TTS API] 응답 성공');
      console.log('🔍 [TTS API] 전체 응답 구조:', {
        success: result.success,
        hasData: !!result.data,
        dataKeys: result.data ? Object.keys(result.data) : [],
        hasAudioData: !!(result.data && result.data.audio_data),
        hasLipSync: !!(result.data && result.data.lip_sync),
        audioDataLength: result.data && result.data.audio_data ? result.data.audio_data.length : 0,
        lipSyncLength: result.data && result.data.lip_sync ? result.data.lip_sync.length : 0
      });
      
      // 🔍 립싱크 데이터 디버깅
      if (result.data.lip_sync) {
        console.log('🎤 [립싱크] 데이터 수신됨:', result.data.lip_sync.length, '개 프레임');
        const validFrames = result.data.lip_sync.filter(frame => frame[1].ParamMouthOpenY > 0);
        console.log('🎤 [립싱크] 입 열림 프레임:', validFrames.length, '개');
        if (validFrames.length > 0) {
          console.log('🎤 [립싱크] 첫 번째 입 열림:', validFrames[0]);
          const maxFrame = validFrames.reduce((max, frame) => 
            frame[1].ParamMouthOpenY > max[1].ParamMouthOpenY ? frame : max
          );
          console.log('🎤 [립싱크] 최대 입 열림:', maxFrame);
        }
      } else {
        console.warn('⚠️ [립싱크] 데이터 없음!');
      }
      
      if (result.success && result.data.audio_data) {
        
        if (result.data.audio_data === 'dummy_audio_data') {
          // Mock 데이터일 경우 브라우저 TTS 사용
          console.log('🔊 [브라우저 TTS] 시작');
          
          try {
            // AI 응답 텍스트 추출
            const textToSpeak = result.data.text || text;
            
            // SpeechSynthesis API 사용
            const utterance = new SpeechSynthesisUtterance(textToSpeak);
            utterance.lang = 'ko-KR';
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.volume = 0.8;
            
            // 한국어 음성 찾기
            const voices = speechSynthesis.getVoices();
            const koreanVoice = voices.find(voice => 
              voice.lang.includes('ko') || voice.name.includes('Korea')
            );
            
            if (koreanVoice) {
              utterance.voice = koreanVoice;
            }
            
            // 음성 재생 이벤트
            utterance.onstart = () => {
              
              console.log('[ChatInterface] 브라우저 TTS 립싱크는 백엔드 데이터 필요');
            };
            
            utterance.onend = () => {
              console.log('[ChatInterface] 브라우저 TTS 완료');
            };
            
            utterance.onerror = (error) => {
              console.error('[ChatInterface] 브라우저 TTS 오류:', error);
            };
            
            // 음성 재생
            speechSynthesis.speak(utterance);
            
            // 재생 완료 대기 (Promise로 변환)
            await new Promise((resolve) => {
              const originalOnEnd = utterance.onend;
              const originalOnError = utterance.onerror;
              
              utterance.onend = (e) => {
                if (originalOnEnd) originalOnEnd(e);
                resolve();
              };
              
              utterance.onerror = (e) => {
                if (originalOnError) originalOnError(e);
                resolve();
              };
            });
            
          } catch (error) {
            console.warn('[ChatInterface] 브라우저 TTS 실패:', error);
            console.error('[ChatInterface] TTS 기능 사용 불가');
            await new Promise(resolve => setTimeout(resolve, 2000));
          }
          
        } else {
          // 실제 Base64 데이터를 Blob URL로 변환
          let audioUrl: string;
          
          try {
            const binaryString = atob(result.data.audio_data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
              bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: `audio/${result.data.audio_format || 'wav'}` });
            audioUrl = URL.createObjectURL(blob);
          } catch (error) {
            console.error('[ChatInterface] Base64 오디오 데이터 변환 실패:', error);
            return;
          }
          
          // 오디오 재생
          const audio = new Audio(audioUrl);
          
          // 오디오 로드 완료 대기 (더 강화된 예외 처리)
          try {
            await new Promise((resolve, reject) => {
              const timeoutId = setTimeout(() => {
                reject(new Error('Audio loading timeout'));
              }, 10000); // 10초 타임아웃
              
              audio.onloadeddata = () => {
                clearTimeout(timeoutId);
                resolve(true);
              };
              
              audio.onerror = (e) => {
                clearTimeout(timeoutId);
                reject(new Error(`Audio loading failed: ${e.type}`));
              };
              
              audio.oncanplay = () => {
                clearTimeout(timeoutId);
                resolve(true);
              };
            });
            
            console.log('[ChatInterface] 실제 오디오 재생 시작');
            await audio.play();
            
            // Blob URL 정리
            setTimeout(() => URL.revokeObjectURL(audioUrl), 5000);
            
          } catch (audioError) {
            console.warn('[ChatInterface] 오디오 재생 실패 (정상 - 실제 TTS 구현 필요):', audioError);
            // Blob URL 정리
            URL.revokeObjectURL(audioUrl);
            return;
          }
        }
        
        // Live2D 립싱크 데이터가 있다면 적용
        if (result.data.lip_sync && live2dViewerRef?.current) {
          try {
            console.log('🎭 [립싱크 적용] 시작 - 데이터:', result.data.lip_sync.length, '개 프레임');
            console.log('🎭 [립싱크 적용] live2dViewerRef.current:', !!live2dViewerRef.current);
            console.log('🎭 [립싱크 적용] 원본 데이터 포맷:', result.data.lip_sync.slice(0, 2));
            
            // 백엔드에서 받은 립싱크 데이터를 Live2DViewer 포맷으로 변환
            // 백엔드: [[timestamp, {ParamMouthOpenY: 0.5, ...}], ...]
            // Live2DViewer: {mouth_shapes: [[timestamp, {ParamMouthOpenY: 0.5, ...}], ...]}
            const lipSyncData = {
              mouth_shapes: result.data.lip_sync,
              duration: result.data.duration || 5.0  // 기본 5초
            };
            
            console.log('🎭 [립싱크 적용] 변환된 데이터:', {
              mouth_shapes_length: lipSyncData.mouth_shapes.length,
              duration: lipSyncData.duration,
              first_frame: lipSyncData.mouth_shapes[0],
              last_frame: lipSyncData.mouth_shapes[lipSyncData.mouth_shapes.length - 1]
            });
            
            // 립싱크 재생 (Live2DViewer에 메서드가 있다면)
            if (typeof live2dViewerRef.current.playLipSync === 'function') {
              console.log('🎭 [립싱크 적용] playLipSync 메서드 호출 시작');
              live2dViewerRef.current.playLipSync(lipSyncData);
              console.log('✅ [립싱크 적용] playLipSync 메서드 호출 완료');
            } else {
              console.warn('❌ [립싱크 적용] playLipSync 메서드가 없음!');
              
              // 대안: setLipSync 메서드 확인
              if (typeof live2dViewerRef.current.setLipSync === 'function') {
                console.log('🎭 [립싱크 적용] setLipSync 메서드로 시도');
                live2dViewerRef.current.setLipSync(lipSyncData);
                console.log('✅ [립싱크 적용] setLipSync 메서드 호출 완료');
              } else {
                console.error('❌ [립싱크 적용] 립싱크 관련 메서드를 찾을 수 없음!');
              }
            }
          } catch (error) {
            console.error('[ChatInterface] 립싱크 재생 실패:', error);
          }
        } else {
          console.error('❌ [ChatInterface] 립싱크 데이터 없음');
        }
        
        console.log('[ChatInterface] TTS 재생 완료');
      } else {
        console.warn('[ChatInterface] TTS 응답에 오디오 데이터가 없음:', result);
      }
      
    } catch (error) {
      console.error('[ChatInterface] TTS 생성/재생 실패:', error);
      
      // Fallback: 브라우저 내장 TTS 사용
      if ('speechSynthesis' in window) {
        console.log('[ChatInterface] 브라우저 내장 TTS 사용');
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ko-KR';
        utterance.rate = 0.9;
        speechSynthesis.speak(utterance);
      }
    }
  };

  // overall_description만 추출하는 함수
  const extractOverallDescription = (text) => {
    if (!text) return text;
    
    try {
      // 이미 짧은 메시지인 경우 (마크다운이 아닌 경우) 그대로 반환
      if (text.length < 200 && !text.includes('```') && !text.includes('###')) {
        console.log('✅ [이미 추출된 메시지] 그대로 사용:', text);
        return text;
      }
      
      // overall_description 패턴 찾기 (마크다운인 경우)
      const match = text.match(/"overall_description"\s*:\s*"([^"]+)"/);
      if (match) {
        console.log('✅ [추출 성공] overall_description:', match[1]);
        return match[1];
      }
      
      // JSON 블록에서 추출 시도
      const jsonMatch = text.match(/```json\s*\n([\s\S]*?)\n```/);
      if (jsonMatch) {
        try {
          const jsonData = JSON.parse(jsonMatch[1]);
          if (jsonData.overall_description) {
            console.log('✅ [JSON 추출 성공] overall_description:', jsonData.overall_description);
            return jsonData.overall_description;
          }
        } catch (e) {
          console.warn('❌ [JSON 파싱 실패]:', e);
        }
      }
      
      console.warn('❌ [추출 실패] overall_description을 찾을 수 없음');
      return '운세 정보를 확인해보세요.';
      
    } catch (error) {
      console.error('❌ [추출 오류]:', error);
      return '운세 정보를 확인해보세요.';
    }
  };

  // chat_message 전용 처리 함수 - 백엔드 WebSocket 립싱크 데이터 사용
  const handleChatMessage = async (data) => {
    console.log('💬 [ChatInterface] chat_message 수신:', data);
    
    if (!data) return;
    
    const content = data.message || data.content || '';
    const audioData = data.audio_data || null;
    const lipSyncData = data.lip_sync_data || null;
    
    if (!content) {
      console.warn('💬 [ChatInterface] chat_message에서 메시지 내용이 없음');
      return;
    }
    
    console.log('🔍 [ChatInterface] 수신된 데이터:', {
      hasContent: !!content,
      hasAudioData: !!audioData,
      hasLipSyncData: !!lipSyncData,
      lipSyncFrames: lipSyncData ? lipSyncData.length : 0
    });
    
    // AI 메시지를 채팅창에 추가
    const aiMessage = {
      id: Date.now(),
      type: 'ai',
      content: content,
      timestamp: new Date(),
      hasAudio: !!audioData,
      hasLipSync: !!lipSyncData
    };
    
    // 타이핑 애니메이션 시작
    setIsTyping(true);
    
    // AI 메시지를 채팅에 추가
    setMessages(prev => {
      const newMessages = [...prev, aiMessage];
      saveChatHistory(newMessages);
      return newMessages;
    });
    
    // 타이핑 애니메이션 후 오디오+립싱크 처리
    setTimeout(async () => {
      setIsTyping(false);
      
      // Live2D 반응 추가
      if (live2dViewerRef?.current && content) {
        try {
          await live2dViewerRef.current.analyzeAndReact(content);
          console.log('💬 [ChatInterface] Live2D 반응 완료');
        } catch (error) {
          console.warn('💬 [ChatInterface] Live2D 반응 실패:', error);
        }
      }
      
      // 백엔드에서 전달받은 립싱크 데이터 우선 사용
      if (lipSyncData) {
        console.log('🎭 [백엔드 립싱크] 백엔드에서 전달받은 립싱크 데이터 분석 시작');
        console.log('🔍 [백엔드 립싱크] 데이터 타입:', typeof lipSyncData);
        console.log('🔍 [백엔드 립싱크] 전체 데이터:', lipSyncData);
        console.log('🔍 [백엔드 립싱크] 키 목록:', Object.keys(lipSyncData || {}));
        
        // mouth_shapes 존재 확인
        const hasMouthShapes = !!(lipSyncData.mouth_shapes);
        console.log('🔍 [백엔드 립싱크] mouth_shapes 존재:', hasMouthShapes);
        
        if (hasMouthShapes) {
          const frameCount = lipSyncData.mouth_shapes.length;
          console.log('🔍 [백엔드 립싱크] 프레임 수:', frameCount);
          console.log('🔍 [백엔드 립싱크] mouth_shapes 타입:', typeof lipSyncData.mouth_shapes);
          console.log('🔍 [백엔드 립싱크] 배열 여부:', Array.isArray(lipSyncData.mouth_shapes));
          
          // 첫 번째 프레임 상세 분석
          if (frameCount > 0) {
            const firstFrame = lipSyncData.mouth_shapes[0];
            console.log('🔍 [백엔드 립싱크] 첫 프레임:', firstFrame);
            console.log('🔍 [백엔드 립싱크] 첫 프레임 타입:', typeof firstFrame);
            console.log('🔍 [백엔드 립싱크] 첫 프레임 배열 여부:', Array.isArray(firstFrame));
            
            if (Array.isArray(firstFrame) && firstFrame.length >= 2) {
              const [timestamp, parameters] = firstFrame;
              console.log('🔍 [백엔드 립싱크] 첫 프레임 - timestamp:', timestamp, typeof timestamp);
              console.log('🔍 [백엔드 립싱크] 첫 프레임 - parameters:', parameters, typeof parameters);
              if (parameters && typeof parameters === 'object') {
                console.log('🔍 [백엔드 립싱크] 첫 프레임 - 파라미터 키들:', Object.keys(parameters));
                console.log('🔍 [백엔드 립싱크] 첫 프레임 - ParamMouthOpenY:', parameters.ParamMouthOpenY);
                console.log('🔍 [백엔드 립싱크] 첫 프레임 - ParamMouthForm:', parameters.ParamMouthForm);
              }
            }
          }
        }
        
        console.log('🔍 [백엔드 립싱크] duration:', lipSyncData.duration, typeof lipSyncData.duration);
        
        try {
          // 백엔드가 보내는 올바른 구조 사용
          if (lipSyncData.mouth_shapes && Array.isArray(lipSyncData.mouth_shapes)) {
            console.log('✅ [백엔드 립싱크] mouth_shapes 배열 검증 통과');
            
            // Live2DViewer 포맷으로 변환 (백엔드 데이터 직접 사용)
            const formattedLipSyncData = {
              mouth_shapes: lipSyncData.mouth_shapes,  // 백엔드에서 보낸 배열 직접 사용
              duration: lipSyncData.duration || (lipSyncData.mouth_shapes.length * 0.0625) // 백엔드 duration 우선, 없으면 계산
            };
            
            console.log('🎭 [백엔드 립싱크] Live2D 전달할 데이터 준비 완료:', {
              frameCount: formattedLipSyncData.mouth_shapes.length,
              duration: formattedLipSyncData.duration,
              firstFrame: formattedLipSyncData.mouth_shapes[0],
              lastFrame: formattedLipSyncData.mouth_shapes[formattedLipSyncData.mouth_shapes.length - 1]
            });
            
            // 추가 테스트 로그: 프레임 재생 예상 시간
            const expectedPlaybackTime = formattedLipSyncData.mouth_shapes.length / 30; // 30fps 가정
            console.log('⏱️ [테스트] 립싱크 데이터 시간 분석:');
            console.log(`  - 프레임 수: ${formattedLipSyncData.mouth_shapes.length}개`);
            console.log(`  - duration: ${formattedLipSyncData.duration}초`);
            console.log(`  - frame_rate: 30 fps (가정)`);
            console.log(`  - 계산된 재생 시간: ${expectedPlaybackTime.toFixed(6)}초`);
            console.log(`  - duration과 계산된 시간 차이: ${Math.abs(formattedLipSyncData.duration - expectedPlaybackTime).toFixed(6)}초`);
            
            // Live2D 립싱크 적용 전 검증
            console.log('🔍 [백엔드 립싱크] live2dViewerRef 존재:', !!live2dViewerRef);
            console.log('🔍 [백엔드 립싱크] live2dViewerRef.current 존재:', !!live2dViewerRef?.current);
            
            if (live2dViewerRef?.current) {
              console.log('🔍 [백엔드 립싱크] playLipSync 메서드 존재:', typeof live2dViewerRef.current.playLipSync);
              
              if (typeof live2dViewerRef.current.playLipSync === 'function') {
                console.log('🎭 [백엔드 립싱크] playLipSync 호출 시작...');
                live2dViewerRef.current.playLipSync(formattedLipSyncData);
                console.log('✅ [백엔드 립싱크] playLipSync 호출 완료 - Live2D가 실제로 입을 움직일지 확인 필요');
              } else {
                console.error('❌ [백엔드 립싱크] playLipSync 메서드가 함수가 아님');
              }
            } else {
              console.error('❌ [백엔드 립싱크] live2dViewerRef.current가 존재하지 않음');
            }
          } else {
            console.error('❌ [백엔드 립싱크] mouth_shapes 검증 실패:', {
              hasMouthShapes: !!(lipSyncData.mouth_shapes),
              isArray: Array.isArray(lipSyncData.mouth_shapes),
              type: typeof lipSyncData.mouth_shapes,
              value: lipSyncData.mouth_shapes
            });
          }
        } catch (error) {
          console.error('❌ [백엔드 립싱크] 적용 중 예외 발생:', error);
          console.error('❌ [백엔드 립싱크] 에러 스택:', error.stack);
        }
      } else {
        console.error('❌ [백엔드 립싱크] 립싱크 데이터 없음');
      }
      
      // 오디오 재생 (WebSocket 오디오 우선)
      if (audioData) {
        console.log('🔊 [WebSocket 오디오] 재생 시작');
        try {
          await webSocketService.playTTSAudio(audioData, content);
          console.log('🔊 [WebSocket 오디오] 재생 완료');
        } catch (error) {
          console.error('❌ [WebSocket 오디오] 재생 실패:', error);
        }
      } else {
        console.log('ℹ️ [오디오] WebSocket 오디오 데이터 없음');
      }
      
      console.log('💬 [ChatInterface] chat_message 처리 완료');
    }, 1000);
  };

  // WebSocket 메시지 처리 (fortune_result는 제거됨 - chat_message로 통합됨)
  const handleWebSocketMessage = async (data) => {
    console.log('⚠️ [Deprecated] handleWebSocketMessage 호출됨 - 이제 chat_message로 통합 처리됩니다');
    console.log('📋 [메시지 타입]:', data.type);
    
    // fortune_result 타입은 더 이상 사용하지 않음
    // 모든 메시지는 chat_message 타입으로 통합됨
    if (data.type === 'fortune_result') {
      console.log('⚠️ [Deprecated] fortune_result 타입 감지 - chat_message로 전환 필요');
      return;
    }
    
    // 기타 메시지 타입만 처리
    console.log('📨 [기타 메시지] 처리:', data.type);
  };

  // WebSocket 이벤트 리스너 설정
  const setupWebSocketListeners = () => {
    webSocketService.on('chatResponse', handleChatResponse);
    webSocketService.on('chatMessage', handleChatMessage);   // chat_message 처리
    webSocketService.on('message', handleWebSocketMessage);  // 추가된 메시지 핸들러
    webSocketService.on('connect', handleWebSocketConnect);
    webSocketService.on('disconnect', handleWebSocketDisconnect);
    webSocketService.on('error', handleWebSocketError);
    webSocketService.on('ttsPlayStart', handleTTSPlayStart); // TTS 재생 시작
    webSocketService.on('ttsPlayEnd', handleTTSPlayEnd);     // TTS 재생 종료
    webSocketService.on('ttsAutoplayBlocked', handleTTSAutoplayBlocked); // TTS 자동재생 차단
  };

  // WebSocket 연결 성공
  const handleWebSocketConnect = () => {
    setIsConnected(true);
    console.log('[ChatInterface] WebSocket 연결 성공');
  };

  // WebSocket 연결 해제
  const handleWebSocketDisconnect = () => {
    setIsConnected(false);
    console.log('[ChatInterface] WebSocket 연결 해제');
  };

  // WebSocket 오류
  const handleWebSocketError = (error) => {
    setIsConnected(false);
    console.error('[ChatInterface] WebSocket 오류:', error);
    
    // 오류 타입에 따른 다른 메시지 표시
    let errorMessage = '채팅 연결에 문제가 발생했습니다.';
    if (error?.type === 'close' && error?.code === 1006) {
      errorMessage = '서버와의 연결이 끊어졌습니다. 자동으로 재연결을 시도합니다.';
    } else if (error?.type === 'error') {
      errorMessage = '네트워크 연결을 확인해주세요.';
    }
    
    addSystemMessage(errorMessage);
  };

  // TTS 재생 시작 이벤트 처리 (chat_message에서 이미 처리하므로 비활성화)
  const handleTTSPlayStart = (data) => {
    // 립싱크는 chat_message 처리에서 이미 수행됨
    // 중복 실행 방지를 위해 비활성화
  };

  // TTS 재생 종료 이벤트 처리
  const handleTTSPlayEnd = () => {
    // 립싱크 정리
    cleanupLipSync();
    
    // Live2D 입을 자연스럽게 닫기
    if (live2dViewerRef?.current && typeof live2dViewerRef.current.updateParameters === 'function') {
      live2dViewerRef.current.updateParameters({
        ParamMouthOpenY: 0.0,
        ParamMouthForm: 0.0,
        ParamMouthOpenX: 0.0
      });
      console.log('🎵 [ChatInterface] Live2D 입 닫기 완료');
    }
  };

  // TTS 자동재생 차단 이벤트 처리
  const handleTTSAutoplayBlocked = (data) => {
    console.warn('🎵 [ChatInterface] TTS 자동재생 차단됨:', data);
    
    // 사용자에게 클릭을 유도하는 시스템 메시지 표시
    addSystemMessage('🔊 음성을 재생하려면 화면을 클릭해주세요. (브라우저 자동재생 정책)');
    
    // 클릭 이벤트 리스너 추가 (일회성)
    const handleUserClick = () => {
      if (data?.audio) {
        try {
          data.audio.play();
          console.log('🎵 [ChatInterface] 사용자 클릭으로 TTS 재생 시작');
          
          // 리스너 제거
          document.removeEventListener('click', handleUserClick);
        } catch (error) {
          console.error('🎵 [ChatInterface] 사용자 클릭 TTS 재생 실패:', error);
        }
      }
    };
    
    document.addEventListener('click', handleUserClick, { once: true });
  };


  // 채팅 응답 처리
  const handleChatResponse = async (data) => {
    console.log('[ChatInterface] 채팅 응답 수신:', data);
    
    // 다양한 응답 데이터 구조 처리
    let content = '';
    let emotion = null;
    let filtered = false;
    
    if (typeof data === 'string') {
      content = data;
    } else if (data && typeof data === 'object') {
      // 다양한 응답 형식 지원
      content = data.message || data.content || data.response || data.text || '';
      emotion = data.emotion;
      filtered = data.filtered || false;
      
      // 만약 data.data가 있다면 중첩된 구조 처리
      if (data.data && typeof data.data === 'object') {
        content = content || data.data.message || data.data.content || data.data.response || data.data.text || '';
        emotion = emotion || data.data.emotion;
        filtered = filtered || data.data.filtered || false;
      }
    }
    
    console.log('[ChatInterface] 처리된 콘텐츠:', content);
    
    if (!content) {
      console.warn('[ChatInterface] 응답에서 콘텐츠를 찾을 수 없음:', data);
      return;
    }
    
    const aiMessage = {
      id: Date.now(),
      type: 'ai',
      content: content,
      timestamp: new Date(),
      emotion: emotion,
      filtered: filtered
    };

    setMessages(prev => {
      const newMessages = [...prev, aiMessage];
      console.log('[ChatInterface] 메시지 추가됨, 총 메시지 수:', newMessages.length);
      console.log('[ChatInterface] 추가된 AI 메시지:', aiMessage);
      saveChatHistory(newMessages);
      return newMessages;
    });
    
    setIsTyping(false);
    console.log('[ChatInterface] 타이핑 상태 해제됨');

    // TTS 음성 생성 및 재생
    if (aiMessage.content) {
      try {
        console.log('[ChatInterface] TTS 음성 생성 시작:', aiMessage.content);
        await generateAndPlayTTS(aiMessage.content);
      } catch (error) {
        console.warn('[ChatInterface] TTS 재생 실패:', error);
      }
    }

    // Live2D 반응 추가 (AI 응답에 대한)
    if (live2dViewerRef?.current && aiMessage.content) {
      try {
        await live2dViewerRef.current.analyzeAndReact(aiMessage.content);
      } catch (error) {
        console.warn('[ChatInterface] Live2D 반응 실패:', error);
      }
    }
  };

  // 환영 메시지 추가
  const addWelcomeMessage = () => {
    const welcomeMessage = {
      id: Date.now(),
      type: 'system',
      content: '안녕하세요! 저는 미라입니다. 오늘 어떤 운세를 봐드릴까요? 🔮',
      timestamp: new Date()
    };
    
    setMessages([welcomeMessage]);
  };

  // 시스템 메시지 추가
  const addSystemMessage = (content) => {
    const systemMessage = {
      id: Date.now(),
      type: 'system',
      content,
      timestamp: new Date()
    };
    
    setMessages(prev => {
      const newMessages = [...prev, systemMessage];
      saveChatHistory(newMessages);
      return newMessages;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    const messageText = message.trim();
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: messageText,
      timestamp: new Date()
    };

    // 사용자 메시지를 채팅에 추가
    setMessages(prev => {
      const newMessages = [...prev, userMessage];
      saveChatHistory(newMessages);
      return newMessages;
    });

    // 입력 필드 초기화
    setMessage('');
    
    // 타이핑 표시
    setIsTyping(true);

    try {
      // WebSocket 연결 상태 확인
      if (isConnected) {
        // WebSocket으로 메시지 전송
        const success = webSocketService.sendChatMessage(messageText);
        
        if (!success) {
          throw new Error('메시지 전송 실패');
        }

        // 상위 컴포넌트에 메시지 전달 (Live2D 반응용)
        if (onMessageSend) {
          onMessageSend(messageText);
        }

        // Live2D 반응 추가 (사용자 메시지에 대한)
        if (live2dViewerRef?.current) {
          try {
            await live2dViewerRef.current.analyzeAndReact(messageText);
          } catch (error) {
            console.warn('[ChatInterface] Live2D 사용자 메시지 반응 실패:', error);
          }
        }

        console.log('[ChatInterface] 메시지 전송 성공:', messageText);
      } else {
        // 연결되지 않은 경우 로컬 처리만
        console.log('[ChatInterface] WebSocket 미연결 - 메시지 로컬 저장:', messageText);
        
        // 연결 안내 메시지 추가
        const systemMessage = {
          id: Date.now() + 1,
          type: 'system',
          content: '서버와 연결 중입니다. 잠시 후 다시 시도해주세요.',
          timestamp: new Date()
        };
        
        setMessages(prev => {
          const newMessages = [...prev, systemMessage];
          saveChatHistory(newMessages);
          return newMessages;
        });
        
        setIsTyping(false);
      }
      
    } catch (error) {
      console.error('[ChatInterface] 메시지 전송 실패:', error);
      setIsTyping(false);
      
      // 오류 메시지 표시
      addSystemMessage('메시지 전송에 실패했습니다. 다시 시도해 주세요.');
    }
  };

  // 연결 상태 확인
  const getConnectionStatus = () => {
    if (isConnected && webSocketService.isConnected()) {
      return 'connected';
    } else if (connectionStatus === 'connecting') {
      return 'connecting';
    } else {
      return 'disconnected';
    }
  };

  // 연결 상태에 따른 메시지 (최적화된 간결한 표현)
  const getConnectionMessage = () => {
    const status = getConnectionStatus();
    switch (status) {
      case 'connected':
        return '✅ 미라 온라인';
      case 'connecting':
        return '🔄 연결중';
      default:
        return '⚪ 오프라인';
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getQuickResponses = () => {
    return [
      '오늘 운세 알려줘',
      '내 별자리 운세는?',
      '연애운이 궁금해',
      '안녕하세요! 오늘 기분이 어떤가요?'  // 일반 메시지 샘플 추가
    ];
  };

  const handleQuickResponse = (text) => {
    setMessage(text);
    // 입력 필드가 disabled 상태여도 focus 시도
    if (inputRef.current) {
      inputRef.current.focus();
      // disabled 상태면 일시적으로 활성화
      if (inputRef.current.disabled) {
        inputRef.current.disabled = false;
        inputRef.current.focus();
      }
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>미라와 대화하기</h3>
        <div className={`connection-status ${getConnectionStatus()}`}>
          <span className="status-dot"></span>
          {getConnectionMessage()}
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.type} ${msg.filtered ? 'filtered' : ''}`}>
            <div className="message-content">
              <p>{msg.content}</p>
              {msg.filtered && (
                <small className="filtered-notice">⚠️ 내용이 필터링되었습니다</small>
              )}
              <span className="message-time">{formatTime(msg.timestamp)}</span>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="message ai typing">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="message-time">입력 중...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="quick-responses">
        {getQuickResponses().map((text, index) => (
          <button 
            key={index}
            className="quick-response-btn"
            onClick={() => handleQuickResponse(text)}
          >
            {text}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="message-form">
        <div className="input-container">
          <textarea
            ref={inputRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "미라에게 메시지를 보내세요... (Enter로 전송)" : "연결 중... 메시지 입력 가능"}
            className="message-input"
            rows="2"
            // disabled 제거 - 항상 입력 가능하도록
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!message.trim()}
            title={!isConnected ? "연결 중... 메시지는 대기열에 저장됩니다" : "메시지 전송"}
          >
            <span className="send-icon">{isConnected ? '📤' : '⏳'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
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
      webSocketService.off('connect', handleWebSocketConnect);
      webSocketService.off('disconnect', handleWebSocketDisconnect);
      webSocketService.off('error', handleWebSocketError);
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

  // 단순한 립싱크 시뮬레이션 시작
  const startLipSyncSimulation = (text: string) => {
    console.log('[ChatInterface] 립싱크 시작, 텍스트:', text);
    console.log('[ChatInterface] live2dViewerRef 존재 여부:', !!live2dViewerRef?.current);
    
    // 기존 인터벌이 있으면 정리
    if (lipSyncIntervalRef.current) {
      console.log('[ChatInterface] 기존 립싱크 인터벌 정리');
      clearInterval(lipSyncIntervalRef.current);
      lipSyncIntervalRef.current = null;
    }
    
    // 새로운 립싱크 인터벌 시작
    const interval = setInterval(() => {
      const randomMouthOpen = 0.3 + Math.random() * 0.5; // 0.3 ~ 0.8
      const mouthParams = {
        ParamMouthOpenY: randomMouthOpen,
        ParamMouthForm: 0.0
      };
      
      if (live2dViewerRef?.current && typeof live2dViewerRef.current.updateParameters === 'function') {
        live2dViewerRef.current.updateParameters(mouthParams);
        console.log('[ChatInterface] 립싱크 - 입 벌림:', randomMouthOpen.toFixed(2));
      } else {
        console.log('[ChatInterface] 립싱크 시뮬레이션 - 입 벌림:', randomMouthOpen.toFixed(2));
      }
    }, 120);
    
    lipSyncIntervalRef.current = interval;
    console.log('[ChatInterface] 립싱크 인터벌 생성:', interval);
  };

  // 단순한 립싱크 시뮬레이션 정지
  const stopLipSyncSimulation = () => {
    console.log('[ChatInterface] 립싱크 정지');
    
    if (lipSyncIntervalRef.current) {
      clearInterval(lipSyncIntervalRef.current);
      lipSyncIntervalRef.current = null;
      console.log('[ChatInterface] 립싱크 인터벌 정리됨');
    }
    
    // 입 다물기
    if (live2dViewerRef?.current && typeof live2dViewerRef.current.updateParameters === 'function') {
      live2dViewerRef.current.updateParameters({ 
        ParamMouthOpenY: 0.0,
        ParamMouthForm: 0.0
      });
      console.log('[ChatInterface] 입 다물기 완료');
    }
  };

  // TTS 음성 생성 및 재생
  const generateAndPlayTTS = async (text) => {
    try {
      console.log('[ChatInterface] TTS API 호출 시작:', text);
      
      // 기존 TTS나 립싱크가 진행 중이면 먼저 정리
      if (lipSyncIntervalRef.current) {
        console.log('[ChatInterface] 기존 TTS/립싱크 진행 중 - 먼저 정리');
        stopLipSyncSimulation();
        
        // 기존 음성도 정지
        if ('speechSynthesis' in window) {
          speechSynthesis.cancel();
          console.log('[ChatInterface] 기존 음성 재생 정지됨');
        }
        
        // 정리 완료를 위한 짧은 대기
        await new Promise(resolve => setTimeout(resolve, 50));
      }
      
      // 사용자 ID 가져오기 (기본값: anonymous)
      const userId = userService.getUserId() || 'anonymous';
      
      // Live2D TTS API 호출 (기존 시스템 사용)
      const response = await fetch('/api/v1/live2d/tts/synthesize', {
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
      
      if (!response.ok) {
        throw new Error(`TTS API 오류: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      console.log('[ChatInterface] TTS API 응답:', result);
      
      if (result.success && result.data.audio_data) {
        
        if (result.data.audio_data === 'dummy_audio_data') {
          // Mock 데이터일 경우 브라우저 TTS 사용
          console.log('[ChatInterface] Mock TTS 데이터 - 브라우저 TTS로 음성 생성');
          
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
              console.log('[ChatInterface] 한국어 음성 선택됨:', koreanVoice.name);
            } else {
              console.log('[ChatInterface] 한국어 음성 없음, 기본 음성 사용');
            }
            
            // 음성 재생 이벤트 - Reference2처럼 단순하게
            utterance.onstart = () => {
              console.log('[ChatInterface] 음성 재생 시작 → 입 벌림 시작');
              
              // 단순한 립싱크 시뮬레이션 시작 (음성과 동기화)
              startLipSyncSimulation(textToSpeak);
            };
            
            utterance.onend = () => {
              console.log('[ChatInterface] TTS 음성 재생 완료');
              stopLipSyncSimulation();
            };
            
            utterance.onerror = (e) => {
              console.warn('[ChatInterface] 브라우저 TTS 오류:', e);
              stopLipSyncSimulation();
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
            // fallback: 시뮬레이션
            console.log('[ChatInterface] TTS 시뮬레이션으로 대체');
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
        if (result.data.lipsync_data && live2dViewerRef?.current) {
          try {
            // 립싱크 재생 (Live2DViewer에 메서드가 있다면)
            if (typeof live2dViewerRef.current.playLipSync === 'function') {
              live2dViewerRef.current.playLipSync(result.data.lipsync_data);
            }
          } catch (error) {
            console.warn('[ChatInterface] 립싱크 재생 실패:', error);
          }
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

  // WebSocket 이벤트 리스너 설정
  const setupWebSocketListeners = () => {
    webSocketService.on('chatResponse', handleChatResponse);
    webSocketService.on('connect', handleWebSocketConnect);
    webSocketService.on('disconnect', handleWebSocketDisconnect);
    webSocketService.on('error', handleWebSocketError);
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
      '타로 카드 뽑아줘',
      '내 별자리 운세는?',
      '연애운이 궁금해'
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
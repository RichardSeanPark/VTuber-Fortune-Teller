import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import webSocketService from '../services/WebSocketService';
import userService from '../services/UserService';
import { STORAGE_KEYS } from '../utils/constants';

const ChatInterface = ({ onMessageSend, connectionStatus }) => {
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

  // 채팅 초기화
  const initializeChat = async () => {
    try {
      // 저장된 채팅 히스토리 로드
      loadChatHistory();
      
      // WebSocket 이벤트 리스너 설정
      setupWebSocketListeners();
      
      // WebSocket 연결 상태 확인 (App에서 이미 연결됨)
      if (webSocketService.isConnected()) {
        setIsConnected(true);
        console.log('[ChatInterface] WebSocket 이미 연결됨');
      } else {
        setIsConnected(false);
        console.log('[ChatInterface] WebSocket 연결 대기 중...');
        // App.js에서 관리하므로 여기서는 별도 연결 시도하지 않음
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
  const handleChatResponse = (data) => {
    console.log('[ChatInterface] 채팅 응답 수신:', data);
    
    const aiMessage = {
      id: Date.now(),
      type: 'ai',
      content: data.message || data.content,
      timestamp: new Date(),
      emotion: data.emotion,
      filtered: data.filtered || false
    };

    setMessages(prev => {
      const newMessages = [...prev, aiMessage];
      saveChatHistory(newMessages);
      return newMessages;
    });
    
    setIsTyping(false);
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
    if (!message.trim() || !isConnected) return;

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
      // WebSocket으로 메시지 전송
      const success = webSocketService.sendChatMessage(messageText);
      
      if (!success) {
        throw new Error('메시지 전송 실패');
      }

      // 상위 컴포넌트에 메시지 전달 (Live2D 반응용)
      if (onMessageSend) {
        onMessageSend(messageText);
      }

      console.log('[ChatInterface] 메시지 전송 성공:', messageText);
      
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
    inputRef.current?.focus();
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
            placeholder="미라에게 메시지를 보내세요... (Enter로 전송)"
            className="message-input"
            rows="2"
            disabled={!isConnected}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!message.trim() || !isConnected}
          >
            <span className="send-icon">📤</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default ChatInterface;
/**
 * WebSocket 서비스 - 정리된 버전
 * 백엔드와 실시간 통신을 담당
 */

class WebSocketService {
  constructor() {
    this.ws = null;
    this.live2dWs = null;
    this.baseUrl = process.env.NODE_ENV === 'development' 
      ? 'ws://175.118.126.76:8000' 
      : `ws://${window.location.host}`;
    this.sessionId = null;
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.listeners = {};
  }

  // 이벤트 리스너 관리
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  off(event, callback) {
    if (this.listeners[event]) {
      const index = this.listeners[event].indexOf(callback);
      if (index !== -1) {
        this.listeners[event].splice(index, 1);
      }
    }
  }

  emit(event, data = null) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => callback(data));
    }
  }

  // 메인 WebSocket 연결
  async connect(sessionId = null) {
    if (this.isConnecting) return false;
    
    this.isConnecting = true;
    this.sessionId = sessionId;
    
    const effectiveSessionId = sessionId || 'anonymous';
    const url = `${this.baseUrl}/ws/chat/${effectiveSessionId}`;

    return new Promise((resolve, reject) => {
      try {
        console.log('[WebSocket] 연결 시도:', url);
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('[WebSocket] 연결 성공');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.emit('connect');
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] 메시지 수신:', data);
            console.log('[WebSocket] 메시지 타입:', data.type);
            console.log('[WebSocket] 메시지 데이터 구조:', Object.keys(data));
            
            // 🔍 디버깅: 조건문 실행 경로 추적
            console.log('🔍 [디버깅] 메시지 타입 검사:', {
              'data.type === "chat_response"': data.type === 'chat_response',
              'data.type === "text_response"': data.type === 'text_response',
              'data.type === "chat_message"': data.type === 'chat_message',
              'actual_type': data.type
            });
            
            // LLM 관련 로그 추가
            if (data.type === 'llm_processing') {
              console.log('🤖 [LLM 호출] AI가 운세 생성을 시작합니다:', data.data);
            } else if (data.type === 'llm_details') {
              console.log('🔍 [LLM 요청] Cerebras API 호출:', data.data);
            } else if (data.type === 'llm_response') {
              console.log('✅ [LLM 응답] AI 응답 수신 완료:', data.data);
              if (data.data.fortune_content) {
                console.log('📜 [LLM 메시지] AI 생성 운세:', data.data.fortune_content);
              }
              if (data.data.full_result) {
                console.log('📊 [LLM 전체 결과]:', data.data.full_result);
              }
            } else if (data.type === 'llm_complete') {
              console.log('🎯 [LLM 완료] AI 운세 생성 완료:', data.data);
            } else if (data.type === 'chat_message') {
              console.log('💬 [채팅 메시지] 봇 응답 수신 - ChatInterface에서 처리됨:', data.data);
              // chat_message는 ChatInterface에서 TTS를 직접 처리하므로 여기서는 로그만 출력
              if (data.data && data.data.audio_data) {
                console.log('🔊 [TTS] 오디오 데이터 포함됨 (ChatInterface에서 처리):', {
                  message: data.data.message ? data.data.message.substring(0, 50) + '...' : 'No message',
                  audioSize: data.data.audio_data.length
                });
              }
            }
            
            // 메시지 타입에 따른 이벤트 발생
            if (data.type === 'chat_response' || data.type === 'text_response') {
              console.log('🎯 [디버깅] chat_response/text_response 경로 실행');
              const responseData = data.data || data;
              console.log('[WebSocket] chatResponse 이벤트 발생, 데이터:', responseData);
              this.emit('chatResponse', responseData);
            } else if (data.type === 'chat_message') {
              console.log('🎯 [디버깅] chat_message 경로 실행');
              // chat_message는 ChatInterface에서 직접 처리 (TTS 포함)
              console.log('[WebSocket] chatMessage 이벤트 발생 - ChatInterface로 위임');
              this.emit('chatMessage', data.data);
            } else {
              console.log('🎯 [디버깅] 기타 메시지 경로 실행, 타입:', data.type);
              console.log('[WebSocket] 일반 message 이벤트 발생');
              this.emit('message', data);
            }
          } catch (error) {
            console.error('[WebSocket] 메시지 파싱 오류:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] 연결 종료', event.code, event.reason);
          this.isConnecting = false;
          this.emit('disconnect');
          if (event.code !== 1000) {
            resolve(false);
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] 연결 오류:', error);
          this.isConnecting = false;
          this.emit('error', error);
          resolve(false);
        };

        // 연결 타임아웃 (10초)
        setTimeout(() => {
          if (this.isConnecting) {
            console.log('[WebSocket] 연결 타임아웃');
            this.isConnecting = false;
            if (this.ws) {
              this.ws.close();
            }
            resolve(false);
          }
        }, 10000);

      } catch (error) {
        this.isConnecting = false;
        console.error('[WebSocket] 연결 실패:', error);
        resolve(false);
      }
    });
  }

  // 메시지 전송
  send(type, data = {}) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type,
        timestamp: new Date().toISOString(),
        ...data
      };
      
      this.ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  // 채팅 메시지 전송
  sendChatMessage(message) {
    return this.send('chat_message', { message });
  }

  // Live2D WebSocket 연결
  async connectLive2D(sessionId = null) {
    const live2dUrl = sessionId 
      ? `${this.baseUrl}/ws/live2d/${sessionId}`
      : `${this.baseUrl}/ws/live2d/anonymous`;

    this.live2dWs = new WebSocket(live2dUrl);
    
    this.live2dWs.onopen = () => {
      console.log('[WebSocket] Live2D 연결 성공');
      this.emit('live2dConnect');
    };

    this.live2dWs.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.emit('live2dMessage', data);
      } catch (error) {
        console.error('[WebSocket] Live2D 메시지 파싱 오류:', error);
      }
    };

    this.live2dWs.onclose = () => {
      console.log('[WebSocket] Live2D 연결 종료');
      this.emit('live2dDisconnect');
    };

    this.live2dWs.onerror = (error) => {
      console.error('[WebSocket] Live2D 연결 오류:', error);
      this.emit('live2dError', error);
    };
  }

  // Live2D 동기화 전송
  sendLive2DSync(emotion, motion = null) {
    if (this.live2dWs && this.live2dWs.readyState === WebSocket.OPEN) {
      const message = {
        type: 'sync_state',
        timestamp: new Date().toISOString(),
        emotion,
        motion
      };
      
      this.live2dWs.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  // TTS 오디오 재생
  async playTTSAudio(base64AudioData, message = '') {
    try {
      // TTS audio playback starting

      // Base64를 Blob으로 변환
      const binaryString = atob(base64AudioData);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      const audioBlob = new Blob([bytes], { type: 'audio/mp3' });
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Audio Blob created

      // Audio 객체 생성 및 재생
      const audio = new Audio(audioUrl);
      
      // 오디오 이벤트 리스너
      audio.onloadstart = () => {
        // Audio loading started
      };
      
      audio.oncanplay = () => {
        // Audio ready to play
      };
      
      audio.onplay = () => {
        // Live2D mouth animation start
        this.emit('ttsPlayStart', { message, duration: audio.duration });
      };
      
      audio.onended = () => {
        // Live2D mouth animation end
        this.emit('ttsPlayEnd');
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = (error) => {
        console.error('❌ [TTS] 오디오 재생 오류:', error);
        URL.revokeObjectURL(audioUrl);
      };

      // 볼륨 설정 및 재생
      audio.volume = 0.8;
      
      try {
        await audio.play();
        // Audio playback started
      } catch (playError) {
        console.warn('TTS autoplay blocked by browser:', playError.message);
        
        // 자동 재생 실패 시 사용자에게 알림
        this.emit('ttsAutoplayBlocked', { audio, message });
      }

    } catch (error) {
      console.error('TTS audio processing failed:', error);
    }
  }

  // 연결 상태 확인
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // 연결 해제
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    if (this.live2dWs) {
      this.live2dWs.close();
      this.live2dWs = null;
    }
    
    this.emit('disconnect');
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
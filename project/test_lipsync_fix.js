/**
 * 립싱크 데이터 생성 확인 테스트
 * EdgeTTS Provider에서 립싱크 데이터가 제대로 생성되고 WebSocket으로 전송되는지 확인
 */

const WebSocket = require('ws');

console.log('🔍 립싱크 데이터 생성 및 전송 테스트 시작');

// WebSocket 연결 (외부 IP 사용)
const ws = new WebSocket('ws://175.118.126.76:8000/ws/chat/test_session_123');

ws.on('open', function() {
    console.log('✅ WebSocket 연결 성공');
    
    // 테스트 메시지 전송 (chat_message 타입 사용)
    const testMessage = {
        type: 'chat_message',
        data: {
            message: '안녕하세요! 립싱크 테스트입니다.',
            user_id: 'test_user',
            session_id: 'test_session_123'
        }
    };
    
    console.log('📤 테스트 메시지 전송:', testMessage.data.message);
    ws.send(JSON.stringify(testMessage));
});

ws.on('message', function(data) {
    try {
        const response = JSON.parse(data.toString());
        console.log('📥 서버 응답:', response.type);
        
        // 립싱크 데이터 확인
        if (response.data && response.data.lip_sync_data) {
            console.log('✅ 립싱크 데이터 수신 성공!');
            console.log('📊 립싱크 데이터 상세:');
            console.log('  - phonemes:', response.data.lip_sync_data.phonemes?.length || 0, '개');
            console.log('  - mouth_shapes:', response.data.lip_sync_data.mouth_shapes?.length || 0, '개');
            console.log('  - duration:', response.data.lip_sync_data.duration, '초');
            console.log('  - frame_rate:', response.data.lip_sync_data.frame_rate);
            
            if (response.data.lip_sync_data.phonemes?.length > 0) {
                console.log('✅ Step 1 완료: EdgeTTS Provider 립싱크 데이터 생성 확인됨');
            } else {
                console.log('❌ 립싱크 데이터는 있지만 phonemes가 비어있음');
            }
        } else {
            console.log('❌ 립싱크 데이터 없음');
        }
        
        // 오디오 데이터 확인
        if (response.data && response.data.audio_data) {
            console.log('✅ TTS 오디오 데이터도 수신됨');
        }
        
    } catch (error) {
        console.error('❌ 응답 파싱 오류:', error);
    }
});

ws.on('error', function(error) {
    console.error('❌ WebSocket 오류:', error);
});

ws.on('close', function() {
    console.log('🔌 WebSocket 연결 종료');
    process.exit(0);
});

// 10초 후 타임아웃
setTimeout(() => {
    console.log('⏰ 테스트 타임아웃 (10초)');
    ws.close();
}, 10000);
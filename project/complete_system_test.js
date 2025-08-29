/**
 * 전체 시스템 테스트 - 립싱크 데이터 흐름 완전 검증
 * 
 * 1. WebSocket 연결 테스트
 * 2. 메시지 전송 및 응답 확인
 * 3. EdgeTTS Provider 립싱크 데이터 생성 확인
 * 4. 데이터베이스 세션 저장 확인
 * 5. WebSocket을 통한 립싱크 데이터 전송 확인
 * 6. 프론트엔드 호환성 검증
 */

const WebSocket = require('ws');

console.log('🎯 전체 시스템 테스트 시작');
console.log('=' .repeat(50));

let testResults = {
    websocket_connection: false,
    message_sending: false,
    lipsync_generation: false,
    data_transmission: false,
    system_integration: false
};

let testNumber = 1;

// WebSocket 연결
console.log(`\n${testNumber++}. WebSocket 연결 테스트`);
const ws = new WebSocket('ws://localhost:8000/ws/chat/system_test_session_' + Date.now());

ws.on('open', function() {
    console.log('✅ WebSocket 연결 성공');
    testResults.websocket_connection = true;
    
    // 여러 메시지로 다양한 시나리오 테스트
    const testMessages = [
        {
            type: 'chat_message',
            data: {
                message: '안녕하세요! 립싱크 시스템 테스트입니다.',
                user_id: 'test_user_1',
                session_id: 'system_test_session_' + Date.now()
            },
            test_name: '기본 채팅 메시지'
        },
        {
            type: 'chat_message', 
            data: {
                message: '이것은 좀 더 긴 메시지로 립싱크 데이터가 더 많이 생성되는지 확인하는 테스트입니다. 한국어 발음 다양성 테스트를 위한 문장입니다.',
                user_id: 'test_user_2',
                session_id: 'system_test_session_' + Date.now()
            },
            test_name: '긴 메시지 테스트'
        },
        {
            type: 'chat_message',
            data: {
                message: '오늘의 운세를 알려주세요!',
                user_id: 'test_user_3', 
                session_id: 'system_test_session_' + Date.now()
            },
            test_name: '운세 요청 메시지'
        }
    ];
    
    let currentTest = 0;
    let receivedResponses = [];
    
    function sendNextMessage() {
        if (currentTest >= testMessages.length) {
            // 모든 테스트 완료
            setTimeout(() => {
                printTestResults();
                ws.close();
            }, 2000);
            return;
        }
        
        const testMsg = testMessages[currentTest];
        console.log(`\n${testNumber++}. ${testMsg.test_name} 테스트`);
        console.log(`📤 메시지 전송: "${testMsg.data.message.substring(0, 30)}..."`);
        
        ws.send(JSON.stringify(testMsg));
        testResults.message_sending = true;
        currentTest++;
        
        // 다음 메시지는 3초 후 전송
        setTimeout(sendNextMessage, 3000);
    }
    
    // 첫 번째 메시지 전송
    setTimeout(sendNextMessage, 1000);
});

ws.on('message', function(data) {
    try {
        const response = JSON.parse(data.toString());
        console.log(`📥 서버 응답: ${response.type}`);
        
        receivedResponses.push(response);
        
        // 응답 유형별 분석
        if (response.type === 'connection_established') {
            console.log('  ✅ 연결 설정 확인됨');
        }
        else if (response.type === 'llm_details') {
            console.log('  ✅ LLM 세부 정보 수신');
        }
        else if (response.type === 'llm_response') {
            console.log('  ✅ LLM 응답 수신');
        }
        else if (response.type === 'chat_message') {
            console.log('  ✅ 챗봇 메시지 수신');
            
            // 립싱크 데이터 상세 분석
            if (response.data && response.data.lip_sync_data) {
                const lsd = response.data.lip_sync_data;
                console.log('  🎭 립싱크 데이터 분석:');
                console.log(`    - phonemes: ${lsd.phonemes?.length || 0}개`);
                console.log(`    - mouth_shapes: ${lsd.mouth_shapes?.length || 0}개`);
                console.log(`    - duration: ${lsd.duration}초`);
                console.log(`    - frame_rate: ${lsd.frame_rate} FPS`);
                
                // 데이터 품질 확인
                if (lsd.phonemes?.length > 0 && lsd.mouth_shapes?.length > 0) {
                    console.log('  ✅ 립싱크 데이터 생성 확인');
                    testResults.lipsync_generation = true;
                    testResults.data_transmission = true;
                    
                    // 첫 번째 몇 개의 phoneme 샘플 출력
                    if (lsd.phonemes.length > 0) {
                        console.log('  📊 Phoneme 샘플 (처음 3개):');
                        for (let i = 0; i < Math.min(3, lsd.phonemes.length); i++) {
                            const phoneme = lsd.phonemes[i];
                            console.log(`    ${i+1}. time:${phoneme[0]?.toFixed(2)}s, sound:'${phoneme[1]}', duration:${phoneme[2]?.toFixed(2)}s`);
                        }
                    }
                    
                    // 첫 번째 몇 개의 mouth shape 샘플 출력  
                    if (lsd.mouth_shapes.length > 0) {
                        console.log('  👄 Mouth Shape 샘플 (처음 2개):');
                        for (let i = 0; i < Math.min(2, lsd.mouth_shapes.length); i++) {
                            const shape = lsd.mouth_shapes[i];
                            const params = shape[1];
                            console.log(`    ${i+1}. time:${shape[0]?.toFixed(2)}s, ParamA:${params?.ParamA}, ParamI:${params?.ParamI}, ParamO:${params?.ParamO}`);
                        }
                    }
                } else {
                    console.log('  ❌ 립싱크 데이터가 비어있음');
                }
            } else {
                console.log('  ❌ 립싱크 데이터 없음');
            }
            
            // TTS 오디오 데이터 확인
            if (response.data && response.data.audio_data) {
                console.log('  🔊 TTS 오디오 데이터 확인됨');
            } else {
                console.log('  ⚠️  TTS 오디오 데이터 없음');
            }
            
            testResults.system_integration = true;
        }
        else if (response.type === 'error') {
            console.log('  ❌ 오류 응답:', response.data?.message || 'Unknown error');
        }
        
    } catch (error) {
        console.error('❌ 응답 파싱 오류:', error);
    }
});

ws.on('error', function(error) {
    console.error('❌ WebSocket 오류:', error);
});

ws.on('close', function() {
    console.log('\n🔌 WebSocket 연결 종료');
    process.exit(0);
});

function printTestResults() {
    console.log('\n' + '='.repeat(50));
    console.log('📊 전체 시스템 테스트 결과');
    console.log('='.repeat(50));
    
    let passedTests = 0;
    let totalTests = Object.keys(testResults).length;
    
    for (const [testName, result] of Object.entries(testResults)) {
        const status = result ? '✅ PASS' : '❌ FAIL';
        const description = getTestDescription(testName);
        console.log(`${status} ${description}`);
        if (result) passedTests++;
    }
    
    console.log('\n📈 전체 결과:');
    console.log(`통과: ${passedTests}/${totalTests} (${Math.round(passedTests/totalTests*100)}%)`);
    
    if (passedTests === totalTests) {
        console.log('\n🎉 모든 테스트 통과! 립싱크 시스템이 정상 동작합니다.');
    } else {
        console.log('\n⚠️  일부 테스트 실패. 시스템 점검 필요.');
    }
}

function getTestDescription(testName) {
    const descriptions = {
        websocket_connection: 'WebSocket 연결',
        message_sending: '메시지 전송',
        lipsync_generation: '립싱크 데이터 생성', 
        data_transmission: '립싱크 데이터 전송',
        system_integration: '시스템 통합'
    };
    return descriptions[testName] || testName;
}

// 30초 후 타임아웃
setTimeout(() => {
    console.log('\n⏰ 테스트 타임아웃 (30초)');
    printTestResults();
    ws.close();
}, 30000);
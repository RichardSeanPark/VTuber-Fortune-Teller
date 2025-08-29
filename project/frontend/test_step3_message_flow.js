/**
 * Step 3: WebSocket 메시지 전달 흐름 상세 테스트
 */
const { chromium } = require('playwright');

async function testMessageFlow() {
    console.log('📡 [Step 3] WebSocket 메시지 전달 흐름 테스트 시작\n');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const messageFlow = {
        sent: [],
        received: [],
        errors: []
    };
    
    page.on('console', msg => {
        const text = msg.text();
        
        // 메시지 송신 로그
        if (text.includes('메시지 전송') || text.includes('sendChatMessage')) {
            messageFlow.sent.push(text);
        }
        
        // 메시지 수신 로그
        if (text.includes('메시지 수신') || text.includes('chat_message')) {
            messageFlow.received.push(text);
        }
        
        // 에러 로그
        if (text.includes('Error') || text.includes('error')) {
            messageFlow.errors.push(text);
        }
    });
    
    try {
        // 1. 페이지 로드
        console.log('3.1 페이지 초기화 및 WebSocket 연결');
        await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        console.log('  ✅ 초기화 완료\n');
        
        // 2. 메시지 흐름 테스트
        console.log('3.2 메시지 흐름 추적 테스트');
        
        const testMessage = '메시지 흐름 테스트';
        console.log(`  📤 테스트 메시지: "${testMessage}"\n`);
        
        // 메시지 전송 전 상태 초기화
        messageFlow.sent = [];
        messageFlow.received = [];
        
        const messageInput = await page.locator('textarea[placeholder*="메시지"]').first();
        await messageInput.fill(testMessage);
        
        const sendStartTime = Date.now();
        await messageInput.press('Enter');
        
        // 응답 대기
        await page.waitForTimeout(3000);
        const roundTripTime = Date.now() - sendStartTime;
        
        // 3. 송신 확인
        console.log('  📊 송신 분석:');
        if (messageFlow.sent.length > 0) {
            console.log(`    ✅ ${messageFlow.sent.length}개 송신 로그`);
            messageFlow.sent.slice(0, 3).forEach(log => 
                console.log(`      - ${log.substring(0, 100)}`)
            );
        } else {
            console.log('    ⚠️ 송신 로그 없음');
        }
        
        // 4. 수신 확인
        console.log('\n  📊 수신 분석:');
        if (messageFlow.received.length > 0) {
            console.log(`    ✅ ${messageFlow.received.length}개 수신 로그`);
            
            // 메시지 타입 분석
            const messageTypes = new Set();
            messageFlow.received.forEach(log => {
                if (log.includes('type:')) {
                    const typeMatch = log.match(/type:\s*(\w+)/);
                    if (typeMatch) messageTypes.add(typeMatch[1]);
                }
            });
            
            if (messageTypes.size > 0) {
                console.log(`    📋 수신된 메시지 타입: ${Array.from(messageTypes).join(', ')}`);
            }
            
            // 립싱크 데이터 포함 여부
            const hasLipsyncData = messageFlow.received.some(log => 
                log.includes('lip_sync_data') || log.includes('lipSyncData')
            );
            console.log(`    🎭 립싱크 데이터: ${hasLipsyncData ? '✅ 포함' : '❌ 미포함'}`);
            
            // 오디오 데이터 포함 여부
            const hasAudioData = messageFlow.received.some(log => 
                log.includes('audio_data') || log.includes('audioData')
            );
            console.log(`    🔊 오디오 데이터: ${hasAudioData ? '✅ 포함' : '❌ 미포함'}`);
            
        } else {
            console.log('    ⚠️ 수신 로그 없음');
        }
        
        // 5. 응답 시간 분석
        console.log(`\n  ⏱️ 응답 시간: ${roundTripTime}ms`);
        if (roundTripTime < 1000) {
            console.log('    ✅ 우수한 응답 속도');
        } else if (roundTripTime < 3000) {
            console.log('    ℹ️ 보통 응답 속도');
        } else {
            console.log('    ⚠️ 느린 응답 속도');
        }
        
        // 6. 에러 확인
        console.log('\n3.3 메시지 전달 에러 확인');
        if (messageFlow.errors.length === 0) {
            console.log('  ✅ 에러 없음');
        } else {
            console.log(`  ⚠️ ${messageFlow.errors.length}개 에러 감지:`);
            messageFlow.errors.slice(0, 3).forEach(error => 
                console.log(`    - ${error.substring(0, 100)}`)
            );
        }
        
        // 7. WebSocket 상태 확인
        console.log('\n3.4 WebSocket 연결 상태');
        const connectionLogs = await page.evaluate(() => {
            const logs = [];
            if (window.webSocketService) {
                logs.push(`연결 상태: ${window.webSocketService.isConnected() ? '연결됨' : '끊김'}`);
            }
            return logs;
        });
        
        if (connectionLogs.length > 0) {
            connectionLogs.forEach(log => console.log(`  ${log}`));
        }
        
        console.log('\n✅ [Step 3] WebSocket 메시지 전달 흐름 테스트 완료\n');
        
    } catch (error) {
        console.error('❌ 메시지 흐름 테스트 실패:', error.message);
    } finally {
        await browser.close();
    }
}

testMessageFlow().catch(console.error);
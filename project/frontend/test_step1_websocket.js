/**
 * Step 1: WebSocket 연결 및 초기화 상세 테스트
 */
const { chromium } = require('playwright');

async function testWebSocketConnection() {
    console.log('🔌 [Step 1] WebSocket 연결 및 초기화 테스트 시작\n');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // 콘솔 로그 수집
    const logs = [];
    page.on('console', msg => {
        const text = msg.text();
        logs.push(text);
        if (text.includes('WebSocket') || text.includes('연결')) {
            console.log(`  📝 ${text}`);
        }
    });
    
    try {
        // 1. 페이지 로드
        console.log('1.1 페이지 로드 테스트');
        const startTime = Date.now();
        await page.goto('http://localhost:3000/', { waitUntil: 'networkidle', timeout: 10000 });
        const loadTime = Date.now() - startTime;
        console.log(`  ✅ 페이지 로드 성공 (${loadTime}ms)\n`);
        
        // 2. WebSocket 연결 상태 확인
        console.log('1.2 WebSocket 연결 상태 확인');
        await page.waitForTimeout(2000); // WebSocket 연결 대기
        
        const wsConnectLogs = logs.filter(log => 
            log.includes('WebSocket 연결') || 
            log.includes('connection_established')
        );
        
        if (wsConnectLogs.length > 0) {
            console.log(`  ✅ WebSocket 연결 확인됨 (${wsConnectLogs.length}개 로그)`);
            wsConnectLogs.forEach(log => console.log(`    - ${log.substring(0, 100)}`));
        } else {
            console.log('  ⚠️ WebSocket 연결 로그 없음');
        }
        
        // 3. WebSocket 메시지 송수신 확인
        console.log('\n1.3 WebSocket 메시지 송수신 테스트');
        
        // 메시지 전송
        const messageInput = await page.locator('textarea[placeholder*="메시지"]').first();
        await messageInput.fill('WebSocket 테스트 메시지');
        await messageInput.press('Enter');
        
        // 응답 대기
        await page.waitForTimeout(3000);
        
        const messageLogs = logs.filter(log => 
            log.includes('메시지 수신') || 
            log.includes('chat_message')
        );
        
        if (messageLogs.length > 0) {
            console.log(`  ✅ 메시지 송수신 확인 (${messageLogs.length}개)`);
        } else {
            console.log('  ⚠️ 메시지 송수신 로그 없음');
        }
        
        // 4. WebSocket 에러 체크
        console.log('\n1.4 WebSocket 에러 체크');
        const errorLogs = logs.filter(log => 
            log.includes('error') || 
            log.includes('Error') ||
            log.includes('실패')
        );
        
        if (errorLogs.length === 0) {
            console.log('  ✅ WebSocket 에러 없음');
        } else {
            console.log(`  ⚠️ ${errorLogs.length}개 에러 발견:`);
            errorLogs.slice(0, 5).forEach(log => console.log(`    - ${log.substring(0, 100)}`));
        }
        
        // 5. 연결 안정성 확인
        console.log('\n1.5 WebSocket 연결 안정성 테스트');
        const reconnectLogs = logs.filter(log => 
            log.includes('재연결') || 
            log.includes('reconnect')
        );
        
        if (reconnectLogs.length === 0) {
            console.log('  ✅ 연결 안정적 (재연결 시도 없음)');
        } else {
            console.log(`  ℹ️ ${reconnectLogs.length}회 재연결 시도`);
        }
        
        console.log('\n✅ [Step 1] WebSocket 연결 테스트 완료\n');
        
    } catch (error) {
        console.error('❌ WebSocket 연결 테스트 실패:', error.message);
    } finally {
        await browser.close();
    }
}

testWebSocketConnection().catch(console.error);
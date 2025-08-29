const { chromium } = require('playwright');

async function testLipSync() {
    const browser = await chromium.launch({ 
        headless: false,  // 헤드풀 모드로 실제 화면을 볼 수 있게
        slowMo: 1000    // 동작을 천천히 해서 관찰할 수 있게
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // 콘솔 로그 수집
    const logs = [];
    page.on('console', msg => {
        const text = msg.text();
        logs.push(text);
        console.log('브라우저 콘솔:', text);
    });
    
    try {
        console.log('🌐 페이지 로딩 중...');
        await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
        
        // 페이지가 완전히 로드될 때까지 대기
        await page.waitForTimeout(3000);
        
        console.log('📝 메시지 입력 중...');
        // 메시지 입력
        await page.fill('input[placeholder*="메시지"], input[placeholder*="질문"], textarea', '안녕하세요, 테스트입니다');
        
        console.log('📨 전송 버튼 클릭...');
        // 전송 버튼 클릭 (여러 가능한 선택자 시도)
        const sendButton = await page.locator('button:has-text("전송"), button:has-text("Send"), button[type="submit"]').first();
        await sendButton.click();
        
        console.log('🎬 립싱크 로그 대기 중... (10초)');
        // 립싱크 관련 로그가 나타날 때까지 대기
        await page.waitForTimeout(10000);
        
        console.log('📊 립싱크 관련 로그 분석...');
        const lipSyncLogs = logs.filter(log => 
            log.includes('립싱크') || 
            log.includes('TTS') || 
            log.includes('🎙️') || 
            log.includes('🎤') || 
            log.includes('🎭') ||
            log.includes('viseme') ||
            log.includes('mouth')
        );
        
        console.log('\n=== 립싱크 관련 로그 ===');
        lipSyncLogs.forEach(log => console.log('📝', log));
        
        if (lipSyncLogs.length === 0) {
            console.log('❌ 립싱크 관련 로그가 없습니다.');
        } else {
            console.log(`✅ 총 ${lipSyncLogs.length}개의 립싱크 관련 로그 발견`);
        }
        
        // Live2D 모델이 로드되었는지 확인
        const live2dModel = await page.evaluate(() => {
            return window.app && window.app._model ? '모델 로드됨' : '모델 없음';
        });
        
        console.log('🎭 Live2D 모델 상태:', live2dModel);
        
        // 추가로 5초 더 대기하여 모든 로그 수집
        await page.waitForTimeout(5000);
        
    } catch (error) {
        console.error('❌ 테스트 실행 중 오류:', error.message);
    } finally {
        await browser.close();
    }
}

// 테스트 실행
testLipSync().catch(console.error);
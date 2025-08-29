/**
 * Step 2: 백엔드 립싱크 데이터 생성 상세 테스트
 */
const { chromium } = require('playwright');

async function testBackendLipsyncGeneration() {
    console.log('🎭 [Step 2] 백엔드 립싱크 데이터 생성 테스트 시작\n');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const lipsyncLogs = [];
    const messageLogs = [];
    
    page.on('console', msg => {
        const text = msg.text();
        
        // 립싱크 관련 로그 수집
        if (text.includes('립싱크') || text.includes('lip_sync') || text.includes('LipSync')) {
            lipsyncLogs.push(text);
            console.log(`  📝 ${text.substring(0, 150)}`);
        }
        
        // 메시지 관련 로그 수집
        if (text.includes('chat_message') || text.includes('메시지 수신')) {
            messageLogs.push(text);
        }
    });
    
    try {
        // 1. 페이지 로드 및 초기화
        console.log('2.1 페이지 초기화');
        await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        console.log('  ✅ 페이지 로드 완료\n');
        
        // 2. 테스트 메시지 전송
        console.log('2.2 테스트 메시지 전송 및 백엔드 응답 확인');
        const testMessages = [
            '안녕하세요',
            '립싱크 테스트입니다',
            '입모양이 정확한가요?'
        ];
        
        for (const message of testMessages) {
            console.log(`\n  📤 전송: "${message}"`);
            
            const messageInput = await page.locator('textarea[placeholder*="메시지"]').first();
            await messageInput.fill(message);
            await messageInput.press('Enter');
            
            // 응답 대기
            await page.waitForTimeout(3000);
            
            // 백엔드 립싱크 데이터 확인
            const backendLipsyncLogs = lipsyncLogs.filter(log => 
                log.includes('백엔드 립싱크') || 
                log.includes('lip_sync_data')
            );
            
            if (backendLipsyncLogs.length > 0) {
                console.log(`  ✅ 백엔드 립싱크 데이터 감지됨`);
                const lastLog = backendLipsyncLogs[backendLipsyncLogs.length - 1];
                
                // 프레임 수 추출
                const frameMatch = lastLog.match(/(\d+)\s*프레임/);
                if (frameMatch) {
                    console.log(`    - 프레임 수: ${frameMatch[1]}`);
                }
                
                // 데이터 유무 확인
                if (lastLog.includes('없음') || lastLog.includes('null')) {
                    console.log(`    ⚠️ 백엔드 립싱크 데이터 없음 (폴백 모드)`);
                } else {
                    console.log(`    ✅ 백엔드 립싱크 데이터 존재`);
                }
            } else {
                console.log(`  ⚠️ 백엔드 립싱크 로그 없음`);
            }
            
            // 에러 확인
            const errorLogs = lipsyncLogs.filter(log => 
                log.includes('❌') || 
                log.includes('error')
            );
            
            if (errorLogs.length > 0) {
                console.log(`    ❌ ${errorLogs.length}개 립싱크 에러 감지`);
            }
            
            lipsyncLogs.length = 0; // 로그 초기화
        }
        
        // 3. 백엔드 데이터 구조 분석
        console.log('\n2.3 백엔드 메시지 구조 분석');
        
        const chatMessages = messageLogs.filter(log => log.includes('chat_message'));
        if (chatMessages.length > 0) {
            console.log(`  ✅ ${chatMessages.length}개 chat_message 수신`);
            
            // 마지막 메시지 분석
            const lastMessage = chatMessages[chatMessages.length - 1];
            console.log(`  📊 메시지 구조 확인:`);
            
            if (lastMessage.includes('audio_data')) {
                console.log('    - audio_data: ✅ 포함');
            } else {
                console.log('    - audio_data: ❌ 미포함');
            }
            
            if (lastMessage.includes('lip_sync_data')) {
                console.log('    - lip_sync_data: ✅ 포함');
            } else {
                console.log('    - lip_sync_data: ❌ 미포함');
            }
            
            if (lastMessage.includes('tts_text')) {
                console.log('    - tts_text: ✅ 포함');
            } else {
                console.log('    - tts_text: ❌ 미포함');
            }
        }
        
        // 4. 에러 확인
        console.log('\n2.4 백엔드 에러 확인');
        const errorCount = messageLogs.filter(log => 
            log.includes('error') || log.includes('Error')
        ).length;
        
        if (errorCount === 0) {
            console.log('  ✅ 백엔드 에러 없음');
        } else {
            console.log(`  ⚠️ ${errorCount}개 에러 감지됨`);
        }
        
        console.log('\n✅ [Step 2] 백엔드 립싱크 데이터 생성 테스트 완료\n');
        
    } catch (error) {
        console.error('❌ 백엔드 립싱크 테스트 실패:', error.message);
    } finally {
        await browser.close();
    }
}

testBackendLipsyncGeneration().catch(console.error);
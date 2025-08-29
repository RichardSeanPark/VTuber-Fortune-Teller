/**
 * Step 4: 프론트엔드 립싱크 데이터 수신 및 처리 테스트
 */
const { chromium } = require('playwright');

async function testFrontendLipsyncProcessing() {
    console.log('🎯 [Step 4] 프론트엔드 립싱크 수신 및 처리 테스트 시작\n');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext();
    const page = await context.newPage();
    
    const lipsyncStats = {
        frames: [],
        intervals: [],
        simulationCount: 0,
        backendDataCount: 0
    };
    
    page.on('console', msg => {
        const text = msg.text();
        
        // 립싱크 프레임 추적
        if (text.includes('립싱크 - 입 벌림:')) {
            const match = text.match(/입 벌림:\s*([\d.]+)/);
            if (match) {
                lipsyncStats.frames.push(parseFloat(match[1]));
            }
        }
        
        // 립싱크 인터벌 추적
        if (text.includes('립싱크 인터벌 생성:')) {
            const match = text.match(/생성:\s*(\d+)/);
            if (match) {
                lipsyncStats.intervals.push(parseInt(match[1]));
            }
        }
        
        // 백엔드 데이터 성공 vs 실패 추적
        if (text.includes('✅') && text.includes('백엔드')) {
            lipsyncStats.backendDataCount++;
        }
        if (text.includes('❌') && text.includes('백엔드')) {
            lipsyncStats.simulationCount++;
        }
    });
    
    try {
        // 1. 페이지 로드
        console.log('4.1 페이지 초기화');
        await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        console.log('  ✅ 초기화 완료\n');
        
        // 2. 립싱크 데이터 수신 테스트
        console.log('4.2 프론트엔드 립싱크 처리 테스트');
        
        const testMessages = [
            '짧은 메시지',
            '조금 더 긴 메시지입니다. 립싱크가 잘 작동하나요?',
            '아주 긴 메시지를 보내봅니다. 프론트엔드에서 립싱크 데이터를 올바르게 처리하고 있는지 확인하기 위한 테스트입니다.'
        ];
        
        for (let i = 0; i < testMessages.length; i++) {
            const message = testMessages[i];
            console.log(`\n  테스트 ${i + 1}: "${message.substring(0, 30)}..."`);
            
            // 통계 초기화
            lipsyncStats.frames = [];
            lipsyncStats.intervals = [];
            
            const messageInput = await page.locator('textarea[placeholder*="메시지"]').first();
            await messageInput.fill(message);
            await messageInput.press('Enter');
            
            // 립싱크 애니메이션 대기
            await page.waitForTimeout(5000);
            
            // 결과 분석
            console.log('  📊 립싱크 처리 결과:');
            
            // 프레임 분석
            if (lipsyncStats.frames.length > 0) {
                const avgMouthOpen = lipsyncStats.frames.reduce((a, b) => a + b, 0) / lipsyncStats.frames.length;
                const maxMouthOpen = Math.max(...lipsyncStats.frames);
                const minMouthOpen = Math.min(...lipsyncStats.frames);
                
                console.log(`    ✅ ${lipsyncStats.frames.length}개 프레임 생성됨`);
                console.log(`    📈 입 벌림 범위: ${minMouthOpen.toFixed(2)} ~ ${maxMouthOpen.toFixed(2)}`);
                console.log(`    📊 평균 입 벌림: ${avgMouthOpen.toFixed(2)}`);
                
                // 프레임 레이트 계산
                if (lipsyncStats.intervals.length > 0) {
                    const intervalMs = lipsyncStats.intervals[0];
                    const fps = Math.round(1000 / intervalMs);
                    console.log(`    ⏱️ 프레임 간격: ${intervalMs}ms (~${fps}fps)`);
                }
            } else {
                console.log('    ⚠️ 립싱크 프레임이 생성되지 않음');
            }
            
            // 메시지 길이와 프레임 수 비교
            const expectedFrames = message.length * 2; // 대략적인 예상 프레임 수
            const frameRatio = lipsyncStats.frames.length / expectedFrames;
            
            if (frameRatio > 0.5 && frameRatio < 2) {
                console.log(`    ✅ 메시지 길이 대비 적절한 프레임 수`);
            } else {
                console.log(`    ⚠️ 메시지 길이 대비 프레임 수 이상 (비율: ${frameRatio.toFixed(2)})`);
            }
        }
        
        // 3. 데이터 소스 분석
        console.log('\n4.3 립싱크 데이터 소스 분석');
        console.log(`  ❌ 백엔드 에러 횟수: ${lipsyncStats.simulationCount}`);
        console.log(`  ✅ 백엔드 성공 횟수: ${lipsyncStats.backendDataCount}`);
        
        if (lipsyncStats.backendDataCount > 0) {
            console.log('  ✅ 백엔드 립싱크 데이터 수신 성공');
        } else {
            console.log('  ❌ 백엔드 립싱크 데이터 수신 실패');
        }
        
        // 4. 메모리 및 성능 확인
        console.log('\n4.4 프론트엔드 성능 확인');
        const metrics = await page.evaluate(() => {
            return {
                memory: performance.memory ? 
                    Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) : null,
                fps: 60 // 기본값, 실제로는 requestAnimationFrame으로 측정 필요
            };
        });
        
        if (metrics.memory) {
            console.log(`  💾 메모리 사용량: ${metrics.memory}MB`);
            if (metrics.memory < 100) {
                console.log('    ✅ 정상적인 메모리 사용량');
            } else {
                console.log('    ⚠️ 높은 메모리 사용량');
            }
        }
        
        console.log('\n✅ [Step 4] 프론트엔드 립싱크 수신 및 처리 테스트 완료\n');
        
    } catch (error) {
        console.error('❌ 프론트엔드 립싱크 테스트 실패:', error.message);
    } finally {
        await browser.close();
    }
}

testFrontendLipsyncProcessing().catch(console.error);
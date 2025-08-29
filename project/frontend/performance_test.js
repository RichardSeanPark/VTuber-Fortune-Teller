const { chromium } = require('playwright');

/**
 * 성능 및 안정성 집중 테스트
 * - 응답 시간 측정
 * - 메모리 사용량 모니터링
 * - 립싱크 품질 검증
 * - 시스템 리소스 분석
 */

(async () => {
  console.log('⚡ [성능 테스트] 립싱크 시스템 성능 및 안정성 검증 시작');
  
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 성능 측정 데이터
  const performanceData = {
    pageLoad: { start: 0, end: 0, duration: 0 },
    ttsApiCalls: [],
    lipSyncFrames: [],
    memoryUsage: [],
    errors: []
  };
  
  // 페이지 로드 성능 측정
  const pageLoadStart = Date.now();
  
  // 콘솔 모니터링
  page.on('console', msg => {
    const text = msg.text();
    const timestamp = Date.now();
    
    // TTS API 응답 시간 측정
    if (text.includes('TTS API 요청 준비')) {
      const apiCall = { start: timestamp, sessionId: text.match(/lipsync_(\d+)/)?.[1] };
      performanceData.ttsApiCalls.push(apiCall);
    }
    
    if (text.includes('TTS API 응답 상태: 200')) {
      const lastCall = performanceData.ttsApiCalls[performanceData.ttsApiCalls.length - 1];
      if (lastCall && !lastCall.duration) {
        lastCall.end = timestamp;
        lastCall.duration = timestamp - lastCall.start;
      }
    }
    
    // 립싱크 프레임 수 추출
    const frameMatch = text.match(/프레임 수:\s*(\d+)/);
    if (frameMatch) {
      performanceData.lipSyncFrames.push({
        frames: parseInt(frameMatch[1]),
        timestamp: timestamp
      });
    }
    
    // 오류 추적
    if (text.includes('❌') || text.includes('Error')) {
      performanceData.errors.push({
        timestamp: timestamp,
        message: text.substring(0, 200)
      });
    }
  });
  
  try {
    // 1. 페이지 로드 성능
    console.log('🏃‍♂️ [테스트 1] 페이지 로드 성능 측정');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    performanceData.pageLoad.end = Date.now();
    performanceData.pageLoad.duration = performanceData.pageLoad.end - pageLoadStart;
    console.log(`📊 페이지 로드 시간: ${performanceData.pageLoad.duration}ms`);
    
    // 초기 메모리 사용량
    const initialMemory = await page.evaluate(() => {
      return {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        timestamp: Date.now()
      };
    });
    performanceData.memoryUsage.push(initialMemory);
    console.log(`💾 초기 메모리: ${Math.round(initialMemory.usedJSHeapSize / 1024 / 1024)}MB`);
    
    await page.waitForTimeout(3000);
    
    // 2. 연속 메시지 처리 성능 테스트
    console.log('🔄 [테스트 2] 연속 메시지 처리 성능 (10회)');
    const testMessages = [
      '성능 테스트 1',
      '성능 테스트 2', 
      '성능 테스트 3',
      '성능 테스트 4',
      '성능 테스트 5',
      '연속 처리 테스트 6',
      '연속 처리 테스트 7',
      '연속 처리 테스트 8',
      '연속 처리 테스트 9',
      '최종 성능 테스트 10'
    ];
    
    const inputElement = page.locator('input[placeholder*="메시지"]').first();
    
    for (let i = 0; i < testMessages.length; i++) {
      const message = testMessages[i];
      const msgStart = Date.now();
      
      console.log(`📝 [${i+1}/10] "${message}"`);
      
      await inputElement.fill(message);
      await page.keyboard.press('Enter');
      
      // 응답 완료 대기 (간단한 대기)
      await page.waitForTimeout(3000);
      
      // 메모리 사용량 체크
      const currentMemory = await page.evaluate(() => {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          timestamp: Date.now()
        };
      });
      performanceData.memoryUsage.push(currentMemory);
      
      const memoryDiff = currentMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      console.log(`💾 메모리 증가: +${Math.round(memoryDiff / 1024 / 1024)}MB`);
      
      if (i < testMessages.length - 1) {
        await page.waitForTimeout(1000); // 메시지간 간격
      }
    }
    
    // 3. 성능 통계 분석
    console.log('\n📊 [성능 분석] 종합 성능 보고서');
    console.log('='.repeat(60));
    
    // TTS API 성능
    const completedCalls = performanceData.ttsApiCalls.filter(call => call.duration);
    if (completedCalls.length > 0) {
      const avgApiTime = completedCalls.reduce((sum, call) => sum + call.duration, 0) / completedCalls.length;
      const maxApiTime = Math.max(...completedCalls.map(call => call.duration));
      const minApiTime = Math.min(...completedCalls.map(call => call.duration));
      
      console.log(`🚀 TTS API 성능:`);
      console.log(`   - 평균 응답시간: ${Math.round(avgApiTime)}ms`);
      console.log(`   - 최대 응답시간: ${maxApiTime}ms`);
      console.log(`   - 최소 응답시간: ${minApiTime}ms`);
      console.log(`   - 총 호출 수: ${completedCalls.length}개`);
    }
    
    // 립싱크 성능
    if (performanceData.lipSyncFrames.length > 0) {
      const avgFrames = performanceData.lipSyncFrames.reduce((sum, item) => sum + item.frames, 0) / performanceData.lipSyncFrames.length;
      const maxFrames = Math.max(...performanceData.lipSyncFrames.map(item => item.frames));
      const minFrames = Math.min(...performanceData.lipSyncFrames.map(item => item.frames));
      
      console.log(`🎭 립싱크 성능:`);
      console.log(`   - 평균 프레임: ${Math.round(avgFrames)}개`);
      console.log(`   - 최대 프레임: ${maxFrames}개`);
      console.log(`   - 최소 프레임: ${minFrames}개`);
      console.log(`   - 총 립싱크: ${performanceData.lipSyncFrames.length}회`);
    }
    
    // 메모리 사용량 분석
    const finalMemory = performanceData.memoryUsage[performanceData.memoryUsage.length - 1];
    const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
    const maxMemory = Math.max(...performanceData.memoryUsage.map(m => m.usedJSHeapSize));
    
    console.log(`💾 메모리 사용량:`);
    console.log(`   - 초기: ${Math.round(initialMemory.usedJSHeapSize / 1024 / 1024)}MB`);
    console.log(`   - 최종: ${Math.round(finalMemory.usedJSHeapSize / 1024 / 1024)}MB`);
    console.log(`   - 증가: +${Math.round(memoryIncrease / 1024 / 1024)}MB`);
    console.log(`   - 최대: ${Math.round(maxMemory / 1024 / 1024)}MB`);
    
    // 오류 분석
    console.log(`⚠️ 발견된 오류:`);
    console.log(`   - 총 오류 수: ${performanceData.errors.length}개`);
    if (performanceData.errors.length > 0) {
      console.log(`   - 주요 오류: "${performanceData.errors[0].message.substring(0, 50)}..."`);
    }
    
    // 4. 품질 평가
    const qualityScore = calculatePerformanceScore(performanceData);
    console.log(`\n🏆 전체 성능 점수: ${qualityScore}/100`);
    
    // 성능 등급
    let grade = 'F';
    if (qualityScore >= 90) grade = 'A+';
    else if (qualityScore >= 80) grade = 'A';
    else if (qualityScore >= 70) grade = 'B';
    else if (qualityScore >= 60) grade = 'C';
    else if (qualityScore >= 50) grade = 'D';
    
    console.log(`📈 성능 등급: ${grade}`);
    
    // 최적화 권장사항
    console.log(`\n💡 최적화 권장사항:`);
    if (completedCalls.length > 0 && avgApiTime > 2000) {
      console.log(`   - TTS API 응답시간 개선 필요 (현재: ${Math.round(avgApiTime)}ms)`);
    }
    if (memoryIncrease > 50 * 1024 * 1024) {
      console.log(`   - 메모리 누수 점검 필요 (증가: ${Math.round(memoryIncrease / 1024 / 1024)}MB)`);
    }
    if (performanceData.errors.length > 5) {
      console.log(`   - 에러 핸들링 개선 필요 (오류: ${performanceData.errors.length}개)`);
    }
    
  } catch (error) {
    console.error('❌ [성능 테스트 실패]', error.message);
  } finally {
    await page.waitForTimeout(3000);
    await browser.close();
  }
})();

function calculatePerformanceScore(data) {
  let score = 100;
  
  // 페이지 로드 시간 페널티
  if (data.pageLoad.duration > 3000) score -= 20;
  else if (data.pageLoad.duration > 2000) score -= 10;
  else if (data.pageLoad.duration > 1000) score -= 5;
  
  // TTS API 성능 페널티
  const completedCalls = data.ttsApiCalls.filter(call => call.duration);
  if (completedCalls.length > 0) {
    const avgApiTime = completedCalls.reduce((sum, call) => sum + call.duration, 0) / completedCalls.length;
    if (avgApiTime > 3000) score -= 20;
    else if (avgApiTime > 2000) score -= 10;
    else if (avgApiTime > 1000) score -= 5;
  }
  
  // 메모리 사용량 페널티
  if (data.memoryUsage.length >= 2) {
    const memoryIncrease = data.memoryUsage[data.memoryUsage.length - 1].usedJSHeapSize - data.memoryUsage[0].usedJSHeapSize;
    const memoryIncreaseMB = memoryIncrease / 1024 / 1024;
    if (memoryIncreaseMB > 100) score -= 25;
    else if (memoryIncreaseMB > 50) score -= 15;
    else if (memoryIncreaseMB > 20) score -= 5;
  }
  
  // 오류 페널티
  score -= Math.min(data.errors.length * 2, 30);
  
  // 립싱크 성공 보너스
  if (data.lipSyncFrames.length >= 5) score += 10;
  
  return Math.max(0, Math.min(100, score));
}
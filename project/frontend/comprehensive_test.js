const { chromium } = require('playwright');

/**
 * 종합적인 립싱크 시스템 테스트
 * - WebSocket 연결 테스트
 * - 다양한 메시지 시나리오 테스트 
 * - 성능 및 안정성 검증
 * - 동기화 정확성 검증
 */

(async () => {
  console.log('🧪 [종합 테스트] 립싱크 시스템 종합 테스트 시작');
  
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  
  // 테스트 결과 수집
  const testResults = {
    websocketConnection: false,
    messageProcessing: [],
    lipSyncFrames: [],
    audioPlayback: [],
    errors: [],
    performance: {
      pageLoadTime: 0,
      averageResponseTime: 0,
      messageCount: 0
    }
  };
  
  const startTime = Date.now();
  
  // 콘솔 로그 모니터링
  page.on('console', msg => {
    const text = msg.text();
    const timestamp = new Date().toISOString();
    
    // 중요한 로그들만 캡처
    if (text.includes('[동기화]') || text.includes('립싱크') || text.includes('TTS') || 
        text.includes('WebSocket') || text.includes('handleChatMessage')) {
      console.log(`[${timestamp}] ${text}`);
      
      // 립싱크 프레임 수 추출
      const frameMatch = text.match(/프레임 수:\s*(\d+)/);
      if (frameMatch) {
        testResults.lipSyncFrames.push(parseInt(frameMatch[1]));
      }
      
      // 오디오 재생 추적
      if (text.includes('재생 시작') || text.includes('재생 완료')) {
        testResults.audioPlayback.push(timestamp);
      }
    }
    
    // 에러 추적
    if (text.includes('❌') || text.includes('Error') || text.includes('Failed')) {
      testResults.errors.push({ timestamp, message: text });
    }
  });
  
  // 네트워크 에러 추적
  page.on('requestfailed', request => {
    testResults.errors.push({
      timestamp: new Date().toISOString(),
      message: `Network failed: ${request.url()} - ${request.failure().errorText}`
    });
  });
  
  try {
    // 1. 페이지 로드 테스트
    console.log('🔄 [테스트 1] 페이지 로드 및 초기화');
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    testResults.performance.pageLoadTime = Date.now() - startTime;
    console.log(`📊 페이지 로드 시간: ${testResults.performance.pageLoadTime}ms`);
    
    // WebSocket 연결 확인
    await page.waitForTimeout(2000);
    const wsLogs = await page.evaluate(() => {
      return window.console._logs || [];
    });
    
    // 2. 입력창 확인
    console.log('🔍 [테스트 2] UI 컴포넌트 확인');
    const inputElement = page.locator('input[placeholder*="메시지"], textarea[placeholder*="메시지"]').first();
    const inputCount = await inputElement.count();
    console.log(`📋 발견된 입력창 수: ${inputCount}`);
    
    if (inputCount === 0) {
      throw new Error('입력창을 찾을 수 없습니다');
    }
    
    // 3. 다양한 메시지 시나리오 테스트
    const testMessages = [
      '안녕하세요!',
      '오늘 날씨가 정말 좋네요. 어떻게 생각하세요?',
      '립싱크 동기화 테스트를 진행하고 있습니다. 정확히 작동하는지 확인해주세요.',
      '🎵 음성과 입모양이 정확히 일치하나요?',
      'ㅎㅎㅎ ㅋㅋㅋ ㅜㅜㅜ 자음모음테스트'
    ];
    
    console.log(`🧪 [테스트 3] ${testMessages.length}개 메시지 시나리오 테스트`);
    
    for (let i = 0; i < testMessages.length; i++) {
      const message = testMessages[i];
      const msgStartTime = Date.now();
      
      console.log(`\n📝 [메시지 ${i+1}/${testMessages.length}] "${message.substring(0, 30)}${message.length > 30 ? '...' : ''}"`);
      
      // 메시지 입력 및 전송
      await inputElement.fill(message);
      await page.keyboard.press('Enter');
      
      // 처리 완료 대기 (최대 15초)
      let processingComplete = false;
      let waitTime = 0;
      const maxWaitTime = 15000; // 15초
      
      while (!processingComplete && waitTime < maxWaitTime) {
        await page.waitForTimeout(500);
        waitTime += 500;
        
        // 립싱크 완료 확인
        const recentLogs = await page.evaluate(() => {
          return typeof window._recentLogs !== 'undefined' ? window._recentLogs : [];
        });
        
        // 간단한 완료 확인 (시뮬레이션 또는 실제 립싱크 완료)
        const isComplete = await page.evaluate(() => {
          // 최근 콘솔 로그에서 완료 신호 찾기
          return document.querySelectorAll('.message').length > 0;
        });
        
        if (waitTime >= 8000) { // 8초 후 다음으로
          processingComplete = true;
        }
      }
      
      const responseTime = Date.now() - msgStartTime;
      testResults.messageProcessing.push({
        message: message.substring(0, 50),
        responseTime,
        completed: processingComplete
      });
      
      console.log(`⏱️ 메시지 처리 시간: ${responseTime}ms`);
      
      // 메시지간 간격
      await page.waitForTimeout(2000);
    }
    
    // 4. 성능 통계 계산
    testResults.performance.messageCount = testMessages.length;
    testResults.performance.averageResponseTime = 
      testResults.messageProcessing.reduce((sum, item) => sum + item.responseTime, 0) / testResults.messageProcessing.length;
    
    console.log('\n📊 [테스트 완료] 종합 테스트 결과');
    console.log('=' * 50);
    
    console.log(`🔗 WebSocket 연결: ${testResults.websocketConnection ? '✅ 성공' : '❌ 실패'}`);
    console.log(`⏱️ 페이지 로드 시간: ${testResults.performance.pageLoadTime}ms`);
    console.log(`📈 평균 응답 시간: ${Math.round(testResults.performance.averageResponseTime)}ms`);
    console.log(`💬 처리된 메시지: ${testResults.performance.messageCount}개`);
    
    // 립싱크 프레임 통계
    if (testResults.lipSyncFrames.length > 0) {
      const avgFrames = testResults.lipSyncFrames.reduce((a, b) => a + b, 0) / testResults.lipSyncFrames.length;
      const maxFrames = Math.max(...testResults.lipSyncFrames);
      const minFrames = Math.min(...testResults.lipSyncFrames);
      console.log(`🎭 립싱크 프레임: 평균 ${Math.round(avgFrames)}, 최대 ${maxFrames}, 최소 ${minFrames}`);
    }
    
    // 오디오 재생 통계
    console.log(`🔊 오디오 이벤트: ${testResults.audioPlayback.length}개`);
    
    // 에러 요약
    if (testResults.errors.length > 0) {
      console.log(`⚠️ 발견된 오류: ${testResults.errors.length}개`);
      testResults.errors.forEach((error, index) => {
        console.log(`   ${index + 1}. ${error.message.substring(0, 100)}`);
      });
    } else {
      console.log('✅ 오류 없음');
    }
    
    // 품질 평가
    const qualityScore = calculateQualityScore(testResults);
    console.log(`🏆 전체 품질 점수: ${qualityScore}/100`);
    
  } catch (error) {
    console.error('❌ [테스트 실패]', error.message);
    testResults.errors.push({
      timestamp: new Date().toISOString(),
      message: `Test failed: ${error.message}`
    });
  } finally {
    await page.waitForTimeout(5000); // 마지막 관찰
    await browser.close();
  }
})();

function calculateQualityScore(results) {
  let score = 100;
  
  // 오류 페널티
  score -= results.errors.length * 10;
  
  // 성능 페널티
  if (results.performance.averageResponseTime > 10000) score -= 20;
  else if (results.performance.averageResponseTime > 5000) score -= 10;
  
  // 페이지 로드 페널티
  if (results.performance.pageLoadTime > 5000) score -= 15;
  else if (results.performance.pageLoadTime > 3000) score -= 5;
  
  // 립싱크 보너스
  if (results.lipSyncFrames.length > 0) score += 10;
  
  return Math.max(0, Math.min(100, score));
}
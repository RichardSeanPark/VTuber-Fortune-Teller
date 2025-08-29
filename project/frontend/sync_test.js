const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 콘솔 로그 캡처 (동기화 관련 로그만)
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[동기화]') || text.includes('[WebSocket 전용]') || text.includes('[TTS API 전용]') || 
        text.includes('립싱크') || text.includes('TTS') || text.includes('handleChatMessage')) {
      console.log(`[FRONTEND] ${text}`);
    }
  });
  
  // 페이지 로드
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');
  console.log('[TEST] 페이지 로드 완료');
  
  // 좀 더 넓은 범위로 채팅 입력창 찾기
  await page.waitForTimeout(2000);
  
  const inputs = await page.locator('input, textarea').all();
  console.log(`[TEST] 발견된 입력 요소 수: ${inputs.length}`);
  
  for (let i = 0; i < inputs.length; i++) {
    const placeholder = await inputs[i].getAttribute('placeholder');
    const type = await inputs[i].getAttribute('type');
    console.log(`[TEST] 입력 요소 ${i}: placeholder="${placeholder}", type="${type}"`);
  }
  
  // 입력창이 있다면 테스트 메시지 전송
  if (inputs.length > 0) {
    const chatInput = inputs[0]; // 첫 번째 입력창 사용
    console.log('[TEST] 동기화 테스트 메시지 전송');
    await chatInput.fill('동기화 테스트 메시지');
    await page.keyboard.press('Enter');
    console.log('[TEST] 메시지 전송 완료');
    
    // 동기화 로그 관찰 대기 (20초)
    await page.waitForTimeout(20000);
  } else {
    console.log('[ERROR] 입력창을 찾을 수 없음');
  }
  
  await browser.close();
})();
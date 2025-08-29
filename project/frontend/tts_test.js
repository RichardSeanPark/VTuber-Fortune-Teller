const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 콘솔 로그 캡처
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('[TTS') || text.includes('[립싱크') || text.includes('[Live2D')) {
      console.log(`[BROWSER] ${text}`);
    }
  });
  
  // 페이지 로드
  await page.goto('http://localhost:3002');
  await page.waitForLoadState('networkidle');
  
  console.log('[TEST] 페이지 로드 완료');
  
  // 채팅 입력창 찾기
  const chatInput = await page.locator('input[placeholder*="메시지"], textarea[placeholder*="메시지"], input[type="text"]').first();
  
  if (await chatInput.count() > 0) {
    console.log('[TEST] 채팅 입력창 발견, 테스트 메시지 입력');
    await chatInput.fill('안녕하세요! 입모양 테스트를 해보겠습니다.');
    
    // 전송 버튼 또는 엔터키
    await page.keyboard.press('Enter');
    console.log('[TEST] 메시지 전송 완료');
    
    // TTS 처리 대기 (15초)
    await page.waitForTimeout(15000);
  } else {
    console.log('[ERROR] 채팅 입력창을 찾을 수 없음');
  }
  
  await browser.close();
})();

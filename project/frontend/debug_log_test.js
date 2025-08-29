const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 강력한 캐시 비활성화
  await page.setExtraHTTPHeaders({ 
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  });
  
  // 모든 콘솔 로그 캡처
  page.on('console', msg => {
    const text = msg.text();
    console.log(`[BROWSER] ${text}`);
  });
  
  // 페이지 로드
  const timestamp = Date.now();
  await page.goto(`http://localhost:3000?bust=${timestamp}`);
  await page.waitForLoadState('networkidle');
  console.log('[TEST] 페이지 로드 완료');
  
  // WebSocket 연결 대기
  await page.waitForTimeout(3000);
  
  // 채팅 입력창 찾기 및 메시지 전송
  const chatInput = await page.locator('input[placeholder*="메시지"], textarea[placeholder*="메시지"], input[type="text"]').first();
  
  if (await chatInput.count() > 0) {
    console.log('[TEST] 채팅 입력창 발견, 디버깅 로그 확인을 위한 메시지 전송');
    await chatInput.fill('안녕! 디버깅 로그 테스트');
    await page.keyboard.press('Enter');
    console.log('[TEST] 메시지 전송 완료');
    
    // 디버깅 로그 및 립싱크 처리 대기
    await page.waitForTimeout(15000);
  } else {
    console.log('[ERROR] 채팅 입력창을 찾을 수 없음');
  }
  
  await browser.close();
})();
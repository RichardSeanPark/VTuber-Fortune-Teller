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
  
  // 캐시 비활성화
  await page.setExtraHTTPHeaders({ 'Cache-Control': 'no-cache' });
  
  // 콘솔 로그 캡처 - 디버깅 로그 확인
  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('🔍 [디버깅]') || text.includes('🎤 [TTS API') || text.includes('[TTS') || text.includes('handleChatMessage')) {
      console.log(`[FRONTEND DEBUG] ${text}`);
    }
  });
  
  // 페이지 로드 (타임스탬프로 캐시 우회)
  const timestamp = Date.now();
  await page.goto(`http://localhost:3000?bust=${timestamp}&v=${timestamp}`);
  await page.waitForLoadState('networkidle');
  
  console.log('[TEST] 페이지 로드 완료 (강력한 캐시 우회)');
  
  // 강제 새로고침
  await page.keyboard.down('Control');
  await page.keyboard.down('Shift');
  await page.keyboard.press('R');
  await page.keyboard.up('Shift');
  await page.keyboard.up('Control');
  await page.waitForLoadState('networkidle');
  console.log('[TEST] 강제 새로고침 완료 (Ctrl+Shift+R)');
  
  // 채팅 입력창 찾기
  const chatInput = await page.locator('input[placeholder*="메시지"], textarea[placeholder*="메시지"], input[type="text"]').first();
  
  if (await chatInput.count() > 0) {
    console.log('[TEST] 채팅 입력창 발견, 디버깅 로그 확인을 위한 테스트 메시지 입력');
    await chatInput.fill('디버깅 로그 테스트 - handleChatMessage 실행 확인');
    
    // 전송 버튼 또는 엔터키
    await page.keyboard.press('Enter');
    console.log('[TEST] 메시지 전송 완료 - 디버깅 로그 출력 대기');
    
    // 디버깅 로그 출력 대기 (30초)
    await page.waitForTimeout(30000);
  } else {
    console.log('[ERROR] 채팅 입력창을 찾을 수 없음');
  }
  
  await browser.close();
})();
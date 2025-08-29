const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  // 모든 콘솔 로그 캡처
  page.on('console', msg => {
    console.log(`[BROWSER] ${msg.text()}`);
  });
  
  // 에러 캡처
  page.on('pageerror', error => {
    console.log(`[PAGE ERROR] ${error}`);
  });
  
  // 네트워크 실패 캡처
  page.on('requestfailed', request => {
    console.log(`[NETWORK FAILED] ${request.url()} - ${request.failure().errorText}`);
  });
  
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');
  
  // DOM 구조 확인
  const title = await page.title();
  console.log(`[TEST] 페이지 제목: ${title}`);
  
  const bodyContent = await page.locator('body').textContent();
  console.log(`[TEST] 바디 콘텐츠 길이: ${bodyContent.length}`);
  console.log(`[TEST] 바디 콘텐츠 미리보기: ${bodyContent.substring(0, 200)}...`);
  
  // React 앱 root 확인
  const appRoot = await page.locator('#root').count();
  console.log(`[TEST] React root 요소 수: ${appRoot}`);
  
  if (appRoot > 0) {
    const rootContent = await page.locator('#root').textContent();
    console.log(`[TEST] Root 콘텐츠: ${rootContent.substring(0, 300)}...`);
  }
  
  // 10초 대기 후 종료
  await page.waitForTimeout(10000);
  await browser.close();
})();
/**
 * 전체 테스트 실행 스크립트
 * WebSocket 기반 립싱크 데이터 전달 시스템 종합 테스트
 */
const { exec } = require('child_process');
const path = require('path');

console.log('🧪 [종합 테스트] WebSocket 기반 립싱크 데이터 전달 시스템 테스트 시작\n');
console.log('=' .repeat(70));
console.log('📋 테스트 순서:');
console.log('  Step 1: WebSocket 연결 및 초기화');
console.log('  Step 2: 백엔드 립싱크 데이터 생성');
console.log('  Step 3: WebSocket 메시지 전달 흐름');
console.log('  Step 4: 프론트엔드 립싱크 처리');
console.log('=' .repeat(70) + '\n');

// 테스트 파일들
const testFiles = [
    'test_step1_websocket.js',
    'test_step2_backend_lipsync.js',
    'test_step3_message_flow.js',
    'test_step4_frontend_lipsync.js'
];

// 테스트 실행 함수
function runTest(testFile) {
    return new Promise((resolve, reject) => {
        const testPath = path.join(__dirname, testFile);
        exec(`node "${testPath}"`, (error, stdout, stderr) => {
            if (error) {
                reject({ file: testFile, error: error.message, stderr });
            } else {
                resolve({ file: testFile, stdout, stderr });
            }
        });
    });
}

// 순차적 테스트 실행
async function runAllTests() {
    const results = {
        passed: 0,
        failed: 0,
        details: []
    };

    for (const testFile of testFiles) {
        try {
            console.log(`⏳ ${testFile} 실행 중...`);
            const startTime = Date.now();
            
            const result = await runTest(testFile);
            const duration = Date.now() - startTime;
            
            console.log(`✅ ${testFile} 완료 (${duration}ms)`);
            console.log(result.stdout);
            
            if (result.stderr && result.stderr.trim()) {
                console.log(`⚠️ 경고 출력:`);
                console.log(result.stderr);
            }
            
            results.passed++;
            results.details.push({
                file: testFile,
                status: 'passed',
                duration,
                output: result.stdout
            });
            
            console.log('-'.repeat(50) + '\n');
            
        } catch (error) {
            console.error(`❌ ${testFile} 실패:`);
            console.error(error.error);
            
            if (error.stderr) {
                console.error('에러 출력:', error.stderr);
            }
            
            results.failed++;
            results.details.push({
                file: error.file,
                status: 'failed',
                error: error.error,
                stderr: error.stderr
            });
            
            console.log('-'.repeat(50) + '\n');
        }
    }

    // 최종 결과 출력
    console.log('🏁 [테스트 완료] 종합 결과\n');
    console.log('=' .repeat(70));
    console.log(`📊 전체 테스트: ${testFiles.length}개`);
    console.log(`✅ 성공: ${results.passed}개`);
    console.log(`❌ 실패: ${results.failed}개`);
    console.log('=' .repeat(70) + '\n');

    // 개별 테스트 결과 요약
    results.details.forEach((detail, index) => {
        const stepNum = index + 1;
        const status = detail.status === 'passed' ? '✅' : '❌';
        console.log(`${status} Step ${stepNum}: ${detail.file} - ${detail.status.toUpperCase()}`);
        
        if (detail.duration) {
            console.log(`   실행 시간: ${detail.duration}ms`);
        }
        
        if (detail.error) {
            console.log(`   에러: ${detail.error}`);
        }
    });

    console.log('\n' + '=' .repeat(70));
    
    if (results.failed === 0) {
        console.log('🎉 모든 테스트가 성공적으로 완료되었습니다!');
        console.log('✅ WebSocket 기반 립싱크 데이터 전달 시스템이 올바르게 작동합니다.');
    } else {
        console.log(`⚠️ ${results.failed}개의 테스트가 실패했습니다.`);
        console.log('🔧 실패한 테스트를 확인하고 문제를 해결해주세요.');
    }
    
    console.log('\n📝 테스트 실행 완료 시각:', new Date().toLocaleString());
    console.log('=' .repeat(70));
}

// 테스트 실행
runAllTests().catch(console.error);
#!/usr/bin/env python3
"""
정확한 Duration 측정 시스템 종합 테스트
librosa 기반 오디오 분석과 TTS duration 비교 검증
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fortune_vtuber.tts.live2d_tts_manager import Live2DTTSManager, Live2DTTSRequest
from fortune_vtuber.tts.tts_interface import EmotionType

# 로깅 설정 - 모든 상세 로그 출력
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_duration_accuracy():
    """Duration 정확성 종합 테스트"""
    
    print("\n" + "="*80)
    print("🧪 Duration 정확성 종합 테스트 시작")
    print("="*80)
    
    # Live2D TTS Manager 초기화
    manager = Live2DTTSManager()
    
    # 테스트할 텍스트들 (다양한 길이)
    test_texts = [
        "안녕하세요",
        "춤은 좋다. 하지만 지금은 점술 일을 하고 있으니까요.",
        "오늘 날씨가 정말 좋네요. 산책하기 딱 좋은 날씨입니다. 어떻게 생각하시나요?",
        "가나다라마바사아자차카타파하. 한글 발음 테스트를 위한 긴 문장입니다. 모음과 자음이 골고루 들어있어야 정확한 테스트가 가능합니다."
    ]
    
    test_results = []
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 테스트 {i}/{len(test_texts)}: '{text[:30]}{'...' if len(text) > 30 else ''}'")
        print("-" * 60)
        
        try:
            # TTS 요청 생성
            request = Live2DTTSRequest(
                text=text,
                user_id="test_user",
                session_id="test_session",
                language="ko",
                voice="female",
                emotion=EmotionType.NEUTRAL,
                speed=1.0,
                pitch=1.0,
                volume=1.0,
                enable_lipsync=True,
                enable_expressions=False,
                enable_motions=False
            )
            
            print(f"🔄 TTS 생성 요청 중...")
            
            # TTS 생성 실행
            result = await manager.generate_speech_with_animation(request)
            
            if result.success and result.audio_data and result.lip_sync_data:
                print(f"✅ TTS 생성 성공")
                
                # 결과 분석
                tts_duration = result.duration
                lip_sync_duration = result.lip_sync_data.duration
                frame_count = len(result.lip_sync_data.mouth_shapes)
                frame_rate = result.lip_sync_data.frame_rate
                calculated_duration = frame_count / frame_rate
                
                # 분석 결과 출력
                print(f"\n📊 분석 결과:")
                print(f"  🎵 TTS 제공 duration: {tts_duration:.6f}초")
                print(f"  🔍 librosa 측정 duration: {lip_sync_duration:.6f}초")
                print(f"  📊 생성된 프레임 수: {frame_count}개")
                print(f"  ⏱️ 프레임 레이트: {frame_rate} fps")
                print(f"  🧮 계산된 재생 시간: {calculated_duration:.6f}초")
                
                # 차이 계산
                tts_vs_librosa_diff = abs(tts_duration - lip_sync_duration)
                tts_vs_librosa_percent = (tts_vs_librosa_diff / max(lip_sync_duration, 0.001)) * 100
                
                librosa_vs_calculated_diff = abs(lip_sync_duration - calculated_duration)
                librosa_vs_calculated_percent = (librosa_vs_calculated_diff / max(calculated_duration, 0.001)) * 100
                
                print(f"\n⚖️ 정확도 분석:")
                print(f"  📈 TTS vs librosa 차이: {tts_vs_librosa_diff:.6f}초 ({tts_vs_librosa_percent:.2f}%)")
                print(f"  📈 librosa vs 계산값 차이: {librosa_vs_calculated_diff:.6f}초 ({librosa_vs_calculated_percent:.2f}%)")
                
                # 정확도 판정
                accuracy_status = "✅ 매우 정확" if tts_vs_librosa_percent < 5 else "⚠️ 부정확" if tts_vs_librosa_percent < 20 else "❌ 매우 부정확"
                frame_accuracy = "✅ 일치" if librosa_vs_calculated_percent < 0.1 else "⚠️ 약간 차이" if librosa_vs_calculated_percent < 1 else "❌ 큰 차이"
                
                print(f"  🎯 TTS duration 정확도: {accuracy_status}")
                print(f"  🎯 프레임 생성 정확도: {frame_accuracy}")
                
                # 오디오 데이터 분석
                audio_size_mb = len(result.audio_data) / (1024 * 1024)
                print(f"\n📦 오디오 데이터:")
                print(f"  📏 크기: {len(result.audio_data):,} bytes ({audio_size_mb:.2f} MB)")
                print(f"  🎵 형식: {result.audio_format}")
                
                # 결과 저장
                test_results.append({
                    'text': text,
                    'text_length': len(text),
                    'tts_duration': tts_duration,
                    'librosa_duration': lip_sync_duration,
                    'frame_count': frame_count,
                    'frame_rate': frame_rate,
                    'calculated_duration': calculated_duration,
                    'tts_vs_librosa_diff_percent': tts_vs_librosa_percent,
                    'librosa_vs_calculated_diff_percent': librosa_vs_calculated_percent,
                    'audio_size_bytes': len(result.audio_data),
                    'success': True
                })
                
            else:
                print(f"❌ TTS 생성 실패: {result.error_message if hasattr(result, 'error_message') else '알 수 없는 오류'}")
                test_results.append({
                    'text': text,
                    'success': False,
                    'error': result.error_message if hasattr(result, 'error_message') else '알 수 없는 오류'
                })
                
        except Exception as e:
            print(f"❌ 테스트 {i} 실패: {e}")
            logger.exception(f"테스트 {i} 예외 발생:")
            test_results.append({
                'text': text,
                'success': False,
                'error': str(e)
            })
    
    # 종합 결과 분석
    print("\n" + "="*80)
    print("📈 종합 테스트 결과 분석")
    print("="*80)
    
    successful_tests = [r for r in test_results if r.get('success', False)]
    failed_tests = [r for r in test_results if not r.get('success', False)]
    
    print(f"✅ 성공한 테스트: {len(successful_tests)}/{len(test_results)}개")
    print(f"❌ 실패한 테스트: {len(failed_tests)}/{len(test_results)}개")
    
    if successful_tests:
        print(f"\n📊 성공한 테스트 통계:")
        
        # TTS vs librosa 차이 분석
        tts_diffs = [r['tts_vs_librosa_diff_percent'] for r in successful_tests]
        avg_tts_diff = sum(tts_diffs) / len(tts_diffs)
        max_tts_diff = max(tts_diffs)
        min_tts_diff = min(tts_diffs)
        
        print(f"  🎯 TTS duration 정확도:")
        print(f"    - 평균 차이: {avg_tts_diff:.2f}%")
        print(f"    - 최대 차이: {max_tts_diff:.2f}%")
        print(f"    - 최소 차이: {min_tts_diff:.2f}%")
        
        # 프레임 생성 정확도 분석
        frame_diffs = [r['librosa_vs_calculated_diff_percent'] for r in successful_tests]
        avg_frame_diff = sum(frame_diffs) / len(frame_diffs)
        max_frame_diff = max(frame_diffs)
        min_frame_diff = min(frame_diffs)
        
        print(f"  🎬 프레임 생성 정확도:")
        print(f"    - 평균 차이: {avg_frame_diff:.4f}%")
        print(f"    - 최대 차이: {max_frame_diff:.4f}%")
        print(f"    - 최소 차이: {min_frame_diff:.4f}%")
        
        # 텍스트 길이별 분석
        print(f"\n📝 텍스트 길이별 분석:")
        for r in successful_tests:
            accuracy_icon = "✅" if r['tts_vs_librosa_diff_percent'] < 10 else "⚠️" if r['tts_vs_librosa_diff_percent'] < 30 else "❌"
            print(f"    {accuracy_icon} 길이 {r['text_length']:2d}자: TTS차이 {r['tts_vs_librosa_diff_percent']:5.1f}%, 프레임차이 {r['librosa_vs_calculated_diff_percent']:6.3f}%")
    
    if failed_tests:
        print(f"\n❌ 실패한 테스트:")
        for i, r in enumerate(failed_tests, 1):
            print(f"  {i}. '{r['text'][:50]}{'...' if len(r['text']) > 50 else ''}' - {r.get('error', '알 수 없는 오류')}")
    
    # 최종 결론
    print(f"\n" + "="*80)
    print("🎯 최종 결론")
    print("="*80)
    
    if successful_tests:
        avg_accuracy = sum(r['tts_vs_librosa_diff_percent'] for r in successful_tests) / len(successful_tests)
        frame_accuracy = sum(r['librosa_vs_calculated_diff_percent'] for r in successful_tests) / len(successful_tests)
        
        if avg_accuracy < 10 and frame_accuracy < 0.1:
            print("✅ 매우 성공적! librosa 기반 duration 측정이 TTS보다 훨씬 정확합니다.")
        elif avg_accuracy < 30 and frame_accuracy < 1:
            print("⚠️ 부분 성공. librosa duration이 TTS보다 정확하지만 개선 여지가 있습니다.")
        else:
            print("❌ 개선 필요. duration 측정에 문제가 있을 수 있습니다.")
            
        print(f"📊 전체 평균 TTS duration 부정확도: {avg_accuracy:.2f}%")
        print(f"🎬 전체 평균 프레임 생성 정확도: {frame_accuracy:.4f}%")
    else:
        print("❌ 모든 테스트가 실패했습니다. 시스템 점검이 필요합니다.")

if __name__ == "__main__":
    print("🚀 정확한 Duration 측정 시스템 테스트 시작...")
    asyncio.run(test_duration_accuracy())
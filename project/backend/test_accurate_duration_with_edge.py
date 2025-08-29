#!/usr/bin/env python3
"""
정확한 Duration 측정 시스템 종합 테스트 (Edge TTS 사용)
librosa 기반 오디오 분석과 TTS duration 비교 검증
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
import base64

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fortune_vtuber.tts.providers.edge_tts import EdgeTTSProvider
from fortune_vtuber.tts.tts_interface import TTSProviderConfig, TTSCostType, TTSQuality, TTSRequest
from fortune_vtuber.tts.live2d_tts_manager import Live2DTTSManager

# 로깅 설정 - 모든 상세 로그 출력
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_duration_accuracy_with_edge():
    """Edge TTS를 사용한 Duration 정확성 종합 테스트"""
    
    print("\n" + "="*80)
    print("🧪 Duration 정확성 종합 테스트 시작 (Edge TTS)")
    print("="*80)
    
    # Edge TTS Provider 직접 초기화
    print("🔧 Edge TTS Provider 초기화...")
    config = TTSProviderConfig(
        provider_id="edge_tts",
        name="EdgeTTS",
        cost_type=TTSCostType.FREE,
        quality=TTSQuality.HIGH,
        supported_languages=["ko-KR"],
        supported_voices={
            "ko-KR": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"]
        },
        default_voice="ko-KR-SunHiNeural",
        api_required=False,
        max_text_length=5000,
        rate_limit_per_minute=60
    )
    edge_provider = EdgeTTSProvider(config)
    
    # Live2DTTSManager 초기화
    manager = Live2DTTSManager()
    
    # 테스트할 텍스트들 (다양한 길이)
    test_texts = [
        "안녕하세요",
        "춤은 좋다. 하지만 지금은 점술 일을 하고 있으니까요.",
        "오늘 날씨가 정말 좋네요. 산책하기 딱 좋은 날씨입니다.",
        "가나다라마바사아자차카타파하. 한글 발음 테스트 문장입니다."
    ]
    
    test_results = []
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n📝 테스트 {i}/{len(test_texts)}: '{text[:30]}{'...' if len(text) > 30 else ''}'")
        print("-" * 60)
        
        try:
            # TTS 요청 생성 (emotion을 None으로 설정)
            tts_request = TTSRequest(
                text=text,
                language="ko-KR",
                voice="ko-KR-SunHiNeural",
                emotion=None,  # None으로 설정하여 에러 방지
                speed=1.0,
                pitch=1.0,
                volume=1.0,
                enable_lipsync=True
            )
            
            print(f"🔄 Edge TTS 생성 요청 중...")
            
            # Edge TTS로 오디오 생성
            edge_result = await edge_provider.async_generate_audio(tts_request)
            
            if edge_result.audio_data:  # TTSResult에는 success 속성이 없으므로 audio_data로 확인
                print(f"✅ Edge TTS 생성 성공")
                
                # 1. Edge TTS가 제공한 duration
                edge_duration = edge_result.duration
                edge_audio_size = len(edge_result.audio_data)
                
                print(f"📊 Edge TTS 결과:")
                print(f"  🎵 Edge 제공 duration: {edge_duration:.6f}초")
                print(f"  📦 오디오 크기: {edge_audio_size:,} bytes ({edge_audio_size/1024/1024:.2f} MB)")
                print(f"  🎵 오디오 형식: {edge_result.audio_format}")
                
                # 2. librosa로 정확한 duration 측정
                print(f"\n🔍 librosa 분석 시작...")
                try:
                    actual_duration = manager._get_accurate_audio_duration(
                        edge_result.audio_data, 
                        edge_result.audio_format
                    )
                    print(f"✅ librosa 분석 완료")
                except Exception as librosa_error:
                    print(f"❌ librosa 분석 실패: {librosa_error}")
                    continue
                
                # 3. 립싱크 데이터 생성 테스트
                print(f"\n🎭 립싱크 데이터 생성 테스트...")
                try:
                    lipsync_data = manager._create_basic_lipsync_data_with_audio_analysis(
                        text, edge_result.audio_data, edge_result.audio_format, edge_duration
                    )
                    print(f"✅ 립싱크 데이터 생성 완료")
                    
                    # 4. 상세 분석
                    frame_count = len(lipsync_data.mouth_shapes)
                    frame_rate = lipsync_data.frame_rate
                    calculated_duration = frame_count / frame_rate
                    
                    print(f"\n📊 상세 분석 결과:")
                    print(f"  🎵 Edge 제공 duration: {edge_duration:.6f}초")
                    print(f"  🔍 librosa 측정 duration: {actual_duration:.6f}초")
                    print(f"  🎭 립싱크 duration: {lipsync_data.duration:.6f}초")
                    print(f"  📊 생성된 프레임 수: {frame_count}개")
                    print(f"  ⏱️ 프레임 레이트: {frame_rate} fps")
                    print(f"  🧮 계산된 재생 시간: {calculated_duration:.6f}초")
                    
                    # 5. 차이 분석
                    edge_vs_librosa_diff = abs(edge_duration - actual_duration)
                    edge_vs_librosa_percent = (edge_vs_librosa_diff / max(actual_duration, 0.001)) * 100
                    
                    librosa_vs_lipsync_diff = abs(actual_duration - lipsync_data.duration)
                    librosa_vs_lipsync_percent = (librosa_vs_lipsync_diff / max(lipsync_data.duration, 0.001)) * 100
                    
                    lipsync_vs_calculated_diff = abs(lipsync_data.duration - calculated_duration)
                    lipsync_vs_calculated_percent = (lipsync_vs_calculated_diff / max(calculated_duration, 0.001)) * 100
                    
                    print(f"\n⚖️ 정확도 분석:")
                    print(f"  📈 Edge vs librosa 차이: {edge_vs_librosa_diff:.6f}초 ({edge_vs_librosa_percent:.2f}%)")
                    print(f"  📈 librosa vs 립싱크 차이: {librosa_vs_lipsync_diff:.6f}초 ({librosa_vs_lipsync_percent:.2f}%)")
                    print(f"  📈 립싱크 vs 계산값 차이: {lipsync_vs_calculated_diff:.6f}초 ({lipsync_vs_calculated_percent:.2f}%)")
                    
                    # 6. 정확도 판정
                    edge_accuracy = "✅ 매우 정확" if edge_vs_librosa_percent < 5 else "⚠️ 부정확" if edge_vs_librosa_percent < 20 else "❌ 매우 부정확"
                    lipsync_accuracy = "✅ 완벽" if librosa_vs_lipsync_percent < 0.1 else "⚠️ 약간 차이" if librosa_vs_lipsync_percent < 1 else "❌ 큰 차이"
                    frame_accuracy = "✅ 완벽" if lipsync_vs_calculated_percent < 0.1 else "⚠️ 약간 차이" if lipsync_vs_calculated_percent < 1 else "❌ 큰 차이"
                    
                    print(f"  🎯 Edge TTS duration 정확도: {edge_accuracy}")
                    print(f"  🎯 립싱크 duration 정확도: {lipsync_accuracy}")
                    print(f"  🎯 프레임 생성 정확도: {frame_accuracy}")
                    
                    # 7. 첫 5개, 마지막 5개 프레임 검증
                    print(f"\n🎬 프레임 샘플 검증:")
                    for j in range(min(3, frame_count)):
                        timestamp, params = lipsync_data.mouth_shapes[j]
                        print(f"  📊 프레임 {j:3d}: 시간={timestamp:.3f}s, 입열림={params.get('ParamMouthOpenY', 0):.3f}")
                    
                    if frame_count > 6:
                        print(f"  ... ({frame_count-6}개 프레임 생략) ...")
                        for j in range(max(0, frame_count-3), frame_count):
                            timestamp, params = lipsync_data.mouth_shapes[j]
                            print(f"  📊 프레임 {j:3d}: 시간={timestamp:.3f}s, 입열림={params.get('ParamMouthOpenY', 0):.3f}")
                    
                    # 결과 저장
                    test_results.append({
                        'text': text,
                        'text_length': len(text),
                        'edge_duration': edge_duration,
                        'librosa_duration': actual_duration,
                        'lipsync_duration': lipsync_data.duration,
                        'frame_count': frame_count,
                        'frame_rate': frame_rate,
                        'calculated_duration': calculated_duration,
                        'edge_vs_librosa_diff_percent': edge_vs_librosa_percent,
                        'librosa_vs_lipsync_diff_percent': librosa_vs_lipsync_percent,
                        'lipsync_vs_calculated_diff_percent': lipsync_vs_calculated_percent,
                        'audio_size_bytes': edge_audio_size,
                        'success': True
                    })
                    
                except Exception as lipsync_error:
                    print(f"❌ 립싱크 생성 실패: {lipsync_error}")
                    logger.exception("립싱크 생성 예외:")
                    test_results.append({
                        'text': text,
                        'success': False,
                        'error': f"립싱크 생성 실패: {lipsync_error}"
                    })
                    
            else:
                print(f"❌ Edge TTS 생성 실패: {edge_result.error_message if hasattr(edge_result, 'error_message') else '알 수 없는 오류'}")
                test_results.append({
                    'text': text,
                    'success': False,
                    'error': f"Edge TTS 생성 실패: {edge_result.error_message if hasattr(edge_result, 'error_message') else '알 수 없는 오류'}"
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
        
        # Edge vs librosa 차이 분석
        edge_diffs = [r['edge_vs_librosa_diff_percent'] for r in successful_tests]
        avg_edge_diff = sum(edge_diffs) / len(edge_diffs)
        max_edge_diff = max(edge_diffs)
        min_edge_diff = min(edge_diffs)
        
        print(f"  🎯 Edge TTS duration 정확도:")
        print(f"    - 평균 차이: {avg_edge_diff:.2f}%")
        print(f"    - 최대 차이: {max_edge_diff:.2f}%")
        print(f"    - 최소 차이: {min_edge_diff:.2f}%")
        
        # librosa vs 립싱크 차이 분석
        lipsync_diffs = [r['librosa_vs_lipsync_diff_percent'] for r in successful_tests]
        avg_lipsync_diff = sum(lipsync_diffs) / len(lipsync_diffs)
        max_lipsync_diff = max(lipsync_diffs)
        min_lipsync_diff = min(lipsync_diffs)
        
        print(f"  🎭 립싱크 duration 정확도:")
        print(f"    - 평균 차이: {avg_lipsync_diff:.4f}%")
        print(f"    - 최대 차이: {max_lipsync_diff:.4f}%")
        print(f"    - 최소 차이: {min_lipsync_diff:.4f}%")
        
        # 프레임 생성 정확도 분석
        frame_diffs = [r['lipsync_vs_calculated_diff_percent'] for r in successful_tests]
        avg_frame_diff = sum(frame_diffs) / len(frame_diffs)
        max_frame_diff = max(frame_diffs)
        min_frame_diff = min(frame_diffs)
        
        print(f"  🎬 프레임 생성 정확도:")
        print(f"    - 평균 차이: {avg_frame_diff:.6f}%")
        print(f"    - 최대 차이: {max_frame_diff:.6f}%")
        print(f"    - 최소 차이: {min_frame_diff:.6f}%")
        
        # 텍스트 길이별 상세 분석
        print(f"\n📝 텍스트 길이별 상세 분석:")
        for r in successful_tests:
            edge_icon = "✅" if r['edge_vs_librosa_diff_percent'] < 10 else "⚠️" if r['edge_vs_librosa_diff_percent'] < 30 else "❌"
            lipsync_icon = "✅" if r['librosa_vs_lipsync_diff_percent'] < 1 else "⚠️" if r['librosa_vs_lipsync_diff_percent'] < 5 else "❌"
            frame_icon = "✅" if r['lipsync_vs_calculated_diff_percent'] < 0.1 else "⚠️" if r['lipsync_vs_calculated_diff_percent'] < 1 else "❌"
            
            print(f"    길이 {r['text_length']:2d}자: Edge차이{edge_icon}{r['edge_vs_librosa_diff_percent']:5.1f}%, 립싱크차이{lipsync_icon}{r['librosa_vs_lipsync_diff_percent']:6.3f}%, 프레임차이{frame_icon}{r['lipsync_vs_calculated_diff_percent']:7.4f}%")
            print(f"              Edge={r['edge_duration']:.3f}s, librosa={r['librosa_duration']:.3f}s, 프레임={r['frame_count']}개")
    
    if failed_tests:
        print(f"\n❌ 실패한 테스트:")
        for i, r in enumerate(failed_tests, 1):
            print(f"  {i}. '{r['text'][:50]}{'...' if len(r['text']) > 50 else ''}' - {r.get('error', '알 수 없는 오류')}")
    
    # 최종 결론
    print(f"\n" + "="*80)
    print("🎯 최종 결론")
    print("="*80)
    
    if successful_tests:
        avg_edge_accuracy = sum(r['edge_vs_librosa_diff_percent'] for r in successful_tests) / len(successful_tests)
        avg_lipsync_accuracy = sum(r['librosa_vs_lipsync_diff_percent'] for r in successful_tests) / len(successful_tests)
        avg_frame_accuracy = sum(r['lipsync_vs_calculated_diff_percent'] for r in successful_tests) / len(successful_tests)
        
        print(f"📊 전체 평균 정확도:")
        print(f"  📈 Edge TTS vs librosa: {avg_edge_accuracy:.2f}% 차이")
        print(f"  🎭 librosa vs 립싱크: {avg_lipsync_accuracy:.4f}% 차이")
        print(f"  🎬 프레임 생성 정확도: {avg_frame_accuracy:.6f}% 차이")
        
        if avg_edge_accuracy > 20:
            print("⚠️ Edge TTS의 duration이 상당히 부정확합니다. librosa 기반 측정이 필요합니다!")
        elif avg_edge_accuracy > 10:
            print("⚠️ Edge TTS의 duration이 부정확합니다. librosa 보정이 도움이 됩니다.")
        else:
            print("✅ Edge TTS의 duration이 비교적 정확합니다.")
            
        if avg_lipsync_accuracy < 0.1 and avg_frame_accuracy < 0.1:
            print("✅ librosa 기반 립싱크 데이터 생성이 매우 정확합니다!")
        elif avg_lipsync_accuracy < 1 and avg_frame_accuracy < 1:
            print("✅ librosa 기반 립싱크 데이터 생성이 정확합니다.")
        else:
            print("⚠️ 립싱크 데이터 생성에 개선이 필요할 수 있습니다.")
    else:
        print("❌ 모든 테스트가 실패했습니다. 시스템 점검이 필요합니다.")

if __name__ == "__main__":
    print("🚀 정확한 Duration 측정 시스템 테스트 시작 (Edge TTS)...")
    asyncio.run(test_duration_accuracy_with_edge())
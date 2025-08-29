#!/usr/bin/env python3
"""
프론트엔드용 립싱크 테스트
실제 프론트엔드에서 사용하는 것처럼 테스트
"""

import requests
import json
import time

def test_frontend_compatible_lipsync():
    """프론트엔드 호환 립싱크 테스트"""
    print("🎭 [프론트엔드 립싱크 호환성 테스트]")
    print("=" * 60)
    
    url = "http://127.0.0.1:8001/api/v1/tts/generate"
    
    # 실제 프론트엔드에서 사용할 만한 한글 텍스트들
    test_texts = [
        "안녕하세요, 반갑습니다!",
        "오늘 날씨가 정말 좋네요.",
        "립싱크가 잘 작동하고 있나요?",
        "아이우에오 발음 테스트입니다."
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n🔬 테스트 {i+1}: '{text}'")
        print("-" * 40)
        
        test_data = {
            "text": text,
            "user_id": "frontend_user",
            "session_id": f"frontend_test_{i}",
            "language": "ko-KR",
            "enable_lipsync": True,
            "enable_expressions": True,
            "enable_motions": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(url, json=test_data, timeout=20)
            end_time = time.time()
            
            print(f"⏱️ 응답 시간: {end_time - start_time:.2f}초")
            print(f"📊 HTTP 상태: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("data", {})
                
                # 립싱크 데이터 검증
                lip_sync = data.get("lip_sync", [])
                
                if lip_sync and len(lip_sync) > 0:
                    print(f"✅ 립싱크 데이터: {len(lip_sync)}개 프레임")
                    
                    # 첫 번째와 마지막 프레임 확인
                    first_frame = lip_sync[0]
                    last_frame = lip_sync[-1]
                    
                    print(f"🎯 첫 프레임: 시간={first_frame[0]:.3f}s, ParamMouthOpenY={first_frame[1]['ParamMouthOpenY']:.3f}")
                    print(f"🏁 마지막 프레임: 시간={last_frame[0]:.3f}s, ParamMouthOpenY={last_frame[1]['ParamMouthOpenY']:.3f}")
                    
                    # 입 열림 범위 분석
                    mouth_values = [frame[1]['ParamMouthOpenY'] for frame in lip_sync]
                    min_val = min(mouth_values)
                    max_val = max(mouth_values)
                    avg_val = sum(mouth_values) / len(mouth_values)
                    
                    print(f"📈 입 열림 범위: {min_val:.3f} ~ {max_val:.3f} (평균: {avg_val:.3f})")
                    
                    # 동적 움직임 확인
                    variations = sum(1 for j in range(1, len(mouth_values)) 
                                   if abs(mouth_values[j] - mouth_values[j-1]) > 0.05)
                    variation_rate = variations / len(mouth_values) * 100
                    
                    print(f"🌊 동적 변화: {variation_rate:.1f}% (움직임 있는 프레임)")
                    
                    if variation_rate > 30:
                        print("✅ 충분한 립싱크 애니메이션!")
                    else:
                        print("⚠️ 움직임이 적음 - 정적일 수 있음")
                        
                else:
                    print("❌ 립싱크 데이터 없음!")
                
                # 오디오 정보
                print(f"🎵 오디오: {data.get('duration', 0):.1f}초, {data.get('provider_used', 'unknown')} 사용")
                
            else:
                print(f"❌ 요청 실패: {response.status_code}")
                print(f"📄 오류 내용: {response.text[:200]}")
                
        except Exception as e:
            print(f"🚨 오류 발생: {e}")
    
    print(f"\n{'=' * 60}")
    print("🎊 프론트엔드 립싱크 호환성 테스트 완료!")
    print("💡 이제 브라우저에서 실제로 립싱크가 작동하는지 확인하세요.")

if __name__ == "__main__":
    test_frontend_compatible_lipsync()
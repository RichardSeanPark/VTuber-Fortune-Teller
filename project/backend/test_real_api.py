#!/usr/bin/env python3
"""
실제 사용되는 TTS API 테스트
/api/v1/tts/generate 엔드포인트로 테스트
"""

import requests
import json
import time

def test_real_tts_api():
    """실제 TTS API 테스트"""
    print("🎯 [실제 TTS API 테스트] /api/v1/tts/generate")
    print("=" * 60)
    
    url = "http://127.0.0.1:8001/api/v1/tts/generate"
    
    test_data = {
        "text": "안녕하세요. 립싱크 데이터가 제대로 생성되는지 테스트합니다.",
        "user_id": "test_user",
        "session_id": "debug_session",
        "language": "ko-KR",
        "voice": None,
        "emotion": None,
        "speed": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "enable_lipsync": True,
        "enable_expressions": True,
        "enable_motions": True,
        "provider_override": None
    }
    
    print(f"📤 요청 데이터: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    print("=" * 60)
    
    try:
        start_time = time.time()
        response = requests.post(url, json=test_data, timeout=30)
        end_time = time.time()
        
        print(f"📊 HTTP 상태: {response.status_code}")
        print(f"⏱️ 응답 시간: {end_time - start_time:.2f}초")
        
        if response.status_code == 200:
            try:
                result = response.json()
                
                print("\n📋 API 응답 구조:")
                print(f"  success: {result.get('success')}")
                print(f"  data 키들: {list(result.get('data', {}).keys())}")
                
                data = result.get("data", {})
                
                # 오디오 관련
                print(f"\n🎵 오디오 정보:")
                print(f"  duration: {data.get('duration')}초")
                print(f"  audio_format: {data.get('audio_format')}")
                print(f"  provider_used: {data.get('provider_used')}")
                print(f"  cached: {data.get('cached')}")
                
                # 립싱크 관련 - 새로운 형식
                print(f"\n👄 립싱크 정보:")
                lip_sync = data.get("lip_sync", [])
                lipsync_data = data.get("lipsync_data", {})
                
                print(f"  lip_sync (프론트엔드용): {type(lip_sync)}, 길이: {len(lip_sync) if isinstance(lip_sync, list) else 'N/A'}")
                print(f"  lipsync_data (메타데이터): {lipsync_data}")
                
                if isinstance(lip_sync, list) and len(lip_sync) > 0:
                    print(f"  첫 번째 요소: {lip_sync[0]}")
                    print(f"  ✅ 립싱크 데이터 존재!")
                    
                    # 데이터 구조 검증
                    first = lip_sync[0]
                    if isinstance(first, list) and len(first) == 2:
                        timestamp, params = first
                        if isinstance(params, dict) and "ParamMouthOpenY" in params:
                            print(f"  ✅ 데이터 구조 올바름: timestamp={timestamp}, ParamMouthOpenY={params['ParamMouthOpenY']}")
                        else:
                            print(f"  ❌ 파라미터 구조 문제: {params}")
                    else:
                        print(f"  ❌ 립싱크 요소 구조 문제: {first}")
                else:
                    print(f"  ❌ 립싱크 데이터가 없음!")
                
                # Live2D 관련
                print(f"\n🎭 Live2D 정보:")
                print(f"  live2d_commands: {len(data.get('live2d_commands', []))}개")
                print(f"  expressions: {len(data.get('expressions', []))}개")
                print(f"  motions: {len(data.get('motions', []))}개")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 파싱 실패: {e}")
                print(f"📄 응답 내용: {response.text[:500]}")
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"📄 응답 내용: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("⏰ 요청 타임아웃")
    except requests.exceptions.ConnectionError:
        print("🔌 연결 실패")
    except Exception as e:
        print(f"🚨 예상치 못한 오류: {e}")

if __name__ == "__main__":
    test_real_tts_api()
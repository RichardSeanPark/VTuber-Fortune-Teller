#!/usr/bin/env python3
"""
립싱크 디버깅 테스트 스크립트
- 한글 텍스트로 TTS API 호출
- 상세 로그를 통한 립싱크 데이터 생성 과정 추적
- 프론트엔드 호환 데이터 구조 검증
"""

import requests
import json
import time
import sys

class LipSyncDebugTest:
    def __init__(self):
        self.backend_url = "http://127.0.0.1:8001"
        
    def test_korean_lipsync(self):
        """한글 텍스트로 립싱크 테스트"""
        print("🎤 [한글 립싱크 테스트] 시작")
        print("=" * 60)
        
        test_cases = [
            "안녕하세요",
            "오늘 날씨가 좋네요",
            "립싱크가 제대로 작동하고 있는지 확인해보겠습니다"
        ]
        
        for i, text in enumerate(test_cases):
            print(f"\n🔍 테스트 케이스 {i+1}: '{text}'")
            print("-" * 40)
            
            try:
                # TTS API 호출
                response = requests.post(
                    f"{self.backend_url}/api/live2d/tts/synthesize",
                    json={
                        "text": text,
                        "voice": "ko-KR-SunHiNeural",
                        "emotion": "neutral",
                        "language": "ko-KR",
                        "session_id": f"debug_test_{i}",
                        "enable_lipsync": True
                    },
                    timeout=30
                )
                
                print(f"📊 HTTP 응답: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 기본 구조 검증
                    success = result.get("success", False)
                    data = result.get("data", {})
                    
                    print(f"✅ 성공 여부: {success}")
                    print(f"🔧 데이터 키들: {list(data.keys())}")
                    
                    # 오디오 데이터 확인
                    has_audio = "audio_data" in data and data["audio_data"]
                    print(f"🎵 오디오 데이터 존재: {has_audio}")
                    
                    if has_audio:
                        audio_length = len(data["audio_data"]) if data["audio_data"] else 0
                        print(f"🎵 오디오 데이터 크기: {audio_length} 문자")
                    
                    # 립싱크 데이터 확인
                    has_lipsync = "lip_sync" in data and data["lip_sync"]
                    print(f"👄 립싱크 데이터 존재: {has_lipsync}")
                    
                    if has_lipsync:
                        lip_sync_data = data["lip_sync"]
                        print(f"👄 립싱크 데이터 타입: {type(lip_sync_data)}")
                        print(f"👄 립싱크 데이터 크기: {len(lip_sync_data) if isinstance(lip_sync_data, list) else 'N/A'}")
                        
                        if isinstance(lip_sync_data, list) and len(lip_sync_data) > 0:
                            # 첫 번째 프레임 분석
                            first_frame = lip_sync_data[0]
                            print(f"👄 첫 번째 프레임: {first_frame}")
                            
                            if isinstance(first_frame, list) and len(first_frame) >= 2:
                                timestamp = first_frame[0]
                                params = first_frame[1]
                                print(f"👄 첫 프레임 - 시간: {timestamp}, 파라미터: {params}")
                                
                                # ParamMouthOpenY 확인
                                if isinstance(params, dict) and "ParamMouthOpenY" in params:
                                    mouth_open = params["ParamMouthOpenY"]
                                    print(f"👄 입 열림 값: {mouth_open}")
                                    
                                    if 0.0 <= mouth_open <= 1.0:
                                        print("✅ 립싱크 데이터 구조가 올바릅니다!")
                                    else:
                                        print(f"❌ 입 열림 값이 범위를 벗어남: {mouth_open}")
                                else:
                                    print("❌ ParamMouthOpenY 파라미터가 없습니다!")
                            else:
                                print("❌ 립싱크 프레임 구조가 올바르지 않습니다!")
                        else:
                            print("❌ 립싱크 데이터가 비어있거나 리스트가 아닙니다!")
                    else:
                        print("❌ 립싱크 데이터가 없습니다!")
                        
                        # 가능한 오류 원인 분석
                        if "error" in result:
                            print(f"🚨 오류 메시지: {result['error']}")
                        
                        # 메타데이터 확인
                        if "metadata" in result:
                            metadata = result["metadata"]
                            print(f"📋 메타데이터: {metadata}")
                
                else:
                    print(f"❌ HTTP 오류: {response.status_code}")
                    print(f"📄 응답 내용: {response.text[:500]}")
                    
            except requests.exceptions.Timeout:
                print("⏰ 요청 타임아웃 - 30초 초과")
            except requests.exceptions.ConnectionError:
                print("🔌 연결 오류 - 백엔드 서버 확인 필요")
            except Exception as e:
                print(f"🚨 예상치 못한 오류: {e}")
                
            print(f"\n{'=' * 60}\n")
            time.sleep(1)  # 각 테스트 간 간격
    
    def test_live2d_endpoint_direct(self):
        """Live2D 엔드포인트 직접 테스트"""
        print("🎭 [Live2D 엔드포인트 직접 테스트]")
        print("=" * 60)
        
        endpoints_to_test = [
            "/api/live2d/status",
            "/api/live2d/health"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                print(f"🔍 {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    success = result.get("success", False)
                    print(f"✅ 성공: {success}")
                    
                    if "data" in result:
                        data = result["data"]
                        print(f"📊 데이터 키들: {list(data.keys())}")
                else:
                    print(f"❌ 실패: {response.text[:200]}")
                    
            except Exception as e:
                print(f"🚨 오류: {e}")
                
            print("-" * 40)

    def run_complete_debug(self):
        """전체 디버깅 테스트 실행"""
        print("🔧 립싱크 디버깅 테스트 시작")
        print(f"📅 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔗 백엔드 URL: {self.backend_url}")
        print("\n" + "=" * 80)
        
        # 1. Live2D 시스템 상태 확인
        self.test_live2d_endpoint_direct()
        
        print("\n" + "=" * 80)
        
        # 2. 한글 TTS 립싱크 테스트
        self.test_korean_lipsync()
        
        print("🎯 테스트 완료!")
        print("\n💡 다음 단계:")
        print("1. 백엔드 로그에서 [립싱크 디버깅] 메시지 확인")
        print("2. 오디오 데이터는 있는데 립싱크가 없다면 lipsync_analyzer 문제")
        print("3. 두 데이터 모두 없다면 TTS 프로바이더 문제")
        print("4. 데이터는 있는데 구조가 다르다면 데이터 변환 문제")

def main():
    """메인 함수"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("📚 립싱크 디버깅 테스트 도구")
        print("\n사용법:")
        print("  python test_lipsync_debug.py          # 전체 테스트")
        print("  python test_lipsync_debug.py --help   # 도움말")
        print("\n🎯 목적:")
        print("  - TTS API에서 립싱크 데이터가 생성되는지 확인")
        print("  - 한글 텍스트 처리 과정 디버깅")
        print("  - 프론트엔드 호환 데이터 구조 검증")
        return 0
    
    tester = LipSyncDebugTest()
    tester.run_complete_debug()
    return 0

if __name__ == "__main__":
    exit(main())
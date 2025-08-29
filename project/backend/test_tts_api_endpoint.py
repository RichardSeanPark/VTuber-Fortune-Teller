#!/usr/bin/env python3
"""
TTS API 엔드포인트 테스트

실제 TTS API를 호출하여 numpy 직렬화 수정이 제대로 작동하는지 확인
"""

import asyncio
import httpx
import json
import sys
import os

async def test_tts_synthesize_endpoint():
    """TTS synthesize 엔드포인트 테스트"""
    print("=== TTS Synthesize 엔드포인트 테스트 ===")
    
    url = "http://localhost:8000/api/v1/live2d/tts/synthesize"
    test_data = {
        "session_id": "test_session_123",
        "text": "안녕하세요! 오늘의 운세를 확인해보세요.",
        "emotion": "happy",
        "language": "ko-KR",
        "enable_lipsync": True
    }
    
    print(f"요청 URL: {url}")
    print(f"요청 데이터: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=test_data)
            
            print(f"\n응답 상태 코드: {response.status_code}")
            print(f"응답 헤더: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"\n✅ JSON 파싱 성공!")
                    print(f"응답 구조: {list(response_data.keys())}")
                    
                    if "data" in response_data:
                        data = response_data["data"]
                        print(f"데이터 구조: {list(data.keys())}")
                        
                        # numpy 타입 관련 필드들 확인
                        numpy_sensitive_fields = ["duration", "generation_time"]
                        for field in numpy_sensitive_fields:
                            if field in data:
                                value = data[field]
                                print(f"  {field}: {value} (타입: {type(value)})")
                        
                        # lip_sync 데이터 확인
                        if "lip_sync" in data and data["lip_sync"]:
                            lip_sync = data["lip_sync"]
                            print(f"  lip_sync 구조: {list(lip_sync.keys())}")
                            
                            if "total_duration" in lip_sync:
                                duration = lip_sync["total_duration"]
                                print(f"  lip_sync.total_duration: {duration} (타입: {type(duration)})")
                    
                    print("\n🎉 TTS API 호출 및 JSON 직렬화 성공!")
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON 파싱 실패: {e}")
                    print(f"응답 내용: {response.text[:500]}...")
                    return False
            else:
                print(f"\n❌ HTTP 오류: {response.status_code}")
                print(f"응답 내용: {response.text}")
                return False
                
    except Exception as e:
        print(f"\n❌ 요청 실행 중 오류: {e}")
        return False

async def test_tts_generate_endpoint():
    """TTS generate 엔드포인트 테스트"""
    print("\n=== TTS Generate 엔드포인트 테스트 ===")
    
    url = "http://localhost:8000/api/v1/tts/generate"
    test_data = {
        "text": "테스트 음성 합성입니다.",
        "user_id": "test_user",
        "language": "ko-KR",
        "enable_lipsync": True,
        "enable_expressions": True,
        "enable_motions": True,
        "emotion": "calm"
    }
    
    print(f"요청 URL: {url}")
    print(f"요청 데이터: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=test_data)
            
            print(f"\n응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    print(f"\n✅ JSON 파싱 성공!")
                    
                    if "data" in response_data:
                        data = response_data["data"]
                        print(f"데이터 구조: {list(data.keys())}")
                        
                        # numpy 타입 확인
                        numpy_fields = ["duration", "generation_time"]
                        for field in numpy_fields:
                            if field in data:
                                value = data[field]
                                print(f"  {field}: {value} (타입: {type(value)})")
                        
                        # Live2D 관련 데이터 확인
                        live2d_fields = ["live2d_commands", "expressions", "motions"]
                        for field in live2d_fields:
                            if field in data and data[field]:
                                print(f"  {field}: {len(data[field])} 항목")
                    
                    print("\n🎉 TTS Generate API 호출 및 JSON 직렬화 성공!")
                    return True
                    
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON 파싱 실패: {e}")
                    print(f"응답 내용: {response.text[:500]}...")
                    return False
            else:
                print(f"\n❌ HTTP 오류: {response.status_code}")
                print(f"응답 내용: {response.text}")
                return False
                
    except Exception as e:
        print(f"\n❌ 요청 실행 중 오류: {e}")
        return False

async def main():
    """메인 테스트 함수"""
    print("TTS API 엔드포인트 테스트")
    print("=" * 50)
    
    # 서버가 실행중인지 확인
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:8000/health")
            if response.status_code != 200:
                print("❌ 서버가 실행되고 있지 않습니다.")
                print("서버를 먼저 실행해주세요: python run_server.py")
                return False
    except Exception:
        print("❌ 서버에 연결할 수 없습니다.")
        print("서버를 먼저 실행해주세요: python run_server.py")
        return False
    
    print("✅ 서버 연결 확인됨")
    
    # 테스트 실행
    tests = [
        ("TTS Synthesize", test_tts_synthesize_endpoint),
        ("TTS Generate", test_tts_generate_endpoint)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n테스트 '{test_name}' 실행 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약:")
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
        all_passed = all_passed and passed
    
    if all_passed:
        print("\n🎉 모든 API 테스트가 성공했습니다!")
        print("numpy.float32 직렬화 문제가 완전히 해결되었습니다.")
    else:
        print("\n⚠️  일부 API 테스트가 실패했습니다.")
        print("서버 로그를 확인해주세요.")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
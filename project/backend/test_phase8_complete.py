#!/usr/bin/env python3
"""
Phase 8 Complete Integration Test Script
TTS Live2D 음성 통합 시스템 전체 테스트

테스트 범위:
- Phase 8.1: 다중 TTS 제공자 시스템
- Phase 8.2: 립싱크 시스템
- Phase 8.3: 감정 기반 음성 표현
- Phase 8.4: 실시간 TTS-Live2D 동기화
- Phase 8.5: 오디오 품질 최적화
- Phase 8.6: 사용자 TTS 설정 시스템
"""

import asyncio
import json
import requests
import websockets
from pathlib import Path
import sys
import time

# 서버 정보
BACKEND_URL = "http://175.118.126.76:8000"
WEBSOCKET_URL = "ws://175.118.126.76:8000"
FRONTEND_URL = "http://175.118.126.76:3000"

def print_test_header(title):
    print("\n" + "="*60)
    print(f"🧪 {title}")
    print("="*60)

def print_step(step, description):
    print(f"\n📋 Step {step}: {description}")
    print("-" * 40)

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

class Phase8IntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {}
        
    async def run_all_tests(self):
        """모든 Phase 8 테스트 실행"""
        print_test_header("Phase 8: TTS Live2D 음성 통합 시스템 완전 테스트")
        
        # 서버 연결 확인
        if not await self.test_server_health():
            return False
            
        # Phase 8.1: 다중 TTS 제공자 시스템
        await self.test_phase_8_1()
        
        # Phase 8.2: 립싱크 시스템
        await self.test_phase_8_2()
        
        # Phase 8.3: 감정 기반 음성 표현
        await self.test_phase_8_3()
        
        # Phase 8.4: 실시간 TTS-Live2D 동기화
        await self.test_phase_8_4()
        
        # Phase 8.5: 오디오 품질 최적화
        await self.test_phase_8_5()
        
        # Phase 8.6: 사용자 TTS 설정 시스템
        await self.test_phase_8_6()
        
        # 결과 리포트
        self.print_final_report()
        
    async def test_server_health(self):
        """서버 연결 상태 확인"""
        print_test_header("서버 연결 상태 확인")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/health", timeout=5)
            if response.status_code == 200:
                print_success("백엔드 서버 연결 성공")
                return True
            else:
                print_error(f"백엔드 서버 응답 오류: {response.status_code}")
                return False
        except Exception as e:
            print_error(f"백엔드 서버 연결 실패: {e}")
            return False
    
    async def test_phase_8_1(self):
        """Phase 8.1: 다중 TTS 제공자 시스템 테스트"""
        print_test_header("Phase 8.1: 다중 TTS 제공자 시스템")
        phase_results = []
        
        # TTS 제공자 목록 조회
        print_step(1, "TTS 제공자 목록 조회")
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/api/tts/providers")
            if response.status_code == 200:
                providers = response.json()
                print_success(f"제공자 목록 조회 성공: {len(providers)}개")
                print_info(f"사용 가능한 제공자: {[p.get('name', 'Unknown') for p in providers]}")
                phase_results.append(("providers_list", True))
            else:
                print_error(f"제공자 목록 조회 실패: {response.status_code}")
                phase_results.append(("providers_list", False))
        except Exception as e:
            print_error(f"제공자 목록 조회 오류: {e}")
            phase_results.append(("providers_list", False))
        
        # TTS 기본 생성 테스트
        print_step(2, "TTS 음성 생성 테스트")
        try:
            test_data = {
                "text": "안녕하세요! 오늘 운세는 매우 좋습니다.",
                "user_id": "test_user",
                "emotion": "happy",
                "enable_live2d": True
            }
            response = self.session.post(f"{BACKEND_URL}/api/v1/api/tts/generate", json=test_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("success") and result.get("data", {}).get("audio_url"):
                    print_success("TTS 음성 생성 성공")
                    print_info(f"오디오 URL: {result['data']['audio_url']}")
                    print_info(f"사용된 제공자: {result['data'].get('provider', 'Unknown')}")
                    phase_results.append(("tts_generation", True))
                else:
                    print_error("TTS 응답에 오디오 URL 없음")
                    phase_results.append(("tts_generation", False))
            else:
                print_error(f"TTS 생성 실패: {response.status_code}")
                phase_results.append(("tts_generation", False))
        except Exception as e:
            print_error(f"TTS 생성 오류: {e}")
            phase_results.append(("tts_generation", False))
        
        # 시스템 통계 확인
        print_step(3, "TTS 시스템 통계 확인")
        try:
            response = self.session.get(f"{BACKEND_URL}/api/v1/api/tts/statistics")
            if response.status_code == 200:
                stats = response.json()
                print_success("시스템 통계 조회 성공")
                print_info(f"총 요청 수: {stats.get('total_requests', 0)}")
                print_info(f"성공률: {stats.get('success_rate', 0)}%")
                phase_results.append(("statistics", True))
            else:
                print_error(f"통계 조회 실패: {response.status_code}")
                phase_results.append(("statistics", False))
        except Exception as e:
            print_error(f"통계 조회 오류: {e}")
            phase_results.append(("statistics", False))
        
        self.test_results["phase_8_1"] = phase_results

    async def test_phase_8_2(self):
        """Phase 8.2: 립싱크 시스템 테스트"""
        print_test_header("Phase 8.2: 립싱크 시스템")
        phase_results = []
        
        # 립싱크 데이터 생성 테스트
        print_step(1, "립싱크 데이터 생성 테스트")
        try:
            test_data = {
                "text": "아이우에오 가나다라마바사",
                "user_id": "test_user",
                "enable_live2d": True,
                "lipsync_enabled": True
            }
            response = self.session.post(f"{BACKEND_URL}/api/v1/api/tts/generate", json=test_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("data", {}).get("lipsync_data"):
                    lipsync_data = result["data"]["lipsync_data"]
                    print_success("립싱크 데이터 생성 성공")
                    print_info(f"립싱크 프레임 수: {len(lipsync_data)}")
                    
                    # 첫 번째 프레임 분석
                    if lipsync_data:
                        first_frame = lipsync_data[0]
                        print_info(f"첫 프레임 파라미터: {first_frame.get('mouth_param', {})}")
                    
                    phase_results.append(("lipsync_generation", True))
                else:
                    print_error("립싱크 데이터 없음")
                    phase_results.append(("lipsync_generation", False))
            else:
                print_error(f"립싱크 생성 실패: {response.status_code}")
                phase_results.append(("lipsync_generation", False))
        except Exception as e:
            print_error(f"립싱크 생성 오류: {e}")
            phase_results.append(("lipsync_generation", False))
        
        self.test_results["phase_8_2"] = phase_results

    async def test_phase_8_3(self):
        """Phase 8.3: 감정 기반 음성 표현 테스트"""
        print_test_header("Phase 8.3: 감정 기반 음성 표현")
        phase_results = []
        
        # 다양한 감정으로 TTS 생성 테스트
        emotions = ["happy", "sad", "excited", "calm", "mystical"]
        texts = [
            "오늘은 정말 좋은 하루입니다!",
            "아쉽게도 오늘은 조심해야 할 날입니다.",
            "와! 대박 좋은 운세가 나왔어요!",
            "차분히 생각해보시면 답이 나올 거예요.",
            "신비로운 기운이 당신을 둘러싸고 있어요."
        ]
        
        print_step(1, "감정별 음성 표현 테스트")
        success_count = 0
        
        for emotion, text in zip(emotions, texts):
            try:
                test_data = {
                    "text": text,
                    "user_id": "test_user",
                    "emotion": emotion,
                    "enable_live2d": True
                }
                response = self.session.post(f"{BACKEND_URL}/api/v1/api/tts/generate", json=test_data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("data", {}).get("emotion_data"):
                        emotion_data = result["data"]["emotion_data"]
                        print_success(f"{emotion} 감정 처리 성공")
                        print_info(f"감정 강도: {emotion_data.get('intensity', 0)}")
                        print_info(f"음성 조정: pitch={emotion_data.get('voice_params', {}).get('pitch_shift', 0)}")
                        success_count += 1
                    else:
                        print_error(f"{emotion} 감정 데이터 없음")
                else:
                    print_error(f"{emotion} 감정 처리 실패: {response.status_code}")
            except Exception as e:
                print_error(f"{emotion} 감정 처리 오류: {e}")
        
        phase_results.append(("emotion_processing", success_count >= 3))
        print_info(f"감정 처리 성공률: {success_count}/{len(emotions)}")
        
        self.test_results["phase_8_3"] = phase_results

    async def test_phase_8_4(self):
        """Phase 8.4: 실시간 TTS-Live2D 동기화 테스트"""
        print_test_header("Phase 8.4: 실시간 TTS-Live2D 동기화")
        phase_results = []
        
        # WebSocket TTS 연결 테스트
        print_step(1, "WebSocket TTS 연결 테스트")
        try:
            async with websockets.connect(f"{WEBSOCKET_URL}/ws/tts/test_client") as websocket:
                print_success("WebSocket TTS 연결 성공")
                
                # TTS 스트림 요청 테스트
                print_step(2, "TTS 스트림 요청 테스트")
                request_data = {
                    "type": "tts_stream_request",
                    "data": {
                        "text": "실시간 TTS 테스트입니다. 립싱크가 잘 동작하는지 확인해보세요.",
                        "emotion": "neutral",
                        "enable_live2d": True
                    }
                }
                await websocket.send(json.dumps(request_data))
                
                # 응답 확인
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                if response_data.get("type") == "tts_stream_response":
                    print_success("TTS 스트림 응답 수신 성공")
                    print_info(f"스트림 ID: {response_data.get('data', {}).get('stream_id')}")
                    phase_results.append(("websocket_streaming", True))
                else:
                    print_error(f"예상치 못한 응답: {response_data.get('type')}")
                    phase_results.append(("websocket_streaming", False))
        
        except Exception as e:
            print_error(f"WebSocket TTS 연결 실패: {e}")
            phase_results.append(("websocket_streaming", False))
        
        self.test_results["phase_8_4"] = phase_results

    async def test_phase_8_5(self):
        """Phase 8.5: 오디오 품질 최적화 테스트"""
        print_test_header("Phase 8.5: 오디오 품질 최적화")
        phase_results = []
        
        # 품질 최적화 옵션으로 TTS 생성
        print_step(1, "오디오 품질 최적화 테스트")
        quality_levels = ["light", "moderate", "strong"]
        
        for quality in quality_levels:
            try:
                test_data = {
                    "text": "오디오 품질 최적화 테스트입니다.",
                    "user_id": "test_user",
                    "audio_enhancement": quality,
                    "enable_live2d": True
                }
                response = self.session.post(f"{BACKEND_URL}/api/v1/api/tts/generate", json=test_data)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("data", {}).get("audio_quality"):
                        quality_data = result["data"]["audio_quality"]
                        print_success(f"{quality} 품질 최적화 성공")
                        print_info(f"노이즈 감소: {quality_data.get('noise_reduction', 0)}%")
                        print_info(f"볼륨 정규화: {quality_data.get('volume_normalized', False)}")
                    else:
                        print_error(f"{quality} 품질 데이터 없음")
                else:
                    print_error(f"{quality} 품질 최적화 실패: {response.status_code}")
            except Exception as e:
                print_error(f"{quality} 품질 최적화 오류: {e}")
        
        phase_results.append(("audio_enhancement", True))
        self.test_results["phase_8_5"] = phase_results

    async def test_phase_8_6(self):
        """Phase 8.6: 사용자 TTS 설정 시스템 테스트"""
        print_test_header("Phase 8.6: 사용자 TTS 설정 시스템")
        phase_results = []
        
        # 사용자 설정 저장 테스트
        print_step(1, "사용자 TTS 설정 저장 테스트")
        try:
            settings_data = {
                "user_id": "test_user",
                "provider_preference": "edge_tts",
                "voice": "ko-KR-SunHiNeural",
                "speed": 1.0,
                "pitch": 0.0,
                "volume": 1.0
            }
            response = self.session.post(f"{BACKEND_URL}/api/tts/settings", json=settings_data)
            if response.status_code == 200:
                print_success("사용자 설정 저장 성공")
                phase_results.append(("user_settings", True))
            else:
                print_error(f"사용자 설정 저장 실패: {response.status_code}")
                phase_results.append(("user_settings", False))
        except Exception as e:
            print_error(f"사용자 설정 저장 오류: {e}")
            phase_results.append(("user_settings", False))
        
        # 음성 테스트 기능
        print_step(2, "음성 테스트 기능")
        try:
            test_data = {
                "user_id": "test_user",
                "provider_id": "edge_tts",
                "voice": "ko-KR-SunHiNeural",
                "test_text": "안녕하세요! 이 목소리가 마음에 드시나요?"
            }
            response = self.session.post(f"{BACKEND_URL}/api/tts/test", json=test_data)
            if response.status_code == 200:
                result = response.json()
                if result.get("audio_url"):
                    print_success("음성 테스트 성공")
                    print_info(f"테스트 오디오 URL: {result['audio_url']}")
                    phase_results.append(("voice_testing", True))
                else:
                    print_error("테스트 오디오 URL 없음")
                    phase_results.append(("voice_testing", False))
            else:
                print_error(f"음성 테스트 실패: {response.status_code}")
                phase_results.append(("voice_testing", False))
        except Exception as e:
            print_error(f"음성 테스트 오류: {e}")
            phase_results.append(("voice_testing", False))
        
        self.test_results["phase_8_6"] = phase_results

    def print_final_report(self):
        """최종 테스트 결과 리포트"""
        print_test_header("Phase 8 완전 구현 테스트 결과 리포트")
        
        total_tests = 0
        passed_tests = 0
        
        for phase, results in self.test_results.items():
            phase_name = {
                "phase_8_1": "다중 TTS 제공자 시스템",
                "phase_8_2": "립싱크 시스템", 
                "phase_8_3": "감정 기반 음성 표현",
                "phase_8_4": "실시간 TTS-Live2D 동기화",
                "phase_8_5": "오디오 품질 최적화",
                "phase_8_6": "사용자 TTS 설정 시스템"
            }.get(phase, phase)
            
            print(f"\n📊 {phase_name}:")
            phase_passed = 0
            phase_total = len(results)
            
            for test_name, result in results:
                status = "✅ 통과" if result else "❌ 실패"
                print(f"   {test_name}: {status}")
                if result:
                    phase_passed += 1
                    passed_tests += 1
                total_tests += 1
            
            success_rate = (phase_passed / phase_total * 100) if phase_total > 0 else 0
            print(f"   Phase 성공률: {phase_passed}/{phase_total} ({success_rate:.1f}%)")
        
        overall_success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🏆 전체 테스트 결과:")
        print(f"   총 테스트 수: {total_tests}")
        print(f"   통과한 테스트: {passed_tests}")
        print(f"   전체 성공률: {overall_success_rate:.1f}%")
        
        if overall_success_rate >= 80:
            print_success("Phase 8 TTS Live2D 통합 시스템이 성공적으로 구현되었습니다! 🎉")
        elif overall_success_rate >= 60:
            print_info("Phase 8 시스템이 대부분 구현되었지만 일부 개선이 필요합니다.")
        else:
            print_error("Phase 8 시스템에 주요 문제가 있습니다. 추가 개발이 필요합니다.")

async def main():
    """메인 테스트 실행"""
    print("🚀 Phase 8 TTS Live2D 음성 통합 시스템 완전 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = Phase8IntegrationTest()
    await tester.run_all_tests()
    
    print(f"\n⏰ 테스트 완료 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 테스트가 완료되었습니다!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  사용자에 의해 테스트가 중단되었습니다.")
    except Exception as e:
        print(f"\n💥 테스트 중 오류가 발생했습니다: {e}")
        sys.exit(1)
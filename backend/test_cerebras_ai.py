#!/usr/bin/env python3
"""
Cerebras AI 통합 테스트 스크립트
모든 Cerebras AI 기능을 독립적으로 테스트합니다.
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.fortune_vtuber.config.cerebras_config import (
    get_cerebras_config, 
    is_cerebras_enabled, 
    validate_cerebras_config,
    cerebras_settings
)
from src.fortune_vtuber.fortune.cerebras_engine import (
    CerebrasFortuneEngine,
    CerebrasDailyFortuneEngine,
    CerebrasTarotFortuneEngine,
    CerebrasZodiacFortuneEngine,
    CerebrasSajuFortuneEngine
)
from src.fortune_vtuber.models.fortune import FortuneType
# UserData 클래스를 간단하게 정의
class UserData:
    def __init__(self, user_id: str, name: str, birth_date: str, gender: str):
        self.user_id = user_id
        self.name = name
        self.birth_date = birth_date
        self.gender = gender

async def test_cerebras_config():
    """Cerebras 설정 테스트"""
    print("🔧 Cerebras AI 설정 테스트")
    print("=" * 50)
    
    # 환경변수 확인
    print("📝 환경변수 확인:")
    print(f"  ENABLE_CEREBRAS: {os.getenv('ENABLE_CEREBRAS')}")
    print(f"  CEREBRAS_API_KEY: {'설정됨' if os.getenv('CEREBRAS_API_KEY') else '없음'}")
    print(f"  CEREBRAS_MODEL: {os.getenv('CEREBRAS_MODEL')}")
    print(f"  CEREBRAS_MAX_TOKENS: {os.getenv('CEREBRAS_MAX_TOKENS')}")
    print(f"  CEREBRAS_TEMPERATURE: {os.getenv('CEREBRAS_TEMPERATURE')}")
    print(f"  CEREBRAS_TIMEOUT: {os.getenv('CEREBRAS_TIMEOUT')}")
    print()
    
    # Cerebras 활성화 상태 확인
    enabled = is_cerebras_enabled()
    print(f"✅ Cerebras 활성화 상태: {enabled}")
    
    # 설정 유효성 검사
    is_valid, message = validate_cerebras_config()
    print(f"{'✅' if is_valid else '❌'} 설정 유효성: {message}")
    
    # Cerebras 설정 객체 확인
    config = get_cerebras_config()
    if config:
        print(f"✅ Cerebras 설정 생성 성공")
        print(f"  모델: {config.model}")
        print(f"  최대 토큰: {config.max_tokens}")
        print(f"  온도: {config.temperature}")
        print(f"  타임아웃: {config.timeout}초")
        print(f"  사용가능 모델: {config.available_models}")
    else:
        print("❌ Cerebras 설정 생성 실패")
    
    print()
    return enabled and is_valid and config is not None

async def test_cerebras_api_connection():
    """Cerebras API 연결 테스트"""
    print("🌐 Cerebras API 연결 테스트")
    print("=" * 50)
    
    config = get_cerebras_config()
    if not config:
        print("❌ Cerebras 설정이 없어 API 테스트를 건너뜁니다.")
        return False
    
    try:
        # 기본 엔진으로 간단한 요청 테스트
        engine = CerebrasFortuneEngine(config)
        
        # 테스트용 사용자 데이터
        user_data = UserData(
            user_id="test_user",
            name="테스트 사용자",
            birth_date="1990-01-01",
            gender="male"
        )
        
        print("📡 API 연결 테스트 중...")
        
        # PersonalizationContext를 사용해 실제 운세 생성 테스트
        from src.fortune_vtuber.fortune.engines import PersonalizationContext
        from datetime import date
        
        context = PersonalizationContext(
            birth_date=date(1990, 5, 15),
            preferences={"name": "테스트 사용자"}
        )
        
        result = await engine.generate_fortune(context)
        
        if result:
            print(f"✅ API 연결 성공!")
            print(f"  운세 ID: {result.fortune_id}")
            print(f"  운세 타입: {result.fortune_type}")
            print(f"  조언: {result.advice[:100] if result.advice else '없음'}{'...' if result.advice and len(result.advice) > 100 else ''}")
            print(f"  Live2D 감정: {getattr(result, 'live2d_emotion', '없음')}")
            print(f"  Live2D 모션: {getattr(result, 'live2d_motion', '없음')}")
            return True
        else:
            print("❌ API에서 빈 응답을 받았습니다.")
            return False
            
    except Exception as e:
        print(f"❌ API 연결 실패: {str(e)}")
        
        # 모델 fallback 테스트
        if "model_not_found" in str(e) or "404" in str(e):
            print("🔄 모델 fallback 테스트 중...")
            try:
                engine = CerebrasFortuneEngine(config)
                # fallback 로직이 작동하는지 확인
                fallback_prompt = FortunePrompt(
                    system_prompt="당신은 친근한 AI 조수입니다.",
                    user_prompt="안녕하세요.",
                    context_data={}
                )
                result = await engine._call_cerebras_api(fallback_prompt)
                if result:
                    print("✅ Fallback 모델로 연결 성공!")
                    return True
            except Exception as fallback_error:
                print(f"❌ Fallback 모델도 실패: {str(fallback_error)}")
        
        return False

async def test_fortune_engines():
    """각 운세 엔진별 테스트"""
    print("🎯 운세 엔진별 기능 테스트")
    print("=" * 50)
    
    config = get_cerebras_config()
    if not config:
        print("❌ Cerebras 설정이 없어 엔진 테스트를 건너뜁니다.")
        return False
    
    # 테스트용 사용자 데이터
    user_data = UserData(
        user_id="test_user",
        name="김철수",
        birth_date="1990-05-15",
        gender="male"
    )
    
    engines_to_test = [
        ("일일운세", CerebrasDailyFortuneEngine, FortuneType.DAILY, {}),
        ("타로", CerebrasTarotFortuneEngine, FortuneType.TAROT, {}),
        ("별자리", CerebrasZodiacFortuneEngine, FortuneType.ZODIAC, {"zodiac_sign": "황소자리"}),
        ("사주", CerebrasSajuFortuneEngine, FortuneType.ORIENTAL, {})
    ]
    
    results = {}
    
    for name, engine_class, fortune_type, additional_params in engines_to_test:
        print(f"🎭 {name} 엔진 테스트...")
        
        try:
            engine = engine_class(config)
            
            # PersonalizationContext 생성
            from src.fortune_vtuber.fortune.engines import PersonalizationContext
            from datetime import datetime
            birth_date_obj = datetime.strptime(user_data.birth_date, "%Y-%m-%d").date()
            
            context = PersonalizationContext(
                birth_date=birth_date_obj,
                preferences={"name": user_data.name}
            )
            
            result = await engine.generate_fortune(
                context=context,
                additional_params=additional_params
            )
            
            if result:
                print(f"✅ {name} 생성 성공!")
                print(f"  운세 ID: {result.fortune_id}")
                print(f"  운세 타입: {result.fortune_type}")
                print(f"  조언: {result.advice[:100] if result.advice else '없음'}{'...' if result.advice and len(result.advice) > 100 else ''}")
                print(f"  Live2D 감정: {getattr(result, 'live2d_emotion', '없음')}")
                print(f"  Live2D 모션: {getattr(result, 'live2d_motion', '없음')}")
                results[name] = True
            else:
                print(f"❌ {name} 생성 실패 - 결과 없음")
                results[name] = False
                
        except Exception as e:
            print(f"❌ {name} 생성 실패: {str(e)}")
            results[name] = False
        
        print()
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"📊 엔진 테스트 결과: {success_count}/{total_count} 성공")
    
    return success_count == total_count

async def test_fallback_system():
    """Fallback 시스템 테스트"""
    print("🔄 Fallback 시스템 테스트")
    print("=" * 50)
    
    # Cerebras를 일시적으로 비활성화하여 fallback 테스트
    original_enabled = cerebras_settings.enable_cerebras
    
    try:
        # Cerebras 비활성화
        cerebras_settings.enable_cerebras = False
        print("📴 Cerebras AI를 일시적으로 비활성화했습니다.")
        
        # 설정 확인
        enabled = is_cerebras_enabled()
        print(f"✅ Cerebras 비활성화 확인: {not enabled}")
        
        if not enabled:
            print("✅ Fallback 시스템이 정상적으로 작동할 것입니다.")
            print("   (실제 fallback 테스트는 fortune_service.py에서 수행됩니다)")
            return True
        else:
            print("❌ Cerebras 비활성화가 제대로 되지 않았습니다.")
            return False
            
    finally:
        # 원래 설정으로 복구
        cerebras_settings.enable_cerebras = original_enabled
        print(f"🔄 Cerebras 설정을 원래대로 복구했습니다: {original_enabled}")

async def main():
    """메인 테스트 함수"""
    print("🤖 Cerebras AI 통합 테스트 시작")
    print("=" * 70)
    print()
    
    test_results = []
    
    # 1. 설정 테스트
    config_ok = await test_cerebras_config()
    test_results.append(("설정 테스트", config_ok))
    print()
    
    # 2. API 연결 테스트
    if config_ok:
        api_ok = await test_cerebras_api_connection()
        test_results.append(("API 연결 테스트", api_ok))
        print()
        
        # 3. 엔진 테스트 (API가 작동하는 경우에만)
        if api_ok:
            engines_ok = await test_fortune_engines()
            test_results.append(("운세 엔진 테스트", engines_ok))
        else:
            test_results.append(("운세 엔진 테스트", False))
            print("⏭️ API 연결 실패로 엔진 테스트를 건너뜁니다.")
    else:
        test_results.append(("API 연결 테스트", False))
        test_results.append(("운세 엔진 테스트", False))
        print("⏭️ 설정 문제로 API 및 엔진 테스트를 건너뜁니다.")
    
    print()
    
    # 4. Fallback 시스템 테스트
    fallback_ok = await test_fallback_system()
    test_results.append(("Fallback 시스템 테스트", fallback_ok))
    
    # 최종 결과 출력
    print("\n" + "=" * 70)
    print("📋 최종 테스트 결과")
    print("=" * 70)
    
    for test_name, result in test_results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name}: {status}")
    
    success_count = sum(result for _, result in test_results)
    total_count = len(test_results)
    
    print(f"\n📊 전체 결과: {success_count}/{total_count} 테스트 통과")
    
    if success_count == total_count:
        print("🎉 모든 테스트가 성공했습니다! Cerebras AI가 정상 작동합니다.")
        return True
    else:
        print("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
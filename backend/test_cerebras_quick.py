#!/usr/bin/env python3
"""
Cerebras 모델 변경 후 빠른 테스트
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
    cerebras_settings
)
from src.fortune_vtuber.fortune.cerebras_engine import CerebrasDailyFortuneEngine
from src.fortune_vtuber.fortune.engines import PersonalizationContext
from datetime import date

async def test_new_model():
    """새로운 모델로 빠른 테스트"""
    print("🤖 Cerebras 모델 변경 후 테스트")
    print("=" * 50)
    
    # 환경변수 확인
    print(f"📝 현재 설정:")
    print(f"  CEREBRAS_MODEL: {os.getenv('CEREBRAS_MODEL')}")
    print(f"  Cerebras 활성화: {is_cerebras_enabled()}")
    
    config = get_cerebras_config()
    if config:
        print(f"  기본 모델: {config.model}")
        print(f"  Fallback 모델: {config.fallback_model}")
        print(f"  사용가능 모델: {config.available_models}")
    
    print()
    
    try:
        # 일일운세 엔진으로 테스트
        engine = CerebrasDailyFortuneEngine(config)
        
        # 테스트용 컨텍스트
        context = PersonalizationContext(
            birth_date=date(1990, 5, 15),
            preferences={"name": "테스트 사용자"}
        )
        
        print("📡 AI 운세 생성 테스트 중...")
        result = await engine.generate_fortune(context)
        
        if result:
            print("✅ AI 운세 생성 성공!")
            print(f"  운세 ID: {result.fortune_id}")
            print(f"  운세 타입: {result.fortune_type}")
            print(f"  조언: {result.advice[:150] if result.advice else '없음'}{'...' if result.advice and len(result.advice) > 150 else ''}")
            print(f"  Live2D 감정: {getattr(result, 'live2d_emotion', '없음')}")
            print(f"  Live2D 모션: {getattr(result, 'live2d_motion', '없음')}")
            return True
        else:
            print("❌ 운세 생성 실패")
            return False
            
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_new_model())
    if success:
        print("\n🎉 모델 변경이 성공적으로 완료되었습니다!")
    else:
        print("\n⚠️ 문제가 있습니다. 설정을 다시 확인해주세요.")
    sys.exit(0 if success else 1)
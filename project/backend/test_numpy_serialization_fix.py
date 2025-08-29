#!/usr/bin/env python3
"""
TTS API numpy.float32 직렬화 수정 테스트

numpy 타입들이 JSON 직렬화에서 안전하게 변환되는지 테스트합니다.
"""

import numpy as np
import json
import sys
import os
from typing import Dict, Any

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fortune_vtuber.utils.serialization import (
    convert_numpy_types,
    safe_json_dumps,
    sanitize_for_json,
    validate_json_serializable,
    fix_lipsync_data,
    create_safe_api_response,
    NumpySafeJSONEncoder
)

def test_basic_numpy_conversion():
    """기본 numpy 타입 변환 테스트"""
    print("=== 기본 numpy 타입 변환 테스트 ===")
    
    test_data = {
        "numpy_float32": np.float32(3.14159),
        "numpy_float64": np.float64(2.71828),
        "numpy_int32": np.int32(42),
        "numpy_int64": np.int64(100),
        "numpy_bool": np.bool_(True),
        "numpy_array": np.array([1.1, 2.2, 3.3], dtype=np.float32),
        "regular_float": 1.23,
        "regular_int": 456,
        "regular_bool": False
    }
    
    print("원본 데이터 타입들:")
    for key, value in test_data.items():
        print(f"  {key}: {type(value)} = {value}")
    
    # 변환 테스트
    converted = convert_numpy_types(test_data)
    print("\n변환된 데이터 타입들:")
    for key, value in converted.items():
        print(f"  {key}: {type(value)} = {value}")
    
    # JSON 직렬화 테스트
    try:
        json_str = json.dumps(converted)
        print(f"\nJSON 직렬화 성공: {json_str[:100]}...")
        return True
    except Exception as e:
        print(f"\nJSON 직렬화 실패: {e}")
        return False

def test_lipsync_data_format():
    """LipSync 데이터 형태 변환 테스트"""
    print("\n=== LipSync 데이터 변환 테스트 ===")
    
    # 가상의 LipSync 데이터 생성 (numpy 타입 포함)
    class MockLipSyncData:
        def __init__(self):
            self.phonemes = [
                (np.float32(0.0), "a", np.float32(0.1)),
                (np.float32(0.1), "e", np.float32(0.15)),
                (np.float32(0.25), "i", np.float32(0.1))
            ]
            self.mouth_shapes = [
                (np.float32(0.0), {"ParamA": np.float32(0.8), "ParamI": np.float32(0.0)}),
                (np.float32(0.05), {"ParamA": np.float32(0.6), "ParamI": np.float32(0.2)}),
                (np.float32(0.1), {"ParamA": np.float32(0.0), "ParamI": np.float32(1.0)})
            ]
            self.duration = np.float32(0.35)
            self.frame_rate = np.float32(30.0)
    
    lipsync_data = MockLipSyncData()
    
    print("원본 LipSync 데이터:")
    print(f"  phonemes[0]: {lipsync_data.phonemes[0]} - 타입들: {[type(x) for x in lipsync_data.phonemes[0]]}")
    print(f"  mouth_shapes[0]: {lipsync_data.mouth_shapes[0]}")
    print(f"  duration: {lipsync_data.duration} ({type(lipsync_data.duration)})")
    
    # 변환 적용
    fixed_data = fix_lipsync_data(lipsync_data)
    
    print("\n변환된 LipSync 데이터:")
    print(f"  phonemes[0]: {fixed_data.phonemes[0]} - 타입들: {[type(x) for x in fixed_data.phonemes[0]]}")
    print(f"  mouth_shapes[0]: {fixed_data.mouth_shapes[0]}")
    print(f"  duration: {fixed_data.duration} ({type(fixed_data.duration)})")
    
    # 직렬화 테스트
    data_dict = {
        "phonemes": fixed_data.phonemes,
        "mouth_shapes": fixed_data.mouth_shapes,
        "duration": fixed_data.duration,
        "frame_rate": fixed_data.frame_rate
    }
    
    try:
        json_str = safe_json_dumps(data_dict)
        print(f"\nJSON 직렬화 성공: {len(json_str)} 문자")
        return True
    except Exception as e:
        print(f"\nJSON 직렬화 실패: {e}")
        return False

def test_api_response_format():
    """API 응답 형태 변환 테스트"""
    print("\n=== API 응답 형태 변환 테스트 ===")
    
    # TTS API 응답과 유사한 데이터 구조 생성
    mock_response = {
        "success": True,
        "data": {
            "duration": np.float32(2.5),
            "generation_time": np.float32(0.8),
            "cached": np.bool_(False),
            "lipsync_data": {
                "enabled": True,
                "phoneme_count": np.int32(15),
                "mouth_shape_count": np.int64(30)
            },
            "expressions": [
                (np.float32(0.0), "joy", np.float32(0.8)),
                (np.float32(1.2), "neutral", np.float32(0.3))
            ],
            "live2d_commands": [
                {
                    "type": "lipsync",
                    "timestamp": np.float32(0.05),
                    "data": {
                        "mouth_parameters": {
                            "ParamA": np.float32(0.7),
                            "ParamI": np.float32(0.1)
                        },
                        "duration": np.float32(0.033)
                    }
                }
            ]
        }
    }
    
    print("원본 API 응답 데이터:")
    print(f"  duration: {mock_response['data']['duration']} ({type(mock_response['data']['duration'])})")
    print(f"  live2d_commands[0]['data']['mouth_parameters']['ParamA']: {mock_response['data']['live2d_commands'][0]['data']['mouth_parameters']['ParamA']}")
    
    # 안전한 응답 생성
    safe_response = create_safe_api_response(mock_response)
    
    print("\n변환된 API 응답 데이터:")
    print(f"  duration: {safe_response['data']['duration']} ({type(safe_response['data']['duration'])})")
    print(f"  live2d_commands[0]['data']['mouth_parameters']['ParamA']: {safe_response['data']['live2d_commands'][0]['data']['mouth_parameters']['ParamA']}")
    
    # JSON 직렬화 테스트
    try:
        json_str = json.dumps(safe_response)
        print(f"\nJSON 직렬화 성공: {len(json_str)} 문자")
        return True
    except Exception as e:
        print(f"\nJSON 직렬화 실패: {e}")
        return False

def test_edge_cases():
    """엣지 케이스 테스트"""
    print("\n=== 엣지 케이스 테스트 ===")
    
    edge_cases = {
        "nested_numpy": {
            "level1": {
                "level2": {
                    "numpy_val": np.float32(1.23)
                }
            }
        },
        "list_with_numpy": [np.int32(1), np.float64(2.0), "string", True],
        "tuple_with_numpy": (np.float32(3.14), "pi", np.bool_(True)),
        "mixed_array": np.array([1, 2.5, 3], dtype=object),
        "empty_array": np.array([]),
        "none_value": None,
        "complex_numpy": np.complex64(1 + 2j)
    }
    
    print("엣지 케이스 원본 데이터:")
    for key, value in edge_cases.items():
        print(f"  {key}: {type(value)} = {value}")
    
    # 변환 및 직렬화 테스트
    try:
        sanitized = sanitize_for_json(edge_cases)
        json_str = json.dumps(sanitized)
        print(f"\n모든 엣지 케이스 JSON 직렬화 성공: {len(json_str)} 문자")
        return True
    except Exception as e:
        print(f"\n엣지 케이스 처리 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("TTS API numpy.float32 직렬화 수정 테스트")
    print("=" * 50)
    
    tests = [
        ("기본 numpy 타입 변환", test_basic_numpy_conversion),
        ("LipSync 데이터 변환", test_lipsync_data_format), 
        ("API 응답 형태 변환", test_api_response_format),
        ("엣지 케이스", test_edge_cases)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
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
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("numpy.float32 직렬화 문제가 해결되었습니다.")
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("추가 수정이 필요할 수 있습니다.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
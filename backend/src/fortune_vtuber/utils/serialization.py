"""
JSON 직렬화 유틸리티

numpy 타입을 Python 네이티브 타입으로 변환하여 
JSON 직렬화 에러를 방지하는 유틸리티 함수들
"""

import json
import numpy as np
from typing import Any, Dict, List, Union, Optional
from dataclasses import is_dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class NumpySafeJSONEncoder(json.JSONEncoder):
    """Numpy 타입을 안전하게 처리하는 JSON 인코더"""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, (np.complex64, np.complex128)):
            return {"real": float(obj.real), "imag": float(obj.imag)}
        elif is_dataclass(obj):
            return asdict(obj)
        return super().default(obj)


def convert_numpy_types(obj: Any) -> Any:
    """
    객체 내의 모든 numpy 타입을 Python 네이티브 타입으로 변환
    
    Args:
        obj: 변환할 객체 (dict, list, numpy 타입 등)
        
    Returns:
        Any: numpy 타입이 변환된 객체
    """
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.complex64, np.complex128)):
        return {"real": float(obj.real), "imag": float(obj.imag)}
    elif is_dataclass(obj):
        return convert_numpy_types(asdict(obj))
    else:
        return obj


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    numpy 타입을 안전하게 처리하여 JSON으로 변환
    
    Args:
        obj: JSON으로 변환할 객체
        **kwargs: json.dumps에 전달할 추가 파라미터
        
    Returns:
        str: JSON 문자열
    """
    try:
        # 먼저 numpy 타입 변환 시도
        converted_obj = convert_numpy_types(obj)
        return json.dumps(converted_obj, **kwargs)
    except (TypeError, ValueError) as e:
        logger.warning(f"Standard conversion failed, using NumpySafeJSONEncoder: {e}")
        # 변환 실패시 커스텀 인코더 사용
        return json.dumps(obj, cls=NumpySafeJSONEncoder, **kwargs)


def sanitize_for_json(data: Any) -> Any:
    """
    JSON 직렬화를 위해 데이터를 정리
    
    Args:
        data: 정리할 데이터
        
    Returns:
        Any: JSON 직렬화 가능한 데이터
    """
    if data is None:
        return None
    
    try:
        # 기본 타입들은 그대로 반환
        if isinstance(data, (str, int, float, bool)):
            return data
        
        # numpy 타입 변환
        if isinstance(data, (np.integer, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.floating, np.float32, np.float64)):
            return float(data)
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.ndarray):
            return data.tolist()
        
        # 컬렉션 타입 재귀 처리
        elif isinstance(data, dict):
            return {key: sanitize_for_json(value) for key, value in data.items()}
        elif isinstance(data, (list, tuple)):
            return [sanitize_for_json(item) for item in data]
        elif isinstance(data, set):
            return [sanitize_for_json(item) for item in data]
        
        # dataclass 처리
        elif is_dataclass(data):
            return sanitize_for_json(asdict(data))
        
        # 기타 객체는 str로 변환
        else:
            logger.debug(f"Converting unknown type {type(data)} to string: {data}")
            return str(data)
            
    except Exception as e:
        logger.error(f"Failed to sanitize data of type {type(data)}: {e}")
        return str(data) if data is not None else None


def validate_json_serializable(data: Any) -> bool:
    """
    데이터가 JSON 직렬화 가능한지 확인
    
    Args:
        data: 확인할 데이터
        
    Returns:
        bool: 직렬화 가능하면 True
    """
    try:
        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False


def fix_lipsync_data(lipsync_data: Any) -> Any:
    """
    립싱크 데이터의 numpy 타입을 수정
    
    Args:
        lipsync_data: 립싱크 데이터 객체
        
    Returns:
        Any: 수정된 립싱크 데이터
    """
    if not lipsync_data:
        return lipsync_data
    
    try:
        if hasattr(lipsync_data, 'phonemes'):
            # phonemes는 List[Tuple[float, str, float]] 형태
            if lipsync_data.phonemes:
                fixed_phonemes = []
                for phoneme in lipsync_data.phonemes:
                    if isinstance(phoneme, (list, tuple)) and len(phoneme) >= 3:
                        fixed_phonemes.append((
                            float(phoneme[0]),  # timestamp
                            str(phoneme[1]),    # phoneme
                            float(phoneme[2])   # duration
                        ))
                    else:
                        fixed_phonemes.append(phoneme)
                lipsync_data.phonemes = fixed_phonemes
        
        if hasattr(lipsync_data, 'mouth_shapes'):
            # mouth_shapes는 List[Tuple[float, Dict[str, float]]] 형태
            if lipsync_data.mouth_shapes:
                fixed_mouth_shapes = []
                for mouth_shape in lipsync_data.mouth_shapes:
                    if isinstance(mouth_shape, (list, tuple)) and len(mouth_shape) >= 2:
                        timestamp = float(mouth_shape[0])
                        params = mouth_shape[1]
                        
                        # params가 dict인 경우 numpy 값들을 float로 변환
                        if isinstance(params, dict):
                            fixed_params = {}
                            for key, value in params.items():
                                fixed_params[str(key)] = float(value)
                            fixed_mouth_shapes.append((timestamp, fixed_params))
                        else:
                            fixed_mouth_shapes.append(mouth_shape)
                    else:
                        fixed_mouth_shapes.append(mouth_shape)
                lipsync_data.mouth_shapes = fixed_mouth_shapes
        
        # 기타 numpy float 속성들 수정
        for attr in ['duration', 'frame_rate', 'total_duration']:
            if hasattr(lipsync_data, attr):
                value = getattr(lipsync_data, attr)
                if isinstance(value, (np.floating, np.float32, np.float64)):
                    setattr(lipsync_data, attr, float(value))
                elif isinstance(value, (np.integer, np.int32, np.int64)):
                    setattr(lipsync_data, attr, int(value))
        
        return lipsync_data
        
    except Exception as e:
        logger.error(f"Failed to fix lipsync data: {e}")
        return lipsync_data


def fix_tts_result_for_json(tts_result: Any) -> Any:
    """
    TTS 결과 객체의 numpy 타입들을 JSON 직렬화 가능하도록 수정
    
    Args:
        tts_result: TTS 결과 객체
        
    Returns:
        Any: 수정된 TTS 결과 객체
    """
    if not tts_result:
        return tts_result
    
    try:
        # 립싱크 데이터 수정
        if hasattr(tts_result, 'lip_sync_data') and tts_result.lip_sync_data:
            tts_result.lip_sync_data = fix_lipsync_data(tts_result.lip_sync_data)
        
        if hasattr(tts_result, 'lip_sync') and tts_result.lip_sync:
            tts_result.lip_sync = fix_lipsync_data(tts_result.lip_sync)
        
        # 숫자 타입 수정
        for attr in ['duration', 'generation_time']:
            if hasattr(tts_result, attr):
                value = getattr(tts_result, attr)
                if isinstance(value, (np.floating, np.float32, np.float64)):
                    setattr(tts_result, attr, float(value))
                elif isinstance(value, (np.integer, np.int32, np.int64)):
                    setattr(tts_result, attr, int(value))
        
        return tts_result
        
    except Exception as e:
        logger.error(f"Failed to fix TTS result: {e}")
        return tts_result


def create_safe_api_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    API 응답을 JSON 직렬화 안전하게 생성
    
    Args:
        data: API 응답 데이터
        
    Returns:
        Dict[str, Any]: JSON 직렬화 안전한 응답 데이터
    """
    try:
        # 전체 데이터를 정리
        sanitized_data = sanitize_for_json(data)
        
        # 직렬화 테스트
        json.dumps(sanitized_data)
        
        return sanitized_data
        
    except Exception as e:
        logger.error(f"Failed to create safe API response: {e}")
        # 실패시 기본적인 에러 응답 반환
        return {
            "success": False,
            "error": {
                "code": "SERIALIZATION_ERROR",
                "message": "데이터 직렬화 중 오류가 발생했습니다",
                "details": str(e)
            }
        }
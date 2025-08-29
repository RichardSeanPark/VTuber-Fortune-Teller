"""
Live2D 감정 엔진 브리지 - JavaScript 감정 엔진을 Python에서 사용

Node.js를 통해 JavaScript 감정 엔진을 실행하고 결과를 파이썬으로 전달
실시간 감정 계산 및 Live2D 파라미터 생성
"""

import json
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmotionBridge:
    """JavaScript 감정 엔진 브리지"""
    
    def __init__(self):
        self.engine_path = Path(__file__).parent / "emotion_engine.js"
        self.node_available = self._check_node_availability()
        
    def _check_node_availability(self) -> bool:
        """Node.js 사용 가능 여부 확인"""
        try:
            result = subprocess.run(
                ['node', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("Node.js not available, falling back to Python implementation")
            return False
    
    def calculate_emotion(self, fortune_result: Dict[str, Any], 
                         session_id: str, 
                         user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """
        운세 결과를 기반으로 감정 상태 계산
        
        Args:
            fortune_result: 운세 결과 데이터
            session_id: 세션 ID
            user_uuid: 사용자 UUID (선택)
            
        Returns:
            계산된 감정 상태 정보
        """
        if self.node_available:
            return self._calculate_with_javascript(fortune_result, session_id, user_uuid)
        else:
            return self._calculate_with_python(fortune_result, session_id, user_uuid)
    
    def _calculate_with_javascript(self, fortune_result: Dict[str, Any], 
                                 session_id: str, 
                                 user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """JavaScript 엔진을 사용한 감정 계산"""
        try:
            # 임시 입력 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                input_data = {
                    'fortuneResult': fortune_result,
                    'sessionId': session_id,
                    'userUuid': user_uuid
                }
                json.dump(input_data, temp_file, ensure_ascii=False, indent=2)
                temp_input_path = temp_file.name
            
            # Node.js 실행 스크립트 생성
            node_script = f"""
const fs = require('fs');

// 감정 엔진 로드
{self._load_emotion_engine_code()}

// 입력 데이터 읽기
const inputData = JSON.parse(fs.readFileSync('{temp_input_path}', 'utf8'));
const engine = new Live2DEmotionEngine();

// 감정 계산
const result = engine.calculateEmotion(
    inputData.fortuneResult,
    inputData.sessionId, 
    inputData.userUuid
);

// 결과 출력
console.log(JSON.stringify(result, null, 2));
"""
            
            # 임시 스크립트 파일 생성
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as script_file:
                script_file.write(node_script)
                script_path = script_file.name
            
            # Node.js 실행
            result = subprocess.run(
                ['node', script_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 임시 파일 정리
            os.unlink(temp_input_path)
            os.unlink(script_path)
            
            if result.returncode == 0:
                emotion_result = json.loads(result.stdout)
                logger.info(f"Emotion calculated via JavaScript for session {session_id}")
                return emotion_result
            else:
                logger.error(f"JavaScript emotion engine error: {result.stderr}")
                return self._calculate_with_python(fortune_result, session_id, user_uuid)
                
        except Exception as e:
            logger.error(f"Failed to calculate emotion with JavaScript: {e}")
            return self._calculate_with_python(fortune_result, session_id, user_uuid)
    
    def _load_emotion_engine_code(self) -> str:
        """JavaScript 감정 엔진 코드 로드"""
        try:
            with open(self.engine_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            logger.error(f"Emotion engine file not found: {self.engine_path}")
            return ""
    
    def _calculate_with_python(self, fortune_result: Dict[str, Any], 
                             session_id: str, 
                             user_uuid: Optional[str] = None) -> Dict[str, Any]:
        """Python 기본 구현 (JavaScript 엔진을 사용할 수 없을 때의 폴백)"""
        
        fortune_type = fortune_result.get('fortune_type', 'daily')
        
        # 기본 감정 결정
        if fortune_type == 'daily':
            emotion_data = self._analyze_daily_fortune_python(fortune_result)
        elif fortune_type == 'tarot':
            emotion_data = self._analyze_tarot_fortune_python(fortune_result)
        elif fortune_type in ['zodiac', 'oriental']:
            emotion_data = self._analyze_mystical_fortune_python(fortune_result)
        else:
            emotion_data = {
                'primary_emotion': 'neutral',
                'intensity': 0.6,
                'confidence': 0.5
            }
        
        # 모션 선택
        motion = self._select_motion_python(emotion_data['primary_emotion'], fortune_type)
        
        # Live2D 파라미터 생성
        parameters = self._generate_parameters_python(
            emotion_data['primary_emotion'], 
            emotion_data['intensity']
        )
        
        # 메시지 선택
        message = self._generate_message_python(emotion_data['primary_emotion'], fortune_result)
        
        return {
            'primary_emotion': emotion_data['primary_emotion'],
            'secondary_emotion': emotion_data.get('secondary_emotion'),
            'intensity': emotion_data['intensity'],
            'motion': motion,
            'duration': self._calculate_duration_python(emotion_data['primary_emotion'], emotion_data['intensity']),
            'parameters': parameters,
            'message': message,
            'fade_timing': self._get_fade_timing_python(emotion_data['primary_emotion']),
            'context_tags': [f"type_{fortune_type}", "python_fallback"],
            'confidence_score': emotion_data['confidence']
        }
    
    def _analyze_daily_fortune_python(self, fortune_result: Dict[str, Any]) -> Dict[str, Any]:
        """일반 운세 분석 (Python 구현)"""
        overall = fortune_result.get('overall_fortune', {})
        score = overall.get('score', 50)
        
        if score >= 85:
            return {'primary_emotion': 'joy', 'intensity': 0.9, 'confidence': 0.9}
        elif score >= 70:
            return {'primary_emotion': 'joy', 'intensity': 0.7, 'confidence': 0.8}
        elif score >= 55:
            return {'primary_emotion': 'comfort', 'intensity': 0.6, 'confidence': 0.7}
        elif score >= 40:
            return {'primary_emotion': 'neutral', 'intensity': 0.5, 'confidence': 0.6}
        else:
            return {'primary_emotion': 'concern', 'intensity': 0.7, 'confidence': 0.7}
    
    def _analyze_tarot_fortune_python(self, fortune_result: Dict[str, Any]) -> Dict[str, Any]:
        """타로 카드 분석 (Python 구현)"""
        return {
            'primary_emotion': 'mystical',
            'secondary_emotion': 'thinking',
            'intensity': 0.8,
            'confidence': 0.8
        }
    
    def _analyze_mystical_fortune_python(self, fortune_result: Dict[str, Any]) -> Dict[str, Any]:
        """신비계열 운세 분석 (Python 구현)"""
        return {
            'primary_emotion': 'mystical',
            'intensity': 0.8,
            'confidence': 0.8
        }
    
    def _select_motion_python(self, emotion: str, fortune_type: str) -> str:
        """모션 선택 (Python 구현)"""
        motion_map = {
            'daily': {
                'joy': 'blessing',
                'comfort': 'blessing',
                'neutral': 'thinking_pose',
                'concern': 'thinking_pose'
            },
            'tarot': {
                'mystical': 'card_draw'
            },
            'zodiac': {
                'mystical': 'crystal_gaze'
            },
            'oriental': {
                'mystical': 'special_reading'
            }
        }
        
        type_map = motion_map.get(fortune_type, motion_map['daily'])
        return type_map.get(emotion, 'thinking_pose')
    
    def _generate_parameters_python(self, emotion: str, intensity: float) -> Dict[str, float]:
        """Live2D 파라미터 생성 (Python 구현)"""
        parameter_map = {
            'joy': {
                'ParamEyeLSmile': intensity,
                'ParamEyeRSmile': intensity,
                'ParamMouthForm': intensity * 1.2,
                'ParamMouthUp': intensity * 0.8,
                'ParamCheek': intensity * 0.6
            },
            'comfort': {
                'ParamEyeLSmile': intensity * 0.7,
                'ParamEyeRSmile': intensity * 0.7,
                'ParamMouthForm': intensity * 0.8,
                'ParamMouthUp': intensity * 0.4,
                'ParamCheek': intensity * 0.3
            },
            'mystical': {
                'ParamEyeLOpen': 1.0 - intensity * 0.3,
                'ParamEyeROpen': 1.0 - intensity * 0.3,
                'ParamEyeLForm': intensity * 0.4,
                'ParamEyeRForm': intensity * 0.4,
                'ParamEyeEffect': intensity * 0.8
            },
            'concern': {
                'ParamBrowLY': -intensity * 0.6,
                'ParamBrowRY': -intensity * 0.6,
                'ParamBrowLAngle': -intensity * 0.4,
                'ParamBrowRAngle': intensity * 0.4,
                'ParamMouthDown': intensity * 0.5
            },
            'thinking': {
                'ParamEyeLOpen': 1.0 - intensity * 0.5,
                'ParamEyeROpen': 1.0 - intensity * 0.5,
                'ParamEyeBallY': -intensity * 0.4,
                'ParamBrowLY': -intensity * 0.3,
                'ParamBrowRY': -intensity * 0.3
            }
        }
        
        return parameter_map.get(emotion, {
            'ParamEyeLOpen': 1.0,
            'ParamEyeROpen': 1.0
        })
    
    def _generate_message_python(self, emotion: str, fortune_result: Dict[str, Any]) -> str:
        """메시지 생성 (Python 구현)"""
        message_map = {
            'joy': [
                "와! 정말 좋은 결과가 나왔어요! ✨",
                "행복한 에너지가 넘쳐나고 있어요! 💫"
            ],
            'comfort': [
                "따뜻한 위로의 메시지를 전해드려요 🌸",
                "마음이 편안해지는 결과네요 😌"
            ],
            'mystical': [
                "신비로운 운명의 흐름이 느껴져요... ✨",
                "우주의 깊은 메시지가 담겨있어요 🌟"
            ],
            'concern': [
                "조금 신중하게 접근해보세요 💭",
                "차분히 생각해볼 시간이 필요해 보여요"
            ],
            'thinking': [
                "깊이 생각해볼만한 메시지가 있어요 🤔",
                "신중한 판단이 필요한 시기인 것 같아요"
            ]
        }
        
        messages = message_map.get(emotion, ["운세를 확인해보세요"])
        import random
        return random.choice(messages)
    
    def _calculate_duration_python(self, emotion: str, intensity: float) -> int:
        """지속 시간 계산 (Python 구현)"""
        base_durations = {
            'joy': 4000,
            'comfort': 5000,
            'mystical': 7000,
            'concern': 4500,
            'thinking': 6000
        }
        
        duration = base_durations.get(emotion, 4000)
        return int(duration * (0.8 + intensity * 0.4))
    
    def _get_fade_timing_python(self, emotion: str) -> Dict[str, float]:
        """페이드 타이밍 (Python 구현)"""
        fade_map = {
            'joy': {'fadeIn': 0.3, 'fadeOut': 0.8},
            'comfort': {'fadeIn': 0.6, 'fadeOut': 0.4},
            'mystical': {'fadeIn': 1.0, 'fadeOut': 0.8},
            'concern': {'fadeIn': 0.4, 'fadeOut': 0.6},
            'thinking': {'fadeIn': 0.8, 'fadeOut': 0.5}
        }
        
        return fade_map.get(emotion, {'fadeIn': 0.5, 'fadeOut': 0.5})


# 싱글톤 인스턴스
emotion_bridge = EmotionBridge()
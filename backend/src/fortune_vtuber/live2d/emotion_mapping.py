"""
Live2D 감정 매핑 시스템 - 운세 결과에 따른 감정/모션 자동 매핑
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
import random

from ..models.live2d import EmotionType, MotionType
from ..fortune.engines import FortuneGrade


class ReactionIntensity(Enum):
    """반응 강도"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class EmotionMapper:
    """운세 결과를 Live2D 감정/모션으로 매핑하는 클래스"""
    
    def __init__(self):
        # 운세 등급별 기본 감정 매핑
        self.grade_emotion_map = {
            FortuneGrade.EXCELLENT: {
                "primary": EmotionType.JOY,
                "secondary": [EmotionType.COMFORT, EmotionType.PLAYFUL],
                "intensity": ReactionIntensity.HIGH
            },
            FortuneGrade.GOOD: {
                "primary": EmotionType.COMFORT,
                "secondary": [EmotionType.JOY, EmotionType.NEUTRAL],
                "intensity": ReactionIntensity.MEDIUM
            },
            FortuneGrade.NORMAL: {
                "primary": EmotionType.NEUTRAL,
                "secondary": [EmotionType.THINKING, EmotionType.COMFORT],
                "intensity": ReactionIntensity.MEDIUM
            },
            FortuneGrade.BAD: {
                "primary": EmotionType.CONCERN,
                "secondary": [EmotionType.THINKING, EmotionType.NEUTRAL],
                "intensity": ReactionIntensity.MEDIUM
            },
            FortuneGrade.WARNING: {
                "primary": EmotionType.CONCERN,
                "secondary": [EmotionType.MYSTICAL, EmotionType.THINKING],
                "intensity": ReactionIntensity.HIGH
            }
        }
        
        # 운세 타입별 특화 모션 매핑
        self.fortune_type_motion_map = {
            "daily": {
                FortuneGrade.EXCELLENT: [MotionType.BLESSING, MotionType.GREETING],
                FortuneGrade.GOOD: [MotionType.GREETING, MotionType.BLESSING],
                FortuneGrade.NORMAL: [MotionType.THINKING_POSE, MotionType.GREETING],
                FortuneGrade.BAD: [MotionType.THINKING_POSE, MotionType.CRYSTAL_GAZE],
                FortuneGrade.WARNING: [MotionType.CRYSTAL_GAZE, MotionType.SPECIAL_READING]
            },
            "tarot": {
                FortuneGrade.EXCELLENT: [MotionType.CARD_DRAW, MotionType.BLESSING],
                FortuneGrade.GOOD: [MotionType.CARD_DRAW, MotionType.GREETING],
                FortuneGrade.NORMAL: [MotionType.CARD_DRAW, MotionType.THINKING_POSE],
                FortuneGrade.BAD: [MotionType.CARD_DRAW, MotionType.CRYSTAL_GAZE],
                FortuneGrade.WARNING: [MotionType.CARD_DRAW, MotionType.SPECIAL_READING]
            },
            "zodiac": {
                FortuneGrade.EXCELLENT: [MotionType.BLESSING, MotionType.CRYSTAL_GAZE],
                FortuneGrade.GOOD: [MotionType.CRYSTAL_GAZE, MotionType.GREETING],
                FortuneGrade.NORMAL: [MotionType.CRYSTAL_GAZE, MotionType.THINKING_POSE],
                FortuneGrade.BAD: [MotionType.THINKING_POSE, MotionType.CRYSTAL_GAZE],
                FortuneGrade.WARNING: [MotionType.SPECIAL_READING, MotionType.CRYSTAL_GAZE]
            },
            "saju": {
                FortuneGrade.EXCELLENT: [MotionType.SPECIAL_READING, MotionType.BLESSING],
                FortuneGrade.GOOD: [MotionType.SPECIAL_READING, MotionType.CRYSTAL_GAZE],
                FortuneGrade.NORMAL: [MotionType.SPECIAL_READING, MotionType.THINKING_POSE],
                FortuneGrade.BAD: [MotionType.THINKING_POSE, MotionType.SPECIAL_READING],
                FortuneGrade.WARNING: [MotionType.SPECIAL_READING, MotionType.CRYSTAL_GAZE]
            }
        }
        
        # 점수별 세부 조정 (0-100)
        self.score_modifiers = {
            (90, 100): {"emotion_boost": 0.3, "motion_intensity": 1.2},
            (80, 89): {"emotion_boost": 0.2, "motion_intensity": 1.1},
            (70, 79): {"emotion_boost": 0.1, "motion_intensity": 1.0},
            (60, 69): {"emotion_boost": 0.0, "motion_intensity": 0.9},
            (50, 59): {"emotion_boost": 0.0, "motion_intensity": 0.8},
            (40, 49): {"emotion_boost": -0.1, "motion_intensity": 0.8},
            (30, 39): {"emotion_boost": -0.1, "motion_intensity": 0.7},
            (20, 29): {"emotion_boost": -0.2, "motion_intensity": 0.7},
            (0, 19): {"emotion_boost": -0.3, "motion_intensity": 0.6}
        }
        
        # 카테고리별 감정 조정 (연애, 금전, 건강, 업무)
        self.category_emotion_adjustments = {
            "love": {
                "high_score": EmotionType.PLAYFUL,
                "low_score": EmotionType.CONCERN,
                "special_motions": [MotionType.BLESSING, MotionType.GREETING]
            },
            "money": {
                "high_score": EmotionType.JOY,
                "low_score": EmotionType.THINKING,
                "special_motions": [MotionType.CRYSTAL_GAZE, MotionType.THINKING_POSE]
            },
            "health": {
                "high_score": EmotionType.COMFORT,
                "low_score": EmotionType.CONCERN,
                "special_motions": [MotionType.BLESSING, MotionType.CRYSTAL_GAZE]
            },
            "work": {
                "high_score": EmotionType.JOY,
                "low_score": EmotionType.THINKING,
                "special_motions": [MotionType.THINKING_POSE, MotionType.SPECIAL_READING]
            }
        }
    
    def map_fortune_to_reaction(
        self, 
        fortune_result: Dict, 
        use_secondary: bool = False,
        randomize: bool = True
    ) -> Tuple[EmotionType, MotionType, int]:
        """
        운세 결과를 Live2D 반응으로 매핑
        
        Args:
            fortune_result: 운세 결과 딕셔너리
            use_secondary: 보조 감정 사용 여부
            randomize: 랜덤 요소 추가 여부
            
        Returns:
            (감정, 모션, 지속시간) 튜플
        """
        # 전체 운세 등급 추출
        overall_fortune = fortune_result.get("overall_fortune", {})
        grade_str = overall_fortune.get("grade", "normal")
        score = overall_fortune.get("score", 50)
        fortune_type = fortune_result.get("fortune_type", "daily")
        
        # 등급 변환
        try:
            grade = FortuneGrade(grade_str)
        except ValueError:
            grade = FortuneGrade.NORMAL
        
        # 기본 감정 선택
        emotion_data = self.grade_emotion_map[grade]
        if use_secondary and randomize:
            emotion = random.choice([emotion_data["primary"]] + emotion_data["secondary"])
        else:
            emotion = emotion_data["primary"]
        
        # 모션 선택
        motion_options = self.fortune_type_motion_map.get(fortune_type, {}).get(
            grade, [MotionType.GREETING]
        )
        motion = random.choice(motion_options) if randomize else motion_options[0]
        
        # 카테고리별 조정
        emotion, motion = self._apply_category_adjustments(
            emotion, motion, fortune_result, score, randomize
        )
        
        # 점수별 지속시간 계산
        duration = self._calculate_duration(score, emotion_data["intensity"])
        
        return emotion, motion, duration
    
    def _apply_category_adjustments(
        self,
        base_emotion: EmotionType,
        base_motion: MotionType,
        fortune_result: Dict,
        overall_score: int,
        randomize: bool
    ) -> Tuple[EmotionType, MotionType]:
        """카테고리별 감정/모션 조정"""
        categories = fortune_result.get("categories", {})
        
        # 가장 높은/낮은 점수 카테고리 찾기
        highest_category = None
        lowest_category = None
        highest_score = 0
        lowest_score = 100
        
        for category_name, category_data in categories.items():
            score = category_data.get("score", 50)
            if score > highest_score:
                highest_score = score
                highest_category = category_name
            if score < lowest_score:
                lowest_score = score
                lowest_category = category_name
        
        # 극단적인 경우 감정 조정
        if highest_score >= 85 and highest_category in self.category_emotion_adjustments:
            adjustment = self.category_emotion_adjustments[highest_category]
            if randomize and random.random() < 0.4:  # 40% 확률로 조정
                base_emotion = adjustment["high_score"]
                if random.random() < 0.3:  # 30% 확률로 특별 모션
                    base_motion = random.choice(adjustment["special_motions"])
        
        elif lowest_score <= 30 and lowest_category in self.category_emotion_adjustments:
            adjustment = self.category_emotion_adjustments[lowest_category]
            if randomize and random.random() < 0.5:  # 50% 확률로 조정
                base_emotion = adjustment["low_score"]
                if random.random() < 0.3:  # 30% 확률로 특별 모션
                    base_motion = random.choice(adjustment["special_motions"])
        
        return base_emotion, base_motion
    
    def _calculate_duration(self, score: int, intensity: ReactionIntensity) -> int:
        """점수와 강도에 따른 지속시간 계산 (밀리초)"""
        # 기본 지속시간 (강도별)
        base_durations = {
            ReactionIntensity.LOW: 3000,      # 3초
            ReactionIntensity.MEDIUM: 5000,   # 5초
            ReactionIntensity.HIGH: 8000,     # 8초
            ReactionIntensity.EXTREME: 12000  # 12초
        }
        
        base_duration = base_durations[intensity]
        
        # 점수별 조정
        for score_range, modifiers in self.score_modifiers.items():
            if score_range[0] <= score <= score_range[1]:
                duration = int(base_duration * modifiers["motion_intensity"])
                break
        else:
            duration = base_duration
        
        # 최소/최대 제한
        return max(2000, min(15000, duration))
    
    def get_greeting_reaction(self, user_context: Optional[Dict] = None) -> Tuple[EmotionType, MotionType, int]:
        """인사 반응 생성"""
        # 시간대별 인사
        from datetime import datetime
        current_hour = datetime.now().hour
        
        if 6 <= current_hour < 12:
            # 아침
            emotion = EmotionType.COMFORT
            motion = MotionType.GREETING
        elif 12 <= current_hour < 18:
            # 오후
            emotion = EmotionType.JOY
            motion = MotionType.GREETING
        elif 18 <= current_hour < 22:
            # 저녁
            emotion = EmotionType.NEUTRAL
            motion = MotionType.GREETING
        else:
            # 밤
            emotion = EmotionType.MYSTICAL
            motion = MotionType.CRYSTAL_GAZE
        
        return emotion, motion, 4000  # 4초
    
    def get_thinking_reaction(self) -> Tuple[EmotionType, MotionType, int]:
        """생각하는 반응 생성"""
        emotion = EmotionType.THINKING
        motion = MotionType.THINKING_POSE
        return emotion, motion, 6000  # 6초
    
    def get_surprise_reaction(self) -> Tuple[EmotionType, MotionType, int]:
        """놀라는 반응 생성"""
        emotion = EmotionType.SURPRISE
        motion = MotionType.SPECIAL_READING
        return emotion, motion, 5000  # 5초
    
    def get_random_idle_reaction(self) -> Tuple[EmotionType, MotionType, int]:
        """랜덤 대기 반응 생성"""
        idle_reactions = [
            (EmotionType.NEUTRAL, MotionType.GREETING, 3000),
            (EmotionType.THINKING, MotionType.THINKING_POSE, 4000),
            (EmotionType.MYSTICAL, MotionType.CRYSTAL_GAZE, 5000),
            (EmotionType.COMFORT, MotionType.BLESSING, 4000)
        ]
        
        return random.choice(idle_reactions)


class ReactionSequencer:
    """연속적인 감정/모션 시퀀스 관리"""
    
    def __init__(self, mapper: EmotionMapper):
        self.mapper = mapper
        
    def create_fortune_reading_sequence(
        self, 
        fortune_type: str, 
        duration_total: int = 15000
    ) -> List[Tuple[EmotionType, MotionType, int]]:
        """운세 읽기 시퀀스 생성"""
        sequences = []
        
        # 1. 준비 단계 (생각하는 모습)
        sequences.append((EmotionType.THINKING, MotionType.THINKING_POSE, 3000))
        
        # 2. 운세 읽기 단계 (타입별 특화)
        if fortune_type == "tarot":
            sequences.append((EmotionType.MYSTICAL, MotionType.CARD_DRAW, 4000))
        elif fortune_type == "zodiac":
            sequences.append((EmotionType.MYSTICAL, MotionType.CRYSTAL_GAZE, 4000))
        elif fortune_type == "saju":
            sequences.append((EmotionType.MYSTICAL, MotionType.SPECIAL_READING, 5000))
        else:  # daily
            sequences.append((EmotionType.NEUTRAL, MotionType.CRYSTAL_GAZE, 3000))
        
        # 3. 완료 단계 (결과에 따른 반응은 별도로 처리)
        remaining_time = duration_total - sum(seq[2] for seq in sequences)
        if remaining_time > 2000:
            sequences.append((EmotionType.COMFORT, MotionType.GREETING, remaining_time))
        
        return sequences
    
    def create_chat_response_sequence(
        self, 
        message_content: str, 
        duration_total: int = 8000
    ) -> List[Tuple[EmotionType, MotionType, int]]:
        """채팅 응답 시퀀스 생성"""
        sequences = []
        
        # 메시지 길이에 따른 반응
        if len(message_content) > 100:
            # 긴 메시지 - 천천히 읽는 모습
            sequences.append((EmotionType.THINKING, MotionType.THINKING_POSE, 4000))
            sequences.append((EmotionType.NEUTRAL, MotionType.GREETING, 4000))
        else:
            # 짧은 메시지 - 빠른 반응
            sequences.append((EmotionType.NEUTRAL, MotionType.GREETING, duration_total))
        
        return sequences
/**
 * Live2D 감정 엔진 - 운세 결과 기반 지능형 감정 매핑 시스템
 * 
 * 운세 점수, 타입, 사용자 히스토리를 종합하여 최적의 감정/모션 조합을 선택
 * JavaScript로 구현하여 실시간 계산 및 프론트엔드 호환성 확보
 */

class Live2DEmotionEngine {
    constructor() {
        this.emotionHistory = new Map(); // session_id -> emotion history
        this.userPreferences = new Map(); // user_uuid -> preference data
        this.contextWeights = {
            fortune_score: 0.4,     // 운세 점수의 가중치
            fortune_type: 0.3,      // 운세 타입의 가중치  
            user_history: 0.2,      // 사용자 선호도의 가중치
            time_context: 0.1       // 시간적 맥락의 가중치
        };
    }

    /**
     * 운세 결과를 기반으로 최적의 감정 상태 계산
     * @param {Object} fortuneResult - 운세 결과 데이터
     * @param {string} sessionId - 세션 ID
     * @param {string} userUuid - 사용자 UUID
     * @returns {Object} 계산된 감정 상태 정보
     */
    calculateEmotion(fortuneResult, sessionId, userUuid = null) {
        const fortuneType = fortuneResult.fortune_type || 'daily';
        const baseEmotion = this._getBaseEmotionFromFortune(fortuneResult);
        const intensity = this._calculateEmotionIntensity(fortuneResult);
        const context = this._buildEmotionalContext(fortuneResult, sessionId, userUuid);
        
        // 감정 조합 계산
        const emotionMix = this._blendEmotions(baseEmotion, context, intensity);
        const recommendedMotion = this._selectMotion(emotionMix, fortuneType, context);
        const customMessage = this._generateContextualMessage(emotionMix, fortuneResult);

        // 히스토리 업데이트
        this._updateEmotionHistory(sessionId, emotionMix);

        return {
            primary_emotion: emotionMix.primary,
            secondary_emotion: emotionMix.secondary,
            intensity: intensity,
            motion: recommendedMotion,
            duration: this._calculateDuration(emotionMix, intensity),
            parameters: this._generateLive2DParameters(emotionMix, intensity),
            message: customMessage,
            fade_timing: this._calculateFadeTiming(emotionMix),
            context_tags: context.tags,
            confidence_score: emotionMix.confidence
        };
    }

    /**
     * 운세 결과로부터 기본 감정 추출
     */
    _getBaseEmotionFromFortune(fortuneResult) {
        const fortuneType = fortuneResult.fortune_type || 'daily';

        switch (fortuneType) {
            case 'daily':
                return this._analyzeDailyFortune(fortuneResult);
            case 'tarot':
                return this._analyzeTarotFortune(fortuneResult);
            case 'zodiac':
                return this._analyzeZodiacFortune(fortuneResult);
            case 'oriental':
                return this._analyzeOrientalFortune(fortuneResult);
            default:
                return { emotion: 'neutral', confidence: 0.5 };
        }
    }

    /**
     * 일반 운세 분석
     */
    _analyzeDailyFortune(fortuneResult) {
        const overall = fortuneResult.overall_fortune || {};
        const grade = overall.grade || 'normal';
        const score = overall.score || 50;

        // 점수 기반 세밀한 감정 매핑
        if (score >= 85) {
            return { emotion: 'joy', confidence: 0.95, intensity_modifier: 1.2 };
        } else if (score >= 70) {
            return { emotion: 'joy', confidence: 0.8, intensity_modifier: 0.9 };
        } else if (score >= 55) {
            return { emotion: 'comfort', confidence: 0.7, intensity_modifier: 0.8 };
        } else if (score >= 40) {
            return { emotion: 'neutral', confidence: 0.6, intensity_modifier: 0.6 };
        } else if (score >= 25) {
            return { emotion: 'concern', confidence: 0.7, intensity_modifier: 0.7 };
        } else {
            return { emotion: 'concern', confidence: 0.8, intensity_modifier: 0.9 };
        }
    }

    /**
     * 타로 카드 분석
     */
    _analyzeTarotFortune(fortuneResult) {
        const cards = fortuneResult.cards || [];
        let positiveCount = 0;
        let negativeCount = 0;
        let neutralCount = 0;

        // 카드별 감정 점수 계산
        cards.forEach(card => {
            const meaning = card.meaning || '';
            const reversed = card.reversed || false;
            
            if (this._isPositiveCard(meaning, reversed)) {
                positiveCount++;
            } else if (this._isNegativeCard(meaning, reversed)) {
                negativeCount++;
            } else {
                neutralCount++;
            }
        });

        const totalCards = cards.length;
        if (totalCards === 0) {
            return { emotion: 'mystical', confidence: 0.5, intensity_modifier: 0.6 };
        }

        const positiveRatio = positiveCount / totalCards;
        const negativeRatio = negativeCount / totalCards;

        if (positiveRatio >= 0.6) {
            return { emotion: 'mystical', confidence: 0.85, intensity_modifier: 1.1, secondary: 'joy' };
        } else if (negativeRatio >= 0.6) {
            return { emotion: 'mystical', confidence: 0.8, intensity_modifier: 1.0, secondary: 'concern' };
        } else {
            return { emotion: 'mystical', confidence: 0.75, intensity_modifier: 0.8 };
        }
    }

    /**
     * 별자리 운세 분석
     */
    _analyzeZodiacFortune(fortuneResult) {
        const predictions = fortuneResult.predictions || {};
        const aspects = Object.keys(predictions).length;
        
        let totalScore = 0;
        let validAspects = 0;

        // 각 운세 영역별 점수 합산
        Object.values(predictions).forEach(prediction => {
            if (typeof prediction.score === 'number') {
                totalScore += prediction.score;
                validAspects++;
            }
        });

        if (validAspects === 0) {
            return { emotion: 'mystical', confidence: 0.5, intensity_modifier: 0.7 };
        }

        const averageScore = totalScore / validAspects;

        if (averageScore >= 75) {
            return { emotion: 'mystical', confidence: 0.9, intensity_modifier: 1.1, secondary: 'joy' };
        } else if (averageScore >= 50) {
            return { emotion: 'mystical', confidence: 0.8, intensity_modifier: 0.9 };
        } else {
            return { emotion: 'mystical', confidence: 0.7, intensity_modifier: 0.8, secondary: 'thinking' };
        }
    }

    /**
     * 사주 운세 분석
     */
    _analyzeOrientalFortune(fortuneResult) {
        const elements = fortuneResult.elements || {};
        const balance = this._calculateElementalBalance(elements);
        const harmony = balance.harmony_score || 50;

        if (harmony >= 80) {
            return { emotion: 'mystical', confidence: 0.95, intensity_modifier: 1.2, secondary: 'comfort' };
        } else if (harmony >= 60) {
            return { emotion: 'mystical', confidence: 0.85, intensity_modifier: 1.0 };
        } else if (harmony >= 40) {
            return { emotion: 'mystical', confidence: 0.75, intensity_modifier: 0.8, secondary: 'thinking' };
        } else {
            return { emotion: 'mystical', confidence: 0.8, intensity_modifier: 0.9, secondary: 'concern' };
        }
    }

    /**
     * 감정 강도 계산
     */
    _calculateEmotionIntensity(fortuneResult) {
        const fortuneType = fortuneResult.fortune_type || 'daily';
        let baseIntensity = 0.6;

        switch (fortuneType) {
            case 'daily':
                const score = fortuneResult.overall_fortune?.score || 50;
                baseIntensity = Math.abs(score - 50) / 50 * 0.8 + 0.4;
                break;
            case 'tarot':
                baseIntensity = 0.8; // 타로는 신비로운 느낌으로 높은 강도
                break;
            case 'zodiac':
                baseIntensity = 0.7; // 별자리도 신비로운 느낌
                break;
            case 'oriental':
                baseIntensity = 0.9; // 사주는 가장 깊고 신비로운 느낌
                break;
        }

        return Math.min(Math.max(baseIntensity, 0.2), 1.0);
    }

    /**
     * 감정적 맥락 구성
     */
    _buildEmotionalContext(fortuneResult, sessionId, userUuid) {
        const context = {
            fortune_type: fortuneResult.fortune_type || 'daily',
            time_of_day: this._getTimeContext(),
            session_history: this._getSessionHistory(sessionId),
            user_preferences: userUuid ? this._getUserPreferences(userUuid) : null,
            tags: []
        };

        // 컨텍스트 태그 생성
        context.tags.push(`type_${context.fortune_type}`);
        context.tags.push(`time_${context.time_of_day}`);
        
        if (context.session_history?.recent_emotions?.length > 0) {
            context.tags.push('has_history');
        }

        return context;
    }

    /**
     * 감정 블렌딩 (주감정 + 보조감정)
     */
    _blendEmotions(baseEmotion, context, intensity) {
        const primary = baseEmotion.emotion;
        const secondary = baseEmotion.secondary || null;
        const confidence = baseEmotion.confidence || 0.7;

        // 세션 히스토리 고려
        const history = context.session_history?.recent_emotions || [];
        if (history.length > 0) {
            const lastEmotion = history[history.length - 1];
            // 같은 감정 반복 방지
            if (lastEmotion === primary && Math.random() < 0.3) {
                const alternativeEmotions = this._getAlternativeEmotions(primary);
                if (alternativeEmotions.length > 0) {
                    const alternative = alternativeEmotions[Math.floor(Math.random() * alternativeEmotions.length)];
                    return {
                        primary: alternative,
                        secondary: primary,
                        confidence: confidence * 0.8,
                        blend_ratio: 0.7
                    };
                }
            }
        }

        return {
            primary,
            secondary,
            confidence,
            blend_ratio: secondary ? 0.8 : 1.0
        };
    }

    /**
     * 모션 선택
     */
    _selectMotion(emotionMix, fortuneType, context) {
        const motionMap = {
            'daily': {
                'joy': ['blessing', 'celebration'],
                'comfort': ['blessing'],
                'neutral': ['thinking_pose'],
                'concern': ['thinking_pose'],
                'mystical': ['crystal_gaze']
            },
            'tarot': {
                'mystical': ['card_draw'],
                'joy': ['card_draw', 'blessing'],
                'concern': ['card_draw', 'thinking_pose']
            },
            'zodiac': {
                'mystical': ['crystal_gaze'],
                'joy': ['crystal_gaze', 'blessing'],
                'thinking': ['crystal_gaze', 'thinking_pose']
            },
            'oriental': {
                'mystical': ['special_reading'],
                'comfort': ['special_reading', 'blessing'],
                'thinking': ['special_reading', 'thinking_pose']
            }
        };

        const typeMap = motionMap[fortuneType] || motionMap['daily'];
        const emotionMotions = typeMap[emotionMix.primary] || ['thinking_pose'];
        
        // 랜덤 선택 (가중치 적용 가능)
        return emotionMotions[Math.floor(Math.random() * emotionMotions.length)];
    }

    /**
     * 상황별 메시지 생성
     */
    _generateContextualMessage(emotionMix, fortuneResult) {
        const messageBank = {
            'joy': [
                "와! 정말 좋은 결과가 나왔어요! ✨",
                "행복한 에너지가 넘쳐나고 있어요! 💫",
                "이런 좋은 운세는 정말 기뻐할 일이에요!"
            ],
            'comfort': [
                "따뜻한 위로의 메시지를 전해드려요 🌸",
                "마음이 편안해지는 결과네요 😌",
                "차분하고 안정적인 에너지가 느껴져요"
            ],
            'mystical': [
                "신비로운 운명의 흐름이 느껴져요... ✨",
                "우주의 깊은 메시지가 담겨있어요 🌟",
                "신비로운 힘이 당신을 인도하고 있어요"
            ],
            'concern': [
                "조금 신중하게 접근해보세요 💭",
                "차분히 생각해볼 시간이 필요해 보여요",
                "마음을 차분히 가져보시길 바라요"
            ],
            'thinking': [
                "깊이 생각해볼만한 메시지가 있어요 🤔",
                "신중한 판단이 필요한 시기인 것 같아요",
                "지혜롭게 선택하시길 바라요"
            ],
            'surprise': [
                "예상치 못한 놀라운 결과예요! 😲",
                "정말 특별한 메시지가 나왔어요!",
                "이런 결과는 흔하지 않아요!"
            ],
            'playful': [
                "재미있는 결과가 나왔어요! 😄",
                "즐거운 일들이 기다리고 있을 것 같아요!",
                "유쾌한 에너지가 느껴져요!"
            ]
        };

        const messages = messageBank[emotionMix.primary] || messageBank['neutral'] || ["운세를 확인해보세요"];
        return messages[Math.floor(Math.random() * messages.length)];
    }

    /**
     * Live2D 파라미터 생성
     */
    _generateLive2DParameters(emotionMix, intensity) {
        const emotionParameters = {
            'joy': {
                ParamEyeLSmile: intensity,
                ParamEyeRSmile: intensity,
                ParamMouthForm: intensity * 1.2,
                ParamMouthUp: intensity * 0.8,
                ParamCheek: intensity * 0.6
            },
            'comfort': {
                ParamEyeLSmile: intensity * 0.7,
                ParamEyeRSmile: intensity * 0.7,
                ParamMouthForm: intensity * 0.8,
                ParamMouthUp: intensity * 0.4,
                ParamCheek: intensity * 0.3
            },
            'mystical': {
                ParamEyeLOpen: 1.0 - intensity * 0.3,
                ParamEyeROpen: 1.0 - intensity * 0.3,
                ParamEyeLForm: intensity * 0.4,
                ParamEyeRForm: intensity * 0.4,
                ParamEyeEffect: intensity * 0.8
            },
            'concern': {
                ParamBrowLY: -intensity * 0.6,
                ParamBrowRY: -intensity * 0.6,
                ParamBrowLAngle: -intensity * 0.4,
                ParamBrowRAngle: intensity * 0.4,
                ParamMouthDown: intensity * 0.5
            },
            'thinking': {
                ParamEyeLOpen: 1.0 - intensity * 0.5,
                ParamEyeROpen: 1.0 - intensity * 0.5,
                ParamEyeBallY: -intensity * 0.4,
                ParamBrowLY: -intensity * 0.3,
                ParamBrowRY: -intensity * 0.3
            },
            'surprise': {
                ParamEyeLOpen: 1.0 + intensity * 0.5,
                ParamEyeROpen: 1.0 + intensity * 0.5,
                ParamBrowLY: intensity * 0.6,
                ParamBrowRY: intensity * 0.6,
                ParamA: intensity * 0.8
            },
            'playful': {
                ParamEyeLSmile: intensity * 0.9,
                ParamEyeRSmile: intensity * 0.9,
                ParamMouthForm: intensity * 1.3,
                ParamMouthUp: intensity,
                ParamEyeBallX: Math.sin(Date.now() * 0.01) * 0.3,
                ParamCheek: intensity * 0.8
            }
        };

        const baseParams = emotionParameters[emotionMix.primary] || {};
        
        // 보조 감정 블렌딩
        if (emotionMix.secondary && emotionParameters[emotionMix.secondary]) {
            const secondaryParams = emotionParameters[emotionMix.secondary];
            const blendRatio = emotionMix.blend_ratio || 0.8;
            
            Object.keys(secondaryParams).forEach(param => {
                if (baseParams[param] !== undefined) {
                    baseParams[param] = baseParams[param] * blendRatio + 
                                      secondaryParams[param] * (1 - blendRatio);
                } else {
                    baseParams[param] = secondaryParams[param] * (1 - blendRatio);
                }
            });
        }

        return baseParams;
    }

    /**
     * 지속 시간 계산
     */
    _calculateDuration(emotionMix, intensity) {
        const baseDuration = {
            'joy': 4000,
            'comfort': 5000,
            'mystical': 7000,
            'concern': 4500,
            'thinking': 6000,
            'surprise': 2500,
            'playful': 3500
        };

        const duration = baseDuration[emotionMix.primary] || 4000;
        return Math.floor(duration * (0.8 + intensity * 0.4));
    }

    /**
     * 페이드 타이밍 계산
     */
    _calculateFadeTiming(emotionMix) {
        const fadeTimings = {
            'joy': { fadeIn: 0.3, fadeOut: 0.8 },
            'comfort': { fadeIn: 0.6, fadeOut: 0.4 },
            'mystical': { fadeIn: 1.0, fadeOut: 0.8 },
            'concern': { fadeIn: 0.4, fadeOut: 0.6 },
            'thinking': { fadeIn: 0.8, fadeOut: 0.5 },
            'surprise': { fadeIn: 0.1, fadeOut: 0.3 },
            'playful': { fadeIn: 0.3, fadeOut: 0.5 }
        };

        return fadeTimings[emotionMix.primary] || { fadeIn: 0.5, fadeOut: 0.5 };
    }

    /**
     * 히스토리 업데이트
     */
    _updateEmotionHistory(sessionId, emotionMix) {
        if (!this.emotionHistory.has(sessionId)) {
            this.emotionHistory.set(sessionId, { recent_emotions: [], timestamps: [] });
        }
        
        const history = this.emotionHistory.get(sessionId);
        history.recent_emotions.push(emotionMix.primary);
        history.timestamps.push(Date.now());

        // 최근 10개만 유지
        if (history.recent_emotions.length > 10) {
            history.recent_emotions = history.recent_emotions.slice(-10);
            history.timestamps = history.timestamps.slice(-10);
        }
    }

    /**
     * 보조 메서드들
     */
    _getTimeContext() {
        const hour = new Date().getHours();
        if (hour >= 5 && hour < 12) return 'morning';
        if (hour >= 12 && hour < 17) return 'afternoon';
        if (hour >= 17 && hour < 22) return 'evening';
        return 'night';
    }

    _getSessionHistory(sessionId) {
        return this.emotionHistory.get(sessionId) || { recent_emotions: [] };
    }

    _getUserPreferences(userUuid) {
        return this.userPreferences.get(userUuid) || null;
    }

    _getAlternativeEmotions(primaryEmotion) {
        const alternatives = {
            'joy': ['comfort', 'playful'],
            'comfort': ['neutral', 'thinking'],
            'mystical': ['thinking', 'concern'],
            'concern': ['thinking', 'neutral'],
            'thinking': ['mystical', 'concern'],
            'surprise': ['joy', 'playful'],
            'playful': ['joy', 'surprise']
        };
        
        return alternatives[primaryEmotion] || ['neutral'];
    }

    _isPositiveCard(meaning, reversed) {
        const positiveKeywords = ['success', 'happiness', 'love', 'prosperity', 'growth', 'healing'];
        const hasPositive = positiveKeywords.some(keyword => meaning.toLowerCase().includes(keyword));
        return reversed ? !hasPositive : hasPositive;
    }

    _isNegativeCard(meaning, reversed) {
        const negativeKeywords = ['death', 'devil', 'tower', 'conflict', 'loss', 'betrayal'];
        const hasNegative = negativeKeywords.some(keyword => meaning.toLowerCase().includes(keyword));
        return reversed ? !hasNegative : hasNegative;
    }

    _calculateElementalBalance(elements) {
        // 오행 균형 계산 로직
        const total = Object.values(elements).reduce((sum, val) => sum + (val || 0), 0);
        if (total === 0) return { harmony_score: 50 };

        const values = Object.values(elements);
        const mean = total / values.length;
        const variance = values.reduce((sum, val) => sum + Math.pow((val || 0) - mean, 2), 0) / values.length;
        const harmony = Math.max(0, 100 - Math.sqrt(variance) * 2);

        return { harmony_score: harmony };
    }
}

// Export for both Node.js and browser environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Live2DEmotionEngine };
} else if (typeof window !== 'undefined') {
    window.Live2DEmotionEngine = Live2DEmotionEngine;
}
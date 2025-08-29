/**
 * Live2D 감정 매핑 시스템 (JavaScript)
 * 
 * 텍스트와 컨텍스트를 기반으로 Live2D 표정과 모션을 결정
 * Reference의 감정 처리 로직을 확장 구현
 */

class EmotionMapper {
    constructor() {
        // 감정 키워드 매핑 (한국어 + 영어)
        this.EMOTION_KEYWORDS = {
            'joy': {
                korean: ['기쁘', '행복', '즐거', '좋아', '웃음', '신나', '만족', '기분좋', '환상', '대박'],
                english: ['happy', 'joy', 'glad', 'cheerful', 'delighted', 'pleased', 'excited', 'wonderful'],
                intensity: {
                    high: ['완전', '정말', '너무', '엄청', '최고', '대박', 'amazing', 'fantastic', 'incredible'],
                    medium: ['좀', '조금', '약간', 'quite', 'pretty', 'fairly'],
                    low: ['살짝', '약간', 'slightly', 'somewhat']
                }
            },
            'sadness': {
                korean: ['슬퍼', '우울', '아쉬움', '눈물', '안타까', '서글픈', '속상', '쓸쓸', '허무'],
                english: ['sad', 'sorrow', 'unhappy', 'depressed', 'melancholy', 'disappointed', 'grief'],
                intensity: {
                    high: ['너무', '정말', '엄청', 'extremely', 'terribly', 'deeply'],
                    medium: ['좀', '약간', 'quite', 'rather'],
                    low: ['살짝', 'slightly', 'a bit']
                }
            },
            'anger': {
                korean: ['화나', '짜증', '분노', '싫어', '열받', '빡쳐', '억울', '불만'],
                english: ['angry', 'mad', 'furious', 'irritated', 'annoyed', 'frustrated', 'upset'],
                intensity: {
                    high: ['완전', '정말', '너무', 'extremely', 'totally', 'absolutely'],
                    medium: ['좀', '약간', 'quite', 'pretty'],
                    low: ['살짝', 'slightly', 'a little']
                }
            },
            'surprise': {
                korean: ['놀라', '깜짝', '어?', '오?', '헐', '와', '어머', '세상에'],
                english: ['surprise', 'shocked', 'amazed', 'astonished', 'stunned', 'wow', 'oh'],
                intensity: {
                    high: ['완전', '정말', 'totally', 'completely', 'absolutely'],
                    medium: ['좀', '약간', 'quite', 'pretty'],
                    low: ['살짝', 'slightly']
                }
            },
            'fear': {
                korean: ['무서', '걱정', '두려', '불안', '겁나', '떨려', '조심'],
                english: ['afraid', 'scared', 'worried', 'anxious', 'fearful', 'nervous', 'concerned'],
                intensity: {
                    high: ['너무', '정말', 'extremely', 'terribly'],
                    medium: ['좀', '약간', 'quite', 'rather'],
                    low: ['살짝', 'slightly']
                }
            },
            'neutral': {
                korean: ['그냥', '보통', '평소', '일반', '그럭저럭', '무난'],
                english: ['normal', 'usual', 'ordinary', 'regular', 'typical', 'average'],
                intensity: {
                    high: [],
                    medium: ['약간', 'somewhat'],
                    low: ['조금', 'slightly']
                }
            },
            'mystical': {
                korean: ['신비', '마법', '신성', '운명', '우주', '영적', '차크라', '기운'],
                english: ['mystical', 'magical', 'spiritual', 'cosmic', 'divine', 'sacred', 'mysterious'],
                intensity: {
                    high: ['완전히', '절대적', 'completely', 'absolutely'],
                    medium: ['좀', '약간', 'quite'],
                    low: ['살짝', 'slightly']
                }
            },
            'thinking': {
                korean: ['생각', '고민', '궁금', '의문', '머리', '분석', '이해'],
                english: ['think', 'wonder', 'consider', 'ponder', 'analyze', 'understand'],
                intensity: {
                    high: ['깊이', '철저히', 'deeply', 'thoroughly'],
                    medium: ['좀', '약간', 'quite'],
                    low: ['살짝', 'slightly']
                }
            }
        };

        // 컨텍스트별 감정 가중치
        this.CONTEXT_WEIGHTS = {
            'fortune_daily': {
                'joy': 1.2,
                'sadness': 0.8,
                'mystical': 0.5
            },
            'fortune_tarot': {
                'mystical': 1.5,
                'thinking': 1.3,
                'surprise': 1.1
            },
            'fortune_zodiac': {
                'mystical': 1.4,
                'joy': 1.1,
                'thinking': 1.2
            },
            'fortune_oriental': {
                'mystical': 1.6,
                'thinking': 1.4,
                'neutral': 1.1
            },
            'conversation': {
                'joy': 1.1,
                'surprise': 1.2,
                'thinking': 1.0
            }
        };

        // 모션 매핑
        this.MOTION_MAPPING = {
            'mao_pro': {
                'joy': {
                    primary: 'mtn_03',  // 기쁨 모션
                    secondary: 'mtn_01', // 대체 모션
                    special: 'special_01' // 특수 기쁨
                },
                'sadness': {
                    primary: 'mtn_02',
                    secondary: 'mtn_04',
                    special: null
                },
                'anger': {
                    primary: 'mtn_04',
                    secondary: 'mtn_02',
                    special: null
                },
                'surprise': {
                    primary: 'special_02',
                    secondary: 'mtn_03',
                    special: 'special_03'
                },
                'fear': {
                    primary: 'mtn_02',
                    secondary: 'mtn_04',
                    special: null
                },
                'mystical': {
                    primary: 'special_01',
                    secondary: 'mtn_01',
                    special: 'special_03'
                },
                'thinking': {
                    primary: 'mtn_01',
                    secondary: 'mtn_04',
                    special: null
                },
                'neutral': {
                    primary: 'mtn_01',
                    secondary: 'mtn_02',
                    special: null
                }
            },
            'shizuku': {
                'joy': {
                    primary: '03',
                    secondary: '01',
                    special: null
                },
                'sadness': {
                    primary: '02',
                    secondary: '04',
                    special: null
                },
                'anger': {
                    primary: '04',
                    secondary: '02',
                    special: null
                },
                'surprise': {
                    primary: '03',
                    secondary: '01',
                    special: null
                },
                'fear': {
                    primary: '02',
                    secondary: '04',
                    special: null
                },
                'mystical': {
                    primary: '01',
                    secondary: '03',
                    special: null
                },
                'thinking': {
                    primary: '01',
                    secondary: '02',
                    special: null
                },
                'neutral': {
                    primary: '01',
                    secondary: '02',
                    special: null
                }
            }
        };
    }

    /**
     * 텍스트와 컨텍스트를 분석하여 감정을 매핑
     * @param {string} text - 분석할 텍스트
     * @param {Object} context - 컨텍스트 정보
     * @param {string} modelName - Live2D 모델 이름
     * @returns {Object} 감정 매핑 결과
     */
    mapEmotionsToExpressions(text, context = {}, modelName = 'mao_pro') {
        const analysis = this.analyzeText(text);
        const contextType = context.type || 'conversation';
        const fortuneResult = context.fortuneResult || {};
        
        // 컨텍스트 기반 감정 조정
        const adjustedEmotions = this.adjustEmotionsForContext(analysis.emotions, contextType, fortuneResult);
        
        // 주 감정과 부 감정 결정
        const primaryEmotion = this.selectPrimaryEmotion(adjustedEmotions);
        const secondaryEmotion = this.selectSecondaryEmotion(adjustedEmotions, primaryEmotion);
        
        // 강도 계산
        const intensity = this.calculateIntensity(text, primaryEmotion, analysis.intensityModifiers);
        
        // 표정 인덱스 매핑
        const expressionIndex = this.getExpressionIndex(primaryEmotion, modelName);
        
        // 모션 선택
        const motion = this.selectMotion(primaryEmotion, intensity, modelName, contextType);
        
        // 지속 시간 계산
        const duration = this.calculateDuration(primaryEmotion, intensity, contextType);
        
        // 페이드 타이밍
        const fadeTiming = this.getFadeTiming(primaryEmotion, intensity);
        
        return {
            primaryEmotion,
            secondaryEmotion,
            intensity,
            expressionIndex,
            motion,
            duration,
            fadeTiming,
            confidence: analysis.confidence,
            contextType,
            analysis: {
                detectedKeywords: analysis.keywords,
                intensityModifiers: analysis.intensityModifiers,
                rawEmotions: analysis.emotions
            }
        };
    }

    /**
     * 텍스트 분석
     * @param {string} text - 분석할 텍스트
     * @returns {Object} 분석 결과
     */
    analyzeText(text) {
        const lowerText = text.toLowerCase();
        const emotions = new Map();
        const keywords = [];
        const intensityModifiers = [];
        let confidence = 0.5;

        // 각 감정별로 키워드 검색
        for (const [emotion, data] of Object.entries(this.EMOTION_KEYWORDS)) {
            let emotionScore = 0;
            let keywordCount = 0;

            // 한국어 키워드 검색
            for (const keyword of data.korean) {
                if (lowerText.includes(keyword)) {
                    emotionScore += 1.0;
                    keywordCount++;
                    keywords.push({ keyword, emotion, language: 'korean' });
                }
            }

            // 영어 키워드 검색
            for (const keyword of data.english) {
                if (lowerText.includes(keyword)) {
                    emotionScore += 1.0;
                    keywordCount++;
                    keywords.push({ keyword, emotion, language: 'english' });
                }
            }

            // 강도 수정자 검색
            for (const [intensityLevel, modifiers] of Object.entries(data.intensity)) {
                for (const modifier of modifiers) {
                    if (lowerText.includes(modifier)) {
                        const multiplier = intensityLevel === 'high' ? 1.5 : 
                                         intensityLevel === 'medium' ? 1.2 : 0.8;
                        emotionScore *= multiplier;
                        intensityModifiers.push({ modifier, level: intensityLevel, emotion });
                    }
                }
            }

            if (emotionScore > 0) {
                emotions.set(emotion, emotionScore);
                confidence = Math.min(1.0, confidence + (keywordCount * 0.1));
            }
        }

        // 기본 감정이 없으면 neutral 추가
        if (emotions.size === 0) {
            emotions.set('neutral', 0.5);
        }

        return {
            emotions,
            keywords,
            intensityModifiers,
            confidence: Math.min(1.0, confidence)
        };
    }

    /**
     * 컨텍스트에 따른 감정 조정
     * @param {Map} emotions - 감정 스코어 맵
     * @param {string} contextType - 컨텍스트 타입
     * @param {Object} fortuneResult - 운세 결과 (있는 경우)
     * @returns {Map} 조정된 감정 스코어
     */
    adjustEmotionsForContext(emotions, contextType, fortuneResult) {
        const adjusted = new Map(emotions);
        const weights = this.CONTEXT_WEIGHTS[contextType] || {};

        // 컨텍스트 가중치 적용
        for (const [emotion, weight] of Object.entries(weights)) {
            if (adjusted.has(emotion)) {
                adjusted.set(emotion, adjusted.get(emotion) * weight);
            }
        }

        // 운세 결과 기반 조정
        if (fortuneResult && fortuneResult.overall_fortune) {
            const score = fortuneResult.overall_fortune.score || 50;
            
            if (score >= 80) {
                this.boostEmotion(adjusted, 'joy', 1.3);
            } else if (score >= 60) {
                this.boostEmotion(adjusted, 'joy', 1.1);
            } else if (score <= 30) {
                this.boostEmotion(adjusted, 'sadness', 1.2);
            }
        }

        return adjusted;
    }

    /**
     * 감정 부스트
     * @param {Map} emotions - 감정 맵
     * @param {string} emotion - 부스트할 감정
     * @param {number} multiplier - 배수
     */
    boostEmotion(emotions, emotion, multiplier) {
        const current = emotions.get(emotion) || 0;
        emotions.set(emotion, current * multiplier);
    }

    /**
     * 주 감정 선택
     * @param {Map} emotions - 감정 스코어 맵
     * @returns {string} 주 감정
     */
    selectPrimaryEmotion(emotions) {
        let maxEmotion = 'neutral';
        let maxScore = 0;

        for (const [emotion, score] of emotions.entries()) {
            if (score > maxScore) {
                maxScore = score;
                maxEmotion = emotion;
            }
        }

        return maxEmotion;
    }

    /**
     * 부 감정 선택
     * @param {Map} emotions - 감정 스코어 맵
     * @param {string} primaryEmotion - 주 감정
     * @returns {string|null} 부 감정
     */
    selectSecondaryEmotion(emotions, primaryEmotion) {
        let secondaryEmotion = null;
        let secondaryScore = 0;

        for (const [emotion, score] of emotions.entries()) {
            if (emotion !== primaryEmotion && score > secondaryScore && score > 0.3) {
                secondaryScore = score;
                secondaryEmotion = emotion;
            }
        }

        return secondaryEmotion;
    }

    /**
     * 감정 강도 계산
     * @param {string} text - 원본 텍스트
     * @param {string} emotion - 감정
     * @param {Array} intensityModifiers - 강도 수정자
     * @returns {number} 강도 (0.0 ~ 1.0)
     */
    calculateIntensity(text, emotion, intensityModifiers) {
        let baseIntensity = 0.6;

        // 감정별 기본 강도
        const baseIntensities = {
            'joy': 0.7,
            'sadness': 0.6,
            'anger': 0.8,
            'surprise': 0.9,
            'fear': 0.7,
            'mystical': 0.8,
            'thinking': 0.5,
            'neutral': 0.4
        };

        baseIntensity = baseIntensities[emotion] || 0.6;

        // 강도 수정자 적용
        for (const modifier of intensityModifiers) {
            if (modifier.emotion === emotion || !modifier.emotion) {
                switch (modifier.level) {
                    case 'high':
                        baseIntensity = Math.min(1.0, baseIntensity * 1.3);
                        break;
                    case 'medium':
                        baseIntensity = Math.min(1.0, baseIntensity * 1.1);
                        break;
                    case 'low':
                        baseIntensity = Math.max(0.1, baseIntensity * 0.8);
                        break;
                }
            }
        }

        // 텍스트 길이에 따른 조정
        const textLength = text.length;
        if (textLength > 100) {
            baseIntensity = Math.min(1.0, baseIntensity * 1.1);
        } else if (textLength < 20) {
            baseIntensity = Math.max(0.3, baseIntensity * 0.9);
        }

        return Math.min(1.0, Math.max(0.1, baseIntensity));
    }

    /**
     * 표정 인덱스 매핑
     * @param {string} emotion - 감정
     * @param {string} modelName - 모델 이름
     * @returns {number} 표정 인덱스
     */
    getExpressionIndex(emotion, modelName) {
        // 기본 mao_pro 매핑 (model_dict.json 기준)
        const emotionIndexMap = {
            'mao_pro': {
                'neutral': 0,
                'fear': 1,
                'sadness': 1,
                'anger': 2,
                'disgust': 2,
                'joy': 3,
                'surprise': 3,
                'mystical': 0,  // neutral과 동일
                'thinking': 1   // fear와 동일한 눈 표정
            },
            'shizuku': {
                'neutral': 0,
                'joy': 1,
                'sadness': 2,
                'anger': 3,
                'surprise': 1,
                'fear': 2,
                'mystical': 0,
                'thinking': 0
            }
        };

        const modelMap = emotionIndexMap[modelName] || emotionIndexMap['mao_pro'];
        return modelMap[emotion] || 0;
    }

    /**
     * 모션 선택
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     * @param {string} modelName - 모델 이름
     * @param {string} contextType - 컨텍스트 타입
     * @returns {Object} 모션 정보
     */
    selectMotion(emotion, intensity, modelName, contextType) {
        const modelMotions = this.MOTION_MAPPING[modelName] || this.MOTION_MAPPING['mao_pro'];
        const emotionMotions = modelMotions[emotion] || modelMotions['neutral'];

        let selectedMotion = emotionMotions.primary;

        // 강도와 컨텍스트에 따른 모션 선택
        if (intensity > 0.8 && emotionMotions.special) {
            selectedMotion = emotionMotions.special;
        } else if (intensity < 0.4 && emotionMotions.secondary) {
            selectedMotion = emotionMotions.secondary;
        }

        // 컨텍스트별 특수 모션
        if (contextType.startsWith('fortune_') && emotion === 'mystical') {
            selectedMotion = emotionMotions.special || selectedMotion;
        }

        return {
            motionGroup: this.getMotionGroup(selectedMotion, modelName),
            motionIndex: this.getMotionIndex(selectedMotion, modelName),
            file: selectedMotion
        };
    }

    /**
     * 모션 그룹 결정
     * @param {string} motionFile - 모션 파일명
     * @param {string} modelName - 모델 이름
     * @returns {string} 모션 그룹
     */
    getMotionGroup(motionFile, modelName) {
        if (motionFile.startsWith('special_')) {
            return 'Special';
        }
        return 'Idle';
    }

    /**
     * 모션 인덱스 결정
     * @param {string} motionFile - 모션 파일명
     * @param {string} modelName - 모델 이름
     * @returns {number} 모션 인덱스
     */
    getMotionIndex(motionFile, modelName) {
        // 파일명에서 숫자 추출
        const match = motionFile.match(/\d+/);
        if (match) {
            return parseInt(match[0]) - 1; // 0-based index
        }
        return 0;
    }

    /**
     * 지속 시간 계산
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     * @param {string} contextType - 컨텍스트 타입
     * @returns {number} 지속 시간 (ms)
     */
    calculateDuration(emotion, intensity, contextType) {
        const baseDurations = {
            'joy': 3000,
            'sadness': 4000,
            'anger': 2500,
            'surprise': 2000,
            'fear': 3500,
            'mystical': 5000,
            'thinking': 4000,
            'neutral': 3000
        };

        let duration = baseDurations[emotion] || 3000;

        // 강도에 따른 조정
        duration *= (0.7 + intensity * 0.6);

        // 컨텍스트에 따른 조정
        if (contextType.startsWith('fortune_')) {
            duration *= 1.2; // 운세 컨텍스트에서는 더 길게
        }

        return Math.round(duration);
    }

    /**
     * 페이드 타이밍 계산
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     * @returns {Object} 페이드 타이밍
     */
    getFadeTiming(emotion, intensity) {
        const fadeTimings = {
            'joy': { fadeIn: 0.3, fadeOut: 0.7 },
            'sadness': { fadeIn: 0.8, fadeOut: 0.4 },
            'anger': { fadeIn: 0.2, fadeOut: 0.6 },
            'surprise': { fadeIn: 0.1, fadeOut: 0.8 },
            'fear': { fadeIn: 0.4, fadeOut: 0.3 },
            'mystical': { fadeIn: 1.0, fadeOut: 1.0 },
            'thinking': { fadeIn: 0.6, fadeOut: 0.5 },
            'neutral': { fadeIn: 0.5, fadeOut: 0.5 }
        };

        const baseTiming = fadeTimings[emotion] || fadeTimings['neutral'];
        
        // 강도에 따른 페이드 속도 조정
        const intensityFactor = 0.8 + (intensity * 0.4);

        return {
            fadeIn: baseTiming.fadeIn * intensityFactor,
            fadeOut: baseTiming.fadeOut * intensityFactor
        };
    }

    /**
     * 감정 키워드 추가
     * @param {string} emotion - 감정
     * @param {string} language - 언어 ('korean' 또는 'english')
     * @param {Array} keywords - 추가할 키워드들
     */
    addEmotionKeywords(emotion, language, keywords) {
        if (!this.EMOTION_KEYWORDS[emotion]) {
            this.EMOTION_KEYWORDS[emotion] = {
                korean: [],
                english: [],
                intensity: { high: [], medium: [], low: [] }
            };
        }
        
        if (!this.EMOTION_KEYWORDS[emotion][language]) {
            this.EMOTION_KEYWORDS[emotion][language] = [];
        }
        
        this.EMOTION_KEYWORDS[emotion][language].push(...keywords);
    }

    /**
     * 모델별 모션 매핑 추가
     * @param {string} modelName - 모델 이름
     * @param {Object} motionMap - 모션 매핑
     */
    addModelMotionMapping(modelName, motionMap) {
        this.MOTION_MAPPING[modelName] = motionMap;
    }
}

module.exports = EmotionMapper;
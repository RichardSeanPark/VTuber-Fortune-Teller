/**
 * Live2D 모델 설정 및 매핑 파일
 * 
 * 실제 Live2D 모델 파일들의 상세 설정과 매핑 정보
 * JavaScript로 작성하여 프론트엔드와 호환성 확보
 */

const LIVE2D_MODELS = {
    // mao_pro 모델 설정
    mao_pro: {
        name: "마오 프로",
        modelPath: "/static/live2d/mao_pro/runtime/mao_pro.model3.json",
        
        // 8가지 표정 매핑 (실제 exp 파일과 연동)
        emotions: {
            neutral: {
                id: 0,
                name: "중립",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_01.exp3.json",
                parameters: {
                    ParamEyeLOpen: 1.0,
                    ParamEyeROpen: 1.0,
                    ParamEyeLSmile: 0.0,
                    ParamEyeRSmile: 0.0,
                    ParamMouthForm: 0.0,
                    ParamBrowLY: 0.0,
                    ParamBrowRY: 0.0
                },
                fadeInTime: 0.5,
                fadeOutTime: 0.5
            },
            joy: {
                id: 1,
                name: "기쁨",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_02.exp3.json",
                parameters: {
                    ParamEyeLSmile: 1.0,
                    ParamEyeRSmile: 1.0,
                    ParamMouthForm: 1.0,
                    ParamMouthUp: 0.8,
                    ParamCheek: 0.5
                },
                fadeInTime: 0.3,
                fadeOutTime: 0.8
            },
            thinking: {
                id: 2,
                name: "사색",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_03.exp3.json",
                parameters: {
                    ParamEyeLOpen: 0.6,
                    ParamEyeROpen: 0.6,
                    ParamEyeBallY: -0.3,
                    ParamBrowLY: -0.2,
                    ParamBrowRY: -0.2
                },
                fadeInTime: 0.8,
                fadeOutTime: 0.5
            },
            concern: {
                id: 3,
                name: "걱정",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_04.exp3.json",
                parameters: {
                    ParamBrowLY: -0.5,
                    ParamBrowRY: -0.5,
                    ParamBrowLAngle: -0.3,
                    ParamBrowRAngle: 0.3,
                    ParamMouthDown: 0.4
                },
                fadeInTime: 0.4,
                fadeOutTime: 0.6
            },
            surprise: {
                id: 4,
                name: "놀람",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_05.exp3.json",
                parameters: {
                    ParamEyeLOpen: 1.4,
                    ParamEyeROpen: 1.4,
                    ParamBrowLY: 0.5,
                    ParamBrowRY: 0.5,
                    ParamA: 0.8
                },
                fadeInTime: 0.1,
                fadeOutTime: 0.3
            },
            mystical: {
                id: 5,
                name: "신비",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_06.exp3.json",
                parameters: {
                    ParamEyeLOpen: 0.8,
                    ParamEyeROpen: 0.8,
                    ParamEyeLForm: 0.3,
                    ParamEyeRForm: 0.3,
                    ParamEyeEffect: 0.7
                },
                fadeInTime: 1.0,
                fadeOutTime: 0.8
            },
            comfort: {
                id: 6,
                name: "위로",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_07.exp3.json",
                parameters: {
                    ParamEyeLSmile: 0.6,
                    ParamEyeRSmile: 0.6,
                    ParamMouthForm: 0.7,
                    ParamMouthUp: 0.3,
                    ParamCheek: 0.2
                },
                fadeInTime: 0.6,
                fadeOutTime: 0.4
            },
            playful: {
                id: 7,
                name: "장난",
                expressionFile: "/static/live2d/mao_pro/runtime/expressions/exp_08.exp3.json",
                parameters: {
                    ParamEyeLSmile: 0.8,
                    ParamEyeRSmile: 0.8,
                    ParamMouthForm: 1.2,
                    ParamMouthUp: 1.0,
                    ParamEyeBallX: 0.2,
                    ParamCheek: 0.8
                },
                fadeInTime: 0.3,
                fadeOutTime: 0.5
            }
        },

        // 모션 매핑 (실제 모션 파일과 연동)
        motions: {
            greeting: {
                id: "greeting",
                name: "인사",
                motionFile: "/static/live2d/mao_pro/runtime/motions/mtn_01.motion3.json",
                duration: 3000,
                loop: false,
                priority: "normal"
            },
            card_draw: {
                id: "card_draw", 
                name: "카드 뽑기",
                motionFile: "/static/live2d/mao_pro/runtime/motions/mtn_02.motion3.json",
                duration: 4000,
                loop: false,
                priority: "high"
            },
            crystal_gaze: {
                id: "crystal_gaze",
                name: "수정구 응시", 
                motionFile: "/static/live2d/mao_pro/runtime/motions/mtn_03.motion3.json",
                duration: 5000,
                loop: true,
                priority: "normal"
            },
            blessing: {
                id: "blessing",
                name: "축복",
                motionFile: "/static/live2d/mao_pro/runtime/motions/mtn_04.motion3.json",
                duration: 4000,
                loop: false,
                priority: "high"
            },
            special_reading: {
                id: "special_reading",
                name: "특별 해석",
                motionFile: "/static/live2d/mao_pro/runtime/motions/special_01.motion3.json",
                duration: 6000,
                loop: false,
                priority: "high"
            },
            thinking_pose: {
                id: "thinking_pose",
                name: "생각하는 자세",
                motionFile: "/static/live2d/mao_pro/runtime/motions/special_02.motion3.json",
                duration: 5000,
                loop: true,
                priority: "low"
            },
            celebration: {
                id: "celebration",
                name: "축하",
                motionFile: "/static/live2d/mao_pro/runtime/motions/special_03.motion3.json",
                duration: 4500,
                loop: false,
                priority: "high"
            }
        },

        // Hit Area 매핑
        hitAreas: {
            head: "HitAreaHead",
            body: "HitAreaBody"
        },

        // 물리 시뮬레이션 설정
        physics: {
            enabled: true,
            physicsFile: "/static/live2d/mao_pro/runtime/mao_pro.physics3.json"
        },

        // 포즈 설정
        pose: {
            enabled: true,
            poseFile: "/static/live2d/mao_pro/runtime/mao_pro.pose3.json"
        }
    },

    // shizuku 모델 설정
    shizuku: {
        name: "시즈쿠",
        modelPath: "/static/live2d/shizuku/runtime/shizuku.model3.json",

        // shizuku는 표정 파일이 없으므로 파라미터로 직접 제어
        emotions: {
            neutral: {
                id: 0,
                name: "중립",
                parameters: {
                    PARAM_EYE_L_OPEN: 1.0,
                    PARAM_EYE_R_OPEN: 1.0,
                    PARAM_MOUTH_OPEN_Y: 0.0
                },
                fadeInTime: 0.5,
                fadeOutTime: 0.5
            },
            joy: {
                id: 1,
                name: "기쁨", 
                parameters: {
                    PARAM_EYE_L_OPEN: 0.8,
                    PARAM_EYE_R_OPEN: 0.8,
                    PARAM_MOUTH_OPEN_Y: 0.6
                },
                fadeInTime: 0.3,
                fadeOutTime: 0.8
            },
            thinking: {
                id: 2,
                name: "사색",
                parameters: {
                    PARAM_EYE_L_OPEN: 0.6,
                    PARAM_EYE_R_OPEN: 0.6,
                    PARAM_MOUTH_OPEN_Y: 0.1
                },
                fadeInTime: 0.8,
                fadeOutTime: 0.5
            }
        },

        // shizuku 모션 매핑
        motions: {
            greeting: {
                id: "greeting",
                name: "인사",
                motionFile: "/static/live2d/shizuku/runtime/motion/01.motion3.json",
                duration: 3000,
                loop: false,
                priority: "normal"
            },
            tap_reaction: {
                id: "tap_reaction",
                name: "터치 반응",
                motionFile: "/static/live2d/shizuku/runtime/motion/02.motion3.json", 
                duration: 2000,
                loop: false,
                priority: "high"
            },
            flick_reaction: {
                id: "flick_reaction",
                name: "플릭 반응",
                motionFile: "/static/live2d/shizuku/runtime/motion/03.motion3.json",
                duration: 2500,
                loop: false,
                priority: "normal"
            },
            idle: {
                id: "idle",
                name: "대기",
                motionFile: "/static/live2d/shizuku/runtime/motion/04.motion3.json",
                duration: 4000,
                loop: true,
                priority: "low"
            }
        },

        // Hit Area 매핑 (shizuku는 hit area 없음)
        hitAreas: {},

        // 물리 시뮬레이션 설정
        physics: {
            enabled: true,
            physicsFile: "/static/live2d/shizuku/runtime/shizuku.physics3.json"
        },

        // 포즈 설정  
        pose: {
            enabled: true,
            poseFile: "/static/live2d/shizuku/runtime/shizuku.pose3.json"
        }
    }
};

// 운세별 상세 감정/모션 매핑
const FORTUNE_EMOTION_MAPPING = {
    // 일반 운세
    daily: {
        excellent: {
            emotion: "joy",
            motion: "celebration",
            intensity: 1.0,
            messages: [
                "와! 정말 좋은 운세가 나왔어요! ✨",
                "오늘은 특별한 날이 될 것 같네요! 💫",
                "이런 훌륭한 운세는 정말 드물어요!"
            ],
            duration: 5000
        },
        good: {
            emotion: "comfort",
            motion: "blessing",
            intensity: 0.8,
            messages: [
                "좋은 운세가 나왔어요! 😊",
                "긍정적인 에너지가 느껴져요!",
                "오늘 하루 기대해봐도 좋겠어요!"
            ],
            duration: 4000
        },
        normal: {
            emotion: "neutral",
            motion: "thinking_pose",
            intensity: 0.5,
            messages: [
                "평범하지만 안정적인 하루가 될 것 같아요.",
                "차분하게 하루를 보내시면 좋겠어요.",
                "작은 행복을 찾아보는 하루가 되길 바라요."
            ],
            duration: 3000
        },
        caution: {
            emotion: "concern",
            motion: "thinking_pose",
            intensity: 0.6,
            messages: [
                "조금 주의가 필요한 하루예요.",
                "신중하게 행동하시는 것이 좋겠어요.", 
                "차분하게 하루를 보내시길 바라요."
            ],
            duration: 4000
        },
        bad: {
            emotion: "concern",
            motion: "thinking_pose",
            intensity: 0.8,
            messages: [
                "오늘은 조금 조심스러운 하루가 될 것 같아요.",
                "마음을 차분히 가지시길 바라요.",
                "힘든 일이 있어도 이겨낼 수 있을 거예요."
            ],
            duration: 5000
        }
    },

    // 타로 카드
    tarot: {
        positive: {
            emotion: "mystical",
            motion: "card_draw",
            intensity: 0.9,
            messages: [
                "카드가 긍정적인 메시지를 전해주고 있어요...",
                "신비로운 타로의 힘이 당신을 도와줄 거예요.",
                "카드들이 희망적인 미래를 보여주고 있어요."
            ],
            duration: 6000
        },
        neutral: {
            emotion: "mystical",
            motion: "card_draw",
            intensity: 0.6,
            messages: [
                "카드가 말하는 메시지를 들어보세요...",
                "신비로운 타로의 힘이 느껴져요.",
                "카드들이 특별한 이야기를 들려주고 있어요."
            ],
            duration: 5000
        },
        warning: {
            emotion: "mystical",
            motion: "card_draw",
            intensity: 0.7,
            messages: [
                "카드가 조심스러운 메시지를 전하고 있어요...",
                "타로가 주의깊게 살펴보라고 말하고 있어요.",
                "카드의 경고를 귀담아 들어보세요."
            ],
            duration: 6000
        }
    },

    // 별자리 운세
    zodiac: {
        favorable: {
            emotion: "mystical",
            motion: "crystal_gaze",
            intensity: 0.9,
            messages: [
                "별들이 당신에게 유리한 배치를 보이고 있어요...",
                "우주의 에너지가 당신을 응원하고 있어요.",
                "별자리가 행운의 메시지를 보내고 있어요."
            ],
            duration: 7000
        },
        neutral: {
            emotion: "mystical", 
            motion: "crystal_gaze",
            intensity: 0.6,
            messages: [
                "별들이 전하는 메시지를 읽고 있어요...",
                "우주의 에너지가 당신을 둘러싸고 있어요.",
                "별자리의 신비로운 힘이 느껴져요."
            ],
            duration: 6000
        },
        challenging: {
            emotion: "mystical",
            motion: "crystal_gaze", 
            intensity: 0.7,
            messages: [
                "별들이 시련을 통한 성장을 말하고 있어요...",
                "우주가 당신의 강인함을 시험하고 있어요.",
                "별자리가 인내의 메시지를 전하고 있어요."
            ],
            duration: 7000
        }
    },

    // 사주 운세
    oriental: {
        auspicious: {
            emotion: "mystical",
            motion: "special_reading",
            intensity: 1.0,
            messages: [
                "사주에서 길한 기운이 강하게 느껴져요...",
                "당신의 운명이 매우 밝게 빛나고 있어요.",
                "오랜 지혜가 행운의 길을 보여주고 있어요."
            ],
            duration: 8000
        },
        balanced: {
            emotion: "mystical",
            motion: "special_reading", 
            intensity: 0.6,
            messages: [
                "사주에 담긴 깊은 의미를 해석하고 있어요...",
                "당신의 운명이 사주에 새겨져 있네요.",
                "오랜 지혜가 담긴 사주의 비밀을 읽고 있어요."
            ],
            duration: 7000
        },
        cautionary: {
            emotion: "mystical",
            motion: "special_reading",
            intensity: 0.8, 
            messages: [
                "사주에서 신중함을 권하고 있어요...",
                "운명의 흐름을 잘 읽어 대처하시길 바라요.",
                "지혜로운 선택이 필요한 시기예요."
            ],
            duration: 8000
        }
    }
};

// TTS 연동을 위한 립싱크 파라미터 매핑
const LIPSYNC_PARAMETERS = {
    mao_pro: {
        // 모음별 입 모양 파라미터
        vowels: {
            'a': { ParamA: 1.0, ParamI: 0.0, ParamU: 0.0, ParamE: 0.0, ParamO: 0.0 },
            'i': { ParamA: 0.0, ParamI: 1.0, ParamU: 0.0, ParamE: 0.0, ParamO: 0.0 },
            'u': { ParamA: 0.0, ParamI: 0.0, ParamU: 1.0, ParamE: 0.0, ParamO: 0.0 },
            'e': { ParamA: 0.0, ParamI: 0.0, ParamU: 0.0, ParamE: 1.0, ParamO: 0.0 },
            'o': { ParamA: 0.0, ParamI: 0.0, ParamU: 0.0, ParamE: 0.0, ParamO: 1.0 },
            'closed': { ParamA: 0.0, ParamI: 0.0, ParamU: 0.0, ParamE: 0.0, ParamO: 0.0 }
        },
        // 감정별 음성 톤 조절
        emotionalTone: {
            joy: { pitch: 1.1, speed: 1.05, volume: 0.9 },
            concern: { pitch: 0.95, speed: 0.95, volume: 0.8 },
            mystical: { pitch: 1.0, speed: 0.9, volume: 0.85 },
            comfort: { pitch: 1.05, speed: 1.0, volume: 0.9 },
            surprise: { pitch: 1.15, speed: 1.1, volume: 0.95 },
            playful: { pitch: 1.1, speed: 1.1, volume: 0.95 },
            thinking: { pitch: 0.98, speed: 0.92, volume: 0.8 },
            neutral: { pitch: 1.0, speed: 1.0, volume: 0.85 }
        }
    },
    shizuku: {
        vowels: {
            'open': { PARAM_MOUTH_OPEN_Y: 1.0 },
            'closed': { PARAM_MOUTH_OPEN_Y: 0.0 }
        },
        emotionalTone: {
            joy: { pitch: 1.08, speed: 1.03, volume: 0.9 },
            thinking: { pitch: 0.97, speed: 0.94, volume: 0.8 },
            neutral: { pitch: 1.0, speed: 1.0, volume: 0.85 }
        }
    }
};

// 리소스 최적화 설정
const RESOURCE_OPTIMIZATION = {
    // 텍스처 품질 설정 (디바이스별)
    textureQuality: {
        high: { scale: 1.0, compression: false },
        medium: { scale: 0.75, compression: true },
        low: { scale: 0.5, compression: true }
    },
    
    // 모델 로딩 최적화
    loading: {
        preloadTextures: true,
        enableCache: true,
        cacheMaxAge: 3600000, // 1 hour
        lazyLoadMotions: true,
        compressMotions: true
    },

    // 메모리 관리
    memory: {
        maxActiveModels: 2,
        gcInterval: 300000, // 5 minutes
        texturePoolSize: 10,
        motionCacheSize: 20
    }
};

// Export for both Node.js and browser environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        LIVE2D_MODELS,
        FORTUNE_EMOTION_MAPPING,
        LIPSYNC_PARAMETERS,
        RESOURCE_OPTIMIZATION
    };
} else if (typeof window !== 'undefined') {
    window.Live2DModelConfig = {
        LIVE2D_MODELS,
        FORTUNE_EMOTION_MAPPING,  
        LIPSYNC_PARAMETERS,
        RESOURCE_OPTIMIZATION
    };
}
/**
 * Live2D 캐릭터 실시간 상태 관리 시스템 (JavaScript)
 * 
 * 캐릭터의 감정, 표정, 모션 상태를 실시간으로 추적하고 관리
 * 상태 변경 이력 및 동기화 지원
 */

const EventEmitter = require('events');

class CharacterState {
    /**
     * 캐릭터 상태 데이터 구조
     * @param {string} sessionId - 세션 ID
     * @param {string} modelName - Live2D 모델 이름
     */
    constructor(sessionId, modelName = 'mao_pro') {
        this.sessionId = sessionId;
        this.modelName = modelName;
        this.createdAt = new Date().toISOString();
        this.lastUpdate = new Date().toISOString();
        
        // 현재 상태
        this.currentState = {
            emotion: 'neutral',
            intensity: 0.5,
            expressionIndex: 0,
            motionGroup: 'Idle',
            motionIndex: 0,
            isMotionPlaying: false,
            mood: 'neutral',  // 장기적 기분 상태
            energy: 0.7,     // 에너지 레벨
            focus: 0.6       // 집중도
        };
        
        // 상태 변경 이력 (최대 50개 유지)
        this.stateHistory = [];
        this.maxHistorySize = 50;
        
        // 예약된 상태 변경 (타이머 기반)
        this.scheduledChanges = new Map();
        
        // 실시간 파라미터
        this.live2dParameters = new Map();
        
        // 성능 메트릭
        this.metrics = {
            stateChanges: 0,
            avgResponseTime: 0,
            lastResponseTime: 0,
            errorCount: 0
        };
    }

    /**
     * 현재 상태 반환
     * @returns {Object} 현재 캐릭터 상태
     */
    getCurrentState() {
        return {
            sessionId: this.sessionId,
            modelName: this.modelName,
            currentState: { ...this.currentState },
            lastUpdate: this.lastUpdate,
            live2dParameters: Object.fromEntries(this.live2dParameters),
            metrics: { ...this.metrics }
        };
    }

    /**
     * 감정 상태 업데이트
     * @param {string} emotion - 감정 ('joy', 'sadness', 'anger', 'surprise', 'fear', 'neutral', 'mystical', 'thinking')
     * @param {number} intensity - 강도 (0.0 ~ 1.0)
     * @param {number} duration - 지속 시간 (ms)
     * @param {Object} fadeTiming - 페이드 타이밍
     * @returns {Object} 상태 변경 결과
     */
    updateEmotion(emotion, intensity = 0.5, duration = 3000, fadeTiming = null) {
        const startTime = Date.now();
        
        try {
            // 이전 상태 백업
            const previousState = { ...this.currentState };
            
            // 새로운 상태 적용
            this.currentState.emotion = emotion;
            this.currentState.intensity = Math.max(0, Math.min(1, intensity));
            
            // 감정에 따른 표정 인덱스 매핑
            this.currentState.expressionIndex = this._getExpressionIndexForEmotion(emotion);
            
            // 기분 상태 조정 (장기적 영향)
            this._adjustMood(emotion, intensity);
            
            // 에너지 및 집중도 조정
            this._adjustEnergyAndFocus(emotion, intensity);
            
            // Live2D 파라미터 계산
            const parameters = this._calculateLive2DParameters(emotion, intensity);
            this._updateLive2DParameters(parameters);
            
            // 상태 이력에 추가
            this._addToHistory('emotion_update', {
                emotion,
                intensity,
                duration,
                fadeTiming,
                previousState,
                parameters: Object.fromEntries(this.live2dParameters)
            });
            
            // 예약된 상태 복원 (지속 시간 후)
            if (duration > 0) {
                this._scheduleStateRestore(duration, previousState);
            }
            
            this.lastUpdate = new Date().toISOString();
            this.metrics.stateChanges++;
            this.metrics.lastResponseTime = Date.now() - startTime;
            this._updateAvgResponseTime();
            
            return {
                success: true,
                sessionId: this.sessionId,
                emotion,
                intensity,
                expressionIndex: this.currentState.expressionIndex,
                parameters: Object.fromEntries(this.live2dParameters),
                duration,
                fadeTiming: fadeTiming || this._getDefaultFadeTiming(emotion),
                timestamp: this.lastUpdate
            };
            
        } catch (error) {
            this.metrics.errorCount++;
            return {
                success: false,
                error: error.message,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 모션 트리거
     * @param {string} motionGroup - 모션 그룹
     * @param {number} motionIndex - 모션 인덱스
     * @param {number} priority - 우선순위 (1~3, 높을수록 우선)
     * @returns {Object} 모션 트리거 결과
     */
    triggerMotion(motionGroup = 'Idle', motionIndex = 0, priority = 1) {
        const startTime = Date.now();
        
        try {
            // 현재 재생 중인 모션과 우선순위 비교
            if (this.currentState.isMotionPlaying && priority <= 1) {
                return {
                    success: false,
                    reason: 'Higher priority motion is already playing',
                    sessionId: this.sessionId
                };
            }
            
            // 모션 상태 업데이트
            this.currentState.motionGroup = motionGroup;
            this.currentState.motionIndex = motionIndex;
            this.currentState.isMotionPlaying = true;
            
            // 모션 종료 타이머 설정 (추정 지속 시간)
            const estimatedDuration = this._estimateMotionDuration(motionGroup, motionIndex);
            this._scheduleMotionEnd(estimatedDuration);
            
            // 상태 이력에 추가
            this._addToHistory('motion_trigger', {
                motionGroup,
                motionIndex,
                priority,
                estimatedDuration
            });
            
            this.lastUpdate = new Date().toISOString();
            this.metrics.stateChanges++;
            this.metrics.lastResponseTime = Date.now() - startTime;
            this._updateAvgResponseTime();
            
            return {
                success: true,
                sessionId: this.sessionId,
                motionGroup,
                motionIndex,
                priority,
                estimatedDuration,
                timestamp: this.lastUpdate
            };
            
        } catch (error) {
            this.metrics.errorCount++;
            return {
                success: false,
                error: error.message,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Live2D 파라미터 직접 설정
     * @param {Object} parameters - 파라미터 맵 (파라미터명: 값)
     * @param {number} duration - 지속 시간 (ms)
     * @param {number} fadeIn - 페이드 인 시간 (초)
     * @param {number} fadeOut - 페이드 아웃 시간 (초)
     * @returns {Object} 파라미터 설정 결과
     */
    setLive2DParameters(parameters, duration = 1000, fadeIn = 0.5, fadeOut = 0.5) {
        const startTime = Date.now();
        
        try {
            // 이전 파라미터 백업
            const previousParameters = new Map(this.live2dParameters);
            
            // 새 파라미터 적용
            for (const [paramName, value] of Object.entries(parameters)) {
                this.live2dParameters.set(paramName, value);
            }
            
            // 상태 이력에 추가
            this._addToHistory('parameter_update', {
                parameters,
                duration,
                fadeIn,
                fadeOut,
                previousParameters: Object.fromEntries(previousParameters)
            });
            
            // 지속 시간 후 이전 상태로 복원 (선택사항)
            if (duration > 0) {
                this._scheduleParameterRestore(duration, previousParameters);
            }
            
            this.lastUpdate = new Date().toISOString();
            this.metrics.stateChanges++;
            this.metrics.lastResponseTime = Date.now() - startTime;
            this._updateAvgResponseTime();
            
            return {
                success: true,
                sessionId: this.sessionId,
                parameters: Object.fromEntries(this.live2dParameters),
                duration,
                fadeIn,
                fadeOut,
                timestamp: this.lastUpdate
            };
            
        } catch (error) {
            this.metrics.errorCount++;
            return {
                success: false,
                error: error.message,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 복합 상태 설정 (감정 + 모션 동시 적용)
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     * @param {string} motionGroup - 모션 그룹
     * @param {number} motionIndex - 모션 인덱스
     * @param {number} duration - 지속 시간
     * @returns {Object} 복합 상태 설정 결과
     */
    setCombinedState(emotion, intensity, motionGroup, motionIndex, duration = 3000) {
        try {
            const emotionResult = this.updateEmotion(emotion, intensity, duration);
            const motionResult = this.triggerMotion(motionGroup, motionIndex, 2);
            
            // 상태 이력에 복합 변경 기록
            this._addToHistory('combined_state', {
                emotion,
                intensity,
                motionGroup,
                motionIndex,
                duration,
                emotionResult,
                motionResult
            });
            
            return {
                success: emotionResult.success && motionResult.success,
                sessionId: this.sessionId,
                emotion: emotionResult,
                motion: motionResult,
                timestamp: this.lastUpdate
            };
            
        } catch (error) {
            this.metrics.errorCount++;
            return {
                success: false,
                error: error.message,
                sessionId: this.sessionId,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * 상태 이력 조회
     * @param {number} limit - 조회할 최대 개수
     * @param {string} type - 필터링할 타입 (선택사항)
     * @returns {Array} 상태 이력 배열
     */
    getStateHistory(limit = 10, type = null) {
        let history = this.stateHistory;
        
        if (type) {
            history = history.filter(entry => entry.type === type);
        }
        
        return history
            .slice(-limit)
            .reverse(); // 최신 순으로 정렬
    }

    /**
     * 성능 메트릭 조회
     * @returns {Object} 성능 메트릭
     */
    getMetrics() {
        return {
            ...this.metrics,
            historySize: this.stateHistory.length,
            scheduledChanges: this.scheduledChanges.size,
            parameterCount: this.live2dParameters.size,
            uptime: Date.now() - new Date(this.createdAt).getTime(),
            healthScore: this._calculateHealthScore()
        };
    }

    /**
     * 상태 리셋
     * @param {boolean} keepHistory - 이력 유지 여부
     */
    reset(keepHistory = true) {
        // 예약된 변경 모두 취소
        for (const timerId of this.scheduledChanges.values()) {
            clearTimeout(timerId);
        }
        this.scheduledChanges.clear();
        
        // 상태 초기화
        this.currentState = {
            emotion: 'neutral',
            intensity: 0.5,
            expressionIndex: 0,
            motionGroup: 'Idle',
            motionIndex: 0,
            isMotionPlaying: false,
            mood: 'neutral',
            energy: 0.7,
            focus: 0.6
        };
        
        // 파라미터 초기화
        this.live2dParameters.clear();
        
        if (!keepHistory) {
            this.stateHistory = [];
        }
        
        this.lastUpdate = new Date().toISOString();
        
        // 리셋 이력 추가
        this._addToHistory('reset', {
            keepHistory,
            resetAt: this.lastUpdate
        });
    }

    // 내부 헬퍼 메서드들

    /**
     * 감정에 따른 표정 인덱스 매핑
     * @param {string} emotion - 감정
     * @returns {number} 표정 인덱스
     */
    _getExpressionIndexForEmotion(emotion) {
        const emotionMap = {
            'mao_pro': {
                'neutral': 0,
                'fear': 1,
                'sadness': 1,
                'anger': 2,
                'joy': 3,
                'surprise': 3,
                'mystical': 0,
                'thinking': 1
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
        
        const modelMap = emotionMap[this.modelName] || emotionMap['mao_pro'];
        return modelMap[emotion] || 0;
    }

    /**
     * 기분 상태 조정 (장기적 감정 상태)
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     */
    _adjustMood(emotion, intensity) {
        const moodImpact = {
            'joy': 0.3,
            'sadness': -0.2,
            'anger': -0.1,
            'surprise': 0.1,
            'fear': -0.15,
            'mystical': 0.05,
            'thinking': 0,
            'neutral': 0
        };
        
        const impact = (moodImpact[emotion] || 0) * intensity;
        
        // 현재 기분을 숫자로 변환
        const moodValues = { 'sad': -1, 'neutral': 0, 'happy': 1 };
        const currentMoodValue = moodValues[this.currentState.mood] || 0;
        
        // 새로운 기분 값 계산
        const newMoodValue = Math.max(-1, Math.min(1, currentMoodValue + impact * 0.1));
        
        // 기분 상태 문자열로 변환
        if (newMoodValue > 0.3) {
            this.currentState.mood = 'happy';
        } else if (newMoodValue < -0.3) {
            this.currentState.mood = 'sad';
        } else {
            this.currentState.mood = 'neutral';
        }
    }

    /**
     * 에너지 및 집중도 조정
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     */
    _adjustEnergyAndFocus(emotion, intensity) {
        const energyAdjustment = {
            'joy': 0.2,
            'anger': 0.3,
            'surprise': 0.4,
            'fear': -0.1,
            'sadness': -0.2,
            'thinking': -0.05,
            'mystical': 0.1,
            'neutral': 0
        };
        
        const focusAdjustment = {
            'thinking': 0.3,
            'mystical': 0.2,
            'fear': 0.1,
            'anger': -0.1,
            'joy': -0.05,
            'surprise': -0.2,
            'sadness': -0.1,
            'neutral': 0
        };
        
        const energyChange = (energyAdjustment[emotion] || 0) * intensity * 0.1;
        const focusChange = (focusAdjustment[emotion] || 0) * intensity * 0.1;
        
        this.currentState.energy = Math.max(0, Math.min(1, this.currentState.energy + energyChange));
        this.currentState.focus = Math.max(0, Math.min(1, this.currentState.focus + focusChange));
    }

    /**
     * Live2D 파라미터 계산
     * @param {string} emotion - 감정
     * @param {number} intensity - 강도
     * @returns {Object} 파라미터 맵
     */
    _calculateLive2DParameters(emotion, intensity) {
        const parameterMap = {
            'joy': {
                'ParamEyeLSmile': intensity,
                'ParamEyeRSmile': intensity,
                'ParamMouthForm': intensity * 1.2,
                'ParamMouthUp': intensity * 0.8,
                'ParamCheek': intensity * 0.6
            },
            'sadness': {
                'ParamBrowLY': -intensity * 0.6,
                'ParamBrowRY': -intensity * 0.6,
                'ParamEyeLOpen': 1.0 - intensity * 0.4,
                'ParamEyeROpen': 1.0 - intensity * 0.4,
                'ParamMouthDown': intensity * 0.5
            },
            'anger': {
                'ParamBrowLAngle': -intensity * 0.8,
                'ParamBrowRAngle': intensity * 0.8,
                'ParamBrowLY': -intensity * 0.4,
                'ParamBrowRY': -intensity * 0.4,
                'ParamMouthDown': intensity * 0.3
            },
            'surprise': {
                'ParamEyeLOpen': 1.0 + intensity * 0.5,
                'ParamEyeROpen': 1.0 + intensity * 0.5,
                'ParamBrowLY': intensity * 0.6,
                'ParamBrowRY': intensity * 0.6,
                'ParamMouthForm': intensity * 0.8
            },
            'fear': {
                'ParamBrowLY': -intensity * 0.3,
                'ParamBrowRY': -intensity * 0.3,
                'ParamEyeLOpen': 1.0 - intensity * 0.2,
                'ParamEyeROpen': 1.0 - intensity * 0.2,
                'ParamBodyAngleZ': intensity * 2.0
            },
            'thinking': {
                'ParamEyeLOpen': 1.0 - intensity * 0.3,
                'ParamEyeROpen': 1.0 - intensity * 0.3,
                'ParamEyeBallY': -intensity * 0.4,
                'ParamBrowLY': -intensity * 0.2,
                'ParamBrowRY': -intensity * 0.2
            },
            'mystical': {
                'ParamEyeLForm': intensity * 0.4,
                'ParamEyeRForm': intensity * 0.4,
                'ParamEyeEffect': intensity * 0.8,
                'ParamBodyAngleY': Math.sin(Date.now() / 1000) * intensity * 3.0
            },
            'neutral': {
                'ParamEyeLOpen': 1.0,
                'ParamEyeROpen': 1.0,
                'ParamMouthForm': 0,
                'ParamBrowLY': 0,
                'ParamBrowRY': 0
            }
        };
        
        return parameterMap[emotion] || parameterMap['neutral'];
    }

    /**
     * Live2D 파라미터 업데이트
     * @param {Object} parameters - 파라미터 맵
     */
    _updateLive2DParameters(parameters) {
        for (const [paramName, value] of Object.entries(parameters)) {
            this.live2dParameters.set(paramName, value);
        }
    }

    /**
     * 기본 페이드 타이밍 반환
     * @param {string} emotion - 감정
     * @returns {Object} 페이드 타이밍
     */
    _getDefaultFadeTiming(emotion) {
        const fadeTimings = {
            'joy': { fadeIn: 0.3, fadeOut: 0.7 },
            'sadness': { fadeIn: 0.8, fadeOut: 0.4 },
            'anger': { fadeIn: 0.2, fadeOut: 0.6 },
            'surprise': { fadeIn: 0.1, fadeOut: 0.8 },
            'fear': { fadeIn: 0.4, fadeOut: 0.3 },
            'thinking': { fadeIn: 0.6, fadeOut: 0.5 },
            'mystical': { fadeIn: 1.0, fadeOut: 1.0 },
            'neutral': { fadeIn: 0.5, fadeOut: 0.5 }
        };
        
        return fadeTimings[emotion] || fadeTimings['neutral'];
    }

    /**
     * 상태 이력에 추가
     * @param {string} type - 변경 타입
     * @param {Object} data - 변경 데이터
     */
    _addToHistory(type, data) {
        const entry = {
            type,
            data,
            timestamp: new Date().toISOString(),
            sessionId: this.sessionId
        };
        
        this.stateHistory.push(entry);
        
        // 이력 크기 제한
        if (this.stateHistory.length > this.maxHistorySize) {
            this.stateHistory.shift();
        }
    }

    /**
     * 상태 복원 예약
     * @param {number} delay - 지연 시간 (ms)
     * @param {Object} previousState - 이전 상태
     */
    _scheduleStateRestore(delay, previousState) {
        const timerId = setTimeout(() => {
            this.currentState.emotion = previousState.emotion;
            this.currentState.intensity = previousState.intensity;
            this.currentState.expressionIndex = previousState.expressionIndex;
            
            this.scheduledChanges.delete(timerId);
            this.lastUpdate = new Date().toISOString();
            
            this._addToHistory('scheduled_restore', {
                delay,
                restoredState: previousState
            });
        }, delay);
        
        this.scheduledChanges.set(timerId, timerId);
    }

    /**
     * 모션 종료 예약
     * @param {number} duration - 모션 지속 시간
     */
    _scheduleMotionEnd(duration) {
        const timerId = setTimeout(() => {
            this.currentState.isMotionPlaying = false;
            this.scheduledChanges.delete(timerId);
            this.lastUpdate = new Date().toISOString();
            
            this._addToHistory('motion_end', {
                duration,
                endedAt: this.lastUpdate
            });
        }, duration);
        
        this.scheduledChanges.set(timerId, timerId);
    }

    /**
     * 파라미터 복원 예약
     * @param {number} delay - 지연 시간
     * @param {Map} previousParameters - 이전 파라미터
     */
    _scheduleParameterRestore(delay, previousParameters) {
        const timerId = setTimeout(() => {
            this.live2dParameters.clear();
            for (const [paramName, value] of previousParameters) {
                this.live2dParameters.set(paramName, value);
            }
            
            this.scheduledChanges.delete(timerId);
            this.lastUpdate = new Date().toISOString();
            
            this._addToHistory('parameter_restore', {
                delay,
                restoredParameters: Object.fromEntries(previousParameters)
            });
        }, delay);
        
        this.scheduledChanges.set(timerId, timerId);
    }

    /**
     * 모션 지속 시간 추정
     * @param {string} motionGroup - 모션 그룹
     * @param {number} motionIndex - 모션 인덱스
     * @returns {number} 추정 지속 시간 (ms)
     */
    _estimateMotionDuration(motionGroup, motionIndex) {
        const durationMap = {
            'Idle': 3000,
            'Special': 5000,
            'Greeting': 2000,
            'Thinking': 4000
        };
        
        return durationMap[motionGroup] || 3000;
    }

    /**
     * 평균 응답 시간 업데이트
     */
    _updateAvgResponseTime() {
        if (this.metrics.stateChanges > 1) {
            this.metrics.avgResponseTime = (
                (this.metrics.avgResponseTime * (this.metrics.stateChanges - 1) + this.metrics.lastResponseTime) /
                this.metrics.stateChanges
            );
        } else {
            this.metrics.avgResponseTime = this.metrics.lastResponseTime;
        }
    }

    /**
     * 시스템 헬스 스코어 계산
     * @returns {number} 헬스 스코어 (0.0 ~ 1.0)
     */
    _calculateHealthScore() {
        let score = 1.0;
        
        // 에러율 기준 감점
        if (this.metrics.stateChanges > 0) {
            const errorRate = this.metrics.errorCount / this.metrics.stateChanges;
            score -= errorRate * 0.5;
        }
        
        // 응답 시간 기준 감점
        if (this.metrics.avgResponseTime > 100) {  // 100ms 기준
            score -= Math.min(0.3, (this.metrics.avgResponseTime - 100) / 1000);
        }
        
        // 예약된 변경 수 기준 감점 (너무 많으면 시스템 부하)
        if (this.scheduledChanges.size > 10) {
            score -= Math.min(0.2, (this.scheduledChanges.size - 10) / 50);
        }
        
        return Math.max(0, Math.min(1, score));
    }
}

/**
 * 캐릭터 상태 매니저 - 다중 세션 관리
 */
class CharacterStateManager extends EventEmitter {
    constructor() {
        super();
        this.sessions = new Map(); // sessionId → CharacterState
        this.globalMetrics = {
            totalSessions: 0,
            activeSessions: 0,
            totalStateChanges: 0,
            averageHealthScore: 1.0
        };
    }

    /**
     * 새 세션 생성
     * @param {string} sessionId - 세션 ID
     * @param {string} modelName - 모델 이름
     * @returns {CharacterState} 캐릭터 상태 인스턴스
     */
    createSession(sessionId, modelName = 'mao_pro') {
        if (this.sessions.has(sessionId)) {
            return this.sessions.get(sessionId);
        }
        
        const characterState = new CharacterState(sessionId, modelName);
        this.sessions.set(sessionId, characterState);
        
        this.globalMetrics.totalSessions++;
        this.globalMetrics.activeSessions++;
        
        this.emit('session_created', { sessionId, modelName });
        
        return characterState;
    }

    /**
     * 세션 조회
     * @param {string} sessionId - 세션 ID
     * @returns {CharacterState|null} 캐릭터 상태 인스턴스
     */
    getSession(sessionId) {
        return this.sessions.get(sessionId) || null;
    }

    /**
     * 세션 삭제
     * @param {string} sessionId - 세션 ID
     * @returns {boolean} 삭제 성공 여부
     */
    removeSession(sessionId) {
        const session = this.sessions.get(sessionId);
        if (session) {
            // 예약된 작업들 정리
            session.reset(false);
            this.sessions.delete(sessionId);
            
            this.globalMetrics.activeSessions--;
            this.emit('session_removed', { sessionId });
            
            return true;
        }
        return false;
    }

    /**
     * 모든 활성 세션 조회
     * @returns {Array} 세션 ID 배열
     */
    getActiveSessions() {
        return Array.from(this.sessions.keys());
    }

    /**
     * 글로벌 메트릭 업데이트 및 반환
     * @returns {Object} 글로벌 메트릭
     */
    getGlobalMetrics() {
        let totalStateChanges = 0;
        let totalHealthScore = 0;
        let sessionCount = 0;
        
        for (const session of this.sessions.values()) {
            const metrics = session.getMetrics();
            totalStateChanges += metrics.stateChanges;
            totalHealthScore += metrics.healthScore;
            sessionCount++;
        }
        
        this.globalMetrics.totalStateChanges = totalStateChanges;
        this.globalMetrics.averageHealthScore = sessionCount > 0 ? totalHealthScore / sessionCount : 1.0;
        
        return { ...this.globalMetrics };
    }

    /**
     * 세션별 상태 요약
     * @returns {Array} 세션 상태 배열
     */
    getAllSessionStates() {
        return Array.from(this.sessions.entries()).map(([sessionId, state]) => ({
            sessionId,
            ...state.getCurrentState(),
            metrics: state.getMetrics()
        }));
    }

    /**
     * 비활성 세션 정리
     * @param {number} inactiveThreshold - 비활성 기준 (ms)
     * @returns {number} 정리된 세션 수
     */
    cleanupInactiveSessions(inactiveThreshold = 30 * 60 * 1000) { // 30분
        const now = Date.now();
        const toRemove = [];
        
        for (const [sessionId, state] of this.sessions) {
            const lastUpdateTime = new Date(state.lastUpdate).getTime();
            if (now - lastUpdateTime > inactiveThreshold) {
                toRemove.push(sessionId);
            }
        }
        
        for (const sessionId of toRemove) {
            this.removeSession(sessionId);
        }
        
        this.emit('cleanup_completed', { removedCount: toRemove.length });
        
        return toRemove.length;
    }
}

module.exports = {
    CharacterState,
    CharacterStateManager
};
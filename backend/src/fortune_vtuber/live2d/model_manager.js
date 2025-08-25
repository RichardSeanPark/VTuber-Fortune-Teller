/**
 * Live2D 모델 관리 시스템 (JavaScript)
 * 
 * Live2D 모델의 메타데이터 관리 및 감정 매핑 처리
 * Reference의 Live2dModel 클래스를 JavaScript로 구현
 */

const fs = require('fs').promises;
const path = require('path');
const chardet = require('chardet');

class Live2dModelManager {
    /**
     * Live2D 모델 관리자 초기화
     * @param {string} modelsPath - 모델 파일들의 기본 경로
     * @param {string} modelDictPath - model_dict.json 파일 경로
     */
    constructor(modelsPath = "static/live2d", modelDictPath = "static/live2d/model_dict.json") {
        this.modelsPath = modelsPath;
        this.modelDictPath = modelDictPath;
        this.loadedModels = new Map(); // 모델 캐시
        this.emotionMappings = new Map(); // 감정 매핑 테이블
        this.modelDict = null;
    }

    /**
     * 초기화 - model_dict.json 로드
     */
    async initialize() {
        try {
            await this.loadModelDictionary();
            console.log('Live2D Model Manager initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Live2D Model Manager:', error);
            throw error;
        }
    }

    /**
     * model_dict.json 파일 로드
     */
    async loadModelDictionary() {
        try {
            const content = await this.loadFileContent(this.modelDictPath);
            this.modelDict = JSON.parse(content);
            
            // 모델별 감정 매핑 초기화
            for (const model of this.modelDict) {
                const emotionMap = {};
                for (const [key, value] of Object.entries(model.emotionMap || {})) {
                    emotionMap[key.toLowerCase()] = value;
                }
                this.emotionMappings.set(model.name, emotionMap);
            }
            
            console.log(`Loaded ${this.modelDict.length} models from dictionary`);
        } catch (error) {
            console.error('Failed to load model dictionary:', error);
            throw error;
        }
    }

    /**
     * 파일 내용을 인코딩 자동감지로 로드
     * @param {string} filePath - 파일 경로
     * @returns {string} 파일 내용
     */
    async loadFileContent(filePath) {
        const encodings = ['utf-8', 'utf8', 'ascii'];
        
        // 일반적인 인코딩으로 시도
        for (const encoding of encodings) {
            try {
                return await fs.readFile(filePath, encoding);
            } catch (error) {
                if (!error.message.includes('Invalid') && !error.message.includes('decode')) {
                    throw error; // 다른 종류의 에러는 즉시 throw
                }
            }
        }
        
        // 인코딩 자동 감지
        try {
            const buffer = await fs.readFile(filePath);
            const detected = chardet.detect(buffer);
            if (detected) {
                return buffer.toString(detected);
            }
        } catch (error) {
            console.warn('Encoding detection failed:', error);
        }
        
        throw new Error(`Failed to decode ${filePath} with any encoding`);
    }

    /**
     * Live2D 모델 메타데이터 로드 (.model3.json 파일 파싱)
     * @param {string} modelName - 모델 이름
     * @returns {Object} 모델 메타데이터
     */
    async loadModelMetadata(modelName) {
        try {
            // 캐시 확인
            if (this.loadedModels.has(modelName)) {
                return this.loadedModels.get(modelName);
            }

            // 모델 정보 검색
            const modelInfo = this.getModelInfo(modelName);
            if (!modelInfo) {
                throw new Error(`Model '${modelName}' not found in model dictionary`);
            }

            // .model3.json 파일 경로 구성
            const modelPath = path.resolve(modelInfo.url.replace(/^\//, ''));
            
            // 모델 파일 로드
            const modelContent = await this.loadFileContent(modelPath);
            const modelData = JSON.parse(modelContent);

            // 메타데이터 구성
            const metadata = {
                name: modelName,
                info: modelInfo,
                model3Data: modelData,
                expressions: this.extractExpressions(modelData),
                motions: this.extractMotions(modelData),
                parameters: this.extractParameters(modelData),
                hitAreas: this.extractHitAreas(modelData),
                emotionMap: this.emotionMappings.get(modelName) || {}
            };

            // 캐시에 저장
            this.loadedModels.set(modelName, metadata);
            console.log(`Model metadata loaded for: ${modelName}`);

            return metadata;
        } catch (error) {
            console.error(`Failed to load model metadata for ${modelName}:`, error);
            throw error;
        }
    }

    /**
     * 사용 가능한 Live2D 모델 목록 반환
     * @returns {Array} 모델 정보 배열
     */
    getModelInfo() {
        if (!this.modelDict) {
            throw new Error('Model dictionary not loaded. Call initialize() first.');
        }

        return this.modelDict.map(model => ({
            name: model.name,
            description: model.description || '',
            url: model.url,
            scale: model.kScale,
            initialPosition: {
                x: model.initialXshift || 0,
                y: model.initialYshift || 0
            },
            offset: {
                x: model.kXOffset || 0
            },
            idleMotionGroup: model.idleMotionGroupName || 'Idle',
            emotionCount: Object.keys(model.emotionMap || {}).length,
            availableEmotions: Object.keys(model.emotionMap || {})
        }));
    }

    /**
     * 특정 모델 정보 반환
     * @param {string} modelName - 모델 이름
     * @returns {Object|null} 모델 정보
     */
    getModelInfo(modelName) {
        if (!this.modelDict) {
            return null;
        }
        return this.modelDict.find(model => model.name === modelName) || null;
    }

    /**
     * 텍스트에서 감정 키워드 추출
     * @param {string} text - 텍스트
     * @param {string} modelName - 모델 이름 (기본값: mao_pro)
     * @returns {Array} 추출된 감정 인덱스 배열
     */
    extractEmotionKeywords(text, modelName = 'mao_pro') {
        const emotionMap = this.emotionMappings.get(modelName);
        if (!emotionMap) {
            console.warn(`No emotion mapping found for model: ${modelName}`);
            return [];
        }

        const emotions = [];
        const lowerText = text.toLowerCase();

        // [감정] 태그 패턴 검색
        let i = 0;
        while (i < lowerText.length) {
            if (lowerText[i] !== '[') {
                i++;
                continue;
            }
            
            for (const emotionKey of Object.keys(emotionMap)) {
                const emotionTag = `[${emotionKey}]`;
                if (lowerText.substring(i, i + emotionTag.length) === emotionTag) {
                    emotions.push(emotionMap[emotionKey]);
                    i += emotionTag.length - 1;
                    break;
                }
            }
            i++;
        }

        return emotions;
    }

    /**
     * 텍스트에서 감정 태그 제거
     * @param {string} text - 원본 텍스트
     * @param {string} modelName - 모델 이름 (기본값: mao_pro)
     * @returns {string} 정제된 텍스트
     */
    removeEmotionKeywords(text, modelName = 'mao_pro') {
        const emotionMap = this.emotionMappings.get(modelName);
        if (!emotionMap) {
            return text;
        }

        let cleanText = text;
        const lowerCleanText = cleanText.toLowerCase();

        for (const emotionKey of Object.keys(emotionMap)) {
            const emotionTag = `[${emotionKey}]`;
            const lowerEmotionTag = emotionTag.toLowerCase();
            
            while (lowerCleanText.includes(lowerEmotionTag)) {
                const index = lowerCleanText.indexOf(lowerEmotionTag);
                cleanText = cleanText.substring(0, index) + cleanText.substring(index + emotionTag.length);
                lowerCleanText = lowerCleanText.substring(0, index) + lowerCleanText.substring(index + emotionTag.length);
            }
        }

        return cleanText.trim();
    }

    /**
     * 표정 정보 추출
     * @param {Object} modelData - model3.json 데이터
     * @returns {Array} 표정 정보 배열
     */
    extractExpressions(modelData) {
        const expressions = modelData.FileReferences?.Expressions || [];
        return expressions.map((exp, index) => ({
            index,
            name: exp.Name,
            file: exp.File
        }));
    }

    /**
     * 모션 정보 추출
     * @param {Object} modelData - model3.json 데이터
     * @returns {Object} 모션 그룹별 정보
     */
    extractMotions(modelData) {
        const motions = modelData.FileReferences?.Motions || {};
        const motionGroups = {};
        
        for (const [groupName, motionList] of Object.entries(motions)) {
            motionGroups[groupName] = motionList.map((motion, index) => ({
                index,
                file: motion.File,
                fadeIn: motion.FadeIn || 500,
                fadeOut: motion.FadeOut || 500
            }));
        }
        
        return motionGroups;
    }

    /**
     * 파라미터 그룹 정보 추출
     * @param {Object} modelData - model3.json 데이터
     * @returns {Array} 파라미터 그룹 배열
     */
    extractParameters(modelData) {
        const groups = modelData.Groups || [];
        return groups.map(group => ({
            name: group.Name,
            target: group.Target,
            ids: group.Ids || []
        }));
    }

    /**
     * 히트 영역 정보 추출
     * @param {Object} modelData - model3.json 데이터
     * @returns {Array} 히트 영역 배열
     */
    extractHitAreas(modelData) {
        const hitAreas = modelData.HitAreas || [];
        return hitAreas.map(area => ({
            id: area.Id,
            name: area.Name || ''
        }));
    }

    /**
     * 모델 캐시 클리어
     * @param {string} modelName - 특정 모델만 클리어 (선택사항)
     */
    clearCache(modelName = null) {
        if (modelName) {
            this.loadedModels.delete(modelName);
            console.log(`Cache cleared for model: ${modelName}`);
        } else {
            this.loadedModels.clear();
            console.log('All model cache cleared');
        }
    }

    /**
     * 감정 문자열 생성 (AI 프롬프트용)
     * @param {string} modelName - 모델 이름
     * @returns {string} 감정 문자열
     */
    getEmotionString(modelName = 'mao_pro') {
        const emotionMap = this.emotionMappings.get(modelName);
        if (!emotionMap) {
            return '';
        }
        
        return Object.keys(emotionMap)
            .map(key => `[${key}]`)
            .join(', ');
    }

    /**
     * 모델 상태 통계 반환
     * @returns {Object} 통계 정보
     */
    getStats() {
        return {
            totalModels: this.modelDict ? this.modelDict.length : 0,
            loadedModels: this.loadedModels.size,
            emotionMappings: this.emotionMappings.size,
            availableModels: this.modelDict ? this.modelDict.map(m => m.name) : []
        };
    }
}

module.exports = Live2dModelManager;
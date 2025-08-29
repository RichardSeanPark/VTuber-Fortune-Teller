/**
 * 운세 API 서비스
 * 백엔드 운세 API와 통신을 담당
 */

import { API_ENDPOINTS } from '../utils/constants';

class FortuneService {
  constructor() {
    this.baseURL = API_ENDPOINTS.BASE_URL;
  }

  /**
   * API 요청 헬퍼 메서드
   */
  async apiRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    console.log(`[FortuneService] API 요청 시작: ${url}`);

    try {
      const response = await fetch(url, {
        ...defaultOptions,
        ...options,
      });

      console.log(`[FortuneService] API 응답 상태: ${response.status}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        console.error(`[FortuneService] API 오류 응답:`, { status: response.status, errorData, url });
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log(`[FortuneService] API 요청 성공: ${endpoint}`, data);
      return data;
    } catch (error) {
      console.error(`[FortuneService] API 요청 실패: ${endpoint}`, {
        url,
        error: error.message,
        baseURL: this.baseURL,
        endpoint
      });
      
      // 네트워크 연결 오류 또는 CORS 오류일 가능성 확인
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(`서버 연결 실패: ${this.baseURL} (네트워크 오류 또는 CORS 문제)`);
      }
      
      throw error;
    }
  }

  /**
   * 일일 운세 요청
   */
  async getDailyFortune(userData) {
    const requestData = {
      birth_date: userData.birthDate,
      gender: userData.gender || 'unknown',
      name: userData.name || 'Anonymous'
    };

    return await this.apiRequest('/api/v1/fortune/daily', {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
  }

  /**
   * 타로 운세 요청
   */
  async getTarotFortune(userData, selectedCards = []) {
    const requestData = {
      birth_date: userData.birthDate,
      gender: userData.gender || 'unknown',
      name: userData.name || 'Anonymous',
      question: userData.question || '',
      selected_cards: selectedCards.map(card => card.id || card)
    };

    return await this.apiRequest('/api/v1/fortune/tarot', {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
  }

  /**
   * 별자리 운세 요청
   */
  async getZodiacFortune(userData) {
    const zodiacSign = userData.zodiacSign || this.getZodiacSign(userData.birthDate);
    
    return await this.apiRequest(`/api/v1/fortune/zodiac/${zodiacSign}?period=daily`, {
      method: 'GET'
    });
  }

  /**
   * 동양 운세 (사주) 요청
   */
  async getSajuFortune(userData) {
    const requestData = {
      birth_date: userData.birthDate,
      birth_time: userData.birthTime || '12:00',
      gender: userData.gender || 'unknown',
      name: userData.name || 'Anonymous',
      lunar_calendar: userData.lunarCalendar || false
    };

    return await this.apiRequest('/api/v1/fortune/oriental', {
      method: 'POST',
      body: JSON.stringify(requestData)
    });
  }

  /**
   * 운세 타입에 따른 통합 요청
   */
  async getFortuneByType(fortuneType, userData, extraData = {}) {
    switch (fortuneType) {
      case 'daily':
        return await this.getDailyFortune(userData);
      
      case 'tarot':
        return await this.getTarotFortune(userData, extraData.selectedCards);
      
      case 'zodiac':
        return await this.getZodiacFortune(userData);
      
      case 'saju':
        return await this.getSajuFortune(userData);
      
      default:
        throw new Error(`알 수 없는 운세 타입: ${fortuneType}`);
    }
  }

  /**
   * 운세 히스토리 조회
   */
  async getFortuneHistory(sessionId) {
    return await this.apiRequest(`/fortune/history/${sessionId}`, {
      method: 'GET'
    });
  }

  /**
   * 운세 결과 저장
   */
  async saveFortuneResult(sessionId, fortuneData) {
    return await this.apiRequest('/fortune/save', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        fortune_data: fortuneData
      })
    });
  }

  /**
   * 생년월일로 별자리 계산
   */
  getZodiacSign(birthDate) {
    const date = new Date(birthDate);
    const month = date.getMonth() + 1;
    const day = date.getDate();

    const zodiacRanges = [
      { sign: 'capricorn', start: [12, 22], end: [1, 19] },
      { sign: 'aquarius', start: [1, 20], end: [2, 18] },
      { sign: 'pisces', start: [2, 19], end: [3, 20] },
      { sign: 'aries', start: [3, 21], end: [4, 19] },
      { sign: 'taurus', start: [4, 20], end: [5, 20] },
      { sign: 'gemini', start: [5, 21], end: [6, 21] },
      { sign: 'cancer', start: [6, 22], end: [7, 22] },
      { sign: 'leo', start: [7, 23], end: [8, 22] },
      { sign: 'virgo', start: [8, 23], end: [9, 22] },
      { sign: 'libra', start: [9, 23], end: [10, 22] },
      { sign: 'scorpio', start: [10, 23], end: [11, 21] },
      { sign: 'sagittarius', start: [11, 22], end: [12, 21] }
    ];

    for (const range of zodiacRanges) {
      const [startMonth, startDay] = range.start;
      const [endMonth, endDay] = range.end;

      if (
        (month === startMonth && day >= startDay) ||
        (month === endMonth && day <= endDay)
      ) {
        return range.sign;
      }
    }

    return 'unknown';
  }

  /**
   * 사용자 데이터 유효성 검사
   */
  validateUserData(fortuneType, userData) {
    const errors = [];

    // 공통 필드 검사
    if (!userData.birthDate) {
      errors.push('생년월일을 입력해주세요.');
    } else {
      const birthDate = new Date(userData.birthDate);
      if (isNaN(birthDate.getTime())) {
        errors.push('올바른 생년월일 형식이 아닙니다.');
      }
    }

    // 운세 타입별 특별 검사
    switch (fortuneType) {
      case 'saju':
        if (!userData.birthTime) {
          errors.push('사주 운세는 출생 시간이 필요합니다.');
        }
        break;
      
      case 'zodiac':
        if (!userData.zodiacSign) {
          // 자동으로 별자리 계산
          userData.zodiacSign = this.getZodiacSign(userData.birthDate);
        }
        break;
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

// 싱글톤 인스턴스 생성
const fortuneService = new FortuneService();

export default fortuneService;
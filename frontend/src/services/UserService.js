/**
 * 사용자 관리 서비스
 * 사용자 프로필 및 세션 관리를 담당
 */

import { API_ENDPOINTS, STORAGE_KEYS } from '../utils/constants';

class UserService {
  constructor() {
    this.baseURL = API_ENDPOINTS.BASE_URL;
    this.currentUser = null;
    this.sessionId = null;
    this.initializeUser();
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

    // 세션 ID가 있으면 헤더에 추가
    if (this.sessionId) {
      defaultOptions.headers['X-Session-ID'] = this.sessionId;
    }

    console.log(`[UserService] API 요청 시작: ${url}`);

    try {
      const response = await fetch(url, {
        ...defaultOptions,
        ...options,
      });

      console.log(`[UserService] API 응답 상태: ${response.status}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        console.error(`[UserService] API 오류 응답:`, { status: response.status, errorData, url });
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log(`[UserService] API 요청 성공: ${endpoint}`, data);
      return data;
    } catch (error) {
      console.error(`[UserService] API 요청 실패: ${endpoint}`, {
        url,
        error: error.message,
        baseURL: this.baseURL,
        sessionId: this.sessionId,
        endpoint
      });
      
      // 네트워크 연결 오류 또는 CORS 오류일 가능성 확인
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error(`사용자 서비스 연결 실패: ${this.baseURL} (네트워크 오류 또는 CORS 문제)`);
      }
      
      throw error;
    }
  }

  /**
   * 사용자 초기화
   */
  initializeUser() {
    // 로컬 스토리지에서 기존 사용자 정보 로드
    const savedUser = this.loadUserFromStorage();
    if (savedUser) {
      this.currentUser = savedUser;
      this.sessionId = savedUser.sessionId;
      console.log('[UserService] 기존 사용자 정보 로드됨:', this.currentUser);
    } else {
      // 새 익명 사용자 생성
      this.createAnonymousUser();
    }
  }

  /**
   * 익명 사용자 생성
   */
  createAnonymousUser() {
    const anonymousUser = {
      id: this.generateUserId(),
      sessionId: this.generateSessionId(),
      name: '익명',
      isAnonymous: true,
      createdAt: new Date().toISOString(),
      preferences: {
        notifications: true,
        autoPlay: true,
        theme: 'default'
      }
    };

    this.currentUser = anonymousUser;
    this.sessionId = anonymousUser.sessionId;
    this.saveUserToStorage(anonymousUser);

    console.log('[UserService] 새 익명 사용자 생성:', this.currentUser);
    return anonymousUser;
  }

  /**
   * 사용자 프로필 생성/업데이트
   */
  async createOrUpdateProfile(profileData) {
    try {
      const userData = {
        session_id: this.sessionId,
        name: profileData.name || this.currentUser.name,
        birth_date: profileData.birthDate,
        birth_time: profileData.birthTime,
        gender: profileData.gender,
        zodiac_sign: profileData.zodiacSign,
        preferences: {
          ...this.currentUser.preferences,
          ...profileData.preferences
        }
      };

      const response = await this.apiRequest('/api/v1/user/profile', {
        method: 'POST',
        body: JSON.stringify(userData)
      });

      // 로컬 사용자 정보 업데이트
      this.currentUser = {
        ...this.currentUser,
        ...profileData,
        updatedAt: new Date().toISOString()
      };

      this.saveUserToStorage(this.currentUser);
      console.log('[UserService] 프로필 업데이트 성공:', this.currentUser);

      return response;
    } catch (error) {
      console.error('[UserService] 프로필 업데이트 실패:', error);
      throw error;
    }
  }

  /**
   * 세션 목록 조회
   */
  async getSessions() {
    try {
      return await this.apiRequest('/api/v1/user/sessions', {
        method: 'GET'
      });
    } catch (error) {
      console.error('[UserService] 세션 목록 조회 실패:', error);
      throw error;
    }
  }

  /**
   * 세션 생성
   */
  async createSession() {
    try {
      const sessionData = {
        user_id: this.currentUser.id,
        started_at: new Date().toISOString()
      };

      const response = await this.apiRequest('/api/v1/user/sessions', {
        method: 'POST',
        body: JSON.stringify(sessionData)
      });

      this.sessionId = response.session_id;
      this.currentUser.sessionId = this.sessionId;
      this.saveUserToStorage(this.currentUser);

      console.log('[UserService] 새 세션 생성:', this.sessionId);
      return response;
    } catch (error) {
      console.error('[UserService] 세션 생성 실패:', error);
      throw error;
    }
  }

  /**
   * 세션 종료
   */
  async endSession() {
    try {
      if (!this.sessionId) return;

      await this.apiRequest(`/api/v1/user/sessions/${this.sessionId}`, {
        method: 'DELETE'
      });

      console.log('[UserService] 세션 종료:', this.sessionId);
    } catch (error) {
      console.error('[UserService] 세션 종료 실패:', error);
    }
  }

  /**
   * 사용자 설정 업데이트
   */
  updatePreferences(preferences) {
    this.currentUser.preferences = {
      ...this.currentUser.preferences,
      ...preferences
    };
    this.saveUserToStorage(this.currentUser);
    console.log('[UserService] 사용자 설정 업데이트:', this.currentUser.preferences);
  }

  /**
   * 로컬 스토리지에서 사용자 정보 로드
   */
  loadUserFromStorage() {
    try {
      const savedUser = localStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return savedUser ? JSON.parse(savedUser) : null;
    } catch (error) {
      console.error('[UserService] 로컬 스토리지 로드 실패:', error);
      return null;
    }
  }

  /**
   * 로컬 스토리지에 사용자 정보 저장
   */
  saveUserToStorage(userData) {
    try {
      localStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(userData));
    } catch (error) {
      console.error('[UserService] 로컬 스토리지 저장 실패:', error);
    }
  }

  /**
   * 사용자 ID 생성
   */
  generateUserId() {
    return 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * 세션 ID 생성
   */
  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  /**
   * 현재 사용자 정보 반환
   */
  getCurrentUser() {
    return this.currentUser;
  }

  /**
   * 현재 세션 ID 반환
   */
  getSessionId() {
    return this.sessionId;
  }

  /**
   * 사용자 로그아웃 (데이터 초기화)
   */
  logout() {
    localStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES);
    localStorage.removeItem(STORAGE_KEYS.CHAT_HISTORY);
    localStorage.removeItem(STORAGE_KEYS.FORTUNE_HISTORY);
    
    this.currentUser = null;
    this.sessionId = null;
    
    console.log('[UserService] 사용자 로그아웃 완료');
    
    // 새 익명 사용자 생성
    this.createAnonymousUser();
  }

  /**
   * 사용자 데이터 유효성 검사
   */
  validateUserData(userData) {
    const errors = [];

    if (userData.name && userData.name.length < 1) {
      errors.push('이름을 입력해주세요.');
    }

    if (userData.birthDate) {
      const birthDate = new Date(userData.birthDate);
      if (isNaN(birthDate.getTime())) {
        errors.push('올바른 생년월일을 입력해주세요.');
      }
    }

    if (userData.birthTime && !/^\d{2}:\d{2}$/.test(userData.birthTime)) {
      errors.push('올바른 시간 형식(HH:MM)을 입력해주세요.');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  /**
   * 디버그 정보 출력
   */
  getDebugInfo() {
    return {
      currentUser: this.currentUser,
      sessionId: this.sessionId,
      storageData: this.loadUserFromStorage()
    };
  }
}

// 싱글톤 인스턴스 생성
const userService = new UserService();

export default userService;
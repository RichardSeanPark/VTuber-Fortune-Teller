import React, { useState } from 'react';
import './FortuneSelector.css';
import fortuneService from '../services/FortuneService';
import userService from '../services/UserService';

const FortuneSelector = ({ onFortuneSelect }) => {
  const [selectedType, setSelectedType] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [userData, setUserData] = useState({
    name: '',
    birthDate: '',
    birthTime: '',
    gender: '',
    zodiacSign: '',
    question: ''
  });
  const [formErrors, setFormErrors] = useState([]);

  const fortuneTypes = [
    {
      id: 'daily',
      name: '일일 운세',
      icon: '🌅',
      description: '오늘 하루의 전반적인 운세를 확인해보세요',
      color: '#FF6B6B'
    },
    {
      id: 'tarot',
      name: '타로 카드',
      icon: '🔮',
      description: '신비로운 타로 카드로 미래를 엿보세요',
      color: '#4ECDC4'
    },
    {
      id: 'zodiac',
      name: '별자리 운세',
      icon: '⭐',
      description: '당신의 별자리에 따른 운세를 알아보세요',
      color: '#45B7D1'
    },
    {
      id: 'saju',
      name: '사주 운세',
      icon: '☯️',
      description: '생년월일 기반 전통 사주 운세',
      color: '#96CEB4'
    }
  ];

  const handleFortuneClick = async (fortuneType) => {
    if (isProcessing) return;

    setSelectedType(fortuneType.id);
    
    // 타로 카드는 별도 처리
    if (fortuneType.id === 'tarot') {
      onFortuneSelect(fortuneType, null); // 타로는 결과 없이 전달
      return;
    }
    
    // 사용자 정보가 필요한 운세인지 확인
    const currentUser = userService.getCurrentUser();
    const needsUserInfo = !currentUser.birthDate || (fortuneType.id === 'saju' && !currentUser.birthTime);
    
    if (needsUserInfo) {
      // 사용자 정보 입력 폼 표시
      setShowUserForm(true);
      setUserData({
        name: currentUser.name || '',
        birthDate: currentUser.birthDate || '',
        birthTime: currentUser.birthTime || '',
        gender: currentUser.gender || '',
        zodiacSign: currentUser.zodiacSign || '',
        question: ''
      });
      return;
    }

    // 사용자 정보가 충분한 경우 바로 운세 요청
    await processFortuneRequest(fortuneType, currentUser);
  };

  const processFortuneRequest = async (fortuneType, userData) => {
    setIsProcessing(true);

    try {
      console.log(`[FortuneSelector] ${fortuneType.name} 요청 시작`);
      
      // 사용자 데이터 유효성 검사
      const validation = fortuneService.validateUserData(fortuneType.id, userData);
      if (!validation.isValid) {
        setFormErrors(validation.errors);
        return;
      }

      // 백엔드 API 호출
      const fortuneResult = await fortuneService.getFortuneByType(
        fortuneType.id, 
        userData,
        { selectedCards: [] } // 타로의 경우 별도 처리
      );

      console.log('[FortuneSelector] 운세 결과 수신:');
      console.log('- Raw API Response:', fortuneResult);
      console.log('- Response Keys:', Object.keys(fortuneResult || {}));
      console.log('- Has success property:', fortuneResult?.success);
      console.log('- Has data property:', fortuneResult?.data);
      
      // API 응답에서 실제 데이터 추출
      let actualFortuneData = null;
      
      if (fortuneResult && typeof fortuneResult === 'object') {
        if (fortuneResult.success === true && fortuneResult.data) {
          // 표준 API 응답 형식: { success: true, data: {...} }
          actualFortuneData = { ...fortuneResult.data };
          console.log('[FortuneSelector] 표준 API 형식에서 데이터 추출:', actualFortuneData);
        } else if (fortuneResult.type) {
          // 이미 운세 데이터 형식인 경우
          actualFortuneData = { ...fortuneResult };
          console.log('[FortuneSelector] 직접 운세 데이터 사용:', actualFortuneData);
        } else {
          // 예상치 못한 형식 - 그냥 사용해보기
          console.warn('[FortuneSelector] 예상치 못한 응답 형식, 그대로 사용:', fortuneResult);
          actualFortuneData = { ...fortuneResult };
        }
      } else {
        console.error('[FortuneSelector] 유효하지 않은 응답:', fortuneResult);
        throw new Error('서버에서 유효하지 않은 응답을 받았습니다.');
      }
      
      // 데이터 변환: fortune_type을 type으로 매핑
      if (actualFortuneData && actualFortuneData.fortune_type && !actualFortuneData.type) {
        // 백엔드 fortune_type을 프론트엔드 type으로 변환
        const typeMapping = {
          'oriental': 'saju',
          'daily': 'daily', 
          'tarot': 'tarot',
          'zodiac': 'zodiac'
        };
        actualFortuneData.type = typeMapping[actualFortuneData.fortune_type] || actualFortuneData.fortune_type;
        console.log('[FortuneSelector] fortune_type을 type으로 변환:', actualFortuneData.fortune_type, '->', actualFortuneData.type);
      }
      
      // 최종 검증
      if (!actualFortuneData || (!actualFortuneData.type && !actualFortuneData.fortune_type)) {
        console.error('[FortuneSelector] 추출된 데이터가 유효하지 않음:', actualFortuneData);
        throw new Error('운세 데이터가 올바르지 않습니다.');
      }
      
      console.log('[FortuneSelector] 최종 추출된 운세 데이터:', actualFortuneData);
      
      // 결과를 상위 컴포넌트로 전달 (frontend2 방식)
      onFortuneSelect(fortuneType, actualFortuneData);
      
      // 성공 피드백
      showSuccessFeedback(fortuneType);
      
    } catch (error) {
      console.error('[FortuneSelector] 운세 요청 실패:', error);
      setFormErrors([`운세 요청에 실패했습니다: ${error.message}`]);
    } finally {
      setIsProcessing(false);
      setSelectedType(null);
      setShowUserForm(false);
    }
  };

  const handleUserFormSubmit = async (e) => {
    e.preventDefault();
    setFormErrors([]);

    try {
      // 사용자 정보 저장
      await userService.createOrUpdateProfile(userData);
      
      // 선택된 운세 타입으로 요청 진행
      const fortuneType = fortuneTypes.find(f => f.id === selectedType);
      await processFortuneRequest(fortuneType, userData);
      
    } catch (error) {
      console.error('[FortuneSelector] 사용자 정보 저장 실패:', error);
      setFormErrors([`사용자 정보 저장에 실패했습니다: ${error.message}`]);
    }
  };

  const handleInputChange = (field, value) => {
    setUserData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // 생년월일 변경 시 별자리 자동 계산
    if (field === 'birthDate' && value) {
      const zodiacSign = fortuneService.getZodiacSign(value);
      setUserData(prev => ({
        ...prev,
        zodiacSign
      }));
    }
  };

  const showSuccessFeedback = (fortuneType) => {
    // 임시 성공 알림 (추후 토스트 알림으로 개선)
    const message = `${fortuneType.name}을(를) 선택했습니다! 미라가 준비 중이에요...`;
    console.log(message);
  };

  return (
    <div className="fortune-selector">
      {!showUserForm ? (
        <>
          <div className="selector-header">
            <h3>운세 선택하기</h3>
            <p>어떤 운세를 봐드릴까요?</p>
          </div>

          <div className="fortune-grid">
            {fortuneTypes.map((fortune) => (
              <div
                key={fortune.id}
                className={`fortune-card ${selectedType === fortune.id ? 'selected' : ''} ${isProcessing ? 'processing' : ''}`}
                onClick={() => handleFortuneClick(fortune)}
                style={{ '--card-color': fortune.color }}
              >
                <div className="card-inner">
                  <div className="card-icon">
                    {selectedType === fortune.id && isProcessing ? (
                      <div className="processing-spinner"></div>
                    ) : (
                      <span>{fortune.icon}</span>
                    )}
                  </div>
                  
                  <div className="card-content">
                    <h4>{fortune.name}</h4>
                    <p>{fortune.description}</p>
                  </div>
                  
                  <div className="card-overlay">
                    <span className="overlay-text">
                      {selectedType === fortune.id && isProcessing ? '처리 중...' : '선택하기'}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="selector-footer">
            <div className="info-text">
              <p>💡 카드를 클릭하여 운세를 선택하세요</p>
              <p>🎯 미라가 당신만을 위한 특별한 운세를 준비해드릴게요!</p>
            </div>
            
            {isProcessing && (
              <div className="processing-info">
                <div className="processing-animation">
                  <span>✨</span>
                  <span>🔮</span>
                  <span>✨</span>
                </div>
                <p>미라가 운세를 준비하고 있어요...</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="user-form-container">
          <div className="form-header">
            <h3>정보 입력</h3>
            <p>정확한 운세를 위해 몇 가지 정보가 필요해요</p>
          </div>

          <form onSubmit={handleUserFormSubmit} className="user-form">
            <div className="form-row">
              <label>
                이름 (선택사항)
                <input
                  type="text"
                  value={userData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  placeholder="이름을 입력하세요"
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                생년월일 *
                <input
                  type="date"
                  value={userData.birthDate}
                  onChange={(e) => handleInputChange('birthDate', e.target.value)}
                  required
                />
              </label>
            </div>

            {selectedType === 'saju' && (
              <div className="form-row">
                <label>
                  출생 시간 *
                  <input
                    type="time"
                    value={userData.birthTime}
                    onChange={(e) => handleInputChange('birthTime', e.target.value)}
                    required
                  />
                </label>
                <small>사주 운세는 정확한 출생 시간이 필요합니다</small>
              </div>
            )}

            <div className="form-row">
              <label>
                성별 (선택사항)
                <select
                  value={userData.gender}
                  onChange={(e) => handleInputChange('gender', e.target.value)}
                >
                  <option value="">선택하지 않음</option>
                  <option value="male">남성</option>
                  <option value="female">여성</option>
                  <option value="other">기타</option>
                </select>
              </label>
            </div>

            {selectedType === 'tarot' && (
              <div className="form-row">
                <label>
                  질문 (선택사항)
                  <textarea
                    value={userData.question}
                    onChange={(e) => handleInputChange('question', e.target.value)}
                    placeholder="타로에게 묻고 싶은 질문을 적어주세요"
                    rows="3"
                  />
                </label>
              </div>
            )}

            {formErrors.length > 0 && (
              <div className="form-errors">
                {formErrors.map((error, index) => (
                  <p key={index} className="error-message">⚠️ {error}</p>
                ))}
              </div>
            )}

            <div className="form-actions">
              <button 
                type="button" 
                onClick={() => {
                  setShowUserForm(false);
                  setSelectedType(null);
                  setFormErrors([]);
                }}
                className="btn-secondary"
              >
                취소
              </button>
              <button 
                type="submit" 
                disabled={isProcessing}
                className="btn-primary"
              >
                {isProcessing ? '처리 중...' : '운세 보기'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default FortuneSelector;
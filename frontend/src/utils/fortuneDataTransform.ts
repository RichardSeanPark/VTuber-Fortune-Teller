/**
 * Fortune Data Transformation Utilities
 * API 응답을 UI 컴포넌트 형식으로 안전하게 변환
 */

/**
 * API 응답을 FortuneResult 컴포넌트가 기대하는 형식으로 변환
 * @param {Object} apiResponse - API에서 받은 응답 데이터
 * @returns {Object} - 변환된 fortune 데이터
 */
export const transformApiResponseToFortuneData = (apiResponse) => {
  // API 응답이 이미 표준화된 형식인지 확인
  if (!apiResponse) {
    console.warn('[FortuneTransform] API 응답이 없습니다');
    return null;
  }

  // success 형식의 API 응답 처리
  if (apiResponse.success && apiResponse.data) {
    return transformFortuneData(apiResponse.data);
  }

  // 직접적인 데이터 형식 처리
  return transformFortuneData(apiResponse);
};

/**
 * Fortune 데이터를 안전하게 변환
 * @param {Object} fortuneData - 변환할 fortune 데이터
 * @returns {Object} - 변환된 데이터
 */
export const transformFortuneData = (fortuneData) => {
  if (!fortuneData) {
    return null;
  }

  // 이미 올바른 형식인 경우 그대로 반환
  if (fortuneData.type) {
    return fortuneData;
  }

  // 레거시 형식에서 새 형식으로 변환
  const transformed = {
    type: fortuneData.fortune_type || fortuneData.type || 'unknown',
    fortune_id: fortuneData.fortune_id || generateRandomId(),
    message: fortuneData.overall_interpretation || 
             fortuneData.interpretation || 
             fortuneData.message || 
             fortuneData.overall_fortune?.description ||
             fortuneData.overall_fortune?.interpretation ||
             '운세 해석을 불러올 수 없습니다.',
    advice: fortuneData.advice || '긍정적인 마음으로 하루를 시작해보세요.',
    live2d_emotion: fortuneData.live2d_emotion || 'joy',
    live2d_motion: fortuneData.live2d_motion || 'greeting',
    created_at: fortuneData.created_at || new Date().toISOString()
  };

  // 타로 카드 데이터 변환
  if (transformed.type === 'tarot') {
    transformed.question = fortuneData.question || '오늘의 운세를 알려주세요';
    transformed.question_type = fortuneData.question_type || 'general';
    transformed.cards = transformTarotCards(fortuneData.cards);
  }

  // 일일 운세 데이터 변환
  if (transformed.type === 'daily') {
    const content = fortuneData.content || {};
    const categories = content.categories || fortuneData.categories || {};
    const overallFortune = fortuneData.overall_fortune || {};
    
    // 메시지 우선순위 재확인
    if (!transformed.message || transformed.message === '운세 해석을 불러올 수 없습니다.') {
      transformed.message = overallFortune.description || 
                           overallFortune.interpretation ||
                           content.advice ||
                           '오늘은 좋은 하루가 될 것 같아요!';
    }
    
    transformed.score = overallFortune.score || content.overall_score || fortuneData.score || 75;
    transformed.love = categories.love?.score || fortuneData.love || 70;
    transformed.money = categories.money?.score || fortuneData.money || 65;
    transformed.health = categories.health?.score || fortuneData.health || 80;
    transformed.work = categories.work?.score || fortuneData.work || 75;
    
    const luckyElements = content.lucky_elements || fortuneData.lucky_elements || {};
    transformed.luckyColor = luckyElements.color || fortuneData.luckyColor || '파란색';
    transformed.luckyNumber = luckyElements.number || fortuneData.luckyNumber || '7';
    transformed.luckyItem = luckyElements.item || fortuneData.luckyItem || '목걸이';
  }

  // 별자리 운세 데이터 변환
  if (transformed.type === 'zodiac') {
    const content = fortuneData.content || {};
    const zodiacInfo = content.zodiac_info || {};
    
    transformed.zodiac = zodiacInfo.sign || fortuneData.zodiac || 'aries';
    transformed.score = content.overall_score || fortuneData.score || 75;
    transformed.traits = zodiacInfo.traits || fortuneData.traits || ['긍정적인 성격', '도전정신이 뛰어남'];
    transformed.goodCompat = zodiacInfo.compatible_signs || fortuneData.goodCompat || '사자자리, 사수자리';
    transformed.badCompat = zodiacInfo.incompatible_signs || fortuneData.badCompat || '게자리, 염소자리';
  }

  // 사주 운세 데이터 변환
  if (transformed.type === 'saju' || transformed.type === 'oriental') {
    transformed.type = 'saju'; // 타입 통일
    transformed.birthDate = fortuneData.birth_date || fortuneData.birthDate;
    transformed.year = fortuneData.year || '갑자';
    transformed.month = fortuneData.month || '을축';
    transformed.day = fortuneData.day || '병인';
    transformed.hour = fortuneData.hour || '정묘';
    transformed.score = fortuneData.score || 75;
  }

  return transformed;
};

/**
 * 타로 카드 데이터 변환
 * @param {Array} cards - 원본 카드 데이터
 * @returns {Array} - 변환된 카드 데이터
 */
export const transformTarotCards = (cards) => {
  if (!Array.isArray(cards)) {
    console.warn('[FortuneTransform] 타로 카드 데이터가 배열이 아닙니다:', cards);
    return [];
  }

  return cards.map((card, index) => {
    // 이미 올바른 형식인 경우
    if (card && typeof card === 'object' && card.name) {
      return {
        id: card.id || index,
        name: card.name || card.card_name || '알 수 없는 카드',
        name_ko: card.name_ko || card.card_name_ko || card.name || '알 수 없는 카드',
        position: card.position || ['과거', '현재', '미래'][index] || '알 수 없음',
        meaning: card.meaning || card.card_meaning || '카드의 의미',
        interpretation: card.interpretation || '카드 해석',
        image_url: card.image_url || '/static/tarot/default.jpg',
        emoji: card.emoji || getTarotEmoji(card.name || card.card_name)
      };
    }

    // 숫자 ID만 있는 경우 (레거시)
    if (typeof card === 'number') {
      return {
        id: card,
        name: `Card ${card}`,
        name_ko: `카드 ${card}`,
        position: ['과거', '현재', '미래'][index] || '알 수 없음',
        meaning: '카드의 의미',
        interpretation: '카드 해석',
        image_url: '/static/tarot/default.jpg',
        emoji: '🔮'
      };
    }

    // 예상치 못한 형식
    console.warn('[FortuneTransform] 예상치 못한 카드 데이터 형식:', card);
    return {
      id: index,
      name: '알 수 없는 카드',
      name_ko: '알 수 없는 카드',
      position: ['과거', '현재', '미래'][index] || '알 수 없음',
      meaning: '카드의 의미',
      interpretation: '카드 해석',
      image_url: '/static/tarot/default.jpg',
      emoji: '🔮'
    };
  });
};

/**
 * 타로 카드 이름에 따른 이모지 반환
 * @param {string} cardName - 카드 이름
 * @returns {string} - 해당하는 이모지
 */
export const getTarotEmoji = (cardName) => {
  const emojiMap = {
    'The Fool': '🤪',
    'The Magician': '🎩',
    'The High Priestess': '🔮',
    'The Empress': '👸',
    'The Emperor': '👑',
    'The Hierophant': '⛪',
    'The Lovers': '💕',
    'The Chariot': '🏎️',
    'Strength': '💪',
    'The Hermit': '🔦',
    'Wheel of Fortune': '🎰',
    'Justice': '⚖️',
    'The Hanged Man': '🙃',
    'Death': '💀',
    'Temperance': '🍷',
    'The Devil': '😈',
    'The Tower': '🏗️',
    'The Star': '⭐',
    'The Moon': '🌙',
    'The Sun': '☀️',
    'Judgement': '📯',
    'The World': '🌍'
  };

  return emojiMap[cardName] || '🔮';
};

/**
 * 랜덤 ID 생성
 * @returns {string} - 랜덤 ID
 */
export const generateRandomId = () => {
  return `fortune_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

/**
 * 데이터 유효성 검사
 * @param {Object} fortuneData - 검사할 데이터
 * @returns {boolean} - 유효성 여부
 */
export const validateFortuneData = (fortuneData) => {
  if (!fortuneData || typeof fortuneData !== 'object') {
    return false;
  }

  // 필수 필드 확인
  const requiredFields = ['type', 'message'];
  for (const field of requiredFields) {
    if (!fortuneData[field]) {
      console.warn(`[FortuneTransform] 필수 필드 누락: ${field}`);
      return false;
    }
  }

  // 타입별 추가 검증
  if (fortuneData.type === 'tarot' && !Array.isArray(fortuneData.cards)) {
    console.warn('[FortuneTransform] 타로 카드 데이터가 배열이 아닙니다');
    return false;
  }

  return true;
};

const fortuneDataTransform = {
  transformApiResponseToFortuneData,
  transformFortuneData,
  transformTarotCards,
  getTarotEmoji,
  generateRandomId,
  validateFortuneData
};

export default fortuneDataTransform;
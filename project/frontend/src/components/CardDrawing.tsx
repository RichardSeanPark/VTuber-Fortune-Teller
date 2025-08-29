import React, { useState, useEffect } from 'react';
import './CardDrawing.css';
import { TAROT_CARDS } from '../utils/constants';

const CardDrawing = ({ isActive, onCardSelect, selectedCards = [], maxCards = 3, onBack }) => {
  const [shuffledCards, setShuffledCards] = useState([]);
  const [isShuffling, setIsShuffling] = useState(false);
  const [selectedPositions, setSelectedPositions] = useState([]);
  const [isRevealing, setIsRevealing] = useState(false);

  useEffect(() => {
    if (isActive) {
      initializeCards();
    }
  }, [isActive]);

  const initializeCards = () => {
    setIsShuffling(true);
    setSelectedPositions([]);
    setIsRevealing(false);

    // 카드 섞기 애니메이션
    setTimeout(() => {
      const cards = Object.values(TAROT_CARDS);
      const shuffled = [...cards].sort(() => Math.random() - 0.5);
      setShuffledCards(shuffled);
      setIsShuffling(false);
    }, 1500);
  };

  const handleCardClick = (cardIndex) => {
    if (isShuffling || isRevealing || selectedPositions.includes(cardIndex) || selectedPositions.length >= maxCards) {
      return;
    }

    const newSelected = [...selectedPositions, cardIndex];
    setSelectedPositions(newSelected);

    // 선택 완료 시 카드 공개
    if (newSelected.length === maxCards) {
      setTimeout(() => {
        revealCards(newSelected);
      }, 500);
    }
  };

  const revealCards = (positions) => {
    setIsRevealing(true);
    
    const selectedCardData = positions.map(pos => shuffledCards[pos]);
    
    // 카드 공개 애니메이션 후 결과 전달
    setTimeout(() => {
      onCardSelect(selectedCardData);
    }, 2000);
  };

  const resetCards = () => {
    setSelectedPositions([]);
    setIsRevealing(false);
    initializeCards();
  };

  const getCardPositionName = (index) => {
    const positions = ['과거', '현재', '미래', '조언', '결과'];
    return positions[index] || `카드 ${index + 1}`;
  };

  if (!isActive) {
    return null;
  }

  return (
    <div className="card-drawing">
      <div className="drawing-header">
        <h3>🔮 타로 카드를 선택하세요</h3>
        <p>
          {selectedPositions.length === 0 && '카드를 클릭하여 운명을 확인해보세요'}
          {selectedPositions.length > 0 && selectedPositions.length < maxCards && 
            `${maxCards - selectedPositions.length}장 더 선택해주세요`}
          {selectedPositions.length === maxCards && '카드를 공개하는 중...'}
        </p>
      </div>

      {isShuffling && (
        <div className="shuffling-animation">
          <div className="shuffle-cards">
            {[...Array(7)].map((_, index) => (
              <div 
                key={index} 
                className="shuffle-card"
                style={{ 
                  animationDelay: `${index * 0.1}s`,
                  zIndex: 7 - index 
                }}
              >
                <div className="card-back"></div>
              </div>
            ))}
          </div>
          <p className="shuffle-text">카드를 섞는 중...</p>
        </div>
      )}

      {!isShuffling && (
        <div className="cards-container">
          <div className="cards-grid">
            {shuffledCards.slice(0, 12).map((card, index) => (
              <div
                key={index}
                className={`tarot-card-item ${
                  selectedPositions.includes(index) ? 'selected' : ''
                } ${isRevealing ? 'revealing' : ''}`}
                onClick={() => handleCardClick(index)}
                style={{ 
                  animationDelay: `${index * 0.05}s`,
                  '--reveal-delay': `${selectedPositions.indexOf(index) * 0.5}s`
                }}
              >
                <div className="card-inner">
                  <div className="card-face card-back">
                    <div className="back-pattern"></div>
                  </div>
                  <div className="card-face card-front">
                    <div className="card-emoji">{card.emoji}</div>
                    <div className="card-name">{card.name}</div>
                    <div className="card-number">{card.id}</div>
                  </div>
                </div>
                
                {selectedPositions.includes(index) && (
                  <div className="position-label">
                    {getCardPositionName(selectedPositions.indexOf(index))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {selectedPositions.length > 0 && (
            <div className="selected-cards-info">
              <h4>선택된 카드</h4>
              <div className="selected-list">
                {selectedPositions.map((pos, index) => (
                  <div key={index} className="selected-card-info">
                    <span className="position">{getCardPositionName(index)}</span>
                    <span className="card-name">{shuffledCards[pos]?.name || '카드'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="drawing-actions">
            <button 
              className="action-button secondary"
              onClick={onBack}
              disabled={isRevealing}
            >
              뒤로가기
            </button>
            
            <button 
              className="action-button secondary"
              onClick={resetCards}
              disabled={isRevealing}
            >
              다시 섞기
            </button>
            
            {selectedPositions.length === maxCards && !isRevealing && (
              <button 
                className="action-button primary"
                onClick={() => revealCards(selectedPositions)}
              >
                카드 공개하기
              </button>
            )}
          </div>
        </div>
      )}

      <div className="drawing-guide">
        <div className="guide-item">
          <span className="guide-icon">✨</span>
          <span>마음을 비우고 직감으로 선택하세요</span>
        </div>
        <div className="guide-item">
          <span className="guide-icon">🎯</span>
          <span>질문을 마음속으로 떠올리며 카드를 고르세요</span>
        </div>
        <div className="guide-item">
          <span className="guide-icon">🔮</span>
          <span>선택한 카드가 당신의 운명을 보여줍니다</span>
        </div>
      </div>
    </div>
  );
};

export default CardDrawing;
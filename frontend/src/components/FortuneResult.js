import React, { useState, useEffect } from 'react';
import './FortuneResult.css';
import { FORTUNE_SCORES, ZODIAC_SIGNS } from '../utils/constants';

const FortuneResult = ({ fortuneData, onClose, onRetry }) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (fortuneData) {
      setIsAnimating(true);
      setTimeout(() => {
        setIsVisible(true);
        setIsAnimating(false);
      }, 300);
    }
  }, [fortuneData]);

  if (!fortuneData) return null;

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => {
      onClose();
    }, 300);
  };

  const getScoreLabel = (score) => {
    for (const [, range] of Object.entries(FORTUNE_SCORES)) {
      if (score >= range.min && score <= range.max) {
        return range.label;
      }
    }
    return '알 수 없음';
  };

  const getScoreColor = (score) => {
    if (score >= 80) return '#198754'; // 녹색
    if (score >= 60) return '#28a745'; // 연녹색
    if (score >= 40) return '#ffc107'; // 노란색
    if (score >= 20) return '#fd7e14'; // 주황색
    return '#dc3545'; // 빨간색
  };

  const renderFortuneContent = () => {
    switch (fortuneData.type) {
      case 'daily':
        return renderDailyFortune();
      case 'tarot':
        return renderTarotFortune();
      case 'zodiac':
        return renderZodiacFortune();
      case 'saju':
        return renderSajuFortune();
      default:
        return renderGenericFortune();
    }
  };

  const renderDailyFortune = () => (
    <div className="fortune-content daily">
      <div className="fortune-header">
        <h3>🌅 오늘의 운세</h3>
        <div className="fortune-date">
          {new Date().toLocaleDateString('ko-KR', { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </div>
      </div>
      
      <div className="overall-score">
        <div className="score-circle" style={{ borderColor: getScoreColor(fortuneData.score) }}>
          <span className="score-number">{fortuneData.score}</span>
          <span className="score-label">{getScoreLabel(fortuneData.score)}</span>
        </div>
      </div>

      <div className="fortune-details">
        <div className="detail-item">
          <span className="detail-icon">💕</span>
          <span className="detail-label">연애운</span>
          <div className="detail-bar">
            <div 
              className="detail-fill" 
              style={{ 
                width: `${fortuneData.love || 70}%`,
                backgroundColor: getScoreColor(fortuneData.love || 70)
              }}
            ></div>
          </div>
        </div>
        
        <div className="detail-item">
          <span className="detail-icon">💰</span>
          <span className="detail-label">금전운</span>
          <div className="detail-bar">
            <div 
              className="detail-fill" 
              style={{ 
                width: `${fortuneData.money || 65}%`,
                backgroundColor: getScoreColor(fortuneData.money || 65)
              }}
            ></div>
          </div>
        </div>
        
        <div className="detail-item">
          <span className="detail-icon">💪</span>
          <span className="detail-label">건강운</span>
          <div className="detail-bar">
            <div 
              className="detail-fill" 
              style={{ 
                width: `${fortuneData.health || 80}%`,
                backgroundColor: getScoreColor(fortuneData.health || 80)
              }}
            ></div>
          </div>
        </div>
        
        <div className="detail-item">
          <span className="detail-icon">📚</span>
          <span className="detail-label">학업/직장운</span>
          <div className="detail-bar">
            <div 
              className="detail-fill" 
              style={{ 
                width: `${fortuneData.work || 75}%`,
                backgroundColor: getScoreColor(fortuneData.work || 75)
              }}
            ></div>
          </div>
        </div>
      </div>

      <div className="fortune-message">
        <p>{fortuneData.message}</p>
      </div>

      <div className="lucky-items">
        <div className="lucky-item">
          <span className="lucky-label">럭키 컬러</span>
          <span className="lucky-value">{fortuneData.luckyColor || '파란색'}</span>
        </div>
        <div className="lucky-item">
          <span className="lucky-label">럭키 넘버</span>
          <span className="lucky-value">{fortuneData.luckyNumber || '7'}</span>
        </div>
        <div className="lucky-item">
          <span className="lucky-label">럭키 아이템</span>
          <span className="lucky-value">{fortuneData.luckyItem || '목걸이'}</span>
        </div>
      </div>
    </div>
  );

  const renderTarotFortune = () => (
    <div className="fortune-content tarot">
      <div className="fortune-header">
        <h3>🔮 타로 카드 리딩</h3>
        <div className="fortune-question">
          <span>질문: {fortuneData.question}</span>
        </div>
      </div>
      
      <div className="tarot-cards">
        {(fortuneData.cards || []).map((card, index) => {
          return (
            <div key={index} className="tarot-card">
              <div className="card-emoji">{card.emoji || '🔮'}</div>
              <div className="card-name">{card.name_ko || card.name}</div>
              <div className="card-position">{card.position}</div>
              <div className="card-meaning">{card.meaning}</div>
              <div className="card-interpretation">{card.interpretation}</div>
            </div>
          );
        })}
      </div>

      <div className="fortune-message">
        <h4>🔮 전체 해석</h4>
        <p>{fortuneData.message}</p>
      </div>

      <div className="tarot-advice">
        <h4>💡 조언</h4>
        <p>{fortuneData.advice || '직감을 믿고 새로운 도전을 시작해보세요.'}</p>
      </div>
    </div>
  );

  const renderZodiacFortune = () => {
    const zodiac = Object.values(ZODIAC_SIGNS).find(z => z.id === fortuneData.zodiac) || ZODIAC_SIGNS.ARIES;
    
    return (
      <div className="fortune-content zodiac">
        <div className="fortune-header">
          <h3>⭐ {zodiac.name} 운세</h3>
          <div className="zodiac-info">
            <span className="zodiac-emoji">{zodiac.emoji}</span>
            <span className="zodiac-period">{zodiac.period}</span>
          </div>
        </div>

        <div className="overall-score">
          <div className="score-circle" style={{ borderColor: getScoreColor(fortuneData.score) }}>
            <span className="score-number">{fortuneData.score}</span>
            <span className="score-label">{getScoreLabel(fortuneData.score)}</span>
          </div>
        </div>

        <div className="fortune-message">
          <p>{fortuneData.message}</p>
        </div>

        <div className="zodiac-traits">
          <h4>🌟 성격 특징</h4>
          <div className="traits-list">
            {(fortuneData.traits || ['리더십이 강함', '도전정신이 뛰어남', '열정적이고 적극적']).map((trait, index) => (
              <div key={index} className="trait-item">
                <span className="trait-bullet">•</span>
                <span>{trait}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="compatibility">
          <h4>💕 궁합</h4>
          <div className="compat-list">
            <div className="compat-item good">
              <span className="compat-label">좋은 궁합</span>
              <span className="compat-signs">{fortuneData.goodCompat || '사자자리, 사수자리'}</span>
            </div>
            <div className="compat-item avoid">
              <span className="compat-label">주의 궁합</span>
              <span className="compat-signs">{fortuneData.badCompat || '게자리, 염소자리'}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSajuFortune = () => (
    <div className="fortune-content saju">
      <div className="fortune-header">
        <h3>☯️ 사주 운세</h3>
        <div className="birth-info">
          {fortuneData.birthDate && (
            <span>{new Date(fortuneData.birthDate).toLocaleDateString('ko-KR')}</span>
          )}
        </div>
      </div>

      <div className="overall-score">
        <div className="score-circle" style={{ borderColor: getScoreColor(fortuneData.score) }}>
          <span className="score-number">{fortuneData.score}</span>
          <span className="score-label">{getScoreLabel(fortuneData.score)}</span>
        </div>
      </div>

      <div className="saju-elements">
        <h4>🔥 사주 구성</h4>
        <div className="elements-grid">
          <div className="element-item">
            <span className="element-label">년주</span>
            <span className="element-value">{fortuneData.year || '갑자'}</span>
          </div>
          <div className="element-item">
            <span className="element-label">월주</span>
            <span className="element-value">{fortuneData.month || '을축'}</span>
          </div>
          <div className="element-item">
            <span className="element-label">일주</span>
            <span className="element-value">{fortuneData.day || '병인'}</span>
          </div>
          <div className="element-item">
            <span className="element-label">시주</span>
            <span className="element-value">{fortuneData.hour || '정묘'}</span>
          </div>
        </div>
      </div>

      <div className="fortune-message">
        <p>{fortuneData.message}</p>
      </div>

      <div className="saju-advice">
        <h4>🍀 개운법</h4>
        <p>{fortuneData.advice || '동쪽 방향으로 산책하고 녹색 옷을 입으시면 좋은 기운을 받을 수 있어요.'}</p>
      </div>
    </div>
  );

  const renderGenericFortune = () => (
    <div className="fortune-content generic">
      <div className="fortune-header">
        <h3>🔮 운세 결과</h3>
      </div>
      
      <div className="fortune-message">
        <p>{fortuneData.message}</p>
      </div>
    </div>
  );

  return (
    <div className={`fortune-result-overlay ${isVisible ? 'visible' : ''}`}>
      <div className={`fortune-result ${isAnimating ? 'animating' : ''}`}>
        <div className="result-header">
          <button className="close-button" onClick={handleClose}>
            ✕
          </button>
        </div>

        {renderFortuneContent()}

        <div className="result-actions">
          <button className="action-button secondary" onClick={onRetry}>
            다시 보기
          </button>
          <button className="action-button primary" onClick={handleClose}>
            확인
          </button>
        </div>
      </div>
    </div>
  );
};

export default FortuneResult;
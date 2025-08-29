/**
 * TTS Settings Panel Component
 * 
 * Provides user interface for TTS provider selection, voice testing,
 * and user preference management for the VTuber fortune-telling application.
 * Based on todo specifications Phase 8.6.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import './TtsSettingsPanel.css';

// Types
interface TTSProvider {
  id: string;
  name: string;
  cost: 'free' | 'free_tier' | 'paid';
  languages: string[];
  voices: string[];
  available: boolean;
  priority: number;
  recommended?: boolean;
  description?: string;
}

interface TTSSettings {
  provider_id: string;
  voice: string;
  speed: number;
  pitch: number;
  volume: number;
  language: string;
}

interface VoiceTestResult {
  audio_url: string;
  provider: string;
  cost_info: {
    cost: number;
    currency: string;
    estimated_monthly: number;
  };
}

interface TtsSettingsPanelProps {
  userId: string;
  isOpen: boolean;
  onClose: () => void;
  onSettingsChange?: (settings: TTSSettings) => void;
  currentSettings?: Partial<TTSSettings>;
}

const TtsSettingsPanel: React.FC<TtsSettingsPanelProps> = ({
  userId,
  isOpen,
  onClose,
  onSettingsChange,
  currentSettings = {}
}) => {
  // State
  const [providers, setProviders] = useState<TTSProvider[]>([]);
  const [settings, setSettings] = useState<TTSSettings>({
    provider_id: '',
    voice: '',
    speed: 1.0,
    pitch: 1.0,
    volume: 1.0,
    language: 'ko-KR',
    ...currentSettings
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<VoiceTestResult | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Refs
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load TTS providers on mount
  useEffect(() => {
    if (isOpen && userId) {
      fetchTtsProviders();
    }
  }, [isOpen, userId]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  // Fetch available TTS providers
  const fetchTtsProviders = useCallback(async () => {
    if (!userId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/tts/providers?user_id=${userId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Sort providers by priority and availability
      const sortedProviders = data.sort((a: TTSProvider, b: TTSProvider) => {
        if (a.available !== b.available) {
          return a.available ? -1 : 1; // Available first
        }
        return a.priority - b.priority; // Then by priority
      });
      
      setProviders(sortedProviders);
      
      // Set default provider if none selected
      if (!settings.provider_id && sortedProviders.length > 0) {
        const defaultProvider = sortedProviders.find(p => p.available && p.recommended) || 
                              sortedProviders.find(p => p.available);
        
        if (defaultProvider) {
          const defaultVoice = defaultProvider.voices[0] || '';
          updateSettings({
            provider_id: defaultProvider.id,
            voice: defaultVoice
          });
        }
      }
      
    } catch (err) {
      console.error('Failed to fetch TTS providers:', err);
      setError(err instanceof Error ? err.message : '제공자 목록을 불러올 수 없습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [userId, settings.provider_id]);

  // Update settings
  const updateSettings = useCallback((updates: Partial<TTSSettings>) => {
    const newSettings = { ...settings, ...updates };
    setSettings(newSettings);
    onSettingsChange?.(newSettings);
  }, [settings, onSettingsChange]);

  // Test voice with selected settings
  const testVoice = useCallback(async (providerId?: string, voice?: string) => {
    const testProviderId = providerId || settings.provider_id;
    const testVoice = voice || settings.voice;
    
    if (!testProviderId || !testVoice) {
      setError('제공자와 음성을 선택해주세요.');
      return;
    }

    // Abort previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    
    setIsPlaying(true);
    setError(null);
    setTestResult(null);
    
    try {
      const response = await fetch('/api/tts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          provider_id: testProviderId,
          voice: testVoice,
          speed: settings.speed,
          pitch: settings.pitch,
          volume: settings.volume,
          language: settings.language
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: VoiceTestResult = await response.json();
      setTestResult(result);

      // Play test audio
      if (result.audio_url) {
        const audio = new Audio(result.audio_url);
        audioRef.current = audio;
        
        audio.onended = () => {
          setIsPlaying(false);
          audioRef.current = null;
        };
        
        audio.onerror = () => {
          setError('오디오 재생에 실패했습니다.');
          setIsPlaying(false);
          audioRef.current = null;
        };
        
        await audio.play();
        
        // Show cost information if applicable
        if (result.cost_info.cost > 0) {
          showCostNotification(result.cost_info);
        }
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return; // Request was aborted
      }
      
      console.error('TTS test failed:', err);
      setError(err instanceof Error ? err.message : '음성 테스트에 실패했습니다.');
    } finally {
      setIsPlaying(false);
    }
  }, [settings, userId]);

  // Save settings to server
  const saveSettings = useCallback(async () => {
    if (!userId) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/tts/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          ...settings
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.status === 'success') {
        // Show success notification
        showSuccessNotification('설정이 저장되었습니다.');
      } else {
        throw new Error(result.message || '설정 저장에 실패했습니다.');
      }

    } catch (err) {
      console.error('Failed to save settings:', err);
      setError(err instanceof Error ? err.message : '설정 저장에 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [userId, settings]);

  // Show cost notification
  const showCostNotification = (costInfo: VoiceTestResult['cost_info']) => {
    if (costInfo.cost > 0) {
      alert(`💰 이 음성은 유료입니다.\n비용: ${costInfo.cost} ${costInfo.currency}\n예상 월 비용: ${costInfo.estimated_monthly} ${costInfo.currency}`);
    }
  };

  // Show success notification
  const showSuccessNotification = (message: string) => {
    // Simple alert for now - could be enhanced with toast notifications
    alert(`✅ ${message}`);
  };

  // Stop current audio playback
  const stopAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsPlaying(false);
  };

  // Get provider by ID
  const getProvider = (providerId: string) => {
    return providers.find(p => p.id === providerId);
  };

  // Get cost badge color
  const getCostBadgeClass = (cost: string) => {
    switch (cost) {
      case 'free': return 'cost-badge-free';
      case 'free_tier': return 'cost-badge-free-tier';
      case 'paid': return 'cost-badge-paid';
      default: return 'cost-badge-unknown';
    }
  };

  // Get cost badge text
  const getCostBadgeText = (cost: string) => {
    switch (cost) {
      case 'free': return '무료';
      case 'free_tier': return '무료 한도';
      case 'paid': return '유료';
      default: return '알 수 없음';
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="tts-settings-overlay">
      <div className="tts-settings-panel">
        <div className="tts-settings-header">
          <h3>🎙️ TTS 음성 설정</h3>
          <button 
            className="close-button" 
            onClick={onClose}
            aria-label="설정 닫기"
          >
            ×
          </button>
        </div>

        <div className="tts-settings-content">
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {isLoading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>설정을 불러오는 중...</p>
            </div>
          ) : (
            <>
              {/* Provider Selection */}
              <div className="settings-section">
                <h4>음성 제공자 선택</h4>
                <div className="providers-grid">
                  {providers.map(provider => (
                    <div 
                      key={provider.id} 
                      className={`provider-card ${settings.provider_id === provider.id ? 'selected' : ''} ${!provider.available ? 'disabled' : ''}`}
                      onClick={() => provider.available && updateSettings({ 
                        provider_id: provider.id, 
                        voice: provider.voices[0] || '' 
                      })}
                    >
                      <div className="provider-header">
                        <div className="provider-name">
                          <h5>{provider.name}</h5>
                          {provider.recommended && (
                            <span className="recommended-badge">추천</span>
                          )}
                        </div>
                        <span className={`cost-badge ${getCostBadgeClass(provider.cost)}`}>
                          {getCostBadgeText(provider.cost)}
                        </span>
                      </div>
                      
                      {provider.description && (
                        <p className="provider-description">{provider.description}</p>
                      )}
                      
                      <div className="provider-info">
                        <span className="voice-count">
                          {provider.voices.length}개 음성
                        </span>
                        {!provider.available && (
                          <span className="unavailable-text">사용 불가</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Voice Selection */}
              {settings.provider_id && (
                <div className="settings-section">
                  <h4>음성 선택</h4>
                  <div className="voice-options">
                    {getProvider(settings.provider_id)?.voices.map(voice => (
                      <div key={voice} className="voice-option">
                        <label className="voice-label">
                          <input
                            type="radio"
                            name="voice"
                            value={voice}
                            checked={settings.voice === voice}
                            onChange={(e) => updateSettings({ voice: e.target.value })}
                          />
                          <span className="voice-name">{voice}</span>
                        </label>
                        <button
                          className={`test-button ${isPlaying ? 'playing' : ''}`}
                          onClick={() => testVoice(settings.provider_id, voice)}
                          disabled={isPlaying}
                        >
                          {isPlaying ? '재생중...' : '테스트'}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Advanced Settings */}
              <div className="settings-section">
                <button 
                  className="advanced-toggle"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                >
                  고급 설정 {showAdvanced ? '▼' : '▶'}
                </button>

                {showAdvanced && (
                  <div className="advanced-settings">
                    <div className="setting-group">
                      <label htmlFor="speed-slider">말하기 속도</label>
                      <div className="slider-container">
                        <input
                          id="speed-slider"
                          type="range"
                          min="0.5"
                          max="2.0"
                          step="0.1"
                          value={settings.speed}
                          onChange={(e) => updateSettings({ speed: parseFloat(e.target.value) })}
                        />
                        <span className="slider-value">{settings.speed.toFixed(1)}x</span>
                      </div>
                    </div>

                    <div className="setting-group">
                      <label htmlFor="pitch-slider">음높이</label>
                      <div className="slider-container">
                        <input
                          id="pitch-slider"
                          type="range"
                          min="0.5"
                          max="2.0"
                          step="0.1"
                          value={settings.pitch}
                          onChange={(e) => updateSettings({ pitch: parseFloat(e.target.value) })}
                        />
                        <span className="slider-value">{settings.pitch.toFixed(1)}x</span>
                      </div>
                    </div>

                    <div className="setting-group">
                      <label htmlFor="volume-slider">음량</label>
                      <div className="slider-container">
                        <input
                          id="volume-slider"
                          type="range"
                          min="0.1"
                          max="2.0"
                          step="0.1"
                          value={settings.volume}
                          onChange={(e) => updateSettings({ volume: parseFloat(e.target.value) })}
                        />
                        <span className="slider-value">{settings.volume.toFixed(1)}x</span>
                      </div>
                    </div>

                    <div className="setting-group">
                      <label htmlFor="language-select">언어</label>
                      <select
                        id="language-select"
                        value={settings.language}
                        onChange={(e) => updateSettings({ language: e.target.value })}
                      >
                        <option value="ko-KR">한국어</option>
                        <option value="en-US">English (US)</option>
                        <option value="ja-JP">日本語</option>
                        <option value="zh-CN">中文</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>

              {/* Test Results */}
              {testResult && (
                <div className="settings-section">
                  <h4>테스트 결과</h4>
                  <div className="test-result">
                    <p><strong>제공자:</strong> {testResult.provider}</p>
                    {testResult.cost_info.cost > 0 && (
                      <p className="cost-info">
                        <strong>비용:</strong> {testResult.cost_info.cost} {testResult.cost_info.currency}
                        (월 예상: {testResult.cost_info.estimated_monthly} {testResult.cost_info.currency})
                      </p>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        <div className="tts-settings-footer">
          <div className="footer-buttons">
            {isPlaying && (
              <button 
                className="stop-button"
                onClick={stopAudio}
              >
                정지
              </button>
            )}
            
            <button 
              className="test-all-button"
              onClick={() => testVoice()}
              disabled={isPlaying || !settings.provider_id || !settings.voice}
            >
              현재 설정 테스트
            </button>
            
            <button 
              className="save-button"
              onClick={saveSettings}
              disabled={isLoading || !settings.provider_id}
            >
              설정 저장
            </button>
            
            <button 
              className="cancel-button"
              onClick={onClose}
            >
              취소
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TtsSettingsPanel;
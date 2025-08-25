# Cerebras AI Fortune VTuber - Deployment Guide

## 🔮 Overview

This guide covers the complete integration of Cerebras AI LLM for fortune generation with the existing Live2D VTuber system, including TTS and real-time chat functionality.

## 📋 Features Implemented

- ✅ **Cerebras AI LLM Integration**: Free Llama 3.1-70B model for personalized fortune generation
- ✅ **4-Card Fortune System**: 일일운세, 타로, 별자리, 사주 with AI-powered responses
- ✅ **Chat-based Responses**: Real-time AI fortune generation in WebSocket chat
- ✅ **TTS Integration**: AI-generated fortune messages converted to speech
- ✅ **Live2D Synchronization**: Emotion and motion sync with fortune content
- ✅ **Graceful Fallback**: Automatic fallback to template-based system when AI unavailable

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/jhbum01/project/VTuber/project/backend
pip install cerebras-cloud-sdk
```

### 2. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
# Cerebras AI Settings
ENABLE_CEREBRAS=true
CEREBRAS_API_KEY=your-cerebras-api-key-here
CEREBRAS_MODEL=llama3.1-70b
CEREBRAS_MAX_TOKENS=1000
CEREBRAS_TEMPERATURE=0.7
CEREBRAS_TIMEOUT=30
CEREBRAS_FALLBACK=true
```

### 3. Get Cerebras API Key

1. Visit [Cerebras Cloud](https://cloud.cerebras.ai/)
2. Sign up for free account
3. Navigate to API Keys section
4. Create new API key
5. Copy key to `.env` file

### 4. Start the Backend

```bash
python run_server.py
```

### 5. Verify Integration

Run the test suite:
```bash
python test_cerebras_integration.py
python test_complete_integration.py
```

## 🔧 API Endpoints

### New AI-Powered Endpoints

#### Daily Fortune
```bash
POST /fortune/ai/daily
Content-Type: application/json

{
    "user_data": {"user_uuid": "user-123"},
    "birth_date": "1990-05-15",
    "zodiac_sign": "TAURUS",
    "force_regenerate": false
}
```

#### Tarot Fortune
```bash
POST /fortune/ai/tarot
Content-Type: application/json

{
    "user_data": {"user_uuid": "user-123"},
    "question": "내 연애운은 어떨까?",
    "question_type": "love"
}
```

#### Zodiac Fortune
```bash
POST /fortune/ai/zodiac
Content-Type: application/json

{
    "user_data": {"user_uuid": "user-123"},
    "zodiac_sign": "TAURUS",
    "period": "daily"
}
```

#### Saju Fortune
```bash
POST /fortune/ai/saju
Content-Type: application/json

{
    "birth_date": "1990-05-15",
    "birth_time": "14:30",
    "user_data": {"user_uuid": "user-123"}
}
```

#### AI Service Status
```bash
GET /fortune/ai/status
```

## 📡 WebSocket Integration

The chat WebSocket now automatically detects fortune requests and responds with AI-generated content:

```javascript
// Frontend example
const ws = new WebSocket('ws://localhost:8000/ws/chat/session-123');

// Send fortune request
ws.send(JSON.stringify({
    type: 'fortune_request',
    data: {
        fortune_type: 'daily',
        question: '오늘 운세가 어떨까?',
        additional_info: {
            birth_date: '1990-05-15',
            zodiac: 'taurus'
        }
    }
}));

// Receive AI response with TTS and Live2D data
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'fortune_result') {
        const {
            fortune_result,
            character_message,
            tts_text,
            live2d_emotion,
            live2d_motion,
            enable_tts,
            enable_live2d
        } = data.data;
        
        // Process fortune display
        // Trigger TTS playback
        // Animate Live2D character
    }
};
```

## 🎭 Live2D Integration

### Emotion Mapping

AI responses include appropriate emotions:
- `joy`: Positive fortune results (score ≥ 70)
- `mystical`: Tarot and spiritual content
- `comfort`: Moderate fortune results (50-69)
- `concern`: Lower fortune results (30-49)
- `neutral`: Default/balanced content

### Motion Mapping

Different motions for different fortune types:
- `crystal_gaze`: Daily fortunes
- `card_draw`: Tarot readings
- `blessing`: Zodiac fortunes
- `special_reading`: Saju/Oriental fortunes

### WebSocket Response Format

```json
{
    "type": "fortune_result",
    "data": {
        "fortune_result": {
            "fortune_id": "ai-123",
            "type": "daily",
            "message": "AI-generated personalized fortune...",
            "score": 85,
            "live2d_emotion": "joy",
            "live2d_motion": "crystal_gaze"
        },
        "character_message": "AI-generated message for TTS",
        "tts_text": "Same as character_message",
        "live2d_emotion": "joy",
        "live2d_motion": "crystal_gaze",
        "enable_tts": true,
        "enable_live2d": true
    }
}
```

## 🔊 TTS Integration

### Automatic TTS Generation

When a fortune is generated via chat:
1. AI generates personalized fortune message
2. System extracts TTS-friendly text
3. WebSocket sends `tts_text` field
4. Frontend triggers TTS playback
5. Live2D lip sync activates automatically

### Message Extraction Priority

1. `fortune_result.message` (AI-generated primary message)
2. `fortune_result.overall.message` (Overall fortune summary)
3. `fortune_result.advice` (Advice text)
4. Default message based on fortune type

### TTS Integration Points

```python
# In chat_service.py
fortune_message = self._extract_fortune_message(fortune_result, fortune_type)

await self._send_to_websocket(websocket, {
    "type": "fortune_result", 
    "data": {
        "tts_text": fortune_message,
        "live2d_emotion": live2d_emotion,
        "live2d_motion": live2d_motion,
        "enable_tts": True,
        "enable_live2d": True
    }
})
```

## ⚙️ Configuration Options

### Cerebras Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_CEREBRAS` | `false` | Enable/disable Cerebras AI |
| `CEREBRAS_API_KEY` | `""` | Your API key |
| `CEREBRAS_MODEL` | `llama3.1-70b` | Model to use |
| `CEREBRAS_MAX_TOKENS` | `1000` | Max response tokens |
| `CEREBRAS_TEMPERATURE` | `0.7` | Generation creativity |
| `CEREBRAS_TIMEOUT` | `30` | Request timeout (seconds) |
| `CEREBRAS_FALLBACK` | `true` | Enable fallback to legacy |

### Fortune Types

Each fortune type has specialized AI prompts:

- **Daily**: Personalized daily guidance with categories (love, money, health, work)
- **Tarot**: 3-card reading interpretation with deep analysis
- **Zodiac**: Astrological insights based on birth date and sign
- **Saju**: Traditional Oriental fortune based on birth date/time

## 🧪 Testing

### Unit Tests

```bash
# Test Cerebras integration
python test_cerebras_integration.py

# Test complete workflow
python test_complete_integration.py
```

### Manual Testing

1. **API Testing**:
   ```bash
   curl -X POST http://localhost:8000/fortune/ai/daily \
     -H "Content-Type: application/json" \
     -d '{"user_data": {"user_uuid": "test"}}'
   ```

2. **WebSocket Testing**:
   - Connect to `/ws/chat/session-123`
   - Send fortune requests
   - Verify AI responses with TTS/Live2D data

3. **Fallback Testing**:
   - Disable Cerebras (set `ENABLE_CEREBRAS=false`)
   - Verify legacy fortune generation works
   - Re-enable and verify AI generation resumes

## 🚨 Troubleshooting

### Common Issues

#### 1. "CEREBRAS_API_KEY가 설정되지 않았습니다"
- Add your API key to `.env` file
- Restart the server
- Verify key is correct

#### 2. "AI_GENERATION_FAILED"
- Check API key validity
- Verify internet connection
- Check Cerebras service status
- System automatically falls back to legacy

#### 3. TTS not playing
- Verify `enable_tts: true` in WebSocket response
- Check frontend TTS integration
- Ensure `tts_text` field is populated

#### 4. Live2D not animating  
- Verify `enable_live2d: true` in response
- Check `live2d_emotion` and `live2d_motion` fields
- Ensure frontend Live2D integration is working

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG python run_server.py
```

### Health Checks

```bash
# Check AI service status
curl http://localhost:8000/fortune/ai/status

# Check overall fortune service
curl http://localhost:8000/fortune/health
```

## 📊 Performance

### Expected Response Times

- **AI Fortune Generation**: 2-5 seconds
- **Fallback Generation**: <500ms  
- **WebSocket Response**: <100ms after generation
- **TTS Generation**: 1-3 seconds
- **Live2D Animation**: Real-time

### Resource Usage

- **Memory**: +50MB for Cerebras client
- **CPU**: Minimal (network-bound)
- **Network**: ~1KB per request/response

### Caching

- Daily fortunes: 24-hour cache
- Zodiac fortunes: 24-hour cache  
- Tarot readings: 1-hour cache
- Saju readings: 1-hour cache

## 🔐 Security

- API keys stored in environment variables
- Input validation on all endpoints
- Rate limiting: 60 requests/minute
- Content filtering for inappropriate requests
- Secure WebSocket connections supported

## 🚀 Production Deployment

### Environment Variables

Ensure these are set in production:
```env
ENABLE_CEREBRAS=true
CEREBRAS_API_KEY=your-production-key
CEREBRAS_FALLBACK=true
LOG_LEVEL=INFO
```

### Monitoring

Monitor these endpoints:
- `/fortune/ai/status` - AI service health
- `/fortune/health` - Overall service health
- WebSocket connection counts
- API response times

### Scaling

- Cerebras API is serverless (auto-scaling)
- Backend can handle multiple concurrent requests
- Consider connection pooling for high traffic

## 📝 Integration Summary

The complete integration provides:

1. **Seamless AI Integration**: Cerebras LLM generates personalized fortunes
2. **4-Card System**: All fortune types supported with AI enhancement  
3. **Real-time Chat**: AI responses in WebSocket chat
4. **TTS + Live2D**: Automatic speech and animation synchronization
5. **Robust Fallback**: Graceful degradation when AI unavailable
6. **Frontend Compatible**: All existing APIs work with AI enhancement

The system maintains 100% backward compatibility while adding powerful AI capabilities for enhanced user experience.

## 🆘 Support

For issues:
1. Check logs for specific error messages
2. Verify environment configuration  
3. Test with both AI enabled/disabled
4. Check Cerebras API status
5. Review integration test results

The system is designed to be resilient - if AI fails, fortune generation continues with the existing template-based system.
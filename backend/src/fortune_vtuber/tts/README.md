# Phase 8.1: Multi-Provider TTS System

This document describes the implementation of Phase 8.1 of the TTS Live2D integration system for the Fortune VTuber application.

## Overview

The new multi-provider TTS system provides:

- **Multiple TTS providers** with intelligent fallback chains
- **User-configurable settings** with provider preferences
- **Korean voice synthesis optimization** (ko-KR-SunHiNeural for Edge TTS)
- **Free-to-paid provider prioritization** (Edge TTS → SiliconFlow TTS → Azure/OpenAI TTS)
- **Live2D integration** with synchronized lip sync and expressions
- **Async-first design** for optimal performance

## Architecture

```
├── tts/
│   ├── __init__.py              # Package exports
│   ├── tts_interface.py         # Base interface and data models
│   ├── tts_factory.py           # Provider factory with auto-detection
│   ├── tts_config_manager.py    # User preferences and configuration
│   ├── live2d_tts_manager.py    # Main integration manager
│   ├── providers/               # Provider implementations
│   │   ├── __init__.py
│   │   ├── edge_tts.py         # Microsoft Edge TTS (free)
│   │   ├── siliconflow_tts.py  # SiliconFlow TTS (free tier)
│   │   ├── azure_tts.py        # Azure Cognitive Services (paid)
│   │   └── openai_tts.py       # OpenAI TTS (paid)
│   └── README.md               # This file
```

## Provider Hierarchy

### 1. Edge TTS (Primary - Free)
- **Cost**: Free
- **Quality**: High
- **Korean Voice**: `ko-KR-SunHiNeural`
- **Languages**: Korean, English, Japanese, Chinese
- **API Required**: No
- **Rate Limit**: ~60 requests/minute

### 2. SiliconFlow TTS (Secondary - Free Tier)
- **Cost**: Free tier available
- **Quality**: High
- **Languages**: Korean, English, Chinese
- **API Required**: Yes (API key needed)
- **Rate Limit**: ~30 requests/minute

### 3. Azure TTS (Tertiary - Paid)
- **Cost**: Paid service
- **Quality**: Premium
- **Languages**: Korean, English, Japanese, Chinese
- **API Required**: Yes (API key + region)
- **Rate Limit**: ~200 requests/minute

### 4. OpenAI TTS (Quaternary - Paid)
- **Cost**: Paid service
- **Quality**: Premium
- **Languages**: Multiple languages
- **API Required**: Yes (API key)
- **Rate Limit**: ~50 requests/minute

## Usage Examples

### Basic TTS Generation

```python
from fortune_vtuber.tts import live2d_tts_manager, Live2DTTSRequest, EmotionType

# Create request
request = Live2DTTSRequest(
    text="안녕하세요! 오늘의 운세를 알려드릴게요.",
    user_id="user123",
    language="ko-KR",
    emotion=EmotionType.HAPPY,
    enable_lipsync=True,
    enable_expressions=True
)

# Generate TTS with Live2D integration
result = await live2d_tts_manager.generate_speech_with_animation(request)

# Access results
print(f"Provider used: {result.provider_info['provider_id']}")
print(f"Duration: {result.total_duration:.2f}s")
print(f"Audio size: {len(result.tts_result.audio_data)} bytes")
```

### User Preference Management

```python
from fortune_vtuber.tts import tts_config_manager

# Update user preferences
preferences = tts_config_manager.update_user_preferences(
    user_id="user123",
    preferred_provider="edge_tts",
    preferred_voice="ko-KR-SunHiNeural",
    speech_speed=1.1,
    speech_pitch=1.0,
    enable_fallback=True
)

# Get available providers for user
providers = tts_config_manager.get_user_tts_options("user123")
```

### Provider Configuration

```python
from fortune_vtuber.tts import tts_factory

# Configure SiliconFlow TTS
await tts_factory.create_provider(
    "siliconflow_tts",
    api_key="your_api_key",
    api_url="https://api.siliconflow.cn/v1/audio/speech"
)

# Check provider availability
providers = await tts_factory.get_available_providers("ko-KR")
print(f"Available providers: {providers}")
```

### Live2D Streaming

```python
# Stream TTS with real-time Live2D synchronization
async for event in live2d_tts_manager.stream_live2d_tts(request):
    if event["type"] == "tts_stream_start":
        # Audio data available
        audio_data = event["data"]["audio_data"]
        
    elif event["type"] == "live2d_sync":
        # Live2D synchronization event
        sync_event = event["data"]["event"]
        if sync_event["type"] == "expression":
            # Update Live2D expression
            pass
        elif sync_event["type"] == "lipsync":
            # Update mouth parameters
            pass
```

## API Endpoints

### Generate TTS
```http
POST /api/tts/generate
Content-Type: application/json

{
    "text": "안녕하세요! 오늘의 운세를 알려드릴게요.",
    "user_id": "user123",
    "language": "ko-KR",
    "emotion": "happy",
    "enable_lipsync": true,
    "enable_expressions": true
}
```

### Get Available Providers
```http
GET /api/tts/providers?user_id=user123&language=ko-KR
```

### Update User Preferences
```http
POST /api/tts/user/user123/preferences
Content-Type: application/json

{
    "preferred_provider": "edge_tts",
    "preferred_voice": "ko-KR-SunHiNeural",
    "speech_speed": 1.1,
    "enable_fallback": true
}
```

### Configure Provider
```http
POST /api/tts/providers/configure
Content-Type: application/json

{
    "provider_id": "siliconflow_tts",
    "api_key": "your_api_key",
    "api_url": "https://api.siliconflow.cn/v1/audio/speech"
}
```

## Environment Configuration

Add the following to your `.env` file:

```env
# TTS Configuration
FORTUNE_TTS_ENABLED=true
FORTUNE_TTS_DEFAULT_LANGUAGE=ko-KR
FORTUNE_TTS_PREFERRED_PROVIDER=edge_tts
FORTUNE_TTS_FALLBACK_ENABLED=true

# Provider API Keys (optional)
FORTUNE_TTS_SILICONFLOW_API_KEY=your_siliconflow_key
FORTUNE_TTS_AZURE_API_KEY=your_azure_key
FORTUNE_TTS_AZURE_REGION=your_azure_region
FORTUNE_TTS_OPENAI_API_KEY=your_openai_key

# Live2D Integration
FORTUNE_TTS_LIPSYNC_ENABLED=true
FORTUNE_TTS_EXPRESSIONS_ENABLED=true
FORTUNE_TTS_MOTIONS_ENABLED=true

# Performance
FORTUNE_TTS_CACHE_ENABLED=true
FORTUNE_TTS_CACHE_MAX_SIZE=100
FORTUNE_TTS_MAX_TEXT_LENGTH=5000
```

## Installation Requirements

### Core Requirements
```bash
pip install aiohttp  # For HTTP API calls
pip install pydantic  # For data validation
```

### Provider-Specific Requirements
```bash
# Edge TTS (recommended)
pip install edge-tts

# SiliconFlow TTS (optional)
pip install aiohttp

# Azure TTS (optional)
pip install azure-cognitiveservices-speech

# OpenAI TTS (optional)
pip install openai
```

## Fallback Chain Logic

1. **Primary**: Try user's preferred provider
2. **Secondary**: Try Edge TTS (if not preferred)
3. **Tertiary**: Try SiliconFlow TTS (if API key available)
4. **Quaternary**: Try Azure TTS (if API key available)
5. **Final**: Try OpenAI TTS (if API key available)

Each provider is checked for:
- Availability (API keys, network connectivity)
- Language support
- Rate limiting status
- Previous error rates

## Live2D Integration Features

### Lip Sync Generation
- Phoneme analysis for Korean text
- Mouth parameter mapping for Live2D models
- Real-time streaming with 50ms updates

### Expression Mapping
- Emotion-based expression selection
- Intensity adjustment based on content
- Smooth transitions between expressions

### Motion Triggers
- Context-aware motion selection
- Fortune-telling specific motions (card_draw, crystal_gaze)
- Synchronized timing with audio

## Performance Optimizations

- **Caching**: Audio and lip sync data caching
- **Rate Limiting**: Built-in rate limiting per provider
- **Connection Pooling**: Reuse HTTP connections
- **Async Processing**: Non-blocking TTS generation
- **Fallback Chains**: Minimize service interruptions

## Error Handling

- **Provider Failures**: Automatic fallback to next provider
- **Rate Limiting**: Exponential backoff and retry
- **Network Issues**: Timeout handling and connection recovery
- **API Errors**: Detailed error reporting and logging

## Monitoring and Statistics

```python
# Get system statistics
stats = live2d_tts_manager.get_tts_statistics()

# Example output:
{
    "providers": {
        "edge_tts": {
            "success_rate": 0.95,
            "average_response_time": 1.2,
            "total_requests": 1000
        }
    },
    "cache_size": 45,
    "active_sessions": 3
}
```

## Backward Compatibility

The new system maintains full backward compatibility with the existing `TTSIntegrationService` class:

```python
# Legacy usage still works
from fortune_vtuber.live2d.tts_integration import tts_service

request = TTSRequest(
    text="안녕하세요",
    voice_profile=voice_profile,
    enable_lipsync=True
)

result = await tts_service.synthesize_speech(request)
```

The legacy interface automatically converts to the new system internally, providing enhanced reliability and provider options.

## Future Enhancements (Phase 8.2+)

- Real-time voice cloning
- Emotion intensity analysis
- Multi-language mixing
- Voice style transfer
- Advanced lip sync algorithms
- Integration with LLM emotion detection
"""
TTS (Text-to-Speech) Provider System for Fortune VTuber

Multi-provider TTS system with fallback chains and Live2D integration support.
Based on Open-LLM-VTuber patterns with Fortune-specific adaptations.

Features:
- Multiple TTS provider support (Edge TTS, SiliconFlow TTS, Azure TTS, OpenAI TTS)
- Intelligent fallback chain: free → paid providers
- User-configurable TTS settings
- Korean voice synthesis optimization
- Async-first design for Live2D integration
"""

from .tts_interface import TTSInterface, TTSResult, TTSRequest, EmotionType
from .tts_factory import TTSProviderFactory, tts_factory
from .tts_config_manager import TTSConfigManager, tts_config_manager
from .live2d_tts_manager import Live2DTTSManager, Live2DTTSRequest, Live2DTTSResult, live2d_tts_manager

# Provider imports (with graceful fallback)
try:
    from .providers.edge_tts import EdgeTTSProvider
except ImportError:
    EdgeTTSProvider = None

try:
    from .providers.siliconflow_tts import SiliconFlowTTSProvider
except ImportError:
    SiliconFlowTTSProvider = None

__all__ = [
    "TTSInterface",
    "TTSResult", 
    "TTSRequest",
    "EmotionType",
    "TTSProviderFactory",
    "TTSConfigManager", 
    "Live2DTTSManager",
    "Live2DTTSRequest",
    "Live2DTTSResult",
    "tts_factory",
    "tts_config_manager",
    "live2d_tts_manager"
]

# Add provider classes if available
if EdgeTTSProvider is not None:
    __all__.append("EdgeTTSProvider")
    
if SiliconFlowTTSProvider is not None:
    __all__.append("SiliconFlowTTSProvider")
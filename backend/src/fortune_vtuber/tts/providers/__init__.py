"""
TTS Provider Implementations

Provider implementations following the TTSInterface pattern.
Each provider implements specific TTS service integration.
"""

# Provider imports will be added as they are implemented
__all__ = []

try:
    from .edge_tts import EdgeTTSProvider
    __all__.append("EdgeTTSProvider")
except ImportError:
    pass

try:
    from .siliconflow_tts import SiliconFlowTTSProvider
    __all__.append("SiliconFlowTTSProvider")
except ImportError:
    pass

try:
    from .azure_tts import AzureTTSProvider
    __all__.append("AzureTTSProvider")
except ImportError:
    pass

try:
    from .openai_tts import OpenAITTSProvider
    __all__.append("OpenAITTSProvider")
except ImportError:
    pass
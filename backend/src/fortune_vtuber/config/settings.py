"""
Fortune VTuber Backend Settings

Environment configuration management for the Live2D Fortune VTuber application.
Based on Open-LLM-VTuber architecture with Fortune-specific adaptations.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
import secrets


class DatabaseSettings(BaseModel):
    """Database configuration settings"""
    
    # SQLite settings (development/testing)
    url: str = Field(default="sqlite+aiosqlite:///./fortune_vtuber.db")
    echo: bool = Field(default=False)
    
    # MariaDB settings (production)
    host: Optional[str] = Field(default=None)
    port: Optional[int] = Field(default=3306)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    database: Optional[str] = Field(default=None)
    
    # Connection pool settings
    pool_size: int = Field(default=5)
    max_overflow: int = Field(default=10)
    pool_timeout: int = Field(default=30)
    pool_recycle: int = Field(default=3600)
    
    @field_validator('url')
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format"""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v


class SecuritySettings(BaseModel):
    """Security configuration settings"""
    
    # JWT settings
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)
    
    # Session settings
    session_timeout_minutes: int = Field(default=60)
    session_cleanup_interval: int = Field(default=300)  # 5 minutes
    
    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_per_minute: int = Field(default=60)
    fortune_rate_limit_per_hour: int = Field(default=10)
    websocket_rate_limit_per_minute: int = Field(default=300)
    
    # Content filtering
    content_filter_enabled: bool = Field(default=True)
    content_filter_strict_mode: bool = Field(default=True)
    ai_content_analysis_enabled: bool = Field(default=False)
    
    # Data encryption
    encryption_key: Optional[str] = Field(default=None)
    hash_salt: str = Field(default_factory=lambda: secrets.token_urlsafe(16))
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is sufficiently strong"""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v


class Live2DSettings(BaseModel):
    """Live2D model configuration settings"""
    
    # Model settings
    default_model: str = "mira"
    models_directory: str = "static/live2d"
    
    # Emotion and motion settings
    default_emotion: str = "neutral"
    emotion_duration: int = 3000  # milliseconds
    motion_duration: int = 5000   # milliseconds
    
    # Model configuration
    model_config: Dict[str, Any] = {
        "mira": {
            "name": "미라",
            "model_path": "/static/live2d/mira/mira.model3.json",
            "emotions": {
                "neutral": 0, "joy": 1, "thinking": 2, "concern": 3,
                "surprise": 4, "mystical": 5, "comfort": 6, "playful": 7
            },
            "motions": {
                "greeting": "motions/greeting.motion3.json",
                "card_draw": "motions/card_draw.motion3.json",
                "crystal_gaze": "motions/crystal_gaze.motion3.json",
                "blessing": "motions/blessing.motion3.json",
                "special_reading": "motions/special_reading.motion3.json",
                "thinking_pose": "motions/thinking_pose.motion3.json"
            }
        }
    }


class TTSSettings(BaseModel):
    """TTS (Text-to-Speech) configuration settings"""
    
    # TTS system enabled
    tts_enabled: bool = Field(default=True)
    
    # Default TTS settings
    default_language: str = Field(default="ko-KR")
    default_voice: str = Field(default="ko-KR-SunHiNeural")
    default_speed: float = Field(default=1.0)
    default_pitch: float = Field(default=1.0)
    default_volume: float = Field(default=1.0)
    
    # Provider configuration
    preferred_provider: str = Field(default="edge_tts")
    fallback_enabled: bool = Field(default=True)
    fallback_chain: List[str] = Field(default_factory=lambda: ["edge_tts", "siliconflow_tts", "azure_tts", "openai_tts"])
    
    # Provider API keys (optional)
    siliconflow_api_key: Optional[str] = Field(default=None)
    siliconflow_api_url: Optional[str] = Field(default=None)
    azure_api_key: Optional[str] = Field(default=None)
    azure_region: Optional[str] = Field(default=None)
    openai_api_key: Optional[str] = Field(default=None)
    openai_base_url: Optional[str] = Field(default=None)
    
    # Live2D integration
    lipsync_enabled: bool = Field(default=True)
    expressions_enabled: bool = Field(default=True)
    motions_enabled: bool = Field(default=True)
    
    # Performance settings
    cache_enabled: bool = Field(default=True)
    cache_max_size: int = Field(default=100)
    cache_ttl_hours: int = Field(default=24)
    rate_limiting_enabled: bool = Field(default=True)
    
    # Audio settings
    audio_format: str = Field(default="mp3")
    sample_rate: int = Field(default=24000)
    max_text_length: int = Field(default=5000)


class FortuneSettings(BaseModel):
    """Fortune generation configuration settings"""
    
    # Fortune types enabled
    daily_fortune_enabled: bool = Field(default=True)
    tarot_fortune_enabled: bool = Field(default=True)
    zodiac_fortune_enabled: bool = Field(default=True)
    oriental_fortune_enabled: bool = Field(default=False)  # Future feature
    
    # Cache settings
    daily_fortune_cache_hours: int = Field(default=24)
    zodiac_weekly_cache_hours: int = Field(default=168)  # 1 week
    zodiac_monthly_cache_hours: int = Field(default=720)  # 30 days
    
    # Content generation
    max_fortune_length: int = Field(default=500)
    min_fortune_length: int = Field(default=50)
    
    # Tarot settings
    tarot_cards_per_reading: int = Field(default=3)
    tarot_spread_types: List[str] = Field(default_factory=lambda: ["past_present_future", "single_card"])
    
    # AI integration (placeholder for future LLM integration)
    ai_generation_enabled: bool = Field(default=False)
    ai_model_name: Optional[str] = Field(default=None)
    ai_api_key: Optional[str] = Field(default=None)


class ServerSettings(BaseModel):
    """Server configuration settings"""
    
    # Basic server settings
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)
    
    # CORS settings
    cors_enabled: bool = Field(default=True)
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])  # Restrict in production
    cors_credentials: bool = Field(default=True)
    cors_methods: List[str] = Field(default_factory=lambda: ["*"])
    cors_headers: List[str] = Field(default_factory=lambda: ["*"])
    
    # Static files
    static_files_enabled: bool = Field(default=True)
    static_directory: str = Field(default="static")
    static_url_path: str = Field(default="/static")
    
    # WebSocket settings
    websocket_enabled: bool = Field(default=True)
    websocket_ping_interval: int = Field(default=20)
    websocket_ping_timeout: int = Field(default=10)
    websocket_close_timeout: int = Field(default=10)
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v):
        """Validate port number range"""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


class LoggingSettings(BaseModel):
    """Logging configuration settings"""
    
    # Log levels
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    
    # File logging
    log_to_file: bool = Field(default=True)
    log_directory: str = Field(default="logs")
    log_rotation: str = Field(default="10 MB")
    log_retention: str = Field(default="30 days")
    
    # Specific loggers
    security_log_enabled: bool = Field(default=True)
    content_filter_log_enabled: bool = Field(default=True)
    api_access_log_enabled: bool = Field(default=True)
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class Settings(BaseSettings):
    """Main application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="FORTUNE_",
        extra="ignore"
    )
    
    # Application info
    app_name: str = Field(default="Fortune VTuber Backend")
    app_version: str = Field(default="1.0.0")
    app_description: str = Field(default="Live2D Fortune VTuber Backend Service")
    environment: str = Field(default="development")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    live2d: Live2DSettings = Field(default_factory=Live2DSettings)
    tts: TTSSettings = Field(default_factory=TTSSettings)
    fortune: FortuneSettings = Field(default_factory=FortuneSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    cache_dir: Path = Field(default_factory=lambda: Path("cache"))
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment setting"""
        valid_envs = ["development", "testing", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def get_database_url(self) -> str:
        """Get the appropriate database URL"""
        if self.database.host and self.database.username:
            # MariaDB connection
            return (
                f"mysql+aiomysql://{self.database.username}:{self.database.password}"
                f"@{self.database.host}:{self.database.port}/{self.database.database}"
                f"?charset=utf8mb4"
            )
        else:
            # SQLite connection
            return self.database.url
    
    def setup_directories(self) -> None:
        """Create necessary directories"""
        directories = [
            self.data_dir,
            self.cache_dir,
            Path(self.logging.log_directory),
            Path(self.server.static_directory),
            Path(self.live2d.models_directory)
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure directories exist
settings.setup_directories()


# Environment-specific configuration
def get_settings() -> Settings:
    """Get settings instance (for dependency injection)"""
    return settings


def load_settings_from_file(config_file: str) -> Settings:
    """Load settings from a specific configuration file"""
    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    # Create new settings instance with specific config file
    return Settings(_env_file=config_file)


# Development helpers
def print_current_settings():
    """Print current settings (for debugging)"""
    print("Current Fortune VTuber Settings:")
    print(f"Environment: {settings.environment}")
    print(f"Database URL: {settings.get_database_url()}")
    print(f"Server: {settings.server.host}:{settings.server.port}")
    print(f"Debug Mode: {settings.server.debug}")
    print(f"Content Filter: {settings.security.content_filter_enabled}")
    print(f"Rate Limiting: {settings.security.rate_limit_enabled}")


if __name__ == "__main__":
    print_current_settings()
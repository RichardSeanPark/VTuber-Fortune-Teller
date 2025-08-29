"""
Cerebras AI 설정 관리
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

from ..fortune.cerebras_engine import CerebrasConfig


class CerebrasSettings(BaseSettings):
    """Cerebras AI 환경 설정"""
    
    # API 설정
    cerebras_api_key: str = Field(
        default="",
        description="Cerebras API Key"
    )
    cerebras_model: str = Field(
        default="llama3.1-8b",
        description="Cerebras 모델명"
    )
    cerebras_max_tokens: int = Field(
        default=1000,
        description="최대 토큰 수"
    )
    cerebras_temperature: float = Field(
        default=0.7,
        description="생성 온도"
    )
    cerebras_timeout: int = Field(
        default=30,
        description="API 타임아웃 (초)"
    )
    
    # 기능 제어
    enable_cerebras: bool = Field(
        default=False,
        description="Cerebras AI 사용 여부"
    )
    cerebras_fallback: bool = Field(
        default=True,
        description="실패 시 기본 엔진 사용 여부"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = ""
        case_sensitive = False
        extra = "ignore"  # 추가 필드 무시


# 전역 설정 인스턴스
cerebras_settings = CerebrasSettings()


def get_cerebras_config() -> Optional[CerebrasConfig]:
    """Cerebras 설정 생성"""
    if not cerebras_settings.enable_cerebras or not cerebras_settings.cerebras_api_key:
        return None
    
    return CerebrasConfig(
        api_key=cerebras_settings.cerebras_api_key,
        model=cerebras_settings.cerebras_model,
        max_tokens=cerebras_settings.cerebras_max_tokens,
        temperature=cerebras_settings.cerebras_temperature,
        timeout=cerebras_settings.cerebras_timeout
    )


def is_cerebras_enabled() -> bool:
    """Cerebras 사용 가능 여부 확인"""
    return (
        cerebras_settings.enable_cerebras and 
        bool(cerebras_settings.cerebras_api_key) and
        cerebras_settings.cerebras_api_key.strip() != ""
    )


def validate_cerebras_config() -> tuple[bool, str]:
    """Cerebras 설정 유효성 검사"""
    if not cerebras_settings.cerebras_api_key:
        return False, "CEREBRAS_API_KEY가 설정되지 않았습니다."
    
    if cerebras_settings.cerebras_max_tokens <= 0:
        return False, "max_tokens는 0보다 커야 합니다."
    
    if not (0.0 <= cerebras_settings.cerebras_temperature <= 2.0):
        return False, "temperature는 0.0-2.0 범위여야 합니다."
    
    if cerebras_settings.cerebras_timeout <= 0:
        return False, "timeout은 0보다 커야 합니다."
    
    return True, "설정이 유효합니다."
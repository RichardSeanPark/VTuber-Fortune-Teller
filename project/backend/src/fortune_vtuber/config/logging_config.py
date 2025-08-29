"""
Fortune VTuber Backend Logging Configuration

통합 로깅 시스템 설정으로 중복 로그 방지 및 성능 최적화
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# 로그 디렉토리 설정
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logging(config_name: str = "development") -> None:
    """
    통합 로깅 시스템 설정
    
    Args:
        config_name: 설정 이름 (development, production, testing)
    """
    
    # 기본 로깅 설정
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "security": {
                "format": "%(asctime)s - SECURITY - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "performance": {
                "format": "%(asctime)s - PERF - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "fortune_vtuber.config.logging_config.JSONFormatter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(LOG_DIR / "fortune_vtuber.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8"
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "security",
                "filename": str(LOG_DIR / "security.log"),
                "maxBytes": 5242880,  # 5MB
                "backupCount": 10,
                "encoding": "utf8"
            },
            "performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "performance",
                "filename": str(LOG_DIR / "performance.log"),
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
                "encoding": "utf8"
            },
            "error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(LOG_DIR / "error.log"),
                "maxBytes": 5242880,  # 5MB
                "backupCount": 10,
                "encoding": "utf8"
            }
        },
        "loggers": {
            # 메인 애플리케이션 로거
            "fortune_vtuber": {
                "level": "DEBUG" if config_name == "development" else "INFO",
                "handlers": ["console", "file", "error"],
                "propagate": False
            },
            # 보안 로거 (중복 방지)
            "security": {
                "level": "INFO",
                "handlers": ["console", "security"],
                "propagate": False
            },
            # 성능 로거
            "performance": {
                "level": "INFO",
                "handlers": ["console", "performance"],
                "propagate": False
            },
            # TTS 로거
            "fortune_vtuber.tts": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # Live2D 로거
            "fortune_vtuber.live2d": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 데이터베이스 로거
            "fortune_vtuber.database": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False
            },
            # 외부 라이브러리 로거 레벨 조정
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "WARNING" if config_name == "production" else "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console", "error"]
        }
    }
    
    # 환경별 설정 조정
    if config_name == "production":
        # 프로덕션 환경에서는 콘솔 로그 레벨 높이기
        logging_config["handlers"]["console"]["level"] = "WARNING"
        logging_config["loggers"]["fortune_vtuber"]["level"] = "INFO"
        
    elif config_name == "testing":
        # 테스트 환경에서는 파일 로그 비활성화
        for logger_config in logging_config["loggers"].values():
            if "file" in logger_config["handlers"]:
                logger_config["handlers"].remove("file")
    
    # 로깅 설정 적용
    logging.config.dictConfig(logging_config)
    
    # 루트 로거 설정으로 기본 동작 제어
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)


class JSONFormatter(logging.Formatter):
    """JSON 포맷 로거"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        
        # 예외 정보가 있다면 추가
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        # 추가 속성이 있다면 포함
        if hasattr(record, 'extra_data'):
            log_entry["extra"] = record.extra_data
            
        return json.dumps(log_entry, ensure_ascii=False)


class PerformanceFilter(logging.Filter):
    """성능 로그 필터"""
    
    def filter(self, record):
        # 5.6초 이상 걸리는 요청만 로그
        if hasattr(record, 'duration') and record.duration >= 5.0:
            return True
        return False


def get_logger(name: str) -> logging.Logger:
    """
    통합 로거 팩토리 함수
    
    Args:
        name: 로거 이름
        
    Returns:
        설정된 로거 인스턴스
    """
    return logging.getLogger(name)


def log_tts_performance(provider: str, duration: float, text_length: int) -> None:
    """
    TTS 성능 로그 기록 (5.6초 문제 모니터링용)
    
    Args:
        provider: TTS 제공자
        duration: 소요 시간 (초)
        text_length: 텍스트 길이
    """
    perf_logger = get_logger("performance")
    
    if duration >= 5.0:
        perf_logger.warning(
            f"TTS_SLOW_RESPONSE - Provider: {provider}, "
            f"Duration: {duration:.2f}s, Text Length: {text_length}"
        )
    elif duration >= 3.0:
        perf_logger.info(
            f"TTS_MODERATE_RESPONSE - Provider: {provider}, "
            f"Duration: {duration:.2f}s, Text Length: {text_length}"
        )


def log_security_event_deduplicated(event_type: str, client_ip: str, details: Dict[str, Any]) -> None:
    """
    중복 방지된 보안 이벤트 로깅
    
    Args:
        event_type: 이벤트 타입
        client_ip: 클라이언트 IP
        details: 추가 정보
    """
    security_logger = get_logger("security")
    
    # 이벤트 해시 생성으로 중복 방지
    event_hash = hash(f"{event_type}:{client_ip}:{details.get('endpoint', '')}")
    
    # 간단한 중복 방지 (메모리 기반, 프로덕션에서는 Redis 등 사용 권장)
    if not hasattr(log_security_event_deduplicated, '_recent_events'):
        log_security_event_deduplicated._recent_events = set()
    
    if event_hash not in log_security_event_deduplicated._recent_events:
        log_security_event_deduplicated._recent_events.add(event_hash)
        
        # 최대 1000개의 최근 이벤트만 추적
        if len(log_security_event_deduplicated._recent_events) > 1000:
            log_security_event_deduplicated._recent_events.clear()
        
        security_logger.info(
            f"SECURITY_EVENT - Type: {event_type}, IP: {client_ip}, "
            f"Details: {json.dumps(details, ensure_ascii=False)}"
        )
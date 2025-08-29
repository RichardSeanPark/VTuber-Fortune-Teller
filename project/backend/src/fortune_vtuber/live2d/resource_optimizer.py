"""
Live2D 리소스 최적화 관리자

텍스처 캐싱, 모델 로딩 최적화, 메모리 관리 등을 담당
디바이스별 품질 조정과 성능 모니터링 기능 제공
"""

import os
import json
import hashlib
import time
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class DeviceType(str, Enum):
    """디바이스 타입"""
    DESKTOP = "desktop"
    TABLET = "tablet"
    MOBILE = "mobile"
    LOW_END = "low_end"


class QualityLevel(str, Enum):
    """품질 레벨"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ResourceMetrics:
    """리소스 사용량 메트릭"""
    memory_usage: int  # bytes
    texture_count: int
    model_count: int
    cache_hit_rate: float
    loading_time: float  # seconds
    last_updated: datetime


@dataclass
class OptimizationConfig:
    """최적화 설정"""
    quality_level: QualityLevel
    texture_scale: float
    enable_compression: bool
    cache_size_mb: int
    preload_textures: bool
    lazy_load_motions: bool
    gc_interval_seconds: int


class Live2DResourceOptimizer:
    """Live2D 리소스 최적화 관리자"""
    
    def __init__(self, base_path: str = "/home/jhbum01/project/VTuber/project/backend/static/live2d"):
        self.base_path = Path(base_path)
        self.cache_dir = self.base_path / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # 캐시 저장소
        self.texture_cache: Dict[str, Dict[str, Any]] = {}
        self.model_cache: Dict[str, Dict[str, Any]] = {}
        self.motion_cache: Dict[str, Dict[str, Any]] = {}
        
        # 메트릭 추적
        self.metrics: Dict[str, ResourceMetrics] = {}
        self.access_log: Dict[str, List[datetime]] = {}
        
        # 디바이스별 최적화 설정
        self.device_configs = {
            DeviceType.DESKTOP: OptimizationConfig(
                quality_level=QualityLevel.HIGH,
                texture_scale=1.0,
                enable_compression=False,
                cache_size_mb=512,
                preload_textures=True,
                lazy_load_motions=False,
                gc_interval_seconds=300
            ),
            DeviceType.TABLET: OptimizationConfig(
                quality_level=QualityLevel.MEDIUM,
                texture_scale=0.8,
                enable_compression=True,
                cache_size_mb=256,
                preload_textures=True,
                lazy_load_motions=True,
                gc_interval_seconds=180
            ),
            DeviceType.MOBILE: OptimizationConfig(
                quality_level=QualityLevel.MEDIUM,
                texture_scale=0.6,
                enable_compression=True,
                cache_size_mb=128,
                preload_textures=False,
                lazy_load_motions=True,
                gc_interval_seconds=120
            ),
            DeviceType.LOW_END: OptimizationConfig(
                quality_level=QualityLevel.LOW,
                texture_scale=0.4,
                enable_compression=True,
                cache_size_mb=64,
                preload_textures=False,
                lazy_load_motions=True,
                gc_interval_seconds=60
            )
        }
        
        # 백그라운드 작업
        self._gc_task: Optional[asyncio.Task] = None
        # 백그라운드 작업은 이벤트 루프가 실행 중일 때만 시작
        # FastAPI가 시작될 때 자동으로 시작됨
    
    def get_optimized_config(self, device_type: DeviceType, 
                           user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """디바이스 타입에 최적화된 설정 반환"""
        config = self.device_configs[device_type]
        
        # 사용자 선호도 적용
        if user_preferences:
            if user_preferences.get("force_high_quality"):
                config.quality_level = QualityLevel.HIGH
                config.texture_scale = 1.0
            elif user_preferences.get("battery_saver"):
                config.quality_level = QualityLevel.LOW
                config.texture_scale = min(config.texture_scale, 0.5)
        
        return {
            "model_config": {
                "texture_scale": config.texture_scale,
                "quality_level": config.quality_level.value,
                "enable_compression": config.enable_compression
            },
            "cache_config": {
                "preload_textures": config.preload_textures,
                "lazy_load_motions": config.lazy_load_motions,
                "cache_size_mb": config.cache_size_mb
            },
            "performance_config": {
                "gc_interval": config.gc_interval_seconds,
                "max_concurrent_animations": 2 if device_type in [DeviceType.MOBILE, DeviceType.LOW_END] else 4
            }
        }
    
    async def optimize_model_loading(self, model_name: str, 
                                   device_type: DeviceType) -> Dict[str, Any]:
        """모델 로딩 최적화"""
        start_time = time.time()
        
        try:
            # 캐시 확인
            cache_key = f"{model_name}_{device_type.value}"
            if cache_key in self.model_cache:
                cached_model = self.model_cache[cache_key]
                if self._is_cache_valid(cached_model):
                    self._log_access(cache_key)
                    logger.info(f"Model {model_name} loaded from cache for {device_type}")
                    return cached_model["data"]
            
            # 모델 로딩 및 최적화
            model_data = await self._load_and_optimize_model(model_name, device_type)
            
            # 캐시 저장
            self.model_cache[cache_key] = {
                "data": model_data,
                "timestamp": datetime.now(),
                "access_count": 1,
                "size_bytes": len(json.dumps(model_data))
            }
            
            loading_time = time.time() - start_time
            self._update_metrics(model_name, loading_time, True)
            
            logger.info(f"Model {model_name} optimized for {device_type} in {loading_time:.2f}s")
            return model_data
            
        except Exception as e:
            logger.error(f"Failed to optimize model {model_name}: {e}")
            raise
    
    async def _load_and_optimize_model(self, model_name: str, 
                                     device_type: DeviceType) -> Dict[str, Any]:
        """모델 로딩 및 최적화 실행"""
        model_path = self.base_path / model_name / "runtime"
        model_file = model_path / f"{model_name}.model3.json"
        
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        # 모델 파일 로드
        with open(model_file, 'r', encoding='utf-8') as f:
            model_data = json.load(f)
        
        # 디바이스별 최적화 적용
        config = self.device_configs[device_type]
        optimized_data = await self._apply_optimizations(model_data, config, model_path)
        
        return optimized_data
    
    async def _apply_optimizations(self, model_data: Dict[str, Any], 
                                 config: OptimizationConfig,
                                 model_path: Path) -> Dict[str, Any]:
        """최적화 적용"""
        optimized = model_data.copy()
        
        # 텍스처 최적화
        if "FileReferences" in optimized:
            file_refs = optimized["FileReferences"]
            
            # 텍스처 스케일링 정보 추가
            if "Textures" in file_refs:
                optimized["TextureOptimization"] = {
                    "scale": config.texture_scale,
                    "compression": config.enable_compression,
                    "quality": config.quality_level.value
                }
            
            # 모션 최적화 (지연 로딩)
            if config.lazy_load_motions and "Motions" in file_refs:
                motion_refs = file_refs["Motions"]
                optimized["MotionLazyLoading"] = {
                    "enabled": True,
                    "preload_idle": True,
                    "motion_groups": list(motion_refs.keys())
                }
            
            # 표정 최적화
            if "Expressions" in file_refs:
                expressions = file_refs["Expressions"]
                if config.quality_level == QualityLevel.LOW and len(expressions) > 4:
                    # 저품질 모드에서는 표정 수 제한
                    optimized["FileReferences"]["Expressions"] = expressions[:4]
                    optimized["ExpressionOptimization"] = {
                        "reduced_count": True,
                        "original_count": len(expressions),
                        "optimized_count": 4
                    }
        
        # 렌더링 최적화 힌트
        optimized["RenderOptimization"] = {
            "quality_level": config.quality_level.value,
            "enable_culling": config.quality_level != QualityLevel.HIGH,
            "max_draw_calls": 100 if config.quality_level == QualityLevel.LOW else 200,
            "enable_batching": True
        }
        
        # 메모리 최적화
        optimized["MemoryOptimization"] = {
            "texture_pool_size": config.cache_size_mb // 4,  # MB
            "gc_interval": config.gc_interval_seconds,
            "auto_cleanup": True
        }
        
        return optimized
    
    async def preload_critical_resources(self, model_name: str, 
                                       device_type: DeviceType) -> Dict[str, Any]:
        """중요 리소스 사전 로딩"""
        preload_results = {
            "model": None,
            "textures": [],
            "motions": [],
            "expressions": []
        }
        
        try:
            # 모델 사전 로딩
            preload_results["model"] = await self.optimize_model_loading(model_name, device_type)
            
            config = self.device_configs[device_type]
            
            # 텍스처 사전 로딩 (설정에 따라)
            if config.preload_textures:
                preload_results["textures"] = await self._preload_textures(model_name, device_type)
            
            # 기본 모션 사전 로딩
            if not config.lazy_load_motions:
                preload_results["motions"] = await self._preload_motions(model_name, ["Idle"])
            
            # 기본 표정 사전 로딩
            preload_results["expressions"] = await self._preload_expressions(model_name, ["neutral", "joy"])
            
            logger.info(f"Critical resources preloaded for {model_name} on {device_type}")
            return preload_results
            
        except Exception as e:
            logger.error(f"Failed to preload resources for {model_name}: {e}")
            return preload_results
    
    async def _preload_textures(self, model_name: str, device_type: DeviceType) -> List[str]:
        """텍스처 사전 로딩"""
        textures = []
        model_path = self.base_path / model_name / "runtime"
        
        # 텍스처 디렉토리 확인
        texture_dirs = []
        if model_name == "mao_pro":
            texture_dirs = [model_path / "mao_pro.4096"]
        elif model_name == "shizuku":
            texture_dirs = [model_path / "shizuku.1024"]
        
        config = self.device_configs[device_type]
        
        for texture_dir in texture_dirs:
            if texture_dir.exists():
                for texture_file in texture_dir.glob("*.png"):
                    cache_key = f"texture_{model_name}_{texture_file.name}_{device_type.value}"
                    
                    # 텍스처 정보 캐시
                    self.texture_cache[cache_key] = {
                        "path": str(texture_file),
                        "scale": config.texture_scale,
                        "compression": config.enable_compression,
                        "timestamp": datetime.now(),
                        "size_estimate": texture_file.stat().st_size
                    }
                    
                    textures.append(str(texture_file))
        
        return textures
    
    async def _preload_motions(self, model_name: str, motion_groups: List[str]) -> List[str]:
        """모션 사전 로딩"""
        motions = []
        model_path = self.base_path / model_name / "runtime"
        
        if model_name == "mao_pro":
            motion_dir = model_path / "motions"
        elif model_name == "shizuku":
            motion_dir = model_path / "motion"
        else:
            return motions
        
        if motion_dir.exists():
            for motion_file in motion_dir.glob("*.motion3.json"):
                cache_key = f"motion_{model_name}_{motion_file.name}"
                
                try:
                    with open(motion_file, 'r', encoding='utf-8') as f:
                        motion_data = json.load(f)
                    
                    self.motion_cache[cache_key] = {
                        "data": motion_data,
                        "path": str(motion_file),
                        "timestamp": datetime.now(),
                        "size_bytes": len(json.dumps(motion_data))
                    }
                    
                    motions.append(str(motion_file))
                    
                except Exception as e:
                    logger.warning(f"Failed to preload motion {motion_file}: {e}")
        
        return motions
    
    async def _preload_expressions(self, model_name: str, expression_names: List[str]) -> List[str]:
        """표정 사전 로딩"""
        expressions = []
        model_path = self.base_path / model_name / "runtime"
        
        if model_name == "mao_pro":
            expression_dir = model_path / "expressions"
            
            if expression_dir.exists():
                for exp_file in expression_dir.glob("*.exp3.json"):
                    cache_key = f"expression_{model_name}_{exp_file.name}"
                    
                    try:
                        with open(exp_file, 'r', encoding='utf-8') as f:
                            exp_data = json.load(f)
                        
                        self.motion_cache[cache_key] = {
                            "data": exp_data,
                            "path": str(exp_file),
                            "timestamp": datetime.now(),
                            "size_bytes": len(json.dumps(exp_data))
                        }
                        
                        expressions.append(str(exp_file))
                        
                    except Exception as e:
                        logger.warning(f"Failed to preload expression {exp_file}: {e}")
        
        return expressions
    
    def get_performance_metrics(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """성능 메트릭 조회"""
        if model_name and model_name in self.metrics:
            return asdict(self.metrics[model_name])
        
        # 전체 메트릭 집계
        total_memory = sum(m.memory_usage for m in self.metrics.values())
        total_textures = sum(m.texture_count for m in self.metrics.values())
        total_models = sum(m.model_count for m in self.metrics.values())
        avg_cache_hit_rate = sum(m.cache_hit_rate for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0
        avg_loading_time = sum(m.loading_time for m in self.metrics.values()) / len(self.metrics) if self.metrics else 0
        
        return {
            "total_memory_usage": total_memory,
            "total_texture_count": total_textures,
            "total_model_count": total_models,
            "average_cache_hit_rate": avg_cache_hit_rate,
            "average_loading_time": avg_loading_time,
            "cache_sizes": {
                "texture_cache": len(self.texture_cache),
                "model_cache": len(self.model_cache),
                "motion_cache": len(self.motion_cache)
            }
        }
    
    async def cleanup_old_cache(self, max_age_hours: int = 24):
        """오래된 캐시 정리"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_items = 0
        
        # 각 캐시 정리
        for cache_name, cache_dict in [
            ("texture", self.texture_cache),
            ("model", self.model_cache),
            ("motion", self.motion_cache)
        ]:
            keys_to_remove = []
            
            for key, item in cache_dict.items():
                if item["timestamp"] < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del cache_dict[key]
                cleaned_items += 1
            
            logger.info(f"Cleaned {len(keys_to_remove)} items from {cache_name} cache")
        
        return cleaned_items
    
    def _is_cache_valid(self, cache_item: Dict[str, Any], max_age_hours: int = 1) -> bool:
        """캐시 유효성 확인"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        return cache_item["timestamp"] > cutoff_time
    
    def _log_access(self, resource_key: str):
        """리소스 접근 로그"""
        if resource_key not in self.access_log:
            self.access_log[resource_key] = []
        
        self.access_log[resource_key].append(datetime.now())
        
        # 최근 100회 접근만 유지
        self.access_log[resource_key] = self.access_log[resource_key][-100:]
    
    def _update_metrics(self, model_name: str, loading_time: float, cache_hit: bool):
        """메트릭 업데이트"""
        if model_name not in self.metrics:
            self.metrics[model_name] = ResourceMetrics(
                memory_usage=0,
                texture_count=0,
                model_count=1,
                cache_hit_rate=1.0 if cache_hit else 0.0,
                loading_time=loading_time,
                last_updated=datetime.now()
            )
        else:
            metrics = self.metrics[model_name]
            # 캐시 히트율 업데이트 (이동 평균)
            metrics.cache_hit_rate = (metrics.cache_hit_rate * 0.9) + (0.1 if cache_hit else 0.0)
            metrics.loading_time = (metrics.loading_time * 0.8) + (loading_time * 0.2)
            metrics.last_updated = datetime.now()
    
    def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        try:
            loop = asyncio.get_running_loop()
            if self._gc_task is None or self._gc_task.done():
                self._gc_task = asyncio.create_task(self._garbage_collection_loop())
        except RuntimeError:
            # 이벤트 루프가 없으면 나중에 시작
            logger.debug("Event loop not running, background tasks will start later")
    
    async def _garbage_collection_loop(self):
        """가비지 컬렉션 루프"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                await self.cleanup_old_cache()
                logger.debug("Background garbage collection completed")
            except Exception as e:
                logger.error(f"Error in garbage collection: {e}")


# 싱글톤 인스턴스
resource_optimizer = Live2DResourceOptimizer()
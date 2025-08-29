"""
메모리 관리 시스템

자동 가비지 컬렉션, 메모리 누수 감지, 리소스 정리를 통해
메모리 사용량을 최적화합니다.
"""

import gc
import threading
import time
import logging
import tracemalloc
import weakref
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import psutil
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """메모리 스냅샷"""
    timestamp: float
    total_mb: float
    rss_mb: float
    vms_mb: float
    percent: float
    gc_stats: Dict[str, int]
    object_count: int


@dataclass
class MemoryLeak:
    """메모리 누수 감지 결과"""
    object_type: str
    count: int
    size_mb: float
    growth_rate: float
    first_seen: float
    last_updated: float


class MemoryManager:
    """메모리 관리 시스템"""
    
    def __init__(self, 
                 snapshot_interval: int = 60,  # 60초마다 스냅샷
                 max_memory_percent: float = 80.0,  # 메모리 사용률 임계치
                 gc_threshold_mb: float = 100.0,  # GC 트리거 임계치
                 leak_detection_enabled: bool = True):
        
        self.snapshot_interval = snapshot_interval
        self.max_memory_percent = max_memory_percent
        self.gc_threshold_mb = gc_threshold_mb
        self.leak_detection_enabled = leak_detection_enabled
        
        # 스냅샷 저장소
        self.snapshots: deque = deque(maxlen=1440)  # 24시간 분량 (60초 간격)
        
        # 메모리 누수 감지
        self.object_tracking: Dict[str, List[int]] = defaultdict(list)
        self.detected_leaks: Dict[str, MemoryLeak] = {}
        
        # 약한 참조로 추적할 객체들
        self.tracked_objects: weakref.WeakSet = weakref.WeakSet()
        
        # 콜백 함수들
        self.memory_alert_callbacks: List[Callable] = []
        self.gc_callbacks: List[Callable] = []
        
        # 모니터링 상태
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 통계
        self.gc_count = 0
        self.memory_cleanups = 0
        self.peak_memory_mb = 0.0
        
        # tracemalloc 시작
        if leak_detection_enabled:
            tracemalloc.start()
        
        logger.info(f"MemoryManager initialized with {snapshot_interval}s interval, "
                   f"{max_memory_percent}% max memory, {gc_threshold_mb}MB GC threshold")
    
    async def start_monitoring(self):
        """메모리 모니터링 시작"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._memory_monitor_worker, daemon=True)
        self._monitor_thread.start()
        
        # 초기 스냅샷
        await self.take_snapshot()
        
        logger.info("Memory monitoring started")
    
    async def stop_monitoring(self):
        """메모리 모니터링 중지"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        if self.leak_detection_enabled:
            tracemalloc.stop()
        
        logger.info("Memory monitoring stopped")
    
    async def take_snapshot(self) -> MemorySnapshot:
        """메모리 스냅샷 생성"""
        try:
            # 프로세스 메모리 정보
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            # 가비지 컬렉터 통계
            gc_stats = {
                f"gen_{i}": gc.get_count()[i] for i in range(3)
            }
            # gc.collected는 Python 3.11에서 제거됨
            try:
                gc_stats['collected'] = gc.collected if hasattr(gc, 'collected') else 0
            except AttributeError:
                gc_stats['collected'] = 0
            
            # 객체 수 계산
            object_count = len(gc.get_objects())
            
            snapshot = MemorySnapshot(
                timestamp=time.time(),
                total_mb=memory_info.rss / 1024 / 1024,
                rss_mb=memory_info.rss / 1024 / 1024,
                vms_mb=memory_info.vms / 1024 / 1024,
                percent=memory_percent,
                gc_stats=gc_stats,
                object_count=object_count
            )
            
            self.snapshots.append(snapshot)
            
            # 피크 메모리 업데이트
            self.peak_memory_mb = max(self.peak_memory_mb, snapshot.total_mb)
            
            # 메모리 임계치 확인
            if snapshot.percent > self.max_memory_percent:
                await self._trigger_memory_alert(snapshot)
            
            # 메모리 누수 감지
            if self.leak_detection_enabled:
                await self._detect_memory_leaks()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to take memory snapshot: {e}")
            return None
    
    async def force_garbage_collection(self) -> Dict[str, int]:
        """강제 가비지 컬렉션 실행"""
        try:
            logger.info("Forcing garbage collection")
            
            # 이전 메모리 사용량
            before = psutil.Process().memory_info().rss / 1024 / 1024
            
            # 가비지 컬렉션 실행
            collected = {
                'gen0': gc.collect(0),
                'gen1': gc.collect(1), 
                'gen2': gc.collect(2)
            }
            
            # 이후 메모리 사용량
            after = psutil.Process().memory_info().rss / 1024 / 1024
            freed_mb = before - after
            
            self.gc_count += 1
            
            # 콜백 실행
            for callback in self.gc_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(collected, freed_mb)
                    else:
                        callback(collected, freed_mb)
                except Exception as e:
                    logger.error(f"GC callback failed: {e}")
            
            logger.info(f"Garbage collection completed: collected {sum(collected.values())} objects, "
                       f"freed {freed_mb:.1f}MB")
            
            return {
                **collected,
                'total_collected': sum(collected.values()),
                'memory_freed_mb': round(freed_mb, 2),
                'before_mb': round(before, 2),
                'after_mb': round(after, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to perform garbage collection: {e}")
            return {'error': str(e)}
    
    def get_memory_stats(self, hours: int = 1) -> Dict[str, Any]:
        """메모리 사용 통계"""
        try:
            cutoff_time = time.time() - (hours * 3600)
            recent_snapshots = [s for s in self.snapshots if s.timestamp > cutoff_time]
            
            if not recent_snapshots:
                return {"message": "No memory data available"}
            
            memory_values = [s.total_mb for s in recent_snapshots]
            percent_values = [s.percent for s in recent_snapshots]
            object_counts = [s.object_count for s in recent_snapshots]
            
            return {
                "time_range_hours": hours,
                "snapshots_count": len(recent_snapshots),
                "memory_usage": {
                    "current_mb": round(memory_values[-1], 2),
                    "peak_mb": round(max(memory_values), 2),
                    "avg_mb": round(sum(memory_values) / len(memory_values), 2),
                    "min_mb": round(min(memory_values), 2),
                    "growth_mb": round(memory_values[-1] - memory_values[0], 2) if len(memory_values) > 1 else 0
                },
                "memory_percent": {
                    "current": round(percent_values[-1], 2),
                    "peak": round(max(percent_values), 2),
                    "avg": round(sum(percent_values) / len(percent_values), 2)
                },
                "object_count": {
                    "current": object_counts[-1],
                    "peak": max(object_counts),
                    "avg": int(sum(object_counts) / len(object_counts)),
                    "growth": object_counts[-1] - object_counts[0] if len(object_counts) > 1 else 0
                },
                "gc_stats": {
                    "total_collections": self.gc_count,
                    "memory_cleanups": self.memory_cleanups,
                    "peak_memory_mb": round(self.peak_memory_mb, 2)
                },
                "memory_leaks": len(self.detected_leaks),
                "tracking_objects": len(self.tracked_objects)
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}
    
    def get_memory_leaks(self) -> List[Dict[str, Any]]:
        """감지된 메모리 누수 정보"""
        leaks = []
        
        for leak in self.detected_leaks.values():
            leaks.append({
                "object_type": leak.object_type,
                "count": leak.count,
                "size_mb": round(leak.size_mb, 2),
                "growth_rate_per_hour": round(leak.growth_rate * 3600, 2),
                "first_detected": datetime.fromtimestamp(leak.first_seen).isoformat(),
                "last_updated": datetime.fromtimestamp(leak.last_updated).isoformat(),
                "duration_hours": round((leak.last_updated - leak.first_seen) / 3600, 1)
            })
        
        return sorted(leaks, key=lambda x: x['size_mb'], reverse=True)
    
    def get_memory_recommendations(self) -> List[str]:
        """메모리 최적화 권장사항"""
        recommendations = []
        
        try:
            stats = self.get_memory_stats(1)
            
            # 현재 메모리 사용률
            current_percent = stats.get('memory_percent', {}).get('current', 0)
            if current_percent > 80:
                recommendations.append(f"메모리 사용률이 {current_percent:.1f}%로 높습니다. 즉시 최적화가 필요합니다.")
            elif current_percent > 60:
                recommendations.append(f"메모리 사용률이 {current_percent:.1f}%입니다. 모니터링을 강화하세요.")
            
            # 메모리 증가 추세
            memory_growth = stats.get('memory_usage', {}).get('growth_mb', 0)
            if memory_growth > 50:
                recommendations.append(f"지난 1시간 동안 {memory_growth:.1f}MB 메모리가 증가했습니다. 누수 가능성을 확인하세요.")
            
            # 객체 수 증가
            object_growth = stats.get('object_count', {}).get('growth', 0)
            if object_growth > 10000:
                recommendations.append(f"객체 수가 {object_growth:,}개 증가했습니다. 불필요한 객체 생성을 줄이세요.")
            
            # 메모리 누수
            if self.detected_leaks:
                recommendations.append(f"{len(self.detected_leaks)}개의 메모리 누수가 감지되었습니다. 즉시 조치가 필요합니다.")
            
            # 가비지 컬렉션 빈도
            if self.gc_count < 5:  # 1시간에 5번 미만
                recommendations.append("가비지 컬렉션이 충분히 실행되지 않고 있습니다. 수동 GC를 고려하세요.")
            
            # 피크 메모리
            peak_mb = stats.get('memory_usage', {}).get('peak_mb', 0)
            current_mb = stats.get('memory_usage', {}).get('current_mb', 0)
            if peak_mb - current_mb > 100:
                recommendations.append("메모리 사용량 변동이 큽니다. 메모리 풀링을 고려하세요.")
            
            if not recommendations:
                recommendations.append("메모리 사용 상태가 양호합니다.")
        
        except Exception as e:
            logger.error(f"Failed to generate memory recommendations: {e}")
            recommendations.append("메모리 권장사항 생성 중 오류가 발생했습니다.")
        
        return recommendations
    
    def track_object(self, obj: Any, name: str = None) -> bool:
        """객체 추적 시작"""
        try:
            self.tracked_objects.add(obj)
            if name:
                obj.__memory_tracking_name__ = name
            return True
        except Exception as e:
            logger.error(f"Failed to track object: {e}")
            return False
    
    def cleanup_resources(self) -> Dict[str, int]:
        """리소스 정리"""
        try:
            logger.info("Performing resource cleanup")
            
            cleanup_stats = {
                'closed_connections': 0,
                'cleared_caches': 0,
                'gc_collections': 0,
                'memory_freed_mb': 0
            }
            
            # 가비지 컬렉션
            gc_result = asyncio.create_task(self.force_garbage_collection())
            
            # 캐시 정리 (cache_service가 있다면)
            try:
                from ..services.cache_service import cache_service
                if hasattr(cache_service, 'cleanup_expired'):
                    expired_count = cache_service.cleanup_expired()
                    cleanup_stats['cleared_caches'] = expired_count
            except ImportError:
                pass
            
            self.memory_cleanups += 1
            
            logger.info(f"Resource cleanup completed: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup resources: {e}")
            return {'error': str(e)}
    
    # Private methods
    
    async def _detect_memory_leaks(self) -> None:
        """메모리 누수 감지"""
        try:
            if not tracemalloc.is_tracing():
                return
            
            # 현재 메모리 사용량 추적
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics('lineno')
            
            # 객체 타입별 메모리 사용량 계산
            type_usage = defaultdict(lambda: {'count': 0, 'size': 0})
            
            for stat in top_stats[:100]:  # 상위 100개만 확인
                obj_type = stat.traceback.format()[-1] if stat.traceback.format() else 'unknown'
                type_usage[obj_type]['count'] += stat.count
                type_usage[obj_type]['size'] += stat.size
            
            # 누수 패턴 감지
            current_time = time.time()
            
            for obj_type, usage in type_usage.items():
                size_mb = usage['size'] / 1024 / 1024
                
                # 이전 데이터와 비교
                if obj_type in self.object_tracking:
                    self.object_tracking[obj_type].append(usage['count'])
                    
                    # 최근 10개 데이터만 유지
                    if len(self.object_tracking[obj_type]) > 10:
                        self.object_tracking[obj_type] = self.object_tracking[obj_type][-10:]
                    
                    # 증가 패턴 확인
                    if len(self.object_tracking[obj_type]) >= 5:
                        counts = self.object_tracking[obj_type]
                        growth_rate = (counts[-1] - counts[0]) / len(counts)
                        
                        # 지속적인 증가 패턴 감지
                        if growth_rate > 10 and size_mb > 1:  # 10개/회, 1MB 이상
                            if obj_type not in self.detected_leaks:
                                self.detected_leaks[obj_type] = MemoryLeak(
                                    object_type=obj_type,
                                    count=usage['count'],
                                    size_mb=size_mb,
                                    growth_rate=growth_rate,
                                    first_seen=current_time,
                                    last_updated=current_time
                                )
                                logger.warning(f"Memory leak detected: {obj_type} "
                                             f"({usage['count']} objects, {size_mb:.1f}MB)")
                            else:
                                # 기존 누수 업데이트
                                leak = self.detected_leaks[obj_type]
                                leak.count = usage['count']
                                leak.size_mb = size_mb
                                leak.growth_rate = growth_rate
                                leak.last_updated = current_time
                else:
                    self.object_tracking[obj_type] = [usage['count']]
                    
        except Exception as e:
            logger.error(f"Memory leak detection failed: {e}")
    
    async def _trigger_memory_alert(self, snapshot: MemorySnapshot) -> None:
        """메모리 알림 트리거"""
        try:
            alert_data = {
                "type": "high_memory_usage",
                "memory_percent": snapshot.percent,
                "memory_mb": snapshot.total_mb,
                "threshold_percent": self.max_memory_percent,
                "timestamp": datetime.fromtimestamp(snapshot.timestamp).isoformat(),
                "object_count": snapshot.object_count,
                "recommendations": self.get_memory_recommendations()
            }
            
            for callback in self.memory_alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert_data)
                    else:
                        callback(alert_data)
                except Exception as e:
                    logger.error(f"Memory alert callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to trigger memory alert: {e}")
    
    def _memory_monitor_worker(self) -> None:
        """메모리 모니터링 워커 스레드"""
        while self._monitoring_active:
            try:
                # 스냅샷 생성
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.take_snapshot())
                loop.close()
                
                # GC 임계치 확인
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > self.gc_threshold_mb:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.force_garbage_collection())
                    loop.close()
                
                time.sleep(self.snapshot_interval)
                
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                time.sleep(60)  # 에러 시 1분 대기
    
    def add_memory_alert_callback(self, callback: Callable) -> None:
        """메모리 알림 콜백 추가"""
        self.memory_alert_callbacks.append(callback)
    
    def add_gc_callback(self, callback: Callable) -> None:
        """GC 콜백 추가"""
        self.gc_callbacks.append(callback)


# 글로벌 인스턴스
memory_manager = MemoryManager()


# 유틸리티 함수들
async def start_memory_monitoring() -> None:
    """메모리 모니터링 시작"""
    await memory_manager.start_monitoring()


async def stop_memory_monitoring() -> None:
    """메모리 모니터링 중지"""
    await memory_manager.stop_monitoring()


async def force_gc() -> Dict[str, int]:
    """강제 가비지 컬렉션"""
    return await memory_manager.force_garbage_collection()


def get_memory_dashboard() -> Dict[str, Any]:
    """메모리 대시보드 데이터"""
    return {
        "stats": memory_manager.get_memory_stats(1),
        "leaks": memory_manager.get_memory_leaks(),
        "recommendations": memory_manager.get_memory_recommendations()
    }


def track_object(obj: Any, name: str = None) -> bool:
    """객체 메모리 추적"""
    return memory_manager.track_object(obj, name)


async def cleanup_memory() -> Dict[str, int]:
    """메모리 정리"""
    return memory_manager.cleanup_resources()
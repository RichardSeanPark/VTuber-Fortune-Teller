"""
성능 모니터링 시스템

실시간 API 응답 시간, 메모리 사용량, CPU 사용률을 모니터링하고
성능 메트릭을 수집하여 최적화 가이드를 제공합니다.
"""

import asyncio
import gc
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import deque
from dataclasses import dataclass
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """성능 메트릭 데이터 클래스"""
    timestamp: float
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    memory_usage_mb: float
    cpu_usage_percent: float
    db_query_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0


@dataclass
class SystemMetrics:
    """시스템 성능 메트릭"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, int]
    active_connections: int


class PerformanceMonitor:
    """성능 모니터링 시스템"""
    
    def __init__(self, max_metrics: int = 10000, alert_threshold_ms: float = 500):
        self.max_metrics = max_metrics
        self.alert_threshold_ms = alert_threshold_ms
        
        # 메트릭 저장소 (메모리 기반 circular buffer)
        self.api_metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics // 10)
        
        # 성능 통계
        self.endpoint_stats: Dict[str, Dict] = {}
        self.alert_callbacks: List[Callable] = []
        
        # 시스템 모니터링 스레드
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 프로세스 정보
        self.process = psutil.Process()
        
        logger.info(f"PerformanceMonitor initialized with {max_metrics} max metrics")
    
    async def start_monitoring(self):
        """모니터링 시작"""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._system_monitor_worker, daemon=True)
        self._monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """모니터링 중지"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def record_api_call(self, endpoint: str, method: str, response_time_ms: float,
                       status_code: int, **extra_metrics) -> None:
        """API 호출 메트릭 기록"""
        try:
            # 현재 시스템 메트릭 수집
            memory_info = self.process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024
            
            try:
                cpu_usage = self.process.cpu_percent()
            except:
                cpu_usage = 0.0
            
            # 메트릭 생성
            metric = PerformanceMetric(
                timestamp=time.time(),
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time_ms,
                status_code=status_code,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage,
                **extra_metrics
            )
            
            # 저장
            self.api_metrics.append(metric)
            
            # 엔드포인트별 통계 업데이트
            self._update_endpoint_stats(metric)
            
            # 성능 알림 체크
            if response_time_ms > self.alert_threshold_ms:
                self._trigger_alert(metric)
                
        except Exception as e:
            logger.error(f"Failed to record API metric: {e}")
    
    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """성능 요약 정보 반환"""
        try:
            cutoff_time = time.time() - (minutes * 60)
            
            # 최근 메트릭 필터링
            recent_metrics = [
                m for m in self.api_metrics 
                if m.timestamp > cutoff_time
            ]
            
            if not recent_metrics:
                return {"message": "No metrics available", "time_range_minutes": minutes}
            
            # 기본 통계
            response_times = [m.response_time_ms for m in recent_metrics]
            memory_usage = [m.memory_usage_mb for m in recent_metrics]
            cpu_usage = [m.cpu_usage_percent for m in recent_metrics if m.cpu_usage_percent > 0]
            
            # 상태 코드 분포
            status_codes = {}
            for m in recent_metrics:
                status_codes[m.status_code] = status_codes.get(m.status_code, 0) + 1
            
            # 느린 요청 분석
            slow_requests = [m for m in recent_metrics if m.response_time_ms > self.alert_threshold_ms]
            
            return {
                "time_range_minutes": minutes,
                "total_requests": len(recent_metrics),
                "response_times": {
                    "avg_ms": round(sum(response_times) / len(response_times), 2),
                    "min_ms": min(response_times),
                    "max_ms": max(response_times),
                    "p95_ms": self._calculate_percentile(response_times, 95),
                    "p99_ms": self._calculate_percentile(response_times, 99)
                },
                "memory_usage": {
                    "avg_mb": round(sum(memory_usage) / len(memory_usage), 2),
                    "min_mb": round(min(memory_usage), 2),
                    "max_mb": round(max(memory_usage), 2),
                    "current_mb": round(memory_usage[-1], 2) if memory_usage else 0
                },
                "cpu_usage": {
                    "avg_percent": round(sum(cpu_usage) / len(cpu_usage), 2) if cpu_usage else 0,
                    "max_percent": max(cpu_usage) if cpu_usage else 0
                },
                "status_codes": status_codes,
                "slow_requests": {
                    "count": len(slow_requests),
                    "percentage": round(len(slow_requests) / len(recent_metrics) * 100, 2),
                    "threshold_ms": self.alert_threshold_ms
                },
                "error_rate": {
                    "4xx_count": sum(1 for m in recent_metrics if 400 <= m.status_code < 500),
                    "5xx_count": sum(1 for m in recent_metrics if m.status_code >= 500),
                    "error_percentage": round(
                        sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics) * 100, 2
                    )
                },
                "top_slow_endpoints": self._get_slow_endpoints(recent_metrics)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}
    
    def get_endpoint_stats(self) -> Dict[str, Any]:
        """엔드포인트별 성능 통계"""
        try:
            stats = {}
            for endpoint, data in self.endpoint_stats.items():
                if data['count'] > 0:
                    stats[endpoint] = {
                        "total_requests": data['count'],
                        "avg_response_time_ms": round(data['total_time'] / data['count'], 2),
                        "min_response_time_ms": data['min_time'],
                        "max_response_time_ms": data['max_time'],
                        "error_count": data['errors'],
                        "error_rate_percent": round(data['errors'] / data['count'] * 100, 2),
                        "last_called": datetime.fromtimestamp(data['last_called']).isoformat()
                    }
            
            # 성능 순으로 정렬
            return dict(sorted(stats.items(), key=lambda x: x[1]['avg_response_time_ms'], reverse=True))
            
        except Exception as e:
            logger.error(f"Failed to get endpoint stats: {e}")
            return {}
    
    def get_system_health(self) -> Dict[str, Any]:
        """시스템 건강 상태"""
        try:
            # 현재 시스템 상태
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # 최근 시스템 메트릭
            recent_system = list(self.system_metrics)[-10:] if self.system_metrics else []
            
            health_status = "healthy"
            warnings = []
            
            # 건강 상태 체크
            if memory_info.percent > 85:
                health_status = "warning"
                warnings.append(f"High memory usage: {memory_info.percent:.1f}%")
            
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                health_status = "warning" if health_status == "healthy" else "critical"
                warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if disk_info.percent > 90:
                health_status = "critical"
                warnings.append(f"Low disk space: {disk_info.percent:.1f}% used")
            
            return {
                "status": health_status,
                "warnings": warnings,
                "current_metrics": {
                    "memory_usage_percent": memory_info.percent,
                    "memory_available_gb": round(memory_info.available / 1024 / 1024 / 1024, 2),
                    "cpu_usage_percent": cpu_percent,
                    "disk_usage_percent": disk_info.percent,
                    "disk_free_gb": round(disk_info.free / 1024 / 1024 / 1024, 2),
                    "active_connections": len(psutil.net_connections()),
                    "uptime_seconds": time.time() - psutil.boot_time()
                },
                "process_info": {
                    "memory_rss_mb": round(self.process.memory_info().rss / 1024 / 1024, 2),
                    "cpu_percent": self.process.cpu_percent(),
                    "threads": self.process.num_threads(),
                    "open_files": len(self.process.open_files()),
                    "connections": len(self.process.connections())
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {"status": "unknown", "error": str(e)}
    
    def get_optimization_recommendations(self) -> List[str]:
        """성능 최적화 권장사항"""
        recommendations = []
        
        try:
            # 최근 1시간 데이터 분석
            summary = self.get_performance_summary(60)
            system_health = self.get_system_health()
            
            # 응답 시간 분석
            if summary.get('response_times', {}).get('avg_ms', 0) > 200:
                recommendations.append("평균 응답 시간이 200ms를 초과합니다. 데이터베이스 쿼리 최적화를 고려하세요.")
            
            if summary.get('response_times', {}).get('p95_ms', 0) > 500:
                recommendations.append("95% 응답 시간이 500ms를 초과합니다. 캐시 적용을 검토하세요.")
            
            # 메모리 분석
            memory_percent = system_health.get('current_metrics', {}).get('memory_usage_percent', 0)
            if memory_percent > 80:
                recommendations.append("메모리 사용률이 높습니다. 가비지 컬렉션 및 메모리 누수를 점검하세요.")
            
            # CPU 분석
            cpu_percent = system_health.get('current_metrics', {}).get('cpu_usage_percent', 0)
            if cpu_percent > 70:
                recommendations.append("CPU 사용률이 높습니다. 비동기 처리 최적화를 고려하세요.")
            
            # 에러율 분석
            error_rate = summary.get('error_rate', {}).get('error_percentage', 0)
            if error_rate > 5:
                recommendations.append(f"에러율이 {error_rate:.1f}%입니다. 예외 처리 및 로깅을 강화하세요.")
            
            # 느린 요청 분석
            slow_percentage = summary.get('slow_requests', {}).get('percentage', 0)
            if slow_percentage > 10:
                recommendations.append(f"느린 요청이 {slow_percentage:.1f}%입니다. 성능 프로파일링을 수행하세요.")
            
            # 캐시 효율성 (구현된 경우)
            if hasattr(self, 'cache_stats'):
                hit_rate = getattr(self, 'cache_hit_rate', 0)
                if hit_rate < 70:
                    recommendations.append(f"캐시 적중률이 {hit_rate:.1f}%로 낮습니다. 캐시 전략을 재검토하세요.")
            
            if not recommendations:
                recommendations.append("현재 성능 지표는 양호합니다. 지속적인 모니터링을 유지하세요.")
                
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            recommendations.append("최적화 권장사항을 생성하는 중 오류가 발생했습니다.")
        
        return recommendations
    
    def export_metrics(self, output_file: Optional[Path] = None) -> str:
        """메트릭 데이터를 JSON으로 내보내기"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "api_metrics": [
                    {
                        "timestamp": m.timestamp,
                        "endpoint": m.endpoint,
                        "method": m.method,
                        "response_time_ms": m.response_time_ms,
                        "status_code": m.status_code,
                        "memory_usage_mb": m.memory_usage_mb,
                        "cpu_usage_percent": m.cpu_usage_percent
                    } for m in list(self.api_metrics)[-1000:]  # 최근 1000개만
                ],
                "endpoint_stats": self.get_endpoint_stats(),
                "performance_summary": self.get_performance_summary(60),
                "system_health": self.get_system_health()
            }
            
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            if output_file:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(json_data, encoding='utf-8')
                logger.info(f"Metrics exported to {output_file}")
            
            return json_data
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    # Private methods
    
    def _update_endpoint_stats(self, metric: PerformanceMetric) -> None:
        """엔드포인트별 통계 업데이트"""
        key = f"{metric.method} {metric.endpoint}"
        
        if key not in self.endpoint_stats:
            self.endpoint_stats[key] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'errors': 0,
                'last_called': 0
            }
        
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_time'] += metric.response_time_ms
        stats['min_time'] = min(stats['min_time'], metric.response_time_ms)
        stats['max_time'] = max(stats['max_time'], metric.response_time_ms)
        stats['last_called'] = metric.timestamp
        
        if metric.status_code >= 400:
            stats['errors'] += 1
    
    def _get_slow_endpoints(self, metrics: List[PerformanceMetric]) -> List[Dict]:
        """느린 엔드포인트 TOP 5"""
        endpoint_times = {}
        
        for m in metrics:
            key = f"{m.method} {m.endpoint}"
            if key not in endpoint_times:
                endpoint_times[key] = []
            endpoint_times[key].append(m.response_time_ms)
        
        # 평균 시간으로 정렬
        avg_times = [
            {
                "endpoint": endpoint,
                "avg_time_ms": round(sum(times) / len(times), 2),
                "max_time_ms": max(times),
                "request_count": len(times)
            }
            for endpoint, times in endpoint_times.items()
        ]
        
        return sorted(avg_times, key=lambda x: x['avg_time_ms'], reverse=True)[:5]
    
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """백분위수 계산"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return round(sorted_values[index], 2)
    
    async def _trigger_alert(self, metric: PerformanceMetric) -> None:
        """성능 알림 트리거"""
        try:
            alert_data = {
                "type": "slow_response",
                "endpoint": f"{metric.method} {metric.endpoint}",
                "response_time_ms": metric.response_time_ms,
                "threshold_ms": self.alert_threshold_ms,
                "timestamp": datetime.fromtimestamp(metric.timestamp).isoformat(),
                "memory_usage_mb": metric.memory_usage_mb,
                "status_code": metric.status_code
            }
            
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert_data)
                    else:
                        callback(alert_data)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def _system_monitor_worker(self) -> None:
        """시스템 메트릭 수집 워커"""
        while self._monitoring_active:
            try:
                # 시스템 메트릭 수집
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                network = psutil.net_io_counters()
                
                metric = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / 1024 / 1024,
                    disk_usage_percent=disk.percent,
                    network_io={
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv
                    },
                    active_connections=len(psutil.net_connections())
                )
                
                self.system_metrics.append(metric)
                
                # 메모리 정리 (10분마다)
                if int(time.time()) % 600 == 0:
                    gc.collect()
                
                time.sleep(30)  # 30초마다 수집
                
            except Exception as e:
                logger.error(f"System monitor error: {e}")
                time.sleep(60)  # 에러 시 1분 대기
    
    def add_alert_callback(self, callback: Callable) -> None:
        """알림 콜백 추가"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable) -> bool:
        """알림 콜백 제거"""
        try:
            self.alert_callbacks.remove(callback)
            return True
        except ValueError:
            return False


# 글로벌 인스턴스
performance_monitor = PerformanceMonitor()


# 유틸리티 함수들
def record_api_performance(endpoint: str, method: str, response_time_ms: float, 
                         status_code: int, **kwargs) -> None:
    """API 성능 메트릭 기록"""
    performance_monitor.record_api_call(endpoint, method, response_time_ms, status_code, **kwargs)


async def get_performance_dashboard() -> Dict[str, Any]:
    """성능 대시보드 데이터"""
    return {
        "summary": performance_monitor.get_performance_summary(60),
        "endpoint_stats": performance_monitor.get_endpoint_stats(),
        "system_health": performance_monitor.get_system_health(),
        "recommendations": performance_monitor.get_optimization_recommendations()
    }


async def start_performance_monitoring() -> None:
    """성능 모니터링 시작"""
    await performance_monitor.start_monitoring()


async def stop_performance_monitoring() -> None:
    """성능 모니터링 중지"""
    await performance_monitor.stop_monitoring()
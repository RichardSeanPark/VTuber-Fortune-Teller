"""
비동기 처리 최적화 시스템

asyncio 기반 비동기 태스크 관리, 동시성 제어, 백그라운드 작업 최적화를 통해
서버 처리 성능을 향상시킵니다.
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import weakref
import functools
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class TaskPriority(int, Enum):
    """태스크 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(str, Enum):
    """태스크 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """태스크 정보"""
    task_id: str
    name: str
    priority: TaskPriority
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    result: Any = None
    retry_count: int = 0
    max_retries: int = 3


class AsyncOptimizer:
    """비동기 처리 최적화 관리자"""
    
    def __init__(self,
                 max_concurrent_tasks: int = 100,
                 max_workers: int = 10,
                 task_timeout: float = 30.0,
                 cleanup_interval: int = 300):
        
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_workers = max_workers
        self.task_timeout = task_timeout
        self.cleanup_interval = cleanup_interval
        
        # 세마포어로 동시성 제어
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        
        # 스레드 풀 executor
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        
        # 태스크 관리
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_info: Dict[str, TaskInfo] = {}
        self.completed_tasks: deque = deque(maxlen=1000)  # 최근 1000개 완료 태스크
        
        # 우선순위 큐
        self.priority_queues: Dict[TaskPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in TaskPriority
        }
        
        # 백그라운드 작업자
        self.queue_workers: List[asyncio.Task] = []
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # 성능 통계
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'cancelled_tasks': 0,
            'average_duration_ms': 0.0,
            'tasks_per_second': 0.0
        }
        
        # 레이트 리미팅
        self.rate_limiters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # 콜백 함수들
        self.task_completion_callbacks: weakref.WeakSet = weakref.WeakSet()
        self.error_callbacks: weakref.WeakSet = weakref.WeakSet()
        
        # 시작 상태
        self._started = False
        
        logger.info(f"AsyncOptimizer initialized: max_concurrent={max_concurrent_tasks}, "
                   f"max_workers={max_workers}, timeout={task_timeout}s")
    
    async def start(self):
        """비동기 최적화 시스템 시작"""
        if self._started:
            return
            
        # 우선순위별 작업자 시작
        for priority in TaskPriority:
            for i in range(2):  # 각 우선순위별로 2개의 워커
                worker = asyncio.create_task(
                    self._queue_worker(priority, f"worker-{priority.name.lower()}-{i}")
                )
                self.queue_workers.append(worker)
        
        # 정리 작업 시작
        self.cleanup_task = asyncio.create_task(self._cleanup_worker())
        
        self._started = True
        logger.info("AsyncOptimizer started with queue workers")
    
    async def stop(self):
        """비동기 최적화 시스템 중지"""
        if not self._started:
            return
            
        # 모든 워커 중지
        for worker in self.queue_workers:
            worker.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # 진행 중인 태스크들 정리
        for task in list(self.active_tasks.values()):
            if not task.done():
                task.cancel()
        
        # 워커들이 완료될 때까지 대기
        if self.queue_workers:
            await asyncio.gather(*self.queue_workers, return_exceptions=True)
        
        if self.cleanup_task:
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 스레드 풀 종료
        self.thread_pool.shutdown(wait=True)
        
        self._started = False
        logger.info("AsyncOptimizer stopped")
    
    async def submit_task(self,
                         coro: Awaitable[Any],
                         name: str,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None,
                         max_retries: int = 3,
                         immediate: bool = False) -> str:
        """비동기 태스크 제출"""
        
        task_id = f"{name}_{int(time.time() * 1000)}_{len(self.task_info)}"
        
        task_info = TaskInfo(
            task_id=task_id,
            name=name,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=time.time(),
            max_retries=max_retries
        )
        
        self.task_info[task_id] = task_info
        self.stats['total_tasks'] += 1
        
        if immediate or priority == TaskPriority.CRITICAL:
            # 즉시 실행
            task = asyncio.create_task(
                self._execute_task_with_semaphore(coro, task_info, timeout)
            )
            self.active_tasks[task_id] = task
        else:
            # 우선순위 큐에 추가
            await self.priority_queues[priority].put((coro, task_info, timeout))
        
        logger.debug(f"Task {task_id} submitted with priority {priority.name}")
        return task_id
    
    async def submit_blocking_task(self,
                                 func: Callable,
                                 *args,
                                 name: str,
                                 priority: TaskPriority = TaskPriority.NORMAL,
                                 timeout: Optional[float] = None,
                                 **kwargs) -> str:
        """블로킹 함수를 스레드 풀에서 실행"""
        
        # 블로킹 함수를 비동기로 래핑
        loop = asyncio.get_event_loop()
        coro = loop.run_in_executor(self.thread_pool, functools.partial(func, *args, **kwargs))
        
        return await self.submit_task(coro, f"blocking_{name}", priority, timeout)
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """태스크 완료 대기"""
        if task_id not in self.task_info:
            raise ValueError(f"Task {task_id} not found")
        
        # 활성 태스크에서 찾기
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            try:
                result = await asyncio.wait_for(task, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                task.cancel()
                raise
        
        # 완료된 태스크에서 찾기
        task_info = self.task_info[task_id]
        if task_info.status == TaskStatus.COMPLETED:
            return task_info.result
        elif task_info.status == TaskStatus.FAILED:
            raise Exception(task_info.error)
        else:
            raise ValueError(f"Task {task_id} is in {task_info.status} status")
    
    async def cancel_task(self, task_id: str) -> bool:
        """태스크 취소"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            
            if task_id in self.task_info:
                self.task_info[task_id].status = TaskStatus.CANCELLED
                self.stats['cancelled_tasks'] += 1
            
            return True
        return False
    
    def apply_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """레이트 리미팅 적용"""
        now = time.time()
        requests = self.rate_limiters[key]
        
        # 윈도우 외부의 요청 제거
        while requests and now - requests[0] > window_seconds:
            requests.popleft()
        
        # 제한 확인
        if len(requests) >= max_requests:
            return False
        
        requests.append(now)
        return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """태스크 상태 조회"""
        if task_id not in self.task_info:
            return None
        
        task_info = self.task_info[task_id]
        return {
            "task_id": task_info.task_id,
            "name": task_info.name,
            "priority": task_info.priority.name,
            "status": task_info.status,
            "created_at": datetime.fromtimestamp(task_info.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(task_info.started_at).isoformat() if task_info.started_at else None,
            "completed_at": datetime.fromtimestamp(task_info.completed_at).isoformat() if task_info.completed_at else None,
            "duration_ms": task_info.duration_ms,
            "retry_count": task_info.retry_count,
            "error": task_info.error
        }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 조회"""
        # 활성 태스크 상태별 집계
        active_by_status = defaultdict(int)
        for task_info in self.task_info.values():
            if task_info.status != TaskStatus.COMPLETED:
                active_by_status[task_info.status] += 1
        
        # 최근 완료된 태스크들의 평균 처리 시간
        recent_durations = [
            task_info.duration_ms for task_info in self.completed_tasks
            if task_info.duration_ms is not None
        ]
        avg_duration = sum(recent_durations) / len(recent_durations) if recent_durations else 0
        
        # 큐 크기
        queue_sizes = {
            priority.name: queue.qsize() 
            for priority, queue in self.priority_queues.items()
        }
        
        return {
            "total_tasks": self.stats['total_tasks'],
            "completed_tasks": self.stats['completed_tasks'],
            "failed_tasks": self.stats['failed_tasks'],
            "cancelled_tasks": self.stats['cancelled_tasks'],
            "active_tasks": len(self.active_tasks),
            "average_duration_ms": round(avg_duration, 2),
            "active_by_status": dict(active_by_status),
            "queue_sizes": queue_sizes,
            "thread_pool_active": self.thread_pool._threads,
            "semaphore_available": self.semaphore._value,
            "memory_usage": {
                "task_info_count": len(self.task_info),
                "completed_tasks_count": len(self.completed_tasks),
                "active_tasks_count": len(self.active_tasks)
            }
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """성능 최적화 권장사항"""
        recommendations = []
        stats = self.get_performance_stats()
        
        # 활성 태스크 수 분석
        active_count = stats['active_tasks']
        if active_count > self.max_concurrent_tasks * 0.8:
            recommendations.append(f"활성 태스크 수가 많습니다 ({active_count}). max_concurrent_tasks 증가를 고려하세요.")
        
        # 큐 크기 분석
        queue_sizes = stats['queue_sizes']
        max_queue_size = max(queue_sizes.values()) if queue_sizes else 0
        if max_queue_size > 50:
            recommendations.append(f"태스크 큐가 쌓이고 있습니다 (최대 {max_queue_size}). 워커 수 증가를 고려하세요.")
        
        # 실패율 분석
        total_completed = stats['completed_tasks'] + stats['failed_tasks']
        if total_completed > 0:
            failure_rate = stats['failed_tasks'] / total_completed * 100
            if failure_rate > 5:
                recommendations.append(f"태스크 실패율이 {failure_rate:.1f}%로 높습니다. 에러 처리를 강화하세요.")
        
        # 평균 처리 시간 분석
        avg_duration = stats['average_duration_ms']
        if avg_duration > 5000:  # 5초 이상
            recommendations.append(f"평균 처리 시간이 {avg_duration:.0f}ms로 깁니다. 태스크 분할을 고려하세요.")
        
        # 스레드 풀 사용률 분석
        thread_usage = len(stats['thread_pool_active'])
        if thread_usage > self.max_workers * 0.8:
            recommendations.append(f"스레드 풀 사용률이 높습니다 ({thread_usage}/{self.max_workers}). max_workers 증가를 고려하세요.")
        
        if not recommendations:
            recommendations.append("비동기 처리 성능이 양호합니다.")
        
        return recommendations
    
    # Private methods
    
    async def _execute_task_with_semaphore(self,
                                         coro: Awaitable[Any],
                                         task_info: TaskInfo,
                                         timeout: Optional[float] = None) -> Any:
        """세마포어를 사용하여 태스크 실행"""
        async with self.semaphore:
            return await self._execute_task(coro, task_info, timeout)
    
    async def _execute_task(self,
                           coro: Awaitable[Any],
                           task_info: TaskInfo,
                           timeout: Optional[float] = None) -> Any:
        """태스크 실행"""
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = time.time()
        
        timeout = timeout or self.task_timeout
        
        try:
            # 타임아웃과 함께 실행
            result = await asyncio.wait_for(coro, timeout=timeout)
            
            # 성공적으로 완료
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = time.time()
            task_info.duration_ms = (task_info.completed_at - task_info.started_at) * 1000
            task_info.result = result
            
            self.stats['completed_tasks'] += 1
            self.completed_tasks.append(task_info)
            
            # 성공 콜백 실행
            await self._run_completion_callbacks(task_info, None)
            
            return result
            
        except asyncio.TimeoutError as e:
            task_info.status = TaskStatus.FAILED
            task_info.error = f"Task timeout after {timeout}s"
            task_info.completed_at = time.time()
            task_info.duration_ms = (task_info.completed_at - task_info.started_at) * 1000
            
            self.stats['failed_tasks'] += 1
            await self._run_completion_callbacks(task_info, e)
            
            logger.warning(f"Task {task_info.task_id} timed out after {timeout}s")
            raise
            
        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = time.time()
            if task_info.started_at:
                task_info.duration_ms = (task_info.completed_at - task_info.started_at) * 1000
            
            self.stats['cancelled_tasks'] += 1
            logger.info(f"Task {task_info.task_id} was cancelled")
            raise
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error = str(e)
            task_info.completed_at = time.time()
            task_info.duration_ms = (task_info.completed_at - task_info.started_at) * 1000
            
            # 재시도 로직
            if task_info.retry_count < task_info.max_retries:
                task_info.retry_count += 1
                logger.info(f"Retrying task {task_info.task_id} (attempt {task_info.retry_count})")
                
                # 지수 백오프로 재시도
                await asyncio.sleep(2 ** task_info.retry_count)
                return await self._execute_task(coro, task_info, timeout)
            
            self.stats['failed_tasks'] += 1
            await self._run_completion_callbacks(task_info, e)
            
            logger.error(f"Task {task_info.task_id} failed: {e}")
            raise
            
        finally:
            # 활성 태스크에서 제거
            if task_info.task_id in self.active_tasks:
                del self.active_tasks[task_info.task_id]
    
    async def _queue_worker(self, priority: TaskPriority, worker_name: str):
        """우선순위 큐 워커"""
        queue = self.priority_queues[priority]
        
        while True:
            try:
                # 큐에서 태스크 가져오기
                coro, task_info, timeout = await queue.get()
                
                # 태스크 실행
                task = asyncio.create_task(
                    self._execute_task_with_semaphore(coro, task_info, timeout)
                )
                self.active_tasks[task_info.task_id] = task
                
                # 태스크 완료 대기 (백그라운드)
                asyncio.create_task(self._monitor_task(task, task_info))
                
            except asyncio.CancelledError:
                logger.info(f"Queue worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Queue worker {worker_name} error: {e}")
                await asyncio.sleep(1)
    
    async def _monitor_task(self, task: asyncio.Task, task_info: TaskInfo):
        """태스크 모니터링"""
        try:
            await task
        except Exception:
            pass  # 에러는 이미 _execute_task에서 처리됨
    
    async def _cleanup_worker(self):
        """정리 작업 워커"""
        while True:
            try:
                current_time = time.time()
                
                # 오래된 완료 태스크 정보 정리
                old_task_ids = [
                    task_id for task_id, task_info in self.task_info.items()
                    if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                        task_info.completed_at and
                        current_time - task_info.completed_at > 3600)  # 1시간 이상 된 것
                ]
                
                for task_id in old_task_ids:
                    del self.task_info[task_id]
                
                if old_task_ids:
                    logger.info(f"Cleaned up {len(old_task_ids)} old task records")
                
                # 다음 정리까지 대기
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                logger.info("Cleanup worker cancelled")
                break
            except Exception as e:
                logger.error(f"Cleanup worker error: {e}")
                await asyncio.sleep(60)
    
    async def _run_completion_callbacks(self, task_info: TaskInfo, error: Optional[Exception]):
        """완료 콜백 실행"""
        try:
            for callback in self.task_completion_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(task_info, error)
                    else:
                        callback(task_info, error)
                except Exception as e:
                    logger.error(f"Task completion callback failed: {e}")
        except Exception as e:
            logger.error(f"Error running completion callbacks: {e}")
    
    def add_completion_callback(self, callback: Callable):
        """완료 콜백 추가"""
        self.task_completion_callbacks.add(callback)
    
    def add_error_callback(self, callback: Callable):
        """에러 콜백 추가"""
        self.error_callbacks.add(callback)


# 글로벌 인스턴스
async_optimizer = AsyncOptimizer()


# 데코레이터들
def async_task(name: str = None, 
               priority: TaskPriority = TaskPriority.NORMAL,
               timeout: float = None,
               max_retries: int = 3):
    """비동기 태스크 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            task_name = name or f"{func.__module__}.{func.__name__}"
            coro = func(*args, **kwargs)
            task_id = await async_optimizer.submit_task(
                coro, task_name, priority, timeout, max_retries
            )
            return await async_optimizer.wait_for_task(task_id)
        return wrapper
    return decorator


def rate_limit(max_requests: int, window_seconds: int, key_func: Callable = None):
    """레이트 리미팅 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 키 생성
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__module__}.{func.__name__}"
            
            # 레이트 리미팅 체크
            if not async_optimizer.apply_rate_limit(key, max_requests, window_seconds):
                raise Exception(f"Rate limit exceeded for {key}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 유틸리티 함수들
async def start_async_optimizer():
    """비동기 최적화 시스템 시작"""
    await async_optimizer.start()


async def stop_async_optimizer():
    """비동기 최적화 시스템 중지"""
    await async_optimizer.stop()


async def submit_background_task(coro: Awaitable[Any], name: str, 
                                priority: TaskPriority = TaskPriority.NORMAL) -> str:
    """백그라운드 태스크 제출"""
    return await async_optimizer.submit_task(coro, name, priority)


def get_async_performance_dashboard() -> Dict[str, Any]:
    """비동기 성능 대시보드"""
    return {
        "stats": async_optimizer.get_performance_stats(),
        "recommendations": async_optimizer.get_optimization_recommendations()
    }
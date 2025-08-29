"""
WebSocket 성능 최적화 시스템

WebSocket 연결 최적화, 메시지 압축, 배치 전송을 통해
실시간 통신 지연시간을 최소화합니다.
"""

import asyncio
import gzip
import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
import weakref

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class CompressionType(str, Enum):
    """압축 타입"""
    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"


class MessagePriority(int, Enum):
    """메시지 우선순위"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class QueuedMessage:
    """큐에 저장되는 메시지"""
    message: Dict[str, Any]
    priority: MessagePriority
    timestamp: float
    attempts: int = 0
    max_attempts: int = 3
    
    def __lt__(self, other):
        # 우선순위가 높을수록, 시간이 오래될수록 먼저 처리
        if self.priority != other.priority:
            return self.priority > other.priority
        return self.timestamp < other.timestamp


@dataclass
class ConnectionMetrics:
    """연결 성능 메트릭"""
    connection_id: str
    connected_at: float
    last_heartbeat: float
    messages_sent: int
    messages_received: int
    bytes_sent: int
    bytes_received: int
    avg_latency_ms: float
    compression_ratio: float
    error_count: int
    
    def update_latency(self, latency_ms: float):
        """지연시간 업데이트"""
        if self.avg_latency_ms == 0:
            self.avg_latency_ms = latency_ms
        else:
            # 지수 이동 평균으로 업데이트
            self.avg_latency_ms = 0.8 * self.avg_latency_ms + 0.2 * latency_ms


class WebSocketOptimizer:
    """WebSocket 성능 최적화 관리자"""
    
    def __init__(self, 
                 batch_size: int = 10,
                 batch_interval_ms: int = 50,
                 compression_threshold: int = 1024,
                 heartbeat_interval: int = 30,
                 max_queue_size: int = 1000):
        
        self.batch_size = batch_size
        self.batch_interval_ms = batch_interval_ms / 1000  # Convert to seconds
        self.compression_threshold = compression_threshold
        self.heartbeat_interval = heartbeat_interval
        self.max_queue_size = max_queue_size
        
        # 연결 관리
        self.connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.connection_queues: Dict[str, asyncio.PriorityQueue] = {}
        
        # 메시지 배치 처리
        self.batch_buffers: Dict[str, List[QueuedMessage]] = defaultdict(list)
        self.last_batch_time: Dict[str, float] = defaultdict(float)
        
        # 성능 추적
        self.global_metrics = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_per_second': 0,
            'avg_latency_ms': 0,
            'compression_savings_bytes': 0
        }
        
        # 배치 처리 태스크
        self.batch_tasks: Dict[str, asyncio.Task] = {}
        self.heartbeat_task: Optional[asyncio.Task] = None
        
        # 약한 참조로 콜백 저장
        self.latency_callbacks: weakref.WeakSet = weakref.WeakSet()
        
        logger.info(f"WebSocketOptimizer initialized: batch_size={batch_size}, "
                   f"batch_interval={batch_interval_ms}ms, compression_threshold={compression_threshold}")
    
    async def add_connection(self, connection_id: str, websocket: WebSocket, 
                           compression_support: CompressionType = CompressionType.NONE) -> bool:
        """WebSocket 연결 추가"""
        try:
            if connection_id in self.connections:
                logger.warning(f"Connection {connection_id} already exists")
                return False
            
            self.connections[connection_id] = websocket
            self.connection_queues[connection_id] = asyncio.PriorityQueue(maxsize=self.max_queue_size)
            
            # 메트릭 초기화
            self.connection_metrics[connection_id] = ConnectionMetrics(
                connection_id=connection_id,
                connected_at=time.time(),
                last_heartbeat=time.time(),
                messages_sent=0,
                messages_received=0,
                bytes_sent=0,
                bytes_received=0,
                avg_latency_ms=0,
                compression_ratio=1.0,
                error_count=0
            )
            
            # 배치 처리 태스크 시작
            self.batch_tasks[connection_id] = asyncio.create_task(
                self._batch_processor(connection_id)
            )
            
            # 하트비트 태스크 시작 (첫 번째 연결시)
            if self.heartbeat_task is None:
                self.heartbeat_task = asyncio.create_task(self._heartbeat_worker())
            
            self.global_metrics['total_connections'] += 1
            self.global_metrics['active_connections'] += 1
            
            logger.info(f"WebSocket connection {connection_id} added successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add connection {connection_id}: {e}")
            return False
    
    async def remove_connection(self, connection_id: str) -> bool:
        """WebSocket 연결 제거"""
        try:
            if connection_id not in self.connections:
                return False
            
            # 배치 처리 태스크 정리
            if connection_id in self.batch_tasks:
                self.batch_tasks[connection_id].cancel()
                try:
                    await self.batch_tasks[connection_id]
                except asyncio.CancelledError:
                    pass
                del self.batch_tasks[connection_id]
            
            # 연결 정보 정리
            del self.connections[connection_id]
            del self.connection_queues[connection_id]
            
            if connection_id in self.batch_buffers:
                del self.batch_buffers[connection_id]
            if connection_id in self.last_batch_time:
                del self.last_batch_time[connection_id]
            if connection_id in self.connection_metrics:
                del self.connection_metrics[connection_id]
            
            self.global_metrics['active_connections'] = len(self.connections)
            
            # 모든 연결이 종료되면 하트비트 태스크도 정리
            if not self.connections and self.heartbeat_task:
                self.heartbeat_task.cancel()
                self.heartbeat_task = None
            
            logger.info(f"WebSocket connection {connection_id} removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove connection {connection_id}: {e}")
            return False
    
    async def send_message(self, connection_id: str, message: Dict[str, Any], 
                          priority: MessagePriority = MessagePriority.NORMAL,
                          force_immediate: bool = False) -> bool:
        """최적화된 메시지 전송"""
        try:
            if connection_id not in self.connections:
                logger.warning(f"Connection {connection_id} not found")
                return False
            
            # 메시지에 타임스탬프 추가
            message['timestamp'] = time.time()
            message['message_id'] = f"{connection_id}_{int(time.time() * 1000)}"
            
            queued_message = QueuedMessage(
                message=message,
                priority=priority,
                timestamp=time.time()
            )
            
            # 즉시 전송이 필요하거나 CRITICAL 우선순위인 경우
            if force_immediate or priority == MessagePriority.CRITICAL:
                return await self._send_single_message(connection_id, queued_message)
            
            # 큐에 추가하여 배치 처리
            try:
                queue = self.connection_queues[connection_id]
                queue.put_nowait(queued_message)
                return True
            except asyncio.QueueFull:
                logger.warning(f"Message queue full for connection {connection_id}")
                # 큐가 가득 찬 경우 즉시 전송 시도
                return await self._send_single_message(connection_id, queued_message)
                
        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            return False
    
    async def broadcast_message(self, message: Dict[str, Any], 
                              priority: MessagePriority = MessagePriority.NORMAL,
                              exclude_connections: List[str] = None) -> int:
        """모든 연결에 메시지 브로드캐스트"""
        exclude_connections = exclude_connections or []
        success_count = 0
        
        tasks = []
        for connection_id in self.connections:
            if connection_id not in exclude_connections:
                task = self.send_message(connection_id, message.copy(), priority)
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for result in results if result is True)
        
        return success_count
    
    def get_connection_metrics(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """연결 메트릭 조회"""
        if connection_id not in self.connection_metrics:
            return None
        
        metrics = self.connection_metrics[connection_id]
        return {
            "connection_id": metrics.connection_id,
            "connected_duration_seconds": time.time() - metrics.connected_at,
            "last_heartbeat_seconds_ago": time.time() - metrics.last_heartbeat,
            "messages_sent": metrics.messages_sent,
            "messages_received": metrics.messages_received,
            "bytes_sent": metrics.bytes_sent,
            "bytes_received": metrics.bytes_received,
            "avg_latency_ms": round(metrics.avg_latency_ms, 2),
            "compression_ratio": round(metrics.compression_ratio, 3),
            "error_count": metrics.error_count,
            "queue_size": self.connection_queues[connection_id].qsize() if connection_id in self.connection_queues else 0
        }
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """전역 메트릭 조회"""
        # 평균 지연시간 계산
        if self.connection_metrics:
            avg_latency = sum(m.avg_latency_ms for m in self.connection_metrics.values()) / len(self.connection_metrics)
        else:
            avg_latency = 0
        
        return {
            "total_connections": self.global_metrics['total_connections'],
            "active_connections": len(self.connections),
            "avg_latency_ms": round(avg_latency, 2),
            "total_messages_sent": sum(m.messages_sent for m in self.connection_metrics.values()),
            "total_bytes_sent": sum(m.bytes_sent for m in self.connection_metrics.values()),
            "compression_savings_bytes": self.global_metrics['compression_savings_bytes'],
            "queue_sizes": {
                conn_id: queue.qsize() 
                for conn_id, queue in self.connection_queues.items()
            }
        }
    
    def get_performance_recommendations(self) -> List[str]:
        """성능 최적화 권장사항"""
        recommendations = []
        
        # 전역 메트릭 분석
        global_metrics = self.get_global_metrics()
        avg_latency = global_metrics.get('avg_latency_ms', 0)
        
        if avg_latency > 100:
            recommendations.append(f"평균 지연시간이 {avg_latency:.1f}ms로 높습니다. 배치 크기를 늘리거나 압축을 활성화하세요.")
        
        # 큐 크기 분석
        queue_sizes = global_metrics.get('queue_sizes', {})
        max_queue_size = max(queue_sizes.values()) if queue_sizes else 0
        if max_queue_size > self.max_queue_size * 0.8:
            recommendations.append(f"메시지 큐가 포화상태입니다 (최대 {max_queue_size}). 배치 처리 간격을 단축하세요.")
        
        # 연결별 분석
        high_error_connections = [
            conn_id for conn_id, metrics in self.connection_metrics.items()
            if metrics.error_count > 10
        ]
        if high_error_connections:
            recommendations.append(f"{len(high_error_connections)}개 연결에서 높은 에러율이 감지되었습니다.")
        
        # 압축 효율성 분석
        compression_ratios = [m.compression_ratio for m in self.connection_metrics.values()]
        if compression_ratios:
            avg_compression = sum(compression_ratios) / len(compression_ratios)
            if avg_compression > 0.9:  # 압축률이 낮음
                recommendations.append("메시지 압축 효과가 낮습니다. 압축 알고리즘 변경을 고려하세요.")
        
        if not recommendations:
            recommendations.append("WebSocket 성능이 양호합니다.")
        
        return recommendations
    
    # Private methods
    
    async def _send_single_message(self, connection_id: str, 
                                 queued_message: QueuedMessage) -> bool:
        """단일 메시지 전송"""
        try:
            websocket = self.connections.get(connection_id)
            if not websocket:
                return False
            
            message_data = json.dumps(queued_message.message, ensure_ascii=False)
            message_bytes = message_data.encode('utf-8')
            
            # 압축 적용 여부 결정
            if len(message_bytes) > self.compression_threshold:
                compressed_data = gzip.compress(message_bytes)
                if len(compressed_data) < len(message_bytes):
                    message_bytes = compressed_data
                    queued_message.message['compressed'] = True
                    
                    # 압축률 업데이트
                    compression_ratio = len(compressed_data) / len(message_data.encode('utf-8'))
                    self.connection_metrics[connection_id].compression_ratio = compression_ratio
                    self.global_metrics['compression_savings_bytes'] += len(message_data.encode('utf-8')) - len(compressed_data)
            
            # 전송 시작 시간 기록
            send_start = time.time()
            
            # 메시지 전송
            await websocket.send_bytes(message_bytes)
            
            # 메트릭 업데이트
            metrics = self.connection_metrics[connection_id]
            metrics.messages_sent += 1
            metrics.bytes_sent += len(message_bytes)
            
            # 지연시간 측정 (클라이언트 응답 시간은 별도 측정)
            send_time_ms = (time.time() - send_start) * 1000
            if send_time_ms > 0:
                metrics.update_latency(send_time_ms)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send single message to {connection_id}: {e}")
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].error_count += 1
            return False
    
    async def _send_batch_messages(self, connection_id: str, 
                                 messages: List[QueuedMessage]) -> int:
        """배치 메시지 전송"""
        try:
            if not messages:
                return 0
            
            websocket = self.connections.get(connection_id)
            if not websocket:
                return 0
            
            # 배치 메시지 구성
            batch_data = {
                "type": "batch_messages",
                "count": len(messages),
                "messages": [msg.message for msg in messages],
                "timestamp": time.time()
            }
            
            message_data = json.dumps(batch_data, ensure_ascii=False)
            message_bytes = message_data.encode('utf-8')
            
            # 압축 적용
            if len(message_bytes) > self.compression_threshold:
                compressed_data = gzip.compress(message_bytes)
                if len(compressed_data) < len(message_bytes):
                    message_bytes = compressed_data
                    batch_data['compressed'] = True
                    
                    # 압축률 업데이트
                    compression_ratio = len(compressed_data) / len(message_data.encode('utf-8'))
                    self.connection_metrics[connection_id].compression_ratio = compression_ratio
            
            # 배치 전송
            await websocket.send_bytes(message_bytes)
            
            # 메트릭 업데이트
            metrics = self.connection_metrics[connection_id]
            metrics.messages_sent += len(messages)
            metrics.bytes_sent += len(message_bytes)
            
            return len(messages)
            
        except Exception as e:
            logger.error(f"Failed to send batch messages to {connection_id}: {e}")
            if connection_id in self.connection_metrics:
                self.connection_metrics[connection_id].error_count += 1
            return 0
    
    async def _batch_processor(self, connection_id: str):
        """배치 처리 워커"""
        while connection_id in self.connections:
            try:
                current_time = time.time()
                batch_buffer = self.batch_buffers[connection_id]
                
                # 큐에서 메시지 수집
                queue = self.connection_queues[connection_id]
                messages_collected = 0
                
                # 배치 크기만큼 또는 타임아웃까지 메시지 수집
                while messages_collected < self.batch_size and len(batch_buffer) < self.batch_size:
                    try:
                        # 짧은 타임아웃으로 메시지 대기
                        queued_message = await asyncio.wait_for(queue.get(), timeout=0.01)
                        batch_buffer.append(queued_message)
                        messages_collected += 1
                    except asyncio.TimeoutError:
                        break
                
                # 배치 전송 조건 확인
                should_send_batch = (
                    len(batch_buffer) >= self.batch_size or
                    (batch_buffer and current_time - self.last_batch_time[connection_id] >= self.batch_interval_ms)
                )
                
                if should_send_batch and batch_buffer:
                    sent_count = await self._send_batch_messages(connection_id, batch_buffer)
                    if sent_count > 0:
                        batch_buffer.clear()
                        self.last_batch_time[connection_id] = current_time
                
                # CPU 부하 방지를 위한 짧은 대기
                await asyncio.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Batch processor error for {connection_id}: {e}")
                await asyncio.sleep(1)
    
    async def _heartbeat_worker(self):
        """하트비트 워커"""
        while self.connections:
            try:
                current_time = time.time()
                
                # 모든 연결에 하트비트 전송
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": current_time,
                    "server_time": current_time
                }
                
                for connection_id in list(self.connections.keys()):
                    try:
                        await self.send_message(
                            connection_id, 
                            heartbeat_message.copy(), 
                            MessagePriority.LOW
                        )
                        self.connection_metrics[connection_id].last_heartbeat = current_time
                    except Exception as e:
                        logger.error(f"Heartbeat failed for {connection_id}: {e}")
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Heartbeat worker error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
    
    def add_latency_callback(self, callback: Callable[[str, float], None]):
        """지연시간 측정 콜백 추가"""
        self.latency_callbacks.add(callback)


# 글로벌 인스턴스
websocket_optimizer = WebSocketOptimizer()


# 유틸리티 함수들
async def optimize_websocket_connection(connection_id: str, websocket: WebSocket) -> bool:
    """WebSocket 연결 최적화"""
    return await websocket_optimizer.add_connection(connection_id, websocket)


async def send_optimized_message(connection_id: str, message: Dict[str, Any], 
                                priority: MessagePriority = MessagePriority.NORMAL) -> bool:
    """최적화된 메시지 전송"""
    return await websocket_optimizer.send_message(connection_id, message, priority)


async def broadcast_optimized_message(message: Dict[str, Any], 
                                    priority: MessagePriority = MessagePriority.NORMAL) -> int:
    """최적화된 브로드캐스트"""
    return await websocket_optimizer.broadcast_message(message, priority)


def get_websocket_performance_dashboard() -> Dict[str, Any]:
    """WebSocket 성능 대시보드"""
    return {
        "global_metrics": websocket_optimizer.get_global_metrics(),
        "connection_count": len(websocket_optimizer.connections),
        "recommendations": websocket_optimizer.get_performance_recommendations()
    }
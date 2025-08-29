"""
성능 모니터링 API 엔드포인트

시스템 성능 메트릭, 최적화 권장사항, 실시간 모니터링 데이터를 제공합니다.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

from ..core.performance_monitor import performance_monitor, get_performance_dashboard
from ..core.memory_manager import memory_manager, get_memory_dashboard
from ..core.async_optimizer import async_optimizer, get_async_performance_dashboard
from ..core.websocket_optimizer import websocket_optimizer, get_websocket_performance_dashboard
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("/dashboard", summary="성능 대시보드")
async def get_performance_dashboard_endpoint() -> Dict[str, Any]:
    """
    종합 성능 대시보드 데이터를 반환합니다.
    """
    try:
        dashboard_data = await get_performance_dashboard()
        memory_data = get_memory_dashboard()
        async_data = get_async_performance_dashboard()
        websocket_data = get_websocket_performance_dashboard()
        
        # 캐시 통계
        cache_stats = cache_service.get_stats()
        
        return {
            "success": True,
            "data": {
                "performance": dashboard_data,
                "memory": memory_data,
                "async_processing": async_data,
                "websocket": websocket_data,
                "cache": cache_stats,
                "timestamp": performance_monitor.get_performance_summary(1).get("time_range_minutes", 60)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", summary="성능 요약")
async def get_performance_summary(
    minutes: int = Query(60, ge=1, le=1440, description="조회할 시간 범위 (분)")
) -> Dict[str, Any]:
    """
    지정된 시간 범위의 성능 요약 정보를 반환합니다.
    """
    try:
        summary = performance_monitor.get_performance_summary(minutes)
        return {
            "success": True,
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory", summary="메모리 통계")
async def get_memory_stats(
    hours: int = Query(1, ge=1, le=24, description="조회할 시간 범위 (시간)")
) -> Dict[str, Any]:
    """
    메모리 사용량 통계를 반환합니다.
    """
    try:
        stats = memory_manager.get_memory_stats(hours)
        leaks = memory_manager.get_memory_leaks()
        recommendations = memory_manager.get_memory_recommendations()
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "memory_leaks": leaks,
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/gc", summary="강제 가비지 컬렉션")
async def force_garbage_collection() -> Dict[str, Any]:
    """
    강제로 가비지 컬렉션을 실행합니다.
    """
    try:
        result = await memory_manager.force_garbage_collection()
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to force garbage collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memory/cleanup", summary="메모리 정리")
async def cleanup_memory() -> Dict[str, Any]:
    """
    메모리 정리 작업을 수행합니다.
    """
    try:
        result = memory_manager.cleanup_resources()
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/async", summary="비동기 처리 통계")
async def get_async_stats() -> Dict[str, Any]:
    """
    비동기 처리 성능 통계를 반환합니다.
    """
    try:
        stats = async_optimizer.get_performance_stats()
        recommendations = async_optimizer.get_optimization_recommendations()
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get async stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/websocket", summary="WebSocket 성능 통계")
async def get_websocket_stats() -> Dict[str, Any]:
    """
    WebSocket 연결 및 성능 통계를 반환합니다.
    """
    try:
        global_metrics = websocket_optimizer.get_global_metrics()
        recommendations = websocket_optimizer.get_performance_recommendations()
        
        return {
            "success": True,
            "data": {
                "global_metrics": global_metrics,
                "recommendations": recommendations
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get websocket stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache", summary="캐시 통계")
async def get_cache_stats() -> Dict[str, Any]:
    """
    캐시 시스템 성능 통계를 반환합니다.
    """
    try:
        stats = cache_service.get_stats()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear", summary="캐시 초기화")
async def clear_cache(
    pattern: Optional[str] = Query(None, description="삭제할 캐시 패턴 (선택사항)")
) -> Dict[str, Any]:
    """
    캐시를 초기화합니다. 패턴이 지정되면 해당 패턴과 일치하는 캐시만 삭제합니다.
    """
    try:
        if pattern:
            cleared_count = cache_service.clear_pattern(pattern)
        else:
            cleared_count = cache_service.clear()
        
        return {
            "success": True,
            "data": {
                "cleared_entries": cleared_count,
                "pattern": pattern
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/endpoints", summary="엔드포인트별 성능 통계")
async def get_endpoint_performance() -> Dict[str, Any]:
    """
    엔드포인트별 성능 통계를 반환합니다.
    """
    try:
        stats = performance_monitor.get_endpoint_stats()
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get endpoint performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-health", summary="시스템 건강 상태")
async def get_system_health() -> Dict[str, Any]:
    """
    전반적인 시스템 건강 상태를 반환합니다.
    """
    try:
        health = memory_manager.get_system_health()
        return {
            "success": True,
            "data": health
        }
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations", summary="최적화 권장사항")
async def get_optimization_recommendations() -> Dict[str, Any]:
    """
    종합적인 성능 최적화 권장사항을 반환합니다.
    """
    try:
        performance_recs = performance_monitor.get_optimization_recommendations()
        memory_recs = memory_manager.get_memory_recommendations()
        async_recs = async_optimizer.get_optimization_recommendations()
        websocket_recs = websocket_optimizer.get_performance_recommendations()
        
        return {
            "success": True,
            "data": {
                "performance": performance_recs,
                "memory": memory_recs,
                "async_processing": async_recs,
                "websocket": websocket_recs,
                "overall_priority": _prioritize_recommendations([
                    *performance_recs,
                    *memory_recs,
                    *async_recs,
                    *websocket_recs
                ])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", summary="성능 데이터 내보내기")
async def export_performance_data() -> Dict[str, Any]:
    """
    성능 데이터를 JSON 형태로 내보냅니다.
    """
    try:
        # 각 시스템에서 데이터 수집
        performance_data = performance_monitor.export_metrics()
        
        return {
            "success": True,
            "data": {
                "export_completed": True,
                "data_size_bytes": len(performance_data.encode('utf-8')) if isinstance(performance_data, str) else 0,
                "export_format": "json"
            },
            "raw_data": performance_data
        }
        
    except Exception as e:
        logger.error(f"Failed to export performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _prioritize_recommendations(recommendations: List[str]) -> List[Dict[str, Any]]:
    """권장사항에 우선순위 부여"""
    priority_keywords = {
        "critical": ["critical", "즉시", "중요", "심각"],
        "high": ["높습니다", "high", "크게", "많이"],
        "medium": ["고려", "권장", "검토", "확인"],
        "low": ["양호", "정상", "괜찮"]
    }
    
    prioritized = []
    
    for rec in recommendations:
        priority = "medium"  # 기본값
        
        for level, keywords in priority_keywords.items():
            if any(keyword in rec for keyword in keywords):
                priority = level
                break
        
        prioritized.append({
            "recommendation": rec,
            "priority": priority,
            "category": _categorize_recommendation(rec)
        })
    
    # 우선순위별로 정렬
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    prioritized.sort(key=lambda x: priority_order.get(x["priority"], 2))
    
    return prioritized


def _categorize_recommendation(recommendation: str) -> str:
    """권장사항을 카테고리별로 분류"""
    categories = {
        "memory": ["메모리", "memory", "가비지", "누수"],
        "performance": ["응답", "지연", "성능", "속도"],
        "database": ["데이터베이스", "쿼리", "DB"],
        "network": ["네트워크", "연결", "WebSocket"],
        "cache": ["캐시", "cache"],
        "async": ["비동기", "태스크", "async", "워커"]
    }
    
    for category, keywords in categories.items():
        if any(keyword in recommendation for keyword in keywords):
            return category
    
    return "general"
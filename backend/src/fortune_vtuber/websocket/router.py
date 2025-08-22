"""
WebSocket Router Module - WebSocket 엔드포인트 통합

실시간 채팅, Live2D 상태 동기화, 시스템 모니터링
"""

from fastapi import APIRouter
from .chat_websocket import router as websocket_router

# WebSocket 라우터 생성
ws_router = APIRouter(prefix="/ws")

# WebSocket 엔드포인트 등록
ws_router.include_router(websocket_router)
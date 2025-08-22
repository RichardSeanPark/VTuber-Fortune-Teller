"""
간단한 API 테스트용 엔드포인트
"""

from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/hello")
async def hello():
    """간단한 헬로 월드 테스트"""
    return {"message": "Hello, Fortune VTuber API!"}

@router.get("/health")
async def health():
    """간단한 헬스 체크"""
    return {"status": "healthy", "service": "fortune-vtuber-api"}
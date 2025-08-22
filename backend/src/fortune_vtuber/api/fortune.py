"""
Fortune API Router - 운세 관련 엔드포인트

4가지 운세 타입 (일일, 타로, 별자리, 사주) API 제공
사용자 맞춤형 운세 생성 및 히스토리 관리
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config.database import get_db
from ..services.fortune_service import FortuneService
from ..services.cache_service import CacheService
from ..models.fortune import (
    FortuneType, QuestionType, ZodiacSign,
    TarotReadingRequest, TarotReadingResponse
)
from ..fortune.engines import (
    FortuneEngineFactory, PersonalizationContext,
    FortuneType as EngineFortuneType
)

logger = logging.getLogger(__name__)

# Initialize services with proper dependencies
from ..services.cache_service import CacheService
cache_service = CacheService()
fortune_service = FortuneService(database_service=None, cache_service=cache_service)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/fortune", tags=["Fortune"])

# Note: Rate limit error handler should be registered at app level


# Response Standardization Functions
def _standardize_tarot_response(fortune_result: Dict[str, Any]) -> Dict[str, Any]:
    """타로 운세 응답을 프론트엔드 호환 형식으로 변환"""
    cards = fortune_result.get("cards", [])
    
    # 카드 데이터를 간소화된 형식으로 변환
    simplified_cards = []
    for card in cards:
        simplified_cards.append({
            "id": len(simplified_cards),  # 인덱스를 ID로 사용
            "name": card.get("card_name", ""),
            "name_ko": card.get("card_name_ko", ""),
            "position": card.get("position", ""),
            "meaning": card.get("card_meaning", ""),
            "interpretation": card.get("interpretation", ""),
            "image_url": card.get("image_url", ""),
            "emoji": _get_tarot_emoji(card.get("card_name", ""))
        })
    
    return {
        "type": "tarot",  # fortune_type -> type
        "fortune_id": fortune_result.get("fortune_id", ""),
        "question": fortune_result.get("question", ""),
        "question_type": fortune_result.get("question_type", "general"),
        "cards": simplified_cards,
        "message": fortune_result.get("overall_interpretation", ""),  # overall_interpretation -> message
        "advice": fortune_result.get("advice", ""),
        "live2d_emotion": fortune_result.get("live2d_emotion", "mystical"),
        "live2d_motion": fortune_result.get("live2d_motion", "card_draw"),
        "created_at": fortune_result.get("created_at", datetime.now().isoformat())
    }


def _standardize_daily_response(fortune_result: Dict[str, Any]) -> Dict[str, Any]:
    """일일 운세 응답을 프론트엔드 호환 형식으로 변환"""
    content = fortune_result.get("content", {})
    categories = content.get("categories", {})
    overall_fortune = content.get("overall_fortune", {})
    
    # 메시지 우선순위: interpretation > overall_fortune.description > advice > 기본 메시지
    message = (
        fortune_result.get("interpretation") or
        overall_fortune.get("description") or
        content.get("advice") or
        "오늘은 좋은 하루가 될 것 같아요!"
    )
    
    return {
        "type": "daily",
        "fortune_id": fortune_result.get("fortune_id", ""),
        "score": overall_fortune.get("score") or content.get("overall_score", 75),
        "message": message,
        "love": categories.get("love", {}).get("score", 70),
        "money": categories.get("money", {}).get("score", 65),
        "health": categories.get("health", {}).get("score", 80),
        "work": categories.get("work", {}).get("score", 75),
        "luckyColor": content.get("lucky_elements", {}).get("color") or 
                     (content.get("lucky_colors", []) and content["lucky_colors"][0]) or "파란색",
        "luckyNumber": str(content.get("lucky_elements", {}).get("number") or 
                          (content.get("lucky_numbers", []) and content["lucky_numbers"][0]) or "7"),
        "luckyItem": content.get("lucky_elements", {}).get("item") or 
                    (content.get("lucky_items", []) and content["lucky_items"][0]) or "목걸이",
        "live2d_emotion": fortune_result.get("live2d_emotion", "joy"),
        "live2d_motion": fortune_result.get("live2d_motion", "greeting"),
        "created_at": fortune_result.get("created_at", datetime.now().isoformat())
    }


def _standardize_zodiac_response(fortune_result: Dict[str, Any]) -> Dict[str, Any]:
    """별자리 운세 응답을 프론트엔드 호환 형식으로 변환"""
    content = fortune_result.get("content", {})
    zodiac_info = content.get("zodiac_info", {})
    fortune_categories = content.get("fortune", {})
    
    # 별자리별 기본 메시지 생성
    zodiac_sign = fortune_result.get("zodiac_sign", "aries")
    zodiac_names = {
        "aries": "양자리", "taurus": "황소자리", "gemini": "쌍둥이자리", 
        "cancer": "게자리", "leo": "사자자리", "virgo": "처녀자리",
        "libra": "천칭자리", "scorpio": "전갈자리", "sagittarius": "사수자리",
        "capricorn": "염소자리", "aquarius": "물병자리", "pisces": "물고기자리"
    }
    
    # 메시지 우선순위: interpretation > fortune 요약 > 기본 메시지
    if fortune_result.get("interpretation"):
        message = fortune_result["interpretation"]
    elif fortune_categories:
        # fortune 카테고리에서 메시지 구성
        love_score = fortune_categories.get("love", {}).get("score", 70)
        career_score = fortune_categories.get("career", {}).get("score", 70)
        message = f"{zodiac_names.get(zodiac_sign, '당신의')} 별자리 운세를 알려드려요! 오늘은 연애운 {love_score}점, 직업운 {career_score}점으로 전반적으로 좋은 하루가 될 것 같아요."
    else:
        message = f"{zodiac_names.get(zodiac_sign, '당신의')} 별자리는 오늘 특별한 기운이 흐르고 있어요. 긍정적인 마음으로 하루를 시작해보세요!"
    
    return {
        "type": "zodiac",
        "fortune_id": fortune_result.get("fortune_id", ""),
        "zodiac": zodiac_sign,
        "score": content.get("overall_score") or 
                (sum(cat.get("score", 70) for cat in fortune_categories.values()) // len(fortune_categories) if fortune_categories else 75),
        "message": message,
        "traits": (zodiac_info.get("traits") or 
                  content.get("personality_traits") or 
                  ["리더십이 강함", "도전정신이 뛰어남"]),
        "goodCompat": zodiac_info.get("compatible_signs") or "사자자리, 사수자리",
        "badCompat": zodiac_info.get("incompatible_signs") or "게자리, 염소자리",
        "live2d_emotion": fortune_result.get("live2d_emotion", "mystical"),
        "live2d_motion": fortune_result.get("live2d_motion", "crystal_gaze"),
        "created_at": fortune_result.get("created_at", datetime.now().isoformat())
    }


def _get_tarot_emoji(card_name: str) -> str:
    """타로 카드 이름에 따른 이모지 반환"""
    emoji_map = {
        "The Fool": "🤪",
        "The Magician": "🎩",
        "The High Priestess": "🔮",
        "The Empress": "👸",
        "The Emperor": "👑",
        "The Hierophant": "⛪",
        "The Lovers": "💕",
        "The Chariot": "🏎️",
        "Strength": "💪",
        "The Hermit": "🔦",
        "Wheel of Fortune": "🎰",
        "Justice": "⚖️",
        "The Hanged Man": "🙃",
        "Death": "💀",
        "Temperance": "🍷",
        "The Devil": "😈",
        "The Tower": "🏗️",
        "The Star": "⭐",
        "The Moon": "🌙",
        "The Sun": "☀️",
        "Judgement": "📯",
        "The World": "🌍"
    }
    return emoji_map.get(card_name, "🔮")


# Request/Response Models
class DailyFortuneRequest(BaseModel):
    """일일 운세 요청 모델"""
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    zodiac: Optional[ZodiacSign] = Field(None, description="별자리")
    user_uuid: Optional[str] = Field(None, description="사용자 UUID")
    force_regenerate: bool = Field(False, description="강제 재생성 여부")
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        if v:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v


class ZodiacFortuneRequest(BaseModel):
    """별자리 운세 요청 모델"""
    period: str = Field("daily", description="기간 (daily, weekly, monthly)")
    user_uuid: Optional[str] = Field(None, description="사용자 UUID")
    force_regenerate: bool = Field(False, description="강제 재생성 여부")
    
    @validator('period')
    def validate_period(cls, v):
        if v not in ["daily", "weekly", "monthly"]:
            raise ValueError("Period must be one of: daily, weekly, monthly")
        return v


class OrientalFortuneRequest(BaseModel):
    """사주 운세 요청 모델"""
    birth_date: str = Field(..., description="생년월일 (YYYY-MM-DD)")
    birth_time: Optional[str] = Field("12:00", description="태어난 시간 (HH:MM)")
    birth_location: Optional[str] = Field(None, description="출생지")
    user_uuid: Optional[str] = Field(None, description="사용자 UUID")
    
    @validator('birth_date')
    def validate_birth_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v
    
    @validator('birth_time')
    def validate_birth_time(cls, v):
        if v:
            try:
                datetime.strptime(v, "%H:%M")
            except ValueError:
                raise ValueError("Invalid time format. Use HH:MM")
        return v


class FortuneHistoryRequest(BaseModel):
    """운세 히스토리 요청 모델"""
    user_uuid: str = Field(..., description="사용자 UUID")
    fortune_type: Optional[str] = Field("all", description="운세 타입")
    page: int = Field(1, ge=1, description="페이지 번호")
    limit: int = Field(20, ge=1, le=100, description="페이지 크기")
    date_from: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")


# API Endpoints
@router.get("/daily", 
           summary="일일 운세 조회",
           description="사용자 맞춤형 일일 운세를 조회합니다. 생년월일과 별자리 정보로 개인화됩니다.")
@limiter.limit("10/minute")  # Allow 10 requests per minute per IP
async def get_daily_fortune(
    request: Request,
    birth_date: Optional[str] = Query(None, description="생년월일 (YYYY-MM-DD)"),
    zodiac: Optional[ZodiacSign] = Query(None, description="별자리"),
    user_uuid: Optional[str] = Query(None, description="사용자 UUID"),
    force_regenerate: bool = Query(False, description="강제 재생성 여부"),
    db: Session = Depends(get_db)
):
    """일일 운세 조회"""
    try:
        # 사용자 데이터 구성
        user_data = None
        if any([birth_date, zodiac, user_uuid]):
            user_data = {}
            if birth_date:
                user_data["birth_date"] = birth_date
            if zodiac:
                user_data["zodiac"] = zodiac.value
            if user_uuid:
                user_data["user_uuid"] = user_uuid
            if force_regenerate:
                user_data["force_regenerate"] = force_regenerate
        
        # 일일 운세 생성/조회
        fortune_result = await fortune_service.get_daily_fortune(
            db, user_data, force_regenerate
        )
        
        return {
            "success": True,
            "data": fortune_result,
            "metadata": {
                "request_id": f"daily_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "cached": not force_regenerate
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_daily_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"운세 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/daily",
            summary="일일 운세 생성",
            description="POST 방식으로 일일 운세를 요청합니다.")
async def create_daily_fortune(
    request: DailyFortuneRequest,
    db: Session = Depends(get_db)
):
    """일일 운세 생성 (POST)"""
    try:
        # 사용자 데이터 구성
        user_data = request.dict(exclude_none=True)
        
        # 일일 운세 생성/조회
        fortune_result = await fortune_service.get_daily_fortune(
            db, user_data if user_data else None, request.force_regenerate
        )
        
        # 프론트엔드 호환 형식으로 변환
        standardized_result = _standardize_daily_response(fortune_result)
        
        return {
            "success": True,
            "data": standardized_result,
            "metadata": {
                "request_id": f"daily_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "POST"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_daily_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/tarot",
            summary="타로 운세 생성", 
            description="질문을 기반으로 타로 카드 운세를 생성합니다.")
@limiter.limit("5/minute")
async def create_tarot_fortune(
    request: Request,
    tarot_request: TarotReadingRequest,
    user_uuid: Optional[str] = Query(None, description="사용자 UUID"),
    db: Session = Depends(get_db)
):
    """타로 운세 생성"""
    try:
        # 사용자 데이터 구성
        user_data = {"user_uuid": user_uuid} if user_uuid else None
        
        # 타로 운세 생성
        fortune_result = await fortune_service.get_tarot_fortune(
            db, tarot_request.question, tarot_request.question_type, user_data, tarot_request.card_count
        )
        
        # 프론트엔드 호환 형식으로 변환
        standardized_result = _standardize_tarot_response(fortune_result)
        
        return {
            "success": True,
            "data": standardized_result,
            "metadata": {
                "request_id": f"tarot_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "question_length": len(tarot_request.question)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_tarot_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"타로 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/zodiac/{zodiac_sign}",
           summary="별자리 운세 조회",
           description="특정 별자리의 운세를 조회합니다.")
async def get_zodiac_fortune(
    zodiac_sign: ZodiacSign,
    period: str = Query("daily", description="기간 (daily, weekly, monthly)"),
    user_uuid: Optional[str] = Query(None, description="사용자 UUID"),
    force_regenerate: bool = Query(False, description="강제 재생성 여부"),
    db: Session = Depends(get_db)
):
    """별자리 운세 조회"""
    try:
        # 입력 검증
        if period not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail="period는 daily, weekly, monthly 중 하나여야 합니다.")
        
        # 사용자 데이터 구성
        user_data = None
        if user_uuid or force_regenerate:
            user_data = {}
            if user_uuid:
                user_data["user_uuid"] = user_uuid
            if force_regenerate:
                user_data["force_regenerate"] = force_regenerate
        
        # 별자리 운세 생성/조회
        fortune_result = await fortune_service.get_zodiac_fortune(
            db, zodiac_sign, period, user_data
        )
        
        # 프론트엔드 호환 형식으로 변환
        standardized_result = _standardize_zodiac_response(fortune_result)
        
        return {
            "success": True,
            "data": standardized_result,
            "metadata": {
                "request_id": f"zodiac_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "zodiac_sign": zodiac_sign.value,
                "period": period
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_zodiac_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"별자리 운세 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/zodiac/{zodiac_sign}",
            summary="별자리 운세 생성",
            description="POST 방식으로 별자리 운세를 요청합니다.")
async def create_zodiac_fortune(
    zodiac_sign: ZodiacSign,
    request: ZodiacFortuneRequest,
    db: Session = Depends(get_db)
):
    """별자리 운세 생성 (POST)"""
    try:
        # 사용자 데이터 구성
        user_data = request.dict(exclude_none=True)
        
        # 별자리 운세 생성/조회
        fortune_result = await fortune_service.get_zodiac_fortune(
            db, zodiac_sign, request.period, user_data if user_data else None
        )
        
        return {
            "success": True,
            "data": fortune_result,
            "metadata": {
                "request_id": f"zodiac_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "POST"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_zodiac_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"별자리 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/oriental",
            summary="사주 운세 생성",
            description="생년월일시를 기반으로 사주 운세를 생성합니다.")
async def create_oriental_fortune(
    request: OrientalFortuneRequest,
    db: Session = Depends(get_db)
):
    """사주 운세 생성"""
    try:
        # 생년월일시 데이터 구성
        birth_data = {
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "birth_location": request.birth_location
        }
        
        # 사용자 데이터 구성
        user_data = {"user_uuid": request.user_uuid} if request.user_uuid else None
        
        # 사주 운세 생성
        fortune_result = await fortune_service.get_oriental_fortune(
            db, birth_data, user_data
        )
        
        return {
            "success": True,
            "data": fortune_result,
            "metadata": {
                "request_id": f"oriental_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "birth_date": request.birth_date
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_oriental_fortune: {e}")
        raise HTTPException(status_code=500, detail=f"사주 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/history",
           summary="운세 히스토리 조회",
           description="사용자의 운세 히스토리를 조회합니다.")
async def get_fortune_history(
    user_uuid: str = Query(..., description="사용자 UUID"),
    fortune_type: str = Query("all", description="운세 타입 (all, daily, tarot, zodiac, oriental)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지 크기"),
    date_from: Optional[str] = Query(None, description="시작 날짜 (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="종료 날짜 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """운세 히스토리 조회"""
    try:
        # 입력 검증
        valid_types = ["all", "daily", "tarot", "zodiac", "oriental"]
        if fortune_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"fortune_type은 {valid_types} 중 하나여야 합니다."
            )
        
        # 날짜 검증
        if date_from:
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="date_from 형식이 올바르지 않습니다 (YYYY-MM-DD)")
        
        if date_to:
            try:
                datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="date_to 형식이 올바르지 않습니다 (YYYY-MM-DD)")
        
        # 페이지네이션 적용된 히스토리 조회
        offset = (page - 1) * limit
        histories = await fortune_service.get_fortune_history(
            db, user_uuid, fortune_type if fortune_type != "all" else None, limit + offset
        )
        
        # 페이지네이션 적용
        total_count = len(histories)
        paginated_histories = histories[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "histories": paginated_histories,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total_count,
                    "pages": (total_count + limit - 1) // limit
                }
            },
            "metadata": {
                "request_id": f"history_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_fortune_history: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/history",
            summary="운세 히스토리 조회 (POST)",
            description="POST 방식으로 운세 히스토리를 조회합니다.")
async def create_fortune_history_query(
    request: FortuneHistoryRequest,
    db: Session = Depends(get_db)
):
    """운세 히스토리 조회 (POST)"""
    try:
        # 페이지네이션 적용된 히스토리 조회
        offset = (request.page - 1) * request.limit
        histories = await fortune_service.get_fortune_history(
            db, 
            request.user_uuid, 
            request.fortune_type if request.fortune_type != "all" else None, 
            request.limit + offset
        )
        
        # 날짜 필터링 (클라이언트 사이드)
        if request.date_from or request.date_to:
            filtered_histories = []
            for history in histories:
                created_date = datetime.fromisoformat(history["created_at"]).date()
                
                # 날짜 범위 체크
                if request.date_from:
                    from_date = datetime.strptime(request.date_from, "%Y-%m-%d").date()
                    if created_date < from_date:
                        continue
                
                if request.date_to:
                    to_date = datetime.strptime(request.date_to, "%Y-%m-%d").date()
                    if created_date > to_date:
                        continue
                
                filtered_histories.append(history)
            
            histories = filtered_histories
        
        # 페이지네이션 적용
        total_count = len(histories)
        paginated_histories = histories[offset:offset + request.limit]
        
        return {
            "success": True,
            "data": {
                "histories": paginated_histories,
                "pagination": {
                    "page": request.page,
                    "limit": request.limit,
                    "total": total_count,
                    "pages": (total_count + request.limit - 1) // request.limit
                },
                "filters": {
                    "fortune_type": request.fortune_type,
                    "date_from": request.date_from,
                    "date_to": request.date_to
                }
            },
            "metadata": {
                "request_id": f"history_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "method": "POST"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_fortune_history_query: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/stats/{user_uuid}",
           summary="운세 통계 조회",
           description="사용자의 운세 이용 통계를 조회합니다.")
async def get_fortune_stats(
    user_uuid: str,
    period_days: int = Query(30, ge=1, le=365, description="통계 기간 (일)"),
    db: Session = Depends(get_db)
):
    """운세 통계 조회"""
    try:
        # 전체 히스토리 조회
        all_histories = await fortune_service.get_fortune_history(db, user_uuid, None, 1000)
        
        # 기간 필터링
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_histories = [
            h for h in all_histories 
            if datetime.fromisoformat(h["created_at"]) > cutoff_date
        ]
        
        # 통계 계산
        total_fortunes = len(recent_histories)
        type_counts = {}
        average_scores = {}
        
        for history in recent_histories:
            fortune_type = history["fortune_type"]
            type_counts[fortune_type] = type_counts.get(fortune_type, 0) + 1
            
            # 점수 평균 계산 (일일 운세만)
            if fortune_type == "daily" and "overall_fortune" in history["result"]:
                score = history["result"]["overall_fortune"].get("score", 0)
                if fortune_type not in average_scores:
                    average_scores[fortune_type] = []
                average_scores[fortune_type].append(score)
        
        # 평균 점수 계산
        for fortune_type in average_scores:
            scores = average_scores[fortune_type]
            average_scores[fortune_type] = sum(scores) / len(scores) if scores else 0
        
        return {
            "success": True,
            "data": {
                "period_days": period_days,
                "total_fortunes": total_fortunes,
                "fortune_types": type_counts,
                "average_scores": average_scores,
                "most_used_type": max(type_counts, key=type_counts.get) if type_counts else None,
                "recent_activity": len([h for h in recent_histories if 
                                     datetime.fromisoformat(h["created_at"]) > 
                                     datetime.now() - timedelta(days=7)])
            },
            "metadata": {
                "request_id": f"stats_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "user_uuid": user_uuid
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_fortune_stats: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


# New Engine-based Endpoints

@router.post("/v2/daily",
            summary="일일 운세 생성 (v2)",
            description="새로운 운세 엔진을 사용한 일일 운세 생성")
async def create_daily_fortune_v2(
    request: DailyFortuneRequest,
    db: Session = Depends(get_db)
):
    """새로운 엔진 기반 일일 운세 생성"""
    try:
        # 개인화 컨텍스트 생성
        context = PersonalizationContext()
        
        if request.birth_date:
            context.birth_date = datetime.strptime(request.birth_date, "%Y-%m-%d").date()
        if request.zodiac:
            context.zodiac_sign = request.zodiac
        
        # 일일 운세 엔진 사용
        engine = FortuneEngineFactory.create_engine(EngineFortuneType.DAILY)
        fortune_result = await engine.generate_fortune(context)
        
        # 결과를 딕셔너리로 변환
        result_dict = {
            "fortune_type": fortune_result.fortune_type.value,
            "date": fortune_result.date.isoformat(),
            "overall_fortune": {
                "score": fortune_result.overall_fortune.score,
                "grade": fortune_result.overall_fortune.grade,
                "description": fortune_result.overall_fortune.description
            },
            "categories": {
                name: {
                    "score": category.score,
                    "grade": category.grade,
                    "description": category.description
                } for name, category in fortune_result.categories.items()
            },
            "lucky_elements": {
                "colors": fortune_result.lucky_elements.colors,
                "numbers": fortune_result.lucky_elements.numbers,
                "items": fortune_result.lucky_elements.items
            },
            "advice": fortune_result.advice,
            "warnings": fortune_result.warnings,
            "live2d_emotion": fortune_result.live2d_emotion,
            "live2d_motion": fortune_result.live2d_motion
        }
        
        # 데이터베이스에 저장
        if request.user_uuid:
            await fortune_service.save_fortune_result(
                db, request.user_uuid, "daily", result_dict
            )
        
        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "request_id": f"daily_v2_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "engine_version": "2.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_daily_fortune_v2: {e}")
        raise HTTPException(status_code=500, detail=f"일일 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/v2/tarot",
            summary="타로 운세 생성 (v2)",
            description="새로운 운세 엔진을 사용한 타로 운세 생성")
async def create_tarot_fortune_v2(
    request: TarotReadingRequest,
    user_uuid: Optional[str] = Query(None, description="사용자 UUID"),
    db: Session = Depends(get_db)
):
    """새로운 엔진 기반 타로 운세 생성"""
    try:
        # 개인화 컨텍스트 생성
        context = PersonalizationContext()
        
        # 타로 운세 엔진 사용
        engine = FortuneEngineFactory.create_engine(EngineFortuneType.TAROT)
        additional_params = {
            "question": request.question,
            "question_type": request.question_type.value if request.question_type else "general"
        }
        
        fortune_result = await engine.generate_fortune(
            context, 
            additional_params=additional_params
        )
        
        # 결과를 딕셔너리로 변환
        result_dict = {
            "fortune_type": fortune_result.fortune_type.value,
            "date": fortune_result.date.isoformat(),
            "question": fortune_result.question,
            "question_type": fortune_result.question_type,
            "overall_fortune": {
                "score": fortune_result.overall_fortune.score,
                "grade": fortune_result.overall_fortune.grade,
                "description": fortune_result.overall_fortune.description
            },
            "tarot_cards": [
                {
                    "position": card.position,
                    "card_name": card.card_name,
                    "card_meaning": card.card_meaning,
                    "interpretation": card.interpretation,
                    "is_reversed": card.is_reversed,
                    "keywords": card.keywords,
                    "image_url": card.image_url
                } for card in fortune_result.tarot_cards
            ],
            "advice": fortune_result.advice,
            "live2d_emotion": fortune_result.live2d_emotion,
            "live2d_motion": fortune_result.live2d_motion
        }
        
        # 데이터베이스에 저장
        if user_uuid:
            await fortune_service.save_fortune_result(
                db, user_uuid, "tarot", result_dict
            )
        
        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "request_id": f"tarot_v2_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "engine_version": "2.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_tarot_fortune_v2: {e}")
        raise HTTPException(status_code=500, detail=f"타로 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/v2/zodiac",
            summary="별자리 운세 생성 (v2)",
            description="새로운 운세 엔진을 사용한 별자리 운세 생성")
async def create_zodiac_fortune_v2(
    zodiac_sign: ZodiacSign,
    request: ZodiacFortuneRequest,
    db: Session = Depends(get_db)
):
    """새로운 엔진 기반 별자리 운세 생성"""
    try:
        # 개인화 컨텍스트 생성
        context = PersonalizationContext()
        context.zodiac_sign = zodiac_sign
        
        # 별자리 운세 엔진 사용
        engine = FortuneEngineFactory.create_engine(EngineFortuneType.ZODIAC)
        additional_params = {"period": request.period}
        
        fortune_result = await engine.generate_fortune(
            context,
            additional_params=additional_params
        )
        
        # 결과를 딕셔너리로 변환
        result_dict = {
            "fortune_type": fortune_result.fortune_type.value,
            "date": fortune_result.date.isoformat(),
            "zodiac_sign": zodiac_sign.value,
            "period": request.period,
            "overall_fortune": {
                "score": fortune_result.overall_fortune.score,
                "grade": fortune_result.overall_fortune.grade,
                "description": fortune_result.overall_fortune.description
            },
            "categories": {
                name: {
                    "score": category.score,
                    "grade": category.grade,
                    "description": category.description
                } for name, category in fortune_result.categories.items()
            },
            "zodiac_info": fortune_result.zodiac_info,
            "lucky_elements": {
                "colors": fortune_result.lucky_elements.colors,
                "numbers": fortune_result.lucky_elements.numbers,
                "items": fortune_result.lucky_elements.items
            },
            "advice": fortune_result.advice,
            "live2d_emotion": fortune_result.live2d_emotion,
            "live2d_motion": fortune_result.live2d_motion
        }
        
        # 데이터베이스에 저장
        if request.user_uuid:
            await fortune_service.save_fortune_result(
                db, request.user_uuid, "zodiac", result_dict
            )
        
        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "request_id": f"zodiac_v2_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "engine_version": "2.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_zodiac_fortune_v2: {e}")
        raise HTTPException(status_code=500, detail=f"별자리 운세 생성 중 오류가 발생했습니다: {str(e)}")


@router.post("/v2/saju",
            summary="사주 운세 생성 (v2)",
            description="새로운 운세 엔진을 사용한 사주 운세 생성")
async def create_saju_fortune_v2(
    request: OrientalFortuneRequest,
    db: Session = Depends(get_db)
):
    """새로운 엔진 기반 사주 운세 생성"""
    try:
        # 개인화 컨텍스트 생성
        context = PersonalizationContext()
        context.birth_date = datetime.strptime(request.birth_date, "%Y-%m-%d").date()
        context.birth_time = request.birth_time
        
        # 사주 운세 엔진 사용
        engine = FortuneEngineFactory.create_engine(EngineFortuneType.ORIENTAL)
        additional_params = {
            "birth_time": request.birth_time,
            "birth_location": request.birth_location
        }
        
        fortune_result = await engine.generate_fortune(
            context,
            additional_params=additional_params
        )
        
        # 결과를 딕셔너리로 변환
        result_dict = {
            "fortune_type": fortune_result.fortune_type.value,
            "date": fortune_result.date.isoformat(),
            "birth_date": request.birth_date,
            "birth_time": request.birth_time,
            "overall_fortune": {
                "score": fortune_result.overall_fortune.score,
                "grade": fortune_result.overall_fortune.grade,
                "description": fortune_result.overall_fortune.description
            },
            "categories": {
                name: {
                    "score": category.score,
                    "grade": category.grade,
                    "description": category.description
                } for name, category in fortune_result.categories.items()
            },
            "saju_elements": [
                {
                    "pillar": element.pillar,
                    "heavenly_stem": element.heavenly_stem,
                    "earthly_branch": element.earthly_branch,
                    "element": element.element,
                    "meaning": element.meaning
                } for element in fortune_result.saju_elements
            ],
            "element_balance": fortune_result.element_balance,
            "advice": fortune_result.advice,
            "live2d_emotion": fortune_result.live2d_emotion,
            "live2d_motion": fortune_result.live2d_motion
        }
        
        # 데이터베이스에 저장
        if request.user_uuid:
            await fortune_service.save_fortune_result(
                db, request.user_uuid, "saju", result_dict
            )
        
        return {
            "success": True,
            "data": result_dict,
            "metadata": {
                "request_id": f"saju_v2_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "engine_version": "2.0"
            }
        }
        
    except Exception as e:
        logger.error(f"Error in create_saju_fortune_v2: {e}")
        raise HTTPException(status_code=500, detail=f"사주 운세 생성 중 오류가 발생했습니다: {str(e)}")


# Health check endpoint for fortune service
@router.get("/health",
           summary="운세 서비스 상태 확인",
           description="운세 서비스의 상태를 확인합니다.")
async def fortune_health_check():
    """운세 서비스 헬스 체크"""
    try:
        # Test each engine individually to identify issues
        engine_status = {}
        test_engines = [EngineFortuneType.DAILY, EngineFortuneType.TAROT, EngineFortuneType.ZODIAC, EngineFortuneType.ORIENTAL]
        
        for engine_type in test_engines:
            try:
                engine = FortuneEngineFactory.create_engine(engine_type)
                engine_status[engine_type.value] = "operational"
            except Exception as e:
                engine_status[engine_type.value] = f"error: {str(e)}"
        
        try:
            available_types = FortuneEngineFactory.get_available_types()
            available_type_values = [t.value for t in available_types]
        except Exception as e:
            available_type_values = ["daily", "tarot", "zodiac", "oriental"]
            engine_status["factory_error"] = str(e)
        
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "fortune_service",
                "engine_status": engine_status,
                "available_types": available_type_values,
                "engine_version": "2.0"
            },
            "metadata": {
                "request_id": f"health_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Fortune service health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "SERVICE_UNHEALTHY",
                    "message": "운세 서비스가 정상적으로 작동하지 않습니다",
                    "details": str(e)
                }
            }
        )
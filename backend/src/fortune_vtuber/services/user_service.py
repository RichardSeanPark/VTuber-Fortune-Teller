"""
User Service - 사용자 관리 서비스

프로필 관리, 세션 추적, 운세 히스토리 관리
익명 사용자 지원 및 개인화 설정
"""

import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.user import User, UserSession, UserPreferences
from ..models.fortune import FortuneSession, ZodiacSign
from ..models.chat import ChatSession
from ..models.live2d import Live2DSessionModel
from .cache_service import CacheService

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관리 서비스"""
    
    def __init__(self, database_service=None, cache_service: CacheService = None):
        self.database_service = database_service
        self.cache_service = cache_service or CacheService()
        self._initialized = False
    
    async def initialize(self):
        """Initialize user service"""
        if self._initialized:
            return
        self._initialized = True
        logger.info("UserService initialized")
    
    async def shutdown(self):
        """Shutdown user service"""
        self._initialized = False
        logger.info("UserService shutdown")
    
    async def create_or_get_user(self, db: Session, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 생성 또는 조회"""
        try:
            name = user_data.get("name", "익명 사용자")
            birth_date = user_data.get("birth_date")
            birth_time = user_data.get("birth_time")
            birth_location = user_data.get("birth_location")
            zodiac_sign = user_data.get("zodiac_sign")
            
            # 기존 사용자 찾기 (이름 + 생년월일 조합)
            existing_user = None
            if birth_date and name != "익명 사용자":
                existing_user = db.query(User).filter(
                    and_(
                        User.name == name,
                        User.birth_date == birth_date
                    )
                ).first()
            
            if existing_user:
                # 기존 사용자 정보 업데이트
                if birth_time and not existing_user.birth_time:
                    existing_user.birth_time = birth_time
                if birth_location and not existing_user.birth_location:
                    existing_user.birth_location = birth_location
                if zodiac_sign and not existing_user.zodiac_sign:
                    existing_user.zodiac_sign = zodiac_sign
                
                existing_user.last_access = datetime.now()
                existing_user.access_count += 1
                
                db.commit()
                
                return await self._format_user_response(existing_user)
            
            # 새 사용자 생성
            new_user = User(
                name=name,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_location=birth_location,
                zodiac_sign=zodiac_sign,
                last_access=datetime.now(),
                access_count=1,
                is_anonymous=name == "익명 사용자"
            )
            
            db.add(new_user)
            db.commit()
            
            # 기본 선호도 설정 생성
            await self._create_default_preferences(db, new_user.uuid)
            
            logger.info(f"User created: {new_user.uuid} ({'anonymous' if new_user.is_anonymous else 'named'})")
            
            return await self._format_user_response(new_user)
            
        except Exception as e:
            logger.error(f"Error creating/getting user: {e}")
            db.rollback()
            raise
    
    async def update_user_profile(self, db: Session, user_uuid: str, 
                                update_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 프로필 업데이트"""
        try:
            user = User.find_by_uuid(db, user_uuid)
            if not user:
                raise ValueError(f"User not found: {user_uuid}")
            
            # 업데이트 가능한 필드들
            updatable_fields = {
                "name", "birth_date", "birth_time", "birth_location", "zodiac_sign"
            }
            
            updated = False
            for field, value in update_data.items():
                if field in updatable_fields and value is not None:
                    # 익명 사용자가 이름을 설정하면 named 사용자로 변경
                    if field == "name" and user.is_anonymous and value != "익명 사용자":
                        user.is_anonymous = False
                    
                    setattr(user, field, value)
                    updated = True
            
            if updated:
                user.updated_at = datetime.now()
                db.commit()
                
                logger.info(f"User profile updated: {user_uuid}")
            
            return await self._format_user_response(user)
            
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            db.rollback()
            raise
    
    async def get_user_profile(self, db: Session, user_uuid: str) -> Dict[str, Any]:
        """사용자 프로필 조회"""
        try:
            user = User.find_by_uuid(db, user_uuid)
            if not user:
                raise ValueError(f"User not found: {user_uuid}")
            
            return await self._format_user_response(user)
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise
    
    async def create_user_session(self, db: Session, user_uuid: str,
                                session_type: str = "web",
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """사용자 세션 생성"""
        try:
            # 사용자 존재 확인
            user = User.find_by_uuid(db, user_uuid)
            if not user:
                raise ValueError(f"User not found: {user_uuid}")
            
            # 기존 활성 세션 확인
            active_session = UserSession.find_active_session(db, user_uuid, session_type)
            
            if active_session:
                # 기존 세션 연장
                active_session.expires_at = datetime.now() + timedelta(hours=24)
                active_session.last_activity = datetime.now()
                
                if metadata:
                    current_metadata = active_session.metadata_dict
                    current_metadata.update(metadata)
                    active_session.metadata_dict = current_metadata
                
                db.commit()
                
                return self._format_session_response(active_session)
            
            # 새 세션 생성
            session_id = f"{session_type}_{user_uuid}_{int(datetime.now().timestamp())}"
            new_session = UserSession(
                session_id=session_id,
                user_uuid=user_uuid,
                session_type=session_type,
                expires_at=datetime.now() + timedelta(hours=24),
                last_activity=datetime.now(),
                is_active=True
            )
            
            if metadata:
                new_session.metadata_dict = metadata
            
            db.add(new_session)
            
            # 사용자 접근 정보 업데이트
            user.last_access = datetime.now()
            user.access_count += 1
            
            db.commit()
            
            logger.info(f"User session created: {new_session.session_id} for user {user_uuid}")
            
            return self._format_session_response(new_session)
            
        except Exception as e:
            logger.error(f"Error creating user session: {e}")
            db.rollback()
            raise
    
    async def get_user_sessions(self, db: Session, user_uuid: str,
                              active_only: bool = True) -> List[Dict[str, Any]]:
        """사용자 세션 목록 조회"""
        try:
            if active_only:
                sessions = UserSession.find_active_sessions_by_user(db, user_uuid)
            else:
                sessions = UserSession.find_sessions_by_user(db, user_uuid, limit=50)
            
            return [self._format_session_response(session) for session in sessions]
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            raise
    
    async def end_user_session(self, db: Session, session_id: str) -> bool:
        """사용자 세션 종료"""
        try:
            session = UserSession.find_by_session_id(db, session_id)
            if not session:
                return False
            
            session.is_active = False
            session.ended_at = datetime.now()
            
            db.commit()
            
            logger.info(f"User session ended: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ending user session: {e}")
            db.rollback()
            raise
    
    async def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions and return count of cleaned sessions"""
        try:
            expired_sessions = db.query(UserSession).filter(
                and_(
                    UserSession.is_active == True,
                    UserSession.expires_at < datetime.now()
                )
            ).all()
            
            count = len(expired_sessions)
            
            for session in expired_sessions:
                session.is_active = False
                session.ended_at = datetime.now()
            
            db.commit()
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            db.rollback()
            raise
    
    async def extend_session(self, db: Session, session_id: str, 
                           extension_hours: int = 24) -> bool:
        """Extend session expiration time"""
        try:
            session = UserSession.find_by_session_id(db, session_id)
            if not session or not session.is_active:
                return False
            
            session.expires_at = datetime.now() + timedelta(hours=extension_hours)
            session.last_active_at = datetime.now()
            
            db.commit()
            
            logger.info(f"Session extended: {session_id} for {extension_hours} hours")
            return True
            
        except Exception as e:
            logger.error(f"Error extending session: {e}")
            db.rollback()
            raise
    
    async def get_user_preferences(self, db: Session, user_uuid: str) -> Dict[str, Any]:
        """사용자 선호도 조회"""
        try:
            preferences = UserPreferences.find_by_user_uuid(db, user_uuid)
            
            if not preferences:
                # 기본 선호도 생성
                preferences = await self._create_default_preferences(db, user_uuid)
            
            return {
                "user_uuid": preferences.user_uuid,
                "fortune_types": preferences.fortune_types_list,
                "notification_time": preferences.notification_time,
                "theme": preferences.theme,
                "language": preferences.language,
                "timezone": preferences.timezone,
                "privacy_settings": preferences.privacy_settings_dict,
                "created_at": preferences.created_at.isoformat(),
                "updated_at": preferences.updated_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            raise
    
    async def update_user_preferences(self, db: Session, user_uuid: str,
                                    preferences_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 선호도 업데이트"""
        try:
            preferences = UserPreferences.find_by_user_uuid(db, user_uuid)
            
            if not preferences:
                preferences = await self._create_default_preferences(db, user_uuid)
            
            # 업데이트 가능한 필드들
            if "fortune_types" in preferences_data:
                preferences.fortune_types_list = preferences_data["fortune_types"]
            
            if "notification_time" in preferences_data:
                preferences.notification_time = preferences_data["notification_time"]
            
            if "theme" in preferences_data:
                preferences.theme = preferences_data["theme"]
            
            if "language" in preferences_data:
                preferences.language = preferences_data["language"]
            
            if "timezone" in preferences_data:
                preferences.timezone = preferences_data["timezone"]
            
            if "privacy_settings" in preferences_data:
                current_privacy = preferences.privacy_settings_dict
                current_privacy.update(preferences_data["privacy_settings"])
                preferences.privacy_settings_dict = current_privacy
            
            preferences.updated_at = datetime.now()
            db.commit()
            
            logger.info(f"User preferences updated: {user_uuid}")
            
            return await self.get_user_preferences(db, user_uuid)
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            db.rollback()
            raise
    
    async def get_user_fortune_history(self, db: Session, user_uuid: str,
                                     fortune_type: Optional[str] = None,
                                     limit: int = 50,
                                     days: Optional[int] = None) -> Dict[str, Any]:
        """사용자 운세 히스토리 조회"""
        try:
            query = db.query(FortuneSession).filter(
                FortuneSession.user_uuid == user_uuid
            )
            
            if fortune_type and fortune_type != "all":
                query = query.filter(FortuneSession.fortune_type == fortune_type)
            
            if days:
                cutoff_date = datetime.now() - timedelta(days=days)
                query = query.filter(FortuneSession.created_at >= cutoff_date)
            
            fortunes = query.order_by(FortuneSession.created_at.desc()).limit(limit).all()
            
            # 운세 타입별 통계
            type_stats = db.query(
                FortuneSession.fortune_type,
                func.count(FortuneSession.id).label('count')
            ).filter(
                FortuneSession.user_uuid == user_uuid
            ).group_by(FortuneSession.fortune_type).all()
            
            return {
                "user_uuid": user_uuid,
                "fortunes": [
                    {
                        "fortune_id": fortune.fortune_id,
                        "fortune_type": fortune.fortune_type,
                        "question": fortune.question,
                        "question_type": fortune.question_type,
                        "result": fortune.result_dict,
                        "created_at": fortune.created_at.isoformat(),
                        "is_cached": fortune.is_cached
                    }
                    for fortune in fortunes
                ],
                "statistics": {
                    "total_fortunes": len(fortunes),
                    "type_breakdown": {stat.fortune_type: stat.count for stat in type_stats},
                    "date_range": {
                        "from": fortunes[-1].created_at.isoformat() if fortunes else None,
                        "to": fortunes[0].created_at.isoformat() if fortunes else None
                    }
                },
                "filters": {
                    "fortune_type": fortune_type,
                    "days": days,
                    "limit": limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user fortune history: {e}")
            raise
    
    async def get_user_activity_summary(self, db: Session, user_uuid: str,
                                      days: int = 30) -> Dict[str, Any]:
        """사용자 활동 요약"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 운세 활동
            fortune_count = db.query(FortuneSession).filter(
                and_(
                    FortuneSession.user_uuid == user_uuid,
                    FortuneSession.created_at >= cutoff_date
                )
            ).count()
            
            # 채팅 활동
            chat_sessions = db.query(ChatSession).filter(
                and_(
                    ChatSession.user_uuid == user_uuid,
                    ChatSession.created_at >= cutoff_date
                )
            ).count()
            
            # Live2D 상호작용
            live2d_sessions = db.query(Live2DSession).filter(
                and_(
                    Live2DSession.user_uuid == user_uuid,
                    Live2DSession.created_at >= cutoff_date
                )
            ).count()
            
            # 사용자 세션
            user_sessions = db.query(UserSession).filter(
                and_(
                    UserSession.user_uuid == user_uuid,
                    UserSession.created_at >= cutoff_date
                )
            ).count()
            
            # 일별 활동 패턴
            daily_activity = db.query(
                func.date(FortuneSession.created_at).label('date'),
                func.count(FortuneSession.id).label('count')
            ).filter(
                and_(
                    FortuneSession.user_uuid == user_uuid,
                    FortuneSession.created_at >= cutoff_date
                )
            ).group_by(func.date(FortuneSession.created_at)).all()
            
            # 선호 운세 타입
            preferred_types = db.query(
                FortuneSession.fortune_type,
                func.count(FortuneSession.id).label('count')
            ).filter(
                and_(
                    FortuneSession.user_uuid == user_uuid,
                    FortuneSession.created_at >= cutoff_date
                )
            ).group_by(FortuneSession.fortune_type).order_by(
                func.count(FortuneSession.id).desc()
            ).limit(3).all()
            
            return {
                "user_uuid": user_uuid,
                "period_days": days,
                "summary": {
                    "fortune_requests": fortune_count,
                    "chat_sessions": chat_sessions,
                    "live2d_interactions": live2d_sessions,
                    "user_sessions": user_sessions
                },
                "daily_activity": [
                    {
                        "date": activity.date.isoformat(),
                        "fortune_count": activity.count
                    }
                    for activity in daily_activity
                ],
                "preferred_fortune_types": [
                    {
                        "type": pref.fortune_type,
                        "count": pref.count
                    }
                    for pref in preferred_types
                ],
                "activity_score": min(100, (fortune_count + chat_sessions) * 2)  # 0-100 점수
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            raise
    
    async def search_users(self, db: Session, query: str, 
                         limit: int = 20) -> List[Dict[str, Any]]:
        """사용자 검색 (관리자용)"""
        try:
            # 이름 또는 UUID로 검색
            search_filter = or_(
                User.name.ilike(f"%{query}%"),
                User.uuid.ilike(f"%{query}%")
            )
            
            users = db.query(User).filter(search_filter).limit(limit).all()
            
            return [await self._format_user_response(user) for user in users]
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            raise
    
    async def cleanup_expired_sessions(self, db: Session) -> int:
        """만료된 세션 정리"""
        try:
            expired_sessions = UserSession.find_expired_sessions(db)
            count = len(expired_sessions)
            
            for session in expired_sessions:
                session.is_active = False
                if not session.ended_at:
                    session.ended_at = datetime.now()
            
            if expired_sessions:
                db.commit()
                logger.info(f"Cleaned up {count} expired user sessions")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            db.rollback()
            raise
    
    async def get_user_statistics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """전체 사용자 통계"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 전체 사용자 수
            total_users = db.query(User).count()
            anonymous_users = db.query(User).filter(User.is_anonymous == True).count()
            named_users = total_users - anonymous_users
            
            # 활성 사용자 (기간 내 접근)
            active_users = db.query(User).filter(
                User.last_access >= cutoff_date
            ).count()
            
            # 신규 사용자
            new_users = db.query(User).filter(
                User.created_at >= cutoff_date
            ).count()
            
            # 세션 통계
            total_sessions = db.query(UserSession).filter(
                UserSession.created_at >= cutoff_date
            ).count()
            
            active_sessions = db.query(UserSession).filter(
                UserSession.is_active == True
            ).count()
            
            # 운세 요청 통계
            fortune_requests = db.query(FortuneSession).filter(
                FortuneSession.created_at >= cutoff_date
            ).count()
            
            # 일별 신규 사용자
            daily_new_users = db.query(
                func.date(User.created_at).label('date'),
                func.count(User.id).label('count')
            ).filter(
                User.created_at >= cutoff_date
            ).group_by(func.date(User.created_at)).all()
            
            return {
                "period_days": days,
                "user_counts": {
                    "total_users": total_users,
                    "named_users": named_users,
                    "anonymous_users": anonymous_users,
                    "active_users": active_users,
                    "new_users": new_users
                },
                "session_counts": {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions
                },
                "activity_counts": {
                    "fortune_requests": fortune_requests
                },
                "daily_new_users": [
                    {
                        "date": item.date.isoformat(),
                        "count": item.count
                    }
                    for item in daily_new_users
                ],
                "user_engagement": {
                    "active_ratio": active_users / total_users if total_users > 0 else 0,
                    "avg_fortune_requests": fortune_requests / active_users if active_users > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            raise
    
    # Private methods
    async def _create_default_preferences(self, db: Session, user_uuid: str) -> UserPreferences:
        """기본 선호도 설정 생성"""
        try:
            preferences = UserPreferences(
                user_uuid=user_uuid,
                fortune_types_list=["daily", "tarot"],
                notification_time="09:00",
                theme="light",
                language="ko",
                timezone="Asia/Seoul",
                privacy_settings_dict={
                    "save_history": True,
                    "personalization": True,
                    "analytics": False
                }
            )
            
            db.add(preferences)
            db.commit()
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error creating default preferences: {e}")
            db.rollback()
            raise
    
    async def _format_user_response(self, user: User) -> Dict[str, Any]:
        """사용자 응답 포맷"""
        return {
            "uuid": user.uuid,
            "name": user.name,
            "birth_date": user.birth_date,
            "birth_time": user.birth_time,
            "birth_location": user.birth_location,
            "zodiac_sign": user.zodiac_sign,
            "is_anonymous": user.is_anonymous,
            "last_access": user.last_access.isoformat() if user.last_access else None,
            "access_count": user.access_count,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    
    def _format_session_response(self, session: UserSession) -> Dict[str, Any]:
        """세션 응답 포맷"""
        return {
            "session_id": session.session_id,
            "user_uuid": session.user_uuid,
            "session_type": session.session_type,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "metadata": session.metadata_dict
        }
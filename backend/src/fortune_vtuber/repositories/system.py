"""
System configuration and analytics repositories
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from .base import BaseRepository, RepositoryError
from ..models.system import SystemSetting, UserAnalytics


class SystemSettingRepository(BaseRepository[SystemSetting]):
    """Repository for SystemSetting"""
    
    def __init__(self, session: Session):
        super().__init__(SystemSetting, session)
    
    async def get_setting(self, key: str, default: Any = None) -> Any:
        """Get setting value by key"""
        try:
            result = await self.session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == key)
            )
            setting = result.scalar_one_or_none()
            return setting.typed_value if setting else default
        except Exception as e:
            raise RepositoryError(f"Failed to get setting: {e}")
    
    async def set_setting(self, key: str, value: Any, 
                         description: str = None, is_public: bool = False) -> SystemSetting:
        """Set setting value"""
        try:
            result = await self.session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                setting.typed_value = value
                if description is not None:
                    setting.description = description
                setting.is_public = is_public
            else:
                setting = SystemSetting(
                    setting_key=key,
                    description=description,
                    is_public=is_public
                )
                setting.typed_value = value
                self.session.add(setting)
            
            await self.session.flush()
            self._clear_cache()
            
            return setting
        except Exception as e:
            raise RepositoryError(f"Failed to set setting: {e}")
    
    async def get_public_settings(self) -> Dict[str, Any]:
        """Get all public settings"""
        try:
            result = await self.session.execute(
                select(SystemSetting).where(SystemSetting.is_public == True)
            )
            settings = result.scalars().all()
            return {setting.setting_key: setting.typed_value for setting in settings}
        except Exception as e:
            raise RepositoryError(f"Failed to get public settings: {e}")
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings (admin only)"""
        try:
            result = await self.session.execute(select(SystemSetting))
            settings = result.scalars().all()
            return {setting.setting_key: setting.typed_value for setting in settings}
        except Exception as e:
            raise RepositoryError(f"Failed to get all settings: {e}")
    
    async def bulk_update_settings(self, settings_dict: Dict[str, Any]):
        """Bulk update multiple settings"""
        try:
            for key, value in settings_dict.items():
                await self.set_setting(key, value)
            await self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to bulk update settings: {e}")
    
    async def delete_setting(self, key: str) -> bool:
        """Delete setting by key"""
        try:
            result = await self.session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                await self.session.delete(setting)
                await self.session.flush()
                self._clear_cache()
                return True
            return False
        except Exception as e:
            raise RepositoryError(f"Failed to delete setting: {e}")


class UserAnalyticsRepository(BaseRepository[UserAnalytics]):
    """Repository for UserAnalytics"""
    
    def __init__(self, session: Session):
        super().__init__(UserAnalytics, session)
    
    async def log_event(self, event_type: str, 
                       user_uuid: str = None, session_id: str = None,
                       event_data: Dict[str, Any] = None, 
                       ip_address: str = None, user_agent: str = None) -> UserAnalytics:
        """Log analytics event"""
        try:
            event = UserAnalytics(
                user_uuid=user_uuid,
                session_id=session_id,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            if event_data:
                event.event_data_dict = event_data
            
            self.session.add(event)
            await self.session.flush()
            
            return event
        except Exception as e:
            raise RepositoryError(f"Failed to log event: {e}")
    
    async def get_user_events(self, user_uuid: str, 
                             event_type: str = None, limit: int = 100) -> List[UserAnalytics]:
        """Get user events"""
        try:
            query = select(UserAnalytics).where(UserAnalytics.user_uuid == user_uuid)
            
            if event_type:
                query = query.where(UserAnalytics.event_type == event_type)
            
            result = await self.session.execute(
                query.order_by(UserAnalytics.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to get user events: {e}")
    
    async def get_session_events(self, session_id: str) -> List[UserAnalytics]:
        """Get session events"""
        try:
            result = await self.session.execute(
                select(UserAnalytics)
                .where(UserAnalytics.session_id == session_id)
                .order_by(UserAnalytics.created_at.asc())
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to get session events: {e}")
    
    async def get_event_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get event statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Total events by type
            event_counts = await self.session.execute(
                select(
                    UserAnalytics.event_type,
                    func.count(UserAnalytics.id).label('count')
                ).where(
                    UserAnalytics.created_at >= cutoff_date
                ).group_by(UserAnalytics.event_type)
            )
            
            # Daily event counts
            daily_counts = await self.session.execute(
                select(
                    func.date(UserAnalytics.created_at).label('date'),
                    func.count(UserAnalytics.id).label('count')
                ).where(
                    UserAnalytics.created_at >= cutoff_date
                ).group_by(func.date(UserAnalytics.created_at))
            )
            
            # Unique users
            unique_users = await self.session.execute(
                select(func.count(func.distinct(UserAnalytics.user_uuid))).where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.user_uuid.isnot(None)
                    )
                )
            )
            
            # Unique sessions
            unique_sessions = await self.session.execute(
                select(func.count(func.distinct(UserAnalytics.session_id))).where(
                    and_(
                        UserAnalytics.created_at >= cutoff_date,
                        UserAnalytics.session_id.isnot(None)
                    )
                )
            )
            
            return {
                'period_days': days,
                'total_events': sum(count.count for count in event_counts.all()),
                'unique_users': unique_users.scalar() or 0,
                'unique_sessions': unique_sessions.scalar() or 0,
                'events_by_type': {
                    count.event_type: count.count 
                    for count in event_counts.all()
                },
                'daily_events': {
                    str(count.date): count.count 
                    for count in daily_counts.all()
                }
            }
        except Exception as e:
            raise RepositoryError(f"Failed to get event statistics: {e}")
    
    async def cleanup_old_events(self, days: int = 90) -> int:
        """Clean up old analytics events"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_events = await self.session.execute(
                select(UserAnalytics).where(
                    UserAnalytics.created_at < cutoff_date
                )
            )
            
            count = 0
            for event in old_events.scalars():
                await self.session.delete(event)
                count += 1
            
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup old events: {e}")
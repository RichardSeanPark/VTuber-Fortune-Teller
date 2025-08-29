"""
User repository with specialized user operations
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import Session

from .base import BaseRepository, RepositoryError
from ..models.user import User


class UserRepository(BaseRepository[User]):
    """Repository for User model with specialized operations"""
    
    def __init__(self, session: Session):
        super().__init__(User, session)
    
    async def find_by_uuid(self, uuid: str, include_deleted: bool = False) -> Optional[User]:
        """Find user by UUID with optional inclusion of deleted users"""
        try:
            query = select(User).where(User.uuid == uuid)
            
            if not include_deleted:
                query = query.where(User.is_deleted == False)
            
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            raise RepositoryError(f"Failed to find user by UUID: {e}")
    
    async def find_by_name(self, name: str, exact_match: bool = True) -> List[User]:
        """Find users by name (exact or partial match)"""
        try:
            query = select(User).where(User.is_deleted == False)
            
            if exact_match:
                query = query.where(User.name == name)
            else:
                query = query.where(User.name.ilike(f"%{name}%"))
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise RepositoryError(f"Failed to find users by name: {e}")
    
    async def find_by_zodiac_sign(self, zodiac_sign: str, 
                                 limit: int = 100, offset: int = 0) -> List[User]:
        """Find users by zodiac sign"""
        try:
            query = select(User).where(
                and_(
                    User.zodiac_sign == zodiac_sign.lower(),
                    User.is_deleted == False
                )
            ).order_by(User.created_at.desc()).limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise RepositoryError(f"Failed to find users by zodiac sign: {e}")
    
    async def find_active_users(self, limit: int = 100, 
                               since_hours: int = 24) -> List[User]:
        """Find users active within specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=since_hours)
            
            query = select(User).where(
                and_(
                    User.is_active == True,
                    User.is_deleted == False,
                    User.last_active_at >= cutoff_time
                )
            ).order_by(User.last_active_at.desc()).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise RepositoryError(f"Failed to find active users: {e}")
    
    async def find_inactive_users(self, inactive_days: int = 30, 
                                 limit: int = 100) -> List[User]:
        """Find users inactive for specified days"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=inactive_days)
            
            query = select(User).where(
                and_(
                    User.is_deleted == False,
                    or_(
                        User.last_active_at < cutoff_time,
                        User.last_active_at.is_(None)
                    )
                )
            ).order_by(User.last_active_at.asc().nullslast()).limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise RepositoryError(f"Failed to find inactive users: {e}")
    
    async def find_users_by_age_range(self, min_age: int = None, 
                                     max_age: int = None, limit: int = 100) -> List[User]:
        """Find users by age range (requires birth_date)"""
        try:\n            # Calculate date ranges for age filtering\n            today = datetime.utcnow().date()\n            \n            conditions = [User.is_deleted == False, User.birth_date.isnot(None)]\n            \n            if min_age is not None:\n                max_birth_date = today.replace(year=today.year - min_age)\n                conditions.append(User.birth_date <= max_birth_date.strftime(\"%Y-%m-%d\"))\n            \n            if max_age is not None:\n                min_birth_date = today.replace(year=today.year - max_age - 1)\n                conditions.append(User.birth_date > min_birth_date.strftime(\"%Y-%m-%d\"))\n            \n            query = select(User).where(and_(*conditions)).limit(limit)\n            \n            result = await self.session.execute(query)\n            return result.scalars().all()\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to find users by age range: {e}\")\n    \n    async def update_last_active(self, user_uuid: str) -> bool:\n        \"\"\"Update user's last active timestamp\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return False\n            \n            user.last_active_at = datetime.utcnow()\n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            return True\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to update last active: {e}\")\n    \n    async def update_preferences(self, user_uuid: str, \n                                preferences: Dict[str, Any]) -> Optional[User]:\n        \"\"\"Update user preferences\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return None\n            \n            # Merge with existing preferences\n            current_prefs = user.preferences_dict\n            current_prefs.update(preferences)\n            user.preferences_dict = current_prefs\n            \n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            return user\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to update user preferences: {e}\")\n    \n    async def set_fortune_preference(self, user_uuid: str, \n                                    key: str, value: Any) -> Optional[User]:\n        \"\"\"Set specific fortune preference\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return None\n            \n            prefs = user.preferences_dict\n            if 'fortune' not in prefs:\n                prefs['fortune'] = {}\n            \n            prefs['fortune'][key] = value\n            user.preferences_dict = prefs\n            \n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            return user\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to set fortune preference: {e}\")\n    \n    async def get_fortune_preference(self, user_uuid: str, \n                                    key: str, default: Any = None) -> Any:\n        \"\"\"Get specific fortune preference\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return default\n            \n            return user.get_fortune_preference(key, default)\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to get fortune preference: {e}\")\n    \n    async def deactivate_user(self, user_uuid: str, reason: str = None) -> bool:\n        \"\"\"Deactivate user account\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return False\n            \n            user.is_active = False\n            \n            # Add deactivation reason to preferences if provided\n            if reason:\n                prefs = user.preferences_dict\n                prefs['deactivation_reason'] = reason\n                prefs['deactivated_at'] = datetime.utcnow().isoformat()\n                user.preferences_dict = prefs\n            \n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            return True\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to deactivate user: {e}\")\n    \n    async def reactivate_user(self, user_uuid: str) -> bool:\n        \"\"\"Reactivate user account\"\"\"\n        try:\n            user = await self.find_by_uuid(user_uuid)\n            if not user:\n                return False\n            \n            user.is_active = True\n            user.last_active_at = datetime.utcnow()\n            \n            # Remove deactivation info from preferences\n            prefs = user.preferences_dict\n            prefs.pop('deactivation_reason', None)\n            prefs.pop('deactivated_at', None)\n            prefs['reactivated_at'] = datetime.utcnow().isoformat()\n            user.preferences_dict = prefs\n            \n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            return True\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to reactivate user: {e}\")\n    \n    async def get_user_statistics(self) -> Dict[str, Any]:\n        \"\"\"Get user statistics\"\"\"\n        try:\n            base_stats = await super().get_statistics()\n            \n            # Count by zodiac signs\n            zodiac_counts = await self.session.execute(\n                select(\n                    User.zodiac_sign,\n                    func.count(User.id).label('count')\n                ).where(\n                    and_(User.is_deleted == False, User.zodiac_sign.isnot(None))\n                ).group_by(User.zodiac_sign)\n            )\n            \n            # Count active users (last 7 days)\n            week_ago = datetime.utcnow() - timedelta(days=7)\n            active_count = await self.session.execute(\n                select(func.count(User.id)).where(\n                    and_(\n                        User.is_deleted == False,\n                        User.is_active == True,\n                        User.last_active_at >= week_ago\n                    )\n                )\n            )\n            \n            # Count users with birth data\n            birth_data_count = await self.session.execute(\n                select(func.count(User.id)).where(\n                    and_(\n                        User.is_deleted == False,\n                        User.birth_date.isnot(None)\n                    )\n                )\n            )\n            \n            base_stats.update({\n                'zodiac_distribution': {\n                    row.zodiac_sign: row.count \n                    for row in zodiac_counts.all()\n                },\n                'active_weekly': active_count.scalar() or 0,\n                'with_birth_data': birth_data_count.scalar() or 0\n            })\n            \n            return base_stats\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to get user statistics: {e}\")\n    \n    async def cleanup_inactive_users(self, inactive_days: int = 365, \n                                    dry_run: bool = True) -> Dict[str, int]:\n        \"\"\"Clean up inactive users (soft delete)\"\"\"\n        try:\n            cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)\n            \n            # Find inactive users\n            query = select(User).where(\n                and_(\n                    User.is_deleted == False,\n                    User.is_active == True,\n                    or_(\n                        User.last_active_at < cutoff_date,\n                        User.last_active_at.is_(None)\n                    )\n                )\n            )\n            \n            result = await self.session.execute(query)\n            inactive_users = result.scalars().all()\n            \n            if not dry_run:\n                # Soft delete inactive users\n                for user in inactive_users:\n                    user.is_deleted = True\n                    user.deleted_at = datetime.utcnow()\n                    \n                    # Add cleanup reason to preferences\n                    prefs = user.preferences_dict\n                    prefs['cleanup_reason'] = f'Inactive for {inactive_days} days'\n                    prefs['cleaned_up_at'] = datetime.utcnow().isoformat()\n                    user.preferences_dict = prefs\n                \n                await self.session.flush()\n                \n                # Clear cache\n                self._clear_cache()\n            \n            return {\n                'found_inactive': len(inactive_users),\n                'cleaned_up': len(inactive_users) if not dry_run else 0,\n                'dry_run': dry_run\n            }\n            \n        except Exception as e:\n            raise RepositoryError(f\"Failed to cleanup inactive users: {e}\")"
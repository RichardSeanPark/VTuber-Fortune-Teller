"""
Chat repositories for sessions and messages
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session, selectinload

from .base import BaseRepository, RepositoryError
from ..models.chat import ChatSession, ChatMessage


class ChatSessionRepository(BaseRepository[ChatSession]):
    """Repository for ChatSession model"""
    
    def __init__(self, session: Session):
        super().__init__(ChatSession, session)
    
    async def find_by_session_id(self, session_id: str) -> Optional[ChatSession]:
        """Find session by session_id"""
        try:
            result = await self.session.execute(
                select(ChatSession).where(ChatSession.session_id == session_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find session by session_id: {e}")
    
    async def find_user_sessions(self, user_uuid: str, limit: int = 10) -> List[ChatSession]:
        """Find user's recent sessions"""
        try:
            result = await self.session.execute(
                select(ChatSession)
                .where(ChatSession.user_uuid == user_uuid)
                .order_by(ChatSession.started_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find user sessions: {e}")
    
    async def find_active_sessions(self, limit: int = 100) -> List[ChatSession]:
        """Find active sessions"""
        try:
            result = await self.session.execute(
                select(ChatSession)
                .where(ChatSession.status == 'active')
                .order_by(ChatSession.started_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find active sessions: {e}")
    
    async def cleanup_expired_sessions(self, hours: int = 24) -> int:
        """Clean up expired sessions"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            expired_sessions = await self.session.execute(
                select(ChatSession).where(
                    and_(
                        ChatSession.status == 'active',
                        ChatSession.expires_at < cutoff_time
                    )
                )
            )
            
            count = 0
            for session in expired_sessions.scalars():
                session.status = 'expired'
                session.ended_at = datetime.utcnow()
                count += 1
            
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup expired sessions: {e}")


class ChatMessageRepository(BaseRepository[ChatMessage]):
    """Repository for ChatMessage model"""
    
    def __init__(self, session: Session):
        super().__init__(ChatMessage, session)
    
    async def find_by_message_id(self, message_id: str) -> Optional[ChatMessage]:
        """Find message by message_id"""
        try:
            result = await self.session.execute(
                select(ChatMessage).where(
                    and_(
                        ChatMessage.message_id == message_id,
                        ChatMessage.is_deleted == False
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find message by message_id: {e}")
    
    async def find_session_messages(self, session_id: str, 
                                   limit: int = 100, include_deleted: bool = False) -> List[ChatMessage]:
        """Find messages for a session"""
        try:
            query = select(ChatMessage).where(ChatMessage.session_id == session_id)
            
            if not include_deleted:
                query = query.where(ChatMessage.is_deleted == False)
            
            result = await self.session.execute(
                query.order_by(ChatMessage.created_at.asc()).limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find session messages: {e}")
    
    async def find_recent_messages(self, session_id: str, count: int = 10) -> List[ChatMessage]:
        """Find recent messages for context"""
        try:
            result = await self.session.execute(
                select(ChatMessage)
                .where(
                    and_(
                        ChatMessage.session_id == session_id,
                        ChatMessage.is_deleted == False
                    )
                )
                .order_by(ChatMessage.created_at.desc())
                .limit(count)
            )
            return list(reversed(result.scalars().all()))  # Return in chronological order
        except Exception as e:
            raise RepositoryError(f"Failed to find recent messages: {e}")
    
    async def cleanup_old_messages(self, days: int = 90) -> int:
        """Clean up old messages (soft delete)"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_messages = await self.session.execute(
                select(ChatMessage).where(
                    and_(
                        ChatMessage.created_at < cutoff_date,
                        ChatMessage.is_deleted == False
                    )
                )
            )
            
            count = 0
            for message in old_messages.scalars():
                message.is_deleted = True
                message.deleted_at = datetime.utcnow()
                count += 1
            
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup old messages: {e}")
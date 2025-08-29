"""
Fortune-related repositories
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from .base import BaseRepository, RepositoryError
from ..models.fortune import FortuneSession, TarotCard, ZodiacInfo


class FortuneSessionRepository(BaseRepository[FortuneSession]):
    """Repository for FortuneSession model"""
    
    def __init__(self, session: Session):
        super().__init__(FortuneSession, session)
    
    async def find_by_fortune_id(self, fortune_id: str) -> Optional[FortuneSession]:
        """Find fortune by fortune_id"""
        try:
            result = await self.session.execute(
                select(FortuneSession).where(FortuneSession.fortune_id == fortune_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find fortune by fortune_id: {e}")
    
    async def find_user_fortunes(self, user_uuid: str, limit: int = 10) -> List[FortuneSession]:
        """Find user's recent fortunes"""
        try:
            result = await self.session.execute(
                select(FortuneSession)
                .where(FortuneSession.user_uuid == user_uuid)
                .order_by(FortuneSession.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find user fortunes: {e}")
    
    async def find_cached_fortune(self, user_uuid: str, fortune_type: str, 
                                 question_type: str = None) -> Optional[FortuneSession]:
        """Find cached fortune for user"""
        try:
            query = select(FortuneSession).where(
                and_(
                    FortuneSession.user_uuid == user_uuid,
                    FortuneSession.fortune_type == fortune_type,
                    FortuneSession.cached_until > datetime.utcnow()
                )
            )
            
            if question_type:
                query = query.where(FortuneSession.question_type == question_type)
            
            result = await self.session.execute(
                query.order_by(FortuneSession.created_at.desc())
            )
            return result.first()
        except Exception as e:
            raise RepositoryError(f"Failed to find cached fortune: {e}")
    
    async def cleanup_expired_cache(self) -> int:
        """Clean up expired cached fortunes"""
        try:
            expired_fortunes = await self.session.execute(
                select(FortuneSession).where(
                    FortuneSession.cached_until < datetime.utcnow()
                )
            )
            
            count = 0
            for fortune in expired_fortunes.scalars():
                await self.session.delete(fortune)
                count += 1
            
            await self.session.flush()
            self._clear_cache()
            
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup expired cache: {e}")


class TarotCardRepository(BaseRepository[TarotCard]):
    """Repository for TarotCard model"""
    
    def __init__(self, session: Session):
        super().__init__(TarotCard, session)
    
    async def find_by_name(self, card_name: str) -> Optional[TarotCard]:
        """Find card by name"""
        try:
            result = await self.session.execute(
                select(TarotCard).where(
                    TarotCard.card_name.ilike(f"%{card_name}%")
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find card by name: {e}")
    
    async def find_by_suit(self, suit: str) -> List[TarotCard]:
        """Find cards by suit"""
        try:
            result = await self.session.execute(
                select(TarotCard).where(TarotCard.suit == suit)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find cards by suit: {e}")
    
    async def get_random_cards(self, count: int = 3) -> List[TarotCard]:
        """Get random cards for reading"""
        try:
            result = await self.session.execute(
                select(TarotCard).order_by(func.random()).limit(count)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to get random cards: {e}")


class ZodiacInfoRepository(BaseRepository[ZodiacInfo]):
    """Repository for ZodiacInfo model"""
    
    def __init__(self, session: Session):
        super().__init__(ZodiacInfo, session)
    
    async def find_by_sign(self, sign: str) -> Optional[ZodiacInfo]:
        """Find zodiac info by sign"""
        try:
            result = await self.session.execute(
                select(ZodiacInfo).where(ZodiacInfo.sign == sign.lower())
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find zodiac by sign: {e}")
    
    async def find_by_element(self, element: str) -> List[ZodiacInfo]:
        """Find zodiac signs by element"""
        try:
            result = await self.session.execute(
                select(ZodiacInfo).where(ZodiacInfo.element == element.lower())
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to find zodiac by element: {e}")
    
    async def get_compatible_signs(self, sign: str) -> List[ZodiacInfo]:
        """Get compatible zodiac signs"""
        try:
            zodiac = await self.find_by_sign(sign)
            if not zodiac:
                return []
            
            compatible_list = zodiac.compatible_signs_list
            if not compatible_list:
                return []
            
            result = await self.session.execute(
                select(ZodiacInfo).where(ZodiacInfo.sign.in_(compatible_list))
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to get compatible signs: {e}")
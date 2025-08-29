"""
Live2D model repository
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import BaseRepository, RepositoryError
from ..models.live2d import Live2DModel


class Live2DModelRepository(BaseRepository[Live2DModel]):
    """Repository for Live2DModel"""
    
    def __init__(self, session: Session):
        super().__init__(Live2DModel, session)
    
    async def find_by_name(self, model_name: str) -> Optional[Live2DModel]:
        """Find model by name"""
        try:
            result = await self.session.execute(
                select(Live2DModel).where(
                    Live2DModel.model_name == model_name,
                    Live2DModel.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to find model by name: {e}")
    
    async def get_active_models(self) -> List[Live2DModel]:
        """Get all active models"""
        try:
            result = await self.session.execute(
                select(Live2DModel).where(Live2DModel.is_active == True)
            )
            return result.scalars().all()
        except Exception as e:
            raise RepositoryError(f"Failed to get active models: {e}")
    
    async def get_default_model(self) -> Optional[Live2DModel]:
        """Get default model (first active model)"""
        try:
            result = await self.session.execute(
                select(Live2DModel)
                .where(Live2DModel.is_active == True)
                .order_by(Live2DModel.created_at.asc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            raise RepositoryError(f"Failed to get default model: {e}")
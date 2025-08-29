"""
Base repository class with common CRUD operations and caching
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Type, Union
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..models.base import BaseModel

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=BaseModel)


class RepositoryError(Exception):
    """Base repository error"""
    pass


class NotFoundError(RepositoryError):
    """Entity not found error"""
    pass


class ConflictError(RepositoryError):
    """Entity conflict error (e.g., duplicate key)"""
    pass


class ValidationError(RepositoryError):
    """Validation error"""
    pass


class BaseRepository(Generic[ModelType], ABC):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: Type[ModelType], session: Session):
        self.model = model
        self.session = session
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
    
    # Cache management
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_parts = [self.model.__name__]
        for arg in args:
            key_parts.append(str(arg))
        for key, value in sorted(kwargs.items()):
            key_parts.append(f"{key}:{value}")
        return ":".join(key_parts)
    
    def _set_cache(self, key: str, value: Any, ttl_seconds: int = 300):
        """Set cache value with TTL"""
        self._cache[key] = value
        self._cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
    
    def _get_cache(self, key: str) -> Optional[Any]:
        """Get cache value if not expired"""
        if key not in self._cache:
            return None
        
        if datetime.utcnow() > self._cache_ttl.get(key, datetime.min):
            # Cache expired
            self._cache.pop(key, None)
            self._cache_ttl.pop(key, None)
            return None
        
        return self._cache[key]
    
    def _clear_cache(self, pattern: str = None):
        """Clear cache (all or by pattern)"""
        if pattern is None:
            self._cache.clear()
            self._cache_ttl.clear()
        else:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                self._cache.pop(key, None)
                self._cache_ttl.pop(key, None)
    
    # Basic CRUD operations
    async def create(self, **kwargs) -> ModelType:
        """Create new entity"""
        try:
            entity = self.model(**kwargs)
            self.session.add(entity)
            await self.session.flush()
            
            # Clear related cache
            self._clear_cache()
            
            logger.debug(f"Created {self.model.__name__} with id {entity.id}")
            return entity
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating {self.model.__name__}: {e}")
            raise ConflictError(f"Entity already exists or violates constraints: {e}")
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error creating {self.model.__name__}: {e}")
            raise RepositoryError(f"Failed to create entity: {e}")
    
    async def get_by_id(self, entity_id: int, use_cache: bool = True) -> Optional[ModelType]:
        """Get entity by ID"""
        cache_key = self._get_cache_key("get_by_id", entity_id)
        
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
        
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == entity_id)
            )
            entity = result.scalar_one_or_none()
            
            if use_cache and entity:
                self._set_cache(cache_key, entity)
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model.__name__} by id {entity_id}: {e}")
            raise RepositoryError(f"Failed to get entity: {e}")
    
    async def get_by_uuid(self, uuid: str, use_cache: bool = True) -> Optional[ModelType]:
        """Get entity by UUID (if model has uuid field)"""
        if not hasattr(self.model, 'uuid'):
            raise AttributeError(f"{self.model.__name__} does not have uuid field")
        
        cache_key = self._get_cache_key("get_by_uuid", uuid)
        
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached is not None:
                return cached
        
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.uuid == uuid)
            )
            entity = result.scalar_one_or_none()
            
            if use_cache and entity:
                self._set_cache(cache_key, entity)
            
            return entity
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting {self.model.__name__} by uuid {uuid}: {e}")
            raise RepositoryError(f"Failed to get entity: {e}")
    
    async def get_all(self, limit: int = 100, offset: int = 0, 
                     order_by: str = "id", desc: bool = False) -> List[ModelType]:\n        \"\"\"Get all entities with pagination\"\"\"\n        try:\n            order_column = getattr(self.model, order_by, self.model.id)\n            order_clause = order_column.desc() if desc else order_column\n            \n            result = await self.session.execute(\n                select(self.model)\n                .order_by(order_clause)\n                .limit(limit)\n                .offset(offset)\n            )\n            \n            return result.scalars().all()\n            \n        except SQLAlchemyError as e:\n            logger.error(f\"Database error getting all {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to get entities: {e}\")\n    \n    async def update(self, entity_id: int, **kwargs) -> Optional[ModelType]:\n        \"\"\"Update entity by ID\"\"\"\n        try:\n            # Remove None values and system fields\n            update_data = {\n                k: v for k, v in kwargs.items() \n                if v is not None and k not in ['id', 'created_at']\n            }\n            \n            if not update_data:\n                return await self.get_by_id(entity_id)\n            \n            # Add updated_at if model has it\n            if hasattr(self.model, 'updated_at'):\n                update_data['updated_at'] = datetime.utcnow()\n            \n            await self.session.execute(\n                update(self.model)\n                .where(self.model.id == entity_id)\n                .values(**update_data)\n            )\n            \n            # Clear cache\n            self._clear_cache()\n            \n            # Return updated entity\n            return await self.get_by_id(entity_id, use_cache=False)\n            \n        except SQLAlchemyError as e:\n            await self.session.rollback()\n            logger.error(f\"Database error updating {self.model.__name__} id {entity_id}: {e}\")\n            raise RepositoryError(f\"Failed to update entity: {e}\")\n    \n    async def delete(self, entity_id: int, soft: bool = None) -> bool:\n        \"\"\"Delete entity by ID (soft or hard delete)\"\"\"\n        try:\n            entity = await self.get_by_id(entity_id)\n            if not entity:\n                return False\n            \n            # Determine delete type\n            if soft is None:\n                soft = hasattr(entity, 'is_deleted')\n            \n            if soft and hasattr(entity, 'is_deleted'):\n                # Soft delete\n                await self.session.execute(\n                    update(self.model)\n                    .where(self.model.id == entity_id)\n                    .values(\n                        is_deleted=True,\n                        deleted_at=datetime.utcnow() if hasattr(self.model, 'deleted_at') else None\n                    )\n                )\n            else:\n                # Hard delete\n                await self.session.execute(\n                    delete(self.model).where(self.model.id == entity_id)\n                )\n            \n            # Clear cache\n            self._clear_cache()\n            \n            logger.debug(f\"{'Soft' if soft else 'Hard'} deleted {self.model.__name__} id {entity_id}\")\n            return True\n            \n        except SQLAlchemyError as e:\n            await self.session.rollback()\n            logger.error(f\"Database error deleting {self.model.__name__} id {entity_id}: {e}\")\n            raise RepositoryError(f\"Failed to delete entity: {e}\")\n    \n    async def count(self, **filters) -> int:\n        \"\"\"Count entities with optional filters\"\"\"\n        try:\n            query = select(func.count(self.model.id))\n            \n            # Apply filters\n            for field, value in filters.items():\n                if hasattr(self.model, field):\n                    query = query.where(getattr(self.model, field) == value)\n            \n            result = await self.session.execute(query)\n            return result.scalar() or 0\n            \n        except SQLAlchemyError as e:\n            logger.error(f\"Database error counting {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to count entities: {e}\")\n    \n    async def exists(self, **filters) -> bool:\n        \"\"\"Check if entity exists with filters\"\"\"\n        try:\n            query = select(self.model.id)\n            \n            # Apply filters\n            for field, value in filters.items():\n                if hasattr(self.model, field):\n                    query = query.where(getattr(self.model, field) == value)\n            \n            result = await self.session.execute(query.limit(1))\n            return result.first() is not None\n            \n        except SQLAlchemyError as e:\n            logger.error(f\"Database error checking existence of {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to check entity existence: {e}\")\n    \n    # Advanced query methods\n    async def find_by(self, limit: int = 100, offset: int = 0, \n                     order_by: str = \"id\", desc: bool = False, **filters) -> List[ModelType]:\n        \"\"\"Find entities by filters\"\"\"\n        try:\n            query = select(self.model)\n            \n            # Apply filters\n            for field, value in filters.items():\n                if hasattr(self.model, field):\n                    if isinstance(value, list):\n                        query = query.where(getattr(self.model, field).in_(value))\n                    else:\n                        query = query.where(getattr(self.model, field) == value)\n            \n            # Apply ordering\n            order_column = getattr(self.model, order_by, self.model.id)\n            order_clause = order_column.desc() if desc else order_column\n            query = query.order_by(order_clause)\n            \n            # Apply pagination\n            query = query.limit(limit).offset(offset)\n            \n            result = await self.session.execute(query)\n            return result.scalars().all()\n            \n        except SQLAlchemyError as e:\n            logger.error(f\"Database error finding {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to find entities: {e}\")\n    \n    async def find_one_by(self, **filters) -> Optional[ModelType]:\n        \"\"\"Find single entity by filters\"\"\"\n        results = await self.find_by(limit=1, **filters)\n        return results[0] if results else None\n    \n    async def bulk_create(self, entities_data: List[Dict[str, Any]]) -> List[ModelType]:\n        \"\"\"Bulk create entities\"\"\"\n        try:\n            entities = [self.model(**data) for data in entities_data]\n            self.session.add_all(entities)\n            await self.session.flush()\n            \n            # Clear cache\n            self._clear_cache()\n            \n            logger.debug(f\"Bulk created {len(entities)} {self.model.__name__} entities\")\n            return entities\n            \n        except IntegrityError as e:\n            await self.session.rollback()\n            logger.error(f\"Integrity error bulk creating {self.model.__name__}: {e}\")\n            raise ConflictError(f\"One or more entities violate constraints: {e}\")\n        except SQLAlchemyError as e:\n            await self.session.rollback()\n            logger.error(f\"Database error bulk creating {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to bulk create entities: {e}\")\n    \n    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:\n        \"\"\"Bulk update entities (each dict must contain 'id')\"\"\"\n        try:\n            count = 0\n            for update_data in updates:\n                entity_id = update_data.pop('id', None)\n                if entity_id:\n                    await self.session.execute(\n                        update(self.model)\n                        .where(self.model.id == entity_id)\n                        .values(**update_data)\n                    )\n                    count += 1\n            \n            # Clear cache\n            self._clear_cache()\n            \n            logger.debug(f\"Bulk updated {count} {self.model.__name__} entities\")\n            return count\n            \n        except SQLAlchemyError as e:\n            await self.session.rollback()\n            logger.error(f\"Database error bulk updating {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to bulk update entities: {e}\")\n    \n    async def bulk_delete(self, entity_ids: List[int], soft: bool = None) -> int:\n        \"\"\"Bulk delete entities\"\"\"\n        try:\n            if not entity_ids:\n                return 0\n            \n            # Determine delete type\n            if soft is None:\n                soft = hasattr(self.model, 'is_deleted')\n            \n            if soft and hasattr(self.model, 'is_deleted'):\n                # Soft delete\n                await self.session.execute(\n                    update(self.model)\n                    .where(self.model.id.in_(entity_ids))\n                    .values(\n                        is_deleted=True,\n                        deleted_at=datetime.utcnow() if hasattr(self.model, 'deleted_at') else None\n                    )\n                )\n            else:\n                # Hard delete\n                await self.session.execute(\n                    delete(self.model).where(self.model.id.in_(entity_ids))\n                )\n            \n            # Clear cache\n            self._clear_cache()\n            \n            logger.debug(f\"Bulk {'soft' if soft else 'hard'} deleted {len(entity_ids)} {self.model.__name__} entities\")\n            return len(entity_ids)\n            \n        except SQLAlchemyError as e:\n            await self.session.rollback()\n            logger.error(f\"Database error bulk deleting {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to bulk delete entities: {e}\")\n    \n    # Utility methods\n    def get_model_name(self) -> str:\n        \"\"\"Get model name\"\"\"\n        return self.model.__name__\n    \n    def get_table_name(self) -> str:\n        \"\"\"Get table name\"\"\"\n        return self.model.__tablename__\n    \n    async def get_statistics(self) -> Dict[str, Any]:\n        \"\"\"Get repository statistics\"\"\"\n        try:\n            total_count = await self.count()\n            \n            stats = {\n                'model': self.get_model_name(),\n                'table': self.get_table_name(),\n                'total_count': total_count,\n                'cache_size': len(self._cache)\n            }\n            \n            # Add soft delete stats if applicable\n            if hasattr(self.model, 'is_deleted'):\n                active_count = await self.count(is_deleted=False)\n                deleted_count = await self.count(is_deleted=True)\n                stats.update({\n                    'active_count': active_count,\n                    'deleted_count': deleted_count\n                })\n            \n            return stats\n            \n        except SQLAlchemyError as e:\n            logger.error(f\"Database error getting statistics for {self.model.__name__}: {e}\")\n            raise RepositoryError(f\"Failed to get statistics: {e}\")"
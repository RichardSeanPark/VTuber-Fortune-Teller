"""
Service layer for business logic and caching

Service layer provides business logic implementation with caching and performance optimization.
Complete implementation of all core services following Phase 1 architecture requirements.
"""

import time
from typing import Dict, Any

from .cache_service import CacheService
from .database_service import DatabaseService
from .chat_service import ChatService
from .fortune_service import FortuneService
from .live2d_service import Live2DService
from .user_service import UserService

class ServiceManager:
    """
    Central service manager for coordinating all backend services
    Implements Phase 1 architecture requirements for service orchestration
    Enhanced with performance monitoring and lazy loading
    """
    
    def __init__(self):
        self._cache_service = None
        self._database_service = None
        self._chat_service = None
        self._fortune_service = None
        self._live2d_service = None
        self._user_service = None
        self._initialized = False
        self._initialization_time = None
        self._service_health = {}
    
    async def initialize(self):
        """Initialize all services in proper dependency order with performance monitoring"""
        if self._initialized:
            return
        
        import time
        start_time = time.time()
        
        try:
            # Initialize core services first with performance tracking
            init_start = time.time()
            self._cache_service = CacheService()
            self._database_service = DatabaseService()
            
            await self._cache_service.initialize()
            await self._database_service.initialize()
            core_init_time = time.time() - init_start
            
            # Initialize business logic services
            business_start = time.time()
            self._chat_service = ChatService(self._database_service, self._cache_service)
            self._fortune_service = FortuneService(self._database_service, self._cache_service)
            self._live2d_service = Live2DService(self._database_service, self._cache_service)
            self._user_service = UserService(self._database_service, self._cache_service)
            
            await self._chat_service.initialize()
            await self._fortune_service.initialize()
            await self._live2d_service.initialize()
            await self._user_service.initialize()
            business_init_time = time.time() - business_start
            
            # Update health status
            self._service_health = {
                "cache_service": "healthy",
                "database_service": "healthy", 
                "chat_service": "healthy",
                "fortune_service": "healthy",
                "live2d_service": "healthy",
                "user_service": "healthy"
            }
            
            self._initialized = True
            self._initialization_time = time.time() - start_time
            
            # Log initialization performance
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"ServiceManager initialized in {self._initialization_time:.3f}s "
                       f"(core: {core_init_time:.3f}s, business: {business_init_time:.3f}s)")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"ServiceManager initialization failed: {e}")
            self._service_health = {"error": str(e)}
            raise
    
    async def shutdown(self):
        """Gracefully shutdown all services"""
        if not self._initialized:
            return
        
        # Shutdown in reverse order
        if self._user_service:
            await self._user_service.shutdown()
        if self._live2d_service:
            await self._live2d_service.shutdown()
        if self._fortune_service:
            await self._fortune_service.shutdown()
        if self._chat_service:
            await self._chat_service.shutdown()
        
        if self._database_service:
            await self._database_service.shutdown()
        if self._cache_service:
            await self._cache_service.shutdown()
        
        self._initialized = False
    
    @property
    def cache_service(self) -> CacheService:
        """Get cache service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._cache_service
    
    @property
    def database_service(self) -> DatabaseService:
        """Get database service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._database_service
    
    @property
    def chat_service(self) -> ChatService:
        """Get chat service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._chat_service
    
    @property
    def fortune_service(self) -> FortuneService:
        """Get fortune service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._fortune_service
    
    @property
    def live2d_service(self) -> Live2DService:
        """Get Live2D service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._live2d_service
    
    @property
    def user_service(self) -> UserService:
        """Get user service instance"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        return self._user_service
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all services"""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "services": {},
                "initialization_time": None
            }
        
        # Get detailed service health
        detailed_health = {}
        for service_name, status in self._service_health.items():
            detailed_health[service_name] = {
                "status": status,
                "initialized": hasattr(self, f"_{service_name}") and getattr(self, f"_{service_name}") is not None
            }
        
        # Add cache service stats if available
        if self._cache_service:
            try:
                cache_stats = self._cache_service.get_stats()
                detailed_health["cache_service"]["stats"] = cache_stats
            except:
                pass
        
        # Add database service stats if available  
        if self._database_service:
            try:
                # Note: get_database_stats should be called in async context
                # For now we'll skip this to avoid sync/async issues
                pass
            except:
                pass
        
        overall_status = "healthy" if all(s == "healthy" for s in self._service_health.values()) else "degraded"
        
        return {
            "status": overall_status,
            "services": detailed_health,
            "initialization_time": self._initialization_time,
            "initialized_at": self._initialization_time,
            "uptime_seconds": time.time() - (time.time() - (self._initialization_time or 0))
        }
    
    async def optimize_services(self) -> Dict[str, Any]:
        """Run optimization tasks on all services"""
        if not self._initialized:
            raise RuntimeError("ServiceManager not initialized")
        
        optimization_results = {}
        
        # Optimize cache service
        if self._cache_service:
            try:
                expired_cleared = self._cache_service.cleanup_expired()
                optimization_results["cache_service"] = {
                    "expired_entries_cleared": expired_cleared,
                    "status": "optimized"
                }
            except Exception as e:
                optimization_results["cache_service"] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Optimize database service
        if self._database_service:
            try:
                db_optimization = await self._database_service.optimize_database()
                optimization_results["database_service"] = db_optimization
            except Exception as e:
                optimization_results["database_service"] = {
                    "status": "error", 
                    "error": str(e)
                }
        
        return optimization_results

__all__ = [
    "ServiceManager",
    "CacheService", 
    "DatabaseService",
    "ChatService",
    "FortuneService",
    "Live2DService",
    "UserService"
]
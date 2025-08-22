"""
Fortune VTuber Backend Main Application

FastAPI application entry point for the Live2D Fortune VTuber backend service.
Based on Open-LLM-VTuber architecture with Fortune-specific features.
"""

import asyncio
import time
import gzip
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging
logger = logging.getLogger(__name__)
import uvicorn

# Configuration and database
from .config.settings import get_settings
from .config.database import init_database, close_database, check_database_health

# Initialize modules 
# from .core.logging import setup_logging
# from .core.security import SecurityManager
from .services import ServiceManager


# Performance Middleware Classes
class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor API response times and add performance headers"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Add request metadata
        request.state.start_time = start_time
        request.state.request_id = f"req_{int(start_time * 1000)}"
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        response.headers["X-Request-ID"] = request.state.request_id
        
        # Log slow requests (>200ms)
        if process_time > 0.2:
            logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.3f}s")
        
        return response


class CompressionMiddleware(BaseHTTPMiddleware):
    """Smart compression middleware for API responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Enable compression for API responses
        if (request.url.path.startswith("/api/") and 
            response.headers.get("content-type", "").startswith("application/json")):
            
            # Add cache control for API responses
            if "cache-control" not in response.headers:
                response.headers["Cache-Control"] = "public, max-age=300"
        
        return response


class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """Add appropriate cache headers for different content types"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Cache headers for static content
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
            response.headers["ETag"] = f'"{hash(request.url.path)}"'
        
        # Cache headers for fortune results
        elif request.url.path.startswith("/api/v1/fortune/"):
            if request.method == "GET":
                response.headers["Cache-Control"] = "public, max-age=1800"  # 30 minutes
        
        # No cache for health checks
        elif request.url.path.startswith("/health"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        
        return response


# Middleware application functions
async def add_performance_monitoring(request: Request, call_next):
    """Add performance monitoring to requests"""
    middleware = PerformanceMonitoringMiddleware(None)
    return await middleware.dispatch(request, call_next)


async def add_compression_middleware(request: Request, call_next):
    """Add compression middleware"""
    middleware = CompressionMiddleware(None)
    return await middleware.dispatch(request, call_next)


async def add_cache_headers(request: Request, call_next):
    """Add cache headers middleware"""
    middleware = CacheHeadersMiddleware(None)
    return await middleware.dispatch(request, call_next)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    settings = get_settings()
    
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
        
        # Initialize security manager
        # security_manager = SecurityManager()
        # app.state.security_manager = security_manager
        # logger.info("Security manager initialized")
        
        # Initialize service manager
        service_manager = ServiceManager()
        await service_manager.initialize()
        app.state.service_manager = service_manager
        logger.info("Service manager initialized")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    # Application is ready
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Cleanup services
        if hasattr(app.state, 'service_manager'):
            await app.state.service_manager.shutdown()
            logger.info("Service manager shutdown")
        
        # Close database
        await close_database()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description=settings.app_description,
        version=settings.app_version,
        debug=settings.server.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development() else None,
        redoc_url="/redoc" if settings.is_development() else None,
        openapi_url="/openapi.json" if settings.is_development() else None
    )
    
    # Add GZip compression middleware (must be added before other middleware)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Configure CORS
    if settings.server.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.server.cors_origins,
            allow_credentials=settings.server.cors_credentials,
            allow_methods=settings.server.cors_methods,
            allow_headers=settings.server.cors_headers,
        )
    
    # Add static files
    if settings.server.static_files_enabled:
        app.mount(
            settings.server.static_url_path,
            StaticFiles(directory=settings.server.static_directory),
            name="static"
        )
    
    # Register routers
    from .api.router import api_router, direct_api_router, v2_api_router
    from .websocket.router import ws_router
    
    app.include_router(api_router)
    app.include_router(direct_api_router)
    app.include_router(v2_api_router)
    app.include_router(ws_router)
    
    # Add performance and monitoring middleware
    app.middleware("http")(add_performance_monitoring)
    app.middleware("http")(add_compression_middleware)
    app.middleware("http")(add_cache_headers)
    # app.middleware("http")(add_security_headers)
    # app.middleware("http")(add_request_logging)
    # app.middleware("http")(add_rate_limiting)
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Add basic health check endpoints
    register_health_endpoints(app)
    
    # Add root route to serve index.html
    register_frontend_routes(app)
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers"""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "status_code": exc.status_code
                },
                "metadata": {
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors"""
        logger.warning(f"Validation error: {exc.errors()} - {request.url}")
        
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors()
                },
                "metadata": {
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.error(f"Unexpected error: {exc} - {request.url}")
        
        settings = get_settings()
        error_detail = str(exc) if settings.is_development() else "Internal server error"
        
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_detail
                },
                "metadata": {
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.now().isoformat()
                }
            }
        )


def register_health_endpoints(app: FastAPI) -> None:
    """Register health check endpoints"""
    
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Basic health check endpoint"""
        return {
            "success": True,
            "data": {
                "status": "healthy",
                "service": "fortune-vtuber-backend",
                "version": get_settings().app_version
            }
        }
    
    @app.get("/health/detailed", tags=["Health"])
    async def detailed_health_check():
        """Detailed health check with database status"""
        settings = get_settings()
        
        # Check database health
        db_health = await check_database_health()
        
        # Overall status
        overall_status = "healthy" if db_health.get("status") == "healthy" else "unhealthy"
        
        return {
            "success": True,
            "data": {
                "status": overall_status,
                "service": settings.app_name,
                "version": settings.app_version,
                "environment": settings.environment,
                "components": {
                    "database": db_health,
                    "api": {"status": "healthy"},
                    "websocket": {"status": "healthy" if settings.server.websocket_enabled else "disabled"}
                }
            }
        }
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check for container orchestration"""
        db_health = await check_database_health()
        
        if db_health.get("status") != "healthy":
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "data": {
                        "status": "not_ready",
                        "reason": "Database not healthy"
                    }
                }
            )
        
        return {
            "success": True,
            "data": {
                "status": "ready"
            }
        }
    
    @app.get("/health/live", tags=["Health"])
    async def liveness_check():
        """Liveness check for container orchestration"""
        return {
            "success": True,
            "data": {
                "status": "alive"
            }
        }
    
    @app.get("/health/services", tags=["Health"])
    async def services_health_check():
        """Service manager health check with detailed service status"""
        try:
            if hasattr(app.state, 'service_manager'):
                health_status = app.state.service_manager.get_health_status()
                return {
                    "success": True,
                    "data": health_status
                }
            else:
                return {
                    "success": False,
                    "data": {
                        "status": "service_manager_not_initialized",
                        "services": {}
                    }
                }
        except Exception as e:
            logger.error(f"Services health check failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "HEALTH_CHECK_FAILED",
                        "message": str(e)
                    }
                }
            )
    
    @app.post("/health/integration-test", tags=["Health"])
    async def run_integration_test():
        """Run comprehensive integration tests"""
        try:
            from .core.integration_test import run_integration_tests
            
            # 통합 테스트 실행
            results = await run_integration_tests()
            
            # 성공 여부 판단
            success = results["summary"]["failed"] == 0
            status_code = 200 if success else 500
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "success": success,
                    "data": results,
                    "metadata": {
                        "test_type": "integration",
                        "timestamp": results.get("completed_at")
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTEGRATION_TEST_FAILED",
                        "message": f"통합 테스트 실행 중 오류가 발생했습니다: {str(e)}"
                    }
                }
            )


def register_frontend_routes(app: FastAPI) -> None:
    """Register frontend routes to serve React SPA"""
    
    @app.get("/", tags=["Frontend"])
    async def serve_frontend():
        """Serve the main frontend application"""
        settings = get_settings()
        static_path = Path(settings.server.static_directory) / "index.html"
        
        if static_path.exists():
            return FileResponse(static_path)
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": {
                        "code": "FRONTEND_NOT_FOUND", 
                        "message": "Frontend application not found"
                    }
                }
            )
    
    @app.get("/app", tags=["Frontend"])
    async def serve_frontend_app():
        """Alternative route to serve frontend application"""
        return await serve_frontend()
    
    @app.get("/favicon.ico", tags=["Frontend"])
    @app.head("/favicon.ico", tags=["Frontend"])
    async def serve_favicon():
        """Serve favicon.ico"""
        settings = get_settings()
        favicon_path = Path(settings.server.static_directory) / "favicon.ico"
        
        if favicon_path.exists():
            return FileResponse(favicon_path)
        else:
            # 기본 favicon을 제공하거나 404 반환
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": {
                        "code": "FAVICON_NOT_FOUND",
                        "message": "Favicon not found"
                    }
                }
            )


# Create the application instance
app = create_application()


# Development server function
def run_dev_server():
    """Run development server"""
    settings = get_settings()
    
    logger.info("Starting development server...")
    
    uvicorn.run(
        "fortune_vtuber.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload,
        log_level=settings.logging.log_level.lower(),
        access_log=settings.logging.api_access_log_enabled
    )


# Production server function
def run_production_server():
    """Run production server with gunicorn"""
    settings = get_settings()
    
    if not settings.is_production():
        raise RuntimeError("Production server should only be used in production environment")
    
    logger.info("Starting production server...")
    
    # This would typically be called via gunicorn command line
    # gunicorn -c gunicorn.conf.py fortune_vtuber.main:app
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.logging.log_level.lower(),
        access_log=settings.logging.api_access_log_enabled
    )


if __name__ == "__main__":
    settings = get_settings()
    
    if settings.is_development():
        run_dev_server()
    else:
        run_production_server()
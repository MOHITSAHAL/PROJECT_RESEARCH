"""
Main FastAPI application entry point.
Configured for POC (local) to Production (AWS) deployment.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import structlog

from .core.config import settings
from .core.logging import setup_logging, get_logger
from .database.connection import db_manager
from .api.v1.router import api_router
from .models.common_models import ErrorResponse, HealthCheck
from .events.base import event_bus
from .events.handlers import PaperEventHandler, AgentEventHandler, SystemEventHandler

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')


def initialize_event_system():
    """Initialize event handlers."""
    event_bus.subscribe(PaperEventHandler())
    event_bus.subscribe(AgentEventHandler())
    event_bus.subscribe(SystemEventHandler())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Research Paper Intelligence System", version=settings.version)
    
    # Initialize event system
    initialize_event_system()
    
    # Initialize database connections
    try:
        health = db_manager.health_check()
        logger.info("Database health check", **health)
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise
    
    # Store start time for uptime calculation
    app.state.start_time = time.time()
    
    # Publish startup event
    await event_bus.publish(
        event_bus.create_event(
            "system.startup",
            {"environment": settings.environment, "version": settings.version},
            "main_app"
        )
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Publish shutdown event
    await event_bus.publish(
        event_bus.create_event(
            "system.shutdown",
            {"environment": settings.environment},
            "main_app"
        )
    )
    
    db_manager.close_connections()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI Research Paper Intelligence System - Transform research papers into interactive AI agents",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware (production security)
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
    )


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Request logging and metrics middleware."""
    start_time = time.time()
    
    # Log request
    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error("request_failed", error=str(e))
        status_code = 500
        response = JSONResponse(
            status_code=500,
            content=ErrorResponse.create(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred"
            ).dict()
        )
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Update metrics
    if settings.enable_metrics:
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=status_code
        ).inc()
        REQUEST_DURATION.observe(duration)
    
    # Log response
    logger.info(
        "request_completed",
        method=request.method,
        url=str(request.url),
        status_code=status_code,
        duration=duration
    )
    
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse.create(
            code=f"HTTP_{exc.status_code}",
            message=exc.detail
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with structured error responses."""
    logger.error("unhandled_exception", error=str(exc), error_type=type(exc).__name__)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse.create(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred" if settings.is_production else str(exc)
        ).dict()
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Application health check endpoint."""
    try:
        # Check database connections
        db_health = db_manager.health_check()
        
        # Calculate uptime
        uptime = time.time() - app.state.start_time if hasattr(app.state, 'start_time') else None
        
        return HealthCheck(
            status="healthy" if all(db_health.values()) else "degraded",
            timestamp=time.time(),
            version=settings.version,
            environment=settings.environment,
            services=db_health,
            uptime=uptime
        )
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return HealthCheck(
            status="unhealthy",
            timestamp=time.time(),
            version=settings.version,
            environment=settings.environment,
            services={"error": str(e)}
        )


# Metrics endpoint (Prometheus)
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics not enabled")
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Include API router
app.include_router(api_router, prefix=settings.api_prefix)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with application information."""
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "docs_url": "/docs" if settings.debug else None,
        "health_url": "/health",
        "api_prefix": settings.api_prefix,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
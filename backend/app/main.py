"""
AquaNexis Backend - Main FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID
import json

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.infrastructure.config import get_settings
from app.infrastructure.database import init_db, close_db, db_manager
from app.infrastructure.logging import configure_logging, get_logger, set_request_id, get_request_id
from app.infrastructure.security import rate_limit
from app.infrastructure.websocket import ws_manager
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as health_router

settings = get_settings()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    configure_logging()
    logger.info("application_starting", environment=settings.env)

    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        raise

    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")
    await close_db()
    logger.info("application_stopped")


app = FastAPI(
    title="AquaNexis API",
    description="Predictive Water Intelligence Platform",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID", "")
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())

    set_request_id(request_id)

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Metrics middleware
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect Prometheus metrics."""
    import time
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)

    return response


# Rate limiting middleware (applied via dependency in routes)
# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        request_id=get_request_id(),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix="/api/v1")


# WebSocket endpoint
@app.websocket("/ws/devices/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for real-time device updates."""
    try:
        device_uuid = UUID(device_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid device ID")
        return

    await ws_manager.connect(websocket, device_uuid)
    
    try:
        while True:
            # Keep connection alive, handle incoming messages if needed
            data = await websocket.receive_text()
            # Echo back for now, could handle commands later
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, device_uuid)
    except Exception as e:
        logger.error("ws_error", device_id=device_id, error=str(e))
        ws_manager.disconnect(websocket, device_uuid)


# Prometheus metrics endpoint
@app.get("/metrics", include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "service": "AquaNexis API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs" if settings.is_development else "disabled",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_config=None,  # We use structlog
    )
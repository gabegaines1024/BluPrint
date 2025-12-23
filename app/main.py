"""FastAPI application main entry point."""

import logging
from pathlib import Path
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import os

from app.database import init_db, engine
from app.models import Base
from app.routes import auth, parts, compatibility, builds, recommendations, agent
from app.exceptions import AppError, AuthenticationError, AuthorizationError, NotFoundError, ValidationError

# Setup logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
log_file = os.environ.get('LOG_FILE', 'app.log')

logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Reduce noise from some loggers
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BluPrint API",
    description="PC Building Compatibility and Recommendation System",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
if cors_origins and cors_origins != ['*']:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Error Handlers
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle application-specific errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.message, 'status_code': exc.status_code}
    )


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.message, 'status_code': exc.status_code}
    )


@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.message, 'status_code': exc.status_code}
    )


@app.exception_handler(NotFoundError)
async def not_found_error_handler(request: Request, exc: NotFoundError):
    """Handle not found errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.message, 'status_code': exc.status_code}
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': exc.message, 'status_code': exc.status_code}
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'error': 'Validation error', 'detail': exc.errors()}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Handle internal server errors."""
    logger.error(f'Internal error: {exc}', exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'error': 'An internal error occurred', 'status_code': 500}
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting BluPrint API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down BluPrint API...")


# Register routers
app.include_router(auth.router)
app.include_router(parts.router)
app.include_router(compatibility.router)
app.include_router(builds.router)
app.include_router(recommendations.router)
app.include_router(agent.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON response with health status.
    """
    try:
        # Check database connectivity
        from sqlalchemy import text
        from app.database import SessionLocal
        
        db = SessionLocal()
        try:
            db.execute(text('SELECT 1'))
            db_status = 'healthy'
        finally:
            db.close()
    except Exception as e:
        logger.error(f'Database health check failed: {e}')
        db_status = 'unhealthy'
    
    status_code = status.HTTP_200_OK if db_status == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content={
            'status': 'ok' if db_status == 'healthy' else 'degraded',
            'database': db_status
        }
    )


# Serve frontend files
project_root = Path(__file__).parent.parent
frontend_dir = project_root / 'frontend'

if frontend_dir.exists():
    # Mount static files
    app.mount("/src", StaticFiles(directory=str(frontend_dir / 'src')), name="src")
    
    @app.get("/")
    async def serve_index():
        """Serve the main HTML page."""
        index_file = frontend_dir / 'index.html'
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Frontend not found'}
        )
    
    @app.get("/{path:path}")
    async def serve_frontend(path: str):
        """Serve static files from frontend directory."""
        # Security: prevent directory traversal
        if '..' in path:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={'error': 'Not found'}
            )
        
        file_path = frontend_dir / path
        
        # Check if file exists
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        
        # If not found, serve index.html for SPA routing
        index_file = frontend_dir / 'index.html'
        if index_file.exists():
            return FileResponse(str(index_file))
        
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={'error': 'Not found'}
        )


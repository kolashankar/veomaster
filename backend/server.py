from fastapi import FastAPI, APIRouter, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import os
import time
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routes import jobs, videos
from services.database_service import db_service
from config import CORS_ORIGINS
from utils.logger import get_logger, log_api_request

# Get logger instance
logger = get_logger(__name__, "app.log")

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(f"📨 Incoming: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_api_request(
                request.method,
                request.url.path,
                response.status_code,
                duration_ms
            )
            
            # Log status with emoji
            if response.status_code < 400:
                logger.info(f"✅ Success: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
            elif response.status_code < 500:
                logger.warning(f"⚠️  Client Error: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
            else:
                logger.error(f"❌ Server Error: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)")
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(f"💥 Exception: {request.method} {request.url.path} - {str(e)} ({duration_ms:.2f}ms)")
            raise


# Create the main app without a prefix
app = FastAPI(title="Google Flow Video Automation API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {
        "message": "Google Flow Video Automation Platform API",
        "status": "running",
        "version": "1.0.0"
    }

# Include route modules
api_router.include_router(jobs.router)
api_router.include_router(videos.router)

# Include the router in the main app
app.include_router(api_router)

# Add logging middleware (BEFORE CORS to log all requests)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS if isinstance(CORS_ORIGINS, list) else CORS_ORIGINS.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 Google Flow Video Automation Platform STARTING")
    logger.info("=" * 80)
    logger.info("✅ Phase 1: Foundation - Database, Models, Storage initialized")
    logger.info("✅ Phase 2: Backend Services - Automation & Upscaling ready")
    logger.info("✅ Phase 3: Frontend - Dashboard & Video Gallery")
    logger.info("✅ Phase 4: Automation Workflow - Browser automation & Error recovery")
    logger.info("✅ Phase 5: Selection & Download - Video management")
    logger.info("✅ Phase 6: Production Polish - UI/UX & Performance optimizations")
    logger.info("✅ Logging System - Comprehensive logging with rotation")
    logger.info("🌐 API Server: http://0.0.0.0:8001")
    logger.info("📝 Logs Directory: /app/logs/")
    logger.info("=" * 80)

@app.on_event("shutdown")
async def shutdown_event():
    await db_service.close()
    logger.info("=" * 80)
    logger.info("👋 Application shutdown complete")
    logger.info("=" * 80)
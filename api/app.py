from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging

from .routes import reports
from .models import HealthCheck

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="User Reports API",
    description="API для получения отчетов пользователей",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {exc}", exc_info=True)

    status_code = 500
    detail = str(exc)

    if hasattr(exc, 'status_code'):
        status_code = exc.status_code
    if hasattr(exc, 'detail'):
        detail = exc.detail

    return JSONResponse(
        status_code=status_code,
        content={
            "error": "Internal Server Error",
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        }
    )

app.include_router(reports.router)

@app.get("/")
async def root():
    return {
        "service": "User Reports API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "user_report": "/reports/me",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthCheck)
async def health_check():
    try:
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = True
    except Exception as e:
        logger.error(f"Database error: {e}")
        db_status = False

    return HealthCheck(
        status="healthy" if db_status else "unhealthy",
        database=db_status,
        timestamp=datetime.now()
    )

@app.get("/ping")
async def ping():
    return {"message": "pong", "timestamp": datetime.now().isoformat()}
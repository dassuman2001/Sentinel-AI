from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis

from app.config.settings import settings
from app.utils.logging import setup_logging
from app.database.session import engine, get_db
from app.database.base_class import Base
# Make sure models are imported to register with Base
from app.models import *
from app.api.v1.router import api_router

# Setup system logging
setup_logging()

# Auto-create tables on startup in development mode
# Note: For production deployments, Alembic migrations are preferred.
if settings.ENV == "dev":
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import logging
        logging.getLogger("sentinel").error(f"Error creating database tables: {str(e)}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Sentinel AI - Enterprise AI-Powered Secret Leak Prevention Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS middleware
# In dev/production, restrict origins as configured
origins = []
if isinstance(settings.BACKEND_CORS_ORIGINS, list):
    origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
else:
    origins = [settings.BACKEND_CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include main API Router
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", status_code=status.HTTP_200_OK, tags=["health"])
def health_check(db: Session = Depends(get_db)) -> dict:
    """System health check verifying database and Redis connections."""
    db_status = "healthy"
    redis_status = "healthy"
    
    # 1. Verify Database Connection
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"
        
    # 2. Verify Redis Connection
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=1)
        r.ping()
    except Exception:
        redis_status = "unhealthy"
        
    if db_status == "unhealthy" or redis_status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": db_status,
                "redis": redis_status
            }
        )
        
    return {
        "status": "healthy",
        "database": db_status,
        "redis": redis_status
    }

@app.get("/", tags=["root"])
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "version": "1.0.0"
    }

from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.faces import router as faces_router
from app.api.routes.recognition import router as recognition_router
from app.api.routes.datasets import router as datasets_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.exports import router as exports_router
from app.api.routes.admin import router as admin_router
from app.config import load_settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware, RateLimitMiddleware
from app.core.exception_handlers import register_exception_handlers
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.core.security import hash_password

# Initialize logging and config early
configure_logging()
settings = load_settings()
logger = logging.getLogger("visionid")


def seed_admin_user() -> None:
    db = Session(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    try:
        count = db.query(User).count()
        if count == 0:
            admin = User(
                full_name="VisionID Admin",
                email="admin@visionid.ai",
                password_hash=hash_password("Admin@12345"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded default admin user: admin@visionid.ai / Admin@12345")
    except Exception as e:
        logger.error("Failed to seed default admin user: %s", e)
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info("Initializing VisionID AI backend services...")
    if settings.auto_create_tables:
        logger.info("Creating database tables if not existing...")
        Base.metadata.create_all(bind=engine)
    seed_admin_user()
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down VisionID AI backend services...")


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Exception handlers
register_exception_handlers(app)

# Request context / correlation ID middleware (must be outermost to trace everything)
app.add_middleware(RequestContextMiddleware)

# Rate limiter middleware
app.add_middleware(
    RateLimitMiddleware,
    default_limit=settings.rate_limit_per_minute,
    path_limits={
        f"{settings.api_prefix}/auth/login": settings.rate_limit_login_per_minute,
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(faces_router, prefix=settings.api_prefix)
app.include_router(recognition_router, prefix=settings.api_prefix)
app.include_router(datasets_router, prefix=settings.api_prefix)
app.include_router(analytics_router, prefix=settings.api_prefix)
app.include_router(exports_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)


@app.get("/")
def root():
    return {"message": "VisionID AI backend is running", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)

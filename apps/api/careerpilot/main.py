from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from careerpilot.api.ai import router as ai_router
from careerpilot.api.health import router as health_router
from careerpilot.api.jobs import router as jobs_router
from careerpilot.api.matching import router as matching_router
from careerpilot.api.profile import router as profile_router
from careerpilot.api.resume import router as resume_router
from careerpilot.core.config import get_settings
from careerpilot.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_started", environment=settings.environment)
    yield
    logger.info("application_stopped")


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(jobs_router)
app.include_router(matching_router)
app.include_router(ai_router)
app.include_router(profile_router)
app.include_router(resume_router)

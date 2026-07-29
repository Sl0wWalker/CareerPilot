from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from careerpilot.api.ai import router as ai_router
from careerpilot.api.automation import router as automation_router
from careerpilot.api.beta import router as beta_router
from careerpilot.api.coach import router as coach_router
from careerpilot.api.documents import router as documents_router
from careerpilot.api.enterprise import router as enterprise_router
from careerpilot.api.health import router as health_router
from careerpilot.api.jobs import router as jobs_router
from careerpilot.api.matching import router as matching_router
from careerpilot.api.platform import router as platform_router
from careerpilot.api.profile import router as profile_router
from careerpilot.api.release import router as release_router
from careerpilot.api.resume import router as resume_router
from careerpilot.api.sync import router as sync_router
from careerpilot.api.tracking import router as tracking_router
from careerpilot.core.config import get_settings
from careerpilot.core.logging import configure_logging
from careerpilot.core.middleware import OperationsMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("application_started", environment=settings.environment)
    yield
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(
    OperationsMiddleware,
    requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
    settings=settings,
)
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
app.include_router(automation_router)
app.include_router(documents_router)
app.include_router(profile_router)
app.include_router(resume_router)
app.include_router(tracking_router)
app.include_router(release_router)
app.include_router(beta_router)
app.include_router(sync_router)
app.include_router(coach_router)
app.include_router(platform_router)
app.include_router(enterprise_router)

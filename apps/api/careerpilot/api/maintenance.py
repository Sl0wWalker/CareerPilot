from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from careerpilot.core.config import get_settings

router = APIRouter(prefix="/api/v1/maintenance", tags=["maintenance"])


class MaintenanceStatus(BaseModel):
    version: str
    governance_documents: dict[str, bool]
    quality_commands: list[str]
    compatibility_policy: str
    security_reporting: str


@router.get("/status", response_model=MaintenanceStatus)
def maintenance_status() -> MaintenanceStatus:
    settings = get_settings()
    repository_root = Path(__file__).resolve().parents[4]
    required = [
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        "docs/GOVERNANCE.md",
        "docs/API_COMPATIBILITY.md",
        "docs/PLUGIN_GOVERNANCE.md",
    ]
    return MaintenanceStatus(
        version=settings.app_version,
        governance_documents={
            document: (repository_root / document).exists() for document in required
        },
        quality_commands=[
            r".\scripts\quality.ps1",
            "pytest apps/api",
            "npm test --prefix apps/web",
        ],
        compatibility_policy="/api/v1 follows semantic versioning and documented deprecation",
        security_reporting="GitHub private vulnerability reporting",
    )


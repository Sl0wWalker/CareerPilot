# CareerPilot

CareerPilot is a free, local-first job application assistant. Milestone 0 provides
the tested local foundation only: a FastAPI service, a React dashboard, SQLite,
database migrations, configuration, structured logs, health checks, and developer
scripts.

AI, job discovery, resume processing, matching, and browser automation are
intentionally outside this milestone.

## Prerequisites

- Windows 11
- Git
- Python 3.12 (the Windows `py` launcher must work)
- Node.js 24 LTS and npm

## First-time setup

Open PowerShell in the repository root:

```powershell
Copy-Item .env.example .env
.\scripts\setup.ps1
```

## Run CareerPilot

```powershell
.\scripts\dev.ps1
```

Open:

- Dashboard: http://localhost:5173
- API health: http://127.0.0.1:8000/health
- API readiness: http://127.0.0.1:8000/ready
- API documentation: http://127.0.0.1:8000/docs

## Run checks

```powershell
.\scripts\test.ps1
.\scripts\lint.ps1
```

## Run database migrations

From the repository root:

```powershell
.\apps\api\.venv\Scripts\python.exe -m alembic -c apps\api\alembic.ini upgrade head
```

No application tables exist yet; migrations are ready for the next milestone.

## Repository layout

```text
apps/api       FastAPI service, database setup, migrations, and backend tests
apps/web       React + TypeScript + Vite dashboard and frontend tests
data           Local runtime data (ignored by Git except for the placeholder)
scripts        Windows setup, development, test, and validation helpers
```


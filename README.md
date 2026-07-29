# CareerPilot

CareerPilot is a free, local-first job application assistant. Version 1 includes a
career knowledge base, resume ingestion, optional local AI intelligence, job discovery,
explainable matching, document generation, supervised browser automation, application
tracking, and release-hardening foundations.

Milestone 12 adds optional offline-first multi-device sync, granular shared workspaces,
connected-account foundations, and webhook APIs. Local use remains fully supported without
connecting a cloud provider. See `docs/milestones/M12.md` for the protocol and privacy model.

Licensed under Apache-2.0. CareerPilot is an original clean-room implementation and
does not include ApplyPilot source code.

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
- Diagnostics: http://127.0.0.1:8000/diagnostics
- Metrics: http://127.0.0.1:8000/metrics

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

Migrations create the career profile and related career-knowledge tables.

## Production release

Production requires authentication and a secret with at least 32 characters. Copy
`.env.example`, set environment-specific values, then use:

```powershell
docker compose up --build -d
```

The web UI is served on port 8080 and the API on port 8000. Backup and restore:

```powershell
.\scripts\backup.ps1
.\scripts\restore.ps1 -BackupPath .\data\backups\<backup-file>.db
```

See `docs/milestones/M9.md` for the security model and release checklist.

## Version 1 documentation

- `docs/USER_GUIDE.md`
- `docs/DEVELOPMENT.md`
- `docs/DEPLOYMENT.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/VALIDATION_REPORT.md`
- `CHANGELOG.md`

## Career profile API

- `GET /profile` retrieves the local profile.
- `POST /profile` creates the profile and optional nested career records.
- `PATCH /profile` updates profile-level fields.
- `GET /profile/full` retrieves the profile with all related career records.

CareerPilot supports one local profile in this milestone. Persistence is separated
into repository, service, and API layers; details are recorded in
`docs/milestones/M1.md`.

## Resume ingestion

Create a career profile before importing a resume. The dashboard supports PDF,
DOCX, and UTF-8 TXT files up to 10 MB.

Resume endpoints:

- `POST /resume/import?filename=<name>` accepts the file bytes with its actual
  `Content-Type`.
- `GET /resume/imports` lists import history.
- `GET /resume/import/{id}` retrieves an import.
- `DELETE /resume/import/{id}` removes an import and its temporary facts.
- `GET /resume/import/{id}/review` retrieves the review queue.
- `PATCH /resume/import/{id}/fact/{factId}` edits or decides a fact.
- `POST /resume/import/{id}/approve` promotes accepted facts to the career profile.

The parser is deterministic and local. See `docs/milestones/M2.md` for its pipeline,
validation rules, and extension points.

## Repository layout

```text
apps/api       FastAPI service, database setup, migrations, and backend tests
apps/web       React + TypeScript + Vite dashboard and frontend tests
data           Local runtime data (ignored by Git except for the placeholder)
scripts        Windows setup, development, test, and validation helpers
```
## Milestone 4

CareerPilot now includes a local intelligent job-discovery workspace with Greenhouse,
Lever, Ashby, Workday-compatible JSON, generic JSON, and RSS source adapters. Listings are
normalized, deduplicated, searchable, filterable, and can be saved or analyzed for
AI-assisted relevance using the existing local provider configuration.

Source syncs are explicit. Saved schedule definitions do not run in the background yet.

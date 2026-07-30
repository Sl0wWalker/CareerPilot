# CareerPilot Local Demo and Self-Testing Guide

This guide was verified on Windows. The demo uses fictional data and never opens or
submits a real job application.

## What is demonstrable today

The local app supports profile and resume ingestion, job browsing, explainable matching,
deterministic or Ollama-assisted document generation, dry-run application review, and
application tracking. ATS browser tests run against local HTML fixtures.

Live browser execution and final submission are **not wired to the API**. A non-dry-run
request is rejected. CAPTCHA bypass is not implemented.

## Prerequisites

- Windows 11
- Git
- Python 3.12 with the `py` launcher
- Node.js 24 LTS and npm
- Ollama 0.32 or newer (optional for AI features)
- Ollama models: `qwen3:8b`; optional embedding model `nomic-embed-text`

No account is required in local development because `CAREERPILOT_AUTH_ENABLED=false`.
There are no demo credentials.

## First-time installation

Open PowerShell in the repository root:

```powershell
Copy-Item .env.example .env
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

The setup creates `apps\api\.venv`, installs Python and npm dependencies, and installs
Playwright Chromium.

Optional local AI:

```powershell
ollama list
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

The default AI endpoint is `http://localhost:11434`.

## Shortest safe demo

Use an empty development database. Then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\demo.ps1
```

Open `http://localhost:4725`. The API is at `http://127.0.0.1:8000`; interactive API
documentation is at `http://127.0.0.1:8000/docs`.

The seed script refuses to run when any non-demo profile exists. It creates only:

- fictional candidate Jordan Taylor;
- a fictional Formal Verification Engineer job;
- an explainable match;
- an approved example resume;
- a completed dry-run automation review;
- a ready (not submitted) tracking record.

## Walk through the demo

1. Complete the first-run introduction.
2. Open **Resume imports**. To exercise parsing, upload
   `samples\demo_resume.txt`, review each extracted fact, and accept only accurate test facts.
3. Open **Job discovery**. Select the fictional job and inspect or recalculate its match.
4. Open **Document studio**. Select the seeded resume, inspect its evidence and keyword
   coverage, and export PDF or DOCX.
5. Open **Application automation**. Inspect the fictional `generic` run. Confirm that the
   sponsorship field is visibly marked for review and the checkpoint is
   `stopped_before_submit`.
6. Open **Applications** and confirm the fictional job is in `ready`, not `submitted`.

When testing with your real resume later, start with a fresh database and never approve an
extracted fact until you verify it.

## Manual startup without demo data

```powershell
.\apps\api\.venv\Scripts\python.exe -m alembic -c apps\api\alembic.ini upgrade head
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

Development ports:

- Dashboard: `http://localhost:4725`
- API: `http://127.0.0.1:8000`
- Health: `http://127.0.0.1:8000/health`
- Readiness: `http://127.0.0.1:8000/ready`
- Diagnostics: `http://127.0.0.1:8000/diagnostics`
- API docs: `http://127.0.0.1:8000/docs`

## Verified test commands

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\lint.ps1
```

Expected results at verification:

- Backend: `59 passed` (one upstream Starlette/httpx deprecation warning)
- Frontend: `1 passed`
- Biome: no errors
- TypeScript and Vite production build: success
- Alembic: upgrade through migration `m19a00000019`

The ATS compatibility suite uses Playwright Chromium and local fixtures. It asserts that
the final Submit control is never clicked.

## Environment variables

Copy `.env.example` to `.env`. Important values:

```text
CAREERPILOT_DATABASE_URL=sqlite:///./data/careerpilot.db
CAREERPILOT_AI_PROVIDER=ollama
CAREERPILOT_AI_MODEL=qwen3:8b
CAREERPILOT_AI_EMBEDDING_MODEL=nomic-embed-text
CAREERPILOT_AI_BASE_URL=http://localhost:11434
CAREERPILOT_AUTH_ENABLED=false
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Do not commit `.env`, the SQLite database, resumes, generated documents, or browser state.

## Reset or reseed safely

Stop CareerPilot first. Back up the database:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\backup.ps1
```

For a completely fresh **demo-only** database, move (do not permanently delete) the exact
database file:

```powershell
New-Item -ItemType Directory -Force .\data\old
Move-Item .\data\careerpilot.db .\data\old\careerpilot-before-reset.db
powershell -ExecutionPolicy Bypass -File .\scripts\demo.ps1
```

Do not run the move command if `data\careerpilot.db` contains information you still need.

## Troubleshooting

- **PowerShell blocks scripts:** prefix commands with
  `powershell -ExecutionPolicy Bypass -File`.
- **`python` is not found:** verify `py --version` reports Python 3.12, then rerun setup.
- **Broken copied virtual environment:** remove only `apps\api\.venv` and rerun setup.
- **npm cannot run:** verify `node --version` and `npm.cmd --version`; reopen PowerShell.
- **Port 4725 or 8000 is busy:** stop the previous CareerPilot processes before restarting.
- **Database tables missing:** run the Alembic upgrade command shown above.
- **Ollama offline:** run `ollama --version`, `ollama list`, and verify
  `http://localhost:11434/api/tags`. Deterministic features still work without Ollama.
- **Model missing:** run `ollama pull qwen3:8b`.
- **Playwright browser missing:** run
  `.\apps\api\.venv\Scripts\python.exe -m playwright install chromium`.
- **No jobs appear:** the normal UI requires a configured/synced source; use demo mode for
  the offline fixture or configure a source in `/docs`.
- **Automation does not open a live site:** this is intentional. Current API behavior is
  supervised fixture/dry-run only.

## Current limitations

- No live application submission.
- No CAPTCHA or MFA automation.
- Real ATS compatibility is not proven by the fixture suite.
- Job import has no simple paste-URL endpoint; sources are configured through the API.
- The UI does not yet provide a full profile editor or source-creation wizard.
- AI output quality depends on the selected local model and still requires user review.

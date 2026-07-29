# CareerPilot Agent Instructions

CareerPilot is an original, local-first job application assistant.

## Scope

- Work in small, tested milestones.
- Keep the application free to run locally.
- Do not copy ApplyPilot source code, prompts, schemas, UI, or documentation.
- Prefer original implementations and official documentation.

## Current architecture

- Backend: Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic Settings.
- Frontend: React, TypeScript, Vite.
- Development database: SQLite.
- Local AI: Ollama by default, behind a provider interface.
- Browser automation: supervised Playwright foundations; final submission requires approval.

The milestone roadmap is complete. Prefer validation, simplification, and reliability work over
new feature breadth. Do not describe a foundation or placeholder as production-ready behavior.

## Safety and quality

- Never commit personal data, resumes, databases, secrets, or browser sessions.
- Add tests for new behavior.
- Run linting, type checks, tests, and builds before completion.
- Keep setup and run instructions current.

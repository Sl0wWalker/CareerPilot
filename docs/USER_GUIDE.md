# CareerPilot v1 User Guide

## Start the application

Run `.\scripts\dev.ps1`, then open `http://localhost:5173`.

The first-run guide explains the safe workflow. It can be reopened from **Start &
help**.

## Recommended workflow

1. Import a PDF, DOCX, or TXT resume.
2. Review every extracted fact and approve only accurate information.
3. Open **AI intelligence** and confirm the local Ollama provider.
4. Discover or import a job and inspect the evidence behind its match score.
5. Create a tailored resume and optional cover letter in **Document studio**.
6. Prepare screening answers from verified facts.
7. Start automation in dry-run mode.
8. Review every field and upload before approving submission.

CareerPilot never bypasses CAPTCHA and must not answer legal attestations without you.

## Backup and restore

Create a backup with `.\scripts\backup.ps1`. Restore only from a verified file under
`data\backups` with `.\scripts\restore.ps1 -BackupPath <path>`.

## Troubleshooting

- `/health`: confirms that the API process is running.
- `/ready`: confirms that the database is reachable.
- `/diagnostics`: shows version, environment, database, and authentication state.
- `/docs`: interactive API documentation in local development.

Do not upload `.env`, databases, resumes, or browser artifacts to GitHub.

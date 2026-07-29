# Changelog

## Unreleased

- Add cursor-based offline-first synchronization with explicit conflict resolution.
- Add optional Gmail, Google Calendar, Google Drive, OneDrive, Dropbox, and LinkedIn connections.
- Add least-privilege shared workspaces and third-party webhook foundations.

## 1.0.0 - 2026-07-29

CareerPilot v1 delivers the complete local-first application workflow:

- verified career profile and deterministic resume ingestion;
- optional Ollama-backed profile intelligence;
- job discovery, normalization, deduplication, and explainable matching;
- evidence-backed resume, cover-letter, and screening-answer generation;
- supervised application automation with mandatory review gates;
- lightweight application tracking and analytics;
- security, diagnostics, backups, containers, and CI foundations;
- first-run onboarding, consolidated help, and release-readiness guidance.

Known limitations:

- ATS websites change frequently; always use dry-run mode first.
- CAPTCHA solving is intentionally unsupported.
- Desktop installers are not included in v1; the supported package is the local web
  application or Docker Compose deployment.
- SQLite is intended for a single-user installation.

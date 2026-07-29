# Deployment Guide

## Supported v1 packages

CareerPilot v1 supports:

- native local development through the PowerShell scripts; and
- a production-style Docker Compose installation.

Desktop installer generation is intentionally deferred. Tauri is the preferred future
wrapper because the existing React UI and local HTTP API can be reused.

## Production configuration

Set `CAREERPILOT_ENVIRONMENT=production`, enable authentication, provide a secret of at
least 32 random characters, restrict CORS origins and trusted hosts, and store the
SQLite data directory on a persistent volume.

Run `docker compose up --build -d`. Verify `/health`, `/ready`, and `/diagnostics`.
Create a backup before every upgrade and test restoration on a copy before release.

## Telemetry

CareerPilot sends no third-party product telemetry. The local `/metrics` endpoint is
controlled by `CAREERPILOT_METRICS_ENABLED`; keep it private when exposed on a network.

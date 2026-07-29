# Coding Standards

## Python

- Target Python 3.12 and use modern type annotations.
- Keep API routes declarative and delegate behavior to services.
- Keep database access in repositories or intentionally scoped services.
- Validate boundaries with Pydantic.
- Use timezone-aware UTC timestamps.
- Prefer explicit domain types over unstructured dictionaries.

## TypeScript and React

- Keep strict TypeScript enabled.
- Prefer accessible semantic HTML.
- Keep server state in API-oriented hooks/services and UI state local.
- Model API payloads explicitly; avoid `any`.
- Every asynchronous view needs loading, empty, error, and success states.

## Database

- Every schema change requires an Alembic migration and migration test.
- Migrations must be forward-safe and document destructive or long-running operations.
- Avoid storing secrets and large personal artifacts in relational tables.

## Security and privacy

- Treat resume and application data as sensitive.
- Use synthetic test fixtures.
- Reject unsafe defaults and fail closed around permissions.
- Human approval remains mandatory for signatures, legal attestations, and final submission.

## Testing

- Unit-test business rules and parsers.
- Add API integration tests for endpoint contracts.
- Add regression tests for every defect.
- Use saved, sanitized page fixtures for ATS automation.
- Keep live-site smoke tests opt-in.


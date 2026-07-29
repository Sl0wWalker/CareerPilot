# CareerPilot v1 Validation and Release Readiness Report

Date: 2026-07-29  
Audited commit: `221e7a5` (`release(v1): polish, package, and launch CareerPilot v1`)

## Recommendation

**Public beta: NO-GO.**  
**Local, single-user alpha: CONDITIONAL GO.**

The core application builds and its current automated checks pass. The audit fixed the
production authentication flow and two dependency vulnerabilities in validation tooling.
However, the repository does not yet contain the end-to-end, accessibility, performance,
live-browser, backup/restore, and packaged-deployment evidence required to call v1 ready for
a public beta.

## Validation performed

| Area | Result |
|---|---|
| Backend unit/integration suite | 30 passed |
| Frontend component suite | 1 passed |
| Backend coverage | 81% overall |
| Python lint | Passed |
| Frontend lint/format | Passed after fixes |
| TypeScript production build | Passed |
| npm dependency audit | 0 vulnerabilities |
| Python dependency audit | 0 known vulnerabilities after upgrades |
| Alembic full downgrade/upgrade chain | Passed |
| Docker Compose build/runtime | Not run: Docker is not installed in the audit environment |
| End-to-end browser suite | Not present |
| Accessibility automation | Not present |
| Performance/load suite | Not present |
| Browser compatibility matrix | Not present |
| Backup/restore destructive rehearsal | Not run against disposable packaged deployment |

## Findings

### Critical

#### C-1: Production UI could not authenticate

**Status: Fixed.**  
**Effort: completed.**

Production Compose enables API authentication, but the React application previously had no
login, registration, token persistence, or authenticated request handling. Every protected
request therefore returned HTTP 401.

The fix adds a first-run owner registration/login gate, token persistence, and authorization
headers for application requests.

#### C-2: Public registration remained open after owner creation

**Status: Fixed.**  
**Effort: completed.**

Anyone able to reach the production API could create another account. Because feature APIs
are protected only by authentication middleware and operate on shared single-user data, that
account could access the owner's career data. Registration now closes after the first owner
account is created, with regression coverage.

### High

#### H-1: Claimed release validation suites do not exist

**Status: Open.**  
**Estimated effort: 4-7 days.**

There is no Playwright end-to-end suite for the web application, no automated accessibility
suite, and no performance/load suite. Browser automation code itself has zero test coverage.
The public beta gate must include representative flows for onboarding, resume ingestion,
matching, document approval, authentication, and stop-before-submit automation.

#### H-2: Frontend regression coverage is insufficient

**Status: Open.**  
**Estimated effort: 2-4 days.**

Only one frontend test exists for a multi-workspace application. Frontend coverage cannot be
generated because `@vitest/coverage-v8` is not installed. Authentication, errors, loading
states, resume review, job discovery, documents, automation, and tracking lack regression
tests.

#### H-3: Packaged deployment has not been executed

**Status: Open.**  
**Estimated effort: 1-2 days after Docker is available.**

The Dockerfiles and Compose definition are plausible, but the images were not built or run
because Docker is not installed in the audit environment. Validate container health,
migrations, authentication, CORS, persistence, restart behavior, and frontend-to-API
connectivity before beta.

#### H-4: Backup and restore need a disposable end-to-end rehearsal

**Status: Open.**  
**Estimated effort: 1 day.**

Scripts and an API backup path exist, but there is no automated proof that a populated
database can be backed up, replaced, restored, migrated, and queried without data loss.

### Medium

#### M-1: Several important backend paths have low or zero coverage

**Status: Open.**  
**Estimated effort: 3-5 days.**

Notable examples are browser runner (0%), background operations (0%), AI providers (26%),
automation repositories (34%), document repositories (36%), and automation APIs (39%).
Overall backend coverage is 81%, but the least-tested code includes the riskiest integrations.

#### M-2: In-memory rate limiting and background jobs are single-process only

**Status: Accepted for local alpha; open for public beta.**  
**Estimated effort: 2-4 days.**

Rate-limit counters and job state disappear on restart and are not shared across workers.
Keep one API process for local use or replace these with durable storage before scaling.

#### M-3: Observability is process-local

**Status: Accepted for local alpha; open for public beta.**  
**Estimated effort: 1-2 days.**

Metrics are mutable in-process counters without persistence, labels, or multi-worker
aggregation. They are suitable for diagnostics, not production monitoring.

#### M-4: Dependency lock/reproducibility is incomplete for Python

**Status: Open.**  
**Estimated effort: 0.5-1 day.**

Python dependencies use version ranges without a committed lock file. A future install can
resolve to different versions. Adopt a lock workflow and run vulnerability checks in CI.

### Low

#### L-1: Test client emits an upstream deprecation warning

**Status: Open.**  
**Estimated effort: less than 0.5 day after upstream compatibility is confirmed.**

FastAPI's test client reports a Starlette/httpx deprecation warning. It does not currently
break tests.

#### L-2: API versioning is inconsistent

**Status: Open.**  
**Estimated effort: 1-2 days.**

Release/auth endpoints use `/api/v1`, while domain endpoints are unversioned. Standardize
before publishing a stable external API.

## Fixes applied by this audit

- Added a production authentication gate to the React entry point.
- Added owner registration and login handling with persisted bearer tokens.
- Added authorization headers to application requests after authentication.
- Closed registration after the first owner account is created.
- Added a backend regression assertion for registration closure.
- Raised the supported pytest floor to a vulnerability-fixed release.
- Upgraded pip in the production API image before dependency installation.

## Required public-beta exit criteria

1. Build and run the Compose stack from a clean machine.
2. Complete authenticated onboarding and all primary workflows in that stack.
3. Add Playwright end-to-end tests for critical user journeys.
4. Add automated accessibility checks with zero serious/critical violations.
5. Add a basic load test and define latency/error budgets.
6. Exercise Greenhouse, Lever, Ashby, Workday, and generic automation fixtures; prove final
   submission cannot occur without explicit approval.
7. Rehearse backup and restore on a disposable populated deployment.
8. Add meaningful frontend coverage and raise coverage on risky backend integrations.
9. Run dependency and secret scans in CI.
10. Resolve all Critical and High findings, then repeat this audit.


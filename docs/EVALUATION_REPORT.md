# CareerPilot Independent Evaluation

Date: 2026-07-29  
Evaluated commit: `8d3fb42`  
Scope: repository after milestones M0-M20

## Executive recommendation

| Release target | Recommendation |
|---|---|
| Open-source release | **Conditional GO**, clearly labeled experimental/local alpha |
| Personal local use | **Conditional GO** for profile, resume, job ingestion, and analysis workflows |
| Public beta | **NO-GO** |
| Production deployment | **NO-GO** |
| Enterprise adoption | **NO-GO** |

CareerPilot is a coherent prototype with a working API, database migrations, broad domain
coverage, and a buildable React interface. It is not the production-grade platform implied by
the M0-M20 roadmap. Several headline capabilities are interfaces, CRUD foundations, or
deterministic demonstrations rather than complete systems. The safest path is to narrow the
product back to its original job-application workflow, validate that workflow end to end, and
remove or explicitly label speculative platform modules.

## Validation results

| Check | Result |
|---|---|
| Backend tests | 56 passed |
| Backend coverage | 84% overall |
| Python lint | Passed |
| Python dependency consistency | Passed |
| Frontend tests | 1 passed |
| Frontend lint | Passed |
| TypeScript/production build | Passed |
| Fresh Alembic upgrade through M19 | Passed |
| API runtime smoke test | `/health`, `/ready`, and `/diagnostics` passed |
| Frontend dependency audit | Not completed: registry access denied in evaluation sandbox |
| Frontend peer check | Failed: two `@emnapi/*` peer mismatches |
| Browser end-to-end tests | Not present |
| Accessibility automation | Not present |
| Performance/load tests | Not present |
| Docker build/runtime | Not executed; Docker unavailable |
| Live ATS validation | Not present |
| Live Ollama quality evaluation | Not present |

The backend coverage percentage overstates confidence because model declarations are counted as
fully covered while integration-heavy paths are weak or untested. Automation runner and
background operations have 0% coverage; AI providers have 26%; automation APIs have 39%; and
document APIs have 41%. The single frontend test is not meaningful coverage for 18 workspaces.

## Readiness scorecard

| Area | Score | Assessment |
|---|---:|---|
| Architecture | 5/10 | Consistent layering, but severe scope expansion in one service |
| Code quality | 6/10 | Typed, lint-clean, readable; many shallow modules |
| Security | 5/10 | Basic auth and safe defaults exist; production model is incomplete |
| Testing | 4/10 | Good unit baseline, inadequate UI/integration/automation evidence |
| Performance | 3/10 | No benchmarks; synchronous network/AI calls and SQLite constrain scale |
| AI quality | 3/10 | Provider integration exists; no task benchmark or hallucination evaluation |
| UX/accessibility | 4/10 | Buildable UI, but only one test and no accessibility audit |
| Operations | 4/10 | Migrations and health checks work; deployment/restore not rehearsed |
| Maintainability | 5/10 | Clear naming, but 20 milestones created architectural drift and excess surface |
| Documentation | 6/10 | Extensive milestone notes; capability claims need calibration |
| Commercial viability | 3/10 | Unvalidated product, sources, automation reliability, and user demand |

## Prioritized findings

### Critical

#### C-1: Application automation does not execute browser automation

`POST /automation/runs/{id}/execute` updates database state and records a completed browser step,
but it never invokes `PlaywrightRunner`. It can report `dry_run_complete` or `running` without
opening or filling a page. This is the primary product promise and must not be represented as
working autofill.

**Risk:** users may trust a false completion state; the core Jobright-like capability is absent.  
**Required action:** connect execution to an isolated browser worker, add saved-page fixtures and
live supervised tests, persist checkpoints, prove uploads and validation, and retain a hard
stop-before-submit invariant.

#### C-2: Roadmap completion is not evidence of product completion

M12-M20 add cloud sync, coaching, platform APIs, enterprise, marketplace, autonomous
intelligence, mobile/global foundations, research, and governance in a repository with 274
tracked files and 56 backend tests. Many features are schemas, database records, deterministic
services, or UI panels rather than operational products.

**Risk:** materially misleading release claims and an unmaintainable product surface.  
**Required action:** publish a capability matrix with `implemented`, `prototype`, `foundation`,
and `planned` states. Remove speculative modules from the default navigation or place them
behind an explicit experimental flag.

### High

#### H-1: No end-to-end proof of the core user journey

There is no browser suite proving resume import, fact approval, job ingestion, matching,
document generation, application preparation, and supervised autofill as one workflow.

#### H-2: ATS support is overstated

Greenhouse, Lever, and Ashby have job-feed integrations. Workday ingestion expects an arbitrary
JSON URL and generic keys; it is not a robust Workday connector. ATS adapters expose selectors
but do not implement tested platform-specific flows.

#### H-3: Frontend regression protection is effectively absent

Only one frontend test exists. Authentication, all major workspaces, failures, accessibility,
and responsive behavior are unprotected.

#### H-4: AI correctness and safety are unmeasured

The provider layer supports Ollama and hosted providers, but there is no versioned evaluation
dataset for extraction accuracy, evidence fidelity, structured-output reliability, or
hallucination rate. Resume and application decisions must not rely on provider availability
alone.

#### H-5: Enterprise and multi-tenant claims conflict with the runtime architecture

SQLite, in-process rate limiting, in-memory background jobs, process-local metrics, and a
single FastAPI deployment are appropriate for local use, not horizontal or enterprise scale.

#### H-6: Production packaging has not been demonstrated

Docker definitions exist, but there is no clean-machine deployment evidence, browser-to-API
connectivity proof, restart/persistence rehearsal, or populated backup/restore test.

### Medium

#### M-1: API versioning and ownership boundaries are inconsistent

Platform and authentication APIs use `/api/v1`; most domain routes are unversioned. Several
domain services still assume one shared local profile while later modules introduce users,
organizations, and workspaces.

#### M-2: Synchronous I/O limits reliability

Job-provider and AI calls use synchronous `httpx` inside request handling. Long AI calls and
source syncs can consume server workers. The in-memory job pool is non-durable and untested.

#### M-3: Database scope is disproportionate to validated behavior

Nineteen migrations create a large domain surface before the original application flow is
validated. This increases migration, privacy, and compatibility risk.

#### M-4: Dependency reproducibility is incomplete

Python uses bounded ranges without a committed lock. Frontend installation reported a
deprecated `@testing-library/jest-dom` release and peer mismatches. The security audit could not
reach the registry in this environment.

#### M-5: License file is an abbreviated notice, not the full Apache-2.0 license text

The repository states Apache-2.0 but `LICENSE` contains only the short notice. Replace it with
the complete canonical license before release.

#### M-6: Existing validation documentation is stale

`docs/VALIDATION_REPORT.md` evaluates the M10 release commit, not the current M20 repository.
Its 30-test and module findings no longer describe the present tree.

### Low

#### L-1: Agent instructions were frozen at Milestone 0

Fixed in this evaluation by replacing obsolete milestone boundaries with the current
architecture and a validation-first rule.

#### L-2: Coverage artifacts were not ignored

Fixed by ignoring `.coverage` and `coverage.xml`.

#### L-3: Upstream FastAPI test-client warning remains

The test suite emits a Starlette/httpx deprecation warning. Track upstream compatibility before
changing dependencies.

## Architecture and code-quality assessment

Strengths:

- Clear API/service/repository/model separation in core modules.
- Pydantic schemas and SQLAlchemy typing are used consistently.
- Fresh migrations apply successfully.
- Security defaults require authentication and a strong secret in production.
- Resume parsing is modular and comparatively well tested.
- Matching exposes deterministic components rather than only an opaque LLM score.
- Final submission is not implemented, avoiding accidental unattended submission.

Weaknesses:

- The modular monolith absorbed unrelated product categories without validating the core loop.
- Later modules often add data models and endpoints without the infrastructure implied by their
  names.
- Integration boundaries are synchronous and minimally tested.
- The frontend is organized as large workspace components with almost no regression coverage.
- The current architecture cannot support the advertised multi-tenant/enterprise scale.

No meaningful duplicated code or dead-code proof was established by static inspection alone,
but broad low-coverage services and unused infrastructure foundations should be treated as
candidates for removal until exercised by an end-to-end flow.

## Security and privacy risk

Positive controls include password hashing, signed bearer tokens, registration closure after
owner creation, trusted-host middleware, restrictive response headers, local defaults, and
ignored personal-data paths.

Remaining risks:

- Access tokens are stored in `localStorage`, increasing impact from any future XSS.
- API authentication is coarse; later shared-workspace data needs systematic row-level
  authorization tests.
- Webhook secrets and connected-account references need a defined encrypted-secret store.
- No automated secret scan or SAST evidence was produced locally.
- Resume/browser artifacts require retention, deletion, and backup-encryption policies.
- Metrics and diagnostics are public paths and must never expose personal or operational
  secrets as they evolve.

## Performance and scalability

No load or latency budgets exist. SQLite and single-process caches are reasonable for a
personal local alpha. They are blockers for multi-user production. Before scaling, measure:

- job sync throughput and external-source failure behavior;
- Ollama latency by model and prompt size;
- resume parse/render time;
- database growth and query plans;
- browser automation memory, retries, and concurrency;
- frontend initial load and workspace rendering.

## Commercial viability

There is no evidence yet for match quality, application completion rate, interview conversion,
user retention, ATS coverage, or willingness to pay. The broad platform roadmap dilutes the
valuable differentiator: truthful, local-first, supervised job application assistance.

The highest-value commercial experiment is a narrow private alpha with 3-5 users applying to
Greenhouse and Lever roles. Measure successful form completion, time saved, correction rate,
unsupported fields, resume factuality, and interview conversion. Do not invest further in
enterprise, marketplace, mobile, or autonomous-coach features until this loop is reliable.

## Highest-impact next improvements

1. **Make one application workflow real:** Greenhouse first, visible browser, deterministic
   fields, upload, review, and stop before submit.
2. **Add an end-to-end test laboratory:** sanitized Greenhouse/Lever forms plus Playwright tests
   for the full profile-to-review journey.
3. **Publish an honest capability matrix:** distinguish production behavior from prototypes and
   foundations.
4. **Hide speculative modules by default:** return the UI to Profile, Resumes, Jobs, Matching,
   Documents, and Apply.
5. **Create AI evaluation fixtures:** factuality, evidence coverage, extraction accuracy,
   structured-output success, latency, and model comparison.
6. **Raise frontend coverage:** authentication and each critical workflow before visual polish.
7. **Rehearse packaged deployment and restore** on a clean, disposable environment.
8. **Only then run a small private alpha** and let observed failures define the next roadmap.

## Changes made during this evaluation

- Updated `AGENTS.md` to remove obsolete M0-only instructions and require honest capability
  labeling.
- Added coverage outputs to `.gitignore`.
- Added this independent evaluation report.

No product features were added and no high-risk architecture changes were attempted.

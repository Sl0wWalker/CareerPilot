# Governance

## Mission

CareerPilot helps people create high-quality, truthful job applications with local-first AI and
explicit human control.

## Decision making

Routine changes use pull-request consensus. Maintainers resolve disagreements using, in order:

1. user safety and privacy;
2. documented product scope;
3. compatibility guarantees;
4. tests and measured evidence;
5. simplicity and long-term maintenance cost.

Cross-cutting or irreversible decisions require an ADR. Security response may temporarily bypass
normal public discussion.

## Releases

Releases follow semantic versioning and `docs/RELEASE_POLICY.md`. `main` must remain releasable.
Automated checks are required before merge. Release notes must call out migrations, deprecations,
security changes, and user-visible behavior.

## Roadmap

The roadmap is maintained in `docs/ROADMAP.md`. Inclusion is not a delivery promise. Issues must
state user value and acceptance criteria before entering an active milestone.

## Changes to governance

Governance changes require a pull request, an ADR when responsibilities materially change, and a
minimum seven-day comment period once the project has multiple active maintainers.


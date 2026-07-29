# Release and Dependency Policy

## Versioning

CareerPilot uses semantic versioning. Changes are recorded under `Unreleased` in `CHANGELOG.md`.

- Patch: compatible fixes and security updates.
- Minor: compatible features and deprecations.
- Major: intentional compatibility breaks with migration guidance.

## Release process

1. All quality gates pass on `main`.
2. Changelog and migration guidance are complete.
3. Dependency and security review passes.
4. Backup and restore checks pass for migration-bearing releases.
5. A signed `vX.Y.Z` tag triggers release artifact generation.
6. Artifacts and checksums are attached to a GitHub release.

## Dependencies

Dependabot opens weekly grouped updates. Security updates receive priority. Major dependency
upgrades require compatibility notes and targeted regression tests. Abandoned or unmaintained
dependencies should be replaced when they affect security or platform support.


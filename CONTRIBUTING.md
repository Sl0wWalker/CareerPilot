# Contributing to CareerPilot

Thank you for helping improve CareerPilot. The project is local-first, privacy-first, and
human-controlled. Contributions must preserve those properties.

## Start here

1. Read `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `docs/GOVERNANCE.md`.
2. For substantial work, open an issue before implementation.
3. Create a focused branch from `main`.
4. Run `.\scripts\setup.ps1`, then `.\scripts\quality.ps1`.
5. Submit a pull request using the repository template.

## Engineering standards

- Keep routers thin; business logic belongs in services and persistence in repositories.
- Maintain strict Python and TypeScript typing.
- Add tests for behavior changes and regression tests for fixes.
- Do not log resumes, candidate facts, credentials, browser sessions, or AI prompts containing
  personal data.
- AI output must not write directly to verified career facts.
- Application submission and legal attestations require explicit user approval.
- Public API changes must follow `docs/API_COMPATIBILITY.md`.
- Architectural changes require an ADR under `docs/adr/`.

## Commit and pull request expectations

Use concise conventional commits such as:

```text
feat(resume): add deterministic section detector
fix(automation): preserve review checkpoint
docs(governance): clarify deprecation policy
```

Pull requests must explain the user impact, tests run, privacy/security impact, and compatibility
impact. Keep unrelated changes out of the same pull request.

## Adding a plugin

Plugins must follow `docs/PLUGIN_GOVERNANCE.md`, declare capabilities and permissions, include
tests, and avoid undisclosed network access. Marketplace inclusion is a separate review from core
repository acceptance.

## Architecture decisions

Copy `docs/adr/0000-template.md`, assign the next number, and record context, decision,
consequences, and alternatives. Accepted ADRs are immutable; supersede them with a new ADR.


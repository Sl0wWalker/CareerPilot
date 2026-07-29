# Security Policy

## Supported versions

Security fixes are provided for the latest minor release of the current major version. Critical
fixes may be backported to the immediately previous minor release at maintainer discretion.

## Reporting a vulnerability

Do not open a public issue. Use GitHub's private vulnerability reporting feature for this
repository. Include affected versions, reproduction steps, impact, and any proposed mitigation.

The project targets:

- acknowledgement within 3 business days;
- initial triage within 7 business days;
- coordinated disclosure after a fix is available.

Never include real resumes, credentials, cookies, tokens, or applicant data in a report. Use
synthetic fixtures.

## Response process

Maintainers will assign severity, reproduce the issue, prepare a private fix, add regression tests,
rotate affected secrets when applicable, publish an advisory, and credit reporters who consent.
Security releases follow semantic versioning but may omit details until users can upgrade safely.

## Scope

Reports concerning authentication, authorization, browser automation, plugin sandboxing, prompt
injection, sensitive-data exposure, supply-chain integrity, and unsafe application submission are
in scope.


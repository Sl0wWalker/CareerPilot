# Plugin Governance

Plugins are untrusted extensions and must declare:

- package identity, publisher, version, and compatible CareerPilot range;
- capabilities and requested permissions;
- network destinations and data categories accessed;
- dependencies and license;
- update channel and support contact.

## Review requirements

Core-distributed plugins require automated contract tests, permission review, dependency audit,
synthetic fixtures, and maintainer approval. Plugins may not bypass human approval gates, access
password fields, exfiltrate career data, conceal network calls, or weaken audit logging.

Security incidents may cause immediate quarantine or revocation. Breaking plugin API changes use a
new contract major version and a documented migration window.

Marketplace ranking or inclusion never implies a security guarantee; the UI must display publisher,
permissions, and trust status before installation.


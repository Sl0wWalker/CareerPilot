# Enterprise deployment

CareerPilot remains runnable on one machine. For a multi-node enterprise
deployment, use the following topology:

```text
TLS ingress / load balancer
  ├─ stateless CareerPilot API replicas
  ├─ static web application
  ├─ PostgreSQL primary plus managed backups
  ├─ distributed task broker and workers
  ├─ shared encrypted artifact storage
  └─ metrics, logs, traces, and SIEM export
```

## Required production controls

1. Replace SQLite with PostgreSQL and test every Alembic migration in staging.
2. Replace the database-local agent runner with a durable broker and idempotent
   workers.
3. Store signing keys, SSO secrets, API credentials, and webhook secrets in an
   external secret manager.
4. Enforce TLS, secure cookies, trusted proxy configuration, and strict CORS.
5. Validate OIDC discovery/JWKS or SAML metadata and assertions with a
   security-reviewed identity library.
6. Back up the database and artifact store; regularly test restore procedures.
7. Export audit events to append-only storage with an organization retention
   policy.
8. Apply per-tenant quotas at API and worker boundaries.
9. Use tenant-aware metrics without placing personal data in labels or logs.
10. Run dependency, container, SAST, DAST, and access-control testing before
    production rollout.

## Horizontal scaling contract

API replicas must remain stateless. Every job uses an idempotency key, tenant
scope, retry policy, and terminal status. Workers must acquire durable leases,
renew them while active, and safely release or expire abandoned work.

## SSO rollout

Keep each connection disabled until metadata and redirect URIs are validated.
Test login, logout, token expiry, group-to-role mapping, emergency local access,
and tenant isolation with a staging identity provider.

## Licensing and billing

The enterprise license table is a neutral entitlement record. Connect billing
only through an M14 plugin. Webhooks must be signed and idempotent; billing
failures must never delete customer data.

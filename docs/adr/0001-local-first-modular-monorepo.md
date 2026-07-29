# ADR-0001: Local-first modular monorepo

- Status: Accepted
- Date: 2026-07-29
- Decision owners: maintainers

## Context

CareerPilot handles highly sensitive career and application information while spanning Python AI
and automation services, a React interface, SDKs, and deployment assets.

## Decision

Keep a modular monorepo with a local FastAPI service, React client, SQLite default, local file
storage, Ollama default provider, explicit service/repository boundaries, and replaceable external
provider interfaces.

## Consequences

Local personal use remains free and private. Shared quality gates and coordinated changes are
straightforward. The repository is large, so ownership boundaries and focused pull requests are
important. Cloud and multi-user capabilities remain optional extensions.

## Alternatives considered

Separate repositories increased coordination cost. A cloud-first architecture conflicted with the
privacy and free-operation goals. A single unstructured application would make adapters and AI
providers difficult to replace.


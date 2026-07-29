# API Compatibility and Deprecation

CareerPilot's public API is versioned under `/api/v1`.

## Guarantees

Within a major version:

- existing fields and endpoints are not removed;
- required request fields are not added without a compatible default;
- enum values may be added, so clients must tolerate unknown values;
- response fields may be added;
- bug and security fixes may tighten invalid-input handling.

Experimental endpoints must be labeled and carry no compatibility guarantee.

## Deprecation

Deprecated behavior must:

1. be documented in the changelog and API documentation;
2. include a replacement and migration guidance;
3. emit an HTTP `Deprecation` header where practical;
4. remain available for at least one minor release and 90 days;
5. be removed only in a major release, except for urgent security risk.

Database migrations, SDKs, webhooks, and plugin contracts follow the same policy.


# In-Process Policy Engine

The runtime now includes an exact-match, deny-by-default policy evaluator.

## Rule fields
- Authenticated principal identifier
- Capability identifier
- Operation
- Explicit allow/deny effect
- Unique rule ID and reason

## Evaluation
- No exact matching allow rule means deny.
- An explicit deny overrides a matching allow.
- No wildcard permissions are supported in this initial version.
- Dispatch evaluates policy itself and replaces any caller-supplied request decision before provider execution.

## Security boundary
The principal identifier must be supplied by a separately authenticated identity layer. The current library does not authenticate users or service identities, persist policy rules, support tenant/resource scopes, or provide policy administration. Do not expose adapter execute methods directly to untrusted callers. This is an in-process authorization primitive, not production authentication or a complete authorization service.

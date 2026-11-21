# Universal Engine / Engineer

## EUPN — Universal Private Network

EUPN currently provides an initial Python 3.11+ node transport implementation. It is **not yet a production-ready private network**.

### Implemented in this branch

- Mutual TLS; TLS 1.2 minimum and CA validation on both sides.
- Peer identity taken from a URI Subject Alternative Name of the form `spiffe://eupn/<node-id>`; Common Name is not used for authorisation.
- Explicit peer allowlisting and sender identity binding to the authenticated certificate.
- Length-prefixed JSON envelopes with a configurable maximum frame size and finite-JSON validation.
- Recipient/envelope validation, read deadlines and acknowledgement matching.
- SQLite inbox/outbox, WAL, full synchronous commits and duplicate-message suppression.
- Persistent outbound queue with automatic retries when peer routes are configured; capped exponential backoff and retained failure details.
- CLI configuration for peer routes and retry interval.
- Unit tests plus a real two-node mutual-TLS delivery integration test using ephemeral test certificates.

### Certificate requirements

Issue a unique certificate and private key for every node from a private CA. Each node certificate must contain:
- A URI SAN exactly matching `spiffe://eupn/<node-id>`.
- A DNS SAN matching the hostname used by the connecting peer (the client also performs normal TLS hostname validation).
- Extended key usages for both server and client authentication when nodes initiate connections in both directions.

Never commit production private keys or CA private keys. Provision and rotate them through a dedicated secrets/certificate-management system. Keep listeners firewalled to known peers.

### Install and test

Requires Python 3.11+ and OpenSSL for the certificate-backed integration test.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
```

### Start a node

```sh
eupn-node --node-id node-a --host 0.0.0.0 --port 7443 \
  --cert certs/node-a.crt --key certs/node-a.key --ca certs/ca.crt \
  --allowed-peers node-b --peer-routes node-b=peer-b.example:7443 \
  --database var/node-a.db
```

For bidirectional communication, configure reciprocal allowlists and routes on each node. The route hostname must match the remote certificate DNS SAN.

### Production gate — still outstanding

Do not expose this build as a production network yet. The following remain required:
- Independent security review, threat model and protocol review.
- Certificate issuance, rotation, revocation and emergency key-compromise procedures.
- Authenticated peer enrollment/discovery and governed route updates.
- Explicit application-level authorisation, message schemas/versioning and payload limits by type.
- Retry policy review, poison-message/dead-letter handling, delivery observability and back-pressure.
- Database backup/restore, migration strategy, disk-full handling and operational recovery drills.
- Rate limiting, connection/concurrency limits, abuse protection and load/soak testing.
- Multi-node topology tests, network-partition/restart tests and failure-injection tests.
- Hardened deployment manifests, firewall policy, secrets management, monitoring, alerting and incident runbooks.
- CI security/dependency scanning and independent release approval.

A passing CI run proves only that the included automated tests passed. It does not certify production readiness or deploy a live network.

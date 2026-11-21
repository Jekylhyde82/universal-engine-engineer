# Universal Engine / Engineer

## EUPN — Universal Private Network

The first EUPN node foundation is now in this repository. It is a Python 3.11+
service for certificate-authenticated node-to-node messaging.

### Implemented

- Mutual TLS, TLS 1.2 minimum; both peers present certificates.
- CA-chain validation and explicit allowlisting by certificate common name.
- Sender identity must match the authenticated TLS certificate.
- Length-prefixed JSON envelopes with a 1 MiB default frame limit.
- Recipient and envelope validation, plus bounded read deadlines.
- SQLite inbox/outbox using WAL and full synchronous commits.
- Duplicate-message suppression; the receiver commits before returning ACK.
- CLI entry point, health information, and automated protocol/storage tests.

### Requirements and security

Use a private CA and unique certificate/key pair for every node. A certificate
common name must equal that node's configured ID. Each node must explicitly
allowlist the remote node IDs it accepts. No default certificates or shared
private keys are included. Keep private keys secret and do not expose the
listener until certificates, firewall rules, and peer allowlists are configured.

### Install and test

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
~~~

### Start a node

~~~sh
eupn-node --node-id node-a --host 0.0.0.0 --port 7443 \
  --cert certs/node-a.crt --key certs/node-a.key --ca certs/ca.crt \
  --allowed-peers node-b --database var/node-a.db
~~~

The remote node must have a certificate issued by the same trusted CA, with
common name node-b, and must allow node-a.

### Remaining work before production

This is a substantial first transport foundation, not a production-ready
private network. Peer discovery, certificate provisioning and rotation,
automated outbox retries, multi-peer routing, application APIs, network policy,
observability, deployment hardening, and independent multi-node integration
testing remain outstanding. Failed outbound messages remain queued, but retry
scheduling is not yet implemented.

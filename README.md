# Secure Python Agent + MCP (mTLS + OPA)

Portable reference deployment: Docker Compose works on a laptop or Linux VM.
Kubernetes manifests are intentionally a later deployment adapter; the application
and policy model do not depend on Docker.

## Security design

- Nginx terminates external mTLS and validates client certificates against the configured CA.
- Nginx overwrites `X-Client-Cert` with its verified peer certificate.
- MCP app is not published; only Nginx can reach it on a private Docker network.
- The app independently checks certificate validity, CA signature, clientAuth EKU and exact URI SAN.
- OPA makes fail-closed per-tool authorization decisions.
- Agent private key is mounted at runtime, never copied into an image.

This proxy-header trust design assumes the MCP container is reachable ONLY from the trusted
Nginx container. Do not publish MCP/OPA ports, do not attach untrusted workloads to the
backend network, and do not trust client-supplied identity headers. For higher assurance,
use mTLS between Nginx and MCP too, or terminate mTLS directly in an ASGI server that
exposes verified peer certificates.

## Quick start (development only)

Requires Docker Engine + Compose plugin and OpenSSL.

```bash
chmod +x scripts/*.sh
./scripts/generate-dev-pki.sh
cp .env.example .env
docker compose -f deployment/docker/docker-compose.yml up --build -d
```

The demo endpoint is `https://localhost:xxxx/mcp`. The demo CA key is intentionally
created locally and MUST NOT be used in production.

Test TLS:
```bash
./scripts/test-mtls.sh
```

Install client dependencies locally and run:
```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-client.txt
python agent/mcp_client.py
```

## Production adaptation

1. Use offline Root CA + online Intermediate CA, SPIRE X.509-SVID, or a managed PKI.
2. Issue a server certificate with the real DNS name in SAN.
3. Issue a client certificate with one exact SPIFFE URI SAN, e.g.
   `spiffe://your-trust-domain/agent/primary`.
4. Configure `MCP_EXPECTED_SPIFFE_ID`, `MCP_ALLOWED_HOSTS`, and OPA policies.
5. Store keys in SPIRE Workload API / Vault / cloud KMS-backed secret manager.
6. Implement renewal and revocation/trust-bundle refresh. Short lifetime alone is not instant revocation.
7. Restrict firewall to the gateway port; protect SSH and Docker daemon.
8. Enable TLS/mTLS on proxy-to-app hop for higher assurance.
9. Add rate limits, request size limits, metrics, log shipping, backups, and incident response.

## Integrating your existing project

Keep your LLM and orchestration code. Replace its MCP transport setup with the pattern in
`agent/mcp_client.py`, using your actual endpoint and runtime-delivered certificate/key.
Replace demo tool bodies in `app/tools/` with your existing business logic. Every tool must
call `authorize_tool()` server-side before performing side effects. Never let the LLM
or client decide authorization.

## Notes

This is a reference scaffold. Pin dependency versions after validating them in your
environment and CI. MCP SDK APIs evolve; The included tests cover certificate parsing/identity and OPA policy behavior;
run the end-to-end TLS tests after starting the stack.

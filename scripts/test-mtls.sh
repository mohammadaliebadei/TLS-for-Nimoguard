#!/usr/bin/env bash
set -euo pipefail
BASE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE"
URL="https://localhost:8443/mcp"
echo "[1] Valid certificate: TLS must succeed (HTTP may be 200/400/405 depending on MCP probe)"
curl -skS --cacert pki/ca/root-ca.crt --cert pki/certs/agent.crt \
  --key pki/private/agent.key -o /dev/null -w "HTTP %{http_code}\n" "$URL" || true

echo "[2] No client certificate: handshake must fail"
if curl -sS --cacert pki/ca/root-ca.crt "$URL" -o /dev/null; then
  echo "FAIL: connection succeeded without client certificate"; exit 1
else echo "PASS: client certificate required"; fi

echo "[3] Trusted CA but wrong URI SAN: gateway TLS succeeds, app identity check returns 403"
curl -skS --cacert pki/ca/root-ca.crt --cert pki/certs/unauthorized.crt \
  --key pki/private/unauthorized.key -o /tmp/mtls-denied.txt -w "HTTP %{http_code}\n" "$URL" || true
cat /tmp/mtls-denied.txt || true

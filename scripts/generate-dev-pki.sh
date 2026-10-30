#!/usr/bin/env bash
set -euo pipefail
umask 077
mkdir -p pki/{ca,certs,private,csr}
chmod 700 pki/private

# Development-only root. Production must use offline root + intermediate CA or SPIRE.
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out pki/private/root-ca.key
openssl req -x509 -new -sha256 -days 3650 -key pki/private/root-ca.key \
  -subj "/CN=Development Agent Root CA" \
  -addext "basicConstraints=critical,CA:TRUE,pathlen:1" \
  -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -out pki/ca/root-ca.crt

issue() {
  name="$1"; cn="$2"; eku="$3"; san="$4"; days="$5"
  openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out "pki/private/$name.key"
  openssl req -new -sha256 -key "pki/private/$name.key" -subj "/CN=$cn" -out "pki/csr/$name.csr"
  printf 'basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature\nextendedKeyUsage=%s\nsubjectAltName=%s\n' \
    "$eku" "$san" > "pki/csr/$name.ext"
  openssl x509 -req -sha256 -days "$days" -in "pki/csr/$name.csr" \
    -CA pki/ca/root-ca.crt -CAkey pki/private/root-ca.key -CAcreateserial \
    -extfile "pki/csr/$name.ext" -out "pki/certs/$name.crt"
}
issue server localhost serverAuth "DNS:localhost,IP:127.0.0.1" 30
issue agent primary-agent clientAuth "URI:spiffe://example.internal/agent/primary" 1
issue unauthorized unknown-agent clientAuth "URI:spiffe://example.internal/agent/unknown" 1
chmod 600 pki/private/*.key
echo "Development PKI created. Never deploy pki/private/root-ca.key."

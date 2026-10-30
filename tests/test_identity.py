from pathlib import Path
from app.identity import load_and_verify_forwarded_cert

def test_agent_certificate_identity(monkeypatch):
    monkeypatch.setenv("CLIENT_CA_FILE", "pki/ca/root-ca.crt")
    pem = Path("pki/certs/agent.crt").read_text()
    identity = load_and_verify_forwarded_cert(pem)
    assert identity.spiffe_id == "spiffe://example.internal/agent/primary"
    assert len(identity.sha256_fingerprint) == 64

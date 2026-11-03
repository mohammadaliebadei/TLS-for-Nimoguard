import pytest
import requests

BASE = "https://localhost:8443/mcp"

def test_valid_client_cert_accepted():
    r = requests.get(f"{BASE}/health", cert=("pki/client.crt", "pki/client.key"), verify="pki/ca.crt", timeout=5)
    assert r.status_code == 200

def test_no_client_cert_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        requests.get(f"{BASE}/health", verify="pki/ca.crt", timeout=5)

def test_wrong_ca_rejected():
    with pytest.raises(requests.exceptions.SSLError):
        requests.get(f"{BASE}/health", cert=("pki/rogue-client.crt", "pki/rogue-client.key"), verify="pki/ca.crt", timeout=5)

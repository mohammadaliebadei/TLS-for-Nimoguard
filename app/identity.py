from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import unquote
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import ExtendedKeyUsageOID, ExtensionOID

@dataclass(frozen=True)
class WorkloadIdentity:
    spiffe_id: str
    serial: str
    sha256_fingerprint: str

_identity: ContextVar[WorkloadIdentity | None] = ContextVar("workload_identity", default=None)

def current_identity() -> WorkloadIdentity:
    value = _identity.get()
    if value is None:
        raise PermissionError("No authenticated workload identity in request context")
    return value

def load_and_verify_forwarded_cert(encoded_pem: str) -> WorkloadIdentity:
    """Verify the forwarded leaf certificate against the configured trust anchor.

    This reference supports a leaf directly signed by the configured CA. For an
    Intermediate CA hierarchy, use SPIRE or a full PKI path validator.
    """
    pem = unquote(encoded_pem)
    cert = x509.load_pem_x509_certificate(pem.encode("ascii"))
    ca_pem = open(os.environ.get("CLIENT_CA_FILE", "/run/pki/client-ca.crt"), "rb").read()
    ca = x509.load_pem_x509_certificate(ca_pem)

    now = datetime.now(timezone.utc)
    if not (cert.not_valid_before_utc <= now < cert.not_valid_after_utc):
        raise PermissionError("Client certificate is expired or not yet valid")

    # Verify signature/issuer relationship to the configured trust anchor.
    cert.verify_directly_issued_by(ca)
    if cert.issuer != ca.subject:
        raise PermissionError("Unexpected client certificate issuer")

    try:
        eku = cert.extensions.get_extension_for_oid(ExtensionOID.EXTENDED_KEY_USAGE).value
        if ExtendedKeyUsageOID.CLIENT_AUTH not in eku:
            raise PermissionError("Certificate is not valid for client authentication")
    except x509.ExtensionNotFound as exc:
        raise PermissionError("Missing Extended Key Usage") from exc

    san = cert.extensions.get_extension_for_oid(
        ExtensionOID.SUBJECT_ALTERNATIVE_NAME
    ).value
    uris = san.get_values_for_type(x509.UniformResourceIdentifier)
    if len(uris) != 1:
        raise PermissionError("Exactly one URI SAN is required")

    return WorkloadIdentity(
        spiffe_id=uris[0],
        serial=format(cert.serial_number, "x"),
        sha256_fingerprint=cert.fingerprint(hashes.SHA256()).hex(),
    )

class VerifiedProxyIdentityMiddleware:
    """Only safe behind private Nginx which overwrites X-Client-Cert."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        raw = headers.get(b"x-client-cert")
        if not raw:
            await self._reject(send, 401, b"client certificate required")
            return
        try:
            identity = load_and_verify_forwarded_cert(raw.decode("ascii"))
            expected = os.getenv(
                "MCP_EXPECTED_SPIFFE_ID",
                "spiffe://example.internal/agent/primary",
            )
            if identity.spiffe_id != expected:
                await self._reject(send, 403, b"workload identity not allowed")
                return
        except Exception:
            await self._reject(send, 401, b"invalid client certificate")
            return

        token = _identity.set(identity)
        try:
            await self.app(scope, receive, send)
        finally:
            _identity.reset(token)

    @staticmethod
    async def _reject(send, status, body):
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": body})

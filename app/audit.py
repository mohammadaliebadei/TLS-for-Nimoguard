import json
import logging
from datetime import datetime, timezone
from app.identity import current_identity

logger = logging.getLogger("security.audit")

def record(tool: str, outcome: str):
    identity = current_identity()
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "subject": identity.spiffe_id,
        "cert_serial": identity.serial,
        "cert_sha256": identity.sha256_fingerprint,
        "tool": tool,
        "outcome": outcome,
    }, separators=(",", ":")))

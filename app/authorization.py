import os
import httpx
from app.identity import current_identity

OPA_URL = os.getenv("OPA_URL", "http://opa:8181/v1/data/agent/allow")

async def authorize_tool(tool_name: str) -> None:
    """Fail-closed authorization. OPA errors deny access."""
    identity = current_identity()
    payload = {"input": {"subject": identity.spiffe_id, "action": tool_name}}
    timeout = httpx.Timeout(2.0, connect=1.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(OPA_URL, json=payload)
        response.raise_for_status()
        result = response.json()
    if result.get("result") is not True:
        raise PermissionError(f"Tool access denied: {tool_name}")

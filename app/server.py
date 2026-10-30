import os
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from app.identity import VerifiedProxyIdentityMiddleware
from app.tools.tools import register_tools

mcp = FastMCP("SecureAgentMCP", stateless_http=True)
register_tools(mcp)

hosts = [h.strip() for h in os.getenv("MCP_ALLOWED_HOSTS", "localhost").split(",") if h.strip()]
security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=hosts,
    allowed_origins=[],
)
app = mcp.streamable_http_app(transport_security=security)
app = VerifiedProxyIdentityMiddleware(app)

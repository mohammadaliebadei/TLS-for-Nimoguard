from mcp.server.fastmcp import FastMCP
from app.authorization import authorize_tool
from app.audit import record

def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def search_knowledge(query: str) -> str:
        """Search the knowledge base. Requires search_knowledge permission."""
        try:
            await authorize_tool("search_knowledge")
            record("search_knowledge", "allowed")
            # Replace this demo body with your retrieval implementation.
            return f"Demo search result for: {query}"
        except Exception:
            record("search_knowledge", "denied")
            raise

    @mcp.tool()
    async def create_report(title: str, body: str) -> str:
        """Create a report. Requires create_report permission."""
        try:
            await authorize_tool("create_report")
            record("create_report", "allowed")
            # Replace this demo body with your report persistence implementation.
            return f"Report accepted: {title}"
        except Exception:
            record("create_report", "denied")
            raise

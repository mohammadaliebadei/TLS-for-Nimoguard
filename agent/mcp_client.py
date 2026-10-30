"""Example MCP client. Adapt the transport factory to the pinned MCP SDK version."""
import asyncio
import os
import ssl
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    ctx = ssl.create_default_context(cafile=os.getenv("MCP_CA", "pki/ca/root-ca.crt"))
    ctx.load_cert_chain(
        certfile=os.getenv("MCP_CERT", "pki/certs/agent.crt"),
        keyfile=os.getenv("MCP_KEY", "pki/private/agent.key"),
    )
    async with httpx.AsyncClient(verify=ctx, timeout=httpx.Timeout(30, read=300)) as http:
        # Some MCP SDK releases expose an httpx_client_factory parameter;
        # confirm the signature for your pinned release.
        async with streamablehttp_client(
            os.getenv("MCP_URL", "https://localhost:8443/mcp"),
            httpx_client_factory=lambda: http,
        ) as (read_stream, write_stream, _):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                print([tool.name for tool in tools.tools])
                result = await session.call_tool(
                    "search_knowledge", {"query": "workload identity"}
                )
                print(result)

if __name__ == "__main__":
    asyncio.run(main())

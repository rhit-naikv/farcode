from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection

client = MultiServerMCPClient(
    {
        "context7": StdioConnection(
            transport="stdio",  # Local subprocess communication
            command="npx",
            # Absolute path to your math_server.py file
            args=[
                "-y",
                "@upstash/context7-mcp",
                "--api-key",
                "ctx7sk-6f5a59f1-f4d3-4132-adf7-b827c53e5875",
            ],
        ),
    }
)


async def get_mcp_tools():
    try:
        return await client.get_tools()
    except Exception as e:
        print(f"Warning: Could not get MCP tools: {e}")
        return []

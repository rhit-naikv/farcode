# Import community file tools
from typing import List

from langchain_community.tools import (
    CopyFileTool,
    DeleteFileTool,
    DuckDuckGoSearchRun,
    FileSearchTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadFileTool,
    WriteFileTool,
)
from langchain_core.tools import BaseTool

from tools.mcp import get_mcp_tools

from .secure_shell_tool import create_secure_shell_tool

# Cache for tool instances to avoid re-initialization
_cached_tools_list = None


async def get_tools() -> List[BaseTool]:
    """
    Initialize and return a list of available tools for the AI agent.

    Tools are cached after first initialization to avoid repeated object creation.

    Returns:
        List of initialized tool instances
    """
    global _cached_tools_list

    if _cached_tools_list is None:
        # Initialize the community file tools once
        _cached_tools_list = [
            ListDirectoryTool(),
            ReadFileTool(),
            WriteFileTool(),
            CopyFileTool(),
            MoveFileTool(),
            DeleteFileTool(),
            FileSearchTool(),
            create_secure_shell_tool(),
            DuckDuckGoSearchRun(),
        ]

        # Add MCP tools
        mcp_tools = await get_mcp_tools()
        _cached_tools_list.extend(mcp_tools)

    return _cached_tools_list

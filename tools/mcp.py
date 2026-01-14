"""Model Context Protocol (MCP) integration for loading external tools."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from rich.console import Console

# Console for warning/error output
_console = Console(stderr=True)

# Settings file path (can be overridden via environment variable)
SETTINGS_PATH = Path(
    os.environ.get("FARCODE_SETTINGS_PATH", Path.home() / ".farcode" / "settings.json")
)


def load_mcp_config() -> List[Dict[str, Any]]:
    """
    Load MCP server configuration from settings file.

    Supports two formats:
    - Array format: [{"name": "server1", "command": "...", "args": [...]}]
    - Object format: {"server1": {"command": "...", "args": [...]}}

    Returns:
        List of server configuration dictionaries
    """
    if not SETTINGS_PATH.exists():
        return []

    try:
        with open(SETTINGS_PATH, "r") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        _console.print(
            f"[yellow]Warning: Invalid JSON in MCP settings file: {e}[/yellow]"
        )
        return []
    except OSError as e:
        _console.print(
            f"[yellow]Warning: Could not read MCP settings file: {e}[/yellow]"
        )
        return []

    mcp_servers = config.get("mcpServers", {})

    # If it's already an array, return as is
    if isinstance(mcp_servers, list):
        return mcp_servers

    # If it's an object/dict, convert to array format
    if isinstance(mcp_servers, dict):
        servers_array = []
        for name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                _console.print(
                    f"[yellow]Warning: Invalid config for MCP server '{name}', skipping[/yellow]"
                )
                continue
            server_config_with_name = server_config.copy()
            server_config_with_name["name"] = name
            if "transport" not in server_config_with_name:
                server_config_with_name["transport"] = "stdio"
            servers_array.append(server_config_with_name)
        return servers_array

    return []


def create_mcp_client() -> Optional[MultiServerMCPClient]:
    """
    Create an MCP client from configuration.

    Returns:
        MultiServerMCPClient if servers are configured, None otherwise
    """
    servers_config = load_mcp_config()

    if not servers_config:
        return None

    servers = {}
    for server_config in servers_config:
        try:
            name = server_config["name"]
            transport = server_config.get("transport", "stdio")
            command = server_config["command"]
            args = server_config.get("args", [])

            connection = StdioConnection(
                transport=transport, command=command, args=args
            )
            servers[name] = connection
        except KeyError as e:
            _console.print(
                f"[yellow]Warning: MCP server config missing required field {e}, skipping[/yellow]"
            )
            continue

    if not servers:
        return None

    return MultiServerMCPClient(servers)


# Global client instance (lazy initialization would be better but keeping existing pattern)
_client: Optional[MultiServerMCPClient] = None


def _get_client() -> Optional[MultiServerMCPClient]:
    """Get or create the MCP client singleton."""
    global _client
    if _client is None:
        _client = create_mcp_client()
    return _client


async def get_mcp_tools() -> List[BaseTool]:
    """
    Retrieve tools from configured MCP servers.

    Returns:
        List of BaseTool instances from MCP servers, empty list if none configured or on error
    """
    client = _get_client()

    if client is None:
        return []

    try:
        return await client.get_tools()
    except ConnectionError as e:
        _console.print(
            f"[yellow]Warning: Could not connect to MCP server: {e}[/yellow]"
        )
        return []
    except TimeoutError as e:
        _console.print(
            f"[yellow]Warning: MCP server connection timed out: {e}[/yellow]"
        )
        return []
    except Exception as e:
        _console.print(
            f"[yellow]Warning: Could not get MCP tools ({type(e).__name__}): {e}[/yellow]"
        )
        return []

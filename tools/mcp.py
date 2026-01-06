import json
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection


def load_mcp_config():
    settings_path = Path.home() / ".farcode" / "settings.json"

    if settings_path.exists():
        with open(settings_path, "r") as f:
            config = json.load(f)
            # The mcpServers can be either an array of server configs or an object with server names as keys
            mcp_servers = config.get("mcpServers", {})

            # If it's already an array, return as is
            if isinstance(mcp_servers, list):
                return mcp_servers
            # If it's an object/dict, convert to array format
            elif isinstance(mcp_servers, dict):
                servers_array = []
                for name, server_config in mcp_servers.items():
                    # Add the name to the config
                    server_config_with_name = server_config.copy()
                    server_config_with_name["name"] = name
                    # Set default transport if not specified
                    if "transport" not in server_config_with_name:
                        server_config_with_name["transport"] = "stdio"
                    servers_array.append(server_config_with_name)
                return servers_array
            else:
                return []
    else:
        # Return empty list as default if settings file doesn't exist
        return []


def create_mcp_client():
    servers_config = load_mcp_config()

    if not servers_config:
        # No servers configured
        return None

    servers = {}
    for server_config in servers_config:
        name = server_config["name"]
        transport = server_config["transport"]
        command = server_config["command"]
        args = server_config["args"]

        connection = StdioConnection(transport=transport, command=command, args=args)
        servers[name] = connection

    return MultiServerMCPClient(servers)


client = create_mcp_client()


async def get_mcp_tools():
    try:
        if client is None:
            return []  # Return empty list if no client configured
        return await client.get_tools()
    except Exception as e:
        print(f"Warning: Could not get MCP tools: {e}")
        return []

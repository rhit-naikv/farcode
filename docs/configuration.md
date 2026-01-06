# Farcode Configuration

Farcode now supports a configuration system using a settings file located at `~/.farcode/settings.json`.

## Settings File Location

The settings file is located at:
- `~/.farcode/settings.json` (in the user's home directory)

## Configuration Options

The settings file supports the following structure:

```json
{
  "mcpServers": [
    {
      "name": "server_name",
      "transport": "stdio",
      "command": "command_to_run",
      "args": ["array", "of", "arguments"]
    }
  ]
}
```

## MCP Servers Configuration

The `mcpServers` list allows you to configure multiple Model Context Protocol (MCP) servers that Farcode can connect to. Each server configuration includes:

- `name`: A unique identifier for the server
- `transport`: The transport method (currently only "stdio" is supported)
- `command`: The command to execute to start the server
- `args`: An array of arguments to pass to the command

## Default Behavior

If the settings file does not exist, Farcode will operate with an empty server list, meaning no MCP tools will be available.
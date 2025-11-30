# Claude Desktop Configuration for PartsBox MCP Server

This document explains how to configure Claude Desktop to use the PartsBox MCP server via Docker.

## Configuration

Add the following configuration to your `claude_desktop_config.json` file:

### Windows

The configuration file is typically located at:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### macOS

The configuration file is typically located at:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

## MCP Server Configuration

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "partsbox": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "C:/docker/partsbox-mcp/.env:/workspace/.env:ro",
        "partsbox-mcp:latest",
        "/bin/bash",
        "-c",
        "cd /workspace && uv run python -m partsbox_mcp.server"
      ]
    }
  }
}
```

## Configuration Details

| Parameter | Description |
|-----------|-------------|
| `command` | Uses Docker to run the MCP server in a container |
| `-i` | Keeps STDIN open for interactive communication |
| `--rm` | Automatically removes the container when it exits |
| `-v .env` | Mounts your `.env` file containing `PARTSBOX_API_KEY` (read-only) |

## Setup Steps

1. **Build the Docker image** (if not already built):
   ```bash
   docker build -t partsbox-mcp:latest .
   ```

2. **Create your `.env` file** at the path specified in the volume mount:
   ```
   PARTSBOX_API_KEY=partsboxapi_your_key_here
   ```

3. **Update paths**: Modify the volume mount path (`C:/docker/partsbox-mcp/.env`) to match where your `.env` file is located on your system.

4. **Restart Claude Desktop** to load the new configuration.

## Verifying the Configuration

After restarting Claude Desktop, the PartsBox MCP server should be available. You can verify by asking Claude to list your parts or check your inventory.

## Troubleshooting

- **Container not starting**: Ensure Docker Desktop is running
- **Authentication errors**: Verify your `PARTSBOX_API_KEY` in the `.env` file
- **Path issues on Windows**: Use forward slashes (`/`) in paths within the JSON configuration
- **Path issues on macOS/Linux**: Update the volume mount path to use Unix-style paths (e.g., `/home/user/partsbox-mcp/.env`)

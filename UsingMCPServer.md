# Using the PartsBox MCP Server

This guide explains how to configure AI assistants to use the PartsBox MCP server.

## Prerequisites

Before configuring the MCP server, ensure you have:

1. Docker installed and running
2. The `partsbox-mcp:latest` Docker image built (`docker compose build`)
3. A `.env` file containing your PartsBox API key stored in a known location
4. A PartsBox API key (generated in Settings | Data)

### Building the Docker Image

```bash
docker compose build
```

### Environment File Setup

Create a `.env` file with your API key:

```
PARTSBOX_API_KEY=partsboxapi_your_api_key_here
```

Store this file in a secure location on your system (e.g., `C:/docker/partsbox-mcp-env` on Windows or `/etc/partsbox-mcp/.env` on Linux/macOS).

## Claude Desktop

Add the following to your Claude Desktop configuration file:

| Platform | Configuration File Location |
|----------|----------------------------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

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
        "/path/to/your/.env:/workspace/.env:ro",
        "partsbox-mcp:latest",
        "uv",
        "run",
        "partsbox-mcp"
      ]
    }
  }
}
```

Replace `/path/to/your/.env` with the absolute path to your `.env` file:
- **Windows example**: `C:/docker/partsbox-mcp-env:/workspace/.env:ro`
- **macOS/Linux example**: `/etc/partsbox-mcp/.env:/workspace/.env:ro`

## Claude Code (CLI)

Create a `.mcp.json` file in the project root where you want to use the PartsBox MCP server:

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
        "./.env:/workspace/.env:ro",
        "partsbox-mcp:latest",
        "uv",
        "run",
        "partsbox-mcp"
      ]
    }
  }
}
```

This configuration uses a relative path (`./.env`) to mount the `.env` file from the current project directory. This allows the configuration to be committed to version control while keeping the `.env` file (containing your API key) in `.gitignore`.

### Configuration Scopes

Claude Code supports three configuration scopes:

| Scope | Description | How to Add |
|-------|-------------|------------|
| **local** | Only you, current project | `claude mcp add -s local ...` (default) |
| **project** | Team-shared via `.mcp.json` | `claude mcp add -s project ...` |
| **user** | Only you, all projects | `claude mcp add -s user ...` |

## Security Notes

- Guard your API key carefully as it provides full access to your PartsBox database
- The `.env` file is mounted read-only (`:ro`) into the container for security
- Keep your `.env` file in `.gitignore` to avoid committing secrets to version control
- The `.mcp.json` file can be safely committed as it contains no secrets

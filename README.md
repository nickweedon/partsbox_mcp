# PartsBox MCP Server

A Model Context Protocol (MCP) server for the PartsBox API using FastMCP. This server enables AI assistants to interact with your PartsBox inventory management system for electronic components.

## Overview

[PartsBox](https://partsbox.com/) is an inventory management system for electronic components. This MCP server provides tools to:

- Manage parts and their metadata
- Track stock levels and locations
- Handle lots and stock entries
- Manage storage locations
- Work with projects and BOMs (Bill of Materials)
- Process orders and receive stock

## Requirements

- Python 3.10+
- uv package manager
- PartsBox API key (generated in Settings | Data)

## Setup

### 1. Install dependencies
```bash
uv sync
```

### 2. Set up environment variables
Create a `.env` file in the project root:
```
PARTSBOX_API_KEY=partsboxapi_your_api_key_here
```

**Security Note:** Guard your API key carefully, as it provides full access to your PartsBox database.

### 3. Run the server
```bash
uv run python partsbox_mcp_server.py
```

## API Overview

The PartsBox API is operation-oriented (not REST) and provides:

### Parts Management
- Create, retrieve, update, and delete parts
- Manage substitutes and meta-parts
- Handle custom fields

### Stock Management
- Add and remove stock
- Move stock between locations
- Update stock entries
- Retrieve stock by part or storage location

### Lots
- Get and update lot data
- Track lot information

### Storage
- Manage storage locations
- Archive and restore locations
- Aggregate stock by location

### Projects
- Create and manage BOMs
- Handle BOM entries
- Track project builds

### Orders
- Create and manage orders
- Add order entries
- Receive stock from orders
- Manage order lifecycle

## Available Tools

*Tools will be implemented to wrap PartsBox API operations. See the server implementation for the complete list of available tools.*

## Important Notes

### Authentication
All API requests require an API key passed in the Authorization header:
```
Authorization: APIKey partsboxapi_[your-key]
```

### Timestamps
PartsBox stores timestamps as 64-bit UNIX UTC timestamps. Timezone conversion is your responsibility.

### Stock Calculations
PartsBox does not store total stock counts. Stock counts are calculated by traversing stock history.

### Rate Limiting
Rate limits may be enforced. Plan for potential rate limiting in your usage.

### API Restrictions
- Cannot create user interface applications using the API (automation only)
- Commercial plan users receive standard support
- Free account users should not expect email responses

## Claude Desktop Integration

Add this to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "partsbox": {
      "command": "uv",
      "args": ["run", "python", "partsbox_mcp_server.py"],
      "cwd": "/path/to/partsbox_mcp"
    }
  }
}
```

## Related Resources

- [PartsBox API Documentation](https://partsbox.com/api.html)
- [PartsBox Website](https://partsbox.com/)


# Developing

This project is designed to work with vscode and the devcontainers plugin. I recommend also running claude --dangerously-skip-permissions once inside the devcontainer for best results 😁
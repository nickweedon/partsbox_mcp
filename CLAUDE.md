# PartsBox MCP Server - Claude Context

This is an MCP (Model Context Protocol) server for interfacing with the PartsBox API. It enables AI assistants to manage electronic component inventory through PartsBox.

## Project Structure

```
partsbox_mcp/
├── partsbox_mcp_server.py  # Main MCP server implementation
├── pyproject.toml          # Project configuration and dependencies
├── .env                    # Environment variables (API key)
├── README.md               # User documentation
├── design.md               # Detailed design documentation
└── CLAUDE.md               # This file - context for Claude
```

## Design Documentation

See [design.md](design.md) for comprehensive design details including:
- Caching strategy with client-controlled keys
- JMESPath filtering and projection
- Strongly-typed return values
- Error handling patterns
- Implementation examples with code

## API Reference

**Full API Documentation:** https://partsbox.com/api.html

### Base URL
```
https://api.partsbox.com/api/1/[operation]
```

### Authentication
```
Authorization: APIKey partsboxapi_[your-key]
```

API keys are generated in PartsBox Settings | Data.

### Request/Response Format
- Default format: JSON
- EDN format available with `mode: "edn"` parameter
- Responses include status info with data under the `"data"` key

### Key API Characteristics
1. **Operation-oriented** - Not a REST API; designed for complex operations and aggregated information
2. **Timestamps** - 64-bit UNIX UTC timestamps; timezone conversion is caller's responsibility
3. **Stock counts** - Not stored; must be calculated from stock history
4. **Rate limits** - Expected to be enforced (not yet specified)

## API Operations

### Parts
- Create/retrieve/update/delete parts
- Manage substitutes and meta-parts
- Handle custom fields

### Stock
- Add/remove stock entries
- Move between locations
- Update entries
- Query by part or location

### Lots
- Get/update lot data
- Track lot information

### Storage
- Manage storage locations
- Archive/restore locations
- Aggregate stock by location

### Projects
- Create/manage BOMs
- Handle BOM entries
- Track builds

### Orders
- Create/manage orders
- Add entries
- Receive stock
- Manage order lifecycle

## Development Notes

- Uses FastMCP framework for MCP server implementation
- Uses `requests` library for HTTP calls
- Environment variables loaded via `python-dotenv`
- Requires Python 3.10+

## Running the Server

```bash
uv sync
uv run python partsbox_mcp_server.py
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PARTSBOX_API_KEY` | Your PartsBox API key (format: `partsboxapi_...`) |

## Testing

Test the server with:
```bash
uv run python -c "from partsbox_mcp_server import mcp; print('Server loads OK')"
```

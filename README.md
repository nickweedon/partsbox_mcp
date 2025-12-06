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

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PARTSBOX_API_KEY` | (required) | Your PartsBox API key |
| `PARTSBOX_MCP_DEBUG` | `true` | Enable timing/logging middleware |
| `PARTSBOX_MCP_MASK_ERRORS` | `false` | Hide internal error details from clients |

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

### Parts API
| Tool | Description |
|------|-------------|
| `list_parts` | List all parts with pagination and JMESPath queries |
| `get_part` | Get detailed information for a specific part |
| `create_part` | Create a new part |
| `update_part` | Update an existing part |
| `delete_part` | Delete a part |
| `add_meta_part_ids` | Add members to a meta-part |
| `remove_meta_part_ids` | Remove members from a meta-part |
| `add_substitute_ids` | Add substitutes to a part |
| `remove_substitute_ids` | Remove substitutes from a part |
| `get_part_storage` | Get aggregated stock by storage location |
| `get_part_lots` | Get individual lot entries for a part |
| `get_part_stock` | Get total stock count for a part |

### Stock API
| Tool | Description |
|------|-------------|
| `add_stock` | Add stock to inventory |
| `remove_stock` | Remove stock from inventory |
| `move_stock` | Move stock between locations |
| `update_stock` | Update a stock entry |

### Lots API
| Tool | Description |
|------|-------------|
| `list_lots` | List all lots |
| `get_lot` | Get lot details |
| `update_lot` | Update lot information |

### Storage API
| Tool | Description |
|------|-------------|
| `list_storage_locations` | List all storage locations |
| `get_storage_location` | Get storage location details |
| `update_storage_location` | Update storage location metadata |
| `rename_storage_location` | Rename a storage location |
| `change_storage_settings` | Modify storage settings (full, single-part, existing-parts-only) |
| `archive_storage_location` | Archive a storage location |
| `restore_storage_location` | Restore an archived location |
| `list_storage_parts` | List aggregated stock by part in a location |
| `list_storage_lots` | List individual lots in a location |

### Projects API
| Tool | Description |
|------|-------------|
| `list_projects` | List all projects/BOMs |
| `get_project` | Get project details |
| `create_project` | Create a new project |
| `update_project` | Update project metadata |
| `delete_project` | Delete a project |
| `archive_project` | Archive a project |
| `restore_project` | Restore an archived project |
| `get_project_entries` | Get BOM entries for a project |
| `add_project_entries` | Add entries to a project BOM |
| `update_project_entries` | Update BOM entries |
| `delete_project_entries` | Remove entries from a BOM |
| `get_project_builds` | Get build history for a project |
| `get_build` | Get build details |
| `update_build` | Update build information |

### Orders API
| Tool | Description |
|------|-------------|
| `list_orders` | List all orders |
| `get_order` | Get order details |
| `create_order` | Create a new order |
| `get_order_entries` | Get line items in an order |
| `add_order_entries` | Add items to an order |
| `delete_order_entry` | Remove an item from an order |
| `receive_order` | Process received inventory |

## MCP Resources

Resources provide read-only access to files and images via URI templates:

| Resource URI | Description |
|--------------|-------------|
| `partsbox://image/{file_id}` | Download and render part images directly in Claude Desktop |
| `partsbox://file/{file_id}` | Download files (datasheets, PDFs, etc.) |
| `partsbox://file-url/{file_id}` | Get the download URL without fetching the file |

The `file_id` is obtained from part data (e.g., the `part/img-id` field returned by `get_part` or `list_parts`).

## JMESPath Query Support

All list operations support JMESPath queries for filtering and projection. This server extends standard JMESPath with custom functions for safe null handling and data transformation:

### Custom Functions

| Function | Description | Example |
|----------|-------------|---------|
| `nvl(value, default)` | Returns default if value is null | `nvl("part/name", '')` |
| `int(value)` | Converts to integer (null on failure) | `int("custom-field/qty")` |
| `str(value)` | Converts any value to string | `str("part/id")` |
| `regex_replace(pattern, repl, value)` | Regex find-and-replace | `regex_replace('[^0-9]', '', "value")` |

### Null-Safe Queries

**IMPORTANT:** Many PartsBox fields are nullable. Use `nvl()` to prevent errors when filtering on these fields:

```python
# UNSAFE - fails if "part/name" is null
query="[?contains(\"part/name\", 'resistor')]"

# SAFE - handles null values
query="[?contains(nvl(\"part/name\", ''), 'resistor')]"
```

### Query Examples

```python
# Search parts by name (null-safe)
query="[?contains(nvl(\"part/name\", ''), 'capacitor')]"

# Filter by manufacturer
query="[?nvl(\"part/manufacturer\", '') == 'Texas Instruments']"

# Combine conditions
query="[?contains(nvl(\"part/name\", ''), 'resistor') && \"stock/total\" > `0`]"

# Sort results
query="sort_by(@, &\"part/name\")"
```

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

## Claude Integration

This MCP server works with Claude Desktop and Claude Code (CLI). See [UsingMCPServer.md](UsingMCPServer.md) for detailed configuration instructions.

## Related Resources

- [PartsBox API Documentation](https://partsbox.com/api.html)
- [PartsBox Website](https://partsbox.com/)


# Developing

This project is designed to work with vscode and the devcontainers plugin. I recommend also running claude --dangerously-skip-permissions once inside the devcontainer for best results 😁
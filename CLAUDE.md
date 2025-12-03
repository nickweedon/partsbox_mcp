# PartsBox MCP Server - Claude Context

This is an MCP (Model Context Protocol) server for interfacing with the PartsBox API. It enables AI assistants to manage electronic component inventory through PartsBox.

## Primary Use Case

This MCP Server will be used by Claude Desktop as part of a custom Claude Desktop "Project" that contains instructions to help guide its usage of this MCP server as well as other behavior.

## Debugging

The user's logs relating to usage of this MCP server can be found at "TODO"

## Project Structure

Follow standard Python project conventions with a modular architecture. API methods should be organized into separate modules by domain.

```
partsbox_mcp/
├── src/
│   └── partsbox_mcp/
│       ├── __init__.py         # Package initialization
│       ├── server.py           # Main MCP server entry point
│       ├── client.py           # HTTP client and authentication
│       ├── api/
│       │   ├── __init__.py     # API module initialization
│       │   ├── parts.py        # Parts API methods
│       │   ├── stock.py        # Stock API methods
│       │   ├── lots.py         # Lots API methods
│       │   ├── storage.py      # Storage API methods
│       │   ├── projects.py     # Projects/BOM API methods
│       │   └── orders.py       # Orders API methods
│       └── utils/
│           ├── __init__.py
│           ├── helpers.py              # Shared utilities
│           └── jmespath_extensions.py  # Custom JMESPath functions (nvl, int, str, regex_replace)
├── tests/
│   └── ...                     # Test files mirroring src structure
├── pyproject.toml              # Project configuration and dependencies
├── .env                        # Environment variables (API key)
├── README.md                   # User documentation
├── design.md                   # Detailed design documentation
└── CLAUDE.md                   # This file - context for Claude
```

## Code Organization Guidelines

1. **Modular API Methods**: Each API domain (Parts, Stock, Lots, Storage, Projects, Orders) MUST be implemented in its own Python module under `src/partsbox_mcp/api/`.

2. **Separation of Concerns**:
   - `client.py` - HTTP client, authentication, and base request handling
   - `api/*.py` - Domain-specific API methods only
   - `utils/` - Shared helper functions and utilities
   - `server.py` - MCP server setup and tool registration

3. **Standard Python Conventions**:
   - Use `src/` layout for proper package isolation
   - Include `__init__.py` files in all packages
   - Follow PEP 8 naming conventions
   - Use type hints throughout
   - Keep modules focused and cohesive

4. **Import Structure**: Each API module should import the shared client and expose its methods. The main server imports and registers tools from each API module.

## Design Documentation

See [design.md](design.md) for comprehensive design details including:
- Caching strategy with client-controlled keys
- JMESPath filtering and projection with custom functions
- Strongly-typed return values
- Error handling patterns
- Implementation examples with code

In addition to this, the design should:
- Never change the structure or field names in the default JMESPath query as this can confuse the LLM
- Always provide a 'returns' description in the docstring that fully describes the returned type in detail as this is the only way that the LLM can introspect the tool method

## JMESPath Query Syntax

### CRITICAL: Field Identifier Escaping

PartsBox uses field names with `/` characters (e.g., `part/name`, `part/tags`). In JMESPath:

- **Double quotes (`"`)** create **QUOTED IDENTIFIERS** for field access
- **Backticks (`` ` ``)** create **LITERAL JSON VALUES** (strings, not field references)

**Using backticks is WRONG and will cause silent failures** - queries return empty results because the backtick expression evaluates to a literal string instead of accessing the field value.

```python
# CORRECT - Double quotes access the field value
"[?contains(\"part/tags\", 'resistor')]"  # Returns parts with 'resistor' tag
"[*].{id: \"part/id\", name: \"part/name\"}"  # Projects field values

# WRONG - Backticks create literal strings, NOT field references
"[?contains(`part/tags`, 'resistor')]"  # Returns NOTHING - checks if literal "part/tags" contains 'resistor'
"[*].{id: `part/id`, name: `part/name`}"  # Returns literal strings "part/id", "part/name"
```

### Custom Functions

The server extends standard JMESPath with custom functions in `utils/jmespath_extensions.py`:

| Function | Signature | Description |
|----------|-----------|-------------|
| `nvl` | `nvl(value, default)` | Returns `default` if `value` is null - **CRITICAL for null safety** |
| `int` | `int(value)` | Converts string/number to integer; returns null on failure |
| `str` | `str(value)` | Converts any value to string representation |
| `regex_replace` | `regex_replace(pattern, replacement, value)` | Regex find-and-replace on strings |

### IMPORTANT: Null-Safe Queries

Many PartsBox fields are nullable. **Always use `nvl()` when filtering with `contains()`, `starts_with()`, or equality checks on nullable fields.** Without it, queries will fail with errors like:

```
"In function contains(), invalid type for value: None, expected one of: ['array', 'string'], received: \"null\""
```

**Correct patterns:**
```python
# SAFE - handles null values
"[?contains(nvl(\"part/name\", ''), 'resistor')]"

# UNSAFE - fails on null
"[?contains(\"part/name\", 'resistor')]"
```

When adding new JMESPath examples in docstrings, always use the null-safe pattern with `nvl()` for string fields.

## Implementation Guidelines

### MCP Tool Method Signatures

The following guidelines should be followed when modifying or creating new MCP tool methods/functions:
- Provide JMESPath filtering and projection when the tool method can return large or complex data types
- Provide paging whenever the method returns a list of objects.
- Never change the structure or field names in the default JMESPath query as this can confuse the LLM
- Provide Strongly-typed return values
- Always provide a JMESPath example in the docstring when the tool accepts JMESPath queries
- Always provide details of the full output schema, described as a JSON schema, in the 'returns' part of the docstring for any method that takes JMESPath queries for filtering and projections. Only document the full schema, do not call out the specific shape of the JMESPath default query as this can consfuse the LLM.

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

## Git Commit Guidelines

- Do NOT include "Generated with Claude Code" or similar AI attribution in commit messages
- Do NOT include "Co-Authored-By: Claude" or similar co-author tags
- Write commit messages as if authored solely by the developer

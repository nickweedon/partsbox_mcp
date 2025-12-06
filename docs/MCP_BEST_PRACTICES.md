# MCP Server Best Practices

This document captures MCP (Model Context Protocol) best practices applied to this project.

## Resources vs Tools

### When to Use Resources
- **Read-only data access** - No side effects
- **File/binary content** - Images, PDFs, datasheets
- **URI-addressable data** - Content that can be identified by a stable URI
- **Frequently accessed reference data** - Catalogs, configuration

### When to Use Tools
- **Operations with side effects** - Create, update, delete
- **Complex queries** - Filtering, aggregation, pagination
- **Multi-step operations** - Stock moves, order processing
- **Actions requiring parameters** - Beyond simple URI parameters

## Parameter Documentation

Use `Annotated` types for all parameters to provide descriptions to LLMs:

```python
from typing import Annotated

@mcp.tool()
async def list_parts(
    limit: Annotated[int, "Maximum items to return (1-1000)"] = 50,
    offset: Annotated[int, "Starting index in query results"] = 0,
) -> Response:
```

**Note:** `Annotated` descriptions complement (not replace) docstring documentation. Tools with JMESPath queries still require full JSON schema documentation in the 'returns' section of the docstring.

## Docstring Requirements for JMESPath Tools

Tools accepting a `query` parameter for JMESPath filtering MUST include:
1. JMESPath examples showing correct syntax (double quotes for field identifiers)
2. Full JSON schema of the output data in the 'returns' section
3. Documentation of custom functions (nvl, int, str, regex_replace)

This is required because LLMs cannot introspect return types - the docstring is the only way they understand the data structure.

## Error Handling

### ToolError for Client-Facing Messages
```python
from fastmcp import ToolError

if not required_param:
    raise ToolError("required_param is required")
```

### ResourceError for Resource Failures
```python
from fastmcp.exceptions import ResourceError

if not file_data:
    raise ResourceError(f"File not found: {file_id}")
```

### Error Masking
Set `mask_error_details=True` in production to hide internal errors. Only `ToolError` and `ResourceError` messages will be exposed.

## Binary Content

### Images
```python
from fastmcp.utilities.types import Image

@mcp.resource("app://image/{id}")
def get_image(id: str) -> Image:
    data = fetch_image_bytes(id)
    return Image(data=data, media_type="image/png")
```

### Files
Return raw bytes for file resources:
```python
@mcp.resource("app://file/{id}")
def get_file(id: str) -> bytes:
    return fetch_file_bytes(id)
```

## Server Configuration

```python
mcp = FastMCP(
    name="Server Name",
    instructions="Description of capabilities for LLMs",
    mask_error_details=True,  # Production
    on_duplicate_tools="error",  # Fail fast
    on_duplicate_resources="error",  # Fail fast
)
```

## References

- [MCP Specification](https://modelcontextprotocol.io/specification/2025-06-18/)
- [FastMCP Documentation](https://gofastmcp.com)

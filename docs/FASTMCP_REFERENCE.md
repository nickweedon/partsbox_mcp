# FastMCP Server Reference

This document summarizes key FastMCP server concepts relevant to this project. It is sourced from the official FastMCP documentation at https://gofastmcp.com.

For complete details, refer to:
- Official documentation: https://gofastmcp.com
- GitHub repository: https://github.com/jlowin/fastmcp

---

## Table of Contents

- [Server Overview](#server-overview)
- [Core Components](#core-components)
  - [Tools](#tools)
  - [Resources](#resources)
  - [Prompts](#prompts)
- [Advanced Features](#advanced-features)
  - [Composition](#composition)
  - [Context](#context)
  - [Elicitation](#elicitation)
  - [Icons](#icons)
  - [Logging](#logging)
  - [Middleware](#middleware)
  - [Progress](#progress)
  - [Proxy Servers](#proxy-servers)
  - [Sampling](#sampling)
  - [Storage Backends](#storage-backends)
  - [Background Tasks](#background-tasks)
- [Authentication](#authentication)
  - [Overview](#authentication-overview)
  - [Token Verification](#token-verification)
  - [Remote OAuth](#remote-oauth)
  - [OAuth Proxy](#oauth-proxy)
  - [OIDC Proxy](#oidc-proxy)
  - [Full OAuth Server](#full-oauth-server)
- [Deployment](#deployment)
  - [Running Your Server](#running-your-server)
  - [HTTP Deployment](#http-deployment)
  - [Project Configuration](#project-configuration)
- [Critical Notes for This Project](#critical-notes-for-this-project)

---

## Server Overview

FastMCP servers are created using the `FastMCP` class:

```python
from fastmcp import FastMCP
mcp = FastMCP(name="MyServer")
```

### Constructor Parameters

| Parameter | Description |
|-----------|-------------|
| `name` | Human-readable identifier for the server |
| `instructions` | Guidance text describing server purpose and functionality |
| `version` | Custom version string (defaults to FastMCP library version) |
| `website_url` | Reference URL for additional information |
| `icons` | Visual representations for client applications |
| `auth` | Authentication provider for HTTP transports |
| `lifespan` | Async context manager for startup/shutdown logic |
| `on_duplicate_tools` | How to handle duplicate tool registrations: "error", "warn", "replace", "ignore" |
| `on_duplicate_resources` | How to handle duplicate resource registrations |
| `on_duplicate_prompts` | How to handle duplicate prompt registrations |
| `mask_error_details` | Hide internal error details from clients (only `ToolError` messages exposed) |
| `strict_input_validation` | Use strict JSON Schema validation instead of Pydantic coercion |
| `include_tags` | Only expose components with these tags |
| `exclude_tags` | Hide components with these tags |
| `tool_serializer` | Custom serialization function for tool return values |

### Global Settings (Environment Variables)

| Variable | Description |
|----------|-------------|
| `FASTMCP_LOG_LEVEL` | Logging verbosity |
| `FASTMCP_MASK_ERROR_DETAILS` | Hide internal errors |
| `FASTMCP_STRICT_INPUT_VALIDATION` | Enable strict type checking |
| `FASTMCP_INCLUDE_FASTMCP_META` | Include FastMCP metadata in responses |

---

## Core Components

### Tools

Tools expose Python functions as executable capabilities for LLMs through the MCP protocol.

#### Basic Pattern

```python
@mcp.tool()
def my_tool(
    param: Annotated[str, "Description of parameter"],
    optional_param: Annotated[int, "Optional parameter"] = 10,
) -> str:
    """
    Tool description shown to the LLM.
    """
    return "result"
```

#### Decorator Arguments

| Parameter | Purpose |
|-----------|---------|
| `name` | Custom tool name (defaults to function name) |
| `description` | Override docstring description |
| `tags` | Categorize tools with string identifiers |
| `enabled` | Toggle tool visibility (default: True) |
| `exclude_args` | Hide arguments from schema |
| `annotations` | Add metadata (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) |
| `meta` | Custom metadata passed to clients |
| `output_schema` | Define expected output format |
| `icons` | Visual icons for the tool |

#### Parameter Annotations

Use `Annotated` with simple strings for descriptions:

```python
image_url: Annotated[str, "URL of the image to process"]
```

For advanced constraints, use Pydantic's `Field`:

```python
width: Annotated[int, Field(description="Width in pixels", ge=1, le=2000)] = 800
```

#### Supported Types

- Basic: `int`, `str`, `bool`, `float`
- Collections: `list`, `dict`, `set`
- Optional types and unions
- Pydantic models and dataclasses
- `Path`, `UUID`, `datetime`, `Enum`, `Literal`

#### Return Values

| Return Type | Conversion |
|-------------|------------|
| `str` | TextContent |
| `bytes` | Base64-encoded BlobResourceContents |
| `dict` / Pydantic model | Auto-serialized to JSON |
| `Image`, `Audio`, `File` | Appropriate MCP content type |
| `ToolResult` | Explicit control over all output aspects |

#### Async Support

FastMCP supports both sync and async functions. Async is preferred for I/O operations:

```python
@mcp.tool
async def fetch_data(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

For CPU-intensive sync code, wrap with `anyio.to_thread.run_sync()`.

#### Tool Management

```python
# Disable/enable tools
tool_instance.disable()
tool_instance.enable()

# Or use decorator
@mcp.tool(enabled=False)
def disabled_tool(): ...

# Remove tools
mcp.remove_tool("tool_name")
```

---

### Resources

Resources represent read-only data access points that clients can retrieve.

#### Basic Pattern

```python
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP!"
```

#### Decorator Arguments

| Parameter | Purpose |
|-----------|---------|
| `uri` | Unique identifier for the resource (required) |
| `name` | Human-readable name (defaults to function name) |
| `description` | Explanation (defaults to docstring) |
| `mime_type` | Content type specification |
| `tags` | Categorization set |
| `enabled` | Boolean to enable/disable |
| `annotations` | Metadata about resource behavior |
| `meta` | Custom application-specific metadata |
| `icons` | Visual icons for the resource |

#### Resource Templates (Parameterized)

Use RFC 6570 URI syntax with placeholders:

```python
@mcp.resource("weather://{city}/current")
def get_weather(city: str) -> dict:
    return {"city": city.capitalize(), "temperature": 22}
```

**Wildcard parameters** capture multiple path segments:

```python
@mcp.resource("path://{filepath*}")
def get_path_content(filepath: str) -> str:
    return f"Content at path: {filepath}"
```

**Query parameters** for optional configuration:

```python
@mcp.resource("data://{id}{?format}")
def get_data(id: str, format: str = "json") -> str:
    return format_data(id, format)
```

#### Static Resources

For pre-defined content:

```python
from fastmcp.resources import TextResource, FileResource

text_resource = TextResource(
    uri="resource://notice",
    name="Notice",
    text="System maintenance scheduled."
)
mcp.add_resource(text_resource)
```

Available classes: `TextResource`, `BinaryResource`, `FileResource`, `HttpResource`, `DirectoryResource`

---

### Prompts

Prompts are reusable message templates that help LLMs generate structured responses.

#### Basic Pattern

```python
@mcp.prompt
def ask_about_topic(topic: str) -> str:
    """Generates a user message asking for an explanation of a topic."""
    return f"Can you please explain the concept of '{topic}'?"
```

#### Decorator Arguments

| Parameter | Purpose |
|-----------|---------|
| `name` | Custom prompt identifier (defaults to function name) |
| `description` | Custom description (overrides docstring) |
| `tags` | Categorization tags as a set of strings |
| `enabled` | Boolean to enable/disable (default: True) |
| `icons` | Optional icon representations |
| `meta` | Custom metadata passed to MCP clients |

#### Return Values

| Return Type | Behavior |
|-------------|----------|
| `str` | Converted to a single PromptMessage |
| `PromptMessage` | Used directly |
| `list[PromptMessage \| str]` | Treated as a conversation sequence |
| Any other type | Converted to string as PromptMessage |

#### Required vs Optional Parameters

```python
@mcp.prompt
def analysis_prompt(
    data_uri: str,                    # Required
    analysis_type: str = "summary",   # Optional
    include_charts: bool = False      # Optional
) -> str:
    return f"Perform '{analysis_type}' analysis on {data_uri}"
```

---

## Advanced Features

### Composition

FastMCP enables combining multiple servers through two approaches.

#### Import Server (Static)

One-time copy of components. Changes after importing are not reflected:

```python
main_mcp.import_server(other_mcp)

# With prefix
main_mcp.import_server(weather_mcp, prefix="weather")
# Tools become: weather_tool_name
# Resources become: data://weather/path
```

#### Mount (Dynamic)

Live connection where changes are immediately reflected:

```python
main_mcp.mount(other_mcp, prefix="sub")
```

**Trade-off**: Mount has higher latency (300-400ms for HTTP-based servers) vs import's faster local access.

---

### Context

The Context object provides access to MCP capabilities within tools, resources, and prompts.

#### Accessing Context

```python
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

@mcp.tool
async def my_tool(data: str, ctx: Context = CurrentContext()) -> str:
    await ctx.info("Processing started")
    return "Done"
```

For nested functions, use `get_context()`:

```python
from fastmcp.server.context import get_context

async def helper_function():
    ctx = get_context()
    await ctx.info("Helper called")
```

#### Available Methods

| Category | Methods |
|----------|---------|
| **Logging** | `ctx.debug()`, `ctx.info()`, `ctx.warning()`, `ctx.error()` |
| **Resources** | `ctx.list_resources()`, `ctx.read_resource(uri)` |
| **Prompts** | `ctx.list_prompts()`, `ctx.get_prompt(name, arguments)` |
| **Progress** | `ctx.report_progress(progress, total)` |
| **State** | `ctx.set_state(key, value)`, `ctx.get_state(key)` |
| **Client** | `ctx.elicit(prompt, response_type)`, `ctx.sample(message)` |

#### Properties

| Property | Description |
|----------|-------------|
| `ctx.request_id` | Unique MCP request identifier |
| `ctx.client_id` | Requesting client's ID |
| `ctx.session_id` | MCP session ID (HTTP only) |
| `ctx.fastmcp` | Access underlying FastMCP server instance |

**Note**: Context is request-scoped; state doesn't persist between requests.

#### HTTP Dependencies

```python
from fastmcp.server.dependencies import get_http_request, get_access_token

request = get_http_request()
user_agent = request.headers.get("user-agent")

token = get_access_token()
if token:
    user_id = token.claims.get("sub")
```

#### Custom Dependencies

```python
from fastmcp import Depends

def get_config() -> dict:
    return {"api_url": "https://api.example.com"}

@mcp.tool
async def fetch(query: str, config: dict = Depends(get_config)) -> str:
    return f"Querying {config['api_url']}"
```

---

### Elicitation

Request structured information from users during tool operations.

```python
@mcp.tool
async def interactive_tool(ctx: Context) -> str:
    result = await ctx.elicit(
        message="Enter your name:",
        response_type=str
    )

    if result.action == "accept":
        return f"Hello, {result.data}!"
    elif result.action == "decline":
        return "User declined to provide input"
    else:  # cancel
        return "Operation cancelled"
```

#### Response Types

- **Scalar types**: `str`, `int`, `bool` (auto-wrapped in MCP-compatible schemas)
- **None**: For approval-only scenarios
- **Constrained options**: `Literal` types, Enums, list of strings
- **Structured data**: Dataclasses, TypedDict, Pydantic models

---

### Icons

Add visual icons to servers and components (v2.13.0+):

```python
from mcp.types import Icon

mcp = FastMCP(
    name="WeatherService",
    icons=[Icon(src="https://example.com/icon.png", mimeType="image/png", sizes=["48x48"])]
)

@mcp.tool(icons=[Icon(src="https://example.com/tool-icon.png")])
def my_tool() -> str:
    return "result"
```

Embedded icons with data URIs:

```python
from fastmcp.utilities.types import Image

img = Image(path="./assets/favicon.png")
icon = Icon(src=img.to_data_uri())
```

---

### Logging

Send log messages to MCP clients through the context:

```python
@mcp.tool
async def process(data: str, ctx: Context) -> str:
    await ctx.debug("Starting processing")
    await ctx.info("Processing data", extra={"data_size": len(data)})
    await ctx.warning("Large data detected")
    await ctx.error("Processing failed", extra={"error_code": 500})
    return "Done"
```

The `extra` parameter accepts arbitrary dictionary data for structured logging.

---

### Middleware

Intercept and modify requests and responses:

```python
from fastmcp.server.middleware import Middleware, MiddlewareContext

class LoggingMiddleware(Middleware):
    async def on_message(self, context: MiddlewareContext, call_next):
        print(f"Processing {context.method}")
        result = await call_next(context)
        print(f"Completed {context.method}")
        return result

mcp.add_middleware(LoggingMiddleware())
```

#### Available Hooks

- **Message-level**: `on_message`, `on_request`, `on_notification`
- **Operation-specific**: `on_call_tool`, `on_read_resource`, `on_get_prompt`, `on_list_tools`, `on_list_resources`, `on_list_prompts`
- **Lifecycle**: `on_initialize`

#### Built-in Middleware

- `TimingMiddleware` / `DetailedTimingMiddleware`: Performance monitoring
- `ResponseCachingMiddleware`: TTL-based response caching
- `RateLimitingMiddleware`: Token bucket or sliding window rate limiting
- Logging middleware: Human-readable or JSON-structured output
- Error handling middleware: Comprehensive error logging and transformation

---

### Progress

Report progress for long-running operations:

```python
@mcp.tool
async def long_operation(ctx: Context) -> str:
    for i in range(100):
        await ctx.report_progress(progress=i, total=100)
        await asyncio.sleep(0.1)
    return "Complete"
```

#### Progress Patterns

| Pattern | Use Case | Example |
|---------|----------|---------|
| Percentage | Known total | `progress=50, total=100` |
| Absolute | Countable items | `progress=3, total=5` |
| Indeterminate | Unknown endpoint | `progress=1500` (no total) |

---

### Proxy Servers

Act as intermediaries to forward requests to backend MCP servers:

```python
from fastmcp import FastMCP
from fastmcp.server.proxy import ProxyClient

proxy = FastMCP.as_proxy(
    ProxyClient("backend_server.py"),
    name="MyProxy"
)
```

#### Benefits

- **Session Isolation**: Each request gets isolated sessions
- **Transport Bridging**: Expose servers on different transports
- **Advanced Feature Support**: Automatic forwarding of sampling, elicitation, logging, progress

**Performance Note**: Operations like `list_tools()` may take hundreds of milliseconds with HTTP backends vs 1-2ms for local tools.

---

### Sampling

Request LLM text generation from the client:

```python
@mcp.tool
async def analyze(text: str, ctx: Context) -> str:
    response = await ctx.sample(
        messages=f"Analyze this text: {text}",
        system_prompt="You are a text analyst",
        temperature=0.7,
        max_tokens=512
    )
    return response.text
```

#### Parameters

| Parameter | Description |
|-----------|-------------|
| `messages` | String or list of strings/SamplingMessage objects |
| `system_prompt` | Guides LLM behavior |
| `temperature` | Controls randomness (0.0-1.0) |
| `max_tokens` | Generation limit (default: 512) |
| `model_preferences` | Model selection hints |

---

### Storage Backends

Pluggable storage for caching and OAuth state management.

| Backend | Best For | Persistence |
|---------|----------|-------------|
| **In-Memory** (default) | Development | No |
| **Disk** | Single-server production | Yes |
| **Redis** | Distributed deployments | Yes |
| **DynamoDB, MongoDB** | Cloud deployments | Yes |

```python
from fastmcp.storage import DiskStore

storage = DiskStore(directory="/path/to/storage")
```

For OAuth tokens, wrap storage with encryption:

```python
from fastmcp.security import FernetEncryptionWrapper

secure_storage = FernetEncryptionWrapper(storage)
```

---

### Background Tasks

Run long-running operations asynchronously with progress tracking. Background tasks can be monitored for completion status.

---

## Authentication

Authentication applies only to HTTP-based transports (http and sse). STDIO inherits security from local execution.

### Authentication Overview

FastMCP addresses three MCP authentication challenges:
- **Automatic Discovery**: Clients examine server metadata
- **Programmatic OAuth**: Flows work without human interaction
- **Token Management**: Automatic token obtaining and refreshing

### Token Verification

Validate tokens from external systems without managing authentication:

```python
from fastmcp.server.auth.providers.jwt import JWTVerifier

verifier = JWTVerifier(
    jwks_uri="https://auth.company.com/.well-known/jwks.json",
    issuer="https://auth.company.com",
    audience="mcp-api"
)

mcp = FastMCP(name="MyServer", auth=verifier)
```

#### Verification Options

| Method | Use Case |
|--------|----------|
| **JWKS Endpoint** | Production with key rotation |
| **Symmetric Key (HMAC)** | Internal microservices |
| **Static Public Key** | Development |
| **Token Introspection** | Opaque tokens |

### Remote OAuth

Leverage external identity providers with Dynamic Client Registration (DCR):

```python
from fastmcp.server.auth import RemoteAuthProvider

auth = RemoteAuthProvider(
    token_verifier=verifier,
    authorization_servers=["https://auth.company.com"],
    base_url="https://api.company.com"
)
```

### OAuth Proxy

For providers without DCR support (GitHub, Google, Azure, Discord):

```python
from fastmcp.server.auth import OAuthProxy

auth = OAuthProxy(
    upstream_authorization_endpoint="https://github.com/login/oauth/authorize",
    upstream_token_endpoint="https://github.com/login/oauth/access_token",
    upstream_client_id="your-client-id",
    upstream_client_secret="your-secret",
    token_verifier=verifier,
    base_url="https://your-server.com"
)
```

### OIDC Proxy

For OIDC providers without DCR (Auth0, Google, Azure, AWS):

```python
from fastmcp.server.auth.oidc_proxy import OIDCProxy

auth = OIDCProxy(
    config_url="https://provider.com/.well-known/openid-configuration",
    client_id="your-client-id",
    client_secret="your-client-secret",
    base_url="https://your-server.com"
)
```

### Full OAuth Server

Implement a complete OAuth 2.0 authorization server when external providers cannot meet requirements. Your server manages users, issues tokens, and validates them independently.

---

## Deployment

### Running Your Server

#### Basic Execution

```python
if __name__ == "__main__":
    mcp.run()
```

#### Transport Options

| Transport | Use Case | Configuration |
|-----------|----------|---------------|
| **STDIO** (default) | Claude Desktop, local tools | `mcp.run()` |
| **HTTP** | Network services, multiple clients | `mcp.run(transport="http", host="0.0.0.0", port=8000)` |
| **SSE** | Legacy (deprecated) | `mcp.run(transport="sse")` |

#### Async Execution

```python
async def main():
    await mcp.run_async(transport="http", port=8000)
```

**Important**: Never call `run()` from within an async function.

#### CLI Usage

```bash
fastmcp run server.py
fastmcp run server.py --with pandas --with numpy
fastmcp run server.py --with-requirements requirements.txt
fastmcp run server.py -- --config config.json --debug
```

### HTTP Deployment

#### ASGI Application

```python
app = mcp.http_app()

# With custom path
app = mcp.http_app(path="/api/mcp/")
```

#### Running with Uvicorn

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

#### CORS Configuration

Only needed for browser-based clients:

```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://your-domain.com"],  # Never use "*" in production
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["mcp-protocol-version", "mcp-session-id", "Authorization", "Content-Type"],
        expose_headers=["mcp-session-id"]
    )
]
```

#### Custom Routes

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "healthy"})
```

#### Framework Integration

```python
# FastAPI
api = FastAPI()
api.mount("/mcp", mcp.http_app())

# Starlette
from starlette.routing import Mount
routes = [Mount("/mcp", app=mcp.http_app())]
```

### Project Configuration

Use `fastmcp.json` for declarative configuration (v2.12.0+):

```json
{
  "$schema": "https://gofastmcp.com/public/schemas/fastmcp.json/v1.json",
  "source": {
    "type": "filesystem",
    "path": "server.py"
  },
  "environment": {
    "type": "uv",
    "python": ">=3.10",
    "dependencies": ["requests", "aiohttp"]
  },
  "deployment": {
    "transport": "stdio",
    "log_level": "INFO",
    "env": {
      "API_KEY": "${API_KEY}"
    }
  }
}
```

Run with:

```bash
fastmcp run                          # Auto-detect fastmcp.json
fastmcp run prod.fastmcp.json        # Specify config file
```

---

## Critical Notes for This Project

1. **STDIO is the default transport** — This project uses STDIO for Claude Desktop integration
2. **Never use stdout** — All logging must go to stderr to avoid corrupting MCP JSON-RPC protocol
3. **Context requires async** — Context methods must be called from async functions
4. **Type hints are schemas** — FastMCP generates JSON schemas from Python type annotations
5. **Docstrings are descriptions** — Tool docstrings become the tool description shown to LLMs
6. **Authentication is HTTP-only** — Auth only applies to HTTP/SSE transports, not STDIO
7. **Request-scoped context** — Context state doesn't persist between requests

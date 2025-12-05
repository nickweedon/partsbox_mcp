# FastMCP Python SDK Reference

This document provides a comprehensive reference for the FastMCP Python SDK. It is sourced from the official FastMCP documentation at https://gofastmcp.com/python-sdk/.

For complete details, refer to:
- Official documentation: https://gofastmcp.com
- GitHub repository: https://github.com/jlowin/fastmcp

---

## Table of Contents

- [Exceptions](#exceptions)
- [Settings](#settings)
- [MCP Config](#mcp-config)
- [CLI](#cli)
  - [CLI Install](#cli-install)
  - [CLI Run](#cli-run)
- [Client](#client)
  - [Client Class](#client-class)
  - [Transports](#client-transports)
  - [Authentication](#client-authentication)
  - [Messages](#client-messages)
  - [Elicitation](#client-elicitation)
  - [Logging](#client-logging)
  - [Progress](#client-progress)
  - [Roots](#client-roots)
  - [Sampling](#client-sampling)
  - [OAuth Callback](#client-oauth-callback)
- [Server](#server)
  - [Server Auth](#server-auth)
  - [Server Auth Providers](#server-auth-providers)
  - [Context](#server-context)
  - [Dependencies](#server-dependencies)
  - [Elicitation](#server-elicitation)
  - [HTTP](#server-http)
  - [Low Level](#server-low-level)
  - [Middleware](#server-middleware)
  - [OpenAPI](#server-openapi)
  - [Proxy](#server-proxy)
- [Tools](#tools)
  - [Tool](#tool)
  - [Tool Manager](#tool-manager)
  - [Tool Transform](#tool-transform)
- [Resources](#resources)
  - [Resource](#resource)
  - [Resource Manager](#resource-manager)
  - [Template](#resource-template)
  - [Types](#resource-types)
- [Prompts](#prompts)
  - [Prompt](#prompt)
  - [Prompt Manager](#prompt-manager)
- [Utilities](#utilities)
  - [Auth](#utilities-auth)
  - [CLI](#utilities-cli)
  - [Components](#utilities-components)
  - [HTTP](#utilities-http)
  - [Inspect](#utilities-inspect)
  - [JSON Schema](#utilities-json-schema)
  - [JSON Schema Type](#utilities-json-schema-type)
  - [Logging](#utilities-logging)
  - [MCP Config](#utilities-mcp-config)
  - [Tests](#utilities-tests)
  - [Types](#utilities-types)
  - [UI](#utilities-ui)

---

## Exceptions

**Module:** `fastmcp.exceptions`

FastMCP provides a hierarchy of custom exceptions for error handling.

### Exception Hierarchy

```
Exception
└── FastMCPError (base for all FastMCP errors)
    ├── ValidationError (parameter/return value validation)
    ├── InvalidSignature (function signature issues)
    ├── ToolError (tool operations)
    ├── ResourceError (resource operations)
    ├── PromptError (prompt operations)
    ├── ClientError (client operations)
    ├── NotFoundError (object not found)
    └── DisabledError (object is disabled)
```

### FastMCPError

Base error for FastMCP. All other exceptions inherit from this class.

```python
from fastmcp.exceptions import FastMCPError

try:
    # FastMCP operations
    pass
except FastMCPError as e:
    print(f"FastMCP error: {e}")
```

### ToolError

Raised for tool-related operation errors. **Special behavior:** When `mask_error_details=True`, only `ToolError` messages are exposed to clients.

```python
from fastmcp import ToolError

@mcp.tool()
def my_tool(param: str) -> str:
    if not param:
        raise ToolError("Parameter cannot be empty")
    return f"Processed: {param}"
```

### Other Exceptions

| Exception | Purpose |
|-----------|---------|
| `ValidationError` | Parameter or return value validation fails |
| `InvalidSignature` | Function signature doesn't comply with FastMCP requirements |
| `ResourceError` | Resource-related operation errors |
| `PromptError` | Prompt-related operation errors |
| `ClientError` | Client-side operation errors |
| `NotFoundError` | Requested object cannot be located |
| `DisabledError` | Attempting to access a disabled object |

---

## Settings

**Module:** `fastmcp.settings`

### Settings Class

Manages FastMCP configuration options.

| Method | Description |
|--------|-------------|
| `get_setting(attr)` | Retrieve config value (supports nested with `__`) |
| `set_setting(attr, value)` | Set config value |
| `settings` | Backward-compatible property returning self |
| `normalize_log_level(v)` | Validator for log level standardization |
| `server_auth_class` | Returns configured AuthProvider or None |

### ExperimentalSettings

Settings class for experimental FastMCP features.

---

## MCP Config

**Module:** `fastmcp.mcp_config`

Defines the canonical MCP configuration format for client-agnostic, extensible configurations.

### Functions

| Function | Description |
|----------|-------------|
| `infer_transport_type_from_url(url)` | Determines transport type ('http' or 'sse') from URL |
| `update_config_file(file_path, server_name, server_config)` | Modifies MCP config file preserving existing settings |

### Classes

| Class | Description |
|-------|-------------|
| `StdioMCPServer` | Stdio-based server configuration with `to_transport()` |
| `RemoteMCPServer` | HTTP/SSE transport configuration with `to_transport()` |
| `MCPConfig` | Core configuration object with FastMCP extensions |
| `CanonicalMCPConfig` | Strictly canonical format without FastMCP extensions |

---

## CLI

**Module:** `fastmcp.cli`

Command-line interface for managing MCP servers.

### Commands

| Command | Description |
|---------|-------------|
| `fastmcp version` | Display version and platform information |
| `fastmcp run [server_spec]` | Execute MCP server or connect to remote instance |
| `fastmcp dev [server_spec]` | Launch server with MCP Inspector for development |
| `fastmcp inspect [server_spec]` | Analyze server and generate inspection reports |
| `fastmcp prepare [config_path]` | Create persistent uv environment with dependencies |

### CLI Install

**Module:** `fastmcp.cli.install`

Install commands for various MCP clients.

#### Claude Code

**Module:** `fastmcp.cli.install.claude_code`

| Function | Description |
|----------|-------------|
| `find_claude_command()` | Locate Claude Code CLI command path |
| `check_claude_code_available()` | Verify Claude Code CLI is installed |
| `install_claude_code(file, server_object, name)` | Install FastMCP server in Claude Code |
| `claude_code_command(server_spec)` | CLI command for Claude Code installation |

#### Claude Desktop

**Module:** `fastmcp.cli.install.claude_desktop`

| Function | Description |
|----------|-------------|
| `get_claude_config_path()` | Returns Claude config directory path |
| `install_claude_desktop(...)` | Install FastMCP server in Claude Desktop |
| `claude_desktop_command(server_spec)` | CLI command for Claude Desktop installation |

#### Cursor

**Module:** `fastmcp.cli.install.cursor`

| Function | Description |
|----------|-------------|
| `generate_cursor_deeplink(...)` | Create Cursor deeplink URL |
| `open_deeplink(url)` | Open deeplink using system handler |
| `install_cursor_workspace(...)` | Install to workspace-specific Cursor config |
| `install_cursor(...)` | Install FastMCP server in Cursor (global) |
| `cursor_command(server_spec)` | CLI command for Cursor installation |

#### Gemini CLI

**Module:** `fastmcp.cli.install.gemini_cli`

| Function | Description |
|----------|-------------|
| `find_gemini_command()` | Returns Gemini CLI command path |
| `check_gemini_cli_available()` | Verify Gemini CLI is installed |
| `install_gemini_cli(...)` | Install FastMCP server in Gemini CLI |
| `gemini_cli_command(server_spec)` | CLI command for Gemini CLI installation |

#### MCP JSON

**Module:** `fastmcp.cli.install.mcp_json`

| Function | Description |
|----------|-------------|
| `install_mcp_json(...)` | Generate MCP configuration JSON for manual installation |
| `mcp_json_command(server_spec)` | CLI command for JSON generation |

#### Shared Utilities

**Module:** `fastmcp.cli.install.shared`

| Function | Description |
|----------|-------------|
| `parse_env_var(env_var)` | Parse `KEY=VALUE` environment variable strings |
| `process_common_args(...)` | Handle common argument processing for install commands |

### CLI Run

**Module:** `fastmcp.cli.run`

| Function | Description |
|----------|-------------|
| `is_url(path)` | Check if string is URL |
| `create_client_server(url)` | Create FastMCP server from client URL |
| `create_mcp_config_server(path)` | Generate server from MCPConfig file |
| `load_mcp_server_config(path)` | Load config from fastmcp.json |
| `run_command(server_spec, ...)` | Primary function for executing servers |
| `run_v1_server_async(server, ...)` | Execute FastMCP 1.x server using async |

---

## Client

**Module:** `fastmcp.client`

### Client Class

**Module:** `fastmcp.client.client`

The `Client` class is the primary interface for interacting with MCP servers.

| Method | Description |
|--------|-------------|
| `initialize()` | Perform MCP initialization handshake (idempotent) |
| `list_tools()` | Discover available server tools |
| `call_tool(name, arguments)` | Execute a server tool |
| `list_resources()` | Access server resources |
| `read_resource(uri)` | Read resource content |
| `list_prompts()` | Retrieve prompt templates |
| `get_prompt(name, arguments)` | Get rendered prompt |
| `is_connected()` | Check connection status |
| `new()` | Create independent client instance with same config |

### Client Transports

**Module:** `fastmcp.client.transports`

#### `infer_transport()`
Automatically determines transport type from diverse inputs (ClientTransport, FastMCP instances, file paths, URLs, MCPConfig).

#### Transport Classes

| Class | Description |
|-------|-------------|
| `ClientTransport` | Abstract base for all transports |
| `WSTransport` | WebSocket connections |
| `SSETransport` | Server-Sent Events |
| `StreamableHttpTransport` | HTTP-based streaming (default for HTTP URLs) |
| `StdioTransport` | Base for subprocess-based transports |
| `PythonStdioTransport` | Execute Python scripts |
| `NodeStdioTransport` | Run Node.js scripts |
| `FastMCPStdioTransport` | Use FastMCP CLI |
| `UvStdioTransport` / `UvxStdioTransport` | UV tool execution |
| `NpxStdioTransport` | NPX package runner |
| `FastMCPTransport` | In-memory transport (same Python process) |
| `MCPConfigTransport` | Unified interface to multiple servers |

### Client Authentication

**Module:** `fastmcp.client.auth`

#### BearerAuth

**Module:** `fastmcp.client.auth.bearer`

Bearer token authentication for FastMCP clients.

```python
from fastmcp.client.auth.bearer import BearerAuth
auth = BearerAuth(token="your-token")
```

#### OAuth

**Module:** `fastmcp.client.auth.oauth`

OAuth 2.1 authentication with browser-based authorization.

| Item | Description |
|------|-------------|
| `check_if_auth_required(mcp_url)` | Check if endpoint requires auth |
| `ClientNotFoundError` | Exception when credentials not found |
| `TokenStorageAdapter` | Manages token persistence |
| `OAuth` | Primary OAuth client provider |

**OAuth Methods:**
- `redirect_handler(authorization_url)` - Open browser for authorization
- `callback_handler()` - Process OAuth callback, returns (code, state)
- `async_auth_flow(request)` - HTTPX auth flow with retry

### Client Messages

**Module:** `fastmcp.client.messages`

#### MessageHandler

Handles MCP messages sent to clients. Override hooks to customize behavior.

| Method | Description |
|--------|-------------|
| `dispatch(message)` | Route messages to handlers |
| `on_message(message)` | Generic handler for all messages |
| `on_request(message)` | Handle server requests |
| `on_ping(message)` | Handle keepalive pings |
| `on_list_roots(message)` | Handle root listing requests |
| `on_create_message(message)` | Process message creation requests |
| `on_notification(message)` | Handle server notifications |
| `on_exception(message)` | Handle processing errors |
| `on_progress(message)` | Track operation progress |
| `on_logging_message(message)` | Receive log messages |
| `on_tool_list_changed(message)` | Tool inventory changes |
| `on_resource_list_changed(message)` | Resource availability changes |
| `on_prompt_list_changed(message)` | Prompt template changes |
| `on_resource_updated(message)` | Resource content updates |
| `on_cancelled(message)` | Cancellation notifications |

### Client Elicitation

**Module:** `fastmcp.client.elicitation`

| Item | Description |
|------|-------------|
| `create_elicitation_callback(handler)` | Create callback for elicitation requests |
| `ElicitResult` | Result of elicitation operation |

### Client Logging

**Module:** `fastmcp.client.logging`

| Function | Description |
|----------|-------------|
| `default_log_handler(message)` | Routes server logs to appropriate levels |
| `create_log_callback(handler)` | Generate logging callback |

### Client Progress

**Module:** `fastmcp.client.progress`

```python
def default_progress_handler(progress: float, total: float | None, message: str | None) -> None
```

Handles progress notifications by logging at debug level.

### Client Roots

**Module:** `fastmcp.client.roots`

| Function | Description |
|----------|-------------|
| `convert_roots_list(roots)` | Transform roots to MCP Root types |
| `create_roots_callback(handler)` | Generate root listing callback |

### Client Sampling

**Module:** `fastmcp.client.sampling`

```python
def create_sampling_callback(sampling_handler) -> SamplingFnT
```

Creates callback for handling LLM sampling requests from servers.

### Client OAuth Callback

**Module:** `fastmcp.client.oauth_callback`

| Function | Description |
|----------|-------------|
| `create_callback_html(message, is_success, ...)` | Create styled OAuth response HTML |
| `create_oauth_callback_server(port, callback_path, ...)` | Create uvicorn server for OAuth callbacks |

| Class | Description |
|-------|-------------|
| `CallbackResponse` | OAuth callback data with `from_dict()` and `to_dict()` |
| `OAuthCallbackResult` | Container for async callback coordination |

---

## Server

**Module:** `fastmcp.server`

### FastMCP Class

The main server class for building MCP servers.

**Execution Methods:**
- `run()` / `run_async()` - Start server
- `run_stdio_async()` - Stdio transport
- `run_http_async()` - HTTP transport
- `http_app()` - Create Starlette ASGI app

**Management Methods:**
- `add_middleware()` - Register middleware
- `add_tool()` / `remove_tool()` - Tool registration
- `add_resource()` / `add_template()` - Resource management
- `add_prompt()` - Prompt registration
- `get_tools()` / `get_resources()` / `get_prompts()` - Retrieve items
- `custom_route()` - Register custom HTTP endpoints

**Composition:**
- `mount()` - Dynamic server connection
- `import_server()` - One-time registration
- `from_openapi()` - Create from OpenAPI spec
- `from_fastapi()` - Create from FastAPI app
- `as_proxy()` - Create proxy for external backend

### Server Auth

**Module:** `fastmcp.server.auth`

#### Core Classes

**Module:** `fastmcp.server.auth.auth`

| Class | Description |
|-------|-------------|
| `AccessToken` | Data structure containing JWT claims |
| `AuthProvider` | Base class for authentication implementations |
| `TokenVerifier` | Base implementation for token validation |
| `RemoteAuthProvider` | Resource server that validates tokens from authorization servers |
| `OAuthProvider` | Complete OAuth Authorization Server implementation |

**AuthProvider Methods:**
- `verify_token(token)` - Validate bearer tokens
- `get_routes(mcp_path)` - Get authentication routes
- `get_well_known_routes(mcp_path)` - Get discovery endpoints
- `get_middleware()` - Get HTTP middleware

#### JWT Issuer

**Module:** `fastmcp.server.auth.jwt_issuer`

| Item | Description |
|------|-------------|
| `derive_jwt_key(...)` | Derive JWT signing key from key material |
| `JWTIssuer` | Issues and validates FastMCP-signed JWT tokens |

**JWTIssuer Methods:**
- `issue_access_token(client_id, scopes, jti, ...)` - Issue access token
- `issue_refresh_token(client_id, scopes, jti, ...)` - Issue refresh token
- `verify_token(token)` - Verify and decode tokens

#### Auth Middleware

**Module:** `fastmcp.server.auth.middleware`

| Class | Description |
|-------|-------------|
| `RequireAuthMiddleware` | Enhanced authentication middleware with detailed error messages |

#### OAuth Proxy

**Module:** `fastmcp.server.auth.oauth_proxy`

| Item | Description |
|------|-------------|
| `create_consent_html(...)` | Generate styled HTML consent pages |
| `create_error_html(...)` | Produce styled HTML error pages |
| `OAuthTransaction` | Server-side state for consent flows |
| `ClientCode` | Client authorization codes bound to PKCE |
| `UpstreamTokenSet` | Holds upstream OAuth tokens |
| `ProxyDCRClient` | Custom DCR client with redirect URI validation |
| `TokenHandler` | OAuth 2.1-compliant error responses |
| `OAuthProxy` | Core proxy for non-DCR identity providers |

#### OIDC Proxy

**Module:** `fastmcp.server.auth.oidc_proxy`

| Class | Description |
|-------|-------------|
| `OIDCConfiguration` | OIDC configuration with `get_oidc_configuration()` |
| `OIDCProxy` | Transparent proxy to OIDC-compliant authorization servers |

#### Redirect Validation

**Module:** `fastmcp.server.auth.redirect_validation`

| Function | Description |
|----------|-------------|
| `matches_allowed_pattern(uri, pattern)` | Check URI matches pattern with wildcards |
| `validate_redirect_uri(redirect_uri, allowed_patterns)` | Validate redirect URI against patterns |

### Server Auth Providers

**Module:** `fastmcp.server.auth.providers`

#### Auth0

**Module:** `fastmcp.server.auth.providers.auth0`

| Class | Description |
|-------|-------------|
| `Auth0ProviderSettings` | Settings for Auth0 OIDC provider |
| `Auth0Provider` | Complete Auth0 implementation |

#### AWS Cognito

**Module:** `fastmcp.server.auth.providers.aws`

| Class | Description |
|-------|-------------|
| `AWSCognitoProviderSettings` | Settings for AWS Cognito |
| `AWSCognitoTokenVerifier` | Token verifier with Cognito-specific claim filtering |
| `AWSCognitoProvider` | Complete AWS Cognito OAuth provider |

#### Azure (Microsoft Entra ID)

**Module:** `fastmcp.server.auth.providers.azure`

| Class | Description |
|-------|-------------|
| `AzureProviderSettings` | Settings for Azure OAuth provider |
| `AzureProvider` | Azure/Microsoft Entra ID authentication using OAuth Proxy |

#### Debug

**Module:** `fastmcp.server.auth.providers.debug`

| Class | Description |
|-------|-------------|
| `DebugTokenVerifier` | Flexible token verifier for testing/development |

**Warning:** Bypasses standard security checks. Only use in controlled environments.

#### Descope

**Module:** `fastmcp.server.auth.providers.descope`

| Class | Description |
|-------|-------------|
| `DescopeProviderSettings` | Settings for Descope provider |
| `DescopeProvider` | Descope integration using metadata forwarding for DCR |

#### Discord

**Module:** `fastmcp.server.auth.providers.discord`

| Class | Description |
|-------|-------------|
| `DiscordProviderSettings` | Settings for Discord OAuth |
| `DiscordTokenVerifier` | Validates tokens via Discord's tokeninfo API |
| `DiscordProvider` | Complete Discord OAuth implementation |

#### GitHub

**Module:** `fastmcp.server.auth.providers.github`

| Class | Description |
|-------|-------------|
| `GitHubProviderSettings` | Settings for GitHub OAuth |
| `GitHubTokenVerifier` | Validates tokens via GitHub API |
| `GitHubProvider` | Complete GitHub OAuth implementation |

#### Google

**Module:** `fastmcp.server.auth.providers.google`

| Class | Description |
|-------|-------------|
| `GoogleProviderSettings` | Settings for Google OAuth |
| `GoogleTokenVerifier` | Validates tokens via Google's tokeninfo API |
| `GoogleProvider` | Complete Google OAuth implementation |

#### In-Memory

**Module:** `fastmcp.server.auth.providers.in_memory`

| Class | Description |
|-------|-------------|
| `InMemoryOAuthProvider` | OAuth 2.1 simulation for testing (no external calls) |

#### Introspection

**Module:** `fastmcp.server.auth.providers.introspection`

| Class | Description |
|-------|-------------|
| `IntrospectionTokenVerifierSettings` | Settings for token introspection |
| `IntrospectionTokenVerifier` | Validates opaque tokens via RFC 7662 introspection |

#### JWT

**Module:** `fastmcp.server.auth.providers.jwt`

| Class | Description |
|-------|-------------|
| `JWKData` / `JWKSData` | JSON Web Key data structures |
| `RSAKeyPair` | RSA key pair utility for testing |
| `JWTVerifierSettings` | Settings for JWT verification |
| `JWTVerifier` | Comprehensive JWT verifier (RS/ES/PS/HS algorithms) |
| `StaticTokenVerifier` | Simple verifier for testing with predefined tokens |

#### OCI

**Module:** `fastmcp.server.auth.providers.oci`

| Class | Description |
|-------|-------------|
| `OCIProviderSettings` | Settings for OCI IAM domain |
| `OCIProvider` | OCI IAM Domain authentication with token exchange |

#### Scalekit

**Module:** `fastmcp.server.auth.providers.scalekit`

| Class | Description |
|-------|-------------|
| `ScalekitProviderSettings` | Settings for Scalekit provider |
| `ScalekitProvider` | Resource server validating tokens from Scalekit |

#### Supabase

**Module:** `fastmcp.server.auth.providers.supabase`

| Class | Description |
|-------|-------------|
| `SupabaseProviderSettings` | Settings for Supabase provider |
| `SupabaseProvider` | Supabase Auth integration using metadata forwarding |

#### WorkOS

**Module:** `fastmcp.server.auth.providers.workos`

| Class | Description |
|-------|-------------|
| `WorkOSProviderSettings` | Settings for WorkOS OAuth |
| `WorkOSTokenVerifier` | Validates tokens via `/oauth2/userinfo` |
| `WorkOSProvider` | WorkOS AuthKit OAuth using OAuth Proxy |
| `AuthKitProviderSettings` | Settings for AuthKit metadata provider |
| `AuthKitProvider` | AuthKit integration using metadata forwarding |

### Server Context

**Module:** `fastmcp.server.context`

#### Context Class

Access MCP features during tool execution.

**Logging:** `debug()`, `info()`, `warning()`, `error()`, `log()`

**Resource/Prompt Access:** `list_resources()`, `list_prompts()`, `read_resource(uri)`, `get_prompt(name, arguments)`

**Progress/Operations:** `report_progress(progress, total, message)`, `list_roots()`, `session_id`

**Advanced:** `sample()`, `elicit()`, `set_state()`, `get_state()`

**Notifications:** `send_tool_list_changed()`, `send_resource_list_changed()`, `send_prompt_list_changed()`

#### Other Items

| Item | Description |
|------|-------------|
| `LogData` | Data object for structured logging |
| `set_context()` | Context manager for MCP context scope |

### Server Dependencies

**Module:** `fastmcp.server.dependencies`

| Function | Description |
|----------|-------------|
| `get_context()` | Retrieve current MCP context |
| `get_http_request()` | Get underlying HTTP request |
| `get_http_headers(include_all=False)` | Extract headers (empty dict if no HTTP context) |
| `get_access_token()` | Get FastMCP access token or None |

### Server Elicitation

**Module:** `fastmcp.server.elicitation`

| Item | Description |
|------|-------------|
| `get_elicitation_schema(response_type)` | Get schema for elicitation response |
| `validate_elicitation_json_schema(schema)` | Validate MCP compatibility |
| `ElicitationJsonSchema` | Custom schema generator for MCP |
| `AcceptedElicitation` | Result when user accepts |
| `ScalarElicitationType` | Type for scalar values |

### Server HTTP

**Module:** `fastmcp.server.http`

| Function | Description |
|----------|-------------|
| `set_http_request(request)` | Context manager storing request in ContextVar |
| `create_base_app(routes, middleware, ...)` | Create foundational Starlette app |
| `create_sse_app(server, ...)` | Create SSE transport app |
| `create_streamable_http_app(server, ...)` | Create Streamable HTTP app |

| Class | Description |
|-------|-------------|
| `StreamableHTTPASGIApp` | ASGI wrapper for Streamable HTTP |
| `StarletteWithLifespan` | Extended Starlette with lifespan management |
| `RequestContextMiddleware` | Captures requests in ContextVar |

### Server Low Level

**Module:** `fastmcp.server.low_level`

| Class | Description |
|-------|-------------|
| `MiddlewareServerSession` | Routes initialization through middleware |
| `LowLevelServer` | Manages low-level operations |

### Server Middleware

**Module:** `fastmcp.server.middleware`

#### Middleware Base

**Module:** `fastmcp.server.middleware.middleware`

| Item | Description |
|------|-------------|
| `make_middleware_wrapper(...)` | Create wrapper applying middleware to context |
| `CallNext` | Callable type for next handler in chain |
| `MiddlewareContext` | Unified context for middleware operations |
| `Middleware` | Base class with dispatching hooks |

**Middleware Hooks:**
`on_message()`, `on_request()`, `on_notification()`, `on_initialize()`, `on_call_tool()`, `on_read_resource()`, `on_get_prompt()`, `on_list_tools()`, `on_list_resources()`, `on_list_resource_templates()`, `on_list_prompts()`

#### Caching Middleware

**Module:** `fastmcp.server.middleware.caching`

| Class | Description |
|-------|-------------|
| `CachableReadResourceContents` | Wrapper for cacheable resource content |
| `CachableToolResult` | Wrapper for tool results |
| `ResponseCachingMiddleware` | Core response caching middleware |
| `ResponseCachingStatistics` | Cache statistics tracking |

#### Logging Middleware

**Module:** `fastmcp.server.middleware.logging`

| Item | Description |
|------|-------------|
| `default_serializer(data)` | Default serializer for payloads |
| `BaseLoggingMiddleware` | Base class for logging middleware |
| `LoggingMiddleware` | Comprehensive request/response logging |
| `StructuredLoggingMiddleware` | Structured JSON logging for log aggregation |

#### Rate Limiting Middleware

**Module:** `fastmcp.server.middleware.rate_limiting`

| Class | Description |
|-------|-------------|
| `RateLimitError` | Error raised when rate limit exceeded |
| `TokenBucketRateLimiter` | Token bucket rate limiting algorithm |
| `SlidingWindowRateLimiter` | Sliding window rate limiting algorithm |
| `RateLimitingMiddleware` | Token bucket middleware (allows burst) |
| `SlidingWindowRateLimitingMiddleware` | Sliding window middleware (precise) |

#### Timing Middleware

**Module:** `fastmcp.server.middleware.timing`

| Class | Description |
|-------|-------------|
| `TimingMiddleware` | Logs execution time of requests |
| `DetailedTimingMiddleware` | Per-operation timing breakdowns |

#### Tool Injection Middleware

**Module:** `fastmcp.server.middleware.tool_injection`

| Class | Description |
|-------|-------------|
| `ToolInjectionMiddleware` | Base for injecting tools into context |
| `PromptToolMiddleware` | Inject prompts as tools |
| `ResourceToolMiddleware` | Inject resources as tools |

### Server OpenAPI

**Module:** `fastmcp.server.openapi`

#### Components

**Module:** `fastmcp.server.openapi.components`

| Class | Description |
|-------|-------------|
| `OpenAPITool` | Tool implementation for OpenAPI endpoints |
| `OpenAPIResource` | Resource implementation for OpenAPI endpoints |
| `OpenAPIResourceTemplate` | Resource template for OpenAPI endpoints |

#### Routing

**Module:** `fastmcp.server.openapi.routing`

| Class | Description |
|-------|-------------|
| `MCPType` | Enum for FastMCP component types from routes |
| `RouteMap` | Mapping configuration for HTTP routes to components |

#### Server

**Module:** `fastmcp.server.openapi.server`

| Class | Description |
|-------|-------------|
| `FastMCPOpenAPI` | FastMCP server creating components from OpenAPI schema |

### Server Proxy

**Module:** `fastmcp.server.proxy`

| Function | Description |
|----------|-------------|
| `default_proxy_roots_handler` | Forward roots requests to clients |

| Class | Description |
|-------|-------------|
| `ProxyManagerMixin` | Base for unified client retrieval |
| `ProxyToolManager` | Sources tools from remote + local |
| `ProxyResourceManager` | Manages resources from multiple sources |
| `ProxyPromptManager` | Handles prompts from multiple sources |
| `ProxyTool/Resource/Template/Prompt` | Wrappers for remote MCP objects |
| `FastMCPProxy` | Main proxy server implementation |
| `ProxyClient` | Forwards sampling, elicitation, logging, progress |
| `StatefulProxyClient` | Maintains session-bound instances |

---

## Tools

### Tool

**Module:** `fastmcp.tools.tool`

| Function | Description |
|----------|-------------|
| `default_serializer(data)` | Convert data to string for results |

| Class | Description |
|-------|-------------|
| `ToolResult` | Outcome of tool execution with `to_mcp_result()` |
| `Tool` | Internal tool registration info |
| `FunctionTool` | Tool wrapping functions |
| `ParsedFunction` | Analyzes function signatures |

**Tool Methods:** `enable()`, `disable()`, `to_mcp_tool()`, `from_function()`, `run()`, `from_tool()`

### Tool Manager

**Module:** `fastmcp.tools.tool_manager`

| Method | Description |
|--------|-------------|
| `has_tool(key)` | Check if tool exists |
| `get_tool(key)` | Retrieve tool by key |
| `get_tools()` | Get all registered tools |
| `add_tool_from_fn(fn, ...)` | Register function as tool |
| `add_tool(tool)` | Register Tool object |
| `add_tool_transformation(tool_name, transformation)` | Apply transformations |
| `get_tool_transformation(tool_name)` | Get active transformations |
| `remove_tool_transformation(tool_name)` | Remove transformations |
| `remove_tool(key)` | Unregister tool |
| `call_tool(key, arguments)` | Execute tool |

### Tool Transform

**Module:** `fastmcp.tools.tool_transform`

Create enhanced tool variants with modified schemas and argument mappings.

| Function | Description |
|----------|-------------|
| `forward(**kwargs)` | Forward args to parent with transformation |
| `forward_raw(**kwargs)` | Bypass transformation, call parent directly |
| `apply_transformations_to_tools()` | Apply configs to multiple tools |

| Class | Description |
|-------|-------------|
| `ArgTransform` | Configure argument transformations |
| `TransformedTool` | Tool created by transforming another |
| `ToolTransformConfig` | Declarative transformation specification |

---

## Resources

### Resource

**Module:** `fastmcp.resources.resource`

| Class | Description |
|-------|-------------|
| `Resource` | Base class for all resources |
| `FunctionResource` | Defers data loading via wrapped functions |

**Resource Methods:** `enable()`, `disable()`, `from_function()`, `set_default_mime_type()`, `set_default_name()`, `read()`, `to_mcp_resource()`, `key()`

### Resource Manager

**Module:** `fastmcp.resources.resource_manager`

| Method | Description |
|--------|-------------|
| `get_resources()` | Get all resources by URI |
| `get_resource_templates()` | Get all templates |
| `add_resource_or_template_from_fn(fn, uri, ...)` | Register function as resource or template |
| `add_resource_from_fn(fn, ...)` | Register function as resource |
| `add_resource(resource)` | Register Resource instance |
| `add_template_from_fn(fn, uri_template, ...)` | Create template from function |
| `add_template(template)` | Register ResourceTemplate |
| `has_resource(uri)` | Check if resource exists |
| `get_resource(uri)` | Retrieve by URI |
| `read_resource(uri)` | Read resource content |

### Resource Template

**Module:** `fastmcp.resources.template`

| Function | Description |
|----------|-------------|
| `extract_query_params(uri_template)` | Extract query params from RFC 6570 syntax |
| `build_regex(template)` | Build regex for URI templates |
| `match_uri_template(uri, uri_template)` | Match and extract parameters |

| Class | Description |
|-------|-------------|
| `ResourceTemplate` | Template for dynamic resources |
| `FunctionResourceTemplate` | Function-based template |

### Resource Types

**Module:** `fastmcp.resources.types`

| Class | Description |
|-------|-------------|
| `TextResource` | Reads from string data |
| `BinaryResource` | Reads from bytes data |
| `FileResource` | Reads file content (text or binary) |
| `HttpResource` | Reads from HTTP endpoints |
| `DirectoryResource` | Lists and reads directory files |

---

## Prompts

### Prompt

**Module:** `fastmcp.prompts.prompt`

| Function | Description |
|----------|-------------|
| `Message(content, role, **kwargs)` | Create PromptMessage objects |

| Class | Description |
|-------|-------------|
| `PromptArgument` | Argument for prompt templates |
| `Prompt` | Base class for prompts |
| `FunctionPrompt` | Function-defined prompt |

**Prompt Methods:** `enable()`, `disable()`, `to_mcp_prompt()`, `from_function()`, `render()`

### Prompt Manager

**Module:** `fastmcp.prompts.prompt_manager`

| Method | Description |
|--------|-------------|
| `has_prompt(key)` | Check if prompt exists |
| `get_prompt(key)` | Retrieve by key |
| `get_prompts()` | Get all prompts |
| `add_prompt_from_fn(fn, ...)` | Create from function |
| `add_prompt(prompt)` | Register Prompt object |
| `render_prompt(name, arguments)` | Locate and render prompt |

---

## Utilities

### Utilities Auth

**Module:** `fastmcp.utilities.auth`

| Function | Description |
|----------|-------------|
| `parse_scopes(value)` | Parse scopes from env vars (JSON array, comma/space-separated, list) |

### Utilities CLI

**Module:** `fastmcp.utilities.cli`

| Function | Description |
|----------|-------------|
| `is_already_in_uv_subprocess()` | Check if running in FastMCP uv subprocess |
| `load_and_merge_config(server_spec, **cli_overrides)` | Load config and apply CLI overrides |
| `log_server_banner(server, transport)` | Log formatted banner with server info |

### Utilities Components

**Module:** `fastmcp.utilities.components`

| Class | Description |
|-------|-------------|
| `FastMCPMeta` | Metaclass for components |
| `FastMCPComponent` | Base for tools, prompts, resources |
| `MirroredComponent` | Components mirrored from remote servers |

**FastMCPComponent Methods:** `key()`, `get_meta()`, `model_copy()`, `enable()`, `disable()`, `copy()`

### Utilities HTTP

**Module:** `fastmcp.utilities.http`

```python
def find_available_port() -> int
```

Find an available port by letting OS assign one.

### Utilities Inspect

**Module:** `fastmcp.utilities.inspect`

| Function | Description |
|----------|-------------|
| `inspect_fastmcp_v2(mcp)` | Extract info from v2.x instance |
| `inspect_fastmcp_v1(mcp)` | Extract info from v1.x instance |
| `inspect_fastmcp(mcp)` | Auto-detect version and extract |
| `format_fastmcp_info(info)` | Convert to FastMCP JSON format |
| `format_mcp_info(mcp)` | Generate standard MCP JSON |
| `format_info(mcp, format, info)` | Flexible formatting |

| Class | Description |
|-------|-------------|
| `ToolInfo`, `PromptInfo`, `ResourceInfo`, `TemplateInfo` | Metadata containers |
| `FastMCPInfo` | Aggregated server information |
| `InspectFormat` | Output format enumeration |

### Utilities JSON Schema

**Module:** `fastmcp.utilities.json_schema`

```python
def compress_schema(
    schema: dict,
    prune_params: list[str] | None = None,
    prune_defs: bool = True,
    prune_additional_properties: bool = True,
    prune_titles: bool = False
) -> dict
```

Remove specified parameters and optimize JSON schemas.

### Utilities JSON Schema Type

**Module:** `fastmcp.utilities.json_schema_type`

```python
def json_schema_to_type(schema: Mapping[str, Any], name: str | None = None) -> type
```

Convert JSON Schema to Python type with Pydantic validation.

**Supports:** Fundamental types, arrays, objects, format validation, numeric limits, string constraints, array constraints, references, enums, unions.

### Utilities Logging

**Module:** `fastmcp.utilities.logging`

| Function | Description |
|----------|-------------|
| `get_logger(name)` | Get logger nested in FastMCP namespace |
| `configure_logging(level, logger, ...)` | Set up logging configuration |
| `temporary_log_level(level, ...)` | Context manager for temporary log level |

### Utilities MCP Config

**Module:** `fastmcp.utilities.mcp_config`

| Function | Description |
|----------|-------------|
| `mcp_config_to_servers_and_transports(config)` | Convert MCPConfig to list of (name, server, transport) |
| `mcp_server_type_to_servers_and_transports(name, server)` | Convert single entry |

### Utilities Tests

**Module:** `fastmcp.utilities.tests`

| Function | Description |
|----------|-------------|
| `temporary_settings(**kwargs)` | Override settings temporarily |
| `run_server_in_process(server_fn, ...)` | Execute server in separate process |
| `run_server_async(server, ...)` | Start server as asyncio task (recommended) |
| `caplog_for_fastmcp(caplog)` | Capture FastMCP logs |

| Class | Description |
|-------|-------------|
| `HeadlessOAuth` | Simulate OAuth flow programmatically |

### Utilities Types

**Module:** `fastmcp.utilities.types`

| Function | Description |
|----------|-------------|
| `get_fn_name(fn)` | Get callable name |
| `get_cached_typeadapter(cls)` | Create/cache TypeAdapters |
| `issubclass_safe(cls, base)` | Safe subclass check |
| `is_class_member_of_type(cls, base)` | Validate type membership |
| `find_kwarg_by_type(fn, kwarg_type)` | Find kwarg by type |
| `create_function_without_params(fn, exclude_params)` | Create variant without params |
| `replace_type(type_, type_map)` | Transform types with substitutions |

| Class | Description |
|-------|-------------|
| `Image` | Image data with `to_image_content()`, `to_data_uri()` |
| `Audio` | Audio data with `to_audio_content()` |
| `File` | File data with `to_resource_content()` |
| `FastMCPBaseModel` | Base Pydantic model |

### Utilities UI

**Module:** `fastmcp.utilities.ui`

Reusable HTML/CSS components for OAuth callbacks and user interfaces.

| Function | Description |
|----------|-------------|
| `create_page(content, title, ...)` | Create complete HTML page |
| `create_logo(icon_url, alt_text)` | Generate logo HTML |
| `create_status_message(message, is_success)` | Build status message |
| `create_info_box(content, is_error, ...)` | Create info container |
| `create_detail_box(rows)` | Build key-value display |
| `create_button_group(buttons)` | Generate button collection |
| `create_secure_html_response(html, status_code)` | HTMLResponse with security headers |

---

## Critical Notes for This Project

1. **Use ToolError for client-facing messages** — When `mask_error_details=True`, only `ToolError` messages are sent to clients
2. **Log to stderr** — Always log errors to stderr, never stdout, to avoid corrupting MCP protocol
3. **Catch FastMCPError broadly** — Use the base class to catch all FastMCP exceptions when needed
4. **Be specific when possible** — Catch specific exceptions for targeted error handling
5. **Convert internal errors** — Wrap internal exceptions in appropriate FastMCP exceptions with user-friendly messages
6. **Context is request-scoped** — State set via `ctx.set_state()` doesn't persist between requests
7. **Authentication is HTTP-only** — Auth only applies to HTTP/SSE transports, not STDIO

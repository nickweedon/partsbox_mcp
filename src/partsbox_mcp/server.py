"""
PartsBox MCP Server - Main Entry Point

This module sets up the FastMCP server and registers all tools
from the API modules.
"""

from fastmcp import FastMCP

from partsbox_mcp.api import parts
from partsbox_mcp.client import CacheInfo, cache

# =============================================================================
# Server Setup
# =============================================================================

mcp = FastMCP("PartsBox MCP Server")


# =============================================================================
# Parts Tools
# =============================================================================


@mcp.tool()
def list_parts(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> parts.PaginatedPartsResponse:
    """
    List all parts with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection. Examples:
            - "[?contains(name, 'resistor')]" - filter by name
            - "[?stock > `100`]" - filter by stock level
            - "[?stock < `10`].{name: name, stock: stock}" - filter + projection
            - "sort_by([?stock > `0`], &name)" - filter + sort

    Returns:
        PaginatedPartsResponse with parts data and pagination info
    """
    return parts.list_parts(
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_part(part_id: str) -> parts.PartResponse:
    """
    Get detailed information for a specific part.

    Args:
        part_id: The unique identifier of the part

    Returns:
        PartResponse with part data or error
    """
    return parts.get_part(part_id)


# =============================================================================
# Cache Tools
# =============================================================================


@mcp.tool()
def get_cache_info(cache_key: str) -> CacheInfo:
    """
    Get information about a pagination cache entry.

    Args:
        cache_key: The cache key to look up

    Returns:
        CacheInfo with validity and timing information
    """
    return cache.get_info(cache_key)


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Run the PartsBox MCP Server."""
    mcp.run()


if __name__ == "__main__":
    main()

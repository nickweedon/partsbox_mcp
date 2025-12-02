"""
Parts API module.

Provides MCP tools for part/all and part/get operations.
"""

from dataclasses import dataclass

import requests

from partsbox_mcp.client import api_client, apply_query, cache
from partsbox_mcp.types import PartData


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class PaginatedPartsResponse:
    """Response for paginated parts listing."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[PartData]
    error: str | None = None
    query_applied: str | None = None


@dataclass
class PartResponse:
    """Response for a single part."""

    success: bool
    data: PartData | None = None
    error: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def list_parts(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedPartsResponse:
    """
    List all parts with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "part/name").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "part/name", "part/tags", "part/mpn"
            - WRONG: `part/name` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `part/tags` evaluates to the literal string "part/tags", not the field value.

            Standard JMESPath examples:
            - "[?\"part/manufacturer\" == 'Texas Instruments']" - filter by manufacturer
            - "[?contains(\"part/tags\", 'resistor')]" - filter by tag
            - "sort_by(@, &\"part/name\")" - sort by name
            - "[*].{id: \"part/id\", name: \"part/name\"}" - projection with field access

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"part/name\", ''), 'resistor')]" - safe name search
            - "[?contains(nvl(\"part/description\", ''), 'SMD')]" - safe description search
            - "[?contains(nvl(\"part/mpn\", ''), 'RC0805')]" - safe MPN search

    Returns:
        PaginatedPartsResponse with parts data and pagination info.

        Data items schema:
        {
            "type": "object",
            "required": ["part/id", "part/name", "part/type", "part/created", "part/owner"],
            "properties": {
                "part/id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "part/name": {"type": "string", "description": "Part name or internal identifier"},
                "part/type": {"type": "string", "enum": ["local", "linked", "sub-assembly", "meta"], "description": "Part type"},
                "part/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "part/owner": {"type": "string", "description": "Owner identifier (26-char compact UUID)"},
                "part/description": {"type": ["string", "null"], "description": "Part description"},
                "part/notes": {"type": ["string", "null"], "description": "User notes (Markdown supported)"},
                "part/footprint": {"type": ["string", "null"], "description": "Physical package footprint"},
                "part/manufacturer": {"type": ["string", "null"], "description": "Manufacturer name"},
                "part/mpn": {"type": ["string", "null"], "description": "Manufacturer part number"},
                "part/linked-id": {"type": ["string", "null"], "description": "Linked part identifier (for linked parts)"},
                "part/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "part/cad-keys": {"type": "array", "items": {"type": "string"}, "description": "CAD keys for matching"},
                "part/attrition": {
                    "type": ["object", "null"],
                    "description": "Attrition settings for manufacturing",
                    "properties": {
                        "percentage": {"type": "number", "description": "Attrition percentage"},
                        "quantity": {"type": "integer", "description": "Fixed attrition quantity"}
                    }
                },
                "part/low-stock": {
                    "type": ["object", "null"],
                    "description": "Low stock threshold settings",
                    "properties": {
                        "report": {"type": "integer", "description": "Report when stock falls below this level"}
                    }
                },
                "part/custom-fields": {"type": ["object", "null"], "description": "Custom field data"},
                "part/stock": {
                    "type": "array",
                    "description": "Stock history entries",
                    "items": {
                        "type": "object",
                        "required": ["stock/quantity", "stock/storage-id", "stock/timestamp"],
                        "properties": {
                            "stock/quantity": {"type": "integer", "description": "Stock quantity"},
                            "stock/storage-id": {"type": "string", "description": "Storage location identifier"},
                            "stock/timestamp": {"type": "integer", "description": "Entry timestamp (UNIX UTC milliseconds)"},
                            "stock/lot-id": {"type": ["string", "null"], "description": "Lot identifier"},
                            "stock/price": {"type": ["number", "null"], "description": "Unit price"},
                            "stock/currency": {"type": ["string", "null"], "description": "Currency code (e.g., 'usd', 'eur')"},
                            "stock/comments": {"type": ["string", "null"], "description": "Entry notes"},
                            "stock/user": {"type": ["string", "null"], "description": "User who created the entry"},
                            "stock/status": {"type": ["string", "null"], "description": "Stock status (ordered, reserved, etc.) or null for on-hand"},
                            "stock/order-id": {"type": ["string", "null"], "description": "Parent order identifier"},
                            "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU"}
                        }
                    }
                }
            }
        }
    """
    # Validate parameters
    if limit < 1 or limit > 1000:
        return PaginatedPartsResponse(
            success=False,
            error="limit must be between 1 and 1000",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if offset < 0:
        return PaginatedPartsResponse(
            success=False,
            error="offset must be non-negative",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    # Get or fetch data
    try:
        if cache_key:
            entry = cache.get(cache_key)
            if entry:
                data = entry.data
                key = cache_key
            else:
                # Cache miss - fetch fresh
                data = api_client.get_all_parts()
                key = cache.create(data)
        else:
            data = api_client.get_all_parts()
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedPartsResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    # Apply JMESPath query
    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedPartsResponse(
                success=False,
                error=error,
                cache_key=key,
                total=0,
                offset=0,
                limit=limit,
                has_more=False,
                query_applied=query,
                data=[],
            )
    else:
        result = data

    # Handle non-list results (aggregation queries)
    if not isinstance(result, list):
        return PaginatedPartsResponse(
            success=True,
            cache_key=key,
            total=1,
            offset=0,
            limit=limit,
            has_more=False,
            query_applied=query,
            data=[result],
        )

    total = len(result)

    # Paginate
    page = result[offset : offset + limit]

    return PaginatedPartsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_part(part_id: str) -> PartResponse:
    """
    Get detailed information for a specific part.

    Args:
        part_id: The unique identifier of the part

    Returns:
        PartResponse with part data or error.

        Data schema:
        {
            "type": "object",
            "required": ["part/id", "part/name", "part/type", "part/created", "part/owner"],
            "properties": {
                "part/id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "part/name": {"type": "string", "description": "Part name or internal identifier"},
                "part/type": {"type": "string", "enum": ["local", "linked", "sub-assembly", "meta"], "description": "Part type"},
                "part/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "part/owner": {"type": "string", "description": "Owner identifier (26-char compact UUID)"},
                "part/description": {"type": ["string", "null"], "description": "Part description"},
                "part/notes": {"type": ["string", "null"], "description": "User notes (Markdown supported)"},
                "part/footprint": {"type": ["string", "null"], "description": "Physical package footprint"},
                "part/manufacturer": {"type": ["string", "null"], "description": "Manufacturer name"},
                "part/mpn": {"type": ["string", "null"], "description": "Manufacturer part number"},
                "part/linked-id": {"type": ["string", "null"], "description": "Linked part identifier (for linked parts)"},
                "part/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "part/cad-keys": {"type": "array", "items": {"type": "string"}, "description": "CAD keys for matching"},
                "part/attrition": {
                    "type": ["object", "null"],
                    "description": "Attrition settings for manufacturing",
                    "properties": {
                        "percentage": {"type": "number", "description": "Attrition percentage"},
                        "quantity": {"type": "integer", "description": "Fixed attrition quantity"}
                    }
                },
                "part/low-stock": {
                    "type": ["object", "null"],
                    "description": "Low stock threshold settings",
                    "properties": {
                        "report": {"type": "integer", "description": "Report when stock falls below this level"}
                    }
                },
                "part/custom-fields": {"type": ["object", "null"], "description": "Custom field data"},
                "part/stock": {
                    "type": "array",
                    "description": "Stock history entries",
                    "items": {
                        "type": "object",
                        "required": ["stock/quantity", "stock/storage-id", "stock/timestamp"],
                        "properties": {
                            "stock/quantity": {"type": "integer", "description": "Stock quantity"},
                            "stock/storage-id": {"type": "string", "description": "Storage location identifier"},
                            "stock/timestamp": {"type": "integer", "description": "Entry timestamp (UNIX UTC milliseconds)"},
                            "stock/lot-id": {"type": ["string", "null"], "description": "Lot identifier"},
                            "stock/price": {"type": ["number", "null"], "description": "Unit price"},
                            "stock/currency": {"type": ["string", "null"], "description": "Currency code (e.g., 'usd', 'eur')"},
                            "stock/comments": {"type": ["string", "null"], "description": "Entry notes"},
                            "stock/user": {"type": ["string", "null"], "description": "User who created the entry"},
                            "stock/status": {"type": ["string", "null"], "description": "Stock status (ordered, reserved, etc.) or null for on-hand"},
                            "stock/order-id": {"type": ["string", "null"], "description": "Parent order identifier"},
                            "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU"}
                        }
                    }
                }
            }
        }
    """
    if not part_id:
        return PartResponse(
            success=False,
            error="part_id is required",
        )

    try:
        data = api_client.get_part(part_id)
        if data is None:
            return PartResponse(
                success=False,
                error=f"Part not found: {part_id}",
            )
        return PartResponse(
            success=True,
            data=data,
        )
    except requests.RequestException as e:
        return PartResponse(
            success=False,
            error=f"API request failed: {e}",
        )

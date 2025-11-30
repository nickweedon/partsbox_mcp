"""
Lots API module.

Provides MCP tools for lot management operations:
- lot/get - Retrieve single lot data by ID
- lot/all - Fetch all lots in database
- lot/update - Modify lot information
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class LotResponse:
    """Response for a single lot."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedLotsResponse:
    """Response for paginated lots listing."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[Any]
    error: str | None = None
    query_applied: str | None = None


@dataclass
class LotUpdateResponse:
    """Response for lot update operations."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def list_lots(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedLotsResponse:
    """
    List all lots with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection. Examples:
            - "[?contains(\"lot/name\", 'batch')]" - filter by name
            - "[?\"lot/expiration-date\" != null]" - lots with expiration
            - "sort_by(@, &\"lot/name\")" - sort by name

    Returns:
        PaginatedLotsResponse with lots data and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "lot/id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "lot/name": {"type": ["string", "null"], "description": "Lot name or number"},
                "lot/description": {"type": ["string", "null"], "description": "Short description"},
                "lot/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "lot/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC)"},
                "lot/expiration-date": {"type": ["integer", "null"], "description": "Expiration timestamp (UNIX UTC)"},
                "lot/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "lot/order-id": {"type": ["string", "null"], "description": "Linked order identifier"},
                "lot/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    if limit < 1 or limit > 1000:
        return PaginatedLotsResponse(
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
        return PaginatedLotsResponse(
            success=False,
            error="offset must be non-negative",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    try:
        if cache_key:
            entry = cache.get(cache_key)
            if entry:
                data = entry.data
                key = cache_key
            else:
                result = api_client._request("lot/all")
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("lot/all")
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedLotsResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedLotsResponse(
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

    if not isinstance(result, list):
        return PaginatedLotsResponse(
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
    page = result[offset : offset + limit]

    return PaginatedLotsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_lot(lot_id: str) -> LotResponse:
    """
    Get detailed information for a specific lot.

    Args:
        lot_id: The unique identifier of the lot

    Returns:
        LotResponse with lot data or error
    """
    if not lot_id:
        return LotResponse(success=False, error="lot_id is required")

    try:
        result = api_client._request("lot/get", {"lot/id": lot_id})
        data = result.get("data")
        if data is None:
            return LotResponse(success=False, error=f"Lot not found: {lot_id}")
        return LotResponse(success=True, data=data)
    except requests.RequestException as e:
        return LotResponse(success=False, error=f"API request failed: {e}")


def update_lot(
    lot_id: str,
    name: str | None = None,
    description: str | None = None,
    comments: str | None = None,
    expiration_date: int | None = None,
    tags: list[str] | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> LotUpdateResponse:
    """
    Update lot information.

    Args:
        lot_id: The unique identifier of the lot
        name: Optional new name for the lot
        description: Optional new description
        comments: Optional new comments
        expiration_date: Optional expiration timestamp (Unix ms)
        tags: Optional list of tags
        custom_fields: Optional custom field values

    Returns:
        LotUpdateResponse with the updated lot data
    """
    if not lot_id:
        return LotUpdateResponse(success=False, error="lot_id is required")

    payload: dict[str, Any] = {"lot/id": lot_id}

    if name is not None:
        payload["lot/name"] = name
    if description is not None:
        payload["lot/description"] = description
    if comments is not None:
        payload["lot/comments"] = comments
    if expiration_date is not None:
        payload["lot/expiration-date"] = expiration_date
    if tags is not None:
        payload["lot/tags"] = tags
    if custom_fields is not None:
        payload["lot/custom"] = custom_fields

    try:
        result = api_client._request("lot/update", payload)
        return LotUpdateResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return LotUpdateResponse(success=False, error=f"API request failed: {e}")

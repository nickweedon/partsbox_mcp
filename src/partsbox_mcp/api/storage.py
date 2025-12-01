"""
Storage API module.

Provides MCP tools for storage location management:
- storage/all - List all storage locations
- storage/get - Retrieve location details
- storage/update - Modify location metadata
- storage/rename - Change location name
- storage/archive - Hide from normal usage
- storage/restore - Un-archive location
- storage/parts - List aggregated stock by part
- storage/lots - List individual lots in location
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class StorageResponse:
    """Response for a single storage location."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedStorageResponse:
    """Response for paginated storage listing."""

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
class StorageOperationResponse:
    """Response for storage modification operations."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedStoragePartsResponse:
    """Response for paginated parts in storage."""

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
class PaginatedStorageLotsResponse:
    """Response for paginated lots in storage."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[Any]
    error: str | None = None
    query_applied: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def list_storage_locations(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    include_archived: bool = False,
) -> PaginatedStorageResponse:
    """
    List all storage locations with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "storage/name").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "storage/name", "storage/id", "storage/archived"
            - WRONG: `storage/name` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `storage/name` evaluates to the literal string "storage/name", not the field value.

            Standard JMESPath examples:
            - "[?\"storage/archived\" == `false`]" - active only
            - "sort_by(@, &\"storage/name\")" - sort by name

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"storage/name\", ''), 'Drawer')]" - safe name search
            - "[?contains(nvl(\"storage/description\", ''), 'SMD')]" - safe description search

        include_archived: Include archived locations (default False)

    Returns:
        PaginatedStorageResponse with storage locations and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "storage/id": {"type": "string", "description": "Storage location identifier (26-char compact UUID)"},
                "storage/name": {"type": "string", "description": "Storage location name"},
                "storage/description": {"type": ["string", "null"], "description": "Storage location description"},
                "storage/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "storage/archived": {"type": "boolean", "description": "Whether location is archived"},
                "storage/full?": {"type": "boolean", "description": "Whether location accepts new stock"},
                "storage/single-part?": {"type": "boolean", "description": "Single-part-only location"},
                "storage/existing-parts-only?": {"type": "boolean", "description": "Restrict to existing parts only"},
                "storage/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    if limit < 1 or limit > 1000:
        return PaginatedStorageResponse(
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
        return PaginatedStorageResponse(
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
                result = api_client._request("storage/all")
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("storage/all")
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedStorageResponse(
            success=False,
            error=f"API request failed: {e}",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    # Filter out archived if not requested
    if not include_archived:
        data = [loc for loc in data if not loc.get("storage/archived", False)]

    if query:
        result, error = apply_query(data, query)
        if error:
            return PaginatedStorageResponse(
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
        return PaginatedStorageResponse(
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

    return PaginatedStorageResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_storage_location(storage_id: str) -> StorageResponse:
    """
    Get detailed information for a specific storage location.

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageResponse with storage data or error
    """
    if not storage_id:
        return StorageResponse(success=False, error="storage_id is required")

    try:
        result = api_client._request("storage/get", {"storage/id": storage_id})
        data = result.get("data")
        if data is None:
            return StorageResponse(
                success=False, error=f"Storage location not found: {storage_id}"
            )
        return StorageResponse(success=True, data=data)
    except requests.RequestException as e:
        return StorageResponse(success=False, error=f"API request failed: {e}")


def update_storage_location(
    storage_id: str,
    comments: str | None = None,
    tags: list[str] | None = None,
) -> StorageOperationResponse:
    """
    Update storage location metadata.

    Args:
        storage_id: The unique identifier of the storage location
        comments: Optional new comments
        tags: Optional list of tags

    Returns:
        StorageOperationResponse with the updated storage data
    """
    if not storage_id:
        return StorageOperationResponse(success=False, error="storage_id is required")

    payload: dict[str, Any] = {"storage/id": storage_id}

    if comments is not None:
        payload["storage/comments"] = comments
    if tags is not None:
        payload["storage/tags"] = tags

    try:
        result = api_client._request("storage/update", payload)
        return StorageOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StorageOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def rename_storage_location(
    storage_id: str,
    new_name: str,
) -> StorageOperationResponse:
    """
    Rename a storage location.

    Args:
        storage_id: The unique identifier of the storage location
        new_name: The new name for the storage location

    Returns:
        StorageOperationResponse with the updated storage data
    """
    if not storage_id:
        return StorageOperationResponse(success=False, error="storage_id is required")
    if not new_name:
        return StorageOperationResponse(success=False, error="new_name is required")

    payload: dict[str, Any] = {
        "storage/id": storage_id,
        "storage/name": new_name,
    }

    try:
        result = api_client._request("storage/rename", payload)
        return StorageOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StorageOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def archive_storage_location(storage_id: str) -> StorageOperationResponse:
    """
    Archive a storage location (hide from normal usage).

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageOperationResponse with the result
    """
    if not storage_id:
        return StorageOperationResponse(success=False, error="storage_id is required")

    try:
        result = api_client._request("storage/archive", {"storage/id": storage_id})
        return StorageOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StorageOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def restore_storage_location(storage_id: str) -> StorageOperationResponse:
    """
    Restore an archived storage location.

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageOperationResponse with the result
    """
    if not storage_id:
        return StorageOperationResponse(success=False, error="storage_id is required")

    try:
        result = api_client._request("storage/restore", {"storage/id": storage_id})
        return StorageOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StorageOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def list_storage_parts(
    storage_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedStoragePartsResponse:
    """
    List aggregated stock by part in a storage location.

    Args:
        storage_id: The storage location ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "source/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "source/quantity", "source/part-id", "source/status"
            - WRONG: `source/quantity` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `source/quantity` evaluates to the literal string "source/quantity", not the field value.

            Standard JMESPath examples:
            - "[?\"source/quantity\" > `100`]" - parts with quantity > 100
            - "sort_by(@, &\"source/quantity\")" - sort by quantity

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?nvl(\"source/status\", '') == 'reserved']" - safe status check

    Returns:
        PaginatedStoragePartsResponse with parts data and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact form)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier"},
                "source/lot-id": {"type": "string", "description": "Lot identifier"},
                "source/quantity": {"type": "integer", "description": "Stock quantity"},
                "source/status": {"type": ["string", "null"], "description": "Stock status (ordered, reserved, allocated, in-production, in-transit, planned, rejected, being-ordered) or null for on-hand"},
                "source/first-timestamp": {"type": "integer", "description": "UNIX timestamp (UTC) of oldest stock entry"},
                "source/last-timestamp": {"type": "integer", "description": "UNIX timestamp (UTC) of most recent stock entry"}
            }
        }
    """
    if not storage_id:
        return PaginatedStoragePartsResponse(
            success=False,
            error="storage_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedStoragePartsResponse(
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
        return PaginatedStoragePartsResponse(
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
                result = api_client._request(
                    "storage/parts", {"storage/id": storage_id}
                )
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("storage/parts", {"storage/id": storage_id})
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedStoragePartsResponse(
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
            return PaginatedStoragePartsResponse(
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
        return PaginatedStoragePartsResponse(
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

    return PaginatedStoragePartsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def list_storage_lots(
    storage_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedStorageLotsResponse:
    """
    List individual lots in a storage location (not aggregated by part).

    Args:
        storage_id: The storage location ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "source/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "source/quantity", "source/lot-id", "source/status"
            - WRONG: `source/quantity` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `source/quantity` evaluates to the literal string "source/quantity", not the field value.

            Standard JMESPath examples:
            - "[?\"source/quantity\" > `0`]" - lots with positive quantity
            - "sort_by(@, &\"source/last-timestamp\")" - sort by last update

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?nvl(\"source/status\", '') == 'allocated']" - safe status check

    Returns:
        PaginatedStorageLotsResponse with lots data and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact form)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier"},
                "source/lot-id": {"type": "string", "description": "Lot identifier"},
                "source/quantity": {"type": "integer", "description": "Stock quantity"},
                "source/status": {"type": ["string", "null"], "description": "Stock status (ordered, reserved, allocated, in-production, in-transit, planned, rejected, being-ordered) or null for on-hand"},
                "source/first-timestamp": {"type": "integer", "description": "UNIX timestamp (UTC) of oldest stock entry"},
                "source/last-timestamp": {"type": "integer", "description": "UNIX timestamp (UTC) of most recent stock entry"}
            }
        }
    """
    if not storage_id:
        return PaginatedStorageLotsResponse(
            success=False,
            error="storage_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedStorageLotsResponse(
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
        return PaginatedStorageLotsResponse(
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
                result = api_client._request(
                    "storage/lots", {"storage/id": storage_id}
                )
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("storage/lots", {"storage/id": storage_id})
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedStorageLotsResponse(
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
            return PaginatedStorageLotsResponse(
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
        return PaginatedStorageLotsResponse(
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

    return PaginatedStorageLotsResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )

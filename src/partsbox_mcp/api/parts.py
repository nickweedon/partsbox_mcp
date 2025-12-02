"""
Parts API module.

Provides MCP tools for part operations:
- part/all - List all parts
- part/get - Retrieve part details
- part/create - Create new part
- part/update - Modify part data
- part/delete - Remove part
- part/add-meta-part-ids - Add equivalent substitutes to meta-part
- part/remove-meta-part-ids - Remove members from meta-part
- part/add-substitute-ids - Add substitutes to part
- part/remove-substitute-ids - Remove substitutes from part
- part/storage - List stock sources aggregating lots by location
- part/lots - List stock sources without aggregating lots
- part/stock - Get total stock count for a part
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache
from partsbox_mcp.types import PartData, SourceData


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


@dataclass
class PartOperationResponse:
    """Response for part modification operations."""

    success: bool
    data: PartData | None = None
    error: str | None = None


@dataclass
class PartStockResponse:
    """Response for part/stock total count."""

    success: bool
    total: int = 0
    error: str | None = None


@dataclass
class PaginatedSourcesResponse:
    """Response for paginated sources listing (part/storage, part/lots)."""

    success: bool
    cache_key: str
    total: int
    offset: int
    limit: int
    has_more: bool
    data: list[SourceData]
    error: str | None = None
    query_applied: str | None = None


# =============================================================================
# Tool Functions
# =============================================================================


def list_parts(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedPartsResponse:
    """List all parts with pagination and optional JMESPath query."""
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
    """Get a specific part by ID."""
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


def create_part(
    name: str,
    part_type: str = "local",
    description: str | None = None,
    notes: str | None = None,
    footprint: str | None = None,
    manufacturer: str | None = None,
    mpn: str | None = None,
    tags: list[str] | None = None,
    cad_keys: list[str] | None = None,
    low_stock_threshold: int | None = None,
    attrition_percentage: float | None = None,
    attrition_quantity: int | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> PartOperationResponse:
    """Create a new part."""
    if not name:
        return PartOperationResponse(success=False, error="name is required")

    valid_types = {"local", "linked", "sub-assembly", "meta"}
    if part_type not in valid_types:
        return PartOperationResponse(
            success=False,
            error=f"part_type must be one of: {', '.join(valid_types)}",
        )

    payload: dict[str, Any] = {
        "part/name": name,
        "part/type": part_type,
    }

    if description is not None:
        payload["part/description"] = description
    if notes is not None:
        payload["part/notes"] = notes
    if footprint is not None:
        payload["part/footprint"] = footprint
    if manufacturer is not None:
        payload["part/manufacturer"] = manufacturer
    if mpn is not None:
        payload["part/mpn"] = mpn
    if tags is not None:
        payload["part/tags"] = tags
    if cad_keys is not None:
        payload["part/cad-keys"] = cad_keys
    if low_stock_threshold is not None:
        payload["part/low-stock"] = {"report": low_stock_threshold}
    if attrition_percentage is not None or attrition_quantity is not None:
        attrition: dict[str, Any] = {}
        if attrition_percentage is not None:
            attrition["percentage"] = attrition_percentage
        if attrition_quantity is not None:
            attrition["quantity"] = attrition_quantity
        payload["part/attrition"] = attrition
    if custom_fields is not None:
        payload["part/custom"] = custom_fields

    try:
        result = api_client._request("part/create", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def update_part(
    part_id: str,
    name: str | None = None,
    description: str | None = None,
    notes: str | None = None,
    footprint: str | None = None,
    manufacturer: str | None = None,
    mpn: str | None = None,
    tags: list[str] | None = None,
    cad_keys: list[str] | None = None,
    low_stock_threshold: int | None = None,
    attrition_percentage: float | None = None,
    attrition_quantity: int | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> PartOperationResponse:
    """Update an existing part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")

    payload: dict[str, Any] = {"part/id": part_id}

    if name is not None:
        payload["part/name"] = name
    if description is not None:
        payload["part/description"] = description
    if notes is not None:
        payload["part/notes"] = notes
    if footprint is not None:
        payload["part/footprint"] = footprint
    if manufacturer is not None:
        payload["part/manufacturer"] = manufacturer
    if mpn is not None:
        payload["part/mpn"] = mpn
    if tags is not None:
        payload["part/tags"] = tags
    if cad_keys is not None:
        payload["part/cad-keys"] = cad_keys
    if low_stock_threshold is not None:
        payload["part/low-stock"] = {"report": low_stock_threshold}
    if attrition_percentage is not None or attrition_quantity is not None:
        attrition: dict[str, Any] = {}
        if attrition_percentage is not None:
            attrition["percentage"] = attrition_percentage
        if attrition_quantity is not None:
            attrition["quantity"] = attrition_quantity
        payload["part/attrition"] = attrition
    if custom_fields is not None:
        payload["part/custom"] = custom_fields

    try:
        result = api_client._request("part/update", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def delete_part(part_id: str) -> PartOperationResponse:
    """Delete a part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")

    try:
        result = api_client._request("part/delete", {"part/id": part_id})
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def add_meta_part_ids(
    part_id: str,
    member_ids: list[str],
) -> PartOperationResponse:
    """Add members to a meta-part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")
    if not member_ids:
        return PartOperationResponse(success=False, error="member_ids is required")

    payload: dict[str, Any] = {
        "part/id": part_id,
        "part/meta-part-ids": member_ids,
    }

    try:
        result = api_client._request("part/add-meta-part-ids", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def remove_meta_part_ids(
    part_id: str,
    member_ids: list[str],
) -> PartOperationResponse:
    """Remove members from a meta-part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")
    if not member_ids:
        return PartOperationResponse(success=False, error="member_ids is required")

    payload: dict[str, Any] = {
        "part/id": part_id,
        "part/meta-part-ids": member_ids,
    }

    try:
        result = api_client._request("part/remove-meta-part-ids", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def add_substitute_ids(
    part_id: str,
    substitute_ids: list[str],
) -> PartOperationResponse:
    """Add substitutes to a part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")
    if not substitute_ids:
        return PartOperationResponse(success=False, error="substitute_ids is required")

    payload: dict[str, Any] = {
        "part/id": part_id,
        "part/substitute-ids": substitute_ids,
    }

    try:
        result = api_client._request("part/add-substitute-ids", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def remove_substitute_ids(
    part_id: str,
    substitute_ids: list[str],
) -> PartOperationResponse:
    """Remove substitutes from a part."""
    if not part_id:
        return PartOperationResponse(success=False, error="part_id is required")
    if not substitute_ids:
        return PartOperationResponse(success=False, error="substitute_ids is required")

    payload: dict[str, Any] = {
        "part/id": part_id,
        "part/substitute-ids": substitute_ids,
    }

    try:
        result = api_client._request("part/remove-substitute-ids", payload)
        return PartOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return PartOperationResponse(success=False, error=f"API request failed: {e}")


def get_part_storage(
    part_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedSourcesResponse:
    """List stock sources for a part, aggregating lots by storage location."""
    if not part_id:
        return PaginatedSourcesResponse(
            success=False,
            error="part_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedSourcesResponse(
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
        return PaginatedSourcesResponse(
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
                result = api_client._request("part/storage", {"part/id": part_id})
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("part/storage", {"part/id": part_id})
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedSourcesResponse(
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
            return PaginatedSourcesResponse(
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
        return PaginatedSourcesResponse(
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

    return PaginatedSourcesResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_part_lots(
    part_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedSourcesResponse:
    """List stock sources for a part without aggregating lots."""
    if not part_id:
        return PaginatedSourcesResponse(
            success=False,
            error="part_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedSourcesResponse(
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
        return PaginatedSourcesResponse(
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
                result = api_client._request("part/lots", {"part/id": part_id})
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("part/lots", {"part/id": part_id})
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedSourcesResponse(
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
            return PaginatedSourcesResponse(
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
        return PaginatedSourcesResponse(
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

    return PaginatedSourcesResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_part_stock(part_id: str) -> PartStockResponse:
    """Get the total stock count for a part."""
    if not part_id:
        return PartStockResponse(success=False, error="part_id is required")

    try:
        result = api_client._request("part/stock", {"part/id": part_id})
        total = result.get("data", 0)
        # The API may return the count directly or in a wrapper
        if isinstance(total, dict):
            total = total.get("stock/total", 0)
        return PartStockResponse(success=True, total=total)
    except requests.RequestException as e:
        return PartStockResponse(success=False, error=f"API request failed: {e}")

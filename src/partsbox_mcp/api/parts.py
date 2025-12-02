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
                "part/img-id": {"type": ["string", "null"], "description": "Image identifier for the part's associated image"},
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
                            "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU"},
                            "stock/linked?": {"type": ["boolean", "null"], "description": "Whether this entry is linked to another (e.g., paired move entries)"}
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
                "part/img-id": {"type": ["string", "null"], "description": "Image identifier for the part's associated image"},
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
                            "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU"},
                            "stock/linked?": {"type": ["boolean", "null"], "description": "Whether this entry is linked to another (e.g., paired move entries)"}
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
    """
    Create a new part.

    Args:
        name: The part name (required)
        part_type: Type of part - "local", "linked", "sub-assembly", or "meta" (default "local")
        description: Optional part description
        notes: Optional user notes (Markdown supported)
        footprint: Optional physical package footprint
        manufacturer: Optional manufacturer name
        mpn: Optional manufacturer part number
        tags: Optional list of tags
        cad_keys: Optional CAD keys for matching
        low_stock_threshold: Optional low stock warning threshold
        attrition_percentage: Optional attrition percentage for manufacturing
        attrition_quantity: Optional fixed attrition quantity for manufacturing
        custom_fields: Optional custom field values

    Returns:
        PartOperationResponse with the created part data.

        Data schema:
        {
            "type": "object",
            "required": ["part/id", "part/name", "part/type", "part/created", "part/owner"],
            "properties": {
                "part/id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "part/name": {"type": "string", "description": "Part name or internal identifier"},
                "part/type": {"type": "string", "enum": ["local", "linked", "sub-assembly", "meta"]},
                "part/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "part/owner": {"type": "string", "description": "Owner identifier"}
            }
        }
    """
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
    """
    Update an existing part.

    Args:
        part_id: The unique identifier of the part (required)
        name: Optional new name
        description: Optional new description
        notes: Optional new notes (Markdown supported)
        footprint: Optional new footprint
        manufacturer: Optional new manufacturer name
        mpn: Optional new manufacturer part number
        tags: Optional new list of tags (replaces existing)
        cad_keys: Optional new CAD keys (replaces existing)
        low_stock_threshold: Optional new low stock warning threshold
        attrition_percentage: Optional new attrition percentage
        attrition_quantity: Optional new fixed attrition quantity
        custom_fields: Optional custom field values to update

    Returns:
        PartOperationResponse with the updated part data.

        Data schema:
        {
            "type": "object",
            "required": ["part/id", "part/name", "part/type", "part/created", "part/owner"],
            "properties": {
                "part/id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "part/name": {"type": "string", "description": "Part name or internal identifier"},
                "part/type": {"type": "string", "enum": ["local", "linked", "sub-assembly", "meta"]},
                "part/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "part/owner": {"type": "string", "description": "Owner identifier"}
            }
        }
    """
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
    """
    Delete a part.

    Args:
        part_id: The unique identifier of the part to delete

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
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
    """
    Add equivalent substitutes (members) to a meta-part.

    Meta-parts are virtual parts that group together equivalent alternatives.
    This function adds parts as members of the meta-part.

    Args:
        part_id: The meta-part identifier
        member_ids: List of part IDs to add as members of the meta-part

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
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
    """
    Remove members from a meta-part.

    Args:
        part_id: The meta-part identifier
        member_ids: List of part IDs to remove from the meta-part

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
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
    """
    Add substitutes to a part.

    Substitutes are alternative parts that can be used in place of this part.
    Unlike meta-parts, substitutes are directional - Part A can have Part B
    as a substitute without Part B having Part A as a substitute.

    Args:
        part_id: The part identifier
        substitute_ids: List of part IDs to add as substitutes

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
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
    """
    Remove substitutes from a part.

    Args:
        part_id: The part identifier
        substitute_ids: List of part IDs to remove as substitutes

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
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
    """
    List stock sources for a part, aggregating lots by storage location.

    This returns aggregated stock data showing where a part is stored
    and how much is in each location. Lots at the same location are
    combined into a single entry.

    Args:
        part_id: The part identifier
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "source/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "source/quantity", "source/storage-id", "source/status"
            - WRONG: `source/quantity` (backticks create literal strings, not field references)

            Standard JMESPath examples:
            - "[?\"source/quantity\" > `100`]" - locations with quantity > 100
            - "sort_by(@, &\"source/quantity\")" - sort by quantity

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

    Returns:
        PaginatedSourcesResponse with aggregated stock sources.

        Data items schema:
        {
            "type": "object",
            "required": ["source/part-id", "source/storage-id", "source/quantity"],
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier"},
                "source/lot-id": {"type": ["string", "null"], "description": "Lot identifier (null when aggregated)"},
                "source/quantity": {"type": "integer", "description": "Aggregated stock quantity at this location"},
                "source/status": {"type": ["string", "null"], "enum": ["ordered", "reserved", "allocated", "in-production", "in-transit", "planned", "rejected", "being-ordered", null]},
                "source/first-timestamp": {"type": ["integer", "null"], "description": "Timestamp of oldest stock entry"},
                "source/last-timestamp": {"type": ["integer", "null"], "description": "Timestamp of most recent stock entry"}
            }
        }
    """
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
    """
    List stock sources for a part without aggregating lots.

    Unlike get_part_storage(), this returns individual lot entries
    without combining them. Each lot at each location is a separate entry.

    Args:
        part_id: The part identifier
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "source/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "source/quantity", "source/lot-id", "source/status"
            - WRONG: `source/quantity` (backticks create literal strings, not field references)

            Standard JMESPath examples:
            - "[?\"source/quantity\" > `0`]" - lots with positive quantity
            - "sort_by(@, &\"source/last-timestamp\")" - sort by last update

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

    Returns:
        PaginatedSourcesResponse with individual lot stock sources.

        Data items schema:
        {
            "type": "object",
            "required": ["source/part-id", "source/storage-id", "source/lot-id", "source/quantity"],
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier"},
                "source/lot-id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "source/quantity": {"type": "integer", "description": "Stock quantity for this lot"},
                "source/status": {"type": ["string", "null"], "enum": ["ordered", "reserved", "allocated", "in-production", "in-transit", "planned", "rejected", "being-ordered", null]},
                "source/first-timestamp": {"type": ["integer", "null"], "description": "Timestamp of oldest stock entry"},
                "source/last-timestamp": {"type": ["integer", "null"], "description": "Timestamp of most recent stock entry"}
            }
        }
    """
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
    """
    Get the total stock count for a part.

    This returns the calculated total quantity of a part across all
    storage locations and lots.

    Args:
        part_id: The part identifier

    Returns:
        PartStockResponse with the total stock count.

        Response schema:
        {
            "success": true,
            "total": 1500,
            "error": null
        }
    """
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

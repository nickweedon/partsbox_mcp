"""
PartsBox MCP Server - Main Entry Point

This module sets up the FastMCP server and registers all tools
from the API modules.
"""

from typing import Any

from fastmcp import FastMCP

from partsbox_mcp.api import files, lots, orders, parts, projects, stock, storage
from partsbox_mcp.api.files import FileDownloadResponse
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
    return parts.get_part(part_id)


@mcp.tool()
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
) -> parts.PartOperationResponse:
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
    return parts.create_part(
        name=name,
        part_type=part_type,
        description=description,
        notes=notes,
        footprint=footprint,
        manufacturer=manufacturer,
        mpn=mpn,
        tags=tags,
        cad_keys=cad_keys,
        low_stock_threshold=low_stock_threshold,
        attrition_percentage=attrition_percentage,
        attrition_quantity=attrition_quantity,
        custom_fields=custom_fields,
    )


@mcp.tool()
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
) -> parts.PartOperationResponse:
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
    return parts.update_part(
        part_id=part_id,
        name=name,
        description=description,
        notes=notes,
        footprint=footprint,
        manufacturer=manufacturer,
        mpn=mpn,
        tags=tags,
        cad_keys=cad_keys,
        low_stock_threshold=low_stock_threshold,
        attrition_percentage=attrition_percentage,
        attrition_quantity=attrition_quantity,
        custom_fields=custom_fields,
    )


@mcp.tool()
def delete_part(part_id: str) -> parts.PartOperationResponse:
    """
    Delete a part.

    Args:
        part_id: The unique identifier of the part to delete

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return parts.delete_part(part_id)


@mcp.tool()
def add_meta_part_ids(
    part_id: str,
    member_ids: list[str],
) -> parts.PartOperationResponse:
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
    return parts.add_meta_part_ids(part_id=part_id, member_ids=member_ids)


@mcp.tool()
def remove_meta_part_ids(
    part_id: str,
    member_ids: list[str],
) -> parts.PartOperationResponse:
    """
    Remove members from a meta-part.

    Args:
        part_id: The meta-part identifier
        member_ids: List of part IDs to remove from the meta-part

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return parts.remove_meta_part_ids(part_id=part_id, member_ids=member_ids)


@mcp.tool()
def add_substitute_ids(
    part_id: str,
    substitute_ids: list[str],
) -> parts.PartOperationResponse:
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
    return parts.add_substitute_ids(part_id=part_id, substitute_ids=substitute_ids)


@mcp.tool()
def remove_substitute_ids(
    part_id: str,
    substitute_ids: list[str],
) -> parts.PartOperationResponse:
    """
    Remove substitutes from a part.

    Args:
        part_id: The part identifier
        substitute_ids: List of part IDs to remove as substitutes

    Returns:
        PartOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return parts.remove_substitute_ids(part_id=part_id, substitute_ids=substitute_ids)


@mcp.tool()
def get_part_storage(
    part_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> parts.PaginatedSourcesResponse:
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
    return parts.get_part_storage(
        part_id=part_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_part_lots(
    part_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> parts.PaginatedSourcesResponse:
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
    return parts.get_part_lots(
        part_id=part_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_part_stock(part_id: str) -> parts.PartStockResponse:
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
    return parts.get_part_stock(part_id)


# =============================================================================
# Stock Tools
# =============================================================================


@mcp.tool()
def add_stock(
    part_id: str,
    storage_id: str,
    quantity: int,
    comments: str | None = None,
    price: float | None = None,
    currency: str | None = None,
    lot_name: str | None = None,
    lot_description: str | None = None,
    order_id: str | None = None,
) -> stock.StockOperationResponse:
    """
    Add inventory for a part.

    Args:
        part_id: The part ID to add stock for
        storage_id: The storage location ID
        quantity: Number of parts to add (must be positive)
        comments: Optional comments for this stock entry
        price: Optional unit price
        currency: Optional currency code (e.g., 'usd', 'eur')
        lot_name: Optional lot name
        lot_description: Optional lot description
        order_id: Optional order ID this stock came from

    Returns:
        StockOperationResponse with the operation result.

        Data schema (when successful, data may contain lot information):
        {
            "type": ["object", "null"],
            "properties": {
                "lot/id": {"type": "string", "description": "Created lot identifier (26-char compact UUID)"}
            }
        }

        Note: The PartsBox API returns status information. Stock is not returned directly;
        use list_parts() to see updated stock levels.
    """
    return stock.add_stock(
        part_id=part_id,
        storage_id=storage_id,
        quantity=quantity,
        comments=comments,
        price=price,
        currency=currency,
        lot_name=lot_name,
        lot_description=lot_description,
        order_id=order_id,
    )


@mcp.tool()
def remove_stock(
    part_id: str,
    storage_id: str,
    quantity: int,
    comments: str | None = None,
    lot_id: str | None = None,
) -> stock.StockOperationResponse:
    """
    Remove parts from inventory.

    Args:
        part_id: The part ID to remove stock from
        storage_id: The storage location ID
        quantity: Number of parts to remove (must be positive)
        comments: Optional comments for this removal
        lot_id: Optional specific lot ID to remove from

    Returns:
        StockOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Stock is not returned directly;
        use list_parts() to see updated stock levels.
    """
    return stock.remove_stock(
        part_id=part_id,
        storage_id=storage_id,
        quantity=quantity,
        comments=comments,
        lot_id=lot_id,
    )


@mcp.tool()
def move_stock(
    part_id: str,
    source_storage_id: str,
    target_storage_id: str,
    quantity: int,
    comments: str | None = None,
    lot_id: str | None = None,
) -> stock.StockOperationResponse:
    """
    Transfer stock to a different location.

    Args:
        part_id: The part ID to move
        source_storage_id: The source storage location ID
        target_storage_id: The target storage location ID
        quantity: Number of parts to move (must be positive)
        comments: Optional comments for this move
        lot_id: Optional specific lot ID to move from

    Returns:
        StockOperationResponse with the operation result.

        Data schema (when successful, may contain lot information):
        {
            "type": ["object", "null"],
            "properties": {
                "lot/id": {"type": "string", "description": "Created lot identifier at target location (26-char compact UUID)"}
            }
        }

        Note: The PartsBox API returns status information. Stock is not returned directly;
        use list_parts() to see updated stock levels.
    """
    return stock.move_stock(
        part_id=part_id,
        source_storage_id=source_storage_id,
        target_storage_id=target_storage_id,
        quantity=quantity,
        comments=comments,
        lot_id=lot_id,
    )


@mcp.tool()
def update_stock(
    part_id: str,
    timestamp: int,
    quantity: int | None = None,
    comments: str | None = None,
    price: float | None = None,
    currency: str | None = None,
) -> stock.StockOperationResponse:
    """
    Modify an existing stock entry.

    Args:
        part_id: The part ID
        timestamp: The timestamp of the stock entry to update
        quantity: Optional new quantity
        comments: Optional new comments
        price: Optional new unit price
        currency: Optional new currency code

    Returns:
        StockOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Stock is not returned directly;
        use list_parts() to see updated stock levels.
    """
    return stock.update_stock(
        part_id=part_id,
        timestamp=timestamp,
        quantity=quantity,
        comments=comments,
        price=price,
        currency=currency,
    )


# =============================================================================
# Lots Tools
# =============================================================================


@mcp.tool()
def list_lots(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> lots.PaginatedLotsResponse:
    """
    List all lots with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "lot/name").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "lot/name", "lot/id", "lot/part-id"
            - WRONG: `lot/name` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `lot/name` evaluates to the literal string "lot/name", not the field value.

            Standard JMESPath examples:
            - "[?\"lot/expiration-date\" != null]" - lots with expiration
            - "sort_by(@, &\"lot/name\")" - sort by name

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"lot/name\", ''), 'batch')]" - safe name search
            - "[?contains(nvl(\"lot/description\", ''), 'production')]" - safe description search

    Returns:
        PaginatedLotsResponse with lots data and pagination info.

        Data items schema:
        {
            "type": "object",
            "required": ["lot/id", "lot/created"],
            "properties": {
                "lot/id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "lot/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "lot/name": {"type": ["string", "null"], "description": "Lot name or number"},
                "lot/description": {"type": ["string", "null"], "description": "Short description"},
                "lot/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "lot/expiration-date": {"type": ["integer", "null"], "description": "Expiration timestamp (UNIX UTC milliseconds)"},
                "lot/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "lot/order-id": {"type": ["string", "null"], "description": "Linked order identifier (26-char compact UUID)"},
                "lot/custom-fields": {"type": ["object", "null"], "description": "Custom field data"},
                "lot/part-id": {"type": ["string", "null"], "description": "Part identifier (contextual, when returned with stock info)"},
                "lot/storage-id": {"type": ["string", "null"], "description": "Storage location identifier (contextual)"},
                "lot/quantity": {"type": ["integer", "null"], "description": "Current quantity (contextual)"}
            }
        }
    """
    return lots.list_lots(
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_lot(lot_id: str) -> lots.LotResponse:
    """
    Get detailed information for a specific lot.

    Args:
        lot_id: The unique identifier of the lot

    Returns:
        LotResponse with lot data or error.

        Data schema:
        {
            "type": "object",
            "required": ["lot/id", "lot/created"],
            "properties": {
                "lot/id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "lot/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "lot/name": {"type": ["string", "null"], "description": "Lot name or number"},
                "lot/description": {"type": ["string", "null"], "description": "Short description"},
                "lot/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "lot/expiration-date": {"type": ["integer", "null"], "description": "Expiration timestamp (UNIX UTC milliseconds)"},
                "lot/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "lot/order-id": {"type": ["string", "null"], "description": "Linked order identifier (26-char compact UUID)"},
                "lot/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return lots.get_lot(lot_id)


@mcp.tool()
def update_lot(
    lot_id: str,
    name: str | None = None,
    description: str | None = None,
    comments: str | None = None,
    expiration_date: int | None = None,
    tags: list[str] | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> lots.LotUpdateResponse:
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
        LotUpdateResponse with the updated lot data.

        Data schema:
        {
            "type": "object",
            "required": ["lot/id", "lot/created"],
            "properties": {
                "lot/id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "lot/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "lot/name": {"type": ["string", "null"], "description": "Lot name or number"},
                "lot/description": {"type": ["string", "null"], "description": "Short description"},
                "lot/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "lot/expiration-date": {"type": ["integer", "null"], "description": "Expiration timestamp (UNIX UTC milliseconds)"},
                "lot/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "lot/order-id": {"type": ["string", "null"], "description": "Linked order identifier (26-char compact UUID)"},
                "lot/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return lots.update_lot(
        lot_id=lot_id,
        name=name,
        description=description,
        comments=comments,
        expiration_date=expiration_date,
        tags=tags,
        custom_fields=custom_fields,
    )


# =============================================================================
# Storage Tools
# =============================================================================


@mcp.tool()
def list_storage_locations(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    include_archived: bool = False,
) -> storage.PaginatedStorageResponse:
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
            "required": ["storage/id", "storage/name"],
            "properties": {
                "storage/id": {"type": "string", "description": "Storage location identifier (26-char compact UUID)"},
                "storage/name": {"type": "string", "description": "Storage location name"},
                "storage/description": {"type": ["string", "null"], "description": "Storage location description"},
                "storage/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "storage/parent-id": {"type": ["string", "null"], "description": "Parent storage location identifier"},
                "storage/path": {"type": ["string", "null"], "description": "Full path of location"},
                "storage/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "storage/archived": {"type": "boolean", "description": "Whether location is archived (default: false)"},
                "storage/full?": {"type": "boolean", "description": "Whether location accepts new stock"},
                "storage/single-part?": {"type": "boolean", "description": "Single-part-only location"},
                "storage/existing-parts-only?": {"type": "boolean", "description": "Restrict to existing parts only"},
                "storage/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "storage/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return storage.list_storage_locations(
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
        include_archived=include_archived,
    )


@mcp.tool()
def get_storage_location(storage_id: str) -> storage.StorageResponse:
    """
    Get detailed information for a specific storage location.

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageResponse with storage data or error.

        Data schema:
        {
            "type": "object",
            "required": ["storage/id", "storage/name"],
            "properties": {
                "storage/id": {"type": "string", "description": "Storage location identifier (26-char compact UUID)"},
                "storage/name": {"type": "string", "description": "Storage location name"},
                "storage/description": {"type": ["string", "null"], "description": "Storage location description"},
                "storage/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "storage/parent-id": {"type": ["string", "null"], "description": "Parent storage location identifier"},
                "storage/path": {"type": ["string", "null"], "description": "Full path of location"},
                "storage/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "storage/archived": {"type": "boolean", "description": "Whether location is archived"},
                "storage/full?": {"type": "boolean", "description": "Whether location accepts new stock"},
                "storage/single-part?": {"type": "boolean", "description": "Single-part-only location"},
                "storage/existing-parts-only?": {"type": "boolean", "description": "Restrict to existing parts only"},
                "storage/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "storage/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return storage.get_storage_location(storage_id)


@mcp.tool()
def update_storage_location(
    storage_id: str,
    comments: str | None = None,
    tags: list[str] | None = None,
) -> storage.StorageOperationResponse:
    """
    Update storage location metadata.

    Args:
        storage_id: The unique identifier of the storage location
        comments: Optional new comments
        tags: Optional list of tags

    Returns:
        StorageOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Use get_storage_location()
        to retrieve the updated storage data.
    """
    return storage.update_storage_location(
        storage_id=storage_id,
        comments=comments,
        tags=tags,
    )


@mcp.tool()
def rename_storage_location(
    storage_id: str,
    new_name: str,
) -> storage.StorageOperationResponse:
    """
    Rename a storage location.

    Args:
        storage_id: The unique identifier of the storage location
        new_name: The new name for the storage location

    Returns:
        StorageOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Use get_storage_location()
        to retrieve the updated storage data.
    """
    return storage.rename_storage_location(
        storage_id=storage_id,
        new_name=new_name,
    )


@mcp.tool()
def archive_storage_location(storage_id: str) -> storage.StorageOperationResponse:
    """
    Archive a storage location (hide from normal usage).

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Use get_storage_location()
        to verify the archive status.
    """
    return storage.archive_storage_location(storage_id)


@mcp.tool()
def restore_storage_location(storage_id: str) -> storage.StorageOperationResponse:
    """
    Restore an archived storage location.

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Use get_storage_location()
        to verify the restore status.
    """
    return storage.restore_storage_location(storage_id)


@mcp.tool()
def change_storage_settings(
    storage_id: str,
    full: bool | None = None,
    single_part: bool | None = None,
    existing_parts_only: bool | None = None,
) -> storage.StorageOperationResponse:
    """
    Modify storage location settings.

    These settings control what can be stored in this location.

    Args:
        storage_id: The unique identifier of the storage location
        full: If True, the location won't accept new stock (marked as full)
        single_part: If True, the location can only contain a single part type
        existing_parts_only: If True, only parts already in the location can be added

    Returns:
        StorageOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Use get_storage_location()
        to verify the updated settings.
    """
    return storage.change_storage_settings(
        storage_id=storage_id,
        full=full,
        single_part=single_part,
        existing_parts_only=existing_parts_only,
    )


@mcp.tool()
def list_storage_parts(
    storage_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> storage.PaginatedStoragePartsResponse:
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
            "required": ["source/part-id", "source/storage-id", "source/lot-id", "source/quantity"],
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier (26-char compact UUID)"},
                "source/lot-id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "source/quantity": {"type": "integer", "description": "Aggregated stock quantity"},
                "source/status": {"type": ["string", "null"], "enum": ["ordered", "reserved", "allocated", "in-production", "in-transit", "planned", "rejected", "being-ordered", null], "description": "Stock status or null for on-hand stock"},
                "source/first-timestamp": {"type": ["integer", "null"], "description": "Timestamp (UNIX UTC milliseconds) of oldest stock entry"},
                "source/last-timestamp": {"type": ["integer", "null"], "description": "Timestamp (UNIX UTC milliseconds) of most recent stock entry"}
            }
        }
    """
    return storage.list_storage_parts(
        storage_id=storage_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def list_storage_lots(
    storage_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> storage.PaginatedStorageLotsResponse:
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
            "required": ["source/part-id", "source/storage-id", "source/lot-id", "source/quantity"],
            "properties": {
                "source/part-id": {"type": "string", "description": "Part identifier (26-char compact UUID)"},
                "source/storage-id": {"type": "string", "description": "Storage location identifier (26-char compact UUID)"},
                "source/lot-id": {"type": "string", "description": "Lot identifier (26-char compact UUID)"},
                "source/quantity": {"type": "integer", "description": "Stock quantity for this lot"},
                "source/status": {"type": ["string", "null"], "enum": ["ordered", "reserved", "allocated", "in-production", "in-transit", "planned", "rejected", "being-ordered", null], "description": "Stock status or null for on-hand stock"},
                "source/first-timestamp": {"type": ["integer", "null"], "description": "Timestamp (UNIX UTC milliseconds) of oldest stock entry"},
                "source/last-timestamp": {"type": ["integer", "null"], "description": "Timestamp (UNIX UTC milliseconds) of most recent stock entry"}
            }
        }
    """
    return storage.list_storage_lots(
        storage_id=storage_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


# =============================================================================
# Projects Tools
# =============================================================================


@mcp.tool()
def list_projects(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    include_archived: bool = False,
) -> projects.PaginatedProjectsResponse:
    """
    List all projects with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "project/name").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "project/name", "project/id", "project/archived"
            - WRONG: `project/name` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `project/name` evaluates to the literal string "project/name", not the field value.

            Standard JMESPath examples:
            - "[?\"project/archived\" == `false`]" - active projects only
            - "sort_by(@, &\"project/name\")" - sort by name

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"project/name\", ''), 'Arduino')]" - safe name search
            - "[?contains(nvl(\"project/description\", ''), 'prototype')]" - safe description search

        include_archived: Include archived projects (default False)

    Returns:
        PaginatedProjectsResponse with projects data and pagination info.

        Data items schema:
        {
            "type": "object",
            "required": ["project/id", "project/name"],
            "properties": {
                "project/id": {"type": "string", "description": "Project identifier (26-char compact UUID)"},
                "project/name": {"type": "string", "description": "Project name"},
                "project/description": {"type": ["string", "null"], "description": "Project description"},
                "project/notes": {"type": ["string", "null"], "description": "Longer-form notes (Markdown supported)"},
                "project/comments": {"type": ["string", "null"], "description": "Project comments"},
                "project/archived": {"type": "boolean", "description": "Whether project is archived (default: false)"},
                "project/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "project/updated": {"type": ["integer", "null"], "description": "Last update timestamp (UNIX UTC milliseconds)"},
                "project/entry-count": {"type": ["integer", "null"], "description": "Number of BOM entries"},
                "project/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return projects.list_projects(
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
        include_archived=include_archived,
    )


@mcp.tool()
def get_project(project_id: str) -> projects.ProjectResponse:
    """
    Get detailed information for a specific project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectResponse with project data or error.

        Data schema:
        {
            "type": "object",
            "required": ["project/id", "project/name"],
            "properties": {
                "project/id": {"type": "string", "description": "Project identifier (26-char compact UUID)"},
                "project/name": {"type": "string", "description": "Project name"},
                "project/description": {"type": ["string", "null"], "description": "Project description"},
                "project/notes": {"type": ["string", "null"], "description": "Longer-form notes (Markdown supported)"},
                "project/comments": {"type": ["string", "null"], "description": "Project comments"},
                "project/archived": {"type": "boolean", "description": "Whether project is archived (default: false)"},
                "project/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "project/updated": {"type": ["integer", "null"], "description": "Last update timestamp (UNIX UTC milliseconds)"},
                "project/entry-count": {"type": ["integer", "null"], "description": "Number of BOM entries"},
                "project/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return projects.get_project(project_id)


@mcp.tool()
def create_project(
    name: str,
    description: str | None = None,
    comments: str | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> projects.ProjectOperationResponse:
    """
    Create a new project.

    Args:
        name: The project name
        description: Optional project description
        comments: Optional project comments
        entries: Optional list of initial BOM entries

    Returns:
        ProjectOperationResponse with the created project data.

        Data schema:
        {
            "type": "object",
            "required": ["project/id", "project/name"],
            "properties": {
                "project/id": {"type": "string", "description": "Project identifier (26-char compact UUID)"},
                "project/name": {"type": "string", "description": "Project name"},
                "project/description": {"type": ["string", "null"], "description": "Project description"},
                "project/notes": {"type": ["string", "null"], "description": "Longer-form notes (Markdown supported)"},
                "project/comments": {"type": ["string", "null"], "description": "Project comments"},
                "project/archived": {"type": "boolean", "description": "Whether project is archived (default: false)"},
                "project/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "project/updated": {"type": ["integer", "null"], "description": "Last update timestamp (UNIX UTC milliseconds)"},
                "project/entry-count": {"type": ["integer", "null"], "description": "Number of BOM entries"},
                "project/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return projects.create_project(
        name=name,
        description=description,
        comments=comments,
        entries=entries,
    )


@mcp.tool()
def update_project(
    project_id: str,
    name: str | None = None,
    description: str | None = None,
    comments: str | None = None,
) -> projects.ProjectOperationResponse:
    """
    Update project metadata.

    Args:
        project_id: The unique identifier of the project
        name: Optional new name
        description: Optional new description
        comments: Optional new comments

    Returns:
        ProjectOperationResponse with the updated project data.

        Data schema:
        {
            "type": "object",
            "required": ["project/id", "project/name"],
            "properties": {
                "project/id": {"type": "string", "description": "Project identifier (26-char compact UUID)"},
                "project/name": {"type": "string", "description": "Project name"},
                "project/description": {"type": ["string", "null"], "description": "Project description"},
                "project/notes": {"type": ["string", "null"], "description": "Longer-form notes (Markdown supported)"},
                "project/comments": {"type": ["string", "null"], "description": "Project comments"},
                "project/archived": {"type": "boolean", "description": "Whether project is archived (default: false)"},
                "project/created": {"type": ["integer", "null"], "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "project/updated": {"type": ["integer", "null"], "description": "Last update timestamp (UNIX UTC milliseconds)"},
                "project/entry-count": {"type": ["integer", "null"], "description": "Number of BOM entries"},
                "project/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return projects.update_project(
        project_id=project_id,
        name=name,
        description=description,
        comments=comments,
    )


@mcp.tool()
def delete_project(project_id: str) -> projects.ProjectOperationResponse:
    """
    Delete a project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.delete_project(project_id)


@mcp.tool()
def archive_project(project_id: str) -> projects.ProjectOperationResponse:
    """
    Archive a project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.archive_project(project_id)


@mcp.tool()
def restore_project(project_id: str) -> projects.ProjectOperationResponse:
    """
    Restore an archived project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.restore_project(project_id)


@mcp.tool()
def get_project_entries(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
    build_id: str | None = None,
) -> projects.PaginatedEntriesResponse:
    """
    Get BOM entries for a project.

    Args:
        project_id: The project ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "entry/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "entry/quantity", "entry/part-id", "entry/order"
            - WRONG: `entry/quantity` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `entry/quantity` evaluates to the literal string "entry/quantity", not the field value.

            Standard JMESPath examples:
            - "[?\"entry/quantity\" > `10`]" - entries with quantity > 10
            - "sort_by(@, &\"entry/order\")" - sort by BOM order

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"entry/name\", ''), 'capacitor')]" - safe name search
            - "[?contains(nvl(\"entry/comments\", ''), 'DNP')]" - safe comments search

        build_id: Optional build ID for historical BOM snapshot

    Returns:
        PaginatedEntriesResponse with BOM entries and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "entry/id": {"type": "string", "description": "Entry identifier"},
                "entry/part-id": {"type": "string", "description": "Part identifier"},
                "entry/quantity": {"type": "integer", "description": "Quantity per board"},
                "entry/name": {"type": ["string", "null"], "description": "BOM name for this entry"},
                "entry/comments": {"type": ["string", "null"], "description": "Additional comments"},
                "entry/designators": {"type": ["array", "null"], "items": {"type": "string"}, "description": "Set of designators (e.g., R1, R2, C1)"},
                "entry/order": {"type": "integer", "description": "Ordering within the BOM"},
                "entry/cad-footprint": {"type": ["string", "null"], "description": "Footprint from CAD program"},
                "entry/cad-key": {"type": ["string", "null"], "description": "CAD key for matching to parts"},
                "entry/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return projects.get_project_entries(
        project_id=project_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
        build_id=build_id,
    )


@mcp.tool()
def add_project_entries(
    project_id: str,
    entries: list[dict[str, Any]],
) -> projects.ProjectOperationResponse:
    """
    Add BOM entries to a project.

    Args:
        project_id: The project ID
        entries: List of entry objects with required fields:
            - entry/part-id: The part ID
            - entry/quantity: Quantity per board
            - Optional: entry/designators, entry/comments

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.add_project_entries(
        project_id=project_id,
        entries=entries,
    )


@mcp.tool()
def update_project_entries(
    project_id: str,
    entries: list[dict[str, Any]],
) -> projects.ProjectOperationResponse:
    """
    Update existing BOM entries.

    Args:
        project_id: The project ID
        entries: List of entry objects with entry/id and fields to update

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.update_project_entries(
        project_id=project_id,
        entries=entries,
    )


@mcp.tool()
def delete_project_entries(
    project_id: str,
    entry_ids: list[str],
) -> projects.ProjectOperationResponse:
    """
    Delete BOM entries from a project.

    Args:
        project_id: The project ID
        entry_ids: List of entry IDs to delete

    Returns:
        ProjectOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return projects.delete_project_entries(
        project_id=project_id,
        entry_ids=entry_ids,
    )


@mcp.tool()
def get_project_builds(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> projects.PaginatedBuildsResponse:
    """
    List all builds for a project.

    Args:
        project_id: The project ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "build/id").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "build/id", "build/project-id", "build/comments"
            - WRONG: `build/id` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `build/id` evaluates to the literal string "build/id", not the field value.

            Standard JMESPath examples:
            - "sort_by(@, &\"build/id\")" - sort by build ID

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"build/comments\", ''), 'prototype')]" - safe comments search

    Returns:
        PaginatedBuildsResponse with builds data and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "build/id": {"type": "string", "description": "Build identifier (26-char compact UUID)"},
                "build/project-id": {"type": "string", "description": "Parent project identifier"},
                "build/comments": {"type": ["string", "null"], "description": "Build notes/comments"}
            }
        }
    """
    return projects.get_project_builds(
        project_id=project_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_build(build_id: str) -> projects.BuildResponse:
    """
    Get detailed information for a specific build.

    Args:
        build_id: The unique identifier of the build

    Returns:
        BuildResponse with build data or error.

        Data schema:
        {
            "type": "object",
            "properties": {
                "build/id": {"type": "string", "description": "Build identifier (26-char compact UUID)"},
                "build/project-id": {"type": "string", "description": "Parent project identifier"},
                "build/comments": {"type": ["string", "null"], "description": "Build notes/comments"}
            }
        }
    """
    return projects.get_build(build_id)


@mcp.tool()
def update_build(
    build_id: str,
    comments: str | None = None,
) -> projects.BuildResponse:
    """
    Update build metadata.

    Args:
        build_id: The unique identifier of the build
        comments: Optional new comments

    Returns:
        BuildResponse with the updated build data.

        Data schema:
        {
            "type": "object",
            "properties": {
                "build/id": {"type": "string", "description": "Build identifier (26-char compact UUID)"},
                "build/project-id": {"type": "string", "description": "Parent project identifier"},
                "build/comments": {"type": ["string", "null"], "description": "Build notes/comments"}
            }
        }
    """
    return projects.update_build(
        build_id=build_id,
        comments=comments,
    )


# =============================================================================
# Orders Tools
# =============================================================================


@mcp.tool()
def list_orders(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> orders.PaginatedOrdersResponse:
    """
    List all orders with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "order/vendor-name").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "order/vendor-name", "order/id", "order/created"
            - WRONG: `order/vendor-name` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `order/vendor-name` evaluates to the literal string "order/vendor-name", not the field value.

            Standard JMESPath examples:
            - "[?\"order/arriving\" != null]" - orders with expected delivery
            - "sort_by(@, &\"order/created\")" - sort by creation date

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?contains(nvl(\"order/vendor-name\", ''), 'Mouser')]" - safe vendor search
            - "[?contains(nvl(\"order/comments\", ''), 'urgent')]" - safe comments search

    Returns:
        PaginatedOrdersResponse with orders data and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "order/id": {"type": "string", "description": "Order identifier (26-char compact UUID)"},
                "order/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "order/vendor-name": {"type": ["string", "null"], "description": "Vendor or distributor name"},
                "order/number": {"type": ["string", "null"], "description": "Vendor's order number"},
                "order/invoice-number": {"type": ["string", "null"], "description": "Vendor's invoice number"},
                "order/po-number": {"type": ["string", "null"], "description": "Purchase order number"},
                "order/comments": {"type": ["string", "null"], "description": "Order comments"},
                "order/notes": {"type": ["string", "null"], "description": "Additional notes (Markdown supported)"},
                "order/arriving": {"type": ["integer", "null"], "description": "Expected delivery timestamp (UNIX UTC milliseconds)"},
                "order/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "order/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return orders.list_orders(
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def get_order(order_id: str) -> orders.OrderResponse:
    """
    Get detailed information for a specific order.

    Args:
        order_id: The unique identifier of the order

    Returns:
        OrderResponse with order data or error.

        Data schema:
        {
            "type": "object",
            "properties": {
                "order/id": {"type": "string", "description": "Order identifier (26-char compact UUID)"},
                "order/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "order/vendor-name": {"type": ["string", "null"], "description": "Vendor or distributor name"},
                "order/number": {"type": ["string", "null"], "description": "Vendor's order number"},
                "order/invoice-number": {"type": ["string", "null"], "description": "Vendor's invoice number"},
                "order/po-number": {"type": ["string", "null"], "description": "Purchase order number"},
                "order/comments": {"type": ["string", "null"], "description": "Order comments"},
                "order/notes": {"type": ["string", "null"], "description": "Additional notes (Markdown supported)"},
                "order/arriving": {"type": ["integer", "null"], "description": "Expected delivery timestamp (UNIX UTC milliseconds)"},
                "order/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "order/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return orders.get_order(order_id)


@mcp.tool()
def create_order(
    vendor: str,
    order_number: str | None = None,
    comments: str | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> orders.OrderOperationResponse:
    """
    Create a new purchase order.

    Args:
        vendor: The vendor/supplier name
        order_number: Optional vendor order number
        comments: Optional order comments
        entries: Optional list of initial order entries

    Returns:
        OrderOperationResponse with the created order data.

        Data schema:
        {
            "type": "object",
            "properties": {
                "order/id": {"type": "string", "description": "Order identifier (26-char compact UUID)"},
                "order/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "order/vendor-name": {"type": ["string", "null"], "description": "Vendor or distributor name"},
                "order/number": {"type": ["string", "null"], "description": "Vendor's order number"},
                "order/invoice-number": {"type": ["string", "null"], "description": "Vendor's invoice number"},
                "order/po-number": {"type": ["string", "null"], "description": "Purchase order number"},
                "order/comments": {"type": ["string", "null"], "description": "Order comments"},
                "order/notes": {"type": ["string", "null"], "description": "Additional notes (Markdown supported)"},
                "order/arriving": {"type": ["integer", "null"], "description": "Expected delivery timestamp (UNIX UTC milliseconds)"},
                "order/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "order/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    return orders.create_order(
        vendor=vendor,
        order_number=order_number,
        comments=comments,
        entries=entries,
    )


@mcp.tool()
def get_order_entries(
    order_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> orders.PaginatedOrderEntriesResponse:
    """
    List stock items in an order.

    Args:
        order_id: The order ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

            CRITICAL SYNTAX NOTE: Field names contain '/' characters (e.g., "stock/quantity").
            You MUST use DOUBLE QUOTES for field identifiers, NOT backticks:
            - CORRECT: "stock/quantity", "stock/part-id", "stock/price"
            - WRONG: `stock/quantity` (backticks create literal strings, not field references)

            Using backticks will silently fail - queries will return empty results because
            `stock/quantity` evaluates to the literal string "stock/quantity", not the field value.

            Standard JMESPath examples:
            - "[?\"stock/quantity\" > `100`]" - entries with quantity > 100
            - "sort_by(@, &\"stock/price\")" - sort by price

            Custom functions available:
            - nvl(value, default): Returns default if value is null
            - int(value): Convert to integer (returns null on failure)
            - str(value): Convert to string
            - regex_replace(pattern, replacement, value): Regex substitution

            IMPORTANT: Use nvl() for safe filtering on nullable fields to avoid errors:
            - "[?nvl(\"stock/currency\", '') == 'USD']" - safe currency check
            - "[?contains(nvl(\"stock/comments\", ''), 'priority')]" - safe comments search

    Returns:
        PaginatedOrderEntriesResponse with order entries and pagination info.

        Data items schema:
        {
            "type": "object",
            "properties": {
                "stock/id": {"type": "string", "description": "Stock entry identifier"},
                "stock/part-id": {"type": "string", "description": "Part identifier"},
                "stock/storage-id": {"type": ["string", "null"], "description": "Storage location identifier"},
                "stock/lot-id": {"type": ["string", "null"], "description": "Lot identifier"},
                "stock/quantity": {"type": "integer", "description": "Quantity ordered"},
                "stock/price": {"type": ["number", "null"], "description": "Unit price"},
                "stock/currency": {"type": ["string", "null"], "description": "Currency code (e.g., USD, EUR)"},
                "stock/timestamp": {"type": "integer", "description": "Creation timestamp (UNIX UTC milliseconds)"},
                "stock/status": {"type": ["string", "null"], "description": "Stock status or null for on-hand"},
                "stock/comments": {"type": ["string", "null"], "description": "Entry notes"},
                "stock/order-id": {"type": "string", "description": "Parent order identifier"},
                "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU that was ordered"},
                "stock/arriving": {"type": ["integer", "null"], "description": "Expected delivery date (UNIX UTC milliseconds)"}
            }
        }
    """
    return orders.get_order_entries(
        order_id=order_id,
        limit=limit,
        offset=offset,
        cache_key=cache_key,
        query=query,
    )


@mcp.tool()
def add_order_entries(
    order_id: str,
    entries: list[dict[str, Any]],
) -> orders.OrderOperationResponse:
    """
    Add items to an open order.

    Args:
        order_id: The order ID
        entries: List of entry objects with required fields:
            - entry/part-id: The part ID
            - entry/quantity: Ordered quantity
            - Optional: entry/price, entry/currency

    Returns:
        OrderOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return orders.add_order_entries(
        order_id=order_id,
        entries=entries,
    )


@mcp.tool()
def receive_order(
    order_id: str,
    storage_id: str,
    entries: list[dict[str, Any]] | None = None,
    comments: str | None = None,
) -> orders.OrderOperationResponse:
    """
    Process received inventory into storage.

    Args:
        order_id: The order ID
        storage_id: The storage location to receive into
        entries: Optional list of entry objects specifying which items
                 and quantities to receive. If not specified, all items
                 are received.
        comments: Optional comments for the receipt

    Returns:
        OrderOperationResponse with the operation result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return orders.receive_order(
        order_id=order_id,
        storage_id=storage_id,
        entries=entries,
        comments=comments,
    )


@mcp.tool()
def delete_order_entry(
    order_id: str,
    stock_id: str,
) -> orders.OrderOperationResponse:
    """
    Delete an entry from an open order.

    This removes a line item from an order that has not yet been received.

    Args:
        order_id: The order ID
        stock_id: The stock entry ID to delete (obtained from order/get-entries)

    Returns:
        OrderOperationResponse with the result.

        Note: The PartsBox API returns status information. Data may be null on success.
    """
    return orders.delete_order_entry(order_id=order_id, stock_id=stock_id)


# =============================================================================
# Files Tools
# =============================================================================


@mcp.tool()
def download_file(file_id: str) -> FileDownloadResponse:
    """
    Download a file from PartsBox.

    Files in PartsBox are typically images or datasheets associated with parts.
    The file_id can be obtained from part data (e.g., part/img-id field).

    Args:
        file_id: The file identifier (obtained from part data, e.g., part/img-id)

    Returns:
        FileDownloadResponse containing:
        - success: Whether the download succeeded
        - data: Raw file bytes (if successful)
        - content_type: MIME type of the file (e.g., "image/png", "application/pdf")
        - filename: Suggested filename from server (if provided)
        - error: Error message (if failed)

    Example:
        # Get a part and download its image
        part = get_part("part_abc123")
        if part.data and part.data.get("part/img-id"):
            file_result = download_file(part.data["part/img-id"])
            if file_result.success:
                with open("part_image.png", "wb") as f:
                    f.write(file_result.data)
    """
    return files.download_file(file_id)


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

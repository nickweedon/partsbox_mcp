"""
PartsBox MCP Server - Main Entry Point

This module sets up the FastMCP server and registers all tools
from the API modules.
"""

from typing import Any

from fastmcp import FastMCP

from partsbox_mcp.api import lots, orders, parts, projects, stock, storage
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
        StockOperationResponse with the created stock entry
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
        StockOperationResponse with the result
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
        StockOperationResponse with the result
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
        StockOperationResponse with the updated stock entry
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
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedLotsResponse with lots data and pagination info
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
        LotResponse with lot data or error
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
        LotUpdateResponse with the updated lot data
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
        query: JMESPath expression for filtering/projection
        include_archived: Include archived locations (default False)

    Returns:
        PaginatedStorageResponse with storage locations and pagination info
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
        StorageResponse with storage data or error
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
        StorageOperationResponse with the updated storage data
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
        StorageOperationResponse with the updated storage data
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
        StorageOperationResponse with the result
    """
    return storage.archive_storage_location(storage_id)


@mcp.tool()
def restore_storage_location(storage_id: str) -> storage.StorageOperationResponse:
    """
    Restore an archived storage location.

    Args:
        storage_id: The unique identifier of the storage location

    Returns:
        StorageOperationResponse with the result
    """
    return storage.restore_storage_location(storage_id)


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
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedStoragePartsResponse with parts data and pagination info
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
    List individual lots in a storage location.

    Args:
        storage_id: The storage location ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedStorageLotsResponse with lots data and pagination info
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
        query: JMESPath expression for filtering/projection
        include_archived: Include archived projects (default False)

    Returns:
        PaginatedProjectsResponse with projects data and pagination info
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
        ProjectResponse with project data or error
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
        ProjectOperationResponse with the created project data
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
        ProjectOperationResponse with the updated project data
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
        ProjectOperationResponse with the result
    """
    return projects.delete_project(project_id)


@mcp.tool()
def archive_project(project_id: str) -> projects.ProjectOperationResponse:
    """
    Archive a project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the result
    """
    return projects.archive_project(project_id)


@mcp.tool()
def restore_project(project_id: str) -> projects.ProjectOperationResponse:
    """
    Restore an archived project.

    Args:
        project_id: The unique identifier of the project

    Returns:
        ProjectOperationResponse with the result
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
        query: JMESPath expression for filtering/projection
        build_id: Optional build ID for historical BOM snapshot

    Returns:
        PaginatedEntriesResponse with BOM entries and pagination info
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
        ProjectOperationResponse with the result
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
        ProjectOperationResponse with the result
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
        ProjectOperationResponse with the result
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
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedBuildsResponse with builds data and pagination info
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
        BuildResponse with build data or error
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
        BuildResponse with the updated build data
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
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedOrdersResponse with orders data and pagination info
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
        OrderResponse with order data or error
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
        OrderOperationResponse with the created order data
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
        query: JMESPath expression for filtering/projection

    Returns:
        PaginatedOrderEntriesResponse with order entries and pagination info
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
        OrderOperationResponse with the result
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
        OrderOperationResponse with the result
    """
    return orders.receive_order(
        order_id=order_id,
        storage_id=storage_id,
        entries=entries,
        comments=comments,
    )


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

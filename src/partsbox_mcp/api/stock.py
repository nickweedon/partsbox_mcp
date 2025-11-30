"""
Stock API module.

Provides MCP tools for stock management operations:
- stock/add - Add inventory for a part
- stock/remove - Remove parts from inventory
- stock/move - Transfer stock to different location
- stock/update - Modify existing stock entry
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class StockOperationResponse:
    """Response for stock modification operations."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedStockResponse:
    """Response for paginated stock listing."""

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
) -> StockOperationResponse:
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
    if not part_id:
        return StockOperationResponse(success=False, error="part_id is required")
    if not storage_id:
        return StockOperationResponse(success=False, error="storage_id is required")
    if quantity <= 0:
        return StockOperationResponse(success=False, error="quantity must be positive")

    payload: dict[str, Any] = {
        "stock/part-id": part_id,
        "stock/storage-id": storage_id,
        "stock/quantity": quantity,
    }

    if comments:
        payload["stock/comments"] = comments
    if price is not None:
        payload["stock/price"] = price
    if currency:
        payload["stock/currency"] = currency
    if lot_name:
        payload["lot/name"] = lot_name
    if lot_description:
        payload["lot/description"] = lot_description
    if order_id:
        payload["stock/order-id"] = order_id

    try:
        result = api_client._request("stock/add", payload)
        return StockOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StockOperationResponse(success=False, error=f"API request failed: {e}")


def remove_stock(
    part_id: str,
    storage_id: str,
    quantity: int,
    comments: str | None = None,
    lot_id: str | None = None,
) -> StockOperationResponse:
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
    if not part_id:
        return StockOperationResponse(success=False, error="part_id is required")
    if not storage_id:
        return StockOperationResponse(success=False, error="storage_id is required")
    if quantity <= 0:
        return StockOperationResponse(success=False, error="quantity must be positive")

    payload: dict[str, Any] = {
        "stock/part-id": part_id,
        "stock/storage-id": storage_id,
        "stock/quantity": quantity,
    }

    if comments:
        payload["stock/comments"] = comments
    if lot_id:
        payload["stock/lot-id"] = lot_id

    try:
        result = api_client._request("stock/remove", payload)
        return StockOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StockOperationResponse(success=False, error=f"API request failed: {e}")


def move_stock(
    part_id: str,
    source_storage_id: str,
    target_storage_id: str,
    quantity: int,
    comments: str | None = None,
    lot_id: str | None = None,
) -> StockOperationResponse:
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
    if not part_id:
        return StockOperationResponse(success=False, error="part_id is required")
    if not source_storage_id:
        return StockOperationResponse(
            success=False, error="source_storage_id is required"
        )
    if not target_storage_id:
        return StockOperationResponse(
            success=False, error="target_storage_id is required"
        )
    if quantity <= 0:
        return StockOperationResponse(success=False, error="quantity must be positive")

    payload: dict[str, Any] = {
        "stock/part-id": part_id,
        "stock/storage-id": source_storage_id,
        "stock/target-storage-id": target_storage_id,
        "stock/quantity": quantity,
    }

    if comments:
        payload["stock/comments"] = comments
    if lot_id:
        payload["stock/lot-id"] = lot_id

    try:
        result = api_client._request("stock/move", payload)
        return StockOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StockOperationResponse(success=False, error=f"API request failed: {e}")


def update_stock(
    part_id: str,
    timestamp: int,
    quantity: int | None = None,
    comments: str | None = None,
    price: float | None = None,
    currency: str | None = None,
) -> StockOperationResponse:
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
    if not part_id:
        return StockOperationResponse(success=False, error="part_id is required")
    if not timestamp:
        return StockOperationResponse(success=False, error="timestamp is required")

    payload: dict[str, Any] = {
        "stock/part-id": part_id,
        "stock/timestamp": timestamp,
    }

    if quantity is not None:
        payload["stock/quantity"] = quantity
    if comments is not None:
        payload["stock/comments"] = comments
    if price is not None:
        payload["stock/price"] = price
    if currency is not None:
        payload["stock/currency"] = currency

    try:
        result = api_client._request("stock/update", payload)
        return StockOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return StockOperationResponse(success=False, error=f"API request failed: {e}")

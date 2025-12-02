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

from partsbox_mcp.client import api_client
from partsbox_mcp.types import StockEntryData


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class StockOperationResponse:
    """Response for stock modification operations."""

    success: bool
    data: StockEntryData | None = None
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
    data: list[StockEntryData]
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
    """Add inventory for a part."""
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
    """Remove parts from inventory."""
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
    """Transfer stock to a different location."""
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
    """Modify an existing stock entry."""
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

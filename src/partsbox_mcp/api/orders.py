"""
Orders API module.

Provides MCP tools for order management:
- order/all - List all orders
- order/get - Retrieve order details
- order/create - Create new purchase order
- order/get-entries - List stock items in order
- order/add-entries - Add items to open orders
- order/receive - Process received inventory into storage
"""

from dataclasses import dataclass
from typing import Any

import requests

from partsbox_mcp.client import api_client, apply_query, cache


# =============================================================================
# Response Types
# =============================================================================


@dataclass
class OrderResponse:
    """Response for a single order."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedOrdersResponse:
    """Response for paginated orders listing."""

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
class OrderOperationResponse:
    """Response for order modification operations."""

    success: bool
    data: dict[str, Any] | None = None
    error: str | None = None


@dataclass
class PaginatedOrderEntriesResponse:
    """Response for paginated order entries."""

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


def list_orders(
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedOrdersResponse:
    """
    List all orders with optional JMESPath query and pagination.

    Args:
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

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
                "order/created": {"type": "integer", "description": "Creation timestamp (UNIX UTC)"},
                "order/vendor-name": {"type": ["string", "null"], "description": "Vendor or distributor name"},
                "order/number": {"type": ["string", "null"], "description": "Vendor's order number"},
                "order/invoice-number": {"type": ["string", "null"], "description": "Vendor's invoice number"},
                "order/po-number": {"type": ["string", "null"], "description": "Purchase order number"},
                "order/comments": {"type": ["string", "null"], "description": "Order comments"},
                "order/notes": {"type": ["string", "null"], "description": "Additional notes (Markdown supported)"},
                "order/arriving": {"type": ["integer", "null"], "description": "Expected delivery timestamp (UNIX UTC)"},
                "order/tags": {"type": "array", "items": {"type": "string"}, "description": "List of tags"},
                "order/custom-fields": {"type": ["object", "null"], "description": "Custom field data"}
            }
        }
    """
    if limit < 1 or limit > 1000:
        return PaginatedOrdersResponse(
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
        return PaginatedOrdersResponse(
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
                result = api_client._request("order/all")
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("order/all")
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedOrdersResponse(
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
            return PaginatedOrdersResponse(
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
        return PaginatedOrdersResponse(
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

    return PaginatedOrdersResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def get_order(order_id: str) -> OrderResponse:
    """
    Get detailed information for a specific order.

    Args:
        order_id: The unique identifier of the order

    Returns:
        OrderResponse with order data or error
    """
    if not order_id:
        return OrderResponse(success=False, error="order_id is required")

    try:
        result = api_client._request("order/get", {"order/id": order_id})
        data = result.get("data")
        if data is None:
            return OrderResponse(success=False, error=f"Order not found: {order_id}")
        return OrderResponse(success=True, data=data)
    except requests.RequestException as e:
        return OrderResponse(success=False, error=f"API request failed: {e}")


def create_order(
    vendor: str,
    order_number: str | None = None,
    comments: str | None = None,
    entries: list[dict[str, Any]] | None = None,
) -> OrderOperationResponse:
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
    if not vendor:
        return OrderOperationResponse(success=False, error="vendor is required")

    payload: dict[str, Any] = {"order/vendor": vendor}

    if order_number is not None:
        payload["order/number"] = order_number
    if comments is not None:
        payload["order/comments"] = comments
    if entries is not None:
        payload["order/entries"] = entries

    try:
        result = api_client._request("order/create", payload)
        return OrderOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return OrderOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def get_order_entries(
    order_id: str,
    limit: int = 50,
    offset: int = 0,
    cache_key: str | None = None,
    query: str | None = None,
) -> PaginatedOrderEntriesResponse:
    """
    List stock items in an order.

    Args:
        order_id: The order ID
        limit: Maximum items to return (1-1000, default 50)
        offset: Starting index in query results (default 0)
        cache_key: Reuse cached data from previous call. Omit for fresh fetch.
        query: JMESPath expression for filtering/projection with custom functions.

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
                "stock/timestamp": {"type": "integer", "description": "Creation timestamp (UNIX UTC)"},
                "stock/status": {"type": ["string", "null"], "description": "Stock status or null for on-hand"},
                "stock/comments": {"type": ["string", "null"], "description": "Entry notes"},
                "stock/order-id": {"type": "string", "description": "Parent order identifier"},
                "stock/vendor-sku": {"type": ["string", "null"], "description": "Vendor SKU that was ordered"},
                "stock/arriving": {"type": ["integer", "null"], "description": "Expected delivery date (UNIX UTC)"}
            }
        }
    """
    if not order_id:
        return PaginatedOrderEntriesResponse(
            success=False,
            error="order_id is required",
            cache_key="",
            total=0,
            offset=0,
            limit=limit,
            has_more=False,
            data=[],
        )

    if limit < 1 or limit > 1000:
        return PaginatedOrderEntriesResponse(
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
        return PaginatedOrderEntriesResponse(
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
                    "order/get-entries", {"order/id": order_id}
                )
                data = result.get("data", [])
                key = cache.create(data)
        else:
            result = api_client._request("order/get-entries", {"order/id": order_id})
            data = result.get("data", [])
            key = cache.create(data)
    except requests.RequestException as e:
        return PaginatedOrderEntriesResponse(
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
            return PaginatedOrderEntriesResponse(
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
        return PaginatedOrderEntriesResponse(
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

    return PaginatedOrderEntriesResponse(
        success=True,
        cache_key=key,
        total=total,
        offset=offset,
        limit=limit,
        has_more=offset + limit < total,
        query_applied=query,
        data=page,
    )


def add_order_entries(
    order_id: str,
    entries: list[dict[str, Any]],
) -> OrderOperationResponse:
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
    if not order_id:
        return OrderOperationResponse(success=False, error="order_id is required")
    if not entries:
        return OrderOperationResponse(success=False, error="entries is required")

    payload: dict[str, Any] = {
        "order/id": order_id,
        "order/entries": entries,
    }

    try:
        result = api_client._request("order/add-entries", payload)
        return OrderOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return OrderOperationResponse(
            success=False, error=f"API request failed: {e}"
        )


def receive_order(
    order_id: str,
    storage_id: str,
    entries: list[dict[str, Any]] | None = None,
    comments: str | None = None,
) -> OrderOperationResponse:
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
    if not order_id:
        return OrderOperationResponse(success=False, error="order_id is required")
    if not storage_id:
        return OrderOperationResponse(success=False, error="storage_id is required")

    payload: dict[str, Any] = {
        "order/id": order_id,
        "stock/storage-id": storage_id,
    }

    if entries is not None:
        payload["order/entries"] = entries
    if comments is not None:
        payload["stock/comments"] = comments

    try:
        result = api_client._request("order/receive", payload)
        return OrderOperationResponse(success=True, data=result.get("data"))
    except requests.RequestException as e:
        return OrderOperationResponse(
            success=False, error=f"API request failed: {e}"
        )

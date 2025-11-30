"""
Unit tests for the Orders API module.

Tests cover:
- list_orders: Paginated orders listing
- get_order: Retrieve single order
- create_order: Create new purchase order
- get_order_entries: List order items
- add_order_entries: Add items to order
- receive_order: Process received inventory
"""

import pytest

from partsbox_mcp.api.orders import (
    add_order_entries,
    create_order,
    get_order,
    get_order_entries,
    list_orders,
    receive_order,
)
from partsbox_mcp.client import cache


class TestListOrders:
    """Tests for the list_orders tool function."""

    def test_list_orders_returns_all(self, fake_api_active):
        """list_orders returns all orders with default parameters."""
        result = list_orders()

        assert result.success is True
        assert result.total == 2  # Sample has 2 orders
        assert len(result.data) == 2
        assert result.error is None

    def test_list_orders_returns_cache_key(self, fake_api_active):
        """list_orders returns a valid cache key."""
        result = list_orders()

        assert result.success is True
        assert result.cache_key is not None
        assert result.cache_key.startswith("pb_")

    def test_list_orders_pagination_limit(self, fake_api_active):
        """list_orders respects the limit parameter."""
        result = list_orders(limit=1)

        assert result.success is True
        assert len(result.data) == 1
        assert result.has_more is True

    def test_list_orders_pagination_offset(self, fake_api_active):
        """list_orders respects the offset parameter."""
        result = list_orders(limit=1, offset=1)

        assert result.success is True
        assert len(result.data) == 1
        assert result.offset == 1
        assert result.has_more is False

    def test_list_orders_cache_reuse(self, fake_api_active):
        """list_orders reuses cached data."""
        result1 = list_orders(limit=1)
        cache_key = result1.cache_key

        result2 = list_orders(limit=1, offset=1, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key

    def test_list_orders_invalid_limit_low(self, fake_api_active):
        """list_orders rejects limit < 1."""
        result = list_orders(limit=0)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_orders_invalid_limit_high(self, fake_api_active):
        """list_orders rejects limit > 1000."""
        result = list_orders(limit=1001)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_orders_invalid_offset(self, fake_api_active):
        """list_orders rejects negative offset."""
        result = list_orders(offset=-1)

        assert result.success is False
        assert "offset must be non-negative" in result.error


class TestListOrdersJMESPath:
    """Tests for JMESPath query support in list_orders."""

    def test_query_filter_by_vendor(self, fake_api_active):
        """JMESPath filter by vendor works."""
        result = list_orders(query='[?contains("order/vendor", \'Mouser\')]')

        assert result.success is True
        assert result.total == 1  # Only Mouser order

    def test_query_filter_by_status(self, fake_api_active):
        """JMESPath filter by status works."""
        result = list_orders(query='[?"order/status" == \'open\']')

        assert result.success is True
        assert result.total == 1  # One open order

    def test_query_projection(self, fake_api_active):
        """JMESPath projection works."""
        result = list_orders(query='[*].{vendor: "order/vendor", status: "order/status"}')

        assert result.success is True
        first = result.data[0]
        assert "vendor" in first
        assert "status" in first
        assert "order/id" not in first

    def test_query_invalid_expression(self, fake_api_active):
        """Invalid JMESPath expression returns error."""
        result = list_orders(query="[?invalid syntax")

        assert result.success is False
        assert "Invalid query expression" in result.error


class TestGetOrder:
    """Tests for the get_order tool function."""

    def test_get_order_success(self, fake_api_active):
        """get_order returns the correct order."""
        result = get_order("order_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["order/id"] == "order_001"
        assert result.data["order/vendor"] == "Mouser Electronics"
        assert result.error is None

    def test_get_order_not_found(self, fake_api_active):
        """get_order returns error for non-existent order."""
        result = get_order("nonexistent_order")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_get_order_empty_id(self, fake_api_active):
        """get_order returns error for empty order_id."""
        result = get_order("")

        assert result.success is False
        assert "order_id is required" in result.error

    def test_get_order_returns_full_data(self, fake_api_active):
        """get_order returns complete order data."""
        result = get_order("order_001")

        assert result.success is True
        order = result.data

        assert "order/id" in order
        assert "order/vendor" in order
        assert "order/number" in order
        assert "order/status" in order
        assert "order/created" in order


class TestCreateOrder:
    """Tests for the create_order tool function."""

    def test_create_order_success(self, fake_api_active):
        """create_order successfully creates an order."""
        result = create_order(vendor="New Vendor")

        assert result.success is True
        assert result.data is not None
        assert result.data["order/vendor"] == "New Vendor"
        assert result.data["order/status"] == "open"

    def test_create_order_with_number(self, fake_api_active):
        """create_order works with order number."""
        result = create_order(
            vendor="Mouser Electronics",
            order_number="MO-99999",
        )

        assert result.success is True
        assert result.data is not None

    def test_create_order_with_comments(self, fake_api_active):
        """create_order works with comments."""
        result = create_order(
            vendor="DigiKey",
            comments="Urgent order",
        )

        assert result.success is True

    def test_create_order_missing_vendor(self, fake_api_active):
        """create_order returns error for missing vendor."""
        result = create_order(vendor="")

        assert result.success is False
        assert "vendor is required" in result.error


class TestGetOrderEntries:
    """Tests for the get_order_entries tool function."""

    def test_get_order_entries_success(self, fake_api_active):
        """get_order_entries returns entries for an order."""
        result = get_order_entries("order_001")

        assert result.success is True
        assert result.total == 2  # Order 001 has 2 entries

    def test_get_order_entries_missing_id(self, fake_api_active):
        """get_order_entries returns error for missing order_id."""
        result = get_order_entries("")

        assert result.success is False
        assert "order_id is required" in result.error

    def test_get_order_entries_pagination(self, fake_api_active):
        """get_order_entries supports pagination."""
        result = get_order_entries("order_001", limit=1)

        assert result.success is True
        assert len(result.data) == 1
        assert result.has_more is True

    def test_get_order_entries_cache_reuse(self, fake_api_active):
        """get_order_entries reuses cached data."""
        result1 = get_order_entries("order_001", limit=1)
        cache_key = result1.cache_key

        result2 = get_order_entries("order_001", limit=1, offset=1, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key


class TestAddOrderEntries:
    """Tests for the add_order_entries tool function."""

    def test_add_order_entries_success(self, fake_api_active):
        """add_order_entries successfully adds entries."""
        entries = [
            {"entry/part-id": "part_001", "entry/quantity": 500},
        ]
        result = add_order_entries("order_001", entries)

        assert result.success is True

    def test_add_order_entries_with_pricing(self, fake_api_active):
        """add_order_entries works with pricing."""
        entries = [
            {
                "entry/part-id": "part_002",
                "entry/quantity": 1000,
                "entry/price": 0.01,
                "entry/currency": "usd",
            },
        ]
        result = add_order_entries("order_001", entries)

        assert result.success is True

    def test_add_order_entries_missing_order_id(self, fake_api_active):
        """add_order_entries returns error for missing order_id."""
        result = add_order_entries("", [{"entry/part-id": "part_001", "entry/quantity": 100}])

        assert result.success is False
        assert "order_id is required" in result.error

    def test_add_order_entries_missing_entries(self, fake_api_active):
        """add_order_entries returns error for missing entries."""
        result = add_order_entries("order_001", [])

        assert result.success is False
        assert "entries is required" in result.error


class TestReceiveOrder:
    """Tests for the receive_order tool function."""

    def test_receive_order_success(self, fake_api_active):
        """receive_order successfully processes received inventory."""
        result = receive_order(
            order_id="order_001",
            storage_id="loc_001",
        )

        assert result.success is True

    def test_receive_order_with_comments(self, fake_api_active):
        """receive_order works with comments."""
        result = receive_order(
            order_id="order_001",
            storage_id="loc_001",
            comments="Received in good condition",
        )

        assert result.success is True

    def test_receive_order_with_entries(self, fake_api_active):
        """receive_order works with specific entries."""
        entries = [
            {"entry/id": "oentry_001", "entry/quantity": 500},
        ]
        result = receive_order(
            order_id="order_001",
            storage_id="loc_001",
            entries=entries,
        )

        assert result.success is True

    def test_receive_order_missing_order_id(self, fake_api_active):
        """receive_order returns error for missing order_id."""
        result = receive_order(order_id="", storage_id="loc_001")

        assert result.success is False
        assert "order_id is required" in result.error

    def test_receive_order_missing_storage_id(self, fake_api_active):
        """receive_order returns error for missing storage_id."""
        result = receive_order(order_id="order_001", storage_id="")

        assert result.success is False
        assert "storage_id is required" in result.error

"""
Unit tests for the new Orders API methods.

Tests cover:
- delete_order_entry: Removing items from open orders
"""

import pytest

from partsbox_mcp.api.orders import delete_order_entry


class TestDeleteOrderEntry:
    """Tests for the delete_order_entry function."""

    def test_delete_order_entry_success(self, fake_api_active):
        """delete_order_entry successfully deletes an entry."""
        result = delete_order_entry(
            order_id="order_001",
            stock_id="oentry_001",
        )

        assert result.success is True
        assert result.error is None

    def test_delete_order_entry_empty_order_id(self, fake_api_active):
        """delete_order_entry fails with empty order_id."""
        result = delete_order_entry(order_id="", stock_id="oentry_001")

        assert result.success is False
        assert "order_id is required" in result.error

    def test_delete_order_entry_empty_stock_id(self, fake_api_active):
        """delete_order_entry fails with empty stock_id."""
        result = delete_order_entry(order_id="order_001", stock_id="")

        assert result.success is False
        assert "stock_id is required" in result.error

"""
Unit tests for the Lots API module.

Tests cover:
- list_lots: Paginated lots listing with JMESPath queries
- get_lot: Retrieve single lot data
- update_lot: Modify lot information
"""

import pytest

from partsbox_mcp.api.lots import get_lot, list_lots, update_lot
from partsbox_mcp.client import cache


class TestListLots:
    """Tests for the list_lots tool function."""

    def test_list_lots_returns_all_lots(self, fake_api_active):
        """list_lots returns all lots with default parameters."""
        result = list_lots()

        assert result.success is True
        assert result.total == 3  # Sample has 3 lots
        assert len(result.data) == 3
        assert result.offset == 0
        assert result.limit == 50
        assert result.has_more is False
        assert result.error is None

    def test_list_lots_returns_cache_key(self, fake_api_active):
        """list_lots returns a valid cache key."""
        result = list_lots()

        assert result.success is True
        assert result.cache_key is not None
        assert result.cache_key.startswith("pb_")

    def test_list_lots_pagination_limit(self, fake_api_active):
        """list_lots respects the limit parameter."""
        result = list_lots(limit=2)

        assert result.success is True
        assert len(result.data) == 2
        assert result.total == 3
        assert result.has_more is True

    def test_list_lots_pagination_offset(self, fake_api_active):
        """list_lots respects the offset parameter."""
        result = list_lots(limit=2, offset=2)

        assert result.success is True
        assert len(result.data) == 1  # Only 1 lot remaining
        assert result.offset == 2
        assert result.has_more is False

    def test_list_lots_cache_reuse(self, fake_api_active):
        """list_lots reuses cached data when cache_key is provided."""
        result1 = list_lots(limit=2)
        cache_key = result1.cache_key

        result2 = list_lots(limit=2, offset=2, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key

    def test_list_lots_invalid_cache_key_fetches_fresh(self, fake_api_active):
        """list_lots fetches fresh data when cache_key is invalid."""
        result = list_lots(cache_key="pb_invalid1")

        assert result.success is True
        assert result.cache_key != "pb_invalid1"
        assert result.total == 3

    def test_list_lots_invalid_limit_low(self, fake_api_active):
        """list_lots rejects limit < 1."""
        result = list_lots(limit=0)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_lots_invalid_limit_high(self, fake_api_active):
        """list_lots rejects limit > 1000."""
        result = list_lots(limit=1001)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_lots_invalid_offset(self, fake_api_active):
        """list_lots rejects negative offset."""
        result = list_lots(offset=-1)

        assert result.success is False
        assert "offset must be non-negative" in result.error


class TestListLotsJMESPath:
    """Tests for JMESPath query support in list_lots."""

    def test_query_filter_by_name(self, fake_api_active):
        """JMESPath filter by name works."""
        result = list_lots(query='[?contains("lot/name", \'Batch\')]')

        assert result.success is True
        assert result.total == 2  # Two batch lots

    def test_query_filter_by_expiration(self, fake_api_active):
        """JMESPath filter by expiration works."""
        result = list_lots(query='[?"lot/expiration-date" != null]')

        assert result.success is True
        assert result.total == 1  # Only one lot has expiration

    def test_query_projection(self, fake_api_active):
        """JMESPath projection works."""
        result = list_lots(query='[*].{name: "lot/name", qty: "lot/quantity"}')

        assert result.success is True
        assert result.total == 3
        first = result.data[0]
        assert "name" in first
        assert "qty" in first
        assert "lot/id" not in first

    def test_query_invalid_expression(self, fake_api_active):
        """Invalid JMESPath expression returns error."""
        result = list_lots(query="[?invalid syntax")

        assert result.success is False
        assert "Invalid query expression" in result.error


class TestGetLot:
    """Tests for the get_lot tool function."""

    def test_get_lot_success(self, fake_api_active):
        """get_lot returns the correct lot."""
        result = get_lot("lot_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["lot/id"] == "lot_001"
        assert result.data["lot/name"] == "Batch 2024-01"
        assert result.error is None

    def test_get_lot_not_found(self, fake_api_active):
        """get_lot returns error for non-existent lot."""
        result = get_lot("nonexistent_lot")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_get_lot_empty_id(self, fake_api_active):
        """get_lot returns error for empty lot_id."""
        result = get_lot("")

        assert result.success is False
        assert "lot_id is required" in result.error

    def test_get_lot_returns_full_data(self, fake_api_active):
        """get_lot returns complete lot data."""
        result = get_lot("lot_001")

        assert result.success is True
        lot = result.data

        assert "lot/id" in lot
        assert "lot/name" in lot
        assert "lot/description" in lot
        assert "lot/part-id" in lot
        assert "lot/storage-id" in lot
        assert "lot/quantity" in lot


class TestUpdateLot:
    """Tests for the update_lot tool function."""

    def test_update_lot_success(self, fake_api_active):
        """update_lot successfully updates a lot."""
        result = update_lot(
            lot_id="lot_001",
            name="Updated Batch Name",
        )

        assert result.success is True
        assert result.data is not None

    def test_update_lot_with_description(self, fake_api_active):
        """update_lot works with description update."""
        result = update_lot(
            lot_id="lot_001",
            description="Updated description",
        )

        assert result.success is True

    def test_update_lot_with_tags(self, fake_api_active):
        """update_lot works with tags update."""
        result = update_lot(
            lot_id="lot_001",
            tags=["new-tag", "another-tag"],
        )

        assert result.success is True

    def test_update_lot_missing_id(self, fake_api_active):
        """update_lot returns error for missing lot_id."""
        result = update_lot(lot_id="")

        assert result.success is False
        assert "lot_id is required" in result.error

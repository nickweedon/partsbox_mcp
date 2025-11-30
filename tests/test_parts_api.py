"""
Unit tests for the Parts API module.

Tests cover:
- list_parts: Basic listing, pagination, caching, JMESPath queries
- get_part: Basic retrieval, not found handling
"""

import pytest

from partsbox_mcp.api.parts import list_parts, get_part
from partsbox_mcp.client import cache, api_client
from tests.fake_partsbox import SAMPLE_PARTS


class TestListParts:
    """Tests for the list_parts tool function."""

    def test_list_parts_returns_all_parts(self, fake_api_active, sample_parts):
        """list_parts returns all parts with default parameters."""
        result = list_parts()

        assert result.success is True
        assert result.total == len(sample_parts)
        assert len(result.data) == len(sample_parts)
        assert result.offset == 0
        assert result.limit == 50
        assert result.has_more is False
        assert result.error is None

    def test_list_parts_returns_cache_key(self, fake_api_active):
        """list_parts returns a valid cache key."""
        result = list_parts()

        assert result.success is True
        assert result.cache_key is not None
        assert result.cache_key.startswith("pb_")
        assert len(result.cache_key) == 11  # "pb_" + 8 hex chars

    def test_list_parts_pagination_limit(self, fake_api_active):
        """list_parts respects the limit parameter."""
        result = list_parts(limit=2)

        assert result.success is True
        assert len(result.data) == 2
        assert result.total == 5  # Total sample parts
        assert result.has_more is True
        assert result.limit == 2

    def test_list_parts_pagination_offset(self, fake_api_active):
        """list_parts respects the offset parameter."""
        result = list_parts(limit=2, offset=2)

        assert result.success is True
        assert len(result.data) == 2
        assert result.offset == 2
        assert result.has_more is True

    def test_list_parts_pagination_last_page(self, fake_api_active):
        """list_parts correctly identifies the last page."""
        result = list_parts(limit=2, offset=4)

        assert result.success is True
        assert len(result.data) == 1  # Only 1 part left
        assert result.has_more is False

    def test_list_parts_cache_reuse(self, fake_api_active):
        """list_parts reuses cached data when cache_key is provided."""
        # First call - get cache key
        result1 = list_parts(limit=2)
        cache_key = result1.cache_key

        # Second call - use cache key
        result2 = list_parts(limit=2, offset=2, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key
        assert result2.offset == 2

    def test_list_parts_invalid_cache_key_fetches_fresh(self, fake_api_active):
        """list_parts fetches fresh data when cache_key is invalid."""
        result = list_parts(cache_key="pb_invalid1")

        assert result.success is True
        assert result.cache_key != "pb_invalid1"  # New key assigned
        assert result.total == 5

    def test_list_parts_invalid_limit_low(self, fake_api_active):
        """list_parts rejects limit < 1."""
        result = list_parts(limit=0)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_parts_invalid_limit_high(self, fake_api_active):
        """list_parts rejects limit > 1000."""
        result = list_parts(limit=1001)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_list_parts_invalid_offset(self, fake_api_active):
        """list_parts rejects negative offset."""
        result = list_parts(offset=-1)

        assert result.success is False
        assert "offset must be non-negative" in result.error


class TestListPartsJMESPath:
    """Tests for JMESPath query support in list_parts."""

    def test_query_filter_by_name(self, fake_api_active):
        """JMESPath filter by name works."""
        # Use quoted identifier syntax for keys with special characters
        result = list_parts(query='[?contains("part/name", \'Resistor\')]')

        assert result.success is True
        assert result.total == 2  # 10K and 1K resistors
        assert result.query_applied == '[?contains("part/name", \'Resistor\')]'

    def test_query_filter_by_type(self, fake_api_active):
        """JMESPath filter by type works."""
        result = list_parts(query='[?"part/type" == \'linked\']')

        assert result.success is True
        assert result.total == 1  # Only ESP32
        assert result.data[0]["part/name"] == "ESP32-WROOM-32"

    def test_query_filter_by_tag(self, fake_api_active):
        """JMESPath filter by tag works."""
        result = list_parts(query='[?contains("part/tags", \'smd\')]')

        assert result.success is True
        assert result.total == 3  # Parts with 'smd' tag: 2 resistors + LED

    def test_query_projection(self, fake_api_active):
        """JMESPath projection works."""
        result = list_parts(
            query='[*].{name: "part/name", mpn: "part/mpn"}'
        )

        assert result.success is True
        assert result.total == 5
        # Check projection worked
        first = result.data[0]
        assert "name" in first
        assert "mpn" in first
        assert "part/id" not in first  # Original key should be gone

    def test_query_filter_and_projection(self, fake_api_active):
        """JMESPath filter + projection works together."""
        result = list_parts(
            query='[?contains("part/name", \'Resistor\')].{name: "part/name"}'
        )

        assert result.success is True
        assert result.total == 2
        assert all("name" in item for item in result.data)

    def test_query_sort(self, fake_api_active):
        """JMESPath sort works."""
        result = list_parts(query='sort_by(@, &"part/name")')

        assert result.success is True
        assert result.total == 5
        names = [p["part/name"] for p in result.data]
        assert names == sorted(names)

    def test_query_invalid_expression(self, fake_api_active):
        """Invalid JMESPath expression returns error."""
        result = list_parts(query="[?invalid syntax here")

        assert result.success is False
        assert "Invalid query expression" in result.error

    def test_query_with_pagination(self, fake_api_active):
        """JMESPath query works with pagination."""
        # Get first page
        result1 = list_parts(
            query='[?contains("part/tags", \'smd\')]',
            limit=2
        )

        assert result1.success is True
        assert result1.total == 3  # 3 parts with 'smd' tag
        assert len(result1.data) == 2
        assert result1.has_more is True

        # Get second page using cache
        result2 = list_parts(
            query='[?contains("part/tags", \'smd\')]',
            limit=2,
            offset=2,
            cache_key=result1.cache_key
        )

        assert result2.success is True
        assert len(result2.data) == 1  # Only 1 remaining
        assert result2.has_more is False


class TestGetPart:
    """Tests for the get_part tool function."""

    def test_get_part_success(self, fake_api_active):
        """get_part returns the correct part."""
        result = get_part("part_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["part/id"] == "part_001"
        assert result.data["part/name"] == "10K Resistor 0805"
        assert result.error is None

    def test_get_part_not_found(self, fake_api_active):
        """get_part returns error for non-existent part."""
        result = get_part("nonexistent_part")

        assert result.success is False
        assert result.data is None
        assert "not found" in result.error.lower()

    def test_get_part_empty_id(self, fake_api_active):
        """get_part returns error for empty part_id."""
        result = get_part("")

        assert result.success is False
        assert "part_id is required" in result.error

    def test_get_part_returns_full_data(self, fake_api_active):
        """get_part returns complete part data with stock."""
        result = get_part("part_001")

        assert result.success is True
        part = result.data

        # Check all expected fields
        assert "part/id" in part
        assert "part/name" in part
        assert "part/description" in part
        assert "part/type" in part
        assert "part/manufacturer" in part
        assert "part/mpn" in part
        assert "part/created" in part
        assert "part/tags" in part
        assert "part/stock" in part

        # Check stock data
        assert len(part["part/stock"]) > 0
        stock = part["part/stock"][0]
        assert "stock/quantity" in stock
        assert "stock/storage-id" in stock


class TestEmptyAPI:
    """Tests with empty API data."""

    def test_list_parts_empty(self):
        """list_parts handles empty data correctly."""
        from tests.fake_partsbox import FakePartsBoxAPI

        with FakePartsBoxAPI(parts=[]):
            result = list_parts()

            assert result.success is True
            assert result.total == 0
            assert len(result.data) == 0
            assert result.has_more is False

    def test_get_part_empty(self):
        """get_part handles empty data correctly."""
        from tests.fake_partsbox import FakePartsBoxAPI

        with FakePartsBoxAPI(parts=[]):
            result = get_part("any_id")

            assert result.success is False
            assert "not found" in result.error.lower()


class TestCacheIntegration:
    """Tests for cache behavior."""

    def test_cache_info_valid(self, fake_api_active):
        """Cache info returns valid data for active cache."""
        result = list_parts()
        cache_key = result.cache_key

        info = cache.get_info(cache_key)

        assert info.valid is True
        assert info.total_items == 5
        assert info.age_seconds >= 0
        assert info.expires_in_seconds > 0

    def test_cache_info_invalid_key(self):
        """Cache info returns invalid for unknown key."""
        info = cache.get_info("pb_unknown1")

        assert info.valid is False
        assert info.total_items is None

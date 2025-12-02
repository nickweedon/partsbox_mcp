"""
Unit tests for the Storage API module.

Tests cover:
- list_storage_locations: Paginated storage listing
- get_storage_location: Retrieve single storage location
- update_storage_location: Update location metadata
- rename_storage_location: Rename a location
- archive_storage_location: Archive a location
- restore_storage_location: Restore archived location
- list_storage_parts: List parts in a storage location
- list_storage_lots: List lots in a storage location
"""

import pytest

from partsbox_mcp.api.storage import (
    archive_storage_location,
    get_storage_location,
    list_storage_locations,
    list_storage_lots,
    list_storage_parts,
    rename_storage_location,
    restore_storage_location,
    update_storage_location,
)
from partsbox_mcp.client import cache


class TestListStorageLocations:
    """Tests for the list_storage_locations tool function."""

    def test_list_storage_returns_non_archived(self, fake_api_active):
        """list_storage_locations returns non-archived locations by default."""
        result = list_storage_locations()

        assert result.success is True
        assert result.total == 3  # Sample has 3 non-archived + 1 archived
        assert result.error is None

    def test_list_storage_includes_archived(self, fake_api_active):
        """list_storage_locations includes archived when requested."""
        result = list_storage_locations(include_archived=True)

        assert result.success is True
        assert result.total == 4  # All 4 locations

    def test_list_storage_returns_cache_key(self, fake_api_active):
        """list_storage_locations returns a valid cache key."""
        result = list_storage_locations()

        assert result.success is True
        assert result.cache_key is not None
        assert result.cache_key.startswith("pb_")

    def test_list_storage_pagination_limit(self, fake_api_active):
        """list_storage_locations respects the limit parameter."""
        result = list_storage_locations(limit=2)

        assert result.success is True
        assert len(result.data) == 2
        assert result.has_more is True

    def test_list_storage_pagination_offset(self, fake_api_active):
        """list_storage_locations respects the offset parameter."""
        result = list_storage_locations(limit=2, offset=2)

        assert result.success is True
        assert len(result.data) == 1  # Only 1 remaining (3 total non-archived)
        assert result.offset == 2
        assert result.has_more is False

    def test_list_storage_cache_reuse(self, fake_api_active):
        """list_storage_locations reuses cached data."""
        result1 = list_storage_locations(limit=2)
        cache_key = result1.cache_key

        result2 = list_storage_locations(limit=2, offset=2, cache_key=cache_key)

        assert result2.success is True
        assert result2.cache_key == cache_key

    def test_list_storage_invalid_limit(self, fake_api_active):
        """list_storage_locations rejects invalid limit."""
        result = list_storage_locations(limit=0)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error


class TestListStorageJMESPath:
    """Tests for JMESPath query support in list_storage_locations."""

    def test_query_filter_by_name(self, fake_api_active):
        """JMESPath filter by name works."""
        result = list_storage_locations(query='[?contains("storage/name", \'Drawer\')]')

        assert result.success is True
        assert result.total == 2  # Drawer A1 and Drawer A2

    def test_query_filter_by_tag(self, fake_api_active):
        """JMESPath filter by tag works."""
        result = list_storage_locations(query='[?contains("storage/tags", \'resistors\')]')

        assert result.success is True
        assert result.total == 1  # Only Drawer A1 has resistors tag

    def test_query_projection(self, fake_api_active):
        """JMESPath projection works."""
        result = list_storage_locations(query='[*].{name: "storage/name", path: "storage/path"}')

        assert result.success is True
        first = result.data[0]
        assert "name" in first
        assert "path" in first
        assert "storage/id" not in first


class TestGetStorageLocation:
    """Tests for the get_storage_location tool function."""

    def test_get_storage_success(self, fake_api_active):
        """get_storage_location returns the correct location."""
        result = get_storage_location("loc_001")

        assert result.success is True
        assert result.data is not None
        assert result.data["storage/id"] == "loc_001"
        assert result.data["storage/name"] == "Drawer A1"

    def test_get_storage_not_found(self, fake_api_active):
        """get_storage_location returns error for non-existent location."""
        result = get_storage_location("nonexistent_loc")

        assert result.success is False
        assert "not found" in result.error.lower()

    def test_get_storage_empty_id(self, fake_api_active):
        """get_storage_location returns error for empty storage_id."""
        result = get_storage_location("")

        assert result.success is False
        assert "storage_id is required" in result.error


class TestUpdateStorageLocation:
    """Tests for the update_storage_location tool function."""

    def test_update_storage_success(self, fake_api_active):
        """update_storage_location successfully updates a location."""
        result = update_storage_location(
            storage_id="loc_001",
            comments="Updated comments",
        )

        assert result.success is True
        assert result.data is not None

    def test_update_storage_with_tags(self, fake_api_active):
        """update_storage_location works with tags update."""
        result = update_storage_location(
            storage_id="loc_001",
            tags=["new-tag", "updated"],
        )

        assert result.success is True

    def test_update_storage_missing_id(self, fake_api_active):
        """update_storage_location returns error for missing storage_id."""
        result = update_storage_location(storage_id="")

        assert result.success is False
        assert "storage_id is required" in result.error


class TestRenameStorageLocation:
    """Tests for the rename_storage_location tool function."""

    def test_rename_storage_success(self, fake_api_active):
        """rename_storage_location successfully renames a location."""
        result = rename_storage_location(
            storage_id="loc_001",
            new_name="Drawer B1",
        )

        assert result.success is True
        assert result.data is not None

    def test_rename_storage_missing_id(self, fake_api_active):
        """rename_storage_location returns error for missing storage_id."""
        result = rename_storage_location(storage_id="", new_name="New Name")

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_rename_storage_missing_name(self, fake_api_active):
        """rename_storage_location returns error for missing new_name."""
        result = rename_storage_location(storage_id="loc_001", new_name="")

        assert result.success is False
        assert "new_name is required" in result.error


class TestArchiveRestoreStorage:
    """Tests for archive and restore storage functions."""

    def test_archive_storage_success(self, fake_api_active):
        """archive_storage_location successfully archives a location."""
        result = archive_storage_location("loc_001")

        assert result.success is True
        assert result.data is not None

    def test_archive_storage_missing_id(self, fake_api_active):
        """archive_storage_location returns error for missing storage_id."""
        result = archive_storage_location("")

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_restore_storage_success(self, fake_api_active):
        """restore_storage_location successfully restores a location."""
        result = restore_storage_location("loc_archived")

        assert result.success is True

    def test_restore_storage_missing_id(self, fake_api_active):
        """restore_storage_location returns error for missing storage_id."""
        result = restore_storage_location("")

        assert result.success is False
        assert "storage_id is required" in result.error


class TestListStorageParts:
    """Tests for the list_storage_parts tool function."""

    def test_list_storage_parts_success(self, fake_api_active):
        """list_storage_parts returns parts in the storage location."""
        result = list_storage_parts("loc_001")

        assert result.success is True
        # 10K resistor (2 entries: initial + move out), 1K resistor
        assert result.total == 3
        assert len(result.data) == 3

    def test_list_storage_parts_missing_id(self, fake_api_active):
        """list_storage_parts returns error for missing storage_id."""
        result = list_storage_parts("")

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_list_storage_parts_pagination(self, fake_api_active):
        """list_storage_parts supports pagination."""
        result = list_storage_parts("loc_001", limit=1)

        assert result.success is True
        assert len(result.data) == 1
        assert result.has_more is True


class TestListStorageLots:
    """Tests for the list_storage_lots tool function."""

    def test_list_storage_lots_success(self, fake_api_active):
        """list_storage_lots returns lots in the storage location."""
        result = list_storage_lots("loc_001")

        assert result.success is True
        assert result.total == 1  # One lot in loc_001

    def test_list_storage_lots_missing_id(self, fake_api_active):
        """list_storage_lots returns error for missing storage_id."""
        result = list_storage_lots("")

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_list_storage_lots_empty_location(self, fake_api_active):
        """list_storage_lots handles empty locations."""
        result = list_storage_lots("loc_archived")

        assert result.success is True
        assert result.total == 0
        assert len(result.data) == 0

"""
Unit tests for the new Parts API methods.

Tests cover:
- create_part: Creating new parts
- update_part: Updating existing parts
- delete_part: Deleting parts
- add_meta_part_ids/remove_meta_part_ids: Meta-part membership
- add_substitute_ids/remove_substitute_ids: Part substitutes
- get_part_storage: Aggregated stock by location
- get_part_lots: Individual lot entries
- get_part_stock: Total stock count
"""

import pytest

from partsbox_mcp.api.parts import (
    create_part,
    update_part,
    delete_part,
    add_meta_part_ids,
    remove_meta_part_ids,
    add_substitute_ids,
    remove_substitute_ids,
    get_part_storage,
    get_part_lots,
    get_part_stock,
)


class TestCreatePart:
    """Tests for the create_part function."""

    def test_create_part_success(self, fake_api_active):
        """create_part successfully creates a new part."""
        result = create_part(
            name="New Resistor",
            part_type="local",
            description="A new test resistor",
            manufacturer="Test Mfg",
            mpn="TEST-001",
            tags=["test", "resistor"],
        )

        assert result.success is True
        assert result.data is not None
        assert result.data["part/name"] == "New Resistor"
        assert result.data["part/type"] == "local"
        assert result.error is None

    def test_create_part_minimal(self, fake_api_active):
        """create_part works with just the name."""
        result = create_part(name="Minimal Part")

        assert result.success is True
        assert result.data["part/name"] == "Minimal Part"
        assert result.data["part/type"] == "local"

    def test_create_part_empty_name(self, fake_api_active):
        """create_part fails with empty name."""
        result = create_part(name="")

        assert result.success is False
        assert "name is required" in result.error

    def test_create_part_invalid_type(self, fake_api_active):
        """create_part fails with invalid part type."""
        result = create_part(name="Test Part", part_type="invalid")

        assert result.success is False
        assert "part_type must be one of" in result.error

    def test_create_part_with_attrition(self, fake_api_active):
        """create_part handles attrition settings."""
        result = create_part(
            name="Attrition Part",
            attrition_percentage=5.0,
            attrition_quantity=10,
        )

        assert result.success is True
        assert result.data is not None

    def test_create_part_with_low_stock(self, fake_api_active):
        """create_part handles low stock threshold."""
        result = create_part(
            name="Low Stock Part",
            low_stock_threshold=50,
        )

        assert result.success is True
        assert result.data is not None


class TestUpdatePart:
    """Tests for the update_part function."""

    def test_update_part_success(self, fake_api_active):
        """update_part successfully updates a part."""
        result = update_part(
            part_id="part_001",
            name="Updated Resistor Name",
            description="Updated description",
        )

        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_update_part_empty_id(self, fake_api_active):
        """update_part fails with empty part_id."""
        result = update_part(part_id="", name="Test")

        assert result.success is False
        assert "part_id is required" in result.error

    def test_update_part_tags(self, fake_api_active):
        """update_part can update tags."""
        result = update_part(
            part_id="part_001",
            tags=["new-tag", "updated"],
        )

        assert result.success is True


class TestDeletePart:
    """Tests for the delete_part function."""

    def test_delete_part_success(self, fake_api_active):
        """delete_part successfully deletes a part."""
        result = delete_part(part_id="part_001")

        assert result.success is True
        assert result.error is None

    def test_delete_part_empty_id(self, fake_api_active):
        """delete_part fails with empty part_id."""
        result = delete_part(part_id="")

        assert result.success is False
        assert "part_id is required" in result.error


class TestMetaPartIds:
    """Tests for meta-part membership operations."""

    def test_add_meta_part_ids_success(self, fake_api_active):
        """add_meta_part_ids successfully adds members."""
        result = add_meta_part_ids(
            part_id="part_001",
            member_ids=["part_002", "part_003"],
        )

        assert result.success is True
        assert result.error is None

    def test_add_meta_part_ids_empty_part_id(self, fake_api_active):
        """add_meta_part_ids fails with empty part_id."""
        result = add_meta_part_ids(part_id="", member_ids=["part_002"])

        assert result.success is False
        assert "part_id is required" in result.error

    def test_add_meta_part_ids_empty_members(self, fake_api_active):
        """add_meta_part_ids fails with empty member_ids."""
        result = add_meta_part_ids(part_id="part_001", member_ids=[])

        assert result.success is False
        assert "member_ids is required" in result.error

    def test_remove_meta_part_ids_success(self, fake_api_active):
        """remove_meta_part_ids successfully removes members."""
        result = remove_meta_part_ids(
            part_id="part_001",
            member_ids=["part_002"],
        )

        assert result.success is True
        assert result.error is None

    def test_remove_meta_part_ids_empty_part_id(self, fake_api_active):
        """remove_meta_part_ids fails with empty part_id."""
        result = remove_meta_part_ids(part_id="", member_ids=["part_002"])

        assert result.success is False
        assert "part_id is required" in result.error


class TestSubstituteIds:
    """Tests for substitute operations."""

    def test_add_substitute_ids_success(self, fake_api_active):
        """add_substitute_ids successfully adds substitutes."""
        result = add_substitute_ids(
            part_id="part_001",
            substitute_ids=["part_004"],
        )

        assert result.success is True
        assert result.error is None

    def test_add_substitute_ids_empty_part_id(self, fake_api_active):
        """add_substitute_ids fails with empty part_id."""
        result = add_substitute_ids(part_id="", substitute_ids=["part_002"])

        assert result.success is False
        assert "part_id is required" in result.error

    def test_add_substitute_ids_empty_substitutes(self, fake_api_active):
        """add_substitute_ids fails with empty substitute_ids."""
        result = add_substitute_ids(part_id="part_001", substitute_ids=[])

        assert result.success is False
        assert "substitute_ids is required" in result.error

    def test_remove_substitute_ids_success(self, fake_api_active):
        """remove_substitute_ids successfully removes substitutes."""
        result = remove_substitute_ids(
            part_id="part_001",
            substitute_ids=["part_004"],
        )

        assert result.success is True
        assert result.error is None


class TestGetPartStorage:
    """Tests for get_part_storage function."""

    def test_get_part_storage_success(self, fake_api_active):
        """get_part_storage returns aggregated stock by location."""
        result = get_part_storage(part_id="part_001")

        assert result.success is True
        assert result.total >= 0
        assert result.cache_key is not None
        assert result.error is None

    def test_get_part_storage_empty_id(self, fake_api_active):
        """get_part_storage fails with empty part_id."""
        result = get_part_storage(part_id="")

        assert result.success is False
        assert "part_id is required" in result.error

    def test_get_part_storage_pagination(self, fake_api_active):
        """get_part_storage respects pagination parameters."""
        result = get_part_storage(part_id="part_001", limit=1, offset=0)

        assert result.success is True
        assert result.limit == 1
        assert result.offset == 0

    def test_get_part_storage_invalid_limit(self, fake_api_active):
        """get_part_storage rejects invalid limit."""
        result = get_part_storage(part_id="part_001", limit=0)

        assert result.success is False
        assert "limit must be between 1 and 1000" in result.error

    def test_get_part_storage_invalid_offset(self, fake_api_active):
        """get_part_storage rejects negative offset."""
        result = get_part_storage(part_id="part_001", offset=-1)

        assert result.success is False
        assert "offset must be non-negative" in result.error


class TestGetPartLots:
    """Tests for get_part_lots function."""

    def test_get_part_lots_success(self, fake_api_active):
        """get_part_lots returns individual lot entries."""
        result = get_part_lots(part_id="part_001")

        assert result.success is True
        assert result.cache_key is not None
        assert result.error is None

    def test_get_part_lots_empty_id(self, fake_api_active):
        """get_part_lots fails with empty part_id."""
        result = get_part_lots(part_id="")

        assert result.success is False
        assert "part_id is required" in result.error

    def test_get_part_lots_pagination(self, fake_api_active):
        """get_part_lots respects pagination parameters."""
        result = get_part_lots(part_id="part_001", limit=10, offset=0)

        assert result.success is True
        assert result.limit == 10


class TestGetPartStock:
    """Tests for get_part_stock function."""

    def test_get_part_stock_success(self, fake_api_active):
        """get_part_stock returns total stock count."""
        result = get_part_stock(part_id="part_001")

        assert result.success is True
        assert result.total == 500  # From sample data: 500 - 100 + 100 = 500
        assert result.error is None

    def test_get_part_stock_empty_id(self, fake_api_active):
        """get_part_stock fails with empty part_id."""
        result = get_part_stock(part_id="")

        assert result.success is False
        assert "part_id is required" in result.error

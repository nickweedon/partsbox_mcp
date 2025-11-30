"""
Unit tests for the Stock API module.

Tests cover:
- add_stock: Add inventory for a part
- remove_stock: Remove parts from inventory
- move_stock: Transfer stock to different location
- update_stock: Modify existing stock entry
"""

import pytest

from partsbox_mcp.api.stock import add_stock, move_stock, remove_stock, update_stock


class TestAddStock:
    """Tests for the add_stock tool function."""

    def test_add_stock_success(self, fake_api_active):
        """add_stock successfully adds inventory."""
        result = add_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=100,
            comments="Test addition",
        )

        assert result.success is True
        assert result.data is not None
        assert result.error is None

    def test_add_stock_with_pricing(self, fake_api_active):
        """add_stock works with pricing information."""
        result = add_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=50,
            price=0.02,
            currency="usd",
        )

        assert result.success is True
        assert result.data is not None

    def test_add_stock_with_lot(self, fake_api_active):
        """add_stock works with lot information."""
        result = add_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=100,
            lot_name="Test Lot",
            lot_description="Test lot description",
        )

        assert result.success is True

    def test_add_stock_missing_part_id(self, fake_api_active):
        """add_stock returns error for missing part_id."""
        result = add_stock(
            part_id="",
            storage_id="loc_001",
            quantity=100,
        )

        assert result.success is False
        assert "part_id is required" in result.error

    def test_add_stock_missing_storage_id(self, fake_api_active):
        """add_stock returns error for missing storage_id."""
        result = add_stock(
            part_id="part_001",
            storage_id="",
            quantity=100,
        )

        assert result.success is False
        assert "storage_id is required" in result.error

    def test_add_stock_invalid_quantity(self, fake_api_active):
        """add_stock returns error for invalid quantity."""
        result = add_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=0,
        )

        assert result.success is False
        assert "quantity must be positive" in result.error

    def test_add_stock_negative_quantity(self, fake_api_active):
        """add_stock returns error for negative quantity."""
        result = add_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=-10,
        )

        assert result.success is False
        assert "quantity must be positive" in result.error


class TestRemoveStock:
    """Tests for the remove_stock tool function."""

    def test_remove_stock_success(self, fake_api_active):
        """remove_stock successfully removes inventory."""
        result = remove_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=10,
        )

        assert result.success is True
        assert result.data is not None

    def test_remove_stock_with_comments(self, fake_api_active):
        """remove_stock works with comments."""
        result = remove_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=5,
            comments="Used in project",
        )

        assert result.success is True

    def test_remove_stock_with_lot_id(self, fake_api_active):
        """remove_stock works with specific lot_id."""
        result = remove_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=10,
            lot_id="lot_001",
        )

        assert result.success is True

    def test_remove_stock_missing_part_id(self, fake_api_active):
        """remove_stock returns error for missing part_id."""
        result = remove_stock(
            part_id="",
            storage_id="loc_001",
            quantity=10,
        )

        assert result.success is False
        assert "part_id is required" in result.error

    def test_remove_stock_invalid_quantity(self, fake_api_active):
        """remove_stock returns error for invalid quantity."""
        result = remove_stock(
            part_id="part_001",
            storage_id="loc_001",
            quantity=0,
        )

        assert result.success is False
        assert "quantity must be positive" in result.error


class TestMoveStock:
    """Tests for the move_stock tool function."""

    def test_move_stock_success(self, fake_api_active):
        """move_stock successfully moves inventory."""
        result = move_stock(
            part_id="part_001",
            source_storage_id="loc_001",
            target_storage_id="loc_002",
            quantity=50,
        )

        assert result.success is True
        assert result.data is not None

    def test_move_stock_with_comments(self, fake_api_active):
        """move_stock works with comments."""
        result = move_stock(
            part_id="part_001",
            source_storage_id="loc_001",
            target_storage_id="loc_002",
            quantity=25,
            comments="Reorganizing storage",
        )

        assert result.success is True

    def test_move_stock_missing_source(self, fake_api_active):
        """move_stock returns error for missing source."""
        result = move_stock(
            part_id="part_001",
            source_storage_id="",
            target_storage_id="loc_002",
            quantity=50,
        )

        assert result.success is False
        assert "source_storage_id is required" in result.error

    def test_move_stock_missing_target(self, fake_api_active):
        """move_stock returns error for missing target."""
        result = move_stock(
            part_id="part_001",
            source_storage_id="loc_001",
            target_storage_id="",
            quantity=50,
        )

        assert result.success is False
        assert "target_storage_id is required" in result.error


class TestUpdateStock:
    """Tests for the update_stock tool function."""

    def test_update_stock_success(self, fake_api_active):
        """update_stock successfully updates inventory."""
        result = update_stock(
            part_id="part_001",
            timestamp=1700000000000,
            quantity=600,
        )

        assert result.success is True
        assert result.data is not None

    def test_update_stock_with_comments(self, fake_api_active):
        """update_stock works with comments update."""
        result = update_stock(
            part_id="part_001",
            timestamp=1700000000000,
            comments="Updated comment",
        )

        assert result.success is True

    def test_update_stock_with_pricing(self, fake_api_active):
        """update_stock works with pricing update."""
        result = update_stock(
            part_id="part_001",
            timestamp=1700000000000,
            price=0.015,
            currency="eur",
        )

        assert result.success is True

    def test_update_stock_missing_part_id(self, fake_api_active):
        """update_stock returns error for missing part_id."""
        result = update_stock(
            part_id="",
            timestamp=1700000000000,
        )

        assert result.success is False
        assert "part_id is required" in result.error

    def test_update_stock_missing_timestamp(self, fake_api_active):
        """update_stock returns error for missing timestamp."""
        result = update_stock(
            part_id="part_001",
            timestamp=0,
        )

        assert result.success is False
        assert "timestamp is required" in result.error

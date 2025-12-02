"""
Tests for type definitions and response type mappings.

These tests verify that:
1. API responses conform to the expected TypedDict structures
2. All required fields are present in sample data
3. Field types match the documented schema
"""

import pytest

from tests.fake_partsbox import (
    FakePartsBoxAPI,
    SAMPLE_BUILDS,
    SAMPLE_LOTS,
    SAMPLE_ORDER_ENTRIES,
    SAMPLE_ORDERS,
    SAMPLE_PARTS,
    SAMPLE_PROJECT_ENTRIES,
    SAMPLE_PROJECTS,
    SAMPLE_STORAGE,
)

from partsbox_mcp.api.lots import list_lots, get_lot
from partsbox_mcp.api.orders import list_orders, get_order, get_order_entries
from partsbox_mcp.api.parts import list_parts, get_part
from partsbox_mcp.api.projects import (
    list_projects,
    get_project,
    get_project_entries,
    get_project_builds,
    get_build,
)
from partsbox_mcp.api.storage import (
    list_storage_locations,
    get_storage_location,
    list_storage_parts,
    list_storage_lots,
)


# =============================================================================
# Part Type Tests
# =============================================================================


class TestPartDataTypes:
    """Tests for Part data type conformance."""

    def test_part_has_required_fields(self) -> None:
        """Verify all parts have required fields."""
        required_fields = ["part/id", "part/name", "part/type", "part/created", "part/owner"]
        for part in SAMPLE_PARTS:
            for field in required_fields:
                assert field in part, f"Part missing required field: {field}"

    def test_part_id_is_string(self) -> None:
        """Verify part IDs are strings."""
        for part in SAMPLE_PARTS:
            assert isinstance(part["part/id"], str)

    def test_part_type_is_valid(self) -> None:
        """Verify part types are valid enum values."""
        valid_types = {"local", "linked", "sub-assembly", "meta"}
        for part in SAMPLE_PARTS:
            assert part["part/type"] in valid_types

    def test_part_created_is_timestamp(self) -> None:
        """Verify created field is a timestamp (integer)."""
        for part in SAMPLE_PARTS:
            assert isinstance(part["part/created"], int)
            assert part["part/created"] > 0

    def test_part_tags_is_list_of_strings(self) -> None:
        """Verify tags is a list of strings."""
        for part in SAMPLE_PARTS:
            assert isinstance(part["part/tags"], list)
            for tag in part["part/tags"]:
                assert isinstance(tag, str)

    def test_part_stock_is_list(self) -> None:
        """Verify stock is a list of stock entries."""
        for part in SAMPLE_PARTS:
            assert isinstance(part["part/stock"], list)

    def test_stock_entry_has_required_fields(self) -> None:
        """Verify stock entries have required fields."""
        required_fields = ["stock/quantity", "stock/storage-id", "stock/timestamp"]
        for part in SAMPLE_PARTS:
            for stock in part["part/stock"]:
                for field in required_fields:
                    assert field in stock, f"Stock entry missing field: {field}"

    def test_list_parts_returns_correct_type(self) -> None:
        """Verify list_parts returns properly typed response."""
        with FakePartsBoxAPI():
            result = list_parts()
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 5
            # Check first part has expected structure
            first_part = result.data[0]
            assert "part/id" in first_part
            assert "part/name" in first_part
            assert "part/stock" in first_part

    def test_get_part_returns_correct_type(self) -> None:
        """Verify get_part returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_part("part_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["part/id"] == "part_001"
            assert "part/stock" in result.data


# =============================================================================
# Stock Entry Type Tests
# =============================================================================


class TestStockEntryDataTypes:
    """Tests for Stock entry data type conformance."""

    def test_stock_quantity_is_integer(self) -> None:
        """Verify stock quantities are integers."""
        for part in SAMPLE_PARTS:
            for stock in part["part/stock"]:
                assert isinstance(stock["stock/quantity"], int)

    def test_stock_price_is_number(self) -> None:
        """Verify stock prices are numbers when present."""
        for part in SAMPLE_PARTS:
            for stock in part["part/stock"]:
                if "stock/price" in stock:
                    assert isinstance(stock["stock/price"], (int, float))

    def test_stock_currency_is_string(self) -> None:
        """Verify currency codes are strings when present."""
        for part in SAMPLE_PARTS:
            for stock in part["part/stock"]:
                if "stock/currency" in stock:
                    assert isinstance(stock["stock/currency"], str)


# =============================================================================
# Lot Type Tests
# =============================================================================


class TestLotDataTypes:
    """Tests for Lot data type conformance."""

    def test_lot_has_required_fields(self) -> None:
        """Verify all lots have required fields."""
        required_fields = ["lot/id", "lot/created"]
        for lot in SAMPLE_LOTS:
            for field in required_fields:
                assert field in lot, f"Lot missing required field: {field}"

    def test_lot_expiration_date_nullable(self) -> None:
        """Verify expiration date can be null or integer."""
        for lot in SAMPLE_LOTS:
            exp_date = lot.get("lot/expiration-date")
            assert exp_date is None or isinstance(exp_date, int)

    def test_lot_tags_is_list(self) -> None:
        """Verify lot tags is a list."""
        for lot in SAMPLE_LOTS:
            assert isinstance(lot["lot/tags"], list)

    def test_list_lots_returns_correct_type(self) -> None:
        """Verify list_lots returns properly typed response."""
        with FakePartsBoxAPI():
            result = list_lots()
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 3

    def test_get_lot_returns_correct_type(self) -> None:
        """Verify get_lot returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_lot("lot_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["lot/id"] == "lot_001"


# =============================================================================
# Storage Type Tests
# =============================================================================


class TestStorageDataTypes:
    """Tests for Storage data type conformance."""

    def test_storage_has_required_fields(self) -> None:
        """Verify all storage locations have required fields."""
        required_fields = ["storage/id", "storage/name"]
        for storage in SAMPLE_STORAGE:
            for field in required_fields:
                assert field in storage, f"Storage missing required field: {field}"

    def test_storage_archived_is_boolean(self) -> None:
        """Verify archived field is boolean."""
        for storage in SAMPLE_STORAGE:
            assert isinstance(storage["storage/archived"], bool)

    def test_storage_boolean_flags(self) -> None:
        """Verify boolean flag fields are boolean."""
        bool_fields = ["storage/full?", "storage/single-part?", "storage/existing-parts-only?"]
        for storage in SAMPLE_STORAGE:
            for field in bool_fields:
                if field in storage:
                    assert isinstance(storage[field], bool)

    def test_list_storage_returns_correct_type(self) -> None:
        """Verify list_storage_locations returns properly typed response."""
        with FakePartsBoxAPI():
            result = list_storage_locations()
            assert result.success is True
            assert isinstance(result.data, list)
            # Should exclude archived by default
            assert len(result.data) == 3

    def test_get_storage_returns_correct_type(self) -> None:
        """Verify get_storage_location returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_storage_location("loc_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["storage/id"] == "loc_001"

    def test_list_storage_parts_returns_source_data(self) -> None:
        """Verify list_storage_parts returns source data format."""
        with FakePartsBoxAPI():
            result = list_storage_parts("loc_001")
            assert result.success is True
            assert isinstance(result.data, list)
            # Check source data format
            for source in result.data:
                assert "part/id" in source or "stock/quantity" in source

    def test_list_storage_lots_returns_lot_data(self) -> None:
        """Verify list_storage_lots returns lot data format."""
        with FakePartsBoxAPI():
            result = list_storage_lots("loc_001")
            assert result.success is True
            assert isinstance(result.data, list)


# =============================================================================
# Project Type Tests
# =============================================================================


class TestProjectDataTypes:
    """Tests for Project data type conformance."""

    def test_project_has_required_fields(self) -> None:
        """Verify all projects have required fields."""
        required_fields = ["project/id", "project/name"]
        for project in SAMPLE_PROJECTS:
            for field in required_fields:
                assert field in project, f"Project missing required field: {field}"

    def test_project_archived_is_boolean(self) -> None:
        """Verify archived field is boolean."""
        for project in SAMPLE_PROJECTS:
            assert isinstance(project["project/archived"], bool)

    def test_project_entry_count_is_integer(self) -> None:
        """Verify entry count is integer."""
        for project in SAMPLE_PROJECTS:
            assert isinstance(project["project/entry-count"], int)

    def test_list_projects_returns_correct_type(self) -> None:
        """Verify list_projects returns properly typed response."""
        with FakePartsBoxAPI():
            result = list_projects()
            assert result.success is True
            assert isinstance(result.data, list)
            # Should exclude archived by default
            assert len(result.data) == 2

    def test_get_project_returns_correct_type(self) -> None:
        """Verify get_project returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_project("proj_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["project/id"] == "proj_001"


# =============================================================================
# Project Entry Type Tests
# =============================================================================


class TestProjectEntryDataTypes:
    """Tests for Project Entry data type conformance."""

    def test_entry_has_required_fields(self) -> None:
        """Verify all entries have required fields."""
        required_fields = ["entry/id", "entry/part-id", "entry/quantity"]
        for project_id, entries in SAMPLE_PROJECT_ENTRIES.items():
            for entry in entries:
                for field in required_fields:
                    assert field in entry, f"Entry in {project_id} missing field: {field}"

    def test_entry_quantity_is_integer(self) -> None:
        """Verify entry quantities are integers."""
        for entries in SAMPLE_PROJECT_ENTRIES.values():
            for entry in entries:
                assert isinstance(entry["entry/quantity"], int)

    def test_entry_designators_is_list(self) -> None:
        """Verify designators is a list or string."""
        for entries in SAMPLE_PROJECT_ENTRIES.values():
            for entry in entries:
                designators = entry.get("entry/designators")
                assert designators is None or isinstance(designators, (list, str))

    def test_get_project_entries_returns_correct_type(self) -> None:
        """Verify get_project_entries returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_project_entries("proj_001")
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 3


# =============================================================================
# Build Type Tests
# =============================================================================


class TestBuildDataTypes:
    """Tests for Build data type conformance."""

    def test_build_has_required_fields(self) -> None:
        """Verify all builds have required fields."""
        required_fields = ["build/id", "build/project-id"]
        for project_id, builds in SAMPLE_BUILDS.items():
            for build in builds:
                for field in required_fields:
                    assert field in build, f"Build in {project_id} missing field: {field}"

    def test_build_quantity_is_integer(self) -> None:
        """Verify build quantities are integers."""
        for builds in SAMPLE_BUILDS.values():
            for build in builds:
                if "build/quantity" in build:
                    assert isinstance(build["build/quantity"], int)

    def test_get_project_builds_returns_correct_type(self) -> None:
        """Verify get_project_builds returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_project_builds("proj_001")
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 1

    def test_get_build_returns_correct_type(self) -> None:
        """Verify get_build returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_build("build_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["build/id"] == "build_001"


# =============================================================================
# Order Type Tests
# =============================================================================


class TestOrderDataTypes:
    """Tests for Order data type conformance."""

    def test_order_has_required_fields(self) -> None:
        """Verify all orders have required fields."""
        required_fields = ["order/id", "order/created"]
        for order in SAMPLE_ORDERS:
            for field in required_fields:
                assert field in order, f"Order missing required field: {field}"

    def test_order_created_is_timestamp(self) -> None:
        """Verify created field is a timestamp."""
        for order in SAMPLE_ORDERS:
            assert isinstance(order["order/created"], int)

    def test_order_status_is_valid(self) -> None:
        """Verify order status is a valid value."""
        valid_statuses = {"open", "ordered", "received"}
        for order in SAMPLE_ORDERS:
            assert order["order/status"] in valid_statuses

    def test_order_arriving_nullable(self) -> None:
        """Verify arriving can be null or integer."""
        for order in SAMPLE_ORDERS:
            arriving = order.get("order/arriving")
            assert arriving is None or isinstance(arriving, int)

    def test_list_orders_returns_correct_type(self) -> None:
        """Verify list_orders returns properly typed response."""
        with FakePartsBoxAPI():
            result = list_orders()
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 2

    def test_get_order_returns_correct_type(self) -> None:
        """Verify get_order returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_order("order_001")
            assert result.success is True
            assert result.data is not None
            assert result.data["order/id"] == "order_001"


# =============================================================================
# Order Entry Type Tests
# =============================================================================


class TestOrderEntryDataTypes:
    """Tests for Order Entry data type conformance."""

    def test_order_entry_has_required_fields(self) -> None:
        """Verify all order entries have required fields."""
        required_fields = ["stock/id", "stock/part-id", "stock/quantity", "stock/order-id"]
        for order_id, entries in SAMPLE_ORDER_ENTRIES.items():
            for entry in entries:
                for field in required_fields:
                    assert field in entry, f"Order entry in {order_id} missing field: {field}"

    def test_order_entry_quantity_is_integer(self) -> None:
        """Verify entry quantities are integers."""
        for entries in SAMPLE_ORDER_ENTRIES.values():
            for entry in entries:
                assert isinstance(entry["stock/quantity"], int)

    def test_order_entry_price_is_number(self) -> None:
        """Verify entry prices are numbers when present."""
        for entries in SAMPLE_ORDER_ENTRIES.values():
            for entry in entries:
                if "stock/price" in entry and entry["stock/price"] is not None:
                    assert isinstance(entry["stock/price"], (int, float))

    def test_order_entry_status_nullable(self) -> None:
        """Verify status can be null or string."""
        for entries in SAMPLE_ORDER_ENTRIES.values():
            for entry in entries:
                status = entry.get("stock/status")
                assert status is None or isinstance(status, str)

    def test_get_order_entries_returns_correct_type(self) -> None:
        """Verify get_order_entries returns properly typed response."""
        with FakePartsBoxAPI():
            result = get_order_entries("order_001")
            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 2


# =============================================================================
# Field Presence Tests
# =============================================================================


class TestNewlyAddedFields:
    """Tests to verify newly added fields are present in sample data."""

    def test_parts_have_footprint(self) -> None:
        """Verify parts have footprint field."""
        for part in SAMPLE_PARTS:
            assert "part/footprint" in part

    def test_parts_have_notes(self) -> None:
        """Verify parts have notes field."""
        for part in SAMPLE_PARTS:
            assert "part/notes" in part

    def test_parts_have_cad_keys(self) -> None:
        """Verify parts have cad-keys field."""
        for part in SAMPLE_PARTS:
            assert "part/cad-keys" in part
            assert isinstance(part["part/cad-keys"], list)

    def test_storage_has_description(self) -> None:
        """Verify storage has description field."""
        for storage in SAMPLE_STORAGE:
            assert "storage/description" in storage

    def test_projects_have_notes(self) -> None:
        """Verify projects have notes field."""
        for project in SAMPLE_PROJECTS:
            assert "project/notes" in project

    def test_project_entries_have_order(self) -> None:
        """Verify project entries have order field."""
        for entries in SAMPLE_PROJECT_ENTRIES.values():
            for entry in entries:
                assert "entry/order" in entry
                assert isinstance(entry["entry/order"], int)

    def test_project_entries_have_cad_fields(self) -> None:
        """Verify project entries have CAD fields."""
        for entries in SAMPLE_PROJECT_ENTRIES.values():
            for entry in entries:
                assert "entry/cad-footprint" in entry
                assert "entry/cad-key" in entry

    def test_orders_have_vendor_name(self) -> None:
        """Verify orders have vendor-name field."""
        for order in SAMPLE_ORDERS:
            assert "order/vendor-name" in order

    def test_orders_have_tags(self) -> None:
        """Verify orders have tags field."""
        for order in SAMPLE_ORDERS:
            assert "order/tags" in order
            assert isinstance(order["order/tags"], list)

    def test_order_entries_have_vendor_sku(self) -> None:
        """Verify order entries have vendor-sku field."""
        for entries in SAMPLE_ORDER_ENTRIES.values():
            for entry in entries:
                assert "stock/vendor-sku" in entry

    def test_lots_have_order_id(self) -> None:
        """Verify lots have order-id field."""
        for lot in SAMPLE_LOTS:
            assert "lot/order-id" in lot

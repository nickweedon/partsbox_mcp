"""
Fake PartsBox API server for testing.

This module provides:
- Sample data matching the real PartsBox API format
- A responses-based mock server for unit tests
- Fixtures for pytest
"""

import json
import time
from typing import Any

import responses

from partsbox_mcp.types import (
    BuildData,
    LotData,
    OrderData,
    OrderEntryData,
    PartData,
    ProjectData,
    ProjectEntryData,
    SourceData,
    StockEntryData,
    StorageData,
)

# =============================================================================
# Sample Data - Matches Real PartsBox API Format
# =============================================================================

# Realistic part data based on real PartsBox API responses
# Note: Field names use '/' characters as per PartsBox API format
SAMPLE_PARTS: list[PartData] = [
    {
        "part/id": "part_001",
        "part/name": "10K Resistor 0805",
        "part/description": "10K Ohm 1% 0805 SMD Resistor",
        "part/type": "local",
        "part/manufacturer": "Yageo",
        "part/mpn": "RC0805FR-0710KL",
        "part/footprint": "0805",
        "part/notes": "Standard 10K pullup/pulldown resistor",
        "part/created": 1700000000000,
        "part/owner": "owner_001",
        "part/tags": ["resistor", "smd", "0805"],
        "part/cad-keys": ["R_0805_10K"],
        "part/attrition": {"percentage": 5.0, "quantity": 0},
        "part/low-stock": {"report": 100},
        "part/custom-fields": None,
        "part/stock": [
            {
                "stock/quantity": 500,
                "stock/storage-id": "loc_001",
                "stock/timestamp": 1700000000000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.01,
                "stock/comments": "Initial stock",
            }
        ],
    },
    {
        "part/id": "part_002",
        "part/name": "100nF Capacitor 0603",
        "part/description": "100nF 16V X7R 0603 MLCC",
        "part/type": "local",
        "part/manufacturer": "Samsung",
        "part/mpn": "CL10B104KB8NNNC",
        "part/footprint": "0603",
        "part/notes": None,
        "part/created": 1700000100000,
        "part/owner": "owner_001",
        "part/tags": ["capacitor", "mlcc", "0603"],
        "part/cad-keys": [],
        "part/custom-fields": {"voltage_rating": "16V"},
        "part/stock": [
            {
                "stock/quantity": 1000,
                "stock/storage-id": "loc_002",
                "stock/timestamp": 1700000100000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.02,
            }
        ],
    },
    {
        "part/id": "part_003",
        "part/name": "ESP32-WROOM-32",
        "part/description": "ESP32 WiFi+BT Module",
        "part/type": "linked",
        "part/manufacturer": "Espressif",
        "part/mpn": "ESP32-WROOM-32",
        "part/footprint": "MODULE_ESP32",
        "part/notes": "WiFi and Bluetooth dual-mode module",
        "part/created": 1700000200000,
        "part/owner": "owner_001",
        "part/linked-id": "linked_esp32",
        "part/tags": ["mcu", "wifi", "bluetooth", "module"],
        "part/cad-keys": ["ESP32-WROOM-32"],
        "part/custom-fields": {"flash_size": "4MB"},
        "part/stock": [
            {
                "stock/quantity": 25,
                "stock/storage-id": "loc_003",
                "stock/timestamp": 1700000200000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 3.50,
            }
        ],
    },
    {
        "part/id": "part_004",
        "part/name": "1K Resistor 0805",
        "part/description": "1K Ohm 1% 0805 SMD Resistor",
        "part/type": "local",
        "part/manufacturer": "Yageo",
        "part/mpn": "RC0805FR-071KL",
        "part/footprint": "0805",
        "part/notes": None,
        "part/created": 1700000300000,
        "part/owner": "owner_001",
        "part/tags": ["resistor", "smd", "0805"],
        "part/cad-keys": ["R_0805_1K"],
        "part/custom-fields": None,
        "part/stock": [
            {
                "stock/quantity": 5,
                "stock/storage-id": "loc_001",
                "stock/timestamp": 1700000300000,
                "stock/user": "testuser",
                "stock/currency": "usd",
                "stock/price": 0.01,
            }
        ],
    },
    {
        "part/id": "part_005",
        "part/name": "Red LED 0805",
        "part/description": "Red LED 0805 SMD",
        "part/type": "local",
        "part/manufacturer": "Everlight",
        "part/mpn": "19-217/R6C-AL1M2VY/3T",
        "part/footprint": "LED_0805",
        "part/notes": None,
        "part/created": 1700000400000,
        "part/owner": "owner_001",
        "part/tags": ["led", "smd", "0805", "red"],
        "part/cad-keys": [],
        "part/custom-fields": None,
        "part/stock": [],
    },
]

# Sample storage locations
SAMPLE_STORAGE: list[StorageData] = [
    {
        "storage/id": "loc_001",
        "storage/name": "Drawer A1",
        "storage/description": "Resistors storage drawer",
        "storage/parent-id": None,
        "storage/path": "Drawer A1",
        "storage/archived": False,
        "storage/full?": False,
        "storage/single-part?": False,
        "storage/existing-parts-only?": False,
        "storage/created": 1700000000000,
        "storage/comments": "SMD Resistors",
        "storage/tags": ["resistors"],
        "storage/custom-fields": None,
    },
    {
        "storage/id": "loc_002",
        "storage/name": "Drawer A2",
        "storage/description": "Capacitors storage drawer",
        "storage/parent-id": None,
        "storage/path": "Drawer A2",
        "storage/archived": False,
        "storage/full?": False,
        "storage/single-part?": False,
        "storage/existing-parts-only?": False,
        "storage/created": 1700000000000,
        "storage/comments": "SMD Capacitors",
        "storage/tags": ["capacitors"],
        "storage/custom-fields": None,
    },
    {
        "storage/id": "loc_003",
        "storage/name": "Module Shelf",
        "storage/description": "MCU modules shelf",
        "storage/parent-id": None,
        "storage/path": "Module Shelf",
        "storage/archived": False,
        "storage/full?": False,
        "storage/single-part?": True,
        "storage/existing-parts-only?": False,
        "storage/created": 1700000000000,
        "storage/comments": "MCU Modules",
        "storage/tags": ["modules", "mcu"],
        "storage/custom-fields": None,
    },
    {
        "storage/id": "loc_archived",
        "storage/name": "Old Storage",
        "storage/description": "Archived location - no longer in use",
        "storage/parent-id": None,
        "storage/path": "Old Storage",
        "storage/archived": True,
        "storage/full?": True,
        "storage/single-part?": False,
        "storage/existing-parts-only?": True,
        "storage/created": 1699000000000,
        "storage/comments": "Archived location",
        "storage/tags": [],
        "storage/custom-fields": None,
    },
]

# Sample lots
SAMPLE_LOTS: list[LotData] = [
    {
        "lot/id": "lot_001",
        "lot/name": "Batch 2024-01",
        "lot/description": "January 2024 procurement",
        "lot/part-id": "part_001",
        "lot/storage-id": "loc_001",
        "lot/quantity": 500,
        "lot/created": 1700000000000,
        "lot/expiration-date": None,
        "lot/tags": ["2024", "batch"],
        "lot/comments": "Initial stock",
        "lot/order-id": None,
        "lot/custom-fields": None,
    },
    {
        "lot/id": "lot_002",
        "lot/name": "Batch 2024-02",
        "lot/description": "February 2024 procurement",
        "lot/part-id": "part_002",
        "lot/storage-id": "loc_002",
        "lot/quantity": 1000,
        "lot/created": 1700000100000,
        "lot/expiration-date": 1800000000000,
        "lot/tags": ["2024", "batch"],
        "lot/comments": "With expiration",
        "lot/order-id": "order_001",
        "lot/custom-fields": {"batch_number": "B2024-02"},
    },
    {
        "lot/id": "lot_003",
        "lot/name": "ESP32 Lot",
        "lot/description": "ESP32 modules",
        "lot/part-id": "part_003",
        "lot/storage-id": "loc_003",
        "lot/quantity": 25,
        "lot/created": 1700000200000,
        "lot/expiration-date": None,
        "lot/tags": ["modules"],
        "lot/comments": "",
        "lot/order-id": "order_002",
        "lot/custom-fields": None,
    },
]

# Sample projects
SAMPLE_PROJECTS: list[ProjectData] = [
    {
        "project/id": "proj_001",
        "project/name": "Arduino Shield v1",
        "project/description": "Custom Arduino shield project",
        "project/notes": "This is a prototype Arduino shield with sensor integration.",
        "project/created": 1700000000000,
        "project/updated": 1700000500000,
        "project/archived": False,
        "project/comments": "Main project",
        "project/entry-count": 3,
        "project/custom-fields": {"revision": "1.0"},
    },
    {
        "project/id": "proj_002",
        "project/name": "ESP32 Board",
        "project/description": "ESP32 development board",
        "project/notes": None,
        "project/created": 1700000100000,
        "project/updated": 1700000600000,
        "project/archived": False,
        "project/comments": "",
        "project/entry-count": 2,
        "project/custom-fields": None,
    },
    {
        "project/id": "proj_archived",
        "project/name": "Old Project",
        "project/description": "Archived project",
        "project/notes": None,
        "project/created": 1699000000000,
        "project/updated": 1699000000000,
        "project/archived": True,
        "project/comments": "",
        "project/entry-count": 0,
        "project/custom-fields": None,
    },
]

# Sample project entries
SAMPLE_PROJECT_ENTRIES: dict[str, list[ProjectEntryData]] = {
    "proj_001": [
        {
            "entry/id": "entry_001",
            "entry/part-id": "part_001",
            "entry/quantity": 10,
            "entry/name": "10K Pullup Resistors",
            "entry/designators": ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8", "R9", "R10"],
            "entry/comments": "",
            "entry/order": 1,
            "entry/cad-footprint": "R_0805",
            "entry/cad-key": "R_0805_10K",
            "entry/custom-fields": None,
        },
        {
            "entry/id": "entry_002",
            "entry/part-id": "part_002",
            "entry/quantity": 5,
            "entry/name": "Decoupling Capacitors",
            "entry/designators": ["C1", "C2", "C3", "C4", "C5"],
            "entry/comments": "Decoupling caps",
            "entry/order": 2,
            "entry/cad-footprint": "C_0603",
            "entry/cad-key": None,
            "entry/custom-fields": None,
        },
        {
            "entry/id": "entry_003",
            "entry/part-id": "part_005",
            "entry/quantity": 2,
            "entry/name": "Status LEDs",
            "entry/designators": ["D1", "D2"],
            "entry/comments": "Status LEDs",
            "entry/order": 3,
            "entry/cad-footprint": "LED_0805",
            "entry/cad-key": None,
            "entry/custom-fields": {"color": "red"},
        },
    ],
    "proj_002": [
        {
            "entry/id": "entry_004",
            "entry/part-id": "part_003",
            "entry/quantity": 1,
            "entry/name": "ESP32 Module",
            "entry/designators": ["U1"],
            "entry/comments": "Main MCU",
            "entry/order": 1,
            "entry/cad-footprint": "MODULE_ESP32",
            "entry/cad-key": "ESP32-WROOM-32",
            "entry/custom-fields": None,
        },
        {
            "entry/id": "entry_005",
            "entry/part-id": "part_002",
            "entry/quantity": 10,
            "entry/name": "Bypass Capacitors",
            "entry/designators": ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"],
            "entry/comments": "",
            "entry/order": 2,
            "entry/cad-footprint": "C_0603",
            "entry/cad-key": None,
            "entry/custom-fields": None,
        },
    ],
}

# Sample builds
SAMPLE_BUILDS: dict[str, list[BuildData]] = {
    "proj_001": [
        {
            "build/id": "build_001",
            "build/project-id": "proj_001",
            "build/quantity": 5,
            "build/created": 1700000500000,
            "build/comments": "First prototype build",
        },
    ],
    "proj_002": [],
}

# Sample orders
SAMPLE_ORDERS: list[OrderData] = [
    {
        "order/id": "order_001",
        "order/vendor-name": "Mouser Electronics",
        "order/vendor": "Mouser Electronics",
        "order/number": "MO-12345",
        "order/invoice-number": "INV-2024-001",
        "order/po-number": "PO-2024-001",
        "order/status": "open",
        "order/created": 1700000000000,
        "order/comments": "Monthly restock",
        "order/notes": "Regular monthly component restock order",
        "order/arriving": 1701000000000,
        "order/tags": ["monthly", "restock"],
        "order/custom-fields": None,
    },
    {
        "order/id": "order_002",
        "order/vendor-name": "DigiKey",
        "order/vendor": "DigiKey",
        "order/number": "DK-67890",
        "order/invoice-number": "DK-INV-67890",
        "order/po-number": None,
        "order/status": "received",
        "order/created": 1699500000000,
        "order/comments": "ESP32 order",
        "order/notes": None,
        "order/arriving": None,
        "order/tags": ["mcu", "esp32"],
        "order/custom-fields": None,
    },
]

# Sample order entries
SAMPLE_ORDER_ENTRIES: dict[str, list[OrderEntryData]] = {
    "order_001": [
        {
            "stock/id": "oentry_001",
            "stock/part-id": "part_001",
            "stock/quantity": 1000,
            "stock/price": 0.008,
            "stock/currency": "usd",
            "stock/timestamp": 1700000000000,
            "stock/order-id": "order_001",
            "stock/status": "ordered",
            "stock/storage-id": None,
            "stock/lot-id": None,
            "stock/comments": "Resistor restock",
            "stock/vendor-sku": "603-RC0805FR-0710KL",
            "stock/custom-price?": False,
            "stock/arriving": 1701000000000,
        },
        {
            "stock/id": "oentry_002",
            "stock/part-id": "part_002",
            "stock/quantity": 2000,
            "stock/price": 0.015,
            "stock/currency": "usd",
            "stock/timestamp": 1700000000000,
            "stock/order-id": "order_001",
            "stock/status": "ordered",
            "stock/storage-id": None,
            "stock/lot-id": None,
            "stock/comments": "Capacitor restock",
            "stock/vendor-sku": "187-CL10B104KB8NNNC",
            "stock/custom-price?": False,
            "stock/arriving": 1701000000000,
        },
    ],
    "order_002": [
        {
            "stock/id": "oentry_003",
            "stock/part-id": "part_003",
            "stock/quantity": 25,
            "stock/price": 3.00,
            "stock/currency": "usd",
            "stock/timestamp": 1699500000000,
            "stock/order-id": "order_002",
            "stock/status": None,
            "stock/storage-id": "loc_003",
            "stock/lot-id": "lot_003",
            "stock/comments": "ESP32 modules received",
            "stock/vendor-sku": "356-ESP32-WROOM-32",
            "stock/custom-price?": False,
            "stock/arriving": None,
        },
    ],
}


def get_sample_parts() -> list[PartData]:
    """Return a copy of sample parts data."""
    return [p.copy() for p in SAMPLE_PARTS]  # type: ignore[misc]


def get_sample_part(part_id: str) -> PartData | None:
    """Return a single sample part by ID."""
    for part in SAMPLE_PARTS:
        if part["part/id"] == part_id:
            return part.copy()  # type: ignore[return-value]
    return None


def get_sample_storage() -> list[StorageData]:
    """Return a copy of sample storage data."""
    return [s.copy() for s in SAMPLE_STORAGE]  # type: ignore[misc]


def get_sample_lots() -> list[LotData]:
    """Return a copy of sample lots data."""
    return [lot.copy() for lot in SAMPLE_LOTS]  # type: ignore[misc]


def get_sample_projects() -> list[ProjectData]:
    """Return a copy of sample projects data."""
    return [p.copy() for p in SAMPLE_PROJECTS]  # type: ignore[misc]


def get_sample_orders() -> list[OrderData]:
    """Return a copy of sample orders data."""
    return [o.copy() for o in SAMPLE_ORDERS]  # type: ignore[misc]


# =============================================================================
# API Response Builders
# =============================================================================


def build_success_response(data: Any) -> dict[str, Any]:
    """Build a successful API response matching real PartsBox format."""
    return {
        "data": data,
        "partsbox.status/category": "ok",
        "partsbox.status/message": "OK",
    }


def build_error_response(message: str) -> dict[str, Any]:
    """Build an error API response."""
    return {
        "data": None,
        "partsbox.status/category": "status/error",
        "partsbox.status/message": message,
    }


# =============================================================================
# Mock Server Setup
# =============================================================================


class FakePartsBoxAPI:
    """
    A fake PartsBox API server using the responses library.

    Usage:
        with FakePartsBoxAPI() as fake_api:
            # Make requests to the API
            response = requests.post("https://api.partsbox.com/api/1/part/all")
    """

    BASE_URL = "https://api.partsbox.com/api/1"

    def __init__(
        self,
        parts: list[dict[str, Any]] | None = None,
        storage: list[dict[str, Any]] | None = None,
        lots: list[dict[str, Any]] | None = None,
        projects: list[dict[str, Any]] | None = None,
        orders: list[dict[str, Any]] | None = None,
    ):
        self._parts = parts if parts is not None else get_sample_parts()
        self._storage = storage if storage is not None else get_sample_storage()
        self._lots = lots if lots is not None else get_sample_lots()
        self._projects = projects if projects is not None else get_sample_projects()
        self._orders = orders if orders is not None else get_sample_orders()
        self._project_entries = {k: [e.copy() for e in v] for k, v in SAMPLE_PROJECT_ENTRIES.items()}
        self._builds = {k: [b.copy() for b in v] for k, v in SAMPLE_BUILDS.items()}
        self._order_entries = {k: [e.copy() for e in v] for k, v in SAMPLE_ORDER_ENTRIES.items()}
        self._mock = responses.RequestsMock(assert_all_requests_are_fired=False)

    def __enter__(self) -> "FakePartsBoxAPI":
        self._mock.start()
        self._setup_endpoints()
        return self

    def __exit__(self, *args: Any) -> None:
        self._mock.stop()
        self._mock.reset()

    def _setup_endpoints(self) -> None:
        """Set up all mock endpoints."""
        # Part endpoints
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/part/all",
            json=build_success_response(self._parts),
            status=200,
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/part/get",
            callback=self._handle_part_get,
            content_type="application/json",
        )

        # Stock endpoints
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/stock/add",
            callback=self._handle_stock_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/stock/remove",
            callback=self._handle_stock_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/stock/move",
            callback=self._handle_stock_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/stock/update",
            callback=self._handle_stock_operation,
            content_type="application/json",
        )

        # Lot endpoints
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/lot/all",
            json=build_success_response(self._lots),
            status=200,
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/lot/get",
            callback=self._handle_lot_get,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/lot/update",
            callback=self._handle_lot_update,
            content_type="application/json",
        )

        # Storage endpoints
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/storage/all",
            json=build_success_response(self._storage),
            status=200,
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/get",
            callback=self._handle_storage_get,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/update",
            callback=self._handle_storage_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/rename",
            callback=self._handle_storage_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/archive",
            callback=self._handle_storage_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/restore",
            callback=self._handle_storage_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/parts",
            callback=self._handle_storage_parts,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/storage/lots",
            callback=self._handle_storage_lots,
            content_type="application/json",
        )

        # Project endpoints
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/project/all",
            json=build_success_response(self._projects),
            status=200,
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/get",
            callback=self._handle_project_get,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/create",
            callback=self._handle_project_create,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/update",
            callback=self._handle_project_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/delete",
            callback=self._handle_project_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/archive",
            callback=self._handle_project_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/restore",
            callback=self._handle_project_operation,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/get-entries",
            callback=self._handle_project_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/add-entries",
            callback=self._handle_project_modify_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/update-entries",
            callback=self._handle_project_modify_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/delete-entries",
            callback=self._handle_project_modify_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/project/get-builds",
            callback=self._handle_project_builds,
            content_type="application/json",
        )

        # Build endpoints
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/build/get",
            callback=self._handle_build_get,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/build/update",
            callback=self._handle_build_update,
            content_type="application/json",
        )

        # Order endpoints
        self._mock.add(
            responses.POST,
            f"{self.BASE_URL}/order/all",
            json=build_success_response(self._orders),
            status=200,
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/order/get",
            callback=self._handle_order_get,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/order/create",
            callback=self._handle_order_create,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/order/get-entries",
            callback=self._handle_order_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/order/add-entries",
            callback=self._handle_order_add_entries,
            content_type="application/json",
        )
        self._mock.add_callback(
            responses.POST,
            f"{self.BASE_URL}/order/receive",
            callback=self._handle_order_receive,
            content_type="application/json",
        )

    def _handle_part_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle part/get requests dynamically."""
        try:
            body = json.loads(request.body)
            part_id = body.get("part/id")

            if not part_id:
                return (
                    400,
                    {},
                    json.dumps(build_error_response("part/id is required")),
                )

            for part in self._parts:
                if part["part/id"] == part_id:
                    return (200, {}, json.dumps(build_success_response(part)))

            return (
                404,
                {},
                json.dumps(build_error_response(f"Part not found: {part_id}")),
            )
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_stock_operation(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle stock operations (add/remove/move/update)."""
        try:
            body = json.loads(request.body)
            # Return the body as confirmation of what was received
            return (200, {}, json.dumps(build_success_response(body)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_lot_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle lot/get requests."""
        try:
            body = json.loads(request.body)
            lot_id = body.get("lot/id")

            if not lot_id:
                return (400, {}, json.dumps(build_error_response("lot/id is required")))

            for lot in self._lots:
                if lot["lot/id"] == lot_id:
                    return (200, {}, json.dumps(build_success_response(lot)))

            return (404, {}, json.dumps(build_error_response(f"Lot not found: {lot_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_lot_update(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle lot/update requests."""
        try:
            body = json.loads(request.body)
            lot_id = body.get("lot/id")

            if not lot_id:
                return (400, {}, json.dumps(build_error_response("lot/id is required")))

            for lot in self._lots:
                if lot["lot/id"] == lot_id:
                    # Update fields
                    if "lot/name" in body:
                        lot["lot/name"] = body["lot/name"]
                    if "lot/description" in body:
                        lot["lot/description"] = body["lot/description"]
                    return (200, {}, json.dumps(build_success_response(lot)))

            return (404, {}, json.dumps(build_error_response(f"Lot not found: {lot_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_storage_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle storage/get requests."""
        try:
            body = json.loads(request.body)
            storage_id = body.get("storage/id")

            if not storage_id:
                return (400, {}, json.dumps(build_error_response("storage/id is required")))

            for loc in self._storage:
                if loc["storage/id"] == storage_id:
                    return (200, {}, json.dumps(build_success_response(loc)))

            return (404, {}, json.dumps(build_error_response(f"Storage not found: {storage_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_storage_operation(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle storage modification operations."""
        try:
            body = json.loads(request.body)
            storage_id = body.get("storage/id")

            if not storage_id:
                return (400, {}, json.dumps(build_error_response("storage/id is required")))

            for loc in self._storage:
                if loc["storage/id"] == storage_id:
                    return (200, {}, json.dumps(build_success_response(loc)))

            return (404, {}, json.dumps(build_error_response(f"Storage not found: {storage_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_storage_parts(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle storage/parts requests."""
        try:
            body = json.loads(request.body)
            storage_id = body.get("storage/id")

            if not storage_id:
                return (400, {}, json.dumps(build_error_response("storage/id is required")))

            # Return parts that have stock in this storage location
            parts_in_storage = []
            for part in self._parts:
                for stock in part.get("part/stock", []):
                    if stock.get("stock/storage-id") == storage_id:
                        parts_in_storage.append({
                            "part/id": part["part/id"],
                            "part/name": part["part/name"],
                            "stock/quantity": stock["stock/quantity"],
                        })

            return (200, {}, json.dumps(build_success_response(parts_in_storage)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_storage_lots(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle storage/lots requests."""
        try:
            body = json.loads(request.body)
            storage_id = body.get("storage/id")

            if not storage_id:
                return (400, {}, json.dumps(build_error_response("storage/id is required")))

            # Return lots in this storage location
            lots_in_storage = [
                lot for lot in self._lots
                if lot.get("lot/storage-id") == storage_id
            ]

            return (200, {}, json.dumps(build_success_response(lots_in_storage)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project/get requests."""
        try:
            body = json.loads(request.body)
            project_id = body.get("project/id")

            if not project_id:
                return (400, {}, json.dumps(build_error_response("project/id is required")))

            for proj in self._projects:
                if proj["project/id"] == project_id:
                    return (200, {}, json.dumps(build_success_response(proj)))

            return (404, {}, json.dumps(build_error_response(f"Project not found: {project_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_create(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project/create requests."""
        try:
            body = json.loads(request.body)
            name = body.get("project/name")

            if not name:
                return (400, {}, json.dumps(build_error_response("project/name is required")))

            new_project = {
                "project/id": f"proj_{int(time.time())}",
                "project/name": name,
                "project/description": body.get("project/description", ""),
                "project/created": int(time.time() * 1000),
                "project/updated": int(time.time() * 1000),
                "project/archived": False,
                "project/comments": body.get("project/comments", ""),
                "project/entry-count": 0,
            }
            self._projects.append(new_project)
            return (200, {}, json.dumps(build_success_response(new_project)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_operation(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project modification operations."""
        try:
            body = json.loads(request.body)
            project_id = body.get("project/id")

            if not project_id:
                return (400, {}, json.dumps(build_error_response("project/id is required")))

            for proj in self._projects:
                if proj["project/id"] == project_id:
                    return (200, {}, json.dumps(build_success_response(proj)))

            return (404, {}, json.dumps(build_error_response(f"Project not found: {project_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_entries(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project/get-entries requests."""
        try:
            body = json.loads(request.body)
            project_id = body.get("project/id")

            if not project_id:
                return (400, {}, json.dumps(build_error_response("project/id is required")))

            entries = self._project_entries.get(project_id, [])
            return (200, {}, json.dumps(build_success_response(entries)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_modify_entries(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project entry modification requests."""
        try:
            body = json.loads(request.body)
            project_id = body.get("project/id")

            if not project_id:
                return (400, {}, json.dumps(build_error_response("project/id is required")))

            return (200, {}, json.dumps(build_success_response({"status": "ok"})))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_project_builds(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle project/get-builds requests."""
        try:
            body = json.loads(request.body)
            project_id = body.get("project/id")

            if not project_id:
                return (400, {}, json.dumps(build_error_response("project/id is required")))

            builds = self._builds.get(project_id, [])
            return (200, {}, json.dumps(build_success_response(builds)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_build_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle build/get requests."""
        try:
            body = json.loads(request.body)
            build_id = body.get("build/id")

            if not build_id:
                return (400, {}, json.dumps(build_error_response("build/id is required")))

            for builds in self._builds.values():
                for build in builds:
                    if build["build/id"] == build_id:
                        return (200, {}, json.dumps(build_success_response(build)))

            return (404, {}, json.dumps(build_error_response(f"Build not found: {build_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_build_update(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle build/update requests."""
        try:
            body = json.loads(request.body)
            build_id = body.get("build/id")

            if not build_id:
                return (400, {}, json.dumps(build_error_response("build/id is required")))

            for builds in self._builds.values():
                for build in builds:
                    if build["build/id"] == build_id:
                        if "build/comments" in body:
                            build["build/comments"] = body["build/comments"]
                        return (200, {}, json.dumps(build_success_response(build)))

            return (404, {}, json.dumps(build_error_response(f"Build not found: {build_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_order_get(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle order/get requests."""
        try:
            body = json.loads(request.body)
            order_id = body.get("order/id")

            if not order_id:
                return (400, {}, json.dumps(build_error_response("order/id is required")))

            for order in self._orders:
                if order["order/id"] == order_id:
                    return (200, {}, json.dumps(build_success_response(order)))

            return (404, {}, json.dumps(build_error_response(f"Order not found: {order_id}")))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_order_create(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle order/create requests."""
        try:
            body = json.loads(request.body)
            vendor = body.get("order/vendor")

            if not vendor:
                return (400, {}, json.dumps(build_error_response("order/vendor is required")))

            new_order = {
                "order/id": f"order_{int(time.time())}",
                "order/vendor": vendor,
                "order/number": body.get("order/number", ""),
                "order/status": "open",
                "order/created": int(time.time() * 1000),
                "order/comments": body.get("order/comments", ""),
            }
            self._orders.append(new_order)
            return (200, {}, json.dumps(build_success_response(new_order)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_order_entries(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle order/get-entries requests."""
        try:
            body = json.loads(request.body)
            order_id = body.get("order/id")

            if not order_id:
                return (400, {}, json.dumps(build_error_response("order/id is required")))

            entries = self._order_entries.get(order_id, [])
            return (200, {}, json.dumps(build_success_response(entries)))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_order_add_entries(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle order/add-entries requests."""
        try:
            body = json.loads(request.body)
            order_id = body.get("order/id")

            if not order_id:
                return (400, {}, json.dumps(build_error_response("order/id is required")))

            return (200, {}, json.dumps(build_success_response({"status": "ok"})))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def _handle_order_receive(self, request: Any) -> tuple[int, dict[str, str], str]:
        """Handle order/receive requests."""
        try:
            body = json.loads(request.body)
            order_id = body.get("order/id")
            storage_id = body.get("stock/storage-id")

            if not order_id:
                return (400, {}, json.dumps(build_error_response("order/id is required")))
            if not storage_id:
                return (400, {}, json.dumps(build_error_response("stock/storage-id is required")))

            return (200, {}, json.dumps(build_success_response({"status": "received"})))
        except Exception as e:
            return (500, {}, json.dumps(build_error_response(str(e))))

    def set_parts(self, parts: list[dict[str, Any]]) -> None:
        """Update the parts data (must be called before entering context)."""
        self._parts = parts


# =============================================================================
# Pytest Fixtures
# =============================================================================


def create_fake_api(
    parts: list[dict[str, Any]] | None = None,
) -> FakePartsBoxAPI:
    """Create a FakePartsBoxAPI instance for testing."""
    return FakePartsBoxAPI(parts)
